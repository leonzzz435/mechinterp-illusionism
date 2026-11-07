"""Prespecified scenario-level framing interaction and bounded follow-up decision."""

from collections import defaultdict
from itertools import product
from pathlib import Path

import numpy as np

from .io import digest, source_hash, write_json
from .pilot import jobs_in
from .pilot_analysis import estimate
from .role_control import CONDITIONS, FRAMES, read_run, stratum

STRATA = ("before", "after_relevant", "after_irrelevant")


def correct(record):
    return int(record["status"] == "ok" and record["result"]["execution"]["correct"])


def sign_flip(scenario_means):
    """Exact two-sided sign-flip sensitivity, assuming symmetric independent null effects."""
    values = np.array(list(scenario_means.values()), dtype=float)
    if not len(values):
        return None
    observed = abs(values.mean())
    null = np.array(list(product((-1, 1), repeat=len(values)))) @ values / len(values)
    return float(np.mean(abs(null) >= observed - 1e-12))


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
    main = report["interaction"][rules["primary_stratum"]]
    active = report["assignment_gaps"]["active/" + rules["primary_stratum"]]
    if active["estimate"] < rules["minimum_active_gap"]:
        return "stop_assignment_gap_not_replicated"
    if (
        main["estimate"] >= rules["minimum_interaction"]
        and main["ci95"] is not None
        and main["ci95"][0] > 0
        and main["positive_scenarios"] >= rules["minimum_positive_scenarios"]
        and main["two_sided_sign_flip_p"] <= rules["primary_two_sided_alpha"]
    ):
        return "wording_sensitive_candidate"
    return "stop_no_clear_wording_specificity"


def summarize(manifest, plan, raw):
    """Called only after run integrity validation; also accepts explicit CPU fixtures in tests."""
    jobs, records = jobs_in(plan), {r["id"]: r for r in raw}
    spec = manifest["config"]
    samples = spec["bootstrap_samples"]
    cells, scenes, controls = defaultdict(list), defaultdict(dict), defaultdict(list)
    for job in jobs:
        row = job["row"]
        key = "/".join((row["frame"], row["relation"], stratum(row)))
        cells[key].append(job)
        scenes[row["scene_id"]][(row["frame"], row["relation"])] = job
        control_axes = [
            ("target_identity", row["target_identity"]),
            ("answer_position", row["expected_position"]),
        ]
        if stratum(row) != "after_relevant":
            control_axes.append(("checkpoint", stratum(row)))
        for axis, value in control_axes:
            controls[f"{row['frame']}/{row['relation']}/{axis}/{value}"].append(job)

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

    cells = {key: group_stat(value) for key, value in sorted(cells.items())}
    controls = {key: group_stat(value) for key, value in sorted(controls.items())}
    deltas, interaction, expected = defaultdict(lambda: defaultdict(list)), {}, defaultdict(int)
    for quartet in scenes.values():
        if set(quartet) != set(CONDITIONS):
            raise ValueError("Incomplete framing quartet in plan")
        row = next(iter(quartet.values()))["row"]
        stage, sid = stratum(row), row["scenario_id"]
        expected[stage] += 1
        if not all(j["id"] in records for j in quartet.values()):
            continue
        y = {key: correct(records[j["id"]]) for key, j in quartet.items()}
        for frame in FRAMES:
            deltas[f"{frame}/{stage}"][sid].append(y[frame, "other"] - y[frame, "target"])
        deltas["interaction/" + stage][sid].append(
            (y["active", "other"] - y["active", "target"])
            - (y["reference", "other"] - y["reference", "target"])
        )
    gaps = {}
    for stage in STRATA:
        for frame in (*FRAMES, "interaction"):
            key = frame + "/" + stage
            values = deltas[key]
            n = sum(map(len, values.values()))
            complete = n == expected[stage]
            usable = values if complete else {}
            stat = {
                "expected_quartets": expected[stage],
                "observed_quartets": n,
                "complete_pairs": complete,
                **estimate(usable, samples),
            }
            if frame != "interaction":
                gaps[key] = stat
            else:
                means = {sid: sum(v) / len(v) for sid, v in sorted(usable.items())}
                stat.update(
                    scenario_means=means,
                    positive_scenarios=sum(v > 0 for v in means.values()),
                    degenerate_interval=bool(stat["ci95"] and stat["ci95"][0] == stat["ci95"][1]),
                    two_sided_sign_flip_p=(
                        sign_flip(means) if stage == spec["decision"]["primary_stratum"] else None
                    ),
                )
                interaction[stage] = stat
    control_pass = all(
        c["expected"] == c["observed"]
        and c["estimate"] is not None
        and c["estimate"] >= spec["decision"]["control_accuracy"]
        for c in controls.values()
    )
    result = {
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
        "cells": cells,
        "controls": controls,
        "controls_passed": control_pass,
        "assignment_gaps": gaps,
        "interaction": interaction,
        "internal_intervention_authorized": False,
        "original_capability_screen_changed": False,
        "note": "Eight development scenarios. One primary interaction; secondary intervals "
        "are exploratory. Sign-flip inference assumes symmetric independent scenario effects. "
        "No equivalence, consciousness or human-illusionism conclusion. A candidate permits "
        "planning only; all other substantive outcomes close this diagnostic branch.",
    }
    result["decision"] = decision(result, spec["decision"])
    return result


def analyze(directory):
    result = summarize(*read_run(directory))
    write_json(Path(directory) / "analysis.json", result)
    return result
