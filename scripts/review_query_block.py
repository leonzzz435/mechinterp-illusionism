"""Offline, observed-block description; preserve the frozen full-sample analysis."""

import argparse
import hashlib
import json
import math
import sys
import tarfile
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from self_model_study.io import digest, file_hash, read_json  # noqa: E402
from self_model_study.query_reference_analysis import summarize  # noqa: E402
from self_model_study.query_reference_audit import (  # noqa: E402
    CATEGORIES,
    classify_choice,
    parse_input,
)
from self_model_study.query_reference_runtime import (  # noqa: E402
    PREFLIGHT,
    jsonl,
    read_run,
)

ARCHIVE_SHA = "6f2da16ae4d121a9434acbab493dfbeff2c8fa2e5f7b017e7ff90c80f4ba86e7"
OUT = ROOT / "review/query-reference-block00-results"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unpack_verified(archive, directory):
    require(file_hash(archive) == ARCHIVE_SHA, "Archive hash changed")
    with tarfile.open(archive) as tar:
        members = tar.getmembers()
        require(len({m.name for m in members}) == len(members), "Duplicate archive path")
        require(all(m.isfile() for m in members), "Non-file archive entry")
        payloads = {m.name: tar.extractfile(m).read() for m in members}
    checks = json.loads(payloads["run/checksums.json"])
    require(
        set(payloads) == {"run/" + p for p in checks} | {"run/checksums.json"},
        "Incomplete checksum inventory",
    )
    for name, expected in checks.items():
        require(
            hashlib.sha256(payloads["run/" + name]).hexdigest() == expected,
            "Internal checksum changed: " + name,
        )
    for name, data in payloads.items():
        target = (directory / name).resolve()
        require(target.is_relative_to(directory.resolve()), "Unsafe archive path")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return len(checks)


