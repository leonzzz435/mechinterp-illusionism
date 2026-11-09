"""Retrospective stage/shortcut audit of saved selections; no model inference."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from analyze_query_sensitivity import (
    ANALYSIS_SHA,
    ARCHIVE_SHAS,
    EVIDENCE,
    ROOT,
    classify_choice,
    file_hash,
    parse_input,
    read_json,
    require,
    resolve_selection,
    save_figure,
    scripted_choices,
    setup_plotting,
    verified_payloads,
    verify_freeze,
)

OUT = ROOT / "review/query-reference-stages"
STAGES = ("before", "snapshot", "after_both")
OWNERS = ("self", "other")
FORMS = ("account_name", "owner_name", "possessive")
TIED_WORLD = "query-self-v1:0011"


def load_records():
    verify_freeze()
    require(file_hash(EVIDENCE / "analysis.json") == ANALYSIS_SHA, "Frozen analysis changed")
    blocks = read_json(EVIDENCE / "verification.json")["blocks"]
    require([b["block"] for b in blocks] == list(range(6)), "Unexpected blocks")
    records = []
    for block, sha in zip(blocks, ARCHIVE_SHAS):
        payloads = verified_payloads(EVIDENCE / block["archive"], sha)
        records.extend(json.loads(line) for line in payloads["run/records.jsonl"].splitlines())
    require(len(records) == len({r["id"] for r in records}) == 16128, "Wrong record inventory")
    require(sum(r["status"] == "tie" for r in records) == 1, "Unexpected tie inventory")
    require(all(r["status"] in {"ok", "tie"} for r in records), "Unexpected error")
    return records


def measure(xs, draws, inferential):
    xs = np.asarray(xs, dtype=float)
    return {
        "estimate": float(xs.mean()),
        "ci95": np.quantile(xs[draws].mean(axis=1), [0.025, 0.975]).tolist()
        if inferential
        else None,
        "world_values": xs.tolist(),
    }


def audit_record(record, variant):
    row, result = record["job"]["row"], record["result"]
    p = parse_input({"prompt": row["prompt"], "choices": row["choices"]})
    for key in ("stage", "queried_owner", "query_form", "target", "expected_command"):
        require(p[key] == row[key], "Printed input and saved metadata disagree")
    selected = result["selected_command"]
    if record["status"] == "tie":
        require(row["world_id"] == TIED_WORLD, "Unexpected tie world")
        policy = resolve_selection(result["candidates"])
        require(policy["resolved"], "Unresolved saved-greedy rule")
        if variant == "v2_stored_greedy":
            selected = policy["selected_command"]
        elif variant == "other_tied_command":
            selected = next(c for c in policy["tied_commands"] if c != policy["selected_command"])
    category = classify_choice(p, selected)
    policies = scripted_choices(p)
    policies["latest_grant_only"] = p["events"][-1]["grant"] if p["events"] else None
    policies["first_grant_only"] = p["events"][0]["grant"] if p["events"] else None
    return {
        "id": record["id"],
        "row": row,
        "parsed": p,
        "selected": selected,
        "category": category,
        "correct": category == "correct_target_current",
        "policies": policies,
    }


def audit_variant(records, variant):
    entries = [
        audit_record(r, variant)
        for r in records
        if variant != "exclude_world_0011" or r["job"]["row"]["world_id"] != TIED_WORLD
    ]
    worlds = sorted({e["row"]["world_id"] for e in entries})
    n = len(worlds)
    require(len(entries) == n * 336, "Partial world")
    draws = np.random.default_rng(1729).integers(n, size=(10000, n))
    inferential = variant != "frozen_v1"
    groups, per_world = defaultdict(list), defaultdict(list)
    for e in entries:
        r = e["row"]
        key = "/".join((r["stage"], r["queried_owner"], r["query_form"]))
        groups[key].append(e)
        per_world[r["world_id"], key].append(e)
    cells, vectors, baselines = {}, {}, {}
    for key, es in sorted(groups.items()):
        stage = key.split("/")[0]
        expected_n = {"before": 8, "snapshot": 16, "after_both": 32}[stage]
        require(all(len(per_world[w, key]) == expected_n for w in worlds), "Unbalanced cell")
        xs = np.array([np.mean([e["correct"] for e in per_world[w, key]]) for w in worlds])
        vectors[key] = xs
        cells[key] = {
            "n": len(es),
            "correct": sum(e["correct"] for e in es),
            "invalid": sum(e["category"] == "invalid" for e in es),
            "accuracy": measure(xs, draws, inferential),
        }
        baselines[key] = {}
        for policy in es[0]["policies"]:
            valid = [e for e in es if e["policies"][policy] is not None]
            require(len(valid) in {0, len(es)}, "Partial policy applicability")
            if not valid:
                baselines[key][policy] = {
                    "applicable": 0,
                    "n": len(es),
                    "accuracy": None,
                    "model_minus_policy": None,
                    "agreement": None,
                }
                continue
            bs = np.array(
                [
                    np.mean(
                        [
                            e["policies"][policy] == e["parsed"]["expected_command"]
                            for e in per_world[w, key]
                        ]
                    )
                    for w in worlds
                ]
            )
            baselines[key][policy] = {
                "applicable": len(es),
                "n": len(es),
                "correct": sum(
                    e["policies"][policy] == e["parsed"]["expected_command"] for e in es
                ),
                "accuracy": float(bs.mean()),
                "agreement": sum(e["selected"] == e["policies"][policy] for e in es),
                "model_minus_policy": measure(xs - bs, draws, inferential),
            }
    contrasts = {}
    for stage in STAGES:
        for form in FORMS:
            contrasts[f"{stage}/{form}/self_minus_other"] = (
                vectors[f"{stage}/self/{form}"] - vectors[f"{stage}/other/{form}"]
            )
        for owner in OWNERS:
            contrasts[f"{stage}/{owner}/account_minus_possessive"] = (
                vectors[f"{stage}/{owner}/account_name"] - vectors[f"{stage}/{owner}/possessive"]
            )
    for base in ("before", "snapshot"):
        changes = {}
        for form in FORMS:
            for owner in OWNERS:
                change = vectors[f"after_both/{owner}/{form}"] - vectors[f"{base}/{owner}/{form}"]
                contrasts[f"after_minus_{base}/{owner}/{form}"] = changes[owner, form] = change
            contrasts[f"after_minus_{base}/{form}/self_minus_other"] = (
                changes["self", form] - changes["other", form]
            )
        for comparator in ("account_name", "owner_name"):
            for owner in OWNERS:
                contrasts[f"after_minus_{base}/{owner}/possessive_minus_{comparator}"] = (
                    changes[owner, "possessive"] - changes[owner, comparator]
                )
            contrasts[f"after_minus_{base}/self_minus_other/possessive_minus_{comparator}"] = (
                changes["self", "possessive"]
                - changes["other", "possessive"]
                - changes["self", comparator]
                + changes["other", comparator]
            )
    # Order is a paired input manipulation: same world, ownership, permissions and key.
    orders = {}
    for owner in OWNERS:
        for form in FORMS:
            pairs = defaultdict(dict)
            for e in groups[f"after_both/{owner}/{form}"]:
                r, p = e["row"], e["parsed"]
                key = (
                    r["world_id"],
                    r["connection_assignment"],
                    r["grant_mapping"],
                    r["option_rotation"],
                )
                last = "target_last" if p["events"][-1]["actor"] == p["target"] else "other_last"
                pairs[key][last] = e
            require(
                len(pairs) == n * 16
                and all(set(v) == {"target_last", "other_last"} for v in pairs.values()),
                "Incomplete order pairs",
            )
            xs = {last: [] for last in ("target_last", "other_last")}
            changed = both = 0
            for w in worlds:
                ps = [p for k, p in pairs.items() if k[0] == w]
                for last in xs:
                    xs[last].append(np.mean([p[last]["correct"] for p in ps]))
                for p in ps:
                    require(
                        p["target_last"]["parsed"]["expected_command"]
                        == p["other_last"]["parsed"]["expected_command"],
                        "Order changed oracle",
                    )
                    changed += p["target_last"]["selected"] != p["other_last"]["selected"]
                    both += p["target_last"]["correct"] and p["other_last"]["correct"]
            orders[f"{owner}/{form}"] = {
                "pairs": len(pairs),
                "changed_selection_pairs_including_invalid": changed,
                "both_correct": both,
                **{last: measure(v, draws, inferential) for last, v in xs.items()},
                "target_last_minus_other_last": measure(
                    np.array(xs["target_last"]) - xs["other_last"], draws, inferential
                ),
            }
    return {
        "worlds": worlds,
        "n_worlds": n,
        "n": len(entries),
        "cells": cells,
        "baselines": baselines,
        "contrasts": {k: measure(v, draws, inferential) for k, v in contrasts.items()},
        "event_orders": orders,
        "status": "descriptive_no_inference" if not inferential else "retrospective_exploratory",
    }


def illustrative_example(records):
    """Explicit post hoc selection, with all owners/forms/stages and both orders exported."""
    lookup = {}
    for r in records:
        row = r["job"]["row"]
        key = (
            row["world_id"],
            row["connection_assignment"],
            row.get("grant_mapping"),
            row["option_rotation"],
            row["stage"],
            row["queried_owner"],
            row["query_form"],
            tuple(row.get("event_order", [])),
        )
        lookup[key] = r
    candidates = []
    for key, r in lookup.items():
        if key[4:7] != ("after_both", "self", "possessive"):
            continue
        e = audit_record(r, "frozen_v1")
        if e["category"] != "other_account_current":
            continue
        snapshot = lookup[(*key[:4], "snapshot", "self", "possessive", ())]
        named = lookup[(*key[:6], "account_name", key[7])]
        if (
            audit_record(snapshot, "frozen_v1")["correct"]
            and audit_record(named, "frozen_v1")["correct"]
        ):
            candidates.append(key)
    require(bool(candidates), "No illustrative example matches declared selection rule")
    chosen = min(candidates)
    complete = [
        r
        for k, r in lookup.items()
        if k[0:2] == chosen[0:2] and k[3] == chosen[3] and (k[2] == chosen[2] or k[4] == "before")
    ]
    require(len(complete) == 24, "Example must include all forms, owners and event orders")
    return {
        "selection_status": "post_hoc_illustration_not_representative_or_prespecified",
        "rule": "Lexicographically first (world, assignment, grant mapping, rotation, "
        "stage, owner, form, "
        "event order) with foreign self/possessive after-both choice, correct matching "
        "snapshot self/possessive and correct after-both self/account-name choice.",
        "chosen_key": chosen,
        "qualifying_rows": len(candidates),
        "opening_record_id": lookup[chosen]["id"],
        "records": sorted(complete, key=lambda r: r["id"]),
    }


def analyze():
    records = load_records()
    variants = {
        key: audit_variant(records, key)
        for key in ("frozen_v1", "exclude_world_0011", "v2_stored_greedy", "other_tied_command")
    }
    frozen = read_json(EVIDENCE / "analysis.json")
    for key, c in variants["frozen_v1"]["cells"].items():
        require(
            c["n"] == frozen["cells"][key]["scheduled"]
            and c["accuracy"]["estimate"] == frozen["cells"][key]["accuracy"],
            "Cell does not reproduce",
        )
    return {
        "version": "query-reference-stages-v1-offline",
        "new_model_inference": False,
        "status": "post_outcome_descriptive_and_exploratory_no_new_decision",
        "original_analysis_sha256": ANALYSIS_SHA,
        "archive_sha256": list(ARCHIVE_SHAS),
        "script_sha256": file_hash(Path(__file__)),
        "limits": "All stages are separate prompts, not a sequential model session. "
        "Snapshot prints the "
        "same final permissions without history; before has different commands and keys. "
        "Whole-world paired bootstrap, 10000 draws, seed 1729. Nominal 95% intervals, "
        "no new hypothesis tests, no multiplicity/selection adjustment, no equivalence claim. "
        "Frozen v1 has no intervals; supplement variants are post hoc. Lookup gates still fail.",
        "variants": variants,
        "example": illustrative_example(records),
    }


def percent(x):
    return f"{100 * x:.2f}"


def estimate(value):
    ci = value["ci95"]
    return f"{100 * value['estimate']:+.2f}" + (
        f" [{100 * ci[0]:+.2f}, {100 * ci[1]:+.2f}]" if ci else " (no interval)"
    )


def write_outputs(report, out):
    out.mkdir(parents=True, exist_ok=True)
    (out / "analysis.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    lines = [
        "# Query forms across three separately prompted task presentations",
        "",
        "**Post hoc CPU supplement. No model inference; no repaired candidate decision.**",
        "",
        report["limits"],
        "",
        "## Original recorded cells",
        "",
        "| Owner / form | Before | Current-state snapshot | Both updates printed |",
        "|---|---:|---:|---:|",
    ]
    raw = report["variants"]["frozen_v1"]
    for owner in OWNERS:
        for form in FORMS:
            cells = [raw["cells"][f"{stage}/{owner}/{form}"] for stage in STAGES]
            lines.append(
                f"| {owner}/{form} | "
                + " | ".join(
                    f"{c['correct']}/{c['n']} = {percent(c['accuracy']['estimate'])}%"
                    for c in cells
                )
                + " |"
            )
    lines += [
        "",
        "Snapshot and after-both have identical final permissions. Before is not the same "
        "answer key. These are independently scored prompts, not changes within one session.",
        "",
        "## Paired-world contrasts in every sensitivity variant",
        "",
        "All values are percentage points. Intervals are exploratory, not tests of equivalence.",
    ]
    for key, variant in report["variants"].items():
        lines += [
            "",
            f"### {key} ({variant['n_worlds']} worlds)",
            "",
            "| Contrast | Estimate and nominal 95% interval |",
            "|---|---:|",
        ]
        lines += [f"| {key} | {estimate(value)} |" for key, value in variant["contrasts"].items()]
    lines += [
        "",
        "## Stage-specific shortcuts (original choices)",
        "",
        "`latest_grant_only` is undefined without events. `latest_grant_or_first` then "
        "falls back to the first offered option: its baseline is 25%, not 50%. "
        "With both updates printed, latest-grant accuracy is 50% pooled over both event orders "
        "in every owner/form cell (100% target-last, 0% other-last). Uniform choice among "
        "four commands is 25%; 50% is a structured shortcut, not general chance.",
        "",
        "| Stage / owner / form | Model (%) | Fallback policy (%) | Latest only (%) | "
        "Model minus fallback (pp) | Latest agreement | First-grant agreement |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for key, c in raw["cells"].items():
        policies = raw["baselines"][key]
        latest, fallback, first = (
            policies[k] for k in ("latest_grant_only", "latest_grant_or_first", "first_grant_only")
        )
        latest_text = (
            f"{latest['agreement']}/{c['n']}" if latest["agreement"] is not None else "N/A"
        )
        first_text = f"{first['agreement']}/{c['n']}" if first["agreement"] is not None else "N/A"
        lines.append(
            f"| {key} | {percent(c['accuracy']['estimate'])} | {percent(fallback['accuracy'])} | "
            f"{percent(latest['accuracy']) if latest['accuracy'] is not None else 'N/A'} | "
            f"{estimate(fallback['model_minus_policy'])} | "
            f"{latest_text} | "
            f"{first_text} |"
        )
    lines += [
        "",
        "## Model minus stage-appropriate shortcut: exploratory 48-world sensitivity",
        "",
        "Unique stored-greedy variant; nominal world-paired intervals, no new tests. "
        "Before/snapshot use the 25% first-option fallback, after-both the 50% latest grant. "
        "These intervals are retrospective and do not repair lookup gates.",
        "",
        "| Stage / owner / form | Model minus policy (pp), nominal 95% interval |",
        "|---|---:|",
    ]
    for key, policies in report["variants"]["v2_stored_greedy"]["baselines"].items():
        value = policies["latest_grant_or_first"]["model_minus_policy"]
        lines.append(f"| {key} | {estimate(value)} |")
    lines += [
        "",
        "## Both event orders, original selections",
        "",
        "| Owner / form | Target updated last (%) | Other updated last (%) | "
        "Both correct / pairs |",
        "|---|---:|---:|---:|",
    ]
    for key, value in raw["event_orders"].items():
        lines.append(
            f"| {key} | {percent(value['target_last']['estimate'])} | "
            f"{percent(value['other_last']['estimate'])} | "
            f"{value['both_correct']}/{value['pairs']} |"
        )
    lines += [
        "",
        "All scripted policies, per-world vectors and model-minus-policy intervals for "
        "every cell/variant are in analysis.json. The first-grant comparison is retrospective. "
        "Disagreement excludes a universal always-latest policy; mixed recency/order mechanisms "
        "remain possible. Foreign is relative to the queried account, so its absolute identity "
        "changes between own and other queries.",
        "",
        "## Reproduce",
        "",
        "`uv run --no-sync python scripts/analyze_query_stages.py`",
        "",
    ]
    (out / "report.md").write_text("\n".join(lines))
    example = report["example"]
    opening = next(r for r in example["records"] if r["id"] == example["opening_record_id"])
    lines = [
        "# Recorded illustration, selected after inspecting outcomes",
        "",
        example["rule"],
        "",
        "This is an illustration, not a representative sample or a preregistered example. "
        "All 24 matched conditions and both event orders follow. "
        "Full prompts/scores are in analysis.json.",
        "",
        f"Opening record: `{opening['id']}`.",
        "",
        "```text",
        opening["job"]["row"]["prompt"],
        "```",
        "",
        "| Stage | Owner | Form | Event order | Expected | Selected | Status |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in sorted(
        example["records"],
        key=lambda r: (
            STAGES.index(r["job"]["row"]["stage"]),
            r["job"]["row"]["queried_owner"],
            r["job"]["row"]["query_form"],
            r["job"]["row"].get("event_order", []),
        ),
    ):
        row = r["job"]["row"]
        lines.append(
            f"| {row['stage']} | {row['queried_owner']} | {row['query_form']} | "
            f"{row.get('event_order', 'N/A')} | {row['expected_command']} | "
            f"{r['result']['selected_command']} | {r['status']} |"
        )
    (out / "example.md").write_text("\n".join(lines) + "\n")
    plots(report, out)
    # Matplotlib emits trailing spaces inside SVG paths; normalize only our new exports.
    for name in ("task_example", "stage_accuracy", "history_contrasts"):
        path = out / f"{name}.svg"
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


def plots(report, out):
    plt = setup_plotting()
    colors = {"account_name": "#176b80", "owner_name": "#8462a1", "possessive": "#c45b35"}
    labels = {
        "account_name": "Account name",
        "owner_name": "Operator name",
        "possessive": "Possessive",
    }
    raw = report["variants"]["frozen_v1"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    for ax, owner in zip(axes, OWNERS):
        for i, form in enumerate(FORMS):
            ys = [100 * raw["cells"][f"{s}/{owner}/{form}"]["accuracy"]["estimate"] for s in STAGES]
            ax.scatter(
                np.arange(3) + (i - 1) * 0.18, ys, color=colors[form], label=labels[form], s=65
            )
        ax.set(
            xticks=range(3),
            xticklabels=["Before", "Final snapshot", "Both updates"],
            ylim=(0, 104),
            title="Own account" if owner == "self" else "Other account",
            ylabel="Correct selections (%)",
        )
        ax.grid(axis="y", alpha=0.15)
        ax.legend(loc="lower left")
    fig.suptitle("Same model, three ways to name the account")
    fig.text(
        0.5,
        -0.02,
        "Original recorded accuracy • separate prompts, not a trajectory • "
        "snapshot and updates share the final state",
        ha="center",
        fontsize=9,
    )
    save_figure(fig, out / "stage_accuracy")
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 4.8))
    for i, (owner, form) in enumerate((o, f) for o in OWNERS for f in FORMS):
        key = f"after_minus_snapshot/{owner}/{form}"
        v = report["variants"]["v2_stored_greedy"]["contrasts"][key]
        mean, lo, hi = 100 * np.array([v["estimate"], *v["ci95"]])
        ax.errorbar(
            mean, 5 - i, xerr=[[mean - lo], [hi - mean]], fmt="o", color=colors[form], capsize=4
        )
    ax.set(
        yticks=range(6),
        yticklabels=list(reversed([f"{o} / {labels[f]}" for o in OWNERS for f in FORMS])),
        xlabel="Accuracy with both updates minus final snapshot (percentage points)",
        title="The printed history changes performance differently across query forms",
    )
    ax.axvline(0, color="#777777", lw=1)
    ax.grid(axis="x", alpha=0.15)
    fig.text(
        0.5,
        -0.02,
        "Post hoc 48-world stored-greedy sensitivity • nominal paired-world 95% intervals • "
        "lookup gates failed",
        ha="center",
        fontsize=9,
    )
    save_figure(fig, out / "history_contrasts")
    plt.close(fig)
    example = report["example"]
    record = next(r for r in example["records"] if r["id"] == example["opening_record_id"])
    row = record["job"]["row"]
    parsed = parse_input({"prompt": row["prompt"], "choices": row["choices"]})
    fig, ax = plt.subplots(figsize=(11, 5.4))
    ax.set(xlim=(0, 11), ylim=(0, 5.4))
    ax.axis("off")
    ax.text(
        0.2,
        5,
        "One saved example: the same target, different query forms",
        fontsize=15,
        weight="bold",
    )
    ax.text(
        0.3,
        3.8,
        "Operator bindings\n"
        + "\n".join(f"{name} → {account}" for name, account in parsed["binding_pairs"]),
        va="center",
        bbox={"boxstyle": "round,pad=.7", "fc": "#eef3f5", "ec": "#176b80"},
    )
    ax.text(
        4.0,
        3.8,
        "Two printed updates\n"
        + "\n".join(f"{e['actor']}: {e['revoke']} → {e['grant']}" for e in parsed["events"]),
        va="center",
        bbox={"boxstyle": "round,pad=.7", "fc": "#eef3f5", "ec": "#176b80"},
    )
    ax.text(
        0.3,
        2.5,
        f"Same target: {parsed['target']}    •    "
        f"Correct current command: {parsed['expected_command']}",
        weight="bold",
        fontsize=11,
    )
    for i, form in enumerate(FORMS):
        matched = next(
            r
            for r in example["records"]
            if r["job"]["row"]["stage"] == "after_both"
            and r["job"]["row"]["queried_owner"] == "self"
            and r["job"]["row"]["query_form"] == form
            and r["job"]["row"]["event_order"] == row["event_order"]
        )
        mr, result = matched["job"]["row"], matched["result"]
        ok = result["selected_command"] == mr["expected_command"]
        ax.text(
            0.3 + 3.7 * i,
            1.4,
            f"{mr['query_reference']}\n↓\n{result['selected_command']}\n"
            + ("Simulator: succeeds" if ok else "Simulator: denied"),
            va="center",
            bbox={
                "boxstyle": "round,pad=.7",
                "fc": "#eff7f3" if ok else "#fff0e8",
                "ec": "#176b80" if ok else "#c45b35",
            },
        )
    ax.text(
        0.3,
        0.1,
        "Post hoc illustration • all 24 matched conditions disclosed • "
        "arrows show task relations, not a neural circuit",
        fontsize=9,
    )
    save_figure(fig, out / "task_example")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    for protected in (
        EVIDENCE,
        ROOT / "review/evidence",
        ROOT / "review/query-reference-sensitivity",
        ROOT / "docs/article",
        ROOT / "src",
        ROOT / "designs",
    ):
        require(not args.out.resolve().is_relative_to(protected.resolve()), "Protected destination")
    report = analyze()
    write_outputs(report, args.out)
    print(json.dumps(report["variants"]["v2_stored_greedy"]["contrasts"], indent=2))


if __name__ == "__main__":
    main()
