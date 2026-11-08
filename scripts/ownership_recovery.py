"""Audit and continue the three recorded upload failures; never rerun saved trials."""

import gc
import json
import re
import shutil
import time
from functools import partial
from pathlib import Path

from huggingface_hub import snapshot_download


def continuation_backend(spec, directory):
    """Compare metadata in its persisted JSON form without changing the scorer."""
    from self_model_study import ownership
    from self_model_study.io import canonical, read_json, write_json

    inputs, _ = ownership.frozen_inputs(spec, ownership.build_plan(spec))
    backend, live_info = ownership.checked_backend(spec)
    # Transformers uses integer id2label keys; JSON objects necessarily use strings.
    # Retain every field and value. Never ignore a model/tokenizer/hardware difference.
    info = json.loads(canonical(live_info))
    saved = read_json(Path(directory) / "manifest.json")["backend_info"]
    changed = sorted(
        k
        for k in saved.keys() | info.keys()
        if k not in saved or k not in info or saved[k] != info[k]
    )
    write_json(
        Path(directory) / "recovery/backend-comparison.json",
        {"saved": saved, "current": info, "equal": saved == info, "changed_fields": changed},
    )
    if saved != info:
        raise ValueError(f"Backend/tokenizer changed across invocations: {changed}")

    class CheckedChoices:
        def choice(self, prompt, choices, format_name):
            result = backend.choice(prompt, choices, format_name)
            # Supplying a factory bypasses ownership.run's default live token check.
            # Preserve that exact check here, using only the model-input fields.
            ownership.check_output({"prompt": prompt, "choices": choices}, result, inputs)
            return result

    return CheckedChoices(), info


def validate_spec(spec):
    if (
        spec.get("engine") != "qwen-ownership-recovery"
        or spec.get("protocol") != "ownership-replication-v1"
        or spec.get("max_seconds") != 1800
        or spec.get("hard_timeout_seconds") != 2700
        or spec.get("original_execution_commit") != "23f9ea8f6ebc31e4a6f3590481b8b8099bc1c2b5"
        or spec.get("artifact_repo") != "zett13/mechinterp-illusionism-results"
        or not re.fullmatch(r"[0-9a-f]{40}", spec.get("artifact_revision", ""))
        or [b["block_index"] for b in spec.get("blocks", [])] != [0, 1, 2]
    ):
        raise ValueError("Recovery must preserve the recorded tranche and bounded invocation")
    for i, block in enumerate(spec["blocks"]):
        if (
            not re.fullmatch(rf"qwen-ownership-{i:02d}-[0-9a-f]{{16}}", block["run_name"])
            or block["record_count"] != [4992, 5376, 4608][i]
            or block["expected_jobs"] != 6144
            or any(
                not re.fullmatch(r"[0-9a-f]{64}", block[k])
                for k in ("manifest_sha256", "error_sha256", "records_hash")
            )
        ):
            raise ValueError("Recovery source differs from the inspected failed jobs")
    return spec


def audit_snapshot(directory, expected):
    from self_model_study.io import digest, file_hash, read_json, source_hash
    from self_model_study.ownership import read_run

    directory = Path(directory)
    for name, key in (("manifest.json", "manifest_sha256"), ("error.json", "error_sha256")):
        if file_hash(directory / name) != expected[key]:
            raise ValueError("Recovery source manifest/error changed")
    if (directory / "checksums.json").exists():
        for name, checksum in read_json(directory / "checksums.json").items():
            path = (directory / name).resolve()
            if not path.is_relative_to(directory.resolve()) or file_hash(path) != checksum:
                raise ValueError("Recovery archive checksum mismatch")
    manifest, plan, records = read_run(directory)
    error = read_json(directory / "error.json")
    if (
        manifest["status"] != "failed"
        or manifest["provenance"]["source_hash"] != source_hash()
        or manifest["config"]["block_index"] != expected["block_index"]
        or len(records) != expected["record_count"]
        or manifest["expected_jobs"] != expected["expected_jobs"]
        or not 0 < len(records) < manifest["expected_jobs"]
        or digest(records) != expected["records_hash"]
        or any(r["status"] != "ok" or r["result"].get("technical_failure") for r in records)
        or error.get("type") != "ConnectionError"
        or not error.get("message", "").startswith(
            "Rate limited: Request error: HTTP status client error (429 Too Many Requests), "
            "domain: https://cas-server-direct.xethub.hf.co/"
        )
    ):
        raise ValueError("Only the audited upload-only failures can be continued")
    return {
        "record_count": len(records),
        "remaining": manifest["expected_jobs"] - len(records),
        "records_hash": digest(records),
        "run_id": manifest["run_id"],
    }


