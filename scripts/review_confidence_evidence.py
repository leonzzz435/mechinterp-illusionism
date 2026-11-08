"""Recompute confidence-pilot decisions from saved scores, without study-package imports.

Checks immutable payloads, actual parent answers, all selections and the two candidate
statistics with a separate question-bootstrap implementation. This is a second software
implementation, not an independent scientist or a second model likelihood calculation.
"""

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import PurePosixPath

import numpy as np
from review_qwen_evidence import archive_files, digest, require

PLAN_HASH = "c6b66f80b92502b237bd3734dfbbc970cf367dfd5b0c72473e6e2bf365bc6e90"


def check_stat(saved, point, draws):
    invalid = int(np.sum(~np.isfinite(draws)))
    require(saved["undefined_bootstrap_draws"] == invalid, "Undefined bootstrap count mismatch")
    require(
        saved["estimate"] is None
        if not np.isfinite(point)
        else saved["estimate"] is not None
        and math.isclose(saved["estimate"], float(point), abs_tol=1e-12),
        "Estimate mismatch",
    )
    if invalid:
        require(saved["ci95"] is None, "Undefined draws require an undefined interval")
    else:
        require(
            saved["ci95"] is not None
            and np.allclose(saved["ci95"], np.quantile(draws, [0.025, 0.975]), atol=1e-12, rtol=0),
            "Question-bootstrap interval mismatch",
        )


