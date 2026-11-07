"""Frozen one-token possessive control; no internal intervention or capability confirmation."""

from copy import deepcopy
from itertools import product
from pathlib import Path

from .action_task import VERSION as ACTION_VERSION
from .action_task import build_design, score_command
from .data import rng_for
from .io import canonical, digest, read_json, write_json
from .pilot import audit_records, jobs_in, run_plan, scientific_spec
from .pilot import tokenizer_audit as audit_tokenizer
from .pilot_backend import create_backend
from .storage import read_records

PROTOCOL = "qwen-possessive-v1"
ENGINE = "qwen-possessive-control"
FRAMES = ("your", "the", "reference")
RELATIONS = ("target", "other")
CONDITIONS = tuple(product(FRAMES, RELATIONS))
DEFAULT_SPEC = {
    "protocol": PROTOCOL,
    "engine": ENGINE,
    "harness_version": "0.4.13",
    "model": {
        "repo": "Qwen/Qwen2.5-7B-Instruct",
        "revision": "a09a35458c702b33eeacc393d103063234e8bc28",
        "dtype": "bfloat16",
        "max_length": 2048,
    },
    "action_version": ACTION_VERSION,
    "dataset_seed": 1729,
    "scenarios": list(range(16, 32)),
    "formats": ["chat"],
    "context_lines": {
        "your": "Your active connection: {actor}.",
        "the": "The active connection: {actor}.",
        "reference": "Reference connection: {actor}.",
    },
    "generation": {},
    "batch_size": 1,
    "num_fewshot": 0,
    "score": "sum_log_likelihood",
    "bootstrap_samples": 10000,
    "analysis_seed": 1729,
    "decision": {
        "primary_stratum": "after_relevant",
        "minimum_interaction": 0.05,
        "minimum_positive_scenarios": 12,
        "control_accuracy": 0.80,
        "primary_two_sided_alpha": 0.05,
    },
    "max_seconds": 5400,
}
# Checked CPU design, frozen before any model inference.
FROZEN_PLAN_HASH = "ab455c85fb4a1c0e237dcbd317f1e0be4401d65dc2cc0a8d9bbe95994d0b511d"
FROZEN_TOKEN_INPUTS_HASH = "44da35dd8ca75899c277f60ec3cbf7b34f4c4f6cceda646e461cb24089a90b4e"


def validate_spec(spec):
    if set(spec) != set(DEFAULT_SPEC):
        raise ValueError("Unknown or incomplete possessive-control configuration")
    for key, value in DEFAULT_SPEC.items():
        if key != "max_seconds" and canonical(spec[key]) != canonical(value):
            raise ValueError(f"Frozen possessive-control field changed: {key}; use a new protocol")
    if type(spec["max_seconds"]) is not int or not 0 < spec["max_seconds"] <= 5400:
        raise ValueError("Possessive-control invocation limit must be 1–5400 seconds")
    return spec


def stratum(row):
    if row["phase"] == "before":
        return "before"
    return "after_relevant" if row["relevant_update"] else "after_irrelevant"


