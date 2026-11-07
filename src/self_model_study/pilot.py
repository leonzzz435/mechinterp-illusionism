"""Bounded Qwen reference/action pilot, isolated from historical confirmation gates."""

import shutil
import time
import uuid
from pathlib import Path

from .action_task import VERSION as ACTION_VERSION
from .action_task import build_design, score_command
from .io import canonical, digest, provenance, read_json, write_json
from .pilot_backend import create_backend, encode_boundary, render_prompt, select_command
from .storage import Journal, read_records, run_lock

PROTOCOL = "qwen-reference-action-v1"
FORMATS = ("plain", "chat")
CATEGORIES = ("ordinary_self", "unusual_self", "open_continuation", "factual_control")
DEFAULT_SPEC = {
    "protocol": PROTOCOL,
    "engine": "qwen-pilot",
    "harness_version": "0.4.13",
    "model": {
        "repo": "Qwen/Qwen2.5-7B-Instruct",
        "revision": "a09a35458c702b33eeacc393d103063234e8bc28",
        "dtype": "bfloat16",
        "max_length": 2048,
    },
    "action_version": ACTION_VERSION,
    "dataset_seed": 1729,
    "scenarios": list(range(8)),
    "formats": list(FORMATS),
    "generation": {"seeds": [42, 43], "temperature": 0.8, "top_p": 0.95, "max_new_tokens": 256},
    "batch_size": 1,
    "num_fewshot": 0,
    "score": "sum_log_likelihood",
    "gate_threshold": 0.8,
    "bootstrap_samples": 10000,
    "max_seconds": 5400,
}


def validate_spec(spec):
    if set(spec) != set(DEFAULT_SPEC):
        raise ValueError("Unknown or incomplete Qwen pilot configuration")
    for key, value in DEFAULT_SPEC.items():
        if key != "max_seconds" and canonical(spec[key]) != canonical(value):
            raise ValueError(f"Frozen pilot field changed: {key}; use a new protocol")
    if type(spec["max_seconds"]) is not int or not 0 < spec["max_seconds"] <= 5400:
        raise ValueError("Qwen invocation limit must be 1–5400 seconds")
    return spec


def load_spec(path):
    return validate_spec(read_json(path))


def scientific_spec(spec):
    return {k: v for k, v in spec.items() if k != "max_seconds"}


def language_prompts():
    rows = read_json(Path(__file__).with_name("pilot_prompts.json"))
    if digest(rows) != "32129c1e0fb1891bb60fb77c78c9e242713135b9a8488665a805855fc25dcc41":
        raise ValueError("Frozen language prompt checksum changed; use a new protocol")
    if len(rows) != 40 or len({r["id"] for r in rows}) != 40:
        raise ValueError("Expected 40 distinct frozen language prompts")
    if any(sum(r["category"] == c for r in rows) != 10 for c in CATEGORIES):
        raise ValueError("Expected ten prompts in each of four categories")
    return rows


def build_plan(spec):
    validate_spec(spec)
    prompts = language_prompts()
    actions = build_design(seed=spec["dataset_seed"], scenarios=8)
    blocks = []
    # Interleave five language prompts with one complete action scenario. Format
    # pairs remain adjacent; interruption cannot selectively finish one format.
    for index in range(8):
        language = []
        for row in prompts[index * 5 : index * 5 + 5]:
            for seed in spec["generation"]["seeds"]:
                for fmt in FORMATS:
                    language.append(
                        {
                            "id": digest([PROTOCOL, row["id"], fmt, seed]),
                            "kind": "language",
                            "row": row,
                            "format": fmt,
                            "seed": seed,
                        }
                    )
        selected = [r for r in actions if int(r["scenario_id"].rsplit(":", 1)[1]) == index]
        choice = [
            {
                "id": digest([PROTOCOL, r["id"], fmt]),
                "kind": "action",
                "row": r,
                "format": fmt,
            }
            for r in selected
            for fmt in FORMATS
        ]
        blocks += [
            {"id": f"language-{index:02d}", "jobs": language},
            {"id": f"action-{index:02d}", "jobs": choice},
        ]
    return {
        "protocol": PROTOCOL,
        "split": "development",
        "prompt_hash": digest(prompts),
        "action_hash": digest(actions),
        "blocks": blocks,
    }


