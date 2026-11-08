"""Render the proposed measurement design; no model outcomes are depicted."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]


def render():
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.hashsalt": "confidence-design-v1"})
    fig, ax = plt.subplots(figsize=(13, 7), facecolor="#f7f9fc")
    ax.set(xlim=(0, 13), ylim=(0, 7))
    ax.axis("off")

    def box(x, y, width, height, title, body, color):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                width,
                height,
                boxstyle="round,pad=0.08,rounding_size=0.1",
                facecolor="white",
                edgecolor=color,
                linewidth=1.6,
            )
        )
        ax.text(
            x + 0.17,
            y + height - 0.25,
            title,
            color=color,
            fontsize=12,
            fontweight="bold",
            va="top",
        )
        ax.text(
            x + 0.17,
            y + height - 0.65,
            body,
            color="#233348",
            fontsize=10.2,
            va="top",
            linespacing=1.6,
        )

    def arrow(start, end, color="#64748b", dashed=False):
        ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=15,
                linewidth=1.6,
                color=color,
                linestyle="--" if dashed else "-",
            )
        )

    ax.text(
        0.25,
        6.6,
        "Does uncertainty change whether Qwen answers?",
        fontsize=21,
        color="#132d4e",
        fontweight="bold",
    )
    ax.text(
        0.25,
        6.15,
        "PROPOSED DESIGN  •  No new model results  •  No internal intervention",
        fontsize=11,
        color="#735524",
    )
    box(
        0.25,
        3.55,
        3.15,
        1.75,
        "128 factual questions",
        "Four options, four rotations\n512 dependent variants\nSame pinned Qwen checkpoint",
        "#1f5c91",
    )
    box(
        4.25,
        3.55,
        3.65,
        1.75,
        "1  Answer",
        "Choose an option: 1–4\n512 selections\nRecord correctness and scores",
        "#1f5c91",
    )
    box(
        8.75,
        3.55,
        3.95,
        1.75,
        "2  Assess that answer",
        "See the actual recorded answer\nReport confidence: ten bands\n"
        "512 selections; fresh forward pass",
        "#7a4f97",
    )
    box(
        4.25,
        0.95,
        3.65,
        1.85,
        "3  Answer or pass",
        "Original question + abstain option\n512 selections; fresh forward pass\n"
        "No earlier answer or report shown",
        "#287568",
    )
    box(
        8.75,
        0.95,
        3.95,
        1.85,
        "Compare the measurements",
        "More abstention after errors?\nConfidence beyond item difficulty?\n"
        "Resample questions, not variants",
        "#735524",
    )
    arrow((3.4, 4.45), (4.23, 4.45))
    arrow((7.9, 4.45), (8.73, 4.45))
    ax.plot([1.8, 1.8, 4.0], [3.47, 1.9, 1.9], color="#64748b", linewidth=1.6)
    arrow((4.0, 1.9), (4.23, 1.9))
    arrow((7.9, 1.9), (8.73, 1.9), dashed=True)
    arrow((10.7, 3.47), (10.7, 2.88), dashed=True)
    ax.text(
        0.25,
        0.48,
        "Separate calibration: 64 questions × 4 rotations = 256 selections. "
        "Total: 1,792 selections.",
        fontsize=10.5,
        color="#233348",
    )
    ax.text(
        0.25,
        0.1,
        "Arrows show data flow, not discovered causal links. "
        "Correct-answer keys stay outside model inputs.",
        fontsize=9.6,
        color="#64748b",
    )
    fig.subplots_adjust(left=0.015, right=0.99, top=0.99, bottom=0.035)
    target = ROOT / "assets"
    target.mkdir(exist_ok=True)
    for extension in ("svg", "pdf", "png"):
        metadata = (
            {"Date": None}
            if extension == "svg"
            else ({"CreationDate": None, "ModDate": None} if extension == "pdf" else {})
        )
        fig.savefig(target / f"confidence_design.{extension}", dpi=180, metadata=metadata)
    plt.close(fig)


if __name__ == "__main__":
    render()
