"""Reader-facing figure from the unchanged, hash-pinned wording-control archive."""

import json
from pathlib import Path

import matplotlib
from review_possessive_evidence import ARCHIVE, SHA256
from review_qwen_evidence import archive_files

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def plot(output=Path("assets/qwen_possessive_results/article_possessive")):
    files, _, _ = archive_files(ARCHIVE, SHA256)
    report = json.loads(files["run/analysis.json"])
    plt.rcParams.update(
        {"font.family": "DejaVu Sans", "svg.fonttype": "none", "svg.hashsalt": "possessive-v1"}
    )
    fig, (left, right) = plt.subplots(
        1, 2, figsize=(13, 6.2), gridspec_kw={"width_ratios": [1.25, 1]}
    )
    colors = ("#a35a27", "#006579")
    for i, frame in enumerate(("your", "the", "reference")):
        stats = [report["cells"][f"{frame}/{r}/after_relevant"] for r in ("target", "other")]
        values = [100 * s["estimate"] for s in stats]
        left.plot(values, [i, i], color="#cbd5e1", linewidth=3, zorder=1)
        for j, (stat, value) in enumerate(zip(stats, values)):
            lo, hi = [100 * x for x in stat["ci95"]]
            left.errorbar(
                value,
                i,
                xerr=[[value - lo], [hi - value]],
                fmt=("o", "D")[j],
                color=colors[j],
                capsize=4,
                zorder=3,
                label=("Context names queried account", "Context names other account")[j]
                if i == 0
                else None,
            )
            left.text(value, i - 0.22, f"{value:.1f}%", ha="center", fontsize=10, color=colors[j])
        gap = report["assignment_gaps"][frame + "/after_relevant"]["estimate"]
        left.text(51, i + 0.24, f"Role gap: {100 * gap:.2f} pp", fontsize=9, color="#475569")
    left.set(
        yticks=range(3),
        yticklabels=["Your active\nconnection", "The active\nconnection", "Reference\nconnection"],
        xlim=(49, 105),
        ylim=(3.0, -0.55),
        xlabel="Correct commands (%) · 256 cases per cell",
        title="The large role gap survives without “your”",
    )
    left.legend(loc="lower left", fontsize=9, frameon=False)
    for i, (key, color) in enumerate((("interaction", "#a35a27"), ("reference_anchor", "#64748b"))):
        stat = report[key]["after_relevant"]
        value = 100 * stat["estimate"]
        lo, hi = [100 * x for x in stat["ci95"]]
        right.errorbar(value, i, xerr=[[value - lo], [hi - value]], fmt="o", color=color, capsize=5)
        right.text(value, i - 0.2, f"{value:+.2f} pp", ha="center", color=color, fontsize=11)
        right.text(value, i + 0.21, f"[{lo:+.2f}, {hi:+.2f}]", ha="center", color=color, fontsize=9)
    right.axvline(0, color="#94a3b8", linewidth=1)
    right.set(
        yticks=[0, 1],
        yticklabels=["Your − The\nPRIMARY", "Your − Reference\ndescriptive"],
        xlim=(-3, 21),
        ylim=(1.65, -0.55),
        xlabel="Difference between role gaps (percentage points)",
        title="The possessive-specific criterion was not met",
    )
    for ax in (left, right):
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)
    fig.suptitle("One word changes; the main behavioral pattern remains", fontsize=16)
    primary = report["interaction"]["after_relevant"]
    margin = report["margin_effects_nats"]["interaction/after_relevant"]
    fig.text(
        0.5,
        0.035,
        "Qwen2.5-7B-Instruct · relevant permission updates · "
        f"{primary['n_clusters']} fresh development scenarios\n"
        "Nominal 95% scenario-bootstrap intervals. Primary exact sign-flip "
        f"p = {primary['two_sided_sign_flip_p']}; "
        f"{primary['positive_scenarios']}/{primary['n_clusters']} contrasts positive.\n"
        f"A secondary likelihood-margin shift remains ({margin['estimate']:+.3f} nats): "
        "failed accuracy criterion does not mean zero influence.",
        ha="center",
        fontsize=9,
        color="#475569",
    )
    fig.tight_layout(rect=(0, 0.17, 1, 0.93), w_pad=2.7)
    output.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("svg", "pdf", "png"):
        metadata = (
            {"CreationDate": None, "ModDate": None}
            if ext == "pdf"
            else ({"Date": None} if ext == "svg" else {})
        )
        fig.savefig(output.with_suffix("." + ext), dpi=180, bbox_inches="tight", metadata=metadata)
    plt.close(fig)


if __name__ == "__main__":
    plot()
