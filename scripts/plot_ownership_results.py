"""Plot the completed tranche's descriptive 2x2 from saved aggregate counts."""

from pathlib import Path

import numpy as np

from self_model_study.io import read_json
from self_model_study.pilot_reporting import setup_plotting

ROOT = Path(__file__).resolve().parents[1]


def main():
    directory = ROOT / "review/ownership-permissions-results"
    report = read_json(directory / "analysis.json")
    if not report["complete"] or report["synthetic"]:
        raise ValueError("Expected the completed real-model tranche")
    plt = setup_plotting()
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.4), sharey=True)
    for ax, stage, title in zip(
        axes,
        ("after_relevant", "after_irrelevant"),
        ("Queried account was updated", "Other account was updated"),
    ):
        values = np.array(
            [
                [
                    100 * report["cells"][f"{frame}/{relation}/{stage}"]["accuracy"]
                    for relation in ("target", "other")
                ]
                for frame in ("your", "their", "neutral")
            ]
        )
        heatmap = ax.imshow(values, vmin=0, vmax=100, cmap="cividis", aspect="auto")
        ax.set(
            xticks=[0, 1],
            xticklabels=["Query account\nnamed in context", "Other account\nnamed in context"],
            yticks=[0, 1, 2],
            yticklabels=[
                "Your active connection",
                "Their active connection",
                "Reference connection",
            ],
            title=title,
        )
        for (row, column), value in np.ndenumerate(values):
            ax.text(
                column,
                row,
                f"{value:.1f}%",
                ha="center",
                va="center",
                fontsize=15,
                color="black" if value >= 65 else "white",
                fontweight="bold",
            )
    fig.suptitle(
        "Qwen: accurate on the updated account, weak on the unchanged account", fontsize=14
    )
    fig.text(
        0.5,
        0.035,
        "48 fresh worlds · 768 choices per cell · descriptive accuracy\n"
        "All six right-hand cells fail the prespecified 80% competence threshold.",
        ha="center",
        fontsize=10,
    )
    fig.subplots_adjust(left=0.24, right=0.9, top=0.83, bottom=0.22, wspace=0.12)
    bar = fig.add_axes((0.92, 0.25, 0.015, 0.55))
    fig.colorbar(heatmap, cax=bar, label="Correct selections (%)")
    # Preserve the manual caption/colorbar layout; the shared helper calls tight_layout.
    for ext in ("svg", "pdf", "png"):
        metadata = (
            {"CreationDate": None, "ModDate": None}
            if ext == "pdf"
            else {"Date": None}
            if ext == "svg"
            else {}
        )
        fig.savefig(
            directory / f"figures/update_account_accuracy.{ext}",
            dpi=180,
            bbox_inches="tight",
            metadata=metadata,
        )
    plt.close(fig)


if __name__ == "__main__":
    main()
