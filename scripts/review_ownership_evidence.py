"""Reaggregate completed ownership evidence offline, without study-package imports.

Checks archived bytes, journal parity, preserved records, simulator/score choices,
all categorical cells and the paired-world statistic. No model inference; not an
independent human review or independent computation of model likelihoods.
"""

import gzip
import hashlib
import json
import math
import sqlite3
import statistics
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from review_qwen_evidence import archive_files, digest, require
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "review/ownership-permissions-results"


def audit():
    provenance = json.loads((RESULTS / "provenance.json").read_text())
    report = json.loads((RESULTS / "analysis.json").read_text())
    preflight = json.loads((ROOT / "review/ownership-permissions-preflight.json").read_text())
    recovery = json.loads((ROOT / "configs/qwen-ownership-recovery.json").read_text())
    cells, worlds, all_records, blocks = defaultdict(Counter), defaultdict(dict), {}, []
    for artifact, original in zip(provenance["archives"], recovery["blocks"], strict=True):
        files, checksum, checked = archive_files(ROOT / artifact["path"], artifact["sha256"])
        manifest = json.loads(files["run/manifest.json"])
        plan = json.loads(files["run/plan.json"])
        raw = [json.loads(line) for line in files["run/records.jsonl"].splitlines()]
        index = artifact["block_index"]
        require(
            index == original["block_index"] == manifest["config"]["block_index"], "Block mismatch"
        )
        require(
            manifest["status"] == "complete" and not manifest["synthetic"], "Not complete real data"
        )
        require(
            digest(plan) == manifest["plan_hash"] == preflight["blocks"][index]["plan_hash"],
            "Plan drift",
        )
        source = {
            Path(n).name: hashlib.sha256(b).hexdigest()
            for n, b in files.items()
            if n.startswith("run/source/self_model_study/")
        }
        require(
            digest(source) == manifest["provenance"]["source_hash"] == report["source_hash"],
            "Source drift",
        )
        inputs = json.loads(
            gzip.decompress(files["run/source/ownership/ownership-permissions-inputs.json.gz"])
        )
        comparison = json.loads(files["run/recovery/backend-comparison.json"])
        require(
            comparison["equal"]
            and comparison["saved"] == comparison["current"] == manifest["backend_info"],
            "Backend drift",
        )
        old = json.loads(files["run/recovery/original-manifest.json"])
        records = {r["id"]: r for r in raw}
        require(
            len(raw) == len(records) == manifest["expected_jobs"] == 6144,
            "Coverage/duplicate failure",
        )
        retained = [r for r in raw if r["id"] in old["records"]]
        require(
            len(retained) == original["record_count"]
            and digest(retained) == original["records_hash"],
            "Original records changed",
        )
        with TemporaryDirectory() as tmp:
            dbfile = Path(tmp) / "trials.sqlite"
            dbfile.write_bytes(files["run/trials.sqlite"])
            with sqlite3.connect(f"file:{dbfile}?mode=ro", uri=True) as db:
                journal = [
                    json.loads(payload)
                    for (payload,) in db.execute("SELECT payload FROM trials ORDER BY id")
                ]
            require(journal == raw, "SQLite/JSONL disagreement")
        jobs = {j["id"]: j for b in plan["blocks"] for j in b["jobs"]}
        require(set(records) == set(jobs) == set(manifest["records"]), "Inventory mismatch")
        for r in raw:
            rid, row, result = r["id"], r["job"]["row"], r["result"]
            require(rid not in all_records and r["job"] == jobs[rid], "Duplicate/changed job")
            require(
                digest({k: v for k, v in r.items() if k != "checksum"})
                == r["checksum"]
                == manifest["records"][rid],
                "Record checksum mismatch",
            )
            require(r["status"] == result["status"] == "ok", "Technical error")
            require(r["config_hash"] == manifest["config_hash"], "Configuration mismatch")
            frozen = inputs[row["prompt"]]
            require(
                all(result[k] == frozen[k] for k in ("rendered_prompt", "prompt_token_ids")),
                "Prompt token drift",
            )
            candidates = result["candidates"]
            require([c["command"] for c in candidates] == row["choices"], "Candidate mismatch")
            for c in candidates:
                require(
                    c["token_ids"] == frozen["continuations"][c["command"]]
                    and c["token_count"] == len(c["token_ids"]),
                    "Command token drift",
                )
            scores = [c["log_likelihood"] for c in candidates]
            require(
                all(math.isfinite(s) for s in scores) and scores.count(max(scores)) == 1,
                "Invalid score/tie",
            )
            selected = row["choices"][scores.index(max(scores))]
            require(selected == result["selected_command"], "Selection mismatch")
            state = deepcopy(row["before"])
            event, target = row["event"], row["target"]
            require(state["permissions"][event["actor"]] == [event["revoke"]], "Invalid revoke")
            if row["phase"] == "after":
                state["permissions"][event["actor"]] = [event["grant"]]
            require(state == row["state"], "Simulator state mismatch")
            other = next(a for a in state["permissions"] if a != target)
            relevant = event["actor"] == target
            require(
                relevant == row["relevant_update"]
                and [row["expected_command"]] == state["permissions"][target],
                "Oracle mismatch",
            )
            correct = selected in state["permissions"][target]
            category = (
                "correct_target_current"
                if correct
                else "other_account_current"
                if selected in state["permissions"][other]
                else "revoked_target"
                if row["phase"] == "after" and relevant and selected == event["revoke"]
                else "other_valid_command"
            )
            if correct:
                state["markers"][target] += 1
            expected_execution = {
                "actor": target,
                "command": selected,
                "valid_command": True,
                "accepted": correct,
                "correct": correct,
                "reason": "executed" if correct else "permission_denied",
                "state_after": state,
            }
            require(result["execution"] == expected_execution, "Execution mismatch")
            stage = (
                "before"
                if row["phase"] == "before"
                else "after_relevant"
                if relevant
                else "after_irrelevant"
            )
            key = f"{row['frame']}/{row['relation']}/{stage}"
            cells[key][category] += 1
            worlds[row["scenario_id"]].setdefault(key, Counter())[category] += 1
            all_records[rid] = r
        blocks.append(
            {
                "block_index": index,
                "archive_sha256": checksum,
                "payload_checksums": checked,
                "records": len(raw),
                "preserved_records": len(retained),
                "new_records": len(raw) - len(retained),
                "backend_comparison_passed": True,
                "journal_jsonl_equal": True,
            }
        )
    require(
        len(all_records) == 18432 and len(worlds) == 48 and len(blocks) == 3, "Incomplete tranche"
    )
    require(
        digest(sorted(all_records.values(), key=lambda r: r["id"])) == report["records_hash"],
        "Combined record hash mismatch",
    )
    require(set(cells) == set(report["cells"]), "Cell inventory mismatch")
    for key, counts in cells.items():
        saved = report["cells"][key]
        require(all(counts[c] == n for c, n in saved["counts"].items()), "Category count mismatch")
        require(
            sum(counts.values()) == saved["scheduled"] == saved["recorded"], "Denominator mismatch"
        )
    contrasts = []
    for sid, groups in sorted(worlds.items()):
        frame_values = []
        for frame in ("your", "their", "neutral"):
            target, other = (
                groups[f"{frame}/{relation}/after_relevant"] for relation in ("target", "other")
            )
            frame_values.append(
                target["other_account_current"] / sum(target.values())
                - other["other_account_current"] / sum(other.values())
            )
        value = statistics.mean(frame_values)
        require(
            math.isclose(value, report["primary"]["world_contrasts"][sid], abs_tol=1e-12),
            "World contrast mismatch",
        )
        contrasts.append(value)
    xs = np.array(contrasts)
    sampled = np.random.default_rng(1729).integers(0, 48, size=(10000, 48))
    interval = np.quantile(xs[sampled].mean(axis=1), [0.025, 0.975]).tolist()
    estimate = statistics.mean(contrasts)
    p = float(2 * t.sf(abs(estimate) / (statistics.stdev(contrasts) / math.sqrt(48)), df=47))
    require(
        math.isclose(estimate, report["primary"]["estimate"], abs_tol=1e-12), "Primary mismatch"
    )
    require(
        np.allclose(interval, report["primary"]["ci95"], rtol=0, atol=1e-12), "Bootstrap mismatch"
    )
    require(math.isclose(p, report["primary"]["unadjusted_t_p"], abs_tol=1e-12), "Test mismatch")
    failed = {
        key: counts["correct_target_current"] / sum(counts.values())
        for key, counts in cells.items()
        if not key.endswith("after_relevant")
        and counts["correct_target_current"] / sum(counts.values()) < 0.8
    }
    require(report["controls_pass"] == (not failed), "Control decision mismatch")
    return {
        "status": "verified",
        "blocks": blocks,
        "choices": len(all_records),
        "worlds": len(worlds),
        "primary": {"estimate": estimate, "ci95": interval, "unadjusted_t_p": p},
        "world_signs": dict(
            Counter("positive" if x > 0 else "negative" if x < 0 else "zero" for x in contrasts)
        ),
        "failed_control_cells": failed,
        "primary_10pp_threshold_met": estimate >= 0.1,
        "limits": (
            "Saved-score reaggregation; no new inference or independent likelihood calculation. "
            "One model/template only; no Holm-family or wording-equivalence decision."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
