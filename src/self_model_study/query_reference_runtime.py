"""Frozen query-reference execution using the existing native scorer and journal."""

import gzip
import json
import math
from pathlib import Path

from .action_task import score_command
from .io import canonical, digest, file_hash, read_json, write_json
from .pilot import audit_records, jobs_in, run_plan, scientific_spec
from .pilot_backend import create_backend, encode_boundary, render_prompt, select_command
from .query_reference import PROTOCOL, ROOT, SPEC_PATH, SPEC_SHA256, build_inputs, specification
from .storage import read_records

ENGINE = "qwen-query-reference"
PREFLIGHT = ROOT / "review/query-self-reference-preflight"
FREEZE = ROOT / "designs/query-self-reference-v1.freeze.json"


def jsonl(path):
    with gzip.open(path, "rt") as stream:
        return [json.loads(line) for line in stream]


def configuration(block):
    if type(block) is not int or block not in range(6):
        raise ValueError("Query-reference has exactly six blocks")
    return {
        "engine": ENGINE,
        "protocol": PROTOCOL,
        "design_sha256": SPEC_SHA256,
        "block_index": block,
        "world_indices": list(range(block * 8, (block + 1) * 8)),
        "model": specification()["model"],
        "batch_size": 1,
        "generation": {},
        "harness_version": "0.4.13",
        "max_seconds": 5400,
    }


def validate_spec(spec):
    expected = configuration(spec.get("block_index"))
    if set(spec) != set(expected) or any(
        canonical(spec[k]) != canonical(v) for k, v in expected.items() if k != "max_seconds"
    ):
        raise ValueError("Changed query-reference configuration")
    if type(spec["max_seconds"]) is not int or not 0 < spec["max_seconds"] <= 5400:
        raise ValueError("Invocation limit must be 1–5400 seconds")
    return spec


def build_plan(spec):
    validate_spec(spec)
    _, rows = build_inputs()
    return {
        "protocol": PROTOCOL,
        "block_index": spec["block_index"],
        "blocks": [
            {
                "id": f"query-self-v1:{i:04d}",
                "jobs": [
                    {"id": r["id"], "kind": "action", "format": "chat", "row": r}
                    for r in rows
                    if r["world_index"] == i
                ],
            }
            for i in spec["world_indices"]
        ],
    }


def source_inventory():
    files = sorted((ROOT / "src/self_model_study").glob("*.py"))
    files += [
        ROOT / n
        for n in (
            "pyproject.toml",
            "uv.lock",
            "scripts/prepare_query_reference.py",
            "scripts/hf_jobs.py",
            "scripts/hf_worker.py",
        )
    ]
    files += sorted((ROOT / "tests").glob("test_query_reference*.py"))
    files += sorted((ROOT / "configs").glob("qwen-query-reference-*.json"))
    return {str(p.relative_to(ROOT)): file_hash(p) for p in files}


def verify_inputs():
    audit = read_json(PREFLIGHT / "audit.json")
    if file_hash(SPEC_PATH) != SPEC_SHA256 or audit["protocol_sha256"] != SPEC_SHA256:
        raise ValueError("Scientific specification drift")
    for name, checksum in audit["artifacts"].items():
        if file_hash(PREFLIGHT / name) != checksum:
            raise ValueError(f"Prepared input artifact changed: {name}")
    for name, checksum in audit["source_files"].items():
        if file_hash(ROOT / name) != checksum:
            raise ValueError(f"Prepared generator/token source changed: {name}")
    return audit


