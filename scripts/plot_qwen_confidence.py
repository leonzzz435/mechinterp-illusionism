"""Reader-facing confidence overview, generated only from a hash-verified result archive."""

import argparse
import json
from pathlib import Path

import matplotlib
from review_qwen_evidence import archive_files, require

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def plot(archive, checksum, output=Path("assets/qwen_confidence_results/article_confidence")):
    files, _, _ = archive_files(archive, checksum)
    report = json.loads(files["run/analysis.json"])
    require(report["complete"] and not report["synthetic"], "Requires complete real-model evidence")
    plt.rcParams.update(
        {"font.family": "DejaVu Sans", "svg.fonttype": "none", "svg.hashsalt": "confidence-v2"}
    )
    fig, axes = plt.subplots(1, 3, figsize=(15, 6.2))
    blue, orange = "#006579", "#a35a27"
    for x, (key, color) in enumerate(
        (("abstain_after_wrong", orange), ("abstain_after_correct", blue))
    ):
        stat = report["metrics"][key]
        axes[0].bar(x, 100 * stat["estimate"], color=color, width=0.55)
        if stat["ci95"]:
            axes[0].vlines(x, *[100 * v for v in stat["ci95"]], color="black", linewidth=1.5)
        axes[0].text(x, 100 * stat["estimate"] + 10, f"{100 * stat['estimate']:.1f}%", ha="center")
    axes[0].set(
        xticks=[0, 1],
        xticklabels=["Wrong", "Correct"],
        ylim=(0, 112),
        ylabel="Abstention rate (%)",
        xlabel="Recorded forced answer",
        title="1  When does it decline to answer?",
    )
    primary = report["primary"]
    estimate = (
        "undefined" if primary["estimate"] is None else f"{100 * primary['estimate']:+.1f} pp"
    )
    if primary["ci95"]:
        estimate += f" [{100 * primary['ci95'][0]:+.1f}, {100 * primary['ci95'][1]:+.1f}]"
    axes[0].text(
        0.5,
        0.97,
        f"Primary difference: {estimate}",
        transform=axes[0].transAxes,
        ha="center",
        va="top",
        fontsize=10,
    )
    axes[1].plot([0, 100], [0, 100], "--", color="#94a3b8", label="Perfect calibration")
    for b in report["calibration_bins"]["confidence"]:
        if not b["count"]:
            continue
        x, y = 100 * b["mean_confidence"], 100 * b["accuracy"]["estimate"]
        axes[1].scatter(x, y, s=30 + b["count"], color=blue, alpha=0.8, zorder=3)
        if b["accuracy"]["ci95"]:
            axes[1].vlines(x, *[100 * v for v in b["accuracy"]["ci95"]], color=blue)
        axes[1].annotate(
            str(b["count"]), (x, y), xytext=(6, 4), textcoords="offset points", fontsize=8
        )
    axes[1].set(
        xlim=(-3, 110),
        ylim=(-3, 110),
        xlabel="Reported confidence (%)",
        ylabel="Answers actually correct (%)",
        title="2  How well does confidence track truth?",
    )
    axes[1].legend(loc="upper left", fontsize=9, frameon=False)
    controls = report["conditional_predictors"]
    if controls and controls["status"] == "ok":
        for i, key in enumerate(("E+Q", "E+Q+V")):
            stat = controls["loss_reductions"][key]
            axes[2].plot(stat["estimate"], i, "o", color=blue)
            if stat["ci95"]:
                axes[2].hlines(i, *stat["ci95"], color=blue)
            axes[2].annotate(
                f"{stat['estimate']:+.3f}",
                (stat["estimate"], i),
                xytext=(0, 12),
                textcoords="offset points",
                ha="center",
                fontsize=10,
            )
        axes[2].axvline(0, color="#94a3b8", linewidth=1)
        axes[2].set(
            yticks=[0, 1],
            yticklabels=["+ Answer\nprobability", "+ Reported\nconfidence"],
            ylim=(1.6, -0.6),
            xlabel="Prediction improvement (log-loss reduction)",
            title="3  Does the self-report add information?",
        )
        axes[2].margins(x=0.25)
    else:
        axes[2].axis("off")
        axes[2].text(0.1, 0.5, "Conditional comparison unavailable", transform=axes[2].transAxes)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("An answer, a confidence judgment, and the option to pass", fontsize=17, y=0.98)
    n = report["complete_assessment_questions"]
    fig.text(
        0.5,
        0.03,
        f"Qwen2.5-7B-Instruct · {n} questions × 4 answer rotations · "
        "95% question-bootstrap intervals\n"
        "Middle: labels count variants; sparse bins can lack intervals. "
        "Right: five folds grouped by question; "
        "intervals conditional on fitted predictors.\n"
        "External predictors: published difficulty, question embeddings and answer position. "
        "The confidence report is not supplied to the abstention stage.",
        ha="center",
        fontsize=9,
        color="#475569",
    )
    fig.tight_layout(rect=(0, 0.16, 1, 0.94), w_pad=2.5)
    output.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("svg", "pdf", "png"):
        metadata = (
            {"CreationDate": None, "ModDate": None}
            if ext == "pdf"
            else {"Date": None}
            if ext == "svg"
            else {}
        )
        fig.savefig(output.with_suffix("." + ext), dpi=180, bbox_inches="tight", metadata=metadata)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive")
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    plot(args.archive, args.sha256)
