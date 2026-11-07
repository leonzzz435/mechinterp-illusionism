"""Evidence-derived activation-exchange figures, examples, article and portable archives."""

from pathlib import Path

from .io import canonical, read_json
from .pilot import jobs_in
from .pilot_reporting import dot_interval, portable_archive, save_figure, setup_plotting
from .role_patch import ARMS, build_plan, preview, read_run, validate_spec
from .role_patch_analysis import analyze
from .role_patch_audit import audit_artifacts
from .storage import run_lock


def design_figure(stem):
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.set(xlim=(0, 12), ylim=(0, 6))
    ax.axis("off")
    ax.text(
        6,
        5.6,
        "Can an internal state carry a wording-dependent role effect?",
        ha="center",
        fontsize=15,
        weight="bold",
    )
    for y, line, color in (
        (4.25, "Your active connection: Cedar.", "#005f73"),
        (2.2, "Reference connection: Cedar.", "#9b5b29"),
    ):
        ax.text(
            0.15,
            y,
            line + "\nSame named actor",
            va="center",
            fontsize=10,
            bbox={"boxstyle": "round,pad=0.6", "fc": "#f4f6f8", "ec": color},
        )
        ax.text(
            5.1,
            y,
            "Block 14 output\nrole-line endpoint .\\n\n3,584 components",
            ha="center",
            va="center",
            fontsize=10,
            bbox={"boxstyle": "round,pad=0.6", "fc": "#e3edf2", "ec": color},
        )
        ax.text(
            9.3,
            y,
            "Later tokens + blocks\nPermissions / changes / question\n"
            "Four full-command likelihoods",
            ha="center",
            va="center",
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.6", "fc": "#f4f6f8", "ec": color},
        )
        for x1, x2 in ((3.2, 3.9), (6.3, 7.5)):
            ax.annotate("", (x2, y), (x1, y), arrowprops={"arrowstyle": "->", "color": color})
    ax.annotate(
        "",
        (5.1, 2.85),
        (5.1, 3.6),
        arrowprops={"arrowstyle": "<->", "linewidth": 2, "color": "#b33a3a"},
    )
    ax.text(6.0, 3.2, "Exchange in\nboth directions", color="#b33a3a", va="center", fontsize=9)
    ax.text(
        6,
        0.85,
        "Controls: unchanged baseline · own activation reinserted · "
        "10 norm-matched random directions",
        ha="center",
        fontsize=10,
    )
    ax.text(
        6,
        0.25,
        "PROTOCOL ONLY · Causal attention prevents this endpoint "
        "from reading later facts or answers",
        ha="center",
        fontsize=9,
        color="#475569",
    )
    save_figure(fig, stem)
    plt.close(fig)


