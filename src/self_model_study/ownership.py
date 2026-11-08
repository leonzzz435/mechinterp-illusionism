"""Qwen/permissions tranche of the unchanged ownership-replication-v1 design."""

import gzip
import json
import tarfile
from copy import deepcopy
from itertools import product
from pathlib import Path

from .action_task import apply_update, successful_commands
from .io import canonical, digest, file_hash, read_json, write_json
from .pilot import audit_records, jobs_in, run_plan, scientific_spec
from .pilot_backend import create_backend, encode_boundary, render_prompt
from .storage import read_records

ROOT = Path(__file__).resolve().parents[2]
DESIGN_PATH = ROOT / "designs/ownership-replication.json"
DESIGN_SHA256 = "d1024e5384ad233be1c41d6cb248c0bd92a2615ea1ac7b9553d88a571358d996"
PREFLIGHT = ROOT / "review/ownership-permissions-preflight.json"
INPUTS = ROOT / "review/ownership-permissions-inputs.json.gz"
ENGINE = "qwen-ownership-permissions"
PROTOCOL = "ownership-replication-v1"
CATEGORIES = (
    "invalid",
    "correct_target_current",
    "other_account_current",
    "revoked_target",
    "other_valid_command",
)


def design():
    if file_hash(DESIGN_PATH) != DESIGN_SHA256:
        raise ValueError("Frozen ownership specification changed")
    return read_json(DESIGN_PATH)


def configuration(block):
    if type(block) is not int or block not in range(3):
        raise ValueError("Only the three authorized Qwen/permissions blocks are supported")
    return {
        "engine": ENGINE,
        "protocol": PROTOCOL,
        "design_sha256": DESIGN_SHA256,
        "tranche": "qwen-permissions-v1",
        "block_index": block,
        "world_indices": list(range(16 * block, 16 * (block + 1))),
        "task_template": "permissions",
        "harness_version": "0.4.13",
        "model": {**design()["models"][0], "dtype": "bfloat16", "max_length": 2048},
        "generation": {},
        "batch_size": 1,
        "formats": ["chat"],
        "num_fewshot": 0,
        "score": "sum_log_likelihood",
        "max_seconds": 5400,
    }


def validate_spec(spec):
    expected = configuration(spec.get("block_index"))
    if set(spec) != set(expected) or any(
        canonical(spec[k]) != canonical(v) for k, v in expected.items() if k != "max_seconds"
    ):
        raise ValueError("Only unchanged Qwen/permissions tranche configurations are supported")
    if type(spec["max_seconds"]) is not int or not 0 < spec["max_seconds"] <= 5400:
        raise ValueError("Invocation time must be 1–5400 seconds")
    return spec


def world(index, spec=None):
    spec = spec or design()
    sid = f"ownership-v1:{index:04d}"

    def ranked(labels):
        return sorted(labels, key=lambda label: digest([94173, sid, label]))

    return (
        sid,
        ranked(spec["sample"]["actor_labels"])[:2],
        ["mark_" + label for label in ranked(spec["sample"]["command_labels"])[:4]],
    )


