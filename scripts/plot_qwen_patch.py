"""Accessible article figure from the unchanged, hash-pinned patch archive."""

import json
from pathlib import Path

import matplotlib
from review_patch_evidence import ARCHIVE, SHA256
from review_qwen_evidence import archive_files

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def plot(output=Path("assets/qwen_role_patch_results/article_patch")):
    files, _, _ = archive_files(ARCHIVE, SHA256)
    report = json.loads(files["run/analysis.json"])
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.hashsalt": "qwen-patch-result-v1"})
    fig, (left, right) = plt.subplots(
        1, 2, figsize=(13, 5.8), gridspec_kw={"width_ratios": [1.2, 1]}
    )
    conditions = ["active/target", "active/other", "reference/target", "reference/other"]
    lookup = {(g["arm"], g["value"]): g for g in report["groups"] if g["axis"] == "cell"}
    for i, condition in enumerate(conditions):
        values = [
            100 * lookup[a, condition + "/after_relevant"]["estimate"] for a in ("baseline", "swap")
        ]
        left.plot(values, [i, i], color="#aab4ba", linewidth=3, zorder=1)
        for j, (v, color, marker) in enumerate(zip(values, ("#64748b", "#006579"), ("o", "D"))):
            left.scatter(
                v,
                i,
                c=color,
                marker=marker,
                s=65,
                zorder=3,
                label=("Baseline (= own-state patch)", "Matched exchange")[j] if i == 0 else None,
            )
            left.text(
                v,
                i + (-0.23 if j == 0 else 0.27),
                f"{v:.1f}%",
                ha="center",
                fontsize=9,
                color=color,
            )
    left.set(
        yticks=range(4),
        yticklabels=[
            "Active · target named",
            "Active · other named",
            "Reference · target named",
            "Reference · other named",
        ],
        xlim=(0, 105),
        ylim=(4.2, -0.7),
        xlabel="Correct commands (%) · 128 cases per cell",
        title="What changed after the relevant update?",
    )
    left.legend(loc="lower left", fontsize=9, frameon=False)
    stats = [
        report["transfer"]["swap"][k]
        for k in ("reference_to_active", "active_to_reference", "total")
    ]
    stats.append(report["primary_contrast"])
    for i, stat in enumerate(stats):
        v, (lo, hi) = 100 * stat["estimate"], [100 * x for x in stat["ci95"]]
        color = "#006579" if i < 3 else "#a35a27"
        right.errorbar(v, i, xerr=[[v - lo], [hi - v]], fmt="o", color=color, capsize=4)
        right.text(hi + 0.25, i, f"{v:+.2f}", va="center", fontsize=9, color=color)
    right.axvline(0, color="#94a3b8", linewidth=1)
    right.set(
        yticks=range(4),
        yticklabels=[
            "Reference → active",
            "Active → reference",
            "Average transfer T",
            "T − mean random T\n(primary C)",
        ],
        xlim=(-4, 11.2),
        ylim=(3.7, -0.7),
        xlabel="Transfer (percentage points)",
        title="One direction shifts; the reverse does not recover",
    )
    for ax in (left, right):
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)
    fig.suptitle("A state exchange did not meet the bidirectional-transfer rule", fontsize=15)
    fig.text(
        0.5,
        0.02,
        "11,264 choices · 8 already observed scenarios · all technical checks passed\n"
        "Nominal 95% scenario-bootstrap intervals. Primary exact sign-flip p = 0.109; "
        "5/8 scenario contrasts positive.\n"
        "Positive transfer means movement toward the donor's role gap, not higher accuracy. "
        "No functional dissociation established.",
        ha="center",
        fontsize=9,
        color="#475569",
    )
    fig.tight_layout(rect=(0, 0.15, 1, 0.93), w_pad=2.4)
    output.parent.mkdir(parents=True, exist_ok=True)
    for extension in ("svg", "pdf", "png"):
        metadata = (
            {"Date": None}
            if extension == "svg"
            else ({"CreationDate": None, "ModDate": None} if extension == "pdf" else {})
        )
        fig.savefig(output.with_suffix("." + extension), dpi=180, metadata=metadata)
    plt.close(fig)


if __name__ == "__main__":
    plot()