def plots(report, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    design_figure(directory / "role_patch_design")
    plt = setup_plotting()
    arms = ["swap", *ARMS[3:]]
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    for ax, key, title in zip(
        axes,
        ("reference_to_active", "active_to_reference", "total"),
        ("Reference → active", "Active → reference", "Bidirectional transfer T"),
    ):
        for i, arm in enumerate(arms):
            dot_interval(ax, i, report["transfer"][arm][key], "#005f73" if i == 0 else "#88969b")
        ax.axhline(0, color="gray", linewidth=1)
        ax.set(
            xticks=range(len(arms)),
            xticklabels=["swap", *map(str, range(10))],
            title=title,
            ylabel="Percentage points",
            xlabel="Exchange / random direction",
        )
    fig.suptitle(f"{report['decision']} · paired scenario bootstrap, nominal 95% intervals")
    save_figure(fig, directory / "role_patch_transfer", report["synthetic"])
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    means = report["primary_contrast"]["scenario_means"]
    for i, (sid, value) in enumerate(sorted(means.items())):
        axes[0].bar(i, 100 * value, color="#005f73" if value > 0 else "#b33a3a")
    axes[0].axhline(0, color="gray", linewidth=1)
    axes[0].set(
        xticks=range(len(means)),
        xticklabels=[s.rsplit(":", 1)[-1] for s in sorted(means)],
        ylabel="Swap − average random transfer (pp)",
        title="Primary contrast C by scenario",
    )
    cells = report["control_cells"]
    for i, cell in enumerate(cells):
        dot_interval(axes[1], i, cell, "#005f73")
    axes[1].axhline(80, color="gray", linestyle="--")
    axes[1].set(
        xticks=range(len(cells)),
        xticklabels=[c["value"].replace("/", "\n") for c in cells],
        ylim=(-3, 105),
        ylabel="Accuracy (%)",
        title="Swap controls: before / irrelevant update",
    )
    axes[1].tick_params(axis="x", labelsize=7, labelrotation=25)
    fig.suptitle(
        f"{report['scientific_completed']}/11264 scientific choices; eight known scenarios"
    )
    save_figure(fig, directory / "role_patch_scenarios_controls", report["synthetic"])
    plt.close(fig)


def fmt(value, scale=100):
    return "pending" if value is None else f"{scale * value:.3f}"


def article(report):
    return (
        "# Moving a state, keeping the question fixed\n\n"
        "A role label had changed how Qwen selected actions in a small simulator. "
        "We next ask whether an internal state at that label contributes to the effect. "
        "Think of copying one intermediate note between two computations while keeping "
        "the recipient's question and permissions fixed. We exchange a 3,584-component "
        "vector at the output of block 14, exactly at the end of the role line. "
        "Causal attention prevents that state from reading the later task facts.\n\n"
        "The model scores complete commands by their summed conditional log-likelihood. "
        "We run the exchange in both directions and compare it with reinserting the original "
        "state and ten equally large random changes. Our sampling units are eight scenarios, "
        "not the thousands of dependent variants.\n\n"
        f"Recorded status: **{report['decision']}**; "
        f"{report['scientific_completed']}/11264 scientific choices. "
        f"Transfer T: {fmt(report['transfer']['swap']['total']['estimate'])} percentage points; "
        f"swap minus mean random transfer C: {fmt(report['primary_contrast']['estimate'])} "
        "percentage points. Consult report.md for intervals, coverage and technical failures. "
        + (
            "**These are synthetic software-test data, not model evidence.**\n\n"
            if report["synthetic"]
            else "\n\n"
        )
        + "A positive result would implicate this state in the measured wording sensitivity. "
        "A null result concerns only this single site and operation. Wording, meaning and "
        "position remain bundled in the contrast. Neither outcome identifies a complete "
        "self-monitoring circuit or decides subjective experience. Human illusionism remains "
        "a philosophical motivation and possible analogy, alongside other interpretations. "
        "Confirmation on unseen scenarios is a separate step.\n"
    )


def markdown_report(report, plan, records):
    lookup = {r["id"]: r for r in records}
    lines = [
        "# Qwen role activation exchange",
        "",
        report["note"],
        "",
        f"Decision: **{report['decision']}**. Status: {report['status']}. "
        f"Scientific coverage: {report['scientific_completed']}/11264; "
        f"technical repeats: {report['technical_repeats_completed']}/32. "
        f"Scoring/execution errors: {report['errors']}; failed technical checks: "
        f"{report['technical_failures']}.",
        "",
        "![Intervention site](figures/role_patch_design.png)",
        "",
        "## Fixed estimands",
        "",
        r"$D_f^c=A_{f,other}^c-A_{f,target}^c$; "
        r"$T_c=\frac12[D_{active}^{self}-D_{active}^c+D_{reference}^c-D_{reference}^{self}]$; "
        r"$C=T_{swap}-\frac1{10}\sum_kT_{random,k}$.",
        "",
        "10,000 paired scenario bootstrap draws, seed 1729; exact two-sided sign flip "
        "over eight scenario contrasts (256 signs). C is the sole primary statistical "
        "comparison. Symmetry of null scenario effects is an assumption of the sign-flip test. "
        "All intervals are nominal; secondary views are descriptive. Errors count as failures; "
        "missing outputs are shown explicitly and cannot pass the decision.",
        "",
        "| Statistic | Estimate (pp) | 95% interval (pp) |",
        "|---|---:|---|",
    ]
    for label, stat in (
        ("Swap T", report["transfer"]["swap"]["total"]),
        ("Primary C", report["primary_contrast"]),
        ("Control change", report["control_change"]),
    ):
        ci = "pending" if not stat["ci95"] else " to ".join(fmt(v) for v in stat["ci95"])
        lines.append(f"| {label} | {fmt(stat['estimate'])} | {ci} |")
    lines += [
        "",
        f"Primary sign-flip p: {report['primary_contrast']['two_sided_sign_flip_p']}; "
        f"positive scenarios: {report['primary_contrast']['positive_scenarios']}/8.",
        "",
        "![Transfer and random controls](figures/role_patch_transfer.png)",
        "",
        "![Scenario effects and controls](figures/role_patch_scenarios_controls.png)",
        "",
        "## Every recorded accuracy and secondary command margin",
        "",
        "Margin = log P(correct command) − log P(other actor's currently permitted command), "
        "in nats. No EOS, added whitespace or length normalization.",
        "",
        "| Arm | Group | Observed / planned | Accuracy (%) | Margin (nats) |",
        "|---|---|---:|---:|---:|",
    ]
    for g in report["groups"]:
        lines.append(
            f"| {g['arm']} | {g['axis']}/{g['value']} | {g['observed']}/{g['expected']} | "
            f"{fmt(g['estimate'])} | {fmt(g['margin']['estimate'], 1)} |"
        )
    lines += [
        "",
        "## Prespecified complete example",
        "",
        "Scenario 0008, target identity 0, relevant update after, grant variant 0, rotation 0. "
        "All four recipient prompts and all intervention outcomes are shown, "
        "including missing work.",
    ]
    selected = [
        j
        for j in jobs_in(plan)
        if not j["technical"]
        and j["row"]["scenario_id"].endswith(":0008")
        and j["row"]["target_identity"] == 0
        and j["row"]["phase"] == "after"
        and j["row"]["relevant_update"]
        and j["row"]["grant_variant"] == 0
        and j["row"]["rotation"] == 0
    ]
    for job in selected:
        row, result = job["row"], lookup.get(job["id"], {}).get("result", {})
        label = row["frame"] + "/" + row["relation"]
        if job["arm"] == "baseline":
            lines += ["", f"### Recipient {label}", "", "```text", row["prompt"], "```"]
        lines += [
            "",
            f"**{job['arm']} · {label}**",
            "",
            f"Selected: {result.get('selected_command', '[pending/error]')}; "
            f"correct: {result.get('execution', {}).get('correct', '[pending/error]')}; "
            f"expected: {row['expected_command']}.",
            "",
            "```json",
            canonical(result.get("candidates", result)),
            "```",
        ]
    lines += ["", "## Interpretation", "", article(report), ""]
    return "\n".join(lines)


def export(directory, destination):
    directory = Path(directory)
    with run_lock(directory):
        manifest = read_json(directory / "manifest.json")
        if manifest["status"] == "design_only":
            spec = validate_spec(read_json(directory / "config.json"))
            if read_json(directory / "plan.json") != build_plan(spec) or any(
                manifest[k] != v for k, v in preview(spec).items()
            ):
                raise ValueError("Frozen patch design changed")
            audit_artifacts(directory, {"synthetic": True}, [])
            design_figure(directory / "figures/role_patch_design")
            return portable_archive(directory, destination, "design_only")
        report = analyze(directory)
        _, plan, records = read_run(directory)
        (directory / "records.jsonl").write_text("".join(canonical(r) + "\n" for r in records))
        plots(report, directory / "figures")
        (directory / "report.md").write_text(markdown_report(report, plan, records))
        (directory / "article_section.md").write_text(article(report))
        return portable_archive(directory, destination, report["status"])