def build_plan(spec):
    validate_spec(spec)
    frozen = design()
    blocks = []
    for index in spec["world_indices"]:
        sid, actors, commands = world(index, frozen)
        before = {
            "commands": commands,
            "permissions": {a: [commands[i]] for i, a in enumerate(actors)},
            "markers": dict.fromkeys(actors, 0),
        }
        jobs = []
        for target_id, updated, phase, grant, rotation, frame, relation in product(
            (0, 1),
            (0, 1),
            ("before", "after"),
            (2, 3),
            range(4),
            ("your", "their", "neutral"),
            ("target", "other"),
        ):
            target = actors[target_id]
            mentioned = target if relation == "target" else actors[1 - target_id]
            event = {
                "actor": actors[updated],
                "revoke": commands[updated],
                "grant": commands[grant],
            }
            state = apply_update(before, event) if phase == "after" else deepcopy(before)
            choices = commands[rotation:] + commands[:rotation]
            event_text = frozen["event_rendering"]["permissions_" + phase].format(
                old=event["revoke"], new=event["grant"], updated_actor=event["actor"]
            )
            prompt = frozen["task_templates"]["permissions"]["render"].format(
                context=frozen["conditions"]["frames"][frame].format(mentioned_actor=mentioned),
                actor_a=actors[0],
                actor_b=actors[1],
                c0=commands[0],
                c1=commands[1],
                event=event_text,
                target=target,
                options="\n".join(choices),
            )
            successes = successful_commands(state, target)
            if len(successes) != 1:
                raise ValueError("Ambiguous simulator oracle")
            rid = digest(
                [
                    PROTOCOL,
                    "permissions",
                    sid,
                    target_id,
                    updated,
                    phase,
                    grant,
                    rotation,
                    frame,
                    relation,
                ]
            )
            row = {
                "id": rid,
                "scenario_id": sid,
                "world_index": index,
                "target_identity": target_id,
                "updated": updated,
                "phase": phase,
                "grant_variant": grant,
                "rotation": rotation,
                "frame": frame,
                "relation": relation,
                "mentioned_actor": mentioned,
                "target": target,
                "event": event,
                "before": before,
                "state": state,
                "choices": choices,
                "expected_command": successes[0],
                "expected_position": choices.index(successes[0]),
                "relevant_update": target == event["actor"],
                "prompt": prompt,
            }
            jobs.append({"id": rid, "kind": "action", "format": "chat", "row": row})
        if len(jobs) != 384 or len({j["id"] for j in jobs}) != 384:
            raise ValueError("Incomplete factorial world")
        # Execution order is fixed without model-based selection; keep all variants per world.
        jobs.sort(key=lambda j: digest([94173, "execution-order", j["id"]]))
        blocks.append({"id": sid, "jobs": jobs})
    return {
        "protocol": PROTOCOL,
        "split": "fresh_replication",
        "task_template": "permissions",
        "block_index": spec["block_index"],
        "blocks": blocks,
    }


def stratum(row):
    return (
        "before"
        if row["phase"] == "before"
        else ("after_relevant" if row["relevant_update"] else "after_irrelevant")
    )


def classify(row, result):
    if result is None:
        return "missing"  # Administrative coverage, never an observed model response.
    command = result.get("selected_command")
    if result.get("status") != "ok" or command not in row["choices"]:
        return "invalid"
    if command in row["state"]["permissions"][row["target"]]:
        return "correct_target_current"
    other = next(a for a in row["state"]["permissions"] if a != row["target"])
    if command in row["state"]["permissions"][other]:
        return "other_account_current"
    if (
        row["phase"] == "after"
        and row["relevant_update"]
        and command in row["before"]["permissions"][row["target"]]
    ):
        return "revoked_target"
    return "other_valid_command"


def without_context(prompt):
    return "\n".join(
        line
        for line in prompt.splitlines()
        if not line.startswith(
            (
                "Your active connection:",
                "Their active connection:",
                "The active connection:",
                "Reference connection:",
            )
        )
    )


def historical_inputs():
    """Read every archived plan, including design archives; do not modify or extract files."""
    exact, stripped, inventory = set(), set(), {}

    def visit(value):
        if isinstance(value, dict):
            if isinstance(value.get("prompt"), str):
                exact.add(value["prompt"])
                stripped.add(without_context(value["prompt"]))
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    for archive in sorted((ROOT / "review/evidence").glob("*.tar.gz")):
        with tarfile.open(archive) as tar:
            member = tar.getmember("run/plan.json")
            visit(json.load(tar.extractfile(member)))
        inventory[archive.name] = file_hash(archive)
    if not inventory or not exact:
        raise ValueError("No historical inputs for overlap audit")
    return exact, stripped, inventory


def check_overlap(prompts, exact, stripped):
    for prompt in prompts:
        if prompt in exact or without_context(prompt) in stripped:
            raise ValueError("Historical input collision; frozen version blocked, no resampling")