def audit(archive):
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        checks = unpack_verified(archive, directory)
        manifest, plan, records = read_run(directory / "run")
        require(
            manifest["status"] == "complete" and not manifest["synthetic"],
            "Expected completed real-model block",
        )
        require(
            manifest["config"]["block_index"] == 0 and len(records) == 2688,
            "Unexpected block or coverage",
        )
        require(
            manifest["provenance"]["git_commit"] == "59061cacf191f737689997b1bb327e75accc71fa",
            "Wrong execution commit",
        )
        full = summarize([(manifest, plan, records)])
        saved = read_json(directory / "run/analysis.json")
        require(digest(full) == digest(saved), "Full-sample analysis differs")
        require(
            full["missing"] == 13440 and not full["inference_eligible"],
            "Partial study incorrectly eligible",
        )

    groups, world_groups, by_id = defaultdict(list), defaultdict(list), {}
    seconds = []
    for record in records:
        row, result = record["job"]["row"], record["result"]
        require(record["status"] == result["status"] == "ok", "Invalid recorded selection")
        scores = {c["command"]: c["log_likelihood"] for c in result["candidates"]}
        require(
            len(scores) == 4 and all(math.isfinite(s) for s in scores.values()),
            "Invalid candidate inventory",
        )
        winners = [c for c in scores if scores[c] == max(scores.values())]
        require(winners == [result["selected_command"]], "Argmax mismatch or tie")
        parsed = parse_input({"prompt": row["prompt"], "choices": row["choices"]})
        category = classify_choice(parsed, winners[0])
        correct = category == "correct_target_current"
        require(correct == result["execution"]["correct"], "Text oracle disagrees")
        obs = {
            "correct": correct,
            "category": category,
            "margin": scores[parsed["expected_command"]] - scores[parsed["foreign_command"]],
        }
        key = "/".join((row["stage"], row["queried_owner"], row["query_form"]))
        groups[key].append(obs)
        world_groups[row["world_id"], key].append(obs)
        by_id[record["id"]] = obs
        seconds.append(record["seconds"])

    cells = {}
    for key, observations in sorted(groups.items()):
        counts = Counter(o["category"] for o in observations)
        n = len(observations)
        applicable = key.startswith("after_both/")
        labeled = {
            c: counts[c] if applicable or not c.startswith("revoked_") else None for c in CATEGORIES
        }
        require(n == full["cells"][key]["recorded"], "Observed denominator differs")
        for cat, count in labeled.items():
            if cat != "invalid":
                require(count == full["cells"][key]["counts"][cat], "Category count differs")
        cells[key] = {
            "n": n,
            "correct": counts["correct_target_current"],
            "accuracy": counts["correct_target_current"] / n,
            "foreign": counts["other_account_current"],
            "foreign_probability": counts["other_account_current"] / n,
            "counts": labeled,
            "margin": sum(o["margin"] for o in observations) / n,
        }

    worlds = sorted({sid for sid, _ in world_groups})
    require(worlds == [f"query-self-v1:{i:04d}" for i in range(8)], "Wrong worlds")
    effects = {}
    for sid in worlds:

        def rate(owner, form, field):
            obs = world_groups[sid, f"after_both/{owner}/{form}"]
            return sum(
                o["correct"] if field == "correct" else o["category"] == "other_account_current"
                for o in obs
            ) / len(obs)

        e = rate("self", "possessive", "foreign") - rate("self", "account_name", "foreign")
        f = rate("self", "account_name", "correct") - rate("self", "possessive", "correct")
        other = rate("other", "account_name", "correct") - rate("other", "possessive", "correct")
        effects[sid] = {"E": e, "F": f, "S": f - other}
        require(
            effects[sid]
            == {k: full["strata"]["after_both"]["per_world"][sid][k] for k in ("E", "F", "S")},
            "World contrast mismatch",
        )
    observed = {
        k: {
            "estimate": sum(v[k] for v in effects.values()) / 8,
            "positive_worlds": sum(v[k] > 0 for v in effects.values()),
            "zero_worlds": sum(v[k] == 0 for v in effects.values()),
            "ci95": None,
            "p_value": None,
        }
        for k in ("E", "F", "S")
    }

    pair_groups = defaultdict(list)
    for entry in jsonl(PREFLIGHT / "pairs.jsonl.gz"):
        if entry["kind"] != "ownership_swaps":
            continue
        pair = entry["pair"]
        a, b = pair["anchor"], pair["counterpart"]
        if a not in by_id:
            require(b not in by_id, "Half an ownership pair")
            continue
        require(b in by_id, "Half an ownership pair")
        if pair["lookup_gate"]:
            key = "ownership/" + "/".join(pair[k] for k in ("stage", "anchor_owner", "query_form"))
            pair_groups[key].append(by_id[a]["correct"] and by_id[b]["correct"])
    pairs = {}
    for key, values in sorted(pair_groups.items()):
        total = full["paired_controls"][key]["scheduled_pairs"]
        require(sum(values) == full["paired_controls"][key]["both_correct"], "Pair count differs")
        require(
            len(values) == total - full["paired_controls"][key]["missing_pairs"],
            "Pair denominator differs",
        )
        pairs[key] = {
            "n": len(values),
            "both_correct": sum(values),
            "rate": sum(values) / len(values),
            "observed_below_80_percent": sum(values) / len(values) < 0.8,
            "best_possible_full_sample_rate": (sum(values) + total - len(values)) / total,
        }
    require(len(pairs) == 8, "Incomplete paired gate inventory")
    return {
        "status": "complete_block_partial_study",
        "new_inference": False,
        "archive_sha256": ARCHIVE_SHA,
        "verified_internal_checksums": checks,
        "full_analysis_recomputed_sha256": digest(full),
        "recorded_choices": len(records),
        "valid_complete_worlds": 8,
        "scheduled_worlds": 48,
        "unrun_choices": full["missing"],
        "technical_errors": 0,
        "ties": 0,
        "decision": full["decision"],
        "inferential_results": "withheld",
        "runtime_seconds": manifest["invocations"][0]["elapsed_seconds"],
        "selection_seconds_total": sum(seconds),
        "peak_allocated_bytes": manifest["invocations"][0]["peak_allocated_bytes"],
        "cells": cells,
        "observed_world_contrasts": effects,
        "observed_block_effects": observed,
        "observed_lookup_pairs": pairs,
        "limit": "Observed eight-world denominators describe this block only. They do not "
        "replace the frozen full-sample endpoint, thresholds or missing-data rule.",
    }


