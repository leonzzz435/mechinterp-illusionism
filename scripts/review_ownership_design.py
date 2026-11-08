"""CPU-only design review of saved ownership evidence and unrun prompt proposals.

Does not change frozen inputs/endpoints, load a tokenizer/model, or submit a job.
The existing worlds are used for inspection, not relabeled as a fresh test set.
"""

import gzip
import json
import tarfile
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path

import numpy as np

from self_model_study.action_task import render, score_command
from self_model_study.io import canonical, digest, file_hash, read_json, write_json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "review/ownership-permissions-results"
OUTPUT = ROOT / "review/ownership-design-audit"
HISTORY = {
    "pilot": "qwen-78ee6db8adfc4f3e",
    "role": "qwen-role-96787d5e7adf4c4d",
    "possessive": "qwen-possessive-f2baaa2fb6b74880",
}
LINES = {
    "your": "Your active connection",
    "active": "Your active connection",
    "the": "The active connection",
    "reference": "Reference connection",
    "neutral": "Reference connection",
}


def actor_order(row):
    if "actor_order" in row:
        return row["actor_order"]
    initial = row["before"]
    return sorted(
        initial["permissions"],
        key=lambda a: initial["commands"].index(initial["permissions"][a][0]),
    )


def historical_named_prompt(row):
    """Exact historical template, named query. There is no historical Their arm."""
    if row["frame"] not in LINES:
        raise ValueError("Their has no counterpart in the historical named-query experiment")
    adapted = {
        **row,
        "view": "named_self",
        "assigned": row["mentioned_actor"],
        "actor_order": actor_order(row),
    }
    prompt, _ = render(adapted)
    return prompt.replace(
        f"Your active connection: {adapted['assigned']}.",
        f"{LINES[row['frame']]}: {adapted['assigned']}.",
    )


def query_reference_probe(row, view):
    """Recover the earlier self/named-self/other semantics, including the oracle change."""
    if view not in {"self", "named_self", "other"}:
        raise ValueError("Unknown query reference")
    adapted = deepcopy(row)
    assigned = row["target"]
    target = (
        next(a for a in row["state"]["permissions"] if a != assigned)
        if view == "other"
        else assigned
    )
    adapted.update(
        assigned=assigned,
        target=target,
        view=view,
        actor_order=actor_order(row),
        relevant_update=target == row["event"]["actor"],
    )
    command = adapted["state"]["permissions"][target][0]
    adapted.update(expected_command=command, expected_position=adapted["choices"].index(command))
    prompt, _ = render(adapted)
    assert score_command(adapted, command)["correct"]
    return {
        "model_input": {"prompt": prompt, "choices": row["choices"]},
        "audit": {
            "view": view,
            "assigned": assigned,
            "target": target,
            "expected_command": command,
            "relevant_update": adapted["relevant_update"],
        },
    }


def snapshot_probe(row):
    """Prospective lookup control: current permissions only, no event/ownership wording."""
    history = "\n".join(f"{a}: {row['state']['permissions'][a][0]}." for a in actor_order(row))
    prompt = (
        "A command succeeds only if the executing connection currently has permission. "
        "Only the permissions listed below exist.\nCurrent permissions:\n"
        + history
        + f"\nSelect one command that would succeed for {row['target']}.\nAvailable commands:\n"
        + "\n".join(f"- {c}" for c in row["choices"])
        + "\nReturn exactly one command from this list."
    )
    return {
        "model_input": {"prompt": prompt, "choices": row["choices"]},
        "audit": {"target": row["target"], "expected_command": row["expected_command"]},
    }


def their_probes(row):
    """Same-target aliases plus owner swaps; examples only, no model measurement."""
    actors = actor_order(row)
    examples = []
    for swap in (0, 1):
        own, rowan = actors[swap], actors[1 - swap]
        forms = {
            "your": ("your active connection", own),
            "their": ("their active connection", rowan),
            "rowan": ("Rowan's active connection", rowan),
            "named_you": (own, own),
            "named_rowan": (rowan, rowan),
        }
        prefix = (
            "There are two operators: you and observer Rowan. The word their refers to Rowan.\n"
            f"Your active connection: {own}.\nRowan's active connection: {rowan}.\n"
            "Current permissions:\n"
            + "\n".join(f"{a}: {row['state']['permissions'][a][0]}." for a in actors)
        )
        for form, (phrase, target) in forms.items():
            examples.append(
                {
                    "model_input": {
                        "prompt": prefix
                        + f"\nSelect one command that would succeed for {phrase}."
                        + "\nAvailable commands:\n"
                        + "\n".join(f"- {c}" for c in row["choices"])
                        + "\nReturn exactly one command from this list.",
                        "choices": row["choices"],
                    },
                    "audit": {
                        "owner_swap": swap,
                        "query_form": form,
                        "target": target,
                        "expected_command": row["state"]["permissions"][target][0],
                    },
                }
            )
    return examples


