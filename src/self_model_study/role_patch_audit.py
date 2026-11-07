"""Read-only integrity and technical checks for patch runs, including partial failures."""

import math
from pathlib import Path

from .io import digest, file_hash, read_json, write_json
from .role_patch import (
    DIRECTIONS_HASH,
    REFERENCE_HASH,
    historical_reference,
    random_directions,
    trial_id,
)
from .role_patch_backend import compare_scores


def initialize_and_audit(directory, manifest, records):
    for filename, factory in (
        ("random_directions.json", random_directions),
        ("baseline_reference.json", historical_reference),
    ):
        path = Path(directory) / filename
        if not path.exists() and not records and manifest["status"] == "prepared":
            write_json(path, factory())
    audit_artifacts(directory, manifest, records)


def audit_artifacts(directory, manifest, records):
    directory = Path(directory)
    directions = read_json(directory / "random_directions.json")
    reference = read_json(directory / "baseline_reference.json")
    if digest(directions) != DIRECTIONS_HASH or digest(reference) != REFERENCE_HASH:
        raise ValueError("Frozen directions or historical baseline changed")
    lookup = {r["id"]: r for r in records}
    files = {}
    for record in records:
        result, job = record["result"], record["job"]
        if record["status"] == "error":
            continue  # Explicit execution failures remain available for reporting.
        if job["arm"] == "baseline":
            ref = result["activation_file"]
            if ref["path"] != f"activations/{job['base_id']}.safetensors":
                raise ValueError("Unexpected activation path")
            path = directory / ref["path"]
            if not path.exists() or file_hash(path) != ref["sha256"]:
                raise ValueError("Missing or changed donor activation file")
            files[job["base_id"]] = ref
    for record in records:
        result, job = record["result"], record["job"]
        if record["status"] == "error":
            continue
        arm = job["arm"]
        checks = result["technical_checks"]
        expected_checks = (
            8
            if arm.startswith("random_")
            else {
                "baseline": 1,
                "self": 5,
                "swap": 4,
                "repeat": 1,
            }[arm]
        )
        if len(checks) != expected_checks:
            raise ValueError("Incomplete technical check coverage")
        if result["technical_failure"] != any(not c["passed"] for c in checks):
            raise ValueError("Technical failure flag differs from checks")
        if arm != "baseline":
            own_result = lookup[trial_id(job["base_id"], "baseline")]["result"]
            if (
                result["rendered_prompt"] != own_result["rendered_prompt"]
                or result["prompt_token_ids"] != own_result["prompt_token_ids"]
                or [(c["command"], c["token_ids"]) for c in result["candidates"]]
                != [(c["command"], c["token_ids"]) for c in own_result["candidates"]]
            ):
                raise ValueError("Recipient input differs from its recorded baseline")
        if arm in {"baseline", "self", "repeat"}:
            kind = "historical_baseline" if arm == "baseline" else "null_score_parity"
            ref = (
                reference["records"][job["base_id"]]["result"]
                if arm == "baseline"
                else lookup[trial_id(job["base_id"], "baseline")]["result"]
            )
            expected = compare_scores(result, ref, 0.001 if arm == "baseline" else 0.000001, kind)
            saved = next(c for c in checks if c["kind"] == kind)
            if saved.get("synthetic_bypass"):
                if not manifest["synthetic"]:
                    raise ValueError("Synthetic bypass in purported real-model evidence")
                expected.update(passed=True, synthetic_bypass=True)
            if saved != expected:
                raise ValueError("Saved parity check disagrees with candidate scores")
        for i, candidate in enumerate(result["candidates"]):
            metrics = candidate["patch"]
            pos = metrics["position"]
            context = result["prompt_token_ids"]
            if (
                not 0 <= pos < len(context)
                or context[pos] != 624
                or metrics["layer"] != 13
                or metrics["mode"] != arm
                or (not manifest["synthetic"] and metrics["width"] != 3584)
            ):
                raise ValueError("Patch location differs from protocol")
            if candidate["forward_input_hash"] != digest((context + candidate["token_ids"])[:-1]):
                raise ValueError("Candidate forward identity mismatch")
            if arm in {"baseline", "repeat"}:
                continue
            donor_id = job["base_id"] if arm == "self" else job["donor_base_id"]
            for key, bid in (("recipient", job["base_id"]), ("donor", donor_id)):
                if metrics[key] != {**files[bid], "key": f"candidate_{i}"}:
                    raise ValueError("Patch source does not match frozen donor mapping")
            donor = lookup[trial_id(donor_id, "baseline")]["result"]["candidates"][i]
            if (
                metrics["donor_position"] != donor["patch"]["position"]
                or candidate["command"] != donor["command"]
            ):
                raise ValueError("Donor candidate/position mismatch")
            expected_pass = metrics["prepatch_max_abs_difference"] <= 1e-6
            saved = next(
                c for c in checks if c["kind"] == "prepatch_state_parity" and c["candidate"] == i
            )
            if saved["passed"] != expected_pass:
                raise ValueError("Prepatch parity check mismatch")
            if arm.startswith("random_"):
                index = int(arm.rsplit("_", 1)[1])
                sign = 1 if job["row"]["frame"] == "active" else -1
                if metrics["random_index"] != index or metrics["random_sign"] != sign:
                    raise ValueError("Random direction or sign differs from protocol")
                desired, actual = metrics["desired_norm"], metrics["actual_norm"]
                error = abs(actual - desired) / desired if desired else (0 if actual == 0 else None)
                saved_error = metrics["relative_norm_error"]
                if (error is None) != (saved_error is None) or (
                    error is not None and not math.isclose(error, saved_error, abs_tol=1e-12)
                ):
                    raise ValueError("Rounded norm calculation mismatch")
                saved = next(
                    c for c in checks if c["kind"] == "rounded_random_norm" and c["candidate"] == i
                )
                if saved["passed"] != (error is not None and error <= 0.05):
                    raise ValueError("Rounded norm validity mismatch")