def build_plan(spec):
    validate_spec(spec)
    # Select one named query per fixed scene; assignment is rebuilt as a factor.
    scenes = [
        r
        for r in build_design(seed=spec["dataset_seed"], scenarios=32)
        if r["view"] == "named_self"
        and int(r["scenario_id"].rsplit(":", 1)[1]) in spec["scenarios"]
    ]
    blocks = []
    for index in spec["scenarios"]:
        selected = [r for r in scenes if int(r["scenario_id"].rsplit(":", 1)[1]) == index]
        selected.sort(key=lambda r: r["id"])
        rng_for([PROTOCOL, index, "scene-order"]).shuffle(selected)
        condition_order = list(CONDITIONS)
        rng_for([PROTOCOL, index, "condition-order"]).shuffle(condition_order)
        jobs = []
        for offset, scene in enumerate(selected):
            # Six conditions remain adjacent but their execution order is counterbalanced.
            start = offset % len(CONDITIONS)
            conditions = condition_order[start:] + condition_order[:start]
            for frame, relation in conditions:
                row = deepcopy(scene)
                actor = (
                    row["target"]
                    if relation == "target"
                    else next(a for a in row["state"]["permissions"] if a != row["target"])
                )
                old = "Your active connection: " + scene["assigned"] + "."
                line = spec["context_lines"][frame].format(actor=actor)
                if row["prompt"].count(old) != 1:
                    raise ValueError("Expected one replaceable role line")
                row["prompt"] = row["prompt"].replace(old, line)
                # Original scene metadata cannot masquerade as an assignment in reference mode.
                for key in ("assigned", "identity", "view", "execution_mode", "language_prompt"):
                    row.pop(key)
                row.update(
                    scene_id=scene["id"],
                    frame=frame,
                    relation=relation,
                    mentioned_actor=actor,
                    target_identity=scene["identity"],
                    execution_mode="named_target_copy",
                )
                row["id"] = digest([PROTOCOL, scene["id"], frame, relation])
                jobs.append({"id": row["id"], "kind": "action", "format": "chat", "row": row})
        blocks.append({"id": f"possessive-{index:02d}", "jobs": jobs})
    plan = {"protocol": PROTOCOL, "split": "development", "blocks": blocks}
    if digest(plan) != FROZEN_PLAN_HASH:
        raise ValueError("Frozen possessive-control inputs changed; use a new protocol")
    return plan


def preview(spec):
    plan = build_plan(spec)
    jobs = jobs_in(plan)
    return {
        "protocol": PROTOCOL,
        "valid": True,
        "kind": "design_only",
        "model_inference": False,
        "action_choices": len(jobs),
        "independent_scenarios": len(plan["blocks"]),
        "scene_variants": len({j["row"]["scene_id"] for j in jobs}),
        "unique_model_inputs": len({j["row"]["prompt"] for j in jobs}),
        "conditions": [list(c) for c in CONDITIONS],
        "plan_hash": digest(plan),
        "config_hash": digest(scientific_spec(spec)),
        "simulator_oracle_accuracy": sum(
            score_command(j["row"], j["row"]["expected_command"])["correct"] for j in jobs
        )
        / len(jobs),
        "max_seconds": spec["max_seconds"],
        "note": "No model result. Repeated before-update inputs are paired design variants.",
    }


def load_tokenizer(spec):
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(
        spec["model"]["repo"], revision=spec["model"]["revision"], trust_remote_code=False
    )


def token_inputs(spec, tokenizer):
    """Check all actual continuations and the one-token, equal-length matched contrast."""
    from collections import defaultdict

    from .pilot_backend import encode_boundary, render_prompt

    inputs, pairs = {}, defaultdict(dict)
    for job in jobs_in(build_plan(spec)):
        row = job["row"]
        rendered = render_prompt(tokenizer, row["prompt"], "chat")
        encoded = [
            encode_boundary(tokenizer, rendered, c, spec["model"]["max_length"])
            for c in row["choices"]
        ]
        item = {
            "rendered_prompt": rendered,
            "prompt_token_ids": encoded[0][0],
            "continuations": dict(zip(row["choices"], [p[1] for p in encoded])),
        }
        inputs[row["prompt"]] = item
        pairs[row["scene_id"], row["relation"]][row["frame"]] = item["prompt_token_ids"]
    for pair in pairs.values():
        a, b = pair["your"], pair["the"]
        if len(a) != len(b) or [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y] != [
            (57, 7771, 785)
        ]:
            raise ValueError("Your/The contrast is not the frozen one-token edit")
    if digest(inputs) != FROZEN_TOKEN_INPUTS_HASH:
        raise ValueError("Rendered tokens differ from the frozen CPU preflight")
    return inputs


def tokenizer_audit(spec, tokenizer=None):
    tokenizer = tokenizer or load_tokenizer(spec)
    inputs = token_inputs(spec, tokenizer)
    return {
        **preview(spec),
        **audit_tokenizer(spec, tokenizer, plan=build_plan(spec)),
        "matched_your_the_pairs": 2048,
        "candidate_boundaries_checked": 24576,
        "token_change": {"position": 57, "your": 7771, "the": 785},
        "token_inputs_hash": digest(inputs),
    }


