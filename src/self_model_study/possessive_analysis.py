"""One prespecified accuracy interaction; reference and margins remain descriptive."""

from collections import defaultdict
from pathlib import Path

from .io import digest, source_hash, write_json
from .pilot import jobs_in
from .pilot_analysis import estimate
from .possessive import CONDITIONS, FRAMES, read_run, stratum
from .role_control_analysis import STRATA, correct, sign_flip


def margin(record, row):
    """Summed conditional command log-likelihood difference in nats, never confidence."""
    if record is None or record["status"] != "ok":
        return None
    scores = {c["command"]: c["log_likelihood"] for c in record["result"]["candidates"]}
    other = next(a for a in row["state"]["permissions"] if a != row["target"])
    return scores[row["expected_command"]] - scores[row["state"]["permissions"][other][0]]


def decision(report, rules):
    if report["synthetic"]:
        return "synthetic_only"
    if not report["same_source_as_execution"]:
        return "source_mismatch"
    if not report["coverage_complete"] or report["status"] not in {
        "complete",
        "complete_with_errors",
    }:
        return "incomplete"
    if report["errors"]:
        return "measurement_failure"
    if not report["controls_passed"]:
        return "stop_control_failure"
    stat = report["interaction"][rules["primary_stratum"]]
    if (
        stat["estimate"] >= rules["minimum_interaction"]
        and stat["ci95"][0] > 0
        and stat["positive_scenarios"] >= rules["minimum_positive_scenarios"]
        and stat["two_sided_sign_flip_p"] <= rules["primary_two_sided_alpha"]
    ):
        return "possessive_wording_candidate"
    return "no_clear_possessive_specificity"


def counterfactuals(jobs, records, samples):
    """Both changed-answer variants must be correct; retain all failed/invalid pairs."""
    factors = ("updated", "grant_variant", "target_identity", "phase", "rotation")
    output = {}
    for axis in ("target_identity", "phase", "grant_variant"):
        pairs = defaultdict(list)
        for job in jobs:
            row = job["row"]
            key = (
                row["scenario_id"],
                row["frame"],
                row["relation"],
                *(row[f] for f in factors if f != axis),
            )
            pairs[key].append(job)
        cells = defaultdict(list)
        for pair in pairs.values():
            if len(pair) != 2:
                raise ValueError("Incomplete counterfactual pair in frozen plan")
            if len({j["row"]["expected_command"] for j in pair}) == 2:
                row = pair[0]["row"]
                cells[f"{row['frame']}/{row['relation']}/{axis}"].append(pair)
        for key, selected in sorted(cells.items()):
            values = defaultdict(list)
            for pair in selected:
                if all(j["id"] in records for j in pair):
                    values[pair[0]["row"]["scenario_id"]].append(
                        int(all(correct(records[j["id"]]) for j in pair))
                    )
            output[key] = {
                "expected_pairs": len(selected),
                "observed_pairs": sum(map(len, values.values())),
                **estimate(values, samples),
            }
    return output


