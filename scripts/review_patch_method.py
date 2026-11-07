"""Descriptive post-run review and CPU-only feasibility check; no model inference.

This does not change the frozen primary analysis or create a runnable cloud protocol.
The optional tokenizer check needs eval extras and the pinned tokenizer already cached.
"""

import argparse
import json
from collections import Counter, defaultdict
from statistics import mean, median

from review_patch_evidence import ARCHIVE, RANDOM, SHA256
from review_qwen_evidence import archive_files, require


def review(tokenizer_check=False):
    files, _, _ = archive_files(ARCHIVE, SHA256)
    saved = json.loads(files["run/analysis.json"])
    records = [json.loads(line) for line in files["run/records.jsonl"].splitlines()]
    baseline = {r["job"]["base_id"]: r for r in records if r["job"]["arm"] == "baseline"}
    transitions, margin_changes, edit_ratios = defaultdict(Counter), defaultdict(list), []
    for record in records:
        job = record["job"]
        if job["arm"] != "swap":
            continue
        row, result = job["row"], record["result"]
        own = baseline[job["base_id"]]["result"]
        edit_ratios.extend(
            c["patch"]["actual_norm"] / c["patch"]["residual_norm"] for c in result["candidates"]
        )
        if row["phase"] != "after" or not row["relevant_update"]:
            continue
        key = row["frame"] + "/" + row["relation"]
        before, after = own["execution"]["correct"], result["execution"]["correct"]
        transitions[key][f"{int(before)}_to_{int(after)}"] += 1
        transitions[key]["changed_choice"] += own["selected_command"] != result["selected_command"]
        other = next(a for a in row["state"]["permissions"] if a != row["target"])
        correct, competitor = row["expected_command"], row["state"]["permissions"][other][0]
        scores = [
            {c["command"]: c["log_likelihood"] for c in r["candidates"]} for r in (own, result)
        ]
        margin_changes[key].append(
            (scores[1][correct] - scores[1][competitor])
            - (scores[0][correct] - scores[0][competitor])
        )
    cells = {}
    for key, counts in sorted(transitions.items()):
        normalized = {f"{a}_to_{b}": counts[f"{a}_to_{b}"] for a in (0, 1) for b in (0, 1)}
        require(sum(normalized.values()) == 128, "Incomplete primary cell")
        require(
            counts["changed_choice"] == normalized["0_to_1"] + normalized["1_to_0"],
            "Also a wrong-to-different-wrong transition; report explicitly",
        )
        cells[key] = {
            "transitions": normalized,
            "changed_choices": counts["changed_choice"],
            "mean_margin_change_nats": mean(margin_changes[key]),
        }
    directional = {}
    for direction in ("reference_to_active", "active_to_reference"):
        swap = saved["transfer"]["swap"][direction]["scenario_means"]
        contrast = {
            s: swap[s] - mean(saved["transfer"][a][direction]["scenario_means"][s] for a in RANDOM)
            for s in swap
        }
        directional[direction] = {
            "exchange_minus_mean_random": mean(contrast.values()),
            "positive_scenarios": sum(v > 0 for v in contrast.values()),
            "scenario_values": contrast,
            "status": "Post hoc descriptive decomposition; no new primary test or success claim",
        }
    require(
        abs(
            mean(d["exchange_minus_mean_random"] for d in directional.values())
            - saved["primary_contrast"]["estimate"]
        )
        < 1e-12,
        "Contrast decomposition mismatch",
    )
    require(len(edit_ratios) == 8192, "Missing swap candidate norms")
    result = {
        "archive_sha256": SHA256,
        "frozen_decision": saved["decision"],
        "kind": "post_run_method_review_not_a_new_experiment",
        "primary_cell_transitions": cells,
        "directional_accuracy_contrasts": directional,
        "prespecified_secondary_margin_transfer": saved["margin_transfer"]["swap"],
        "exchange_norm_divided_by_recipient_norm": {
            "min": min(edit_ratios),
            "median": median(edit_ratios),
            "max": max(edit_ratios),
            "candidate_edits": len(edit_ratios),
            "independent_scenarios": 8,
            "interpretation": "Norm ratio, not proportion of coordinates or information changed",
        },
        "no_model_inference": True,
    }
    if tokenizer_check:
        result["proposed_control_tokenizer_check"] = check_wording(baseline)
    return result


