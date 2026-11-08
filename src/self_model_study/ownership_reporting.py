"""Categorical audit and descriptive tranche report; no four-cell replication verdict."""

import shutil
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from .io import canonical, digest, write_json
from .ownership import CATEGORIES, DESIGN_PATH, INPUTS, PREFLIGHT, classify, read_run, stratum
from .pilot import jobs_in
from .pilot_reporting import portable_archive, save_figure, setup_plotting
from .storage import run_lock


def summarize(runs):
    jobs, records, manifests = {}, {}, []
    for manifest, plan, raw in runs:
        manifests.append(manifest)
        for job in jobs_in(plan):
            if job["id"] in jobs:
                raise ValueError("Overlapping tranche blocks; duplicate selections")
            jobs[job["id"]] = job
        records.update({r["id"]: r for r in raw})
    if (
        len({m["provenance"]["source_hash"] for m in manifests}) != 1
        or len({m["synthetic"] for m in manifests}) != 1
    ):
        raise ValueError("Cannot merge different source or synthetic/real runs")
    for key in ("tokenizer_vocabulary_hash", "chat_template_hash", "preflight_sha256"):
        if (
            not all(m["synthetic"] for m in manifests)
            and len({m["backend_info"].get(key) for m in manifests}) != 1
        ):
            raise ValueError("Cannot merge different tokenizer/preflight provenance")
    if not all(m["synthetic"] for m in manifests):
        for key in ("packages", "python", "git_commit"):
            if len({digest(m["provenance"][key]) for m in manifests}) != 1:
                raise ValueError("Cannot merge different execution provenance")
    cells, by_world, by_position, by_command = (
        defaultdict(Counter),
        defaultdict(lambda: defaultdict(Counter)),
        defaultdict(Counter),
        defaultdict(Counter),
    )
    paired = {field: defaultdict(dict) for field in ("target_identity", "phase", "grant_variant")}
    factors = (
        "target_identity",
        "updated",
        "phase",
        "grant_variant",
        "rotation",
        "frame",
        "relation",
    )
    for rid, job in jobs.items():
        row = job["row"]
        result = records.get(rid, {}).get("result")
        label = classify(row, result)
        key = "/".join((row["frame"], row["relation"], stratum(row)))
        cells[key][label] += 1
        by_world[row["scenario_id"]][key][label] += 1
        by_position[f"{key}/{row['expected_position']}"][label] += 1
        by_command[f"{key}/{row['expected_command']}"][label] += 1
        for field in paired:
            pairkey = (row["scenario_id"],) + tuple(row[k] for k in factors if k != field)
            paired[field][pairkey][row[field]] = (row["expected_command"], label)

    def cell(counts):
        n = sum(counts.values())
        return {
            "scheduled": n,
            "recorded": n - counts["missing"],
            "counts": {c: counts[c] for c in (*CATEGORIES, "missing")},
            "accuracy": counts["correct_target_current"] / n,
            "other_account_rate": counts["other_account_current"] / n,
        }

    primary = {}
    for sid, groups in sorted(by_world.items()):
        primary[sid] = np.mean(
            [
                cell(groups[f"{frame}/target/after_relevant"])["other_account_rate"]
                - cell(groups[f"{frame}/other/after_relevant"])["other_account_rate"]
                for frame in ("your", "their", "neutral")
            ]
        ).item()
    complete = (
        len(jobs) == len(records) == 18432
        and len(by_world) == 48
        and all(m["status"] == "complete" for m in manifests)
    )
    primary_report = {
        "estimate": float(np.mean(list(primary.values()))),
        "world_contrasts": primary,
        "ci95": None,
        "unadjusted_t_p": None,
        "multiplicity_status": "four-model/template family incomplete; no adjusted decision",
    }
    if complete:
        from scipy.stats import ttest_1samp

        xs = np.array(list(primary.values()))
        draws = np.random.default_rng(1729).choice(xs, size=(10000, 48), replace=True).mean(axis=1)
        primary_report["ci95"] = np.quantile(draws, [0.025, 0.975]).tolist()
        if np.var(xs, ddof=1) > 0:
            primary_report["unadjusted_t_p"] = float(ttest_1samp(xs, 0).pvalue)
    controls = {
        key: cell(counts) for key, counts in cells.items() if not key.endswith("after_relevant")
    }
    changed = {}
    for field, groups in paired.items():
        eligible = [
            list(pair.values())
            for pair in groups.values()
            if len(pair) == 2 and len({x[0] for x in pair.values()}) == 2
        ]
        changed[field] = {
            "scheduled_changed_pairs": len(eligible),
            "both_correct": sum(
                all(v[1] == "correct_target_current" for v in pair) for pair in eligible
            ),
            "missing_pairs": sum(any(v[1] == "missing" for v in pair) for pair in eligible),
        }
    return {
        "protocol": "ownership-replication-v1",
        "model_template": "Qwen2.5-7B-Instruct/permissions",
        "run_ids": [m["run_id"] for m in manifests],
        "source_hash": manifests[0]["provenance"]["source_hash"],
        "status": "complete" if complete else "incomplete_tranche",
        "complete": complete,
        "synthetic": any(m["synthetic"] for m in manifests),
        "scheduled_choices": len(jobs),
        "recorded_choices": len(records),
        "expected_tranche_choices": 18432,
        "independent_worlds": len(by_world),
        "records_hash": digest(sorted(records.values(), key=lambda r: r["id"])),
        "cells": {k: cell(v) for k, v in sorted(cells.items())},
        "per_world": {
            sid: {k: cell(v) for k, v in sorted(groups.items())}
            for sid, groups in sorted(by_world.items())
        },
        "by_position": {k: cell(v) for k, v in sorted(by_position.items())},
        "by_command": {k: cell(v) for k, v in sorted(by_command.items())},
        "changed_answer_pairs": changed,
        "primary": primary_report,
        "controls_pass": complete and all(v["accuracy"] >= 0.8 for v in controls.values()),
        "decision": "no_full_replication_or_equivalence_decision; three model/template cells unrun",
        "limits": (
            "All-choice denominators include missing/invalid outcomes. "
            "Partial tranche has no CI/test. "
            "Unadjusted test only when all 48 worlds are complete; Holm family and TOST decisions "
            "remain pending, never select models/templates to rescue significance."
        ),
    }


