"""Data-derived wording-control figures, full examples and portable evidence."""

from pathlib import Path

from .io import canonical, digest, read_json
from .pilot import jobs_in
from .pilot_reporting import portable_archive, save_figure, setup_plotting
from .possessive import CONDITIONS, build_plan, preview, read_run, stratum, validate_spec
from .possessive_analysis import STRATA, analyze
from .storage import run_lock


def design_figure(stem):
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.axis("off")
    ax.text(
        0.5,
        0.98,
        "Does one word change how a role affects the answer?",
        ha="center",
        fontsize=16,
        weight="bold",
    )
    ax.text(
        0.5,
        0.87,
        "Same permissions, update, question and commands · queried account: Cedar",
        ha="center",
        fontsize=11,
    )
    for x, relation, actor in (
        (0.03, "Queried account named", "Cedar"),
        (0.53, "Other account named", "Dune"),
    ):
        ax.text(x, 0.74, relation, fontsize=12, weight="bold")
        for y, line in (
            (0.61, f"Your active connection: {actor}."),
            (0.43, f"The active connection: {actor}."),
            (0.25, f"Reference connection: {actor}."),
        ):
            ax.text(
                x,
                y,
                line,
                fontsize=11,
                bbox={"boxstyle": "round,pad=.5", "fc": "#eff7f8", "ec": "#006579"},
            )
    ax.text(
        0.5,
        0.09,
        "Primary: Your role gap − The role gap\n"
        "Your → The changes one token; Reference is a descriptive anchor.",
        ha="center",
        fontsize=11,
    )
    ax.text(
        0.5,
        -0.06,
        "DESIGN ONLY · 16 development scenarios · 6,144 choices\n"
        "No internal intervention, measured result or discovered mechanism",
        ha="center",
        fontsize=9,
        color="#555555",
    )
    Path(stem).parent.mkdir(parents=True, exist_ok=True)
    save_figure(fig, Path(stem))
    plt.close(fig)


def dot(ax, x, stat, color):
    if stat["estimate"] is not None:
        ax.plot(x, 100 * stat["estimate"], "o", color=color)
        if stat["ci95"]:
            ax.vlines(x, *(100 * v for v in stat["ci95"]), color=color)


def plots(report, directory):
    plt = setup_plotting()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    design_figure(directory / "possessive_design")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for i, (frame, relation) in enumerate(CONDITIONS):
        dot(axes[0], i, report["cells"][f"{frame}/{relation}/after_relevant"], "#006579")
    axes[0].set(
        xticks=range(6),
        xticklabels=["\n".join(c) for c in CONDITIONS],
        ylim=(-3, 103),
        ylabel="Correct choices (%)",
        title="Target permission changed",
    )
    for i, stage in enumerate(STRATA):
        dot(axes[1], i, report["interaction"][stage], "#be6a2e")
    axes[1].axhline(0, color="gray", linewidth=1)
    axes[1].set(
        xticks=range(3),
        xticklabels=[s.replace("_", "\n") for s in STRATA],
        ylabel="Your gap − The gap (percentage points)",
        title="Possessive interaction",
    )
    fig.suptitle("Wording control · " + report["decision"])
    fig.text(
        0.5,
        -0.02,
        "Nominal 95% scenario-bootstrap intervals; 16 scenarios. "
        "Only after_relevant is primary. Missing sextets: no paired estimate.",
        ha="center",
        fontsize=9,
    )
    save_figure(fig, directory / "possessive_results", report["synthetic"])
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
    primary = report["interaction"]["after_relevant"]
    vals = primary["scenario_means"]
    axes[0].bar(range(len(vals)), [100 * v for v in vals.values()], color="#006579")
    axes[0].axhline(0, color="gray", linewidth=1)
    axes[0].set(
        xticks=range(len(vals)),
        xticklabels=[s.rsplit(":", 1)[1] for s in vals],
        ylabel="Your gap − The gap (pp)",
        title="Primary contrast by scenario",
    )
    axes[0].tick_params(axis="x", rotation=60)
    for i, stage in enumerate(STRATA):
        dot(axes[1], i, report["reference_anchor"][stage], "#555555")
    axes[1].axhline(0, color="gray", linewidth=1)
    axes[1].set(
        xticks=range(3),
        xticklabels=[s.replace("_", "\n") for s in STRATA],
        ylabel="Your gap − Reference gap (pp)",
        title="Historical contrast · descriptive",
    )
    fig.text(
        0.5,
        -0.02,
        "Reference is not an alternative primary success criterion. "
        "Same template and vocabulary; no broad generalization claim.",
        ha="center",
        fontsize=9,
    )
    save_figure(fig, directory / "possessive_scenarios", report["synthetic"])
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(14, 5))
    for i, stat in enumerate(report["controls"].values()):
        dot(ax, i, stat, "#006579")
    ax.axhline(80, color="#be6a2e", linestyle="--", label="Pilot quality threshold")
    ax.set(
        xticks=range(len(report["controls"])),
        xticklabels=list(report["controls"]),
        ylim=(-3, 103),
        ylabel="Correct choices (%)",
        title="All 48 control cells",
    )
    ax.tick_params(axis="x", labelsize=7, rotation=90)
    ax.legend()
    save_figure(fig, directory / "possessive_controls", report["synthetic"])
    plt.close(fig)


def value(stat, percent=True):
    if stat["estimate"] is None:
        return "pending / incomplete"
    scale, unit = (100, " pp") if percent else (1, " nats")
    point = f"{scale * stat['estimate']:+.3f}{unit}"
    if stat["ci95"]:
        point += f" [{scale * stat['ci95'][0]:+.3f}, {scale * stat['ci95'][1]:+.3f}]"
    return point


