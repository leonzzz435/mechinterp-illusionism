"""Portable confidence evidence, prespecified examples and data-derived figures."""

import csv
from pathlib import Path

import numpy as np

from .confidence import read_run
from .confidence_analysis import analyze
from .io import canonical
from .pilot import jobs_in
from .pilot_reporting import portable_archive, save_figure, setup_plotting
from .storage import run_lock


def number(stat, scale=1):
    if not stat or stat["estimate"] is None:
        return "undefined / insufficient data"
    text = f"{stat['estimate'] * scale:.4f}"
    if stat["ci95"] is not None:
        text += f" [{stat['ci95'][0] * scale:.4f}, {stat['ci95'][1] * scale:.4f}]"
    return text


def plots(report, directory):
    plt = setup_plotting()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    synthetic = report["synthetic"]
    if not report["rows"]:
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.axis("off")
        ax.text(0.05, 0.6, "Incomplete run: no complete assessment question", fontsize=16)
        ax.text(
            0.05,
            0.35,
            f"Recorded {report['completed_jobs']} / {report['expected_jobs']} selections",
        )
        save_figure(fig, directory / "confidence_pending", synthetic)
        plt.close(fig)
        return
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    for ax, name, label in zip(
        axes,
        ("confidence", "raw_confidence", "calibrated_confidence"),
        ("Reported confidence", "Answer-menu confidence", "Calibrated answer confidence"),
    ):
        ax.plot([0, 1], [0, 1], "--", color="gray")
        for b in report["calibration_bins"][name]:
            if not b["count"]:
                continue
            x, y = b["mean_confidence"], b["accuracy"]["estimate"]
            ax.plot(x, y, "o", color="#006579")
            if b["accuracy"]["ci95"]:
                ax.vlines(x, *b["accuracy"]["ci95"], color="#006579")
            ax.annotate(
                str(b["count"]), (x, y), xytext=(4, 5), textcoords="offset points", fontsize=8
            )
        ax.set(
            xlim=(-0.03, 1.03),
            ylim=(-0.03, 1.08),
            xlabel="Confidence",
            ylabel="Fraction correct",
            title=label,
        )
    fig.suptitle("Calibration · labels are variant counts; intervals resample questions")
    fig.text(
        0.5,
        -0.04,
        f"{report['complete_assessment_questions']} complete questions; "
        "empty bins omitted, counts in analysis.json. "
        + (
            "COMPLETE-CASE DESCRIPTION OF INCOMPLETE RUN"
            if not report["complete"]
            else "Descriptive 95% intervals"
        ),
        ha="center",
        fontsize=9,
    )
    save_figure(fig, directory / "confidence_calibration", synthetic)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for x, name, label in (
        (0, "abstain_after_wrong", "Forced answer\nwas wrong"),
        (1, "abstain_after_correct", "Forced answer\nwas correct"),
    ):
        stat = report["metrics"][name]
        if stat["estimate"] is not None:
            axes[0].bar(x, stat["estimate"], color="#006579")
            if stat["ci95"]:
                axes[0].vlines(x, *stat["ci95"], color="black")
    axes[0].set(
        xticks=[0, 1],
        xticklabels=["Previously wrong", "Previously correct"],
        ylim=(0, 1.05),
        ylabel="Abstention rate",
        title="Does the model withhold unreliable answers?",
    )
    matrix = np.array(
        [
            [report["transitions"][f"{a}->{b}"] for b in ("correct", "wrong", "abstain")]
            for a in ("correct", "wrong")
        ]
    )
    axes[1].imshow(matrix, cmap="Blues", vmin=0)
    for (i, j), value in np.ndenumerate(matrix):
        axes[1].text(j, i, str(value), ha="center", va="center", color="black")
    axes[1].set(
        xticks=range(3),
        xticklabels=["Correct", "Wrong", "Abstain"],
        yticks=[0, 1],
        yticklabels=["Correct", "Wrong"],
        xlabel="Optional-answer stage",
        ylabel="Forced-answer stage",
        title="Revisions and abstentions (variant counts)",
    )
    fig.suptitle(f"{report['decision']} · primary S = {number(report['primary'], 100)} pp")
    save_figure(fig, directory / "confidence_behavior", synthetic)
    plt.close(fig)

    controls = report.get("conditional_predictors")
    if controls and controls["status"] == "ok":
        fig, ax = plt.subplots(figsize=(9, 5))
        for i, (name, stat) in enumerate(controls["loss_reductions"].items()):
            ax.plot(i, stat["estimate"], "o", color="#006579")
            if stat["ci95"]:
                ax.vlines(i, *stat["ci95"], color="#006579")
        ax.axhline(0, color="gray")
        ax.set(
            xticks=[0, 1],
            xticklabels=[
                "Add answer-score probability\nto external predictors",
                "Add verbal confidence\nto external + answer-score predictors",
            ],
            ylabel="Held-out log-loss reduction (nats)",
            title="Does the confidence report add predictive information?",
        )
        fig.text(
            0.5,
            -0.02,
            "Five folds grouped by question. Intervals conditional on fitted predictors.\n"
            "A positive value does not establish privileged introspection.",
            ha="center",
            fontsize=9,
        )
        save_figure(fig, directory / "confidence_controls", synthetic)
        plt.close(fig)