def load_tokenizer(spec):
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(
        spec["model"]["repo"], revision=spec["model"]["revision"], trust_remote_code=False
    )


def encode_inputs(plan, tokenizer):
    inputs = {}
    for job in jobs_in(plan):
        row = job["row"]
        if row["prompt"] in inputs:
            continue
        rendered = render_prompt(tokenizer, row["prompt"], "chat")
        pairs = [encode_boundary(tokenizer, rendered, c, 2048) for c in row["choices"]]
        inputs[row["prompt"]] = {
            "rendered_prompt": rendered,
            "prompt_token_ids": pairs[0][0],
            "continuations": dict(zip(row["choices"], [pair[1] for pair in pairs])),
        }
    return inputs


def freeze_inputs(destination=PREFLIGHT, token_path=INPUTS, tokenizer=None):
    """CPU preparation only. The exact plans and token inputs are frozen before weights load."""
    plans = [build_plan(configuration(i)) for i in range(3)]
    historical, stripped, inventory = historical_inputs()
    tokenizer = tokenizer or load_tokenizer(configuration(0))
    inputs, blocks = {}, []
    for i, plan in enumerate(plans):
        encoded = encode_inputs(plan, tokenizer)
        check_overlap(encoded, historical, stripped)
        inputs.update(encoded)
        blocks.append(
            {
                "block_index": i,
                "world_indices": configuration(i)["world_indices"],
                "choices": len(jobs_in(plan)),
                "plan_hash": digest(plan),
                "token_inputs_hash": digest(encoded),
            }
        )
    token_path = Path(token_path)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_bytes(gzip.compress((canonical(inputs) + "\n").encode(), mtime=0))
    modules = ("ownership.py", "pilot.py", "pilot_backend.py", "action_task.py", "io.py")
    audit = {
        "protocol": PROTOCOL,
        "kind": "design_only",
        "model_inference": False,
        "design_sha256": DESIGN_SHA256,
        "model": configuration(0)["model"],
        "blocks": blocks,
        "scheduled_choices": 18432,
        "independent_worlds": 48,
        "world_assignments": [world(i) for i in range(48)],
        "historical_archives": inventory,
        "historical_prompt_count": len(historical),
        "exact_and_context_stripped_collisions": 0,
        "source_files": {
            f"src/self_model_study/{n}": file_hash(Path(__file__).parent / n) for n in modules
        },
        "tokenizer_vocabulary_hash": digest(tokenizer.get_vocab()),
        "chat_template": tokenizer.chat_template,
        "chat_template_hash": digest(tokenizer.chat_template),
        "token_inputs_sha256": file_hash(token_path),
        "token_inputs_hash": digest(inputs),
        "max_context_including_answer": max(
            len(v["prompt_token_ids"]) + len(c)
            for v in inputs.values()
            for c in v["continuations"].values()
        ),
        "command_token_lengths": {
            command: sorted(
                {
                    len(v["continuations"][command])
                    for v in inputs.values()
                    if command in v["continuations"]
                }
            )
            for command in sorted({c for v in inputs.values() for c in v["continuations"]})
        },
    }
    write_json(destination, audit)
    return audit


def frozen_inputs(spec, plan):
    audit = read_json(PREFLIGHT)
    if audit["design_sha256"] != DESIGN_SHA256 or audit["blocks"][spec["block_index"]][
        "plan_hash"
    ] != digest(plan):
        raise ValueError("Plan differs from pre-inference manifest")
    if file_hash(INPUTS) != audit["token_inputs_sha256"]:
        raise ValueError("Frozen token inputs changed")
    if any(file_hash(ROOT / p) != h for p, h in audit["source_files"].items()):
        raise ValueError("Execution source differs from CPU preflight")
    inputs = json.loads(gzip.decompress(INPUTS.read_bytes()))
    selected = {j["row"]["prompt"]: inputs[j["row"]["prompt"]] for j in jobs_in(plan)}
    if digest(selected) != audit["blocks"][spec["block_index"]]["token_inputs_hash"]:
        raise ValueError("Frozen token subset mismatch")
    return selected, audit


