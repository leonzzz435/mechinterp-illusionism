"""One prespecified transfer-vs-random contrast; eight scenarios are the sampling units."""

from collections import defaultdict
from pathlib import Path

import numpy as np

from .io import source_hash, write_json
from .pilot import jobs_in
from .pilot_analysis import correct, estimate
from .role_control import stratum
from .role_control_analysis import sign_flip
from .role_patch import ARMS, read_run


def statistic(values):
    stat = estimate({k: [v] for k, v in values.items()})
    return {
        **stat,
        "scenario_means": values,
        "positive_scenarios": sum(v > 0 for v in values.values()),
        "two_sided_sign_flip_p": sign_flip(values),
    }


def margin(record, row):
    if record is None or record["status"] != "ok":
        return None
    other = next(a for a in row["state"]["permissions"] if a != row["target"])
    competitor = row["state"]["permissions"][other][0]
    scores = {c["command"]: c["log_likelihood"] for c in record["result"]["candidates"]}
    return scores[row["expected_command"]] - scores[competitor]


def decision(report, rules):
    if report["synthetic"]:
        return "synthetic_only"
    if not report["same_source_as_execution"]:
        return "source_mismatch"
    if report["technical_failures"] or report["status"] == "failed":
        return "technical_failure"
    if not report["coverage_complete"]:
        return "incomplete"
    if report["errors"]:
        return "measurement_failure"
    control = report["control_change"]
    if (
        not report["controls_passed"]
        or control["ci95"] is None
        or control["ci95"][0] <= rules["control_change_lower_bound"]
    ):
        return "stop_control_failure"
    transfer = report["transfer"]["swap"]
    total, primary = transfer["total"], report["primary_contrast"]
    if (
        total["estimate"] >= rules["minimum_transfer"]
        and total["ci95"][0] > 0
        and transfer["reference_to_active"]["estimate"] > 0
        and transfer["active_to_reference"]["estimate"] > 0
        and primary["ci95"][0] > 0
        and primary["two_sided_sign_flip_p"] <= rules["primary_two_sided_alpha"]
        and primary["positive_scenarios"] >= rules["minimum_positive_scenarios"]
    ):
        return "bidirectional_transfer_candidate"
    return "no_bidirectional_transfer_candidate"


