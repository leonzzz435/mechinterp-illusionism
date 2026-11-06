"""Article view of archived Qwen results; overall plus all relevant-update perspectives."""

import argparse
import hashlib
import json
import tarfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ARCHIVE = Path("review/evidence/qwen-78ee6db8adfc4f3e.tar.gz")
SHA256 = "cf8eceea87129acaad2365f36af99d8f54923015923c837419a691252b8f12fa"


def plot(archive=ARCHIVE, output=Path("assets/qwen_pilot_results/article_action")):
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Expected the unchanged original Qwen export")
    with tarfile.open(archive) as bundle:
        report = json.load(bundle.extractfile("run/analysis.json"))
    selected = [
        ("overall", "all", "All choices"),
        (
            "view_update",
            "self/after_relevant",
            'Your permission changed\n("your active connection")',
        ),
        ("view_update", "named_self/after_relevant", "Your permission changed\n(connection named)"),
        ("view_update", "other/after_relevant", "Other connection's\npermission changed"),
    ]
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.hashsalt": "qwen-article-v1"})
    fig, ax = plt.subplots(figsize=(11, 5.6))
    for fmt, offset, color in (("plain", -0.14, "#be6a2e"), ("chat", 0.14, "#006579")):
        for index, (axis, value, _) in enumerate(selected):
            g = next(
                g
                for g in report["action_groups"]
                if (g["format"], g["axis"], g["value"]) == (fmt, axis, value)
            )
            point = 100 * g["estimate"]
            low, high = [100 * v for v in g["ci95"]]
            ax.errorbar(
                point,
                index + offset,
                xerr=[[point - low], [high - point]],
                fmt="o",
                color=color,
                capsize=3,
                markersize=7,
                label={"plain": "Plain text", "chat": "Chat format"}[fmt] if index == 0 else None,
            )
            ax.text(high + 1.5, index + offset, f"{point:.1f}%", va="center", color=color)
    ax.axvline(80, color="#999999", linestyle="--", linewidth=1.3)
    ax.axhline(0.55, color="#dddddd", linewidth=1)
    ax.set(yticks=range(4), yticklabels=[r[2] for r in selected], xlim=(0, 112), ylim=(3.6, -0.6))
    ax.set_xticks(range(0, 101, 20))
    ax.set_xlabel("Correct command selections (%)")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=14)
    ax.legend(loc="lower left", frameon=False)
    fig.suptitle("High overall accuracy can conceal failures after permission changes", fontsize=14)
    fig.text(
        0.5,
        0.015,
        "Qwen2.5-7B-Instruct · 8 development scenarios · nominal 95% scenario-bootstrap intervals\n"
        "Dashed line: 80% screen threshold. Both formats fail the full 24-check screen.",
        ha="center",
        fontsize=9,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.085, 1, 0.95))
    output.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("svg", "pdf", "png"):
        metadata = (
            {"Date": None} if ext == "svg" else {"CreationDate": None} if ext == "pdf" else {}
        )
        fig.savefig(output.with_suffix("." + ext), dpi=180, metadata=metadata)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    parser.add_argument(
        "--out", type=Path, default=Path("assets/qwen_pilot_results/article_action")
    )
    args = parser.parse_args()
    plot(args.archive, args.out)
