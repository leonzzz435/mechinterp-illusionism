"""Design-only illustration and evidence-driven role-control exports."""

from pathlib import Path

from .io import canonical, digest, read_json
from .pilot import jobs_in
from .pilot_reporting import portable_archive, save_figure, setup_plotting
from .role_control import CONDITIONS, build_plan, preview, read_run, stratum, validate_spec
from .role_control_analysis import STRATA, analyze
from .storage import run_lock


def design_figure(stem):
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.axis("off")
    ax.text(0.5, 0.96, "One question. Four context lines.", ha="center", fontsize=17, weight="bold")
    ax.text(
        0.5,
        0.83,
        "Same permissions, event, command list and named target: Dune",
        ha="center",
        fontsize=11,
    )
    for x, y, title, line in (
        (0.02, 0.60, "Active / target", "Your active connection: Dune."),
        (0.53, 0.60, "Active / other", "Your active connection: Cedar."),
        (0.02, 0.31, "Reference / target", "Reference connection: Dune."),
        (0.53, 0.31, "Reference / other", "Reference connection: Cedar."),
    ):
        ax.text(
            x,
            y,
            title + "\n\n" + line,
            fontsize=11,
            va="center",
            bbox={"boxstyle": "round,pad=0.7", "fc": "#eff7f8", "ec": "#006579"},
        )
    ax.text(
        0.5,
        0.09,
        "Primary comparison: assignment gap under active wording\n"
        "minus assignment gap under reference wording",
        ha="center",
        fontsize=11,
    )
    ax.text(
        0.5,
        -0.07,
        "DESIGN ONLY · No measured result or neural mechanism\n"
        "8 new development scenarios · 2,048 choices · Qwen2.5-7B-Instruct · chat format",
        ha="center",
        fontsize=9,
        color="#555555",
    )
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    save_figure(fig, stem)
    plt.close(fig)


def plots(report, directory):
    plt = setup_plotting()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    design_figure(directory / "role_control_design")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4))
    for i, (frame, relation) in enumerate(CONDITIONS):
        stat = report["cells"][f"{frame}/{relation}/after_relevant"]
        if stat["estimate"] is not None:
            axes[0].plot(i, 100 * stat["estimate"], "o", color="#006579")
            if stat["ci95"]:
                axes[0].vlines(i, *(100 * v for v in stat["ci95"]), color="#006579")
    axes[0].set(
        xticks=range(4),
        xticklabels=["\n".join(c) for c in CONDITIONS],
        ylim=(-3, 103),
        ylabel="Correct choices (%)",
        title="Target permission changed",
    )
    for i, stage in enumerate(STRATA):
        stat = report["interaction"][stage]
        if stat["estimate"] is not None:
            axes[1].plot(i, 100 * stat["estimate"], "o", color="#be6a2e")
            if stat["ci95"]:
                axes[1].vlines(i, *(100 * v for v in stat["ci95"]), color="#be6a2e")
    axes[1].axhline(0, color="gray", linewidth=1)
    axes[1].set(
        xticks=range(3),
        xticklabels=[s.replace("_", "\n") for s in STRATA],
        ylabel="Active gap − reference gap (pp)",
        title="Framing interaction",
    )
    fig.suptitle("Role-control result · " + report["decision"])
    fig.text(
        0.5,
        -0.02,
        "Nominal 95% scenario-bootstrap intervals; 8 independent scenarios. "
        "Missing quartets receive no paired estimate.\nOnly after_relevant is primary; "
        "no equivalence or consciousness conclusion.",
        ha="center",
        fontsize=9,
    )
    save_figure(fig, directory / "role_control_results", report["synthetic"])
    plt.close(fig)


def markdown_report(report, plan, records):
    by_id = {r["id"]: r for r in records}
    lines = [
        "# Qwen role-framing control",
        "",
        report["note"],
        "",
        f"Decision: **{report['decision']}**; {report['completed_jobs']}/"
        f"{report['expected_jobs']} choices; {report['errors']} failed/tied/invalid outcomes.",
        "",
        "![Control design](figures/role_control_design.png)",
        "",
        "![Recorded results](figures/role_control_results.png)",
        "",
        "| Condition/checkpoint | Observed / planned | Accuracy |",
        "|---|---:|---:|",
    ]
    for key, stat in sorted(report["cells"].items()):
        accuracy = "pending" if stat["estimate"] is None else f"{100 * stat['estimate']:.2f}%"
        lines.append(f"| {key} | {stat['observed']}/{stat['expected']} | {accuracy} |")
    lines += [
        "",
        "## Fixed complete examples",
        "",
        "Selection fixed before inference: scenario 0008, target identity 0, "
        "relevant after-update, grant alternative 0, rotation 0; all four conditions. "
        "The full archive retains every candidate score and control outcome.",
    ]
    for job in jobs_in(plan):
        row = job["row"]
        if not (
            row["scenario_id"].endswith(":0008")
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
            if digest(plan) != digest(build_plan(spec)) or manifest["plan_hash"] != digest(plan):
                raise ValueError("Design differs from frozen role-control inputs")
            if manifest != {"engine": spec["engine"], "status": "design_only", **preview(spec)}:
                raise ValueError("Design summary changed")
            inputs = [
                {"id": j["id"], "prompt": j["row"]["prompt"], "choices": j["row"]["choices"]}
                for j in jobs_in(plan)
            ]
            if read_json(directory / "model_inputs.json") != inputs:
                raise ValueError("Exported model inputs changed")
            return portable_archive(directory, destination, "design_only")
        report = analyze(directory)
        _, plan, records = read_run(directory)
        (directory / "records.jsonl").write_text("".join(canonical(r) + "\n" for r in records))
        plots(report, directory / "figures")
        (directory / "report.md").write_text(markdown_report(report, plan, records))
        return portable_archive(directory, destination, report["status"])