def prepare_resume(source, destination, expected):
    """Change only a new working copy after verifying the immutable original snapshot."""
    from self_model_study.io import provenance, read_json, write_json

    source, destination = Path(source), Path(destination)
    audit = audit_snapshot(source, expected)
    shutil.copytree(source, destination)
    history = destination / "recovery"
    history.mkdir(exist_ok=False)
    shutil.copy2(destination / "manifest.json", history / "original-manifest.json")
    for name in ("error.json", "checksums.json"):
        if (destination / name).exists():
            shutil.move(destination / name, history / ("original-" + name))
    manifest = read_json(destination / "manifest.json")
    manifest["status"] = "paused"
    write_json(destination / "manifest.json", manifest)
    write_json(
        history / "audit.json",
        {
            **audit,
            "source": expected,
            "previous_status": "failed",
            "new_status": "paused",
            "reason": "Verified upload-only 429; all recorded selections valid and retained",
            "continuation_provenance": provenance(),
        },
    )
    return audit


def run_group(spec, directory, checkpoint):
    from self_model_study.io import write_json
    from self_model_study.ownership import configuration, run
    from self_model_study.ownership_reporting import analyze_tranche, export

    validate_spec(spec)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    staging = directory.parent / ".restore"
    started = time.monotonic()
    # Verify every block before loading weights. The parent worker's private-repo check
    # and pinned download prevent changing the recovery source while a job is running.
    snapshot_download(
        spec["artifact_repo"],
        repo_type="dataset",
        revision=spec["artifact_revision"],
        allow_patterns=[b["run_name"] + "/run/**" for b in spec["blocks"]],
        local_dir=staging,
        max_workers=1,
    )
    for block in spec["blocks"]:
        audit_snapshot(staging / block["run_name"] / "run", block)
    directories = []
    for block in spec["blocks"]:
        target = directory / f"block-{block['block_index']:02d}"
        prepare_resume(staging / block["run_name"] / "run", target, block)
        directories.append(target)
    shutil.rmtree(staging)
    state = {"status": "running", "original_records": 14976, "new_records": 0, "blocks": []}
    write_json(directory / "recovery-state.json", state)
    checkpoint(directory)
    try:
        for block, target in zip(spec["blocks"], directories):
            remaining = int(spec["max_seconds"] - (time.monotonic() - started))
            if remaining <= 0:
                state["status"] = "paused"
                break
            config = {**configuration(block["block_index"]), "max_seconds": remaining}
            try:
                result = run(
                    config,
                    target,
                    checkpoint=checkpoint,
                    backend_factory=partial(continuation_backend, directory=target),
                )
            finally:
                export(
                    target,
                    directory.parent / "exports" / f"block-{block['block_index']:02d}.tar.gz",
                )
            added = len(result["records"]) - block["record_count"]
            state["new_records"] += added
            state["blocks"].append(
                {
                    "block_index": block["block_index"],
                    "status": result["status"],
                    "new_records": added,
                }
            )
            write_json(directory / "recovery-state.json", state)
            checkpoint(directory)
            if result["status"] != "complete":
                state["status"] = result["status"]
                break
            gc.collect()
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        else:
            state["status"] = "complete"
        analyze_tranche(directories, directory / "combined")
        return state
    except Exception:
        state["status"] = "failed"
        raise
    finally:
        state["elapsed_seconds"] = time.monotonic() - started
        write_json(directory / "recovery-state.json", state)
        checkpoint(directory)