def jobs_in(plan):
    return [job for block in plan["blocks"] for job in block["jobs"]]


def preview(spec):
    plan = build_plan(spec)
    return {
        "protocol": PROTOCOL,
        "valid": True,
        "language_outputs": 160,
        "action_choices": 3072,
        "independent_action_scenarios": 8,
        "human_rating_outputs": 40,
        "blocks": len(plan["blocks"]),
        "plan_hash": digest(plan),
        "prompt_hash": plan["prompt_hash"],
        "max_seconds": spec["max_seconds"],
        "model_inference": False,
    }


def tokenizer_audit(spec, tokenizer=None, *, plan=None):
    """CPU-only optional check using the actual pinned tokenizer, never model weights."""
    if tokenizer is None:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(
            spec["model"]["repo"], revision=spec["model"]["revision"], trust_remote_code=False
        )
    summary = preview(spec) if plan is None else {"plan_hash": digest(plan)}
    plan = build_plan(spec) if plan is None else plan
    lengths, examples, maximum = {}, {}, 0
    for job in jobs_in(plan):
        rendered = render_prompt(tokenizer, job["row"]["prompt"], job["format"])
        examples.setdefault(job["kind"] + "/" + job["format"], rendered)
        if job["kind"] == "action":
            for command in job["row"]["choices"]:
                ctx, cont = encode_boundary(
                    tokenizer, rendered, command, spec["model"]["max_length"]
                )
                lengths.setdefault(command, set()).add(len(cont))
                maximum = max(maximum, len(ctx) + len(cont))
        else:
            length = (
                len(tokenizer.encode(rendered, add_special_tokens=False))
                + spec["generation"]["max_new_tokens"]
            )
            if length > spec["model"]["max_length"]:
                raise ValueError("Generation exceeds context limit; no truncation")
            maximum = max(maximum, length)
    return {
        **summary,
        "tokenizer_checked": True,
        "tokenizer_revision": spec["model"]["revision"],
        "tokenizer_vocabulary_hash": digest(tokenizer.get_vocab()),
        "chat_template": tokenizer.chat_template,
        "chat_template_hash": digest(tokenizer.chat_template),
        "max_context_including_answer_or_generation_reserve": maximum,
        "command_token_lengths": {k: sorted(v) for k, v in sorted(lengths.items())},
        "rendered_examples": examples,
    }


def audit_records(records, plan, manifest, recover=False):
    expected = {j["id"]: j for j in jobs_in(plan)}
    seen = {}
    for record in records:
        job_id = record["id"]
        body = {k: v for k, v in record.items() if k != "checksum"}
        if job_id in seen or job_id not in expected or record["checksum"] != digest(body):
            raise ValueError("Unknown, duplicate or corrupted pilot record")
        if record["job"] != expected[job_id]:
            raise ValueError("Pilot record differs from frozen task plan")
        if record["config_hash"] != manifest["config_hash"]:
            raise ValueError("Pilot record configuration mismatch")
        result = record["result"]
        if record["status"] != result["status"]:
            raise ValueError("Record status disagrees with result")
        job = expected[job_id]
        if job["kind"] == "action" and record["status"] != "error":
            row = job["row"]
            candidates = result["candidates"]
            if [c["command"] for c in candidates] != row["choices"]:
                raise ValueError("Candidate command order differs from task")
            scores = [
                c["log_likelihood"] if c["log_likelihood"] is not None else float("nan")
                for c in candidates
            ]
            selected, status = select_command(row["choices"], scores)
            if result["selected_command"] != selected or result["status"] != status:
                raise ValueError("Saved selection disagrees with likelihood scores")
            if result["execution"] != score_command(row, selected):
                raise ValueError("Saved execution disagrees with simulator")
        seen[job_id] = record["checksum"]
    if any(seen.get(k) != v for k, v in manifest["records"].items()):
        raise ValueError("Missing or changed committed pilot record")
    if not recover and seen != manifest["records"]:
        raise ValueError("Uncommitted records: resume once to recover the atomic journal")
    return seen


