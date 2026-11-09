"""Render two existing article cells; no model calls or statistical reanalysis."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "review/query-reference-stages/analysis.json"
SOURCE_SHA256 = "12d845d4f485da6022c5160479f7fa6bc223438fbb40efd9ccdd3b6a3de16052"
OUT = ROOT / "review/article-v2-editorial"


def render(out):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    payload = SOURCE.read_bytes()
    if hashlib.sha256(payload).hexdigest() != SOURCE_SHA256:
        raise ValueError("Stored stage results changed; refusing to relabel new evidence.")
    raw = json.loads(payload)["variants"]["frozen_v1"]
    keys = ("after_both/self/possessive", "after_both/self/account_name")
    cells = {key: raw["cells"][key] for key in keys}
    contrast_key = "after_both/self/account_minus_possessive"
    gap = raw["contrasts"][contrast_key]
    if gap["ci95"] is not None or any(c["accuracy"]["ci95"] is not None for c in cells.values()):
        raise ValueError("Expected original descriptive cells without inferential intervals.")
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {"svg.fonttype": "none", "svg.hashsalt": "article-v2-editorial", "font.size": 12}
    )
    fig, ax = plt.subplots(figsize=(12, 6.3))
    fig.subplots_adjust(left=0.28, right=0.93, bottom=0.32, top=0.70)
    ink, muted = "#172c3b", "#4b5e6a"
    values = [100 * c["accuracy"]["estimate"] for c in cells.values()]
    colors = ["#b45336", "#176b80"]
    ax.barh([1, 0], [100, 100], height=0.45, color="#edf1f3", zorder=1)
    ax.barh([1, 0], values, height=0.45, color=colors, zorder=2)
    for y, value in zip([1, 0], values):
        ax.text(
            value - 1.8,
            y,
            f"{value:.2f}%",
            ha="right",
            va="center",
            fontsize=20,
            weight="bold",
            color="white",
        )
    ax.set(
        xlim=(0, 100),
        ylim=(-0.5, 1.5),
        xticks=[0, 25, 50, 75, 100],
        yticks=[1, 0],
        yticklabels=["“your active connection”", "Direct account name"],
        xlabel="Correct command selections (%)",
    )
    ax.tick_params(axis="both", length=0, pad=10, colors=muted)
    ax.xaxis.label.set_color(muted)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.text(0.06, 0.91, "Same target. Different wording.", fontsize=25, weight="bold", color=ink)
    fig.text(
        0.06,
        0.84,
        "Qwen2.5-7B-Instruct · own account · both permission updates printed",
        fontsize=12,
        color=muted,
    )
    fig.text(
        0.06,
        0.20,
        f"{100 * gap['estimate']:.2f} percentage points",
        fontsize=21,
        weight="bold",
        color=ink,
    )
    fig.text(
        0.06, 0.15, "Paired world mean, computed before rounding the displayed rates.", color=muted
    )
    fig.text(
        0.06,
        0.08,
        "48 worlds · 1,536 selections per wording · original tie counted as failure",
        fontsize=10,
        color=muted,
    )
    fig.text(
        0.06,
        0.035,
        "Lookup controls failed. This difference does not establish a self-specific mechanism.",
        fontsize=10,
        color=muted,
    )
    for ext in ("svg", "pdf", "png"):
        metadata = (
            {"CreationDate": None, "ModDate": None}
            if ext == "pdf"
            else {"Date": None}
            if ext == "svg"
            else {}
        )
        dest = out / f"wording_comparison.{ext}"
        fig.savefig(dest, dpi=180, metadata=metadata)
        if ext == "svg":
            dest.write_text(
                "\n".join(line.rstrip() for line in dest.read_text().splitlines()) + "\n"
            )
    plt.close(fig)
    data = {
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": SOURCE_SHA256,
        "variant": "frozen_v1",
        "cells": cells,
        "contrast_key": contrast_key,
        "contrast": gap,
        "new_inference": False,
        "new_statistical_analysis": False,
        "status": "Original descriptive estimates; tie is failure; frozen lookup gates failed.",
        "display": "Two own-account forms; all three forms and both owners remain in the article.",
        "outputs": {
            f"wording_comparison.{ext}": hashlib.sha256(
                (out / f"wording_comparison.{ext}").read_bytes()
            ).hexdigest()
            for ext in ("svg", "pdf", "png")
        },
    }
    (out / "figure-data.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    render(args.out)


if __name__ == "__main__":
    main()
