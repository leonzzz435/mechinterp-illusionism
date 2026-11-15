"""Generate publication figures for Follow-up Experiments 2 (Scaling) and 3 (28-Layer Geometry)."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/followup"
OUT.mkdir(parents=True, exist_ok=True)


def plot_scaling():
    s14 = json.loads(
        (ROOT / "review/followup/exp2-scale-14b/followup/scale-14b/summary.json").read_text()
    )
    s32 = json.loads(
        (ROOT / "review/followup/exp2-scale-32b/followup/scale-32b/summary.json").read_text()
    )

    # 7B 48-world values from Table 2 of ARTICLE.md
    models = ["Qwen2.5-7B\n(48 worlds)", "Qwen2.5-14B\n(16 worlds)", "Qwen2.5-32B\n(16 worlds)"]
    acc_self_acct = [
        95.18,
        s14["cells"]["after_both|self|account_name"]["accuracy"] * 100,
        s32["cells"]["after_both|self|account_name"]["accuracy"] * 100,
    ]
    acc_self_op = [
        71.35,
        s14["cells"]["after_both|self|owner_name"]["accuracy"] * 100,
        s32["cells"]["after_both|self|owner_name"]["accuracy"] * 100,
    ]
    acc_self_poss = [
        60.16,
        s14["cells"]["after_both|self|possessive"]["accuracy"] * 100,
        s32["cells"]["after_both|self|possessive"]["accuracy"] * 100,
    ]
    acc_other_poss = [
        71.29,
        s14["cells"]["after_both|other|possessive"]["accuracy"] * 100,
        s32["cells"]["after_both|other|possessive"]["accuracy"] * 100,
    ]

    m_self_acct = [
        7.663,
        s14["cells"]["after_both|self|account_name"]["mean_margin"],
        s32["cells"]["after_both|self|account_name"]["mean_margin"],
    ]
    m_self_op = [
        3.293,
        s14["cells"]["after_both|self|owner_name"]["mean_margin"],
        s32["cells"]["after_both|self|owner_name"]["mean_margin"],
    ]
    m_self_poss = [
        1.089,
        s14["cells"]["after_both|self|possessive"]["mean_margin"],
        s32["cells"]["after_both|self|possessive"]["mean_margin"],
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.5), dpi=180)
    x = np.arange(len(models))

    ax1.plot(
        x, acc_self_acct, marker="o", lw=2.2, label="Self: Account Name (0-Hop)", color="#1f77b4"
    )
    ax1.plot(
        x, acc_self_op, marker="s", lw=2.2, label="Self: Operator Name (1-Hop)", color="#ff7f0e"
    )
    ax1.plot(
        x,
        acc_self_poss,
        marker="^",
        lw=2.5,
        label='Self: Possessive "your" (2-Hop)',
        color="#d62728",
    )
    ax1.plot(
        x,
        acc_other_poss,
        marker="D",
        lw=1.8,
        ls="--",
        label='Other: Possessive "their" (2-Hop)',
        color="#7f7f7f",
    )
    ax1.set_xticks(x)
    ax1.set_xticklabels(models)
    ax1.set_ylim(50, 103)
    ax1.set_ylabel("After-Both Accuracy (%)")
    ax1.set_title("A. Discrete Choice Accuracy Across Model Scale")
    ax1.grid(alpha=0.25)
    ax1.legend(frameon=True, fontsize=8.5, loc="lower right")
    for xi, yv in zip(x, acc_self_poss):
        ax1.annotate(
            f"{yv:.1f}%",
            (xi, yv),
            textcoords="offset points",
            xytext=(0, -14),
            ha="center",
            fontsize=8.5,
            color="#d62728",
            fontweight="bold",
        )

    ax2.plot(
        x, m_self_acct, marker="o", lw=2.2, label="Self: Account Name (0-Hop)", color="#1f77b4"
    )
    ax2.plot(x, m_self_op, marker="s", lw=2.2, label="Self: Operator Name (1-Hop)", color="#ff7f0e")
    ax2.plot(
        x, m_self_poss, marker="^", lw=2.5, label='Self: Possessive "your" (2-Hop)', color="#d62728"
    )
    ax2.set_xticks(x)
    ax2.set_xticklabels(models)
    ax2.set_ylabel("Mean Log-Likelihood Margin [nats]")
    ax2.set_title("B. Continuous Decision Margin Across Scale")
    ax2.grid(alpha=0.25)
    ax2.legend(frameon=True, fontsize=8.5, loc="upper left")
    for xi, yv in zip(x, m_self_poss):
        ax2.annotate(
            f"+{yv:.2f}",
            (xi, yv),
            textcoords="offset points",
            xytext=(0, -13),
            ha="center",
            fontsize=8.5,
            color="#d62728",
            fontweight="bold",
        )

    fig.tight_layout()
    fig.savefig(OUT / "qwen_scaling_curve.png", bbox_inches="tight")
    plt.close(fig)


def plot_subspace():
    sub = json.loads(
        (ROOT / "review/followup/exp3-subspace-7b/followup/subspace-7b/summary.json").read_text()
    )
    layers = sub["layers"]
    blocks = [x["block"] for x in layers]
    auroc = [x["m_self_probe_cv_auroc"] for x in layers]
    cos_lm = [x["cos_L_M_probe"] for x in layers]
    cos_rm = [x["cos_Role_M_probe"] for x in layers]
    cos_lr = [x["cos_L_Role"] for x in layers]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10.5, 6.2), sharex=True, dpi=180)
    ax1.plot(
        blocks, auroc, marker="o", lw=2.2, color="#2ca02c", label="M_self 5-Fold CV Probe AUROC"
    )
    ax1.axhline(0.5, color="#888888", ls="--", lw=1.0, label="Chance (0.50)")
    ax1.axvline(18, color="#d62728", ls=":", lw=1.3, alpha=0.8)
    ax1.annotate(
        "Block 20 peak: 0.764",
        xy=(20, max(auroc)),
        xytext=(13.5, 0.72),
        arrowprops={"arrowstyle": "->", "color": "#2ca02c"},
        fontsize=9,
        fontweight="bold",
        color="#2ca02c",
    )
    ax1.set_ylabel("CV AUROC")
    ax1.set_ylim(0.40, 0.82)
    ax1.set_title(
        "Qwen2.5-7B-Instruct (All 28 Blocks): Functional M_self Emerges Late "
        "While L_self Remains Near-Orthogonal"
    )
    ax1.grid(alpha=0.25)
    ax1.legend(loc="upper left", fontsize=8.5)

    ax2.plot(
        blocks, cos_lm, marker="o", lw=2.0, color="#1f77b4", label="cos(v_L_self, v_M_self_probe)"
    )
    ax2.plot(
        blocks, cos_rm, marker="s", lw=2.0, color="#ff7f0e", label="cos(v_Role, v_M_self_probe)"
    )
    ax2.plot(
        blocks, cos_lr, marker="^", lw=1.6, ls="--", color="#9467bd", label="cos(v_L_self, v_Role)"
    )
    ax2.axhline(0.0, color="#444444", lw=0.9)
    ax2.axvline(18, color="#d62728", ls=":", lw=1.3, alpha=0.8)
    ax2.set_xlabel("Transformer Block (1–28)")
    ax2.set_ylabel("Cosine Similarity")
    ax2.set_ylim(-0.25, 0.35)
    ax2.set_xticks(blocks)
    ax2.grid(alpha=0.25)
    ax2.legend(loc="upper left", fontsize=8.5, ncol=3)

    fig.tight_layout()
    fig.savefig(OUT / "qwen_subspace_28layers.png", bbox_inches="tight")
    plt.close(fig)


def plot_multispan():
    mp = json.loads(
        (ROOT / "review/followup/exp1-multispan-7b/followup/multispan-7b/summary.json").read_text()
    )
    rows = mp["sweep"]
    blocks = sorted({r["block"] for r in rows})
    spans = ["header_span", "query_span", "joint_span"]
    labels = {
        "header_span": "Role-Header Span (5 tokens)",
        "query_span": "Query Sentence Span (9–10 tokens)",
        "joint_span": "Joint Span (Header + Query)",
    }
    colors = {"header_span": "#1f77b4", "query_span": "#ff7f0e", "joint_span": "#2ca02c"}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.5), sharey=True, dpi=180)
    for sp in spans:
        ys_a2r = [
            next(r["T_A2R_pp"] for r in rows if r["block"] == b and r["span"] == sp) for b in blocks
        ]
        ys_r2a = [
            next(r["T_R2A_pp"] for r in rows if r["block"] == b and r["span"] == sp) for b in blocks
        ]
        ax1.plot(blocks, ys_a2r, marker="o", lw=2.2, label=labels[sp], color=colors[sp])
        ax2.plot(blocks, ys_r2a, marker="o", lw=2.2, label=labels[sp], color=colors[sp])

    # Mark single-token Block 14 baseline
    b14_end = next(r for r in rows if r["block"] == 14 and r["span"] == "header_end")
    ax1.scatter(
        [14],
        [b14_end["T_A2R_pp"]],
        color="#d62728",
        s=70,
        zorder=5,
        label="Single-Token header_end (B14)",
    )
    ax2.scatter(
        [14],
        [b14_end["T_R2A_pp"]],
        color="#d62728",
        s=70,
        zorder=5,
        label="Single-Token header_end (B14)",
    )

    for ax, title in [
        (ax1, "A. Active → Reference (Disruption Transfer T_A→R)"),
        (ax2, "B. Reference → Active (Bidirectional Rescue T_R→A)"),
    ]:
        ax.axhline(0.0, color="#555555", lw=0.9, ls="--")
        ax.set_xticks(blocks)
        ax.set_xlabel("Transformer Block")
        ax.set_title(title)
        ax.grid(alpha=0.25)
    ax1.set_ylabel("Causal Transfer [percentage points]")
    ax2.legend(loc="upper right", fontsize=8.0, frameon=True)

    fig.tight_layout()
    fig.savefig(OUT / "qwen_multispan_circuit.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    plot_scaling()
    plot_subspace()
    plot_multispan()
    print("Generated all 3 follow-up plots in", OUT)
