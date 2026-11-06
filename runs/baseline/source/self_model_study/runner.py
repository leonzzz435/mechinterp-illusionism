"""Bounded runs, audit metadata, development calibration and confirmation gates."""

import os
import shutil
import time
import uuid
from pathlib import Path

from .backend import historical, make_backend, resolve_assets
from .data import build_dataset, dataset_summary
from .interventions import conditions
from .io import canonical, digest, file_hash, provenance, read_json, source_hash, write_json
from .storage import Journal, read_records, run_lock


def scientific_config(config):
    return {
        k: v
        for k, v in config.items()
        if k not in {"max_seconds", "max_jobs", "protocol", "evidence_run"}
    }


def rows_for(config):
    if config["phase"] == "reference":
        return [
            {
                "id": "historical:target",
                "scenario_id": "historical:target",
                "kind": "language",
                "family": "historical",
                "view": "unspecified",
                "split": "development",
                "template_id": "historical",
                "expected": None,
                "prompt": historical()["target_prompt"],
            }
        ]
    return build_dataset(config["dataset"], config["split"])


def jobs(config, rows):
    # Baselines first; all interventions use paired RNG seeds for the same row/replicate.
    for condition in conditions(config):
        for row in rows:
            seeds = config["generation"]["seeds"] if row["kind"] == "language" else [config["seed"]]
            for seed in seeds:
                trial_id = digest([row["id"], condition["id"], seed])
                yield trial_id, row, condition, seed


def expected_jobs(config, rows):
    return len(conditions(config)) * sum(
        len(config["generation"]["seeds"]) if r["kind"] == "language" else 1 for r in rows
    )


def baseline_gate(config, records):
    """Denominator includes errors; each view, name role and position must pass."""
    result = {}
    for family in config["dataset"]["families"]:
        baseline = [
            r
            for r in records
            if r["row"]["family"] == family and r["condition"]["id"] == "baseline"
        ]
        checks = {}
        for field, values in [
            ("view", ["self", "other"]),
            ("identity", [0, 1]),
            ("swapped", [False, True]),
            ("rotation", [0, 1, 2, 3]),
            ("expected", list("ABCD")),
        ]:
            for value in values:
                subset = [r for r in baseline if r["row"][field] == value]
                checks[f"{field}:{value}"] = (
                    sum(r.get("result", {}).get("correct", False) for r in subset) / len(subset)
                    if subset
                    else 0.0
                )
        result[family] = {"checks": checks, "passed": min(checks.values(), default=0) >= 0.8}
    return result


def verify_evidence(config, evidence):
    evidence = Path(evidence)
    manifest = read_json(evidence / "manifest.json")
    old = manifest["config"]
    if manifest["config_hash"] != digest(scientific_config(old)):
        raise ValueError("Evidence configuration checksum mismatch")
    if manifest.get("status") != "complete" or old["backend"] != "torch":
        raise ValueError(
            "Evidence must be a completed real-model run; mock/partial runs cannot qualify"
        )
    if old["split"] != "validation" or old["phase"] != "exploratory":
        raise ValueError(
            "Evidence must be an exploratory validation run with single-feature results"
        )
    if manifest["provenance"]["source_hash"] != source_hash():
        raise ValueError("Source changed since validation; rerun validation under the current code")
    for key in ("model", "sae", "dataset", "seed", "generation", "calibration", "statistics"):
        if old[key] != config[key]:
            raise ValueError(f"Validation and target differ in {key}")
    if config["dataset"]["counts"] != {"development": 40, "validation": 40, "test": 100}:
        raise ValueError("Confirmation requires the preregistered 40/40/100 scenario counts")
    calibration = read_json(evidence / "calibration.json")
    if not calibration["passed"] or not manifest.get("health", {}).get("passed"):
        raise ValueError("Calibration or post-run baseline integrity failed")
    if calibration["direction_hash"] != file_hash(evidence / "directions.npz"):
        raise ValueError("Evidence directions changed")
    records = read_records(evidence)
    if manifest["records_hash"] != digest(records):
        raise ValueError("Evidence journal checksum mismatch")
    if any(r["status"] != "ok" for r in records):
        raise ValueError("Evidence contains execution failures")
    expected = {j[0] for j in jobs(old, rows_for(old))}
    if {r["trial_id"] for r in records} != expected:
        raise ValueError("Evidence trial coverage is incomplete")
    gate = baseline_gate(config, records)
    if not all(v["passed"] for v in gate.values()):
        raise ValueError(f"Baseline capability gate failed: {canonical(gate)}")
    available = {r["condition"]["id"] for r in records}
    required = {c["id"] for c in conditions(config)}
    if config["phase"] == "combined":
        required = {x for x in required if not x.startswith("combined:")}
        required |= {
            f"feature:{fid}@{strength:+.3f}"
            for fid in (2728, 10230)
            for strength in config["interventions"]["strengths"]
        }
    if not required <= available:
        raise ValueError("Requested conditions lack single-condition validation evidence")
    return manifest, records, calibration, gate