def scripted_choices(row):
    """Same policies as the draft; distinguish active ownership from context naming."""
    return {
        "latest_grant_or_first": row["event"]["grant"]
        if row["phase"] == "after"
        else row["choices"][0],
        "ignore_update": row["before"]["permissions"][row["target"]][0],
        "context_named_actor": row["state"]["permissions"][row["mentioned_actor"]][0],
        "always_active_actor": row["state"]["permissions"][row["mentioned_actor"]][0]
        if row["frame"] == "your"
        else None,
    }


def error_bounds(target_accuracy, other_accuracy):
    """Conditional on BOTH observed accuracies; not a prospective design constraint."""
    if not all(0 <= a <= 1 for a in (target_accuracy, other_accuracy)):
        raise ValueError("Accuracy must be a probability")
    return [-(1 - other_accuracy), 1 - target_accuracy]


def stage(row):
    return (
        "before"
        if row["phase"] == "before"
        else "after_relevant"
        if row["relevant_update"]
        else "after_irrelevant"
    )


def read_archives():
    records = []
    for a in read_json(RESULTS / "provenance.json")["archives"]:
        path = ROOT / a["path"]
        assert file_hash(path) == a["sha256"]
        with tarfile.open(path) as tar:
            records.extend(json.loads(line) for line in tar.extractfile("run/records.jsonl"))
    assert len(records) == len({r["id"] for r in records}) == 18432
    return records


def history_audit():
    result = {}
    for label, filename in HISTORY.items():
        path = ROOT / "review/evidence" / (filename + ".tar.gz")
        with tarfile.open(path) as tar:
            plan = json.load(tar.extractfile("run/plan.json"))
            jobs = [j for b in plan["blocks"] for j in b["jobs"] if j["kind"] == "action"]
            analysis = (
                json.load(tar.extractfile("run/analysis.json")) if label == "possessive" else None
            )
        bound = [
            j
            for j in jobs
            if "Select one command that would succeed for your active connection."
            in j["row"]["prompt"]
        ]
        matched = 0
        if label != "pilot":
            for job in jobs:
                assert historical_named_prompt(job["row"]) == job["row"]["prompt"]
                matched += 1
        result[label] = {
            "archive": str(path.relative_to(ROOT)),
            "sha256": file_hash(path),
            "action_jobs": len(jobs),
            "query_bound_jobs": len(bound),
            "historical_named_renderer_exact_matches": matched,
            "example": jobs[0]["row"]["prompt"],
        }
        if analysis is not None:
            # The quoted table is independently counted from raw records below.
            with tarfile.open(path) as tar:
                raw = [json.loads(line) for line in tar.extractfile("run/records.jsonl")]
            cells = defaultdict(Counter)
            for record in raw:
                row = record["job"]["row"]
                if stage(row) == "after_relevant":
                    key = f"{row['frame']}/{row['relation']}"
                    cells[key]["n"] += 1
                    cells[key]["correct"] += int(record["result"]["execution"]["correct"])
            result[label]["relevant_update_counts"] = dict(cells)
    return result