def check_output(prompt, result, inputs):
    expected = inputs[prompt]
    for key in ("rendered_prompt", "prompt_token_ids"):
        if result.get(key) != expected[key]:
            raise ValueError("Model input differs from audited possessive tokens")
    if len(result["candidates"]) != 4:
        raise ValueError("Missing candidate tokens")
    for c in result["candidates"]:
        ids = expected["continuations"].get(c["command"])
        if ids is None or c["token_ids"] != ids or c["token_count"] != len(ids):
            raise ValueError("Candidate continuation differs from audited tokens")


def checked_backend(spec):
    # Runs before loading pretrained weights; every call is checked again at execution.
    tokenizer = load_tokenizer(spec)
    inputs = token_inputs(spec, tokenizer)
    backend, info = create_backend(spec)

    class CheckedBackend:
        def choice(self, prompt, choices, fmt):
            result = backend.choice(prompt, choices, fmt)
            check_output(prompt, result, inputs)
            return result

    return CheckedBackend(), {
        **info,
        "token_inputs_hash": digest(inputs),
        "matched_token_check": True,
    }


def audit_model_records(spec, plan, records, info):
    inputs = token_inputs(spec, load_tokenizer(spec))
    if info.get("token_inputs_hash") != digest(inputs) or not info.get("matched_token_check"):
        raise ValueError("Missing or changed token audit provenance")
    expected = {j["id"]: j for j in jobs_in(plan)}
    for record in records:
        if record["status"] != "error":
            check_output(expected[record["id"]]["row"]["prompt"], record["result"], inputs)


def prepare(spec, directory, tokenizer_check=False):
    """Export complete CPU inputs/oracles, with a manifest explicitly marked design-only."""
    directory = Path(directory)
    if directory.exists() and any(directory.iterdir()):
        raise ValueError("Choose a new or empty design directory")
    plan, summary = build_plan(spec), preview(spec)
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / "config.json", spec)
    write_json(directory / "plan.json", plan)
    write_json(
        directory / "model_inputs.json",
        [
            {"id": j["id"], "prompt": j["row"]["prompt"], "choices": j["row"]["choices"]}
            for j in jobs_in(plan)
        ],
    )
    write_json(directory / "manifest.json", {"engine": ENGINE, "status": "design_only", **summary})
    if tokenizer_check:
        write_json(directory / "tokenizer_audit.json", tokenizer_audit(spec))
    from .possessive_reporting import design_figure

    design_figure(directory / "figures/possessive_design")
    return summary


def run(spec, directory, max_jobs=None, backend_factory=None, checkpoint=None):
    path = Path(directory) / "manifest.json"
    if path.exists() and read_json(path).get("status") == "design_only":
        raise ValueError("CPU design is not a model run; choose a separate run directory")

    def audit_existing(_directory, manifest, records):
        if records and not manifest["synthetic"]:
            audit_model_records(spec, build_plan(spec), records, manifest["backend_info"])

    return run_plan(
        validate_spec(spec),
        build_plan(spec),
        directory,
        max_jobs,
        backend_factory or checked_backend,
        checkpoint,
        artifact_audit=audit_existing,
    )


def read_run(directory):
    directory = Path(directory)
    manifest = read_json(directory / "manifest.json")
    if manifest.get("status") == "design_only":
        raise ValueError("CPU design is not a model run; choose a separate run directory")
    if manifest["protocol"] != PROTOCOL or manifest["engine"] != ENGINE:
        raise ValueError("Not a possessive-control run")
    spec = validate_spec(manifest["config"])
    plan = read_json(directory / "plan.json")
    if digest(plan) != manifest["plan_hash"] or digest(plan) != digest(build_plan(spec)):
        raise ValueError("Possessive-control plan differs from frozen inputs")
    if digest(scientific_spec(spec)) != manifest["config_hash"]:
        raise ValueError("Possessive-control config hash mismatch")
    if manifest["expected_jobs"] != len(jobs_in(plan)):
        raise ValueError("Possessive-control expected coverage changed")
    records = read_records(directory)
    audit_records(records, plan, manifest)
    if not manifest["synthetic"]:
        audit_model_records(spec, plan, records, manifest["backend_info"])
    return manifest, plan, records