def outputs(result, destination):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    destination.mkdir(parents=True, exist_ok=True)
    (destination / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Block 00: descriptive observations, not a full-sample decision",
        "",
        "The block contains 2,688 valid selections in eight complete worlds. The frozen "
        "study requires 48 worlds / 16,128 selections. No confidence intervals, p-values "
        "or passing decision are issued for this subset.",
        "",
        "The archived fixed-sample report retains 13,440 unrun cases as administrative "
        "missingness. Its percentages use all scheduled cases and are **not observed "
        "eight-world accuracies**. The table below uses only this complete block; neither "
        "the frozen report nor its decision has been changed.",
        "",
        "| Stage / owner / query form | Correct / observed | Accuracy | Foreign-current |",
        "|---|---:|---:|---:|",
    ]
    for key, c in result["cells"].items():
        lines.append(
            f"| {key} | {c['correct']}/{c['n']} | {100 * c['accuracy']:.2f}% | "
            f"{c['foreign']}/{c['n']} |"
        )
    lines += [
        "",
        "## Descriptive contrasts after both updates",
        "",
        "Same prespecified formulas, averaged over the observed eight worlds only. "
        "These are interim descriptions, not the full-sample primary estimates.",
        "",
        "| Contrast | Observed estimate (pp) | Positive worlds | Zero worlds |",
        "|---|---:|---:|---:|",
    ]
    for key, c in result["observed_block_effects"].items():
        lines.append(
            f"| {key} | {100 * c['estimate']:+.4f} | "
            f"{c['positive_worlds']}/8 | {c['zero_worlds']}/8 |"
        )
    lines += ["", "| World | E (pp) | F (pp) | S (pp) |", "|---|---:|---:|---:|"]
    for sid, c in result["observed_world_contrasts"].items():
        lines.append(f"| {sid} | {100 * c['E']:+.3f} | {100 * c['F']:+.3f} | {100 * c['S']:+.3f} |")
    lines += [
        "",
        "## Paired lookup controls",
        "",
        "The 80% threshold belongs to the full sample. Below-threshold observed "
        "block rates are concerns, not a final failed-study decision. The last column "
        "is an algebraic upper bound if every unrun pair were correct, not a prediction.",
        "",
        "| Control | Both correct / observed pairs | Rate | Best possible full sample |",
        "|---|---:|---:|---:|",
    ]
    for key, c in result["observed_lookup_pairs"].items():
        lines.append(
            f"| {key} | {c['both_correct']}/{c['n']} | {100 * c['rate']:.2f}% | "
            f"{100 * c['best_possible_full_sample_rate']:.2f}% |"
        )
    lines += [
        "",
        "## Categorical outcomes after both updates",
        "",
        "| Owner / form | Correct | Foreign current | Revoked target | Revoked other | Other |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key, c in result["cells"].items():
        if key.startswith("after_both/"):
            counts = c["counts"]
            lines.append(
                "| "
                + key.removeprefix("after_both/")
                + " | "
                + " | ".join(
                    str(counts[k])
                    for k in (
                        "correct_target_current",
                        "other_account_current",
                        "revoked_target",
                        "revoked_other",
                        "remaining_valid_command",
                    )
                )
                + " |"
            )
    lines += [
        "",
        "Revoked categories are not applicable before changes or in history-free "
        "snapshots; their null entries in the JSON are not observed zeros.",
        "",
        "![Observed block accuracies](observed-accuracy.png)",
        "",
        "Reproduce with `uv run --no-sync python scripts/review_query_block.py`. "
        "This checks the archive, native output/token provenance, text oracle, independent "
        "score argmax, simulator outcomes, frozen pair inventory and the saved full-sample "
        "analysis. It performs no model inference.",
        "",
    ]
    (destination / "observed-report.md").write_text("\n".join(lines))

    plt.rcParams.update({"svg.hashsalt": "query-block00-observed", "font.size": 10})
    columns = [
        (o, f) for o in ("self", "other") for f in ("possessive", "owner_name", "account_name")
    ]
    stages = ("before", "snapshot", "after_both")
    values = np.array(
        [[100 * result["cells"][f"{s}/{o}/{f}"]["accuracy"] for o, f in columns] for s in stages]
    )
    fig, ax = plt.subplots(figsize=(11, 4.9))
    view = ax.imshow(values, vmin=0, vmax=100, cmap="YlGnBu", aspect="auto")
    for i, stage in enumerate(stages):
        for j, (owner, form) in enumerate(columns):
            c = result["cells"][f"{stage}/{owner}/{form}"]
            ax.text(
                j,
                i,
                f"{values[i, j]:.1f}%\n{c['correct']}/{c['n']}",
                ha="center",
                va="center",
                color="white" if values[i, j] >= 65 else "black",
            )
    ax.set_xticks(
        range(6),
        [
            "Your",
            "Own operator\nname",
            "Own account\nname",
            "Their",
            "Other operator\nname",
            "Other account\nname",
        ],
    )
    ax.set_yticks(range(3), ["Before updates", "Current snapshot", "After both updates"])
    ax.set_title("Query reference changes performance — observed block 00", pad=18)
    fig.colorbar(view, ax=ax, label="Correct selections (%)", fraction=0.03, pad=0.025)
    fig.text(
        0.5,
        0.02,
        "Eight of 48 planned worlds • descriptive only • "
        "no confidence intervals or final gate decision",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    for ext in ("svg", "pdf", "png"):
        metadata = (
            {"Date": None}
            if ext == "svg"
            else ({"CreationDate": None, "ModDate": None} if ext == "pdf" else {})
        )
        fig.savefig(destination / f"observed-accuracy.{ext}", dpi=180, metadata=metadata)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    archive = OUT / "qwen-query-00-4edce03e18d645e7.tar.gz"
    result = audit(archive)
    outputs(result, args.out)
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "status",
                    "recorded_choices",
                    "technical_errors",
                    "decision",
                    "observed_block_effects",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
