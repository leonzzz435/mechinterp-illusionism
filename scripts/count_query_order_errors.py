"""CPU-only descriptive counts: error direction by update order and paired-world signs."""

import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

from analyze_query_stages import (
    ARCHIVE_SHAS,
    FORMS,
    OWNERS,
    ROOT,
    TIED_WORLD,
    audit_record,
    file_hash,
    load_records,
    read_json,
    require,
)

STAGES = ROOT / "review/query-reference-stages/analysis.json"
STAGES_SHA = "12d845d4f485da6022c5160479f7fa6bc223438fbb40efd9ccdd3b6a3de16052"
OUT = ROOT / "review/query-reference-order-errors"
CATEGORIES = (
    "correct_target_current",
    "other_account_current",
    "revoked_target",
    "revoked_other",
    "invalid",
)
CONTRASTS = (
    "after_minus_snapshot/self/possessive",
    "after_minus_snapshot/possessive/self_minus_other",
)


def sign_counts(values):
    return {
        "negative": sum(x < 0 for x in values),
        "positive": sum(x > 0 for x in values),
        "zero": sum(x == 0 for x in values),
    }


def count_variant(records, variant, saved):
    groups, worlds = defaultdict(list), defaultdict(list)
    for record in records:
        row = record["job"]["row"]
        if variant == "exclude_world_0011" and row["world_id"] == TIED_WORLD:
            continue
        entry = audit_record(record, variant)
        if row["query_form"] == "possessive" and row["stage"] in {"snapshot", "after_both"}:
            worlds[row["world_id"], row["stage"], row["queried_owner"]].append(entry["correct"])
        if row["stage"] != "after_both":
            continue
        p = entry["parsed"]
        order = "target_last" if p["events"][-1]["actor"] == p["target"] else "target_first"
        groups[f"{row['queried_owner']}/{row['query_form']}/{order}"].append(entry)
    expected_keys = {
        f"{o}/{f}/{order}"
        for o in OWNERS
        for f in FORMS
        for order in ("target_last", "target_first")
    }
    require(set(groups) == expected_keys, "Incomplete order split")
    cells = {}
    for key, entries in sorted(groups.items()):
        require(len(entries) == 16 * saved["n_worlds"], "Unbalanced order cell")
        counts = Counter(e["category"] for e in entries)
        require(set(counts) <= set(CATEGORIES), "Unexpected response category")
        n, correct = len(entries), counts["correct_target_current"]
        first = sum(e["selected"] == e["parsed"]["events"][0]["grant"] for e in entries)
        latest = sum(e["selected"] == e["parsed"]["events"][-1]["grant"] for e in entries)
        require(
            first + latest + counts["revoked_target"] + counts["revoked_other"] + counts["invalid"]
            == n,
            "Response partition does not sum",
        )
        cells[key] = {
            "n": n,
            "counts": {c: counts[c] for c in CATEGORIES},
            "errors_including_invalid": n - correct,
            "accuracy": correct / n,
            "foreign_fraction_of_errors": counts["other_account_current"] / (n - correct)
            if n != correct
            else None,
            "foreign_is": "first_grant" if key.endswith("target_last") else "latest_grant",
            "first_grant_agreement": first,
            "latest_grant_agreement": latest,
            "latest_grant_correct": sum(
                e["parsed"]["events"][-1]["grant"] == e["parsed"]["expected_command"]
                for e in entries
            ),
        }
    world_ids = saved["worlds"]
    vectors = {key: [] for key in CONTRASTS}
    for w in world_ids:
        changes = {}
        for owner in OWNERS:
            before = worlds[w, "snapshot", owner]
            after = worlds[w, "after_both", owner]
            require(len(before) == 16 and len(after) == 32, "Incomplete world pairing")
            changes[owner] = Fraction(sum(after), len(after)) - Fraction(sum(before), len(before))
        vectors[CONTRASTS[0]].append(changes["self"])
        vectors[CONTRASTS[1]].append(changes["self"] - changes["other"])
    signs = {}
    for key, values in vectors.items():
        require(
            [float(x) for x in values] == saved["contrasts"][key]["world_values"],
            "Raw-count signs do not reproduce saved world contrasts",
        )
        signs[key] = {
            **sign_counts(values),
            "n_worlds": len(values),
            "world_values": {w: float(x) for w, x in zip(world_ids, values)},
        }
    return {"cells": cells, "signs": signs, "n_worlds": saved["n_worlds"]}