def summarize(records, report):
    baseline = defaultdict(lambda: defaultdict(Counter))
    definitions = Counter()
    for record in records:
        row = record["job"]["row"]
        key = f"{row['frame']}/{row['relation']}/{stage(row)}"
        for name, choice in scripted_choices(row).items():
            if choice is None:
                continue
            for group in (key, "all/" + stage(row)):
                c = baseline[name][group]
                c["n"] += 1
                c["correct"] += int(score_command(row, choice)["correct"])
                c["agrees_with_model"] += int(choice == record["result"]["selected_command"])
        definitions[
            "revoked_target_applicable"
            if stage(row) == "after_relevant"
            else "revoked_target_structurally_inapplicable"
        ] += 1
    for groups in baseline.values():
        for counts in groups.values():
            counts["accuracy"] = counts["correct"] / counts["n"]
            counts["prediction_agreement"] = counts["agrees_with_model"] / counts["n"]
    frames = ("your", "their", "neutral")
    cells = report["cells"]
    accuracies = {
        relation: np.mean(
            [cells[f"{f}/{relation}/after_relevant"]["accuracy"] for f in frames]
        ).item()
        for relation in ("target", "other")
    }
    diagnostics = {}
    for stratum in ("before", "after_relevant", "after_irrelevant"):
        frame_means = {
            f: np.mean(
                [cells[f"{f}/{r}/{stratum}"]["accuracy"] for r in ("target", "other")]
            ).item()
            for f in frames
        }
        contrasts = {}
        for f in ("your", "their"):
            values = [
                np.mean(
                    [
                        world[f"{f}/{r}/{stratum}"]["accuracy"]
                        - world[f"neutral/{r}/{stratum}"]["accuracy"]
                        for r in ("target", "other")
                    ]
                )
                for _, world in sorted(report["per_world"].items())
            ]
            draws = np.random.default_rng(1729).choice(values, size=(10000, 48)).mean(axis=1)
            contrasts[f + "_minus_reference"] = {
                "estimate": float(np.mean(values)),
                "nominal_ci95": np.quantile(draws, [0.025, 0.975]).tolist(),
                "positive_worlds": sum(int(x > 0) for x in values),
                "negative_worlds": sum(int(x < 0) for x in values),
            }
        diagnostics[stratum] = {"frame_mean_accuracy": frame_means, "posthoc_contrasts": contrasts}
    delta = accuracies["other"] - accuracies["target"]
    return {
        "scripted_baselines": dict(baseline),
        "scripted_baseline_limit": (
            "Structured-state shortcut policies, not measured language-model competence "
            "or causal mixture proportions. always_active_actor is defined only for Your; "
            "context_named_actor is the explicit cross-frame extension."
        ),
        "primary_error_budget": {
            "accuracy": accuracies,
            "conditional_error_contrast_bounds": error_bounds(
                accuracies["target"], accuracies["other"]
            ),
            "categorical_contrast": report["primary"]["estimate"],
            "accuracy_gap_other_minus_target": delta,
            "remaining_error_contrast": delta - report["primary"]["estimate"],
            "interpretation": (
                "Bounds hold at fixed observed accuracies; not a pre-run impossibility "
                "or a causal explanation."
            ),
        },
        "frame_diagnostics": diagnostics,
        "frame_inference_status": (
            "Post hoc, six descriptive paired-world contrasts, nominal unadjusted intervals; "
            "no new confirmatory decision."
        ),
        "classification_applicability": dict(definitions),
    }


def main():
    records = read_archives()
    report = read_json(RESULTS / "analysis.json")
    assert digest(sorted(records, key=lambda r: r["id"])) == report["records_hash"]
    history = history_audit()
    output = summarize(records, report)
    old = history["possessive"]["relevant_update_counts"]["your/target"]
    old_error = 1 - old["correct"] / old["n"]
    new_error = 1 - report["cells"]["your/target/after_relevant"]["accuracy"]
    output.update(
        kind="cpu_design_review",
        model_inference=False,
        execution_enabled=False,
        input_analysis_sha256=file_hash(RESULTS / "analysis.json"),
        records_hash=report["records_hash"],
        review_source_sha256={
            path: file_hash(ROOT / path)
            for path in (
                "scripts/review_ownership_design.py",
                "src/self_model_study/action_task.py",
                "src/self_model_study/io.py",
            )
        },
        historical_prompt_audit=history,
        historical_your_target_error=old_error,
        current_your_target_error=new_error,
        error_rate_ratio=old_error / new_error,
    )
    OUTPUT.mkdir(exist_ok=True)
    pairs, probes, snapshots = [], [], []
    for record in sorted(records, key=lambda r: r["id"]):
        row = record["job"]["row"]
        if row["frame"] in {"your", "neutral"}:
            pairs.append(
                {
                    "source_id": row["id"],
                    "world": row["scenario_id"],
                    "compact_input": {"prompt": row["prompt"], "choices": row["choices"]},
                    "historical_template_input": {
                        "prompt": historical_named_prompt(row),
                        "choices": row["choices"],
                    },
                    "audit": {"target": row["target"], "expected_command": row["expected_command"]},
                }
            )
        if row["frame"] == "your" and row["relation"] == "target":
            probes.extend(
                {"source_id": row["id"], **query_reference_probe(row, view)}
                for view in ("self", "named_self", "other")
            )
            snapshots.append({"source_id": row["id"], **snapshot_probe(row)})
    for name, values in (
        ("named_template_pairs", pairs),
        ("query_reference_probes", probes),
        ("current_snapshot_controls", snapshots),
    ):
        raw = "".join(canonical(x) + "\n" for x in values).encode()
        path = OUTPUT / f"{name}.jsonl.gz"
        path.write_bytes(gzip.compress(raw, mtime=0))
        output[name] = {"rows": len(values), "sha256": file_hash(path), "model_evaluated": False}
    first = min(
        (r["job"]["row"] for r in records if r["job"]["row"]["phase"] == "after"),
        key=lambda r: r["id"],
    )
    write_json(
        OUTPUT / "their_reference_probes.json",
        {
            "kind": "unrun_semantic_examples",
            "model_inference": False,
            "selection_rule": (
                "Smallest recorded row ID after an update; no response-based selection."
            ),
            "examples": their_probes(first),
        },
    )
    write_json(OUTPUT / "audit.json", output)
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "records": len(records),
                "primary_error_budget": output["primary_error_budget"],
                "historical_error_ratio": output["error_rate_ratio"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
