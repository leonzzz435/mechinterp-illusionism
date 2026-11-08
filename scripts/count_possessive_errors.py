"""Post hoc CPU count of error direction in the immutable Your/The archive.

Matches the classification in review_qwen_evidence.py / QWEN_RESULTS.md:80.
Reads saved scores and simulator states only; no model, tokenizer or inference.
Prints deterministic JSON. Never rewrites an existing audit or result report.
"""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from review_possessive_evidence import ARCHIVE, CONFIG_HASH, PLAN_HASH, SHA256
from review_qwen_evidence import archive_files, digest, require
from review_role_evidence import outcome

CATEGORIES = (
    "correct",
    "invalid_or_error",
    "revoked_target_command",
    "other_actor_command",
    "other_command",
)


def classify(row, selected, accepted, status="ok"):
    """Classify relevant-update choices, with the original audit's error precedence."""
    require(
        row["phase"] == "after" and row["relevant_update"],
        "Classification requires a relevant after-update",
    )
    if status != "ok":
        return "invalid_or_error"
    require(selected in row["state"]["commands"], "Unknown selected command")
    target = row["target"]
    require(
        bool(accepted) == (selected in row["state"]["permissions"][target]),
        "Inconsistent accepted flag",
    )
    if accepted:
        return "correct"
    other = next(a for a in row["state"]["permissions"] if a != target)
    if selected == row["before"]["permissions"][target][0]:
        return "revoked_target_command"
    if selected in row["state"]["permissions"][other]:
        return "other_actor_command"
    return "other_command"


def counts(labels):
    histogram = Counter(labels)
    return {
        "n": len(labels),
        "errors": len(labels) - histogram["correct"],
        **{key: histogram[key] for key in CATEGORIES},
    }


def count_errors(path=ARCHIVE, sha256=SHA256):
    files, actual_sha, checked = archive_files(path, sha256)
    manifest = json.loads(files["run/manifest.json"])
    plan = json.loads(files["run/plan.json"])
    saved = json.loads(files["run/analysis.json"])
    raw = [json.loads(line) for line in files["run/records.jsonl"].splitlines()]
    require(manifest["plan_hash"] == digest(plan) == PLAN_HASH, "Frozen plan mismatch")
    require(
        manifest["config_hash"] == CONFIG_HASH
        and manifest["config"]["scenarios"] == list(range(16, 32)),
        "Wrong configuration or cohort",
    )
    require(
        manifest["status"] == saved["status"] == "complete" and not manifest["synthetic"],
        "Requires complete real-model evidence",
    )
    require(digest(raw) == saved["records_hash"], "Record inventory hash mismatch")
    jobs = [j for block in plan["blocks"] for j in block["jobs"]]
    expected = {j["id"]: j for j in jobs}
    require(
        len(expected) == len(jobs) == len(raw) == manifest["expected_jobs"] == 6144,
        "Incomplete or duplicate coverage",
    )
    groups, scenarios, ids = defaultdict(list), defaultdict(lambda: defaultdict(list)), {}
    seen = set()
    for record in raw:
        rid = record["id"]
        require(rid in expected and rid not in seen, "Unknown/duplicate record")
        seen.add(rid)
        require(
            record["job"] == expected[rid] and record["config_hash"] == CONFIG_HASH,
            "Changed record job/configuration",
        )
        require(
            digest({k: v for k, v in record.items() if k != "checksum"})
            == record["checksum"]
            == manifest["records"].get(rid),
            "Record checksum mismatch",
        )
        require(record["status"] == record["result"]["status"] == "ok", "Invalid record")
        row, result = record["job"]["row"], record["result"]
        # Independently reconstruct the state, argmax and executed command from saved inputs.
        accepted = outcome(row, result)
        if row["phase"] != "after" or not row["relevant_update"]:
            continue
        label = classify(row, result["selected_command"], accepted)
        cell = row["frame"] + "/" + row["relation"]
        groups[cell].append(label)
        scenarios[row["scenario_id"]][cell].append(label)
        ids[rid] = {"scenario": row["scenario_id"], "cell": cell, "category": label}
    require(seen == set(expected) == set(manifest["records"]), "Missing recorded jobs")
    expected_cells = {
        f + "/" + r for f in ("your", "the", "reference") for r in ("target", "other")
    }
    require(set(groups) == expected_cells and len(scenarios) == 16, "Wrong counting population")
    require(all(len(v) == 256 for v in groups.values()), "Wrong cell denominator")
    require(
        all(
            set(v) == expected_cells and all(len(x) == 16 for x in v.values())
            for v in scenarios.values()
        ),
        "Incomplete scenario cells",
    )
    for cell, labels in groups.items():
        require(
            counts(labels)["correct"] / len(labels)
            == saved["cells"][cell + "/after_relevant"]["estimate"],
            "Counted accuracy disagrees with original report",
        )
    return {
        "protocol": "possessive-error-direction-posthoc-v1",
        "status": "post_hoc_descriptive",
        "archive_sha256": actual_sha,
        "verified_payloads": checked,
        "verified_records": len(seen),
        "plan_hash": PLAN_HASH,
        "source_commit": manifest["provenance"]["git_commit"],
        "analysis_code_sha256": {
            name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in (
                "count_possessive_errors.py",
                "review_possessive_evidence.py",
                "review_qwen_evidence.py",
                "review_role_evidence.py",
            )
        },
        "model_inference": False,
        "population": "after relevant update, all three frames and both context relations",
        "classification_source": "scripts/review_qwen_evidence.py:381-401; docs/QWEN_RESULTS.md:80",
        "independent_scenarios": 16,
        "scenario_indices": list(range(16, 32)),
        "counted_selections": len(ids),
        "denominators": (
            "n includes correct choices; errors excludes correct; "
            "zero errors is not 0% error composition"
        ),
        "confidence_status": (
            "Descriptive post hoc counts on existing development data; "
            "no new confidence intervals, p-values or frozen candidate decision"
        ),
        "confidence_intervals": None,
        "cells": {k: counts(v) for k, v in sorted(groups.items())},
        "per_scenario": {
            sid: {k: counts(v) for k, v in sorted(cells.items())}
            for sid, cells in sorted(scenarios.items())
        },
        "record_categories": dict(sorted(ids.items())),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", nargs="?", type=Path, default=ARCHIVE)
    parser.add_argument("--sha256", default=SHA256)
    args = parser.parse_args()
    print(json.dumps(count_errors(args.archive, args.sha256), indent=2, sort_keys=True))