def check_output(row, result, inputs):
    expected = inputs[row["prompt"]]
    if any(result.get(k) != expected[k] for k in ("rendered_prompt", "prompt_token_ids")):
        raise ValueError("Executed input differs from frozen tokens")
    if [c["command"] for c in result["candidates"]] != row["choices"]:
        raise ValueError("Candidate inventory changed")
    for c in result["candidates"]:
        if c["token_ids"] != expected["continuations"][c["command"]] or c["token_count"] != len(
            c["token_ids"]
        ):
            raise ValueError("Candidate tokens changed")


def checked_backend(spec):
    plan = build_plan(spec)
    inputs, audit = frozen_inputs(spec, plan)
    tokenizer = load_tokenizer(spec)
    if (
        digest(tokenizer.get_vocab()) != audit["tokenizer_vocabulary_hash"]
        or digest(tokenizer.chat_template) != audit["chat_template_hash"]
    ):
        raise ValueError("Tokenizer changed before model loading")
    backend, info = create_backend(spec)
    if any(info[k] != audit[k] for k in ("tokenizer_vocabulary_hash", "chat_template_hash")):
        raise ValueError("Loaded scorer tokenizer differs from preflight")
    return backend, {
        **info,
        "preflight_sha256": file_hash(PREFLIGHT),
        "token_inputs_hash": audit["blocks"][spec["block_index"]]["token_inputs_hash"],
    }


def run(spec, directory, max_jobs=None, backend_factory=None, checkpoint=None):
    validate_spec(spec)
    plan = build_plan(spec)
    inputs = None
    if backend_factory is None:
        inputs, _ = frozen_inputs(spec, plan)

    def execute(backend, job):
        row = job["row"]
        result = backend.choice(row["prompt"], row["choices"], job["format"])
        if inputs is not None:
            check_output(row, result, inputs)
        if result["status"] == "invalid_scores":
            result["technical_failure"] = "Nonfinite or incomplete scores; stop, no fallback"
        return result

    def audit_existing(_directory, manifest, records):
        if not manifest["synthetic"]:
            saved_inputs, audit = frozen_inputs(spec, plan)
            if manifest["backend_info"]["preflight_sha256"] != file_hash(PREFLIGHT):
                raise ValueError("Preflight changed across invocations")
            for record in records:
                if record["status"] != "error":
                    check_output(record["job"]["row"], record["result"], saved_inputs)

    return run_plan(
        spec,
        plan,
        directory,
        max_jobs,
        backend_factory or checked_backend,
        checkpoint,
        trial_executor=execute,
        artifact_audit=audit_existing,
    )


def read_run(directory):
    directory = Path(directory)
    manifest = read_json(directory / "manifest.json")
    spec = validate_spec(manifest["config"])
    plan = read_json(directory / "plan.json")
    if (
        manifest["engine"] != ENGINE
        or manifest["protocol"] != PROTOCOL
        or digest(plan) != manifest["plan_hash"]
        or digest(plan) != digest(build_plan(spec))
    ):
        raise ValueError("Saved ownership plan changed")
    if digest(scientific_spec(spec)) != manifest["config_hash"]:
        raise ValueError("Saved ownership config changed")
    records = read_records(directory)
    audit_records(records, plan, manifest)
    if manifest["expected_jobs"] != len(jobs_in(plan)):
        raise ValueError("Saved expected coverage changed")
    if manifest["status"] == "complete" and (
        len(records) != manifest["expected_jobs"] or any(r["status"] != "ok" for r in records)
    ):
        raise ValueError("Invalid complete-run status")
    if not manifest["synthetic"]:
        inputs, _ = frozen_inputs(spec, plan)
        for record in records:
            if record["status"] != "error":
                check_output(record["job"]["row"], record["result"], inputs)
    return manifest, plan, records