def check_candidate_statistics(saved, correct, abstain, confidence):
    """Resample question multiplicities; AUC uses explicit correct/incorrect pairs."""
    n = len(correct)
    selected = np.random.default_rng(1729).choice(n, size=(10000, n), replace=True)
    weights = np.array([np.bincount(row, minlength=n) for row in selected])
    wrong, right = (~correct).sum(1), correct.sum(1)
    zw, zr = ((~correct) & abstain).sum(1), (correct & abstain).sum(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        primary = zw.sum() / wrong.sum() - zr.sum() / right.sum()
        primary_draws = (weights @ zw) / (weights @ wrong) - (weights @ zr) / (weights @ right)
        # Every cross-question pair remains, including rotations of one question.
        comparison = (confidence[:, :, None, None] > confidence[None, None, :, :]).astype(float)
        comparison += 0.5 * (confidence[:, :, None, None] == confidence[None, None, :, :])
        comparison *= correct[:, :, None, None] & (~correct)[None, None, :, :]
        wins = comparison.sum(axis=(1, 3))
        auc = wins.sum() / (right.sum() * wrong.sum())
        auc_draws = ((weights @ wins) * weights).sum(1) / ((weights @ right) * (weights @ wrong))
    check_stat(saved["primary"], primary, primary_draws)
    check_stat(saved["metrics"]["confidence_auroc"], auc, auc_draws)


def audit(path, sha256):
    files, actual, count = archive_files(path, sha256)
    manifest = json.loads(files["run/manifest.json"])
    plan = json.loads(files["run/plan.json"])
    saved = json.loads(files["run/analysis.json"])
    records = [json.loads(line) for line in files["run/records.jsonl"].splitlines()]
    spec = manifest["config"]
    require(manifest["plan_hash"] == digest(plan) == PLAN_HASH, "Frozen plan mismatch")
    frozen = json.loads(files["run/source/self_model_study/confidence_spec_v2.json"])
    require(spec == frozen, "Frozen configuration mismatch")
    require(
        manifest["config_hash"] == digest({k: v for k, v in spec.items() if k != "max_seconds"}),
        "Configuration hash mismatch",
    )
    require(
        manifest["status"] == saved["status"] == "complete"
        and not manifest["synthetic"]
        and saved["complete"],
        "Requires complete real-model evidence",
    )
    source = {
        PurePosixPath(name).name: hashlib.sha256(content).hexdigest()
        for name, content in files.items()
        if name.startswith("run/source/self_model_study/")
    }
    require(digest(source) == manifest["provenance"]["source_hash"], "Source snapshot mismatch")
    ordered = [j for b in plan["blocks"] for j in b["jobs"]]
    jobs = {j["id"]: j for j in ordered}
    require(len(records) == len(jobs) == manifest["expected_jobs"] == 1792, "Coverage mismatch")
    require([r["id"] for r in records] == sorted(jobs), "Missing/duplicate record IDs")
    # JSONL uses journal ID order; walk the frozen execution plan for parent dependencies.
    inventory = {r["id"]: r for r in records}
    by_id, groups, ties = {}, defaultdict(dict), Counter()
    calibration = json.loads(files["run/calibration.json"])
    for job in ordered:
        r = inventory[job["id"]]
        rid, result, row = r["id"], r["result"], r["job"]["row"]
        require(r["job"] == jobs[rid] and rid not in by_id, "Changed/duplicate job")
        require(r["config_hash"] == manifest["config_hash"], "Record config mismatch")
        require(
            digest({k: v for k, v in r.items() if k != "checksum"})
            == r["checksum"]
            == manifest["records"][rid],
            "Record checksum mismatch",
        )
        require(r["status"] == result["status"] == "ok", "Failed selection")
        candidates = result["candidates"]
        require([c["command"] for c in candidates] == row["choices"], "Candidate menu changed")
        require(
            all(
                c["token_count"] == 1
                and c["token_ids"] == [15 + int(c["command"])]
                and math.isfinite(c["log_likelihood"])
                for c in candidates
            ),
            "Invalid token/score",
        )
        top = max(c["log_likelihood"] for c in candidates)
        winners = [c for c in candidates if c["log_likelihood"] == top]
        answer = min(winners, key=lambda c: c["token_ids"][0])["command"]
        tied = len(winners) > 1
        require(
            result["selected_command"] == answer and result["score_tie"] == tied, "Argmax mismatch"
        )
        require(
            result["tied_commands"] == ([c["command"] for c in winners] if tied else []),
            "Tie inventory mismatch",
        )
        if tied:
            ties[row["split"] + "/" + row["phase"]] += 1
        phase, judgment = row["phase"], result["judgment"]
        correct = None if phase == "confidence" else answer == row["correct_number"]
        abstained = answer == "5" if phase == "abstention" else None
        confidence = (int(answer) + 0.5) / 10 if phase == "confidence" else None
        require(
            (judgment["correct"], judgment["abstained"], judgment["confidence"])
            == (correct, abstained, confidence),
            "Judgment mismatch",
        )
        parent = by_id[r["job"]["parent_id"]] if phase == "confidence" else None
        require(
            result["parent_checksum"] == (parent["checksum"] if parent else None),
            "Actual answer dependency mismatch",
        )
        prior = parent["result"]["selected_command"] if parent else None
        prompt = spec["design"]["prompts"][phase].format(
            question=row["question"],
            options="\n".join(f"{i + 1}. {s}" for i, s in enumerate(row["answer_texts"])),
            answer_number=prior,
            answer_text=row["answer_texts"][int(prior) - 1] if prior else None,
        )
        require(result["input_prompt"] == prompt, "Model prompt/actual answer mismatch")
        if row["split"] == "assessment":
            require(result["calibration_checksum"] == digest(calibration), "Calibration changed")
            groups[row["item_id"], row["rotation"]][phase] = (correct, abstained, confidence)
        by_id[rid] = r
    require(dict(ties) == saved["tie_counts"], "Tie count mismatch")
    calibration_records = {
        r["id"]: r["checksum"] for r in records if r["job"]["row"]["split"] == "calibration"
    }
    require(calibration["calibration_record_hashes"] == calibration_records, "Calibration leakage")
    require(len(groups) == saved["paired_variants"] == 512, "Assessment coverage mismatch")
    require(
        len({i for i, _ in groups}) == saved["complete_assessment_questions"] == 128,
        "Question count mismatch",
    )
    correct, abstain, confidence = [], [], []
    for key in sorted(groups):
        stages = groups[key]
        require(set(stages) == {"answer", "confidence", "abstention"}, "Unpaired stages")
        correct.append(stages["answer"][0])
        abstain.append(stages["abstention"][1])
        confidence.append(stages["confidence"][2])
    y, z, v = [np.array(a).reshape(128, 4) for a in (correct, abstain, confidence)]
    check_candidate_statistics(saved, y, z, v)
    counts = {
        "forced_correct": int(y.any(1).sum()),
        "forced_wrong": int((~y).any(1).sum()),
        "abstained": int(z.any(1).sum()),
        "answered": int((~z).any(1).sum()),
    }
    require(counts == saved["feasibility"]["group_questions"], "Feasibility group mismatch")
    usable = min(counts.values()) >= 20 and len(set(confidence)) >= 3
    primary, auc = saved["primary"], saved["metrics"]["confidence_auroc"]
    candidate = (
        usable
        and primary["estimate"] >= 0.1
        and primary["ci95"] is not None
        and primary["ci95"][0] > 0
        and auc["ci95"] is not None
        and auc["ci95"][0] > 0.5
    )
    decision = (
        "measurement_unusable"
        if not usable
        else "behavioral_candidate_for_review"
        if candidate
        else "no_behavioral_candidate"
    )
    require(
        saved["decision"] == decision and saved["feasibility"]["usable"] == usable,
        "Candidate decision mismatch",
    )
    return {
        "archive_sha256": actual,
        "verified_payloads": count,
        "verified_records": len(records),
        "candidate_likelihoods": sum(len(r["result"]["candidates"]) for r in records),
        "independent_assessment_questions": len(y),
        "primary": primary,
        "confidence_auroc": auc,
        "tie_counts": dict(ties),
        "decision": decision,
        "likelihoods_recomputed_by_model": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive")
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.archive, args.sha256), indent=2, sort_keys=True))
