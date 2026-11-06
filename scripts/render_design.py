#!/usr/bin/env python3
"""Render a design diagram; this is not a measured neural mechanism."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from self_model_study.reporting import save_figure


def main():
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor("#f7f7f2")
    ax.set(xlim=(0, 12), ylim=(0, 5))
    ax.axis("off")
    boxes = [
        (
            0.3,
            1.5,
            "Matched scenarios",
            "Role · observations · actions\nSelf / other · swapped facts",
        ),
        (
            4.3,
            1.5,
            "Registered intervention",
            "Baseline · additions · ablations\nSaved scale and random controls",
        ),
        (8.3, 2.8, "Language assay", "Self-reference and coherence\nBlinded ratings"),
        (8.3, 0.3, "Task assay", "Correct role-conditioned choice\nSelf / other accuracy"),
    ]
    for x, y, title, subtitle in boxes:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                3.25,
                1.35,
                boxstyle="round,pad=0.12",
                facecolor="white",
                edgecolor="#005f73",
                linewidth=1.6,
            )
        )
        ax.text(x + 1.625, y + 0.95, title, ha="center", va="center", fontsize=12, weight="bold")
        ax.text(
            x + 1.625, y + 0.43, subtitle, ha="center", va="center", fontsize=10, color="#334155"
        )
    for start, end in [
        ((3.7, 2.15), (4.1, 2.15)),
        ((7.7, 2.15), (8.1, 3.45)),
        ((7.7, 2.15), (8.1, 0.95)),
    ]:
        ax.add_patch(
            FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=16, color="#005f73")
        )
    ax.text(
        6,
        4.75,
        "What changes when a model represents itself?",
        ha="center",
        fontsize=18,
        weight="bold",
    )
    ax.text(
        6,
        -0.02,
        "Experimental design — not a consciousness measure or a discovered circuit",
        ha="center",
        fontsize=10,
        color="#475569",
    )
    out = Path("assets/study_design")
    out.parent.mkdir(exist_ok=True)
    save_figure(fig, out)
    plt.close(fig)


if __name__ == "__main__":
    main()