def summarize(manifest, plan, records):
    jobs = jobs_in(plan)
    lookup = {r["id"]: r for r in records}
    scientific = [j for j in jobs if not j["technical"]]
    # Complete planned denominators, missing outputs stay explicitly missing, errors score zero.
    grouped, primary = defaultdict(list), defaultdict(list)
    for job in scientific:
        row, arm = job["row"], job["arm"]
        record = lookup.get(job["id"])
        condition = row["frame"] + "/" + row["relation"]
        axes = {
            "cell": condition + "/" + stratum(row),
            "position": str(row["expected_position"]),
            "identity": str(row["target_identity"]),
            "command": row["expected_command"],
        }
        for axis, value in axes.items():
            grouped[(arm, axis, value)].append((row, record))
        if stratum(row) == "after_relevant":
            primary[(arm, row["scenario_id"], row["frame"], row["relation"])].append((row, record))
    groups = []
    for (arm, axis, value), rows in sorted(grouped.items()):
        clusters = defaultdict(list)
        margins = defaultdict(list)
        observed = 0
        for row, record in rows:
            if record is not None:
                observed += 1
                clusters[row["scenario_id"]].append(correct(record))
                m = margin(record, row)
                if m is not None:
                    margins[row["scenario_id"]].append(m)
        groups.append(
            {
                "arm": arm,
                "axis": axis,
                "value": value,
                "expected": len(rows),
                "observed": observed,
                **estimate(clusters),
                "margin": estimate(margins),
            }
        )

    scenarios = sorted({j["row"]["scenario_id"] for j in scientific})
    transfers, margin_transfers = {}, {}
    for metric, destination in (("accuracy", transfers), ("margin", margin_transfers)):
        gaps = {}
        for arm in ARMS:
            for scenario in scenarios:
                for frame in ("active", "reference"):
                    cells = {}
                    for relation in ("target", "other"):
                        rows = primary[(arm, scenario, frame, relation)]
                        values = [
                            correct(r) if metric == "accuracy" else margin(r, row)
                            for row, r in rows
                        ]
                        if (
                            len(rows) == 16
                            and all(r is not None for _, r in rows)
                            and all(v is not None for v in values)
                        ):
                            cells[relation] = float(np.mean(values))
                    if len(cells) == 2:
                        gaps[(arm, scenario, frame)] = cells["other"] - cells["target"]
        for arm in ARMS:
            forward, reverse, total = {}, {}, {}
            for scenario in scenarios:
                keys = [(a, scenario, f) for a in ("self", arm) for f in ("active", "reference")]
                if all(k in gaps for k in keys):
                    forward[scenario] = (
                        gaps[("self", scenario, "active")] - gaps[(arm, scenario, "active")]
                    )
                    reverse[scenario] = (
                        gaps[(arm, scenario, "reference")] - gaps[("self", scenario, "reference")]
                    )
                    total[scenario] = (forward[scenario] + reverse[scenario]) / 2
            destination[arm] = {
                "reference_to_active": statistic(forward),
                "active_to_reference": statistic(reverse),
                "total": statistic(total),
            }
    contrast = {}
    for scenario in scenarios:
        if all(scenario in transfers[a]["total"]["scenario_means"] for a in ("swap", *ARMS[3:])):
            contrast[scenario] = transfers["swap"]["total"]["scenario_means"][scenario] - float(
                np.mean([transfers[a]["total"]["scenario_means"][scenario] for a in ARMS[3:]])
            )
    controls = [
        g
        for g in groups
        if g["arm"] == "swap" and g["axis"] == "cell" and not g["value"].endswith("after_relevant")
    ]
    control_change = defaultdict(list)
    by_base = {(j["base_id"], j["arm"]): lookup.get(j["id"]) for j in scientific}
    for j in scientific:
        if j["arm"] == "swap" and stratum(j["row"]) != "after_relevant":
            base, swapped = by_base[(j["base_id"], "baseline")], by_base[(j["base_id"], "swap")]
            if base is not None and swapped is not None:
                control_change[j["row"]["scenario_id"]].append(correct(swapped) - correct(base))
    technical = [c for r in records for c in r["result"].get("technical_checks", [])]
    norms = defaultdict(list)
    for r in records:
        if r["job"]["arm"].startswith("random_"):
            norms[r["job"]["arm"]].extend(
                c["patch"]["relative_norm_error"] for c in r["result"].get("candidates", [])
            )
    report = {
        "protocol": manifest["protocol"],
        "run_id": manifest["run_id"],
        "status": manifest["status"],
        "synthetic": manifest["synthetic"],
        "same_source_as_execution": manifest["provenance"]["source_hash"] == source_hash(),
        "expected_jobs": len(jobs),
        "completed_jobs": len(records),
        "scientific_expected": len(scientific),
        "scientific_completed": sum(not r["job"]["technical"] for r in records),
        "technical_repeats_completed": sum(r["job"]["technical"] for r in records),
        "coverage_complete": len(records) == len(jobs)
        and manifest["status"] in {"complete", "complete_with_errors"},
        "errors": sum(r["status"] != "ok" for r in records),
        "technical_failures": sum(not c["passed"] for c in technical),
        "technical_check_count": len(technical),
        "groups": groups,
        "transfer": transfers,
        "margin_transfer": margin_transfers,
        "primary_contrast": statistic(contrast),
        "control_cells": controls,
        "control_change": estimate(control_change),
        "controls_passed": len(controls) == 8
        and all(
            g["observed"] == g["expected"] and g["estimate"] is not None and g["estimate"] >= 0.8
            for g in controls
        ),
        "random_norm_error_max": {
            a: max(v for v in values if v is not None)
            if any(v is not None for v in values)
            else None
            for a, values in norms.items()
        },
        "note": "Exploratory intervention on eight known scenarios; no held-out confirmation. "
        "Intervals resample scenarios, not variants or random directions. "
        "The historical capability-screen failure is unchanged.",
    }
    report["decision"] = decision(report, manifest["config"]["decision"])
    return report


def analyze(directory):
    report = summarize(*read_run(directory))
    write_json(Path(directory) / "analysis.json", report)
    return report