def check_wording(baseline):
    from transformers import AutoTokenizer

    from self_model_study.action_task import build_design
    from self_model_study.io import digest

    revision = "a09a35458c702b33eeacc393d103063234e8bc28"
    tokenizer = AutoTokenizer.from_pretrained(
        "Qwen/Qwen2.5-7B-Instruct", revision=revision, local_files_only=True
    )
    changes = Counter()
    for record in baseline.values():
        row, output = record["job"]["row"], record["result"]
        if row["frame"] != "active":
            continue
        old = f"Your active connection: {row['mentioned_actor']}."
        new = f"The active connection: {row['mentioned_actor']}."
        require(output["rendered_prompt"].count(old) == 1, "Ambiguous role line")
        a = output["prompt_token_ids"]
        b = tokenizer.encode(output["rendered_prompt"].replace(old, new), add_special_tokens=False)
        require(len(a) == len(b), "Unequal token lengths")
        diffs = [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y]
        require(len(diffs) == 1, "More than one token changed")
        changes[diffs[0]] += 1
    # Enumerate only the proposed CPU design, without scores or a launch configuration.
    scenes = [
        r
        for r in build_design(scenarios=32)
        if r["view"] == "named_self" and int(r["scenario_id"].rsplit(":", 1)[1]) >= 16
    ]
    require(len(scenes) == 16 * 64, "Proposed scene count mismatch")
    proposal, equal_length_pairs = [], 0
    for row in scenes:
        old = f"Your active connection: {row['assigned']}."
        for actor in row["state"]["permissions"]:
            matched = []
            for label in (
                "Your active connection",
                "The active connection",
                "Reference connection",
            ):
                prompt = row["prompt"].replace(old, f"{label}: {actor}.")
                proposal.append(
                    {"scenario_id": row["scenario_id"], "prompt": prompt, "choices": row["choices"]}
                )
                rendered = tokenizer.apply_chat_template(
                    [{"role": "user", "content": prompt}],
                    tokenize=False,
                    add_generation_prompt=True,
                )
                tokens = tokenizer.encode(rendered, add_special_tokens=False)
                matched.append(tokens)
                for command in row["choices"]:
                    whole = tokenizer.encode(rendered + command, add_special_tokens=False)
                    require(
                        whole[: len(tokens)] == tokens and len(whole) <= 2048,
                        "Invalid proposed continuation boundary",
                    )
                    require(tokenizer.decode(whole[len(tokens) :]) == command, "Command mismatch")
            require(
                len(matched[0]) == len(matched[1])
                and [(i, x, y) for i, (x, y) in enumerate(zip(matched[0], matched[1])) if x != y]
                == [(57, 7771, 785)],
                "Your/The pair is not the promised one-token edit",
            )
            equal_length_pairs += 1
    return {
        "tokenizer_revision": revision,
        "historical_active_prompts_checked": sum(changes.values()),
        "historical_token_changes": [
            {"position": i, "from": a, "to": b, "count": n}
            for (i, a, b), n in sorted(changes.items())
        ],
        "draft_scenarios": list(range(16, 32)),
        "draft_choice_cases": len(proposal),
        "draft_equal_length_Your_The_pairs": equal_length_pairs,
        "draft_command_boundaries": 4 * len(proposal),
        "draft_model_inputs_hash": digest(proposal),
        "status": "CPU feasibility only; same template/vocabulary; not a frozen or run protocol",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tokenizer-check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(review(args.tokenizer_check), sort_keys=True, indent=2))