def article(report):
    return (
        "# Knowing an answer, reporting confidence, deciding to answer\n\n"
        + ("**SYNTHETIC SOFTWARE TEST — NO MODEL FINDING.**\n\n" if report["synthetic"] else "")
        + "We asked a fixed Qwen model factual multiple-choice questions, recorded its answers, "
        "asked for confidence in those actual answers, and separately offered abstention. "
        "The question is whether withholding an answer tracks its own earlier errors.\n\n"
        + f"The run contains {report['completed_jobs']} of {report['expected_jobs']} selections. "
        + f"Its decision is **{report['decision']}**. The difference between abstention rates "
        + "after wrong and correct forced answers is "
        + f"{number(report['primary'], 100)} percentage points. "
        + "Intervals resample whole questions, preserving their option rotations.\n\n"
        + "A new confidence prompt can solve the question again. Difficulty can also explain "
        "both mistakes and hesitation. External predictors and recorded answer transitions "
        "accompany the main result. No activations are changed; this establishes no causal "
        "link from the confidence report to abstention.\n\n"
        + "The philosophical interest is how a system constructs and uses judgments about itself. "
        "A useful judgment would be a limited functional result; human illusionism and subjective "
        "experience remain separate questions.\n"
    )


def markdown(report, plan, records):
    lines = [
        "# Qwen confidence/abstention pilot",
        "",
        article(report),
        "## Measurement and uncertainty",
        "",
        "Primary: S = P(abstain | forced wrong) − P(abstain | forced correct). "
        "10,000 paired question-bootstrap draws, seed 1729. Secondary intervals are descriptive. "
        "Conditional-predictor intervals do not include refitting uncertainty.",
        "",
        f"Complete assessment questions: {report['complete_assessment_questions']}. "
        f"Errors: {len(report['error_ids'])}; pending: {report['pending_jobs']}.",
        "",
        "| Quantity | Estimate [95% interval] |",
        "|---|---:|",
    ]
    for name, stat in report["metrics"].items():
        lines.append(f"| {name} | {number(stat)} |")
    lines += [
        "",
        "## Feasibility and controls",
        "",
        "```json",
        canonical(
            {
                k: report.get(k)
                for k in (
                    "feasibility",
                    "confidence_occupancy",
                    "menu_mass",
                    "transitions",
                    "breakdowns",
                )
            }
        ),
        "```",
        "",
        "Full calibration, grouped folds, predictions and model coefficients are in analysis.json.",
        "",
        "![Calibration](figures/confidence_calibration.png)",
        "",
        "![Behavior and revisions](figures/confidence_behavior.png)",
        "",
        "## Complete example fixed before inference",
        "",
    ]
    first = next(j["row"]["item_id"] for j in jobs_in(plan) if j["row"]["split"] == "assessment")
    by_id = {r["id"]: r for r in records}
    for job in jobs_in(plan):
        if job["row"]["item_id"] != first:
            continue
        result = by_id.get(job["id"], {}).get("result", {})
        lines += [
            f"### {first} / rotation {job['row']['rotation']} / {job['row']['phase']}",
            "",
            "```text",
            result.get("input_prompt", "[Pending or blocked dependent input]"),
            "```",
            "",
            "```json",
            canonical(result),
            "```",
            "",
        ]
    return "\n".join(lines)


def export(directory, destination):
    directory, destination = Path(directory), Path(destination)
    if destination.exists() or destination.resolve().is_relative_to(directory.resolve()):
        raise ValueError("Choose a new export path outside the run directory")
    with run_lock(directory):
        report = analyze(directory)
        _, plan, records = read_run(directory)
        (directory / "records.jsonl").write_text("".join(canonical(r) + "\n" for r in records))
        # The initial plan labels unresolved dependent inputs; this is the actual input ledger.
        (directory / "actual_inputs.jsonl").write_text(
            "".join(
                canonical(
                    {
                        "id": r["id"],
                        "input_prompt": r["result"].get("input_prompt"),
                        "rendered_prompt": r["result"].get("rendered_prompt"),
                        "parent_checksum": r["result"].get("parent_checksum"),
                        "status": r["status"],
                    }
                )
                + "\n"
                for r in records
            )
        )
        with (directory / "assessment.csv").open("w", newline="") as stream:
            fields = [
                "item_id",
                "rotation",
                "correct_position",
                "answer_position",
                "optional_answer",
                "correct",
                "optional_correct",
                "abstained",
                "confidence",
                "raw_confidence",
                "calibrated_confidence",
            ]
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(report["rows"])
        plots(report, directory / "figures")
        (directory / "report.md").write_text(markdown(report, plan, records))
        (directory / "article_section.md").write_text(article(report))
        return portable_archive(directory, destination, report["status"])