def summarize(manifest, plan, raw):
    jobs, records = jobs_in(plan), {r["id"]: r for r in raw}
    spec, samples = manifest["config"], manifest["config"]["bootstrap_samples"]
    cells, controls, commands, scenes = (
        defaultdict(list),
        defaultdict(list),
        defaultdict(list),
        defaultdict(dict),
    )
    for job in jobs:
        row = job["row"]
        prefix = f"{row['frame']}/{row['relation']}"
        cells[prefix + "/" + stratum(row)].append(job)
        commands[prefix + "/" + row["expected_command"]].append(job)
        scenes[row["scene_id"]][row["frame"], row["relation"]] = job
        axes = [
            ("target_identity", row["target_identity"]),
            ("answer_position", row["expected_position"]),
        ]
        if stratum(row) != "after_relevant":
            axes.append(("checkpoint", stratum(row)))
        for axis, value in axes:
            controls[f"{prefix}/{axis}/{value}"].append(job)

    def group_stat(selected):
        values = defaultdict(list)
        for job in selected:
            if job["id"] in records:
                values[job["row"]["scenario_id"]].append(correct(records[job["id"]]))
        return {
            "expected": len(selected),
            "observed": sum(map(len, values.values())),
            **estimate(values, samples),
        }

    deltas, margins, expected = (
        defaultdict(lambda: defaultdict(list)),
        defaultdict(lambda: defaultdict(list)),
        defaultdict(int),
    )
    for sextet in scenes.values():
        if set(sextet) != set(CONDITIONS):
            raise ValueError("Incomplete wording sextet in plan")
        row = next(iter(sextet.values()))["row"]
        stage, sid = stratum(row), row["scenario_id"]
        expected[stage] += 1
        if not all(j["id"] in records for j in sextet.values()):
            continue
        y = {key: correct(records[j["id"]]) for key, j in sextet.items()}
        m = {key: margin(records[j["id"]], j["row"]) for key, j in sextet.items()}
        for source, values in ((deltas, y), (margins, m)):
            if any(v is None for v in values.values()):
                continue
            gap = {f: values[f, "other"] - values[f, "target"] for f in FRAMES}
            for f in FRAMES:
                source[f + "/" + stage][sid].append(gap[f])
            source["interaction/" + stage][sid].append(gap["your"] - gap["the"])
            source["reference_anchor/" + stage][sid].append(gap["your"] - gap["reference"])

    def paired_stats(source, label, stage, primary=False):
        values = source[label + "/" + stage]
        n = sum(map(len, values.values()))
        usable = values if n == expected[stage] else {}
        means = {s: sum(v) / len(v) for s, v in sorted(usable.items())}
        return {
            "expected_sextets": expected[stage],
            "observed_sextets": n,
            "complete_pairs": n == expected[stage],
            **estimate(usable, samples),
            "scenario_means": means,
            "positive_scenarios": sum(v > 0 for v in means.values()),
            "two_sided_sign_flip_p": sign_flip(means) if primary else None,
        }

    control_stats = {key: group_stat(v) for key, v in sorted(controls.items())}
    report = {
        "protocol": manifest["protocol"],
        "run_id": manifest["run_id"],
        "status": manifest["status"],
        "synthetic": manifest["synthetic"],
        "coverage_complete": len(records) == len(jobs),
        "expected_jobs": len(jobs),
        "completed_jobs": len(records),
        "errors": sum(r["status"] != "ok" for r in raw),
        "same_source_as_execution": manifest["provenance"]["source_hash"] == source_hash(),
        "analysis_source_hash": source_hash(),
        "records_hash": digest(raw),
        "cells": {key: group_stat(v) for key, v in sorted(cells.items())},
        "controls": control_stats,
        "controls_passed": all(
            c["observed"] == c["expected"]
            and c["estimate"] is not None
            and c["estimate"] >= spec["decision"]["control_accuracy"]
            for c in control_stats.values()
        ),
        "command_accuracy": {key: group_stat(v) for key, v in sorted(commands.items())},
        "counterfactuals": counterfactuals(jobs, records, samples),
        "assignment_gaps": {
            f + "/" + s: paired_stats(deltas, f, s) for f in FRAMES for s in STRATA
        },
        "interaction": {
            s: paired_stats(
                deltas, "interaction", s, primary=s == spec["decision"]["primary_stratum"]
            )
            for s in STRATA
        },
        "reference_anchor": {s: paired_stats(deltas, "reference_anchor", s) for s in STRATA},
        "margin_effects_nats": {
            f + "/" + s: paired_stats(margins, f, s)
            for f in (*FRAMES, "interaction", "reference_anchor")
            for s in STRATA
        },
        "internal_intervention_authorized": False,
        "original_capability_screen_changed": False,
        "note": "Sixteen fresh development instances of the same template and vocabulary. "
        "One primary Your/The accuracy interaction after relevant updates. Reference anchor, "
        "margins, counterfactual pairs and other strata are descriptive. Bootstrap resamples "
        "scenarios, never variants. Exact sign flips assume symmetric independent null effects. "
        "No equivalence, self-monitoring, consciousness or human-illusionism conclusion. "
        "A candidate permits interpretation and planning only; no automatic intervention.",
    }
    report["decision"] = decision(report, spec["decision"])
    return report


def analyze(directory):
    result = summarize(*read_run(directory))
    write_json(Path(directory) / "analysis.json", result)
    return result
