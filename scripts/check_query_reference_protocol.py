"""Structural checks for an unrun protocol draft, not an input/token preflight."""

import hashlib
import json
import math
import tarfile
from collections import Counter
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "designs/query-self-reference-v1.json"
OUT = ROOT / "review/query-self-reference-protocol-check.json"


def sha(value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check():
    spec = json.loads(SPEC.read_text())
    assert spec["status"] == "review_draft_not_frozen" and not spec["execution_enabled"]
    assert spec["authorized_spend_usd"] == 0
    sample, factorial = spec["sampling"], spec["factorial"]
    worlds = {}
    for index in range(sample["world_count"]):
        sid = f"query-self-v1:{index:04d}"
        worlds[sid] = {
            pool: list(sample[pool])
            if pool == "operator_labels"
            else sorted(
                sample[pool],
                key=lambda label: sha([sample["seed"], sid, pool, label]),
            )[:n]
            for pool, n in (("account_labels", 2), ("operator_labels", 2), ("command_labels", 4))
        }
    fingerprints = [
        (tuple(sorted(w["account_labels"])), tuple(sorted(w["command_labels"])))
        for w in worlds.values()
    ]
    assert len(fingerprints) == len(set(fingerprints)) == 48
    assert all(not set(w["account_labels"]) & set(w["operator_labels"]) for w in worlds.values())
    ordered_ids = sorted(worlds, key=lambda sid: sha([sample["seed"], "nuisance", sid]))
    nuisance = {sid: rank % 8 for rank, sid in enumerate(ordered_ids)}
    assert Counter(nuisance.values()) == {i: 6 for i in range(8)}
    names_as_self = Counter(
        worlds[sid]["operator_labels"][(value >> 2) & 1] for sid, value in nuisance.items()
    )
    assert names_as_self == {"Rowan": 24, "Morgan": 24}
    archives = [
        ROOT / "review/evidence" / (name + ".tar.gz")
        for name in (
            "qwen-78ee6db8adfc4f3e",
            "qwen-role-96787d5e7adf4c4d",
            "qwen-possessive-f2baaa2fb6b74880",
        )
    ] + sorted((ROOT / "review/ownership-permissions-results/archives").glob("*.tar.gz"))
    assert len(archives) == 6
    old_pairs = set()
    before = {}
    for path in archives:
        with tarfile.open(path) as tar:
            plan = json.load(tar.extractfile("run/plan.json"))
            for block in plan["blocks"]:
                for job in block["jobs"]:
                    if job["kind"] == "action":
                        old_pairs.add(tuple(sorted(job["row"]["before"]["permissions"])))
            if path.name == "qwen-possessive-f2baaa2fb6b74880.tar.gz":
                raw = [json.loads(line) for line in tar.extractfile("run/records.jsonl")]
                for frame in ("your", "reference"):
                    rows = [
                        r
                        for r in raw
                        if r["job"]["row"]["phase"] == "before"
                        and r["job"]["row"]["frame"] == frame
                    ]
                    before[frame] = {
                        "correct": sum(int(r["result"]["execution"]["correct"]) for r in rows),
                        "n": len(rows),
                    }
    assert not {fp[0] for fp in fingerprints} & old_pairs
    common = math.prod(len(v) for v in factorial["common"].values())
    counts = {}
    for stage, details in factorial["stages"].items():
        counts[stage] = common * math.prod(len(v) for v in details["extra_factors"].values())
        assert counts[stage] == details["choices_per_world"]
        assert 48 * counts[stage] == details["choices_total"]
    assert sum(counts.values()) == factorial["choices_per_world"] == 336
    assert 48 * sum(counts.values()) == factorial["total_choices"] == 16128
    assert factorial["planned_blocks"] * factorial["worlds_per_block"] == 48
    assert factorial["worlds_per_block"] * 336 == factorial["choices_per_block"]
    # Both updated accounts get distinct grants; crossing event order makes the last
    # grant correct exactly half the time, for either owner. This checks the rule,
    # not an implemented renderer or the ability of a model to resolve its aliases.
    correct = []
    for own, queried, mapping, order in product((0, 1), (0, 1), (0, 1), ((0, 1), (1, 0))):
        target = own if queried == 0 else 1 - own
        grants = (2, 3) if mapping == 0 else (3, 2)
        correct.append(grants[target] == grants[order[-1]])
    assert sum(correct) / len(correct) == 0.5
    previous = json.loads((ROOT / "review/ownership-design-audit/audit.json").read_text())
    return {
        "status": "structural_checks_passed_not_execution_ready",
        "protocol_sha256": file_hash(SPEC),
        "checker_sha256": file_hash(Path(__file__)),
        "model_inference": False,
        "tokenizer_loaded": False,
        "planned_counts_per_world": counts,
        "planned_choices": factorial["total_choices"],
        "unique_account_command_sets": len(fingerprints),
        "historical_account_pair_overlap": 0,
        "nuisance_combination_counts": dict(Counter(nuisance.values())),
        "worlds_per_operator_name_as_self": dict(names_as_self),
        "world_assignment_hash": sha({"worlds": worlds, "nuisance": nuisance}),
        "source_archives": {str(p.relative_to(ROOT)): file_hash(p) for p in archives},
        "rule_level_latest_grant_primary_accuracy": sum(correct) / len(correct),
        "matched_historical_before": before,
        "matched_historical_before_your_minus_reference": (
            before["your"]["correct"] / before["your"]["n"]
            - before["reference"]["correct"] / before["reference"]["n"]
        ),
        "current_before_your_minus_reference": previous["frame_diagnostics"]["before"][
            "posthoc_contrasts"
        ]["your_minus_reference"]["estimate"],
        "current_comparison_source_sha256": file_hash(
            ROOT / "review/ownership-design-audit/audit.json"
        ),
        "not_checked": [
            "full generated input manifest and exact/context-stripped prompt overlap",
            "rendered query aliases and independent simulator agreement",
            "actual tokenizer boundaries, IDs, lengths and chat defaults",
            "scoring, resume, analysis implementation and software tests",
            "sample precision or model performance",
        ],
    }


if __name__ == "__main__":
    result = check()
    OUT.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "output": str(OUT)}, indent=2))