def markdown(report):
    lines = [
        "# Qwen / permissions: ownership replication tranche",
        "",
        "**SYNTHETIC SOFTWARE FIXTURE**"
        if report["synthetic"]
        else "Recorded model evidence; one model/template cell only.",
        "",
        f"Status: {report['status']}; "
        f"{report['recorded_choices']}/{report['expected_tranche_choices']} tranche choices.",
        report["decision"],
        "",
        report["limits"],
        "",
        "| Frame / mention / stage | Scheduled | Correct | Other current | Revoked target "
        "| Other valid | Invalid | Missing |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, v in report["cells"].items():
        c = v["counts"]
        lines.append(
            f"| {key} | {v['scheduled']} | {c['correct_target_current']} "
            f"| {c['other_account_current']} | {c['revoked_target']} "
            f"| {c['other_valid_command']} | {c['invalid']} | {c['missing']} |"
        )
    lines += [
        "",
        "Primary world-averaged other-command contrast: " + str(report["primary"]["estimate"]),
        "Nominal paired-world interval (complete tranche only): " + str(report["primary"]["ci95"]),
        "Unadjusted t-test (not a family decision): " + str(report["primary"]["unadjusted_t_p"]),
        "",
        "Full positions, commands, changed-answer pairs and world counts: analysis.json.",
        "No Mistral/routing inference or article update is authorized by this report.",
        "",
    ]
    return "\n".join(lines)


def plots(report, destination):
    plt = setup_plotting()
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    keys = [k for k in report["cells"] if k.endswith("after_relevant")]
    fig, ax = plt.subplots(figsize=(12, 5))
    bottom = np.zeros(len(keys))
    for category in (*CATEGORIES, "missing"):
        values = np.array(
            [report["cells"][k]["counts"][category] / report["cells"][k]["scheduled"] for k in keys]
        )
        ax.bar(range(len(keys)), values, bottom=bottom, label=category)
        bottom += values
    ax.set(
        xticks=range(len(keys)),
        xticklabels=[k.replace("/after_relevant", "").replace("/", "\n") for k in keys],
        ylabel="Fraction of scheduled choices",
        ylim=(0, 1),
        title="Target-relevant update: categorical outcomes",
    )
    ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1, 1))
    save_figure(fig, destination / "categorical_errors", report["synthetic"])
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(12, 4))
    values = report["primary"]["world_contrasts"]
    ax.bar(range(len(values)), list(values.values()))
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set(
        xlabel="Independent world (fixed order)",
        ylabel="Other-command target − other rate",
        title="Descriptive world contrasts; full family pending",
    )
    save_figure(fig, destination / "world_contrasts", report["synthetic"])
    plt.close(fig)


def analyze(directory):
    report = summarize([read_run(directory)])
    write_json(Path(directory) / "analysis.json", report)
    return report


def export(directory, destination):
    directory = Path(directory)
    with run_lock(directory):
        manifest, plan, records = read_run(directory)
        report = summarize([(manifest, plan, records)])
        write_json(directory / "analysis.json", report)
        (directory / "records.jsonl").write_text("".join(canonical(r) + "\n" for r in records))
        (directory / "report.md").write_text(markdown(report))
        source = directory / "source/ownership"
        source.mkdir(parents=True, exist_ok=True)
        for file in (DESIGN_PATH, PREFLIGHT, INPUTS):
            if file.exists():
                shutil.copy2(file, source / file.name)
        plots(report, directory / "figures")
        return portable_archive(directory, destination, manifest["status"])


def analyze_tranche(directories, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    report = summarize([read_run(path) for path in directories])
    write_json(destination / "analysis.json", report)
    (destination / "report.md").write_text(markdown(report))
    plots(report, destination / "figures")
    return report
