"""Post hoc, CPU-only query-reference sensitivity; never rewrite frozen v1 evidence."""

import argparse
import hashlib
import json
import math
import sys
import tarfile
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from self_model_study.io import digest, file_hash, read_json  # noqa: E402
from self_model_study.pilot_backend import select_command  # noqa: E402
from self_model_study.pilot_reporting import save_figure, setup_plotting  # noqa: E402
from self_model_study.query_reference_analysis import (  # noqa: E402
    cell,
    contrasts,
    pair_report,
    summarize,
)
from self_model_study.query_reference_audit import (  # noqa: E402
    classify_choice,
    parse_input,
    scripted_choices,
)
from self_model_study.query_reference_runtime import verify_freeze  # noqa: E402

EVIDENCE = ROOT / "review/query-reference-results"
OUT = ROOT / "review/query-reference-sensitivity"
VERSION = "query-self-reference-v2-offline"
ANALYSIS_SHA = "eccaf6f8ec3524a415b7d7de089087aac64750537e2b58dd0478b2952aabeb09"
ARCHIVE_SHAS = (
    "6f2da16ae4d121a9434acbab493dfbeff2c8fa2e5f7b017e7ff90c80f4ba86e7",
    "d09c79e9db4954188920b51c9dddd9f005a7423cad92e82ac6fdfb71437c6989",
    "27b794b128d3978e37d7c9da0fcd534479a3672d8ee3c0303fffbc14f95773ad",
    "2a534e189469d647e4c5a6dfe649e8eb782f1759a601a3236684b28d8f7d1274",
    "be7a5fed556d731e0de3b07895fb71060247e4150b70bec51b7d8dd0c3674605",
    "a2eabe16cc93816fd558fead6fb4e2a39ec226a48ff54d8869ebf78df441d42e",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verified_payloads(path, expected):
    require(file_hash(path) == expected, "Evidence archive hash changed")
    with tarfile.open(path) as archive:
        members = archive.getmembers()
        require(all(m.isfile() for m in members), "Non-file archive entry")
        require(len({m.name for m in members}) == len(members), "Duplicate archive path")
        payloads = {m.name: archive.extractfile(m).read() for m in members}
    checks = json.loads(payloads["run/checksums.json"])
    require(
        set(payloads) == {"run/" + p for p in checks} | {"run/checksums.json"},
        "Incomplete internal checksum inventory",
    )
    for name, expected in checks.items():
        require(
            hashlib.sha256(payloads["run/" + name]).hexdigest() == expected,
            "Internal checksum mismatch",
        )
    return payloads


def resolve_selection(candidates):
    """Answer-blind rule: only an exact maximum can win; no arbitrary fallback."""
    require(len({c["command"] for c in candidates}) == len(candidates), "Duplicate command")
    require(bool(candidates), "No candidates")
    for candidate in candidates:
        value = candidate["log_likelihood"]
        require(type(value) in (int, float) and math.isfinite(value), "Invalid/nonfinite score")
        require(type(candidate.get("native_is_greedy")) is bool, "Missing greedy flag")
    top = max(c["log_likelihood"] for c in candidates)
    winners = [c for c in candidates if c["log_likelihood"] == top]
    greedy = [c for c in winners if c["native_is_greedy"]]
    selected = winners[0] if len(winners) == 1 else (greedy[0] if len(greedy) == 1 else None)
    return {
        "score_tie": len(winners) > 1,
        "tied_commands": [c["command"] for c in winners] if len(winners) > 1 else [],
        "selected_command": selected["command"] if selected else None,
        "selection_policy": "exact_max_then_unique_stored_greedy",
        "resolved": selected is not None,
    }


def world_statistics(vectors, eligible=True):
    """Paired world resampling; exploratory family only, no amendment-selection correction."""
    matrix = np.array([vectors[k] for k in ("E", "F", "S")], dtype=float).T
    require(matrix.ndim == 2 and matrix.shape[1] == 3, "Expected E/F/S world vectors")
    require(np.isfinite(matrix).all() and len(matrix) >= 2, "Invalid world vectors")
    n = len(matrix)
    indices = np.random.default_rng(1729).integers(0, n, size=(10000, n))
    result = {}
    for i, name in enumerate(("E", "F", "S")):
        xs = matrix[:, i]
        mean, variance = float(xs.mean()), float(xs.var(ddof=1))
        defined = eligible and variance > 0
        statistic = mean / math.sqrt(variance / n) if defined else None
        raw_p = float(2 * t.sf(abs(statistic), n - 1)) if defined else None
        result[name] = {
            "estimate": mean,
            "ci95": np.quantile(xs[indices].mean(axis=1), [0.025, 0.975]).tolist()
            if eligible
            else None,
            "raw_p": raw_p,
            "t": statistic,
            "df": n - 1 if defined else None,
            "holm_input": raw_p if defined else 1.0,
            "holm_placeholder": not defined,
            "positive_worlds": int((xs > 0).sum()),
            "world_contrasts": xs.tolist(),
            "test_status": "defined"
            if defined
            else ("unresolved_invalid" if not eligible else "zero_variance"),
        }
    previous = 0.0
    for rank, key in enumerate(sorted(result, key=lambda k: result[k]["holm_input"])):
        value = min(1.0, max(previous, (3 - rank) * result[key]["holm_input"]))
        result[key]["holm_p"] = previous = value
    return result, indices


def apply_resolution(observations, row, command):
    """Derived observations only: retain the raw status and never mutate input evidence."""
    parsed = parse_input({"prompt": row["prompt"], "choices": row["choices"]})
    category = classify_choice(parsed, command)
    require(category != "invalid", "Unresolved/invalid derived command")
    require(sum(o["id"] == row["id"] for o in observations) == 1, "Ambiguous record ID")
    return [
        {
            **o,
            "source_status": o["status"],
            "status": "resolved_tie_in_supplement",
            "category": category,
            "correct": category == "correct_target_current",
            "foreign": category == "other_account_current",
        }
        if o["id"] == row["id"]
        else dict(o)
        for o in observations
    ]


def summarize_variant(rows, observations):
    worlds = sorted({o["world_id"] for o in observations})
    by_id = {o["id"]: o for o in observations}
    rows = [r for r in rows if r["world_id"] in worlds]
    require(len(rows) == len(observations) == len(by_id) == len(worlds) * 336, "Partial world")
    groups, primary, world_cells = defaultdict(list), defaultdict(list), defaultdict(list)
    for row in rows:
        obs = by_id[row["id"]]
        key = "/".join((row["stage"], row["queried_owner"], row["query_form"]))
        groups[key].append(obs)
        world_cells[row["world_id"], key].append(obs)
        if row["stage"] == "after_both":
            primary[row["world_id"], row["queried_owner"], row["query_form"]].append(obs)
    vectors, per_world = contrasts(primary, worlds)
    eligible = all(o["category"] != "invalid" for o in observations)
    statistics, indices = world_statistics(vectors, eligible)
    cells = {k: cell(v, eligible=False) for k, v in sorted(groups.items())}
    lookup_cells = {
        k: {
            "correct": v["counts"]["correct_target_current"],
            "n": v["scheduled"],
            "accuracy": v["accuracy"],
            "numerical_pass": v["accuracy"] >= 0.8,
        }
        for k, v in cells.items()
        if k.split("/")[0] in {"before", "snapshot"} and not k.endswith("possessive")
    }
    pairs = {k: v for k, v in pair_report(rows, observations, False).items() if v["lookup_gate"]}
    gate = all(c["numerical_pass"] for c in lookup_cells.values()) and all(
        p["numerical_pass"] for p in pairs.values()
    )
    alias = {}
    for stage in ("before", "snapshot", "after_both"):
        for owner in ("self", "other"):
            for left, right in (("possessive", "owner_name"), ("owner_name", "account_name")):
                xs = np.array(
                    [
                        np.mean([o["correct"] for o in world_cells[w, f"{stage}/{owner}/{left}"]])
                        - np.mean(
                            [o["correct"] for o in world_cells[w, f"{stage}/{owner}/{right}"]]
                        )
                        for w in worlds
                    ]
                )
                alias[f"{stage}/{owner}/{left}_minus_{right}"] = {
                    "estimate": float(xs.mean()),
                    "ci95": np.quantile(xs[indices].mean(axis=1), [0.025, 0.975]).tolist()
                    if eligible
                    else None,
                    "status": "exploratory_descriptive_no_test",
                }
    return {
        "worlds": worlds,
        "n_worlds": len(worlds),
        "recorded_choices": len(observations),
        "eligible_for_exploratory_statistics": eligible,
        "primary": statistics,
        "per_world": per_world,
        "cells": cells,
        "alias_accuracy_contrasts": alias,
        "lookup_cells": lookup_cells,
        "lookup_pairs": pairs,
        "lookup_numerical_pass": gate,
        "analysis_decision": (
            "unresolved_invalid_no_statistics"
            if not eligible
            else ("lookup_gate_failed" if not gate else "exploratory_only_no_confirmatory_decision")
        ),
    }


def analyze():
    verify_freeze()
    require(file_hash(EVIDENCE / "analysis.json") == ANALYSIS_SHA, "Frozen analysis hash changed")
    original = read_json(EVIDENCE / "analysis.json")
    inventory = read_json(EVIDENCE / "verification.json")["blocks"]
    require([b["block"] for b in inventory] == list(range(6)), "Wrong block inventory")
    runs, records = [], []
    for block, expected in zip(inventory, ARCHIVE_SHAS):
        require(block["archive_sha256"] == expected, "Archive inventory changed")
        payloads = verified_payloads(EVIDENCE / block["archive"], expected)
        raw = [json.loads(line) for line in payloads["run/records.jsonl"].splitlines()]
        runs.append(
            (json.loads(payloads["run/manifest.json"]), json.loads(payloads["run/plan.json"]), raw)
        )
        records.extend(raw)
    require(digest(summarize(runs)) == digest(original), "Frozen analysis does not reproduce")
    require(len(records) == len({r["id"] for r in records}) == 16128, "Incomplete records")
    rows = [r["job"]["row"] for r in records]
    ties, shortcuts = (
        [],
        defaultdict(
            lambda: {
                "n": 0,
                "baseline_correct": 0,
                "latest_agreement": 0,
                "first_grant_agreement": 0,
                "unresolved": 0,
            }
        ),
    )
    for record in records:
        row, result = record["job"]["row"], record["result"]
        selected, status = select_command(
            row["choices"], [c["log_likelihood"] for c in result["candidates"]]
        )
        require(status == record["status"] == result["status"], "Stored status differs")
        require(selected == result["selected_command"], "Stored selection differs")
        require(status in {"ok", "tie"}, "Non-tie error cannot be amended")
        policy = resolve_selection(result["candidates"])
        if status == "ok":
            require(policy["selected_command"] == selected, "Policy changed a unique maximum")
        else:
            ties.append({"row": row, "result": result, "resolution": policy})
        if row["stage"] == "after_both":
            parsed = parse_input({"prompt": row["prompt"], "choices": row["choices"]})
            counter = shortcuts[row["queried_owner"] + "/" + row["query_form"]]
            latest = scripted_choices(parsed)["latest_grant_or_first"]
            counter["n"] += 1
            counter["baseline_correct"] += latest == parsed["expected_command"]
            counter["latest_agreement"] += selected == latest
            counter["first_grant_agreement"] += selected == parsed["events"][0]["grant"]
            counter["unresolved"] += status == "tie"
    require(len(ties) == 1, "This supplement requires inspection if tie inventory changes")
    tie = ties[0]
    require(tie["row"]["world_id"] == "query-self-v1:0011", "Unexpected tied world")
    require(tie["resolution"]["resolved"], "No unique stored-greedy maximum; do not force a choice")
    remaining = [o for o in original["observations"] if o["world_id"] != tie["row"]["world_id"]]
    require(len(remaining) == 47 * 336, "Exclusion must remove a whole world")
    variants = {"exclude_world_0011": summarize_variant(rows, remaining)}
    greedy_command = tie["resolution"]["selected_command"]
    derived = apply_resolution(original["observations"], tie["row"], greedy_command)
    variants["v2_stored_greedy"] = summarize_variant(rows, derived)
    other = [c for c in tie["resolution"]["tied_commands"] if c != greedy_command]
    require(len(other) == 1, "Expected exactly two tied candidates for exhaustive assignment bound")
    variants["other_tied_command"] = summarize_variant(
        rows, apply_resolution(original["observations"], tie["row"], other[0])
    )
    for variant in (variants["v2_stored_greedy"], variants["other_tied_command"]):
        require(not variant["lookup_numerical_pass"], "Unexpected changed lookup outcome")
        for key, control in variant["lookup_cells"].items():
            require(
                control["accuracy"] == original["lookup_cells"][key]["accuracy"],
                "Tie resolution changed a lookup cell",
            )
        for key, control in variant["lookup_pairs"].items():
            require(control == original["paired_controls"][key], "Tie resolution changed a pair")
    return {
        "version": VERSION,
        "status": "retrospective_exploratory_supplement",
        "new_model_inference": False,
        "new_cloud_spend": False,
        "original_analysis_sha256": ANALYSIS_SHA,
        "archive_sha256": list(ARCHIVE_SHAS),
        "amendment_sha256": file_hash(ROOT / "docs/QUERY_REFERENCE_V2_AMENDMENT.md"),
        "frozen_v1_decision": original["decision"],
        "frozen_v1_valid_worlds": original["valid_complete_worlds"],
        "frozen_v1_primary": original["primary"],
        "frozen_v1_cells": original["cells"],
        "tie": {
            "id": tie["row"]["id"],
            "world": tie["row"]["world_id"],
            "original_status": "tie",
            "resolution": tie["resolution"],
            "candidates": tie["result"]["candidates"],
            "derived_category": classify_choice(
                parse_input({"prompt": tie["row"]["prompt"], "choices": tie["row"]["choices"]}),
                greedy_command,
            ),
        },
        "variants": variants,
        "original_shortcut_agreement": dict(sorted(shortcuts.items())),
        "limits": "Post hoc policy and outcome-dependent world exclusion; all variants retained. "
        "Nominal paired-world intervals, 10000 draws seed 1729; t df=n-1; Holm E/F/S "
        "within each variant only, not across sensitivity analyses or policy selection. "
        "No confirmatory candidate, functional dissociation or human-illusionism claim.",
    }


def write_outputs(report, destination):
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "analysis.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    labels = {
        "exclude_world_0011": "47 worlds; exclude 0011",
        "v2_stored_greedy": "48 worlds; stored-greedy v2",
        "other_tied_command": "48 worlds; other tied command",
    }
    lines = [
        "# Retrospective query-reference sensitivity",
        "",
        "**Exploratory, after outcome inspection.**",
        "Frozen v1 remains `incomplete_or_invalid_no_inference`; no original record changed.",
        "",
        report["limits"],
        "",
        "## All analyses, no significance-based selection",
        "",
        "| Analysis | Contrast | pp | Nominal 95% interval (pp) | Raw p | Holm p |",
        "|---|---|---:|---|---:|---:|",
    ]
    for name, value in report["frozen_v1_primary"].items():
        lines.append(
            f"| Frozen v1 (48) | {name} | {100 * value['estimate']:.4f} | "
            "withheld | undefined | placeholder only |"
        )
    for key, variant in report["variants"].items():
        for name, value in variant["primary"].items():
            lo, hi = value["ci95"]
            lines.append(
                f"| {labels[key]} | {name} | {100 * value['estimate']:.4f} | "
                f"[{100 * lo:.4f}, {100 * hi:.4f}] | {value['raw_p']:.6g} | {value['holm_p']:.6g} |"
            )
    lines += [
        "",
        "The intervals and p-values above are exploratory. No v1 inference is restored.",
        "Both full-sample assignments keep the lookup decision `lookup_gate_failed`.",
        "",
        "## Original error counts (before tie resolution)",
        "",
        "| Owner / form | Errors | Foreign current | Revoked target | "
        "Revoked other | Tie/invalid |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key, value in sorted(report["frozen_v1_cells"].items()):
        if key.startswith("after_both/"):
            c = value["counts"]
            lines.append(
                f"| {key.removeprefix('after_both/')} | {value['errors_including_missing']} | "
                f"{c['other_account_current']} | {c['revoked_target']} | "
                f"{c['revoked_other']} | {c['invalid']} |"
            )
    lines += [
        "",
        "## Original choices versus the declared shortcut",
        "",
        "| Owner / form | Scheduled | Latest-grant baseline correct | Latest agreement | "
        "First-grant agreement | Unresolved |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key, value in report["original_shortcut_agreement"].items():
        lines.append(
            f"| {key} | {value['n']} | {value['baseline_correct']} | {value['latest_agreement']} | "
            f"{value['first_grant_agreement']} | {value['unresolved']} |"
        )
    lines += [
        "",
        "Agreement counts and the first-grant comparator are retrospective descriptions, "
        "not internal mechanisms.",
        "",
        "Reproduce: `uv run --no-sync python scripts/analyze_query_sensitivity.py`",
        "",
    ]
    (destination / "report.md").write_text("\n".join(lines))
    plt = setup_plotting()
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.8), sharey=True)
    ylabels = [
        "Frozen v1\n(no interval)",
        "47 worlds\nexclude tie world",
        "48 worlds\nstored-greedy v2",
        "48 worlds\nother tied command",
    ]
    for ax, contrast in zip(axes, ("E", "F", "S")):
        ax.scatter(
            100 * report["frozen_v1_primary"][contrast]["estimate"],
            3,
            marker="D",
            color="#555555",
            s=35,
        )
        for i, key in enumerate(labels):
            value = report["variants"][key]["primary"][contrast]
            mean, lo, hi = 100 * np.array([value["estimate"], *value["ci95"]])
            ax.errorbar(
                mean,
                2 - i,
                xerr=[[mean - lo], [hi - mean]],
                fmt="o",
                capsize=4,
                color=("#28758a", "#b66b2c", "#8064a2")[i],
            )
        ax.axvline(0, color="#bbbbbb", linewidth=1)
        ax.set_title(
            {
                "E": "Foreign-command excess (E)",
                "F": "Accuracy cost (F)",
                "S": "Own-minus-other cost (S)",
            }[contrast]
        )
        ax.set_xlabel("Percentage points")
        ax.set_yticks([3, 2, 1, 0], ylabels)
        ax.set_ylim(-0.6, 3.6)
        ax.grid(axis="x", alpha=0.2)
    fig.suptitle("One tied selection: three retrospective sensitivity analyses")
    fig.text(
        0.5,
        0.015,
        "Post hoc paired-world 95% intervals • lookup gates fail • frozen v1 unchanged",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    save_figure(fig, destination / "sensitivity")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    require(
        not args.out.resolve().is_relative_to(EVIDENCE.resolve()), "Cannot overwrite v1 evidence"
    )
    report = analyze()
    write_outputs(report, args.out)
    print(
        json.dumps(
            {
                key: {name: value["estimate"] for name, value in v["primary"].items()}
                for key, v in report["variants"].items()
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