def freeze(destination=FREEZE):
    """Seal the unchanged draft's scientific content; do not grant paid execution."""
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Freeze already exists; no overwrite")
    audit = verify_inputs()
    worlds, rows = build_inputs()
    if worlds != read_json(PREFLIGHT / "worlds.json") or rows != jsonl(
        PREFLIGHT / "manifest.jsonl.gz"
    ):
        raise ValueError("Generator differs from prepared manifest")
    result = {
        "protocol": PROTOCOL,
        "status": "frozen_before_assessment",
        "model_inference": False,
        "paid_launch_authorized": False,
        "authorized_spend_usd": 0,
        "scientific_spec_sha256": SPEC_SHA256,
        "administrative_note": (
            "Original draft metadata preserved; this record seals its scientific content, "
            "not a spend allocation."
        ),
        "preflight_sha256": file_hash(PREFLIGHT / "audit.json"),
        "artifacts": audit["artifacts"],
        "source_files": source_inventory(),
        "plans": {str(i): digest(build_plan(configuration(i))) for i in range(6)},
        "runtime_rules": {
            "invalid_outcomes": (
                "Count as failures; any missing, tied, failed or nonfinite selection prevents "
                "inferential eligibility. Report descriptive all-scheduled contrasts."
            ),
            "scoring": (
                "lm-eval 0.4.13 native summed full-command likelihood; batch 1, eager attention, "
                "FP32 softmax, BF16 model, no logits/KV cache, no normalization or EOS"
            ),
            "failure": (
                "Preserve failed record and stop on score/input/source drift or exceptions; "
                "exact ties remain invalid records without arbitrary winner. "
                "Failed runs are not retried automatically."
            ),
            "control_intervals": (
                "Nominal world-bootstrap intervals only with all 48 valid complete worlds; "
                "lookup gates use the prespecified point thresholds."
            ),
            "example": (
                "world 0000, assignment 0, after_both, grant mapping 0, event order [0,1], "
                "option rotation 0; both owners and all three aliases"
            ),
        },
    }
    write_json(destination, result)
    return result


def verify_freeze():
    frozen = read_json(FREEZE)
    if frozen.get("status") != "frozen_before_assessment" or frozen.get("protocol") != PROTOCOL:
        raise ValueError("No valid query-reference freeze")
    if frozen["scientific_spec_sha256"] != file_hash(SPEC_PATH):
        raise ValueError("Frozen specification changed")
    if frozen["preflight_sha256"] != file_hash(PREFLIGHT / "audit.json"):
        raise ValueError("Frozen input preflight changed")
    if frozen["source_files"] != source_inventory():
        raise ValueError("Frozen execution source changed")
    audit = verify_inputs()
    if frozen["artifacts"] != audit["artifacts"]:
        raise ValueError("Frozen artifact inventory changed")
    return frozen


def frozen_tokens(spec, plan):
    frozen = verify_freeze()
    if frozen["plans"][str(spec["block_index"])] != digest(plan):
        raise ValueError("Plan differs from frozen inventory")
    expected = {j["id"] for j in jobs_in(plan)}
    tokens = {r["id"]: r for r in jsonl(PREFLIGHT / "tokens.jsonl.gz") if r["id"] in expected}
    if set(tokens) != expected:
        raise ValueError("Incomplete frozen tokens")
    return tokens


def check_output(row, result, expected):
    for key in ("rendered_prompt", "prompt_token_ids"):
        if result.get(key) != expected[key]:
            raise ValueError("Executed prompt differs from frozen input")
    candidates = result.get("candidates", [])
    if len(candidates) != 4 or [c["command"] for c in candidates] != row["choices"]:
        raise ValueError("Incomplete or reordered candidate scores")
    for c, token in zip(candidates, expected["candidates"]):
        if any(c.get(k) != token[k] for k in ("command", "token_ids", "token_count")):
            raise ValueError("Executed candidate differs from frozen input")
    scores = [
        c["log_likelihood"] if c.get("log_likelihood") is not None else math.nan for c in candidates
    ]
    selected, status = select_command(row["choices"], scores)
    if (result.get("selected_command"), result.get("status")) != (selected, status):
        raise ValueError("Selection disagrees with full-command scores")


def check_tokenizer(tokenizer, jobs, tokens):
    audit = read_json(PREFLIGHT / "audit.json")["tokenizer"]
    if (
        digest(tokenizer.get_vocab()) != audit["vocabulary_sha256"]
        or digest(tokenizer.chat_template) != audit["chat_template_sha256"]
    ):
        raise ValueError("Tokenizer/template drift before weights load")
    for job in jobs:
        row, saved = job["row"], tokens[job["id"]]
        rendered = render_prompt(tokenizer, row["prompt"], "chat")
        if rendered != saved["rendered_prompt"]:
            raise ValueError("Chat defaults changed")
        for c in saved["candidates"]:
            ctx, cont = encode_boundary(tokenizer, rendered, c["command"], 2048)
            if ctx != saved["prompt_token_ids"] or cont != c["token_ids"]:
                raise ValueError("Tokenizer input drift before weights load")