def analyze():
    require(file_hash(STAGES) == STAGES_SHA, "Original stage analysis changed")
    saved, records = read_json(STAGES), load_records()
    variants = {
        name: count_variant(records, name, saved["variants"][name])
        for name in ("frozen_v1", "exclude_world_0011", "v2_stored_greedy", "other_tied_command")
    }
    for name, variant in variants.items():
        for owner in OWNERS:
            for form in FORMS:
                a, b = [
                    variant["cells"][f"{owner}/{form}/{order}"]
                    for order in ("target_last", "target_first")
                ]
                full = saved["variants"][name]["cells"][f"after_both/{owner}/{form}"]
                require(a["n"] + b["n"] == full["n"], "Order counts do not sum")
                require(
                    a["counts"]["correct_target_current"] + b["counts"]["correct_target_current"]
                    == full["correct"],
                    "Correct counts do not sum",
                )
    return {
        "status": "post_hoc_descriptive_counts_no_new_tests_or_decision",
        "new_model_inference": False,
        "source_stage_sha256": STAGES_SHA,
        "archive_sha256": list(ARCHIVE_SHAS),
        "script_sha256": file_hash(Path(__file__)),
        "variants": variants,
        "limits": "Signs describe the named world contrast, not a sign test "
        "or independent replication. "
        "Both after-both order cells are equally weighted. Foreign is relative to the queried "
        "account: its current command is the first grant when target-last and the latest grant "
        "when target-first. Raw tied selections stay invalid; derived policies remain post hoc. "
        "The after-both named controls are diagnostics, not additional frozen lookup gates.",
    }


def write_outputs(result, out):
    out.mkdir(parents=True, exist_ok=True)
    (out / "analysis.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    lines = [
        "# Query-reference error direction by update order",
        "",
        result["limits"],
        "",
        "## World signs: two distinct contrasts, all four views",
        "",
        "| View | Contrast | Negative | Positive | Zero | Worlds |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for view, variant in result["variants"].items():
        for contrast, signs in variant["signs"].items():
            lines.append(
                f"| {view} | {contrast} | {signs['negative']} | {signs['positive']} | "
                f"{signs['zero']} | {signs['n_worlds']} |"
            )
    for view, variant in result["variants"].items():
        lines += [
            "",
            f"## {view}: every owner, form and order",
            "",
            "| Owner / form / order | N | Correct | Foreign current | Revoked target | "
            "Revoked other | Invalid | All errors | Foreign / errors | Foreign position | "
            "Latest policy correct |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
        ]
        for key, v in variant["cells"].items():
            c, ratio = v["counts"], v["foreign_fraction_of_errors"]
            fraction = f"{100 * ratio:.2f}%" if ratio is not None else "undefined (no errors)"
            lines.append(
                f"| {key} | {v['n']} | {c['correct_target_current']} | "
                f"{c['other_account_current']} | "
                f"{c['revoked_target']} | {c['revoked_other']} | {c['invalid']} | "
                f"{v['errors_including_invalid']} | {fraction} | {v['foreign_is']} | "
                f"{v['latest_grant_correct']} |"
            )
    lines += [
        "",
        "The first/latest agreement counts and all exact per-world values are in analysis.json.",
        "No intervals, hypothesis tests, new model inference or changed gate decisions.",
        "",
        "Reproduce: `uv run --no-sync python scripts/count_query_order_errors.py`",
        "",
    ]
    (out / "report.md").write_text("\n".join(lines))


if __name__ == "__main__":
    report = analyze()
    write_outputs(report, OUT)
    print(json.dumps(report["variants"]["v2_stored_greedy"]["signs"], indent=2))
