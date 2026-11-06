"""Display supplied human judgments and paired format effects from the rated export."""

import argparse
import json
from pathlib import Path

import matplotlib
from review_qwen_evidence import archive_files, audit_ratings

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ARCHIVE = Path("review/evidence/qwen-78ee6db8adfc4f3e-with-ratings-v1.tar.gz")
SHA256 = "c260bb001dac8841def6bdb28d7b5e418e9f329c44e005602f5467bd40c3aa9b"


def plot(archive=ARCHIVE, output=Path("assets/qwen_pilot_results/article_language")):
    files, _, _ = archive_files(archive, SHA256)
    report = json.loads(files["run/analysis.json"])
    jobs = {j["id"]: j for b in json.loads(files["run/plan.json"])["blocks"] for j in b["jobs"]}
    rows = [json.loads(line) for line in files["run/records.jsonl"].splitlines()]
    human = audit_ratings(files, jobs, {r["id"]: r for r in rows}, report["human_ratings"])
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.hashsalt": "qwen-language-v1"})
    fig, (left, right) = plt.subplots(
        1, 2, figsize=(13, 5.4), gridspec_kw={"width_ratios": [1.4, 1]}
    )
    labels = {
        "disclaimer": "AI identity / limitation",
        "experience_claim": "Own experience claim",
        "coherent": "Coherent response",
    }
    for i, metric in enumerate(labels):
        for k, fmt in enumerate(("plain", "chat")):
            counts = human["counts"][metric][fmt]
            y, start = 3 * i + k, 0
            for value, color, name in (
                ("1", "#006579", "Yes"),
                ("0", "#e0e5e8", "No"),
                ("unclear", "#d6a35b", "Unclear"),
            ):
                width = counts.get(value, 0)
                left.barh(
                    y,
                    width,
                    left=start,
                    height=0.7,
                    color=color,
                    label=name if i == k == 0 else None,
                    hatch="///" if value == "unclear" else None,
                )
                if width:
                    left.text(
                        start + width / 2,
                        y,
                        str(width),
                        ha="center",
                        va="center",
                        color="white" if value == "1" else "#333333",
                        fontsize=9,
                    )
                start += width
    left.set(
        yticks=[0, 1, 3, 4, 6, 7],
        yticklabels=[f"{labels[m]} · {fmt}" for m in labels for fmt in ("plain", "chat")],
        xlim=(0, 20),
        xticks=[0, 5, 10, 15, 20],
        ylim=(9, -1),
        xlabel="Responses (20 per format)",
        title="40 human-rated texts · one rater",
    )
    left.legend(loc="lower center", ncol=3, frameon=False)
    disclaimer = next(e for e in report["human_ratings"]["effects"] if e["metric"] == "disclaimer")
    for i, (stat, color) in enumerate(
        ((disclaimer, "#006579"), (report["action_format_effect"], "#be6a2e"))
    ):
        point = 100 * stat["estimate"]
        lo, hi = [100 * v for v in stat["ci95"]]
        right.errorbar(point, i, xerr=[[point - lo], [hi - point]], fmt="o", capsize=3, color=color)
        right.text(hi + 1.5, i, f"{point:+.1f}", va="center", color=color)
    right.axvline(0, color="#999999", linewidth=1)
    right.set(
        yticks=[0, 1],
        yticklabels=[
            "AI identity / limitation\n20 paired prompts",
            "Overall action accuracy\n8 paired scenarios",
        ],
        ylim=(1.6, -0.6),
        xlim=(-10, 52),
        xlabel="Chat − plain (percentage points)",
        title="Paired format effects",
    )
    for ax in (left, right):
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)
    fig.suptitle(
        "More explicit AI descriptions in chat; the action capability screen still fails",
        fontsize=14,
    )
    fig.text(
        0.5,
        0.015,
        "Nominal 95% bootstrap intervals; exploratory. "
        "Only four prompt pairs drive the disclaimer difference.\n"
        "Two unclear judgments retained; no full paired effect estimated "
        "for experience claims or coherence.\n"
        "Different task sets and clustering units; "
        "no equivalence or causal dissociation is established.",
        ha="center",
        fontsize=9,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.15, 1, 0.93), w_pad=3)
    output.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("svg", "pdf", "png"):
        meta = (
            {"Date": None}
            if ext == "svg"
            else {"CreationDate": None, "ModDate": None}
            if ext == "pdf"
            else {}
        )
        fig.savefig(output.with_suffix("." + ext), dpi=180, metadata=meta)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    parser.add_argument(
        "--out", type=Path, default=Path("assets/qwen_pilot_results/article_language")
    )
    args = parser.parse_args()
    plot(args.archive, args.out)