def checked_backend(spec):
    from transformers import AutoTokenizer

    plan = build_plan(spec)
    tokens = frozen_tokens(spec, plan)
    tokenizer = AutoTokenizer.from_pretrained(
        spec["model"]["repo"], revision=spec["model"]["tokenizer_revision"], trust_remote_code=False
    )
    check_tokenizer(tokenizer, jobs_in(plan), tokens)
    backend, info = create_backend(spec)
    check_tokenizer(backend.tokenizer, jobs_in(plan), tokens)
    backend.lm.logits_cache = False
    backend.lm.model.config.use_cache = False
    return backend, {
        **info,
        "model_config": backend.lm.model.config.to_dict(),
        "logits_cache": False,
        "kv_cache": False,
        "freeze_sha256": file_hash(FREEZE),
        "preflight_sha256": file_hash(PREFLIGHT / "audit.json"),
    }


def safe_error_value(value):
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite": repr(value)}
    if isinstance(value, dict):
        return {k: safe_error_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [safe_error_value(v) for v in value]
    return value


def execute_checked(backend, job, tokens):
    row = job["row"]
    result = backend.choice(row["prompt"], row["choices"], "chat")
    for candidate in result.get("candidates", []):
        value = candidate.get("log_likelihood")
        if isinstance(value, float) and not math.isfinite(value):
            candidate["log_likelihood"], candidate["nonfinite"] = None, repr(value)
    try:
        check_output(row, result, tokens[job["id"]])
    except (ValueError, KeyError, TypeError) as exc:
        return {
            "status": "error",
            "selected_command": None,
            "technical_failure": str(exc),
            "raw_output": safe_error_value(result),
        }
    if result["status"] == "invalid_scores":
        result["technical_failure"] = "Nonfinite scores; stop without retry"
    return result


def run(spec, directory, max_jobs=None, backend_factory=None, checkpoint=None):
    validate_spec(spec)
    plan = build_plan(spec)
    tokens = frozen_tokens(spec, plan)

    def factory(config):
        backend, info = (backend_factory or checked_backend)(config)
        if backend_factory is not None and not info.get("synthetic", False):
            raise ValueError("Injected test backend must be marked synthetic")
        return backend, info

    def audit_existing(_directory, manifest, records):
        if not manifest["synthetic"] and manifest["backend_info"]["freeze_sha256"] != file_hash(
            FREEZE
        ):
            raise ValueError("Freeze changed across invocations")
        for r in records:
            if r["status"] != "error":
                check_output(r["job"]["row"], r["result"], tokens[r["id"]])

    return run_plan(
        spec,
        plan,
        directory,
        max_jobs,
        factory,
        checkpoint,
        trial_executor=lambda backend, job: execute_checked(backend, job, tokens),
        artifact_audit=audit_existing,
    )


def read_run(directory):
    directory = Path(directory)
    manifest, plan = read_json(directory / "manifest.json"), read_json(directory / "plan.json")
    spec = validate_spec(manifest["config"])
    if (
        manifest["engine"] != ENGINE
        or manifest["protocol"] != PROTOCOL
        or digest(plan) != manifest["plan_hash"]
        or plan != build_plan(spec)
        or digest(scientific_spec(spec)) != manifest["config_hash"]
    ):
        raise ValueError("Saved query-reference run differs from frozen protocol")
    tokens = frozen_tokens(spec, plan)
    records = read_records(directory)
    audit_records(records, plan, manifest)
    if manifest["synthetic"] != manifest.get("backend_info", {}).get("synthetic", True):
        raise ValueError("Synthetic/model provenance flags disagree")
    if manifest["expected_jobs"] != len(jobs_in(plan)):
        raise ValueError("Incorrect expected coverage")
    if manifest["status"] == "complete" and (
        len(records) != len(jobs_in(plan)) or any(r["status"] != "ok" for r in records)
    ):
        raise ValueError("False complete status")
    if not manifest["synthetic"] and manifest["backend_info"]["freeze_sha256"] != file_hash(FREEZE):
        raise ValueError("Saved freeze provenance differs")
    for r in records:
        if r["status"] != "error":
            check_output(r["job"]["row"], r["result"], tokens[r["id"]])
            if r["result"]["execution"] != score_command(
                r["job"]["row"], r["result"]["selected_command"]
            ):
                raise ValueError("Saved simulator outcome differs")
    return manifest, plan, records
