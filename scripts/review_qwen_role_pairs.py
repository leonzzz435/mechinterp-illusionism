"""Post hoc matched-role inspection of the frozen Qwen archive; no model inference.

Matches named-self and other queries for the SAME target and simulator state.
The sole prompt difference must be the name in the active-connection line.
This descriptive analysis does not modify or replace the failed pilot screen.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

from review_qwen_evidence import archive_files, audit, outcome, require

ARCHIVE = Path("review/evidence/qwen-78ee6db8adfc4f3e.tar.gz")
SHA256 = "cf8eceea87129acaad2365f36af99d8f54923015923c837419a691252b8f12fa"
FACTORS = ("scenario_id", "updated", "grant_variant", "target", "phase", "rotation")


def match_pairs(records):
    grouped = defaultdict(dict)
    for record in records:
        job = record["job"]
        if job["kind"] != "action" or job["row"]["view"] not in {"named_self", "other"}:
            continue
        row = job["row"]
        key = (job["format"], *(row[f] for f in FACTORS))
        require(row["view"] not in grouped[key], "Duplicate matched-role member")
        grouped[key][row["view"]] = record
    pairs = []
    for key, pair in sorted(grouped.items()):
        require(set(pair) == {"named_self", "other"}, "Incomplete matched-role pair")
        named, other = pair["named_self"], pair["other"]
        a, b = named["job"]["row"], other["job"]["row"]
        require(a["assigned"] == a["target"] != b["assigned"], "Incorrect role contrast")
        for field in ("state", "before", "event", "choices", "expected_command", "actor_order"):
            require(a[field] == b[field], "Matched pair differs in " + field)
        for text_a, text_b in (
            (a["prompt"], b["prompt"]),
            (named["result"]["rendered_prompt"], other["result"]["rendered_prompt"]),
        ):
            line_a = "Your active connection: " + a["assigned"] + "."
            line_b = "Your active connection: " + b["assigned"] + "."
            require(text_a.count(line_a) == text_b.count(line_b) == 1, "Missing role line")
            require(
                text_a.replace(line_a, "<ROLE>") == text_b.replace(line_b, "<ROLE>"),
                "Prompt differs outside active-connection line",
            )
        pairs.append((key, named, other))
    return pairs


def summarize(pairs):
    counts = Counter()
    clusters = defaultdict(list)
    for _, named, other in pairs:
        yn, _ = outcome(named["job"]["row"], named["result"], named["status"])
        yo, _ = outcome(other["job"]["row"], other["result"], other["status"])
        counts[f"{yn}/{yo}"] += 1
        clusters[named["job"]["row"]["scenario_id"]].append(yo - yn)
    return {
        "pairs": len(pairs),
        "independent_scenarios": len(clusters),
        "correctness_named_self_other": dict(sorted(counts.items())),
        "named_self_correct": counts["1/0"] + counts["1/1"],
        "other_correct": counts["0/1"] + counts["1/1"],
        "mean_scenario_other_minus_named_self": sum(
            sum(values) / len(values) for values in clusters.values()
        )
        / len(clusters),
    }


def review():
    integrity = audit(ARCHIVE, SHA256)
    require(not integrity["action_gate_passed"], "Expected the frozen failed pilot")
    files, _, _ = archive_files(ARCHIVE, SHA256)
    records = [json.loads(line) for line in files["run/records.jsonl"].splitlines()]
    pairs = match_pairs(records)
    require(len(pairs) == 1024, "Expected all named-self/other role pairs")
    groups, relevant = defaultdict(list), defaultdict(list)
    for pair in pairs:
        key, named, _ = pair
        row = named["job"]["row"]
        condition = (
            "before"
            if row["phase"] == "before"
            else "after_relevant"
            if row["relevant_update"]
            else "after_irrelevant"
        )
        groups[key[0] + "/" + condition].append(pair)
        if key[0] == "chat" and condition == "after_relevant":
            relevant[row["scenario_id"]].append(pair)
    examples, by_scenario = [], {}
    for sid, subset in sorted(relevant.items()):
        by_scenario[sid] = summarize(subset)
        # Outcome-conditioned illustrations, selected AFTER viewing results.
        # Include the first failure per scenario, regardless of error category.
        errors = [
            pair
            for pair in subset
            if not outcome(pair[1]["job"]["row"], pair[1]["result"], pair[1]["status"])[0]
        ]
        if not errors:
            continue
        _, named, other = errors[0]
        row = named["job"]["row"]
        examples.append(
            {
                "scenario_id": sid,
                "factors": {f: row[f] for f in FACTORS},
                "state": row["state"],
                "expected_command": row["expected_command"],
                "members": {
                    label: {
                        "record_id": r["id"],
                        "record_checksum": r["checksum"],
                        "assigned": r["job"]["row"]["assigned"],
                        "status": r["status"],
                        "rendered_prompt": r["result"]["rendered_prompt"],
                        "selected_command": r["result"]["selected_command"],
                        "candidates": r["result"]["candidates"],
                    }
                    for label, r in (("named_self", named), ("other", other))
                },
            }
        )
    return {
        "kind": "post_hoc_descriptive_matched_role_review",
        "archive_sha256": SHA256,
        "action_gate_passed": integrity["action_gate_passed"],
        "matched_pairs_verified": len(pairs),
        "groups": {key: summarize(value) for key, value in sorted(groups.items())},
        "chat_after_relevant_by_scenario": by_scenario,
        "example_selection": "First erroneous chat named-self after-relevant pair per scenario, "
        "sorted by scenario, updated actor, grant alternative, target, phase and rotation. "
        "Post hoc, outcome-conditioned illustrations; frequencies use ALL pairs.",
        "examples": examples,
        "limitations": [
            "Eight development scenarios; variants and repeated before prompts are dependent.",
            "Same-state pairing was specified after results; no confirmatory inference.",
            "The input contrast does not identify an internal mechanism or self-specificity.",
            "Both original capability screens remain failed; no internal edit is unlocked.",
            "No new model call, score recomputation, prompt change or human-rating change.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(review(), indent=2, ensure_ascii=False, allow_nan=False))