def freeze_protocol(config, evidence, destination):
    if config["phase"] != "confirmatory" or config["backend"] != "torch":
        raise ValueError("Only real confirmatory configurations can be frozen")
    manifest, records, calibration, gate = verify_evidence(config, evidence)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    artifact_dir = destination.with_suffix(".artifacts")
    if destination.exists() or artifact_dir.exists():
        raise ValueError(
            "Protocol or its artifact directory already exists; never overwrite a freeze"
        )
    payload = {
        "schema_version": 1,
        "config_hash": digest(scientific_config(config)),
        "config": scientific_config(config),
        "source_hash": source_hash(),
        "assets": manifest["assets"],
        "packages": manifest["provenance"]["packages"],
        "python": manifest["provenance"]["python"],
        "evidence_run_id": manifest["run_id"],
        "evidence_hash": digest(records),
        "calibration": calibration,
        "gate": gate,
        "primary_conditions": [c["id"] for c in conditions(config) if c["kind"] != "none"],
        "primary_outcomes": [
            "self_accuracy_delta",
            "other_accuracy_delta",
            "self_minus_other_delta",
        ],
        "test_policy": "One run_id per frozen protocol; resume that run, never overwrite",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    payload["protocol_hash"] = digest(payload)
    artifact_dir.mkdir()
    for name in ("directions.npz", "calibration.json"):
        shutil.copy2(Path(evidence) / name, artifact_dir / name)
    with destination.open("x") as stream:
        stream.write(canonical(payload) + "\n")
    return payload


def verify_protocol(config):
    if not config["protocol"]:
        raise ValueError("Test access requires a frozen protocol")
    path = Path(config["protocol"])
    payload = read_json(path)
    if payload["protocol_hash"] != digest(
        {k: v for k, v in payload.items() if k != "protocol_hash"}
    ):
        raise ValueError("Protocol checksum mismatch")
    if payload["config_hash"] != digest(scientific_config(config)):
        raise ValueError("Configuration changed after protocol freeze")
    if payload["source_hash"] != source_hash():
        raise ValueError("Implementation changed after freeze")
    artifacts = path.with_suffix(".artifacts")
    if file_hash(artifacts / "directions.npz") != payload["calibration"]["direction_hash"]:
        raise ValueError("Frozen direction checksum mismatch")
    if read_json(artifacts / "calibration.json") != payload["calibration"]:
        raise ValueError("Frozen calibration changed")
    return payload


def claim_protocol(path, run_id):
    claim = Path(str(path) + ".claim.json")
    try:
        fd = os.open(claim, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        if read_json(claim).get("run_id") != run_id:
            raise ValueError(
                "This protocol has already opened its test set in another run"
            ) from None
    else:
        with os.fdopen(fd, "w") as stream:
            stream.write(canonical({"run_id": run_id}) + "\n")


def run(config, directory, backend_factory=make_backend):
    directory = Path(directory)
    with run_lock(directory):
        return _run(config, directory, backend_factory)


def _run(config, directory, backend_factory):
    start = time.monotonic()
    deadline = start + config["max_seconds"]
    manifest_path = directory / "manifest.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else None
    fingerprint = digest(scientific_config(config))
    prov = provenance()
    protocol = verify_protocol(config) if config["phase"] == "confirmatory" else None
    evidence = None
    if config["phase"] == "combined":
        evidence, _, _, _ = verify_evidence(config, config["evidence_run"])
    if manifest:
        if (
            manifest["config_hash"] != fingerprint
            or manifest["provenance"]["source_hash"] != source_hash()
        ):
            raise ValueError("Cannot resume after scientific configuration or source changes")
        if (
            manifest["provenance"]["packages"] != prov["packages"]
            or manifest["provenance"]["python"] != prov["python"]
        ):
            raise ValueError("Cannot resume with a different Python/package environment")
        if manifest["status"] == "complete":
            return manifest
    if protocol and (
        protocol["packages"] != prov["packages"] or protocol["python"] != prov["python"]
    ):
        raise ValueError("Confirmation requires the validation Python/package environment")
    assets = resolve_assets(
        config,
        manifest["assets"]
        if manifest
        else protocol["assets"]
        if protocol
        else evidence["assets"]
        if evidence
        else None,
    )
    if not manifest:
        manifest = {
            "schema_version": 1,
            "run_id": str(uuid.uuid4()),
            "config": config,
            "config_hash": fingerprint,
            "assets": assets,
            "provenance": prov,
            "synthetic": config["backend"] == "mock",
            "status": "initializing",
            "invocations": [],
        }
        write_json(manifest_path, manifest)
        # A dirty working tree is reproducible from the bundle, not just its commit label.
        snapshot = directory / "source" / "self_model_study"
        snapshot.mkdir(parents=True, exist_ok=True)
        for source in Path(__file__).parent.iterdir():
            if source.suffix in {".py", ".json"}:
                shutil.copy2(source, snapshot / source.name)
        root = Path(__file__).resolve().parents[2]
        for name in ("pyproject.toml", "uv.lock"):
            if (root / name).exists():
                shutil.copy2(root / name, directory / "source" / name)
    if protocol:
        claim_protocol(config["protocol"], manifest["run_id"])
        manifest["protocol_hash"] = protocol["protocol_hash"]
        write_json(directory / "protocol.json", protocol)
        for name in ("calibration.json", "directions.npz"):
            target = directory / name
            frozen = Path(config["protocol"]).with_suffix(".artifacts") / name
            if target.exists() and file_hash(target) != file_hash(frozen):
                raise ValueError("Run calibration differs from frozen calibration")
            if not target.exists():
                shutil.copy2(frozen, target)
    if evidence:
        for name in ("calibration.json", "directions.npz"):
            source = Path(config["evidence_run"]) / name
            target = directory / name
            if target.exists() and file_hash(target) != file_hash(source):
                raise ValueError("Combined run calibration differs from single-condition evidence")
            if not target.exists():
                shutil.copy2(source, target)
    rows = rows_for(config)
    manifest["dataset"] = dataset_summary(rows)
    manifest["expected_jobs"] = expected_jobs(config, rows)
    write_json(directory / "dataset.json", rows)
    write_json(directory / "config.json", config)
    journal = Journal(directory)
    invocation = {
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "max_seconds": config["max_seconds"],
        "max_jobs": config["max_jobs"],
        "new_jobs": 0,
    }
    manifest["invocations"].append(invocation)
    manifest["status"] = "running"
    write_json(manifest_path, manifest)
    backend = None
    try:
        backend = backend_factory(config, assets)
        manifest["backend_info"] = backend.info
        calibration = backend.prepare(directory, deadline)
        if (
            config["backend"] == "torch"
            and not calibration["passed"]
            and config["phase"] != "reference"
        ):
            manifest["status"] = "blocked_calibration"
            return manifest
        for trial_id, row, condition, seed in jobs(config, rows):
            if journal.contains(trial_id):
                continue
            if time.monotonic() >= deadline or (
                config["max_jobs"] is not None and invocation["new_jobs"] >= config["max_jobs"]
            ):
                manifest["status"] = "paused"
                break
            tick = time.monotonic()
            record = {
                "trial_id": trial_id,
                "row": row,
                "condition": condition,
                "seed": seed,
                "synthetic": config["backend"] == "mock",
            }
            try:
                record["result"] = backend.evaluate(row, condition, seed)
                record["status"] = "ok"
            except Exception as exc:
                # A failed trial remains failed; resume never silently reruns it.
                record.update(
                    status="error", error={"type": type(exc).__name__, "message": str(exc)}
                )
            record["seconds"] = time.monotonic() - tick
            journal.put(trial_id, record["status"], record)
            invocation["new_jobs"] += 1
            if record["status"] == "error":
                manifest["status"] = "paused_after_error"
                break
        else:
            manifest["status"] = "complete"
        manifest["health"] = backend.health_check()
        if not manifest["health"]["passed"]:
            manifest["status"] = "failed_health"
    except KeyboardInterrupt:
        manifest["status"] = "interrupted"
    except TimeoutError as exc:
        manifest.update(status="paused_calibration", error=str(exc))
    except Exception as exc:
        manifest.update(status="failed", error={"type": type(exc).__name__, "message": str(exc)})
        raise
    finally:
        records = journal.rows()
        journal.close()
        invocation["elapsed_seconds"] = time.monotonic() - start
        manifest["completed_jobs"] = len(records)
        manifest["error_jobs"] = sum(r["status"] != "ok" for r in records)
        manifest["records_hash"] = digest(records)
        if records:
            per_job = sum(r["seconds"] for r in records) / len(records)
            manifest["estimated_remaining_seconds"] = per_job * (
                manifest["expected_jobs"] - len(records)
            )
        write_json(manifest_path, manifest)
    return manifest