def article_section(report):
    stat = report["interaction"]["after_relevant"]
    return (
        "# One word, the same task\n\n"
        + ("**SYNTHETIC SOFTWARE TEST ONLY.**\n\n" if report["synthetic"] else "")
        + "Imagine two accounts, each allowed one command. After a permission changes, "
        "the model must pick the command that works for a named account. We changed "
        "“Your active connection” to “The active connection”, keeping every later token "
        "in the same position. The question is whether the personal wording changes "
        "how the context account affects that choice.\n\n"
        f"The primary difference between role gaps was {value(stat)}, with uncertainty "
        f"resampled over scenarios. The frozen decision was **{report['decision']}**; "
        f"{report['completed_jobs']}/{report['expected_jobs']} choices were recorded. "
        "A missing estimate means the paired comparison is incomplete.\n\n"
        "This experiment changes an input word, not an internal activation. It addresses "
        "the interpretation of our earlier role effect. Even a clear wording effect "
        "would not identify a self-monitoring system or decide whether humans experience "
        "an illusion of phenomenal consciousness. Those remain different questions.\n"
    )


def markdown_report(report, plan, records):
    lines = [
        "# Qwen possessive-wording control",
        "",
        report["note"],
        "",
        f"Decision: **{report['decision']}**; {report['completed_jobs']}/"
        f"{report['expected_jobs']} choices; {report['errors']} failed/tied/invalid outcomes.",
        "",
        "Primary $S=(A_{Your,other}-A_{Your,target})-(A_{The,other}-A_{The,target})$.",
        "",
        "Primary S: " + value(report["interaction"]["after_relevant"]),
        "Exact two-sided scenario sign-flip p: "
        + str(report["interaction"]["after_relevant"]["two_sided_sign_flip_p"]),
        "",
    ]
    for name in ("design", "results", "scenarios", "controls"):
        lines += [f"![{name}](figures/possessive_{name}.png)", ""]
    for title, stats, paired in (
        ("Accuracy by condition and checkpoint", report["cells"], False),
        ("All quality controls", report["controls"], False),
        ("Command identity", report["command_accuracy"], False),
        ("Changed-answer pairs: both correct", report["counterfactuals"], True),
    ):
        lines += [f"## {title}", "", "| Cell | Observed / planned | Accuracy |", "|---|---:|---:|"]
        for key, stat in stats.items():
            o, e = ("observed_pairs", "expected_pairs") if paired else ("observed", "expected")
            point = "pending" if stat["estimate"] is None else f"{100 * stat['estimate']:.2f}%"
            lines.append(f"| {key} | {stat[o]}/{stat[e]} | {point} |")
        lines.append("")
    lines += [
        "## Secondary command margins",
        "",
        "Correct command minus other account’s allowed command, summed log-likelihood in "
        "nats. Failed scores are missing here, but are failures in accuracy; incomplete "
        "sextets suppress the paired margin estimate.",
        "",
        "| Gap / contrast and checkpoint | Estimate [nominal 95% interval] |",
        "|---|---:|",
    ]
    for key, stat in report["margin_effects_nats"].items():
        lines.append(f"| {key} | {value(stat, False)} |")
    lines += [
        "",
        "## Example fixed before inference",
        "",
        "Scenario 0016, target identity 0, relevant after-update, grant alternative 0, "
        "rotation 0; all six conditions. All other examples remain in the archive.",
    ]
    by_id = {r["id"]: r for r in records}
    for job in jobs_in(plan):
        row = job["row"]
        if not (
            row["scenario_id"].endswith(":0016")
            and row["target_identity"] == 0
            and stratum(row) == "after_relevant"
            and row["grant_variant"] == row["rotation"] == 0
        ):
            continue
        record = by_id.get(job["id"])
        result = record["result"] if record else {}
        lines += [
            "",
            f"### {row['frame']} / {row['relation']}",
            "",
            "```text",
            result.get("rendered_prompt", row["prompt"]),
            "```",
            "",
            f"Expected: `{row['expected_command']}`; selected: "
            f"`{result.get('selected_command', '[PENDING/ERROR]')}`; "
            f"status: {record['status'] if record else 'pending'}.",
            "",
            "```json",
            canonical(result.get("candidates", [])),
            "```",
        ]
    if report["synthetic"]:
        lines.insert(2, "**SYNTHETIC SOFTWARE TEST ONLY — not model evidence.**\n")
    return "\n".join(lines) + "\n"


def export(directory, destination):
    directory = Path(directory)
    with run_lock(directory):
        manifest = read_json(directory / "manifest.json")
        if manifest.get("status") == "design_only":
            spec = validate_spec(read_json(directory / "config.json"))
            plan = read_json(directory / "plan.json")
            if digest(plan) != digest(build_plan(spec)) or manifest != {
                "engine": spec["engine"],
                "status": "design_only",
                **preview(spec),
            }:
                raise ValueError("Design differs from frozen possessive inputs")
            expected = [
                {"id": j["id"], "prompt": j["row"]["prompt"], "choices": j["row"]["choices"]}
                for j in jobs_in(plan)
            ]
            if read_json(directory / "model_inputs.json") != expected:
                raise ValueError("Exported model inputs changed")
            return portable_archive(directory, destination, "design_only")
        report = analyze(directory)
        _, plan, records = read_run(directory)
        (directory / "records.jsonl").write_text("".join(canonical(r) + "\n" for r in records))
        plots(report, directory / "figures")
        (directory / "report.md").write_text(markdown_report(report, plan, records))
        (directory / "article_section.md").write_text(article_section(report))
        return portable_archive(directory, destination, report["status"])