def read_run(directory):
    directory = Path(directory)
    manifest, plan = read_json(directory / "manifest.json"), read_json(directory / "plan.json")
    if manifest["protocol"] != PROTOCOL or digest(plan) != manifest["plan_hash"]:
        raise ValueError("Pilot plan checksum mismatch")
    validate_spec(manifest["config"])
    if digest(scientific_spec(manifest["config"])) != manifest["config_hash"]:
        raise ValueError("Pilot configuration checksum mismatch")
    records = read_records(directory)
    audit_records(records, plan, manifest)
    return manifest, plan, records


def run(spec, directory, max_jobs=None, backend_factory=create_backend, checkpoint=None):
    validate_spec(spec)
    return run_plan(spec, build_plan(spec), directory, max_jobs, backend_factory, checkpoint)


def run_plan(
    spec,
    plan,
    directory,
    max_jobs=None,
    backend_factory=create_backend,
    checkpoint=None,
    trial_executor=None,
    artifact_audit=None,
):
    """Shared journaled execution; the caller validates and freezes its own protocol."""
    if max_jobs is not None and (type(max_jobs) is not int or max_jobs < 1):
        raise ValueError("max_jobs must be a positive integer")
    directory = Path(directory)
    with run_lock(directory):
        return _run(
            spec,
            plan,
            directory,
            max_jobs,
            backend_factory,
            checkpoint,
            trial_executor,
            artifact_audit,
        )


def _run(
    spec,
    plan,
    directory,
    max_jobs,
    backend_factory,
    checkpoint,
    trial_executor=None,
    artifact_audit=None,
):
    started = time.monotonic()
    prov = provenance()
    fingerprint = digest(scientific_spec(spec))
    path = directory / "manifest.json"
    if path.exists():
        manifest = read_json(path)
        if manifest["config_hash"] != fingerprint or manifest["plan_hash"] != digest(plan):
            raise ValueError("Cannot resume a changed pilot protocol or dataset")
        if digest(read_json(directory / "plan.json")) != manifest["plan_hash"]:
            raise ValueError("Saved pilot plan checksum mismatch")
        for field in ("source_hash", "python", "packages"):
            if manifest["provenance"][field] != prov[field]:
                raise ValueError(f"Cannot resume after {field} changes")
        if manifest["status"] == "failed":
            raise ValueError("Failed run retained; inspect errors. No automatic retry")
    else:
        write_json(directory / "plan.json", plan)
        # These exports are for inspection, not serialized as an LM request.
        write_json(
            directory / "model_inputs.json",
            [
                {
                    "id": j["id"],
                    "prompt": j["row"]["prompt"],
                    "format": j["format"],
                    **({"choices": j["row"]["choices"]} if j["kind"] == "action" else {}),
                }
                for j in jobs_in(plan)
            ],
        )
        snapshot = directory / "source/self_model_study"
        snapshot.mkdir(parents=True, exist_ok=True)
        for item in Path(__file__).parent.iterdir():
            if item.suffix in {".py", ".json"}:
                shutil.copy2(item, snapshot / item.name)
        root = Path(__file__).resolve().parents[2]
        for name in ("pyproject.toml", "uv.lock"):
            shutil.copy2(root / name, directory / "source" / name)
        manifest = {
            "protocol": plan["protocol"],
            "engine": spec["engine"],
            "run_id": "qwen-" + uuid.uuid4().hex[:16],
            "config": spec,
            "config_hash": fingerprint,
            "plan_hash": digest(plan),
            "provenance": prov,
            "synthetic": True,  # Only a successfully initialized real backend clears this.
            "status": "prepared",
            "records": {},
            "expected_jobs": len(jobs_in(plan)),
            "invocations": [],
        }
        write_json(path, manifest)
    records = read_records(directory)
    manifest["records"] = audit_records(records, plan, manifest, recover=True)
    if artifact_audit:
        artifact_audit(directory, manifest, records)
    if len(records) == manifest["expected_jobs"]:
        manifest["status"] = (
            "complete_with_errors" if any(r["status"] != "ok" for r in records) else "complete"
        )
        write_json(path, manifest)
        return manifest
    invocation = {"max_seconds": spec["max_seconds"], "max_jobs": max_jobs, "new_jobs": 0}
    invocation["started_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    manifest["invocations"].append(invocation)
    manifest["status"] = "running"
    write_json(path, manifest)
    journal = Journal(directory)
    try:
        if checkpoint:
            checkpoint(directory)
        backend, info = backend_factory(spec)
        if "backend_info" in manifest and manifest["backend_info"] != info:
            raise ValueError("Backend/tokenizer changed across invocations")
        manifest["backend_info"] = info
        manifest["synthetic"] = info.get("synthetic", True)
        for block in plan["blocks"]:
            for job in block["jobs"]:
                if job["id"] in manifest["records"]:
                    continue
                if time.monotonic() - started >= spec["max_seconds"] or (
                    max_jobs is not None and invocation["new_jobs"] >= max_jobs
                ):
                    manifest["status"] = "paused"
                    return manifest
                tick = time.monotonic()
                row = job["row"]
                # Only prompt, candidate commands, format and sampling seed reach inference.
                try:
                    result = (
                        trial_executor(backend, job)
                        if trial_executor
                        else (
                            backend.choice(row["prompt"], row["choices"], job["format"])
                            if job["kind"] == "action"
                            else backend.generate(row["prompt"], job["format"], job["seed"])
                        )
                    )
                    if job["kind"] == "action":
                        result["execution"] = score_command(row, result["selected_command"])
                    if result.get("technical_failure"):
                        manifest["status"] = "failed"
                except Exception as exc:
                    result = {
                        "status": "error",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                    # Preserve the failed trial and stop. No silent retry on another prompt.
                    manifest["status"] = "failed"
                record = {
                    "id": job["id"],
                    "job": job,
                    "config_hash": fingerprint,
                    "status": result["status"],
                    "result": result,
                    "seconds": time.monotonic() - tick,
                }
                record["checksum"] = digest(record)
                journal.put(job["id"], record["status"], record)
                manifest["records"][job["id"]] = record["checksum"]
                invocation["new_jobs"] += 1
                write_json(path, manifest)
                if manifest["status"] == "failed":
                    return manifest
            if checkpoint:
                checkpoint(directory)
            print(
                f"Pilot checkpoint: {len(manifest['records'])}/{manifest['expected_jobs']} outputs",
                flush=True,
            )
        manifest["status"] = (
            "complete_with_errors"
            if any(r["status"] != "ok" for r in journal.rows())
            else "complete"
        )
    except KeyboardInterrupt:
        manifest["status"] = "interrupted"
    except Exception as exc:
        manifest["status"] = "failed"
        write_json(directory / "error.json", {"type": type(exc).__name__, "message": str(exc)})
        raise
    finally:
        journal.close()
        invocation["elapsed_seconds"] = time.monotonic() - started
        if manifest.get("backend_info", {}).get("gpu"):
            import torch

            invocation["peak_allocated_bytes"] = torch.cuda.max_memory_allocated()
        write_json(path, manifest)
        if checkpoint:
            checkpoint(directory)
    return manifest
