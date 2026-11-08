"""Auditable reports and figures; synthetic/incomplete status remains prominent."""

import shutil
from contextlib import ExitStack
from pathlib import Path

import numpy as np

from .io import canonical, write_json
from .pilot_reporting import portable_archive, save_figure, setup_plotting
from .query_reference import SPEC_PATH, build_inputs
from .query_reference_analysis import FORMS, OWNERS, STAGES, analyze_runs
from .query_reference_runtime import FREEZE, PREFLIGHT, read_run
from .storage import run_lock


def number(value, scale=1):
    return "not estimable" if value is None else f"{value * scale:+.3f}"


def confidence(bounds, scale=100):
    return "withheld" if bounds is None else f"[{bounds[0] * scale:+.3f}, {bounds[1] * scale:+.3f}]"


def markdown(report):
    lines = [
        "# Query-bound self-reference: fixed-sample report",
        "",
        "**SYNTHETIC SOFTWARE FIXTURE — NOT MODEL EVIDENCE**"
        if report["synthetic"]
        else "Recorded Qwen2.5-7B-Instruct selections; one permission template.",
        "",
        f"Status: **{report['status']}**. Recorded {report['recorded_choices']}/"
        f"{report['scheduled_choices']} choices; "
        f"{report['valid_complete_worlds']}/48 valid complete worlds.",
        f"Decision: **{report['decision']}**.",
        "",
        report["limits"],
        "",
        "## The question",
        "",
        "An operator owns one of two accounts. We ask for a successful command using either "
        "your/their active connection, the operator's name, or the same account's name. "
        "Within each comparison the task facts and correct answer are identical. In the primary "
        "checkpoint both accounts have changed permissions; reversing update order keeps the "
        "answer fixed. A rule that always chooses the newest grant succeeds on half "
        "the primary cases.",
        "",
        "## Prespecified contrasts",
        "",
        r"For each world, $E=q_{self,possessive}-q_{self,account}$, "
        r"$F=A_{self,account}-A_{self,possessive}$ and "
        r"$S=F-(A_{other,account}-A_{other,possessive})$.",
        "",
        "Positive E means more foreign-account choices; positive F means an accuracy cost. "
        "Positive S means a larger cost for the addressee than for the other operator. "
        "All three expected directions were fixed before responses. E and F are correlated, "
        "not independent replications. F−E is the contrast in remaining errors.",
        "",
        report["uncertainty"],
        "",
        "| Contrast | Estimate (pp) | Nominal 95% CI (pp) | Raw p | Holm p | Test status |",
        "|---|---:|---|---:|---:|---|",
    ]
    for name, r in report["primary"].items():
        lines.append(
            f"| {name} | {number(r['estimate'], 100)} | {confidence(r['ci95'])} | "
            f"{r['raw_p']} | {r['holm_p']:.6g} | {r['test_status']} |"
        )
    lines += [
        "",
        "Undefined tests use a labeled conservative value of 1 only inside Holm; "
        "they cannot qualify. Zero variance never proves equivalence.",
        "",
        "## Accuracy, foreign choices and error budgets",
        "",
        "| Stage / owner / alias | Correct / scheduled | Accuracy (%) | Foreign (%) | "
        "Error budget (%) | Margin (nats) | Missing / invalid recorded |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for key, c in report["cells"].items():
        lines.append(
            f"| {key} | {c['counts']['correct_target_current']}/{c['scheduled']} | "
            f"{100 * c['accuracy']:.2f} | {100 * c['foreign_probability']:.2f} | "
            f"{100 * c['error_rate']:.2f} | {number(c['margin'])} | "
            f"{c['missing']} / {c['invalid_recorded']} |"
        )
    primary_worlds = list(report["strata"]["after_both"]["per_world"].values())
    bounds = np.mean([v["conditional_E_bounds"] for v in primary_worlds], axis=0).tolist()
    lines += [
        "",
        "At the **fixed observed accuracies**, the categorical contrast E is bounded by "
        f"{confidence(bounds)} pp. This is not a pre-run generator bound. "
        "All-success cells and all error budgets are retained in analysis.json. "
        "The accuracy endpoint remains ceiling-limited too.",
        "",
        "Revoked-target/other categories are not applicable before updates or in snapshots "
        "without printed history. Missing observations are administrative invalids, included "
        "in all-scheduled denominators and identified separately. Error-conditional shares "
        "use scheduled failures including missing cases; with no errors they are undefined. "
        "Incomplete-data estimates are descriptive and have no inferential CI or test.",
        "",
        "## Lookup and paired controls",
        "",
        f"Lookup numerical thresholds passed: **{report['lookup_numerical_pass']}**. "
        f"Eligible model gate passed: **{report['lookup_gate_passed']}**.",
        "",
        "| Control | Fully correct pairs / scheduled | Rate | Required gate |",
        "|---|---:|---:|---|",
    ]
    for key, p in report["paired_controls"].items():
        lines.append(
            f"| {key} | {p['both_correct']}/{p['scheduled_pairs']} | "
            f"{100 * p['fully_correct_rate']:.2f}% | {p['lookup_gate']} |"
        )
    lines += [
        "",
        "Every one of eight named lookup cells and eight corresponding pair cells "
        "must reach 80%. Possessive errors are outcomes, not screening exclusions. "
        "Passing those controls does not establish dynamic update competence or authorize "
        "an intervention. After-both named controls and both event orders remain visible.",
        "",
        "## Scope and reading guide",
        "",
        "The report retains all stage/order contrasts, both owner-name comparisons, "
        "score margins, world-level effects, and accuracy by account, operator, answer "
        "position, command and order in analysis.json. Those are descriptive analyses, "
        "not replacement endpoints. examples.md uses the example selected before responses; "
        "it does not select an unusually strong model answer.",
        "",
        "If E and F pass but S does not, the candidate concerns reference-sensitive "
        "own-query behavior without demonstrated own-versus-other specificity. A negative "
        "or incomplete result cannot establish unchanged behavior. This task does not "
        "measure private internal access, subjective experience or human illusionism.",
        "",
    ]
    return "\n".join(lines)


def plots(report, destination):
    plt = setup_plotting()
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    suffix = " — incomplete/invalid" if not report["inference_eligible"] else ""

    def save(fig, name):
        save_figure(fig, destination / name, report["synthetic"])
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 4))
    ax.axis("off")
    boxes = [
        (0.13, 0.5, "Two explicit owner bindings\nYour / their / owner / account"),
        (0.49, 0.5, "Same target and permissions\nBefore / snapshot / both updates"),
        (0.85, 0.5, "Four full-command scores\nExecute selected command"),
    ]
    for x, y, text in boxes:
        ax.text(
            x,
            y,
            text,
            ha="center",
            va="center",
            transform=ax.transAxes,
            bbox={"boxstyle": "round,pad=.8", "fc": "#e8f1f8", "ec": "#396080"},
        )
    for left, right in ((0.27, 0.34), (0.64, 0.72)):
        ax.annotate(
            "",
            xy=(right, 0.5),
            xytext=(left, 0.5),
            xycoords="axes fraction",
            arrowprops={"arrowstyle": "->", "lw": 2},
        )
    ax.set_title("Fixed query-reference experiment — no internal intervention")
    save(fig, "design")

    fig, ax = plt.subplots(figsize=(7, 4))
    for i, name in enumerate(("E", "F", "S")):
        r = report["primary"][name]
        ax.plot(i, r["estimate"] * 100, "o", color="#225588")
        if r["ci95"] is not None:
            ax.vlines(i, *np.array(r["ci95"]) * 100, color="#225588", linewidth=2)
    ax.axhline(0, color="gray", linewidth=0.7)
    ax.set(
        xticks=range(3),
        xticklabels=["E: foreign", "F: accuracy", "S: specificity"],
        ylabel="Percentage points",
        title="Prespecified contrasts" + suffix,
    )
    save(fig, "primary")

    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
    for ax, stage in zip(axes, STAGES):
        keys = [f"{stage}/{owner}/{form}" for owner in OWNERS for form in FORMS]
        x = np.arange(6)
        ax.bar(x - 0.18, [report["cells"][k]["accuracy"] for k in keys], 0.36, label="Correct")
        ax.bar(
            x + 0.18,
            [report["cells"][k]["foreign_probability"] for k in keys],
            0.36,
            label="Foreign",
        )
        ax.set(
            xticks=x,
            xticklabels=[k.replace(stage + "/", "").replace("/", "\n") for k in keys],
            ylim=(0, 1.03),
            title=stage,
            ylabel="Fraction of scheduled cases",
        )
        ax.tick_params(axis="x", labelsize=7, rotation=45)
    axes[0].legend()
    fig.suptitle("All aliases and checkpoints" + suffix)
    save(fig, "alias_performance")

    fig, ax = plt.subplots(figsize=(11, 4))
    for name in ("E", "F", "S"):
        ax.plot(
            range(48), np.array(report["primary"][name]["world_contrasts"]) * 100, ".-", label=name
        )
    ax.axhline(0, color="gray", linewidth=0.7)
    ax.set(
        xlabel="World index (fixed order)",
        ylabel="Percentage points",
        title="World contrasts; variants are not independent samples" + suffix,
    )
    ax.legend()
    save(fig, "world_contrasts")

    fig, ax = plt.subplots(figsize=(11, 4))
    keys = sorted(report["lookup_cells"])
    ax.bar(
        np.arange(8) - 0.18,
        [report["lookup_cells"][k]["accuracy"] for k in keys],
        0.36,
        label="Named lookup accuracy",
    )
    ax.bar(
        np.arange(8) + 0.18,
        [report["paired_controls"]["ownership/" + k]["fully_correct_rate"] for k in keys],
        0.36,
        label="Both pair members correct",
    )
    ax.axhline(0.8, color="black", linestyle="--", label="Prespecified 80% gate")
    ax.set(
        xticks=range(8),
        xticklabels=[k.replace("/", "\n") for k in keys],
        ylim=(0, 1.03),
        title="Lookup controls" + suffix,
        ylabel="Fraction of scheduled cases/pairs",
    )
    ax.tick_params(axis="x", labelsize=8)
    ax.legend(fontsize=8)
    save(fig, "lookup_controls")


def examples(runs):
    _, rows = build_inputs()
    records = {r["id"]: r for _, _, raw in runs for r in raw}
    selected = [
        r
        for r in rows
        if r["world_index"] == 0
        and r["connection_assignment"] == 0
        and r["stage"] == "after_both"
        and r["grant_mapping"] == 0
        and r["event_order"] == [0, 1]
        and r["option_rotation"] == 0
    ]
    lines = [
        "# Example fixed before responses",
        "",
        "**SYNTHETIC SOFTWARE FIXTURE**" if runs[0][0]["synthetic"] else "Recorded selections.",
        "",
    ]
    for row in selected:
        result = records.get(row["id"], {}).get("result")
        lines += [
            f"## {row['queried_owner']} / {row['query_form']}",
            "",
            "```text",
            row["prompt"],
            "```",
            "",
            f"Simulator answer: `{row['expected_command']}`.",
            "",
            "```json",
            canonical(result) if result else '{"status": "missing"}',
            "```",
            "",
        ]
    return "\n".join(lines)


def write_report(report, destination):
    write_json(destination / "analysis.json", report)
    (destination / "report.md").write_text(markdown(report))
    plots(report, destination / "figures")


def analyze(directory):
    directory = Path(directory)
    report = analyze_runs([directory])
    write_json(directory / "analysis.json", report)
    return report


def export(directory, destination):
    directory = Path(directory)
    with run_lock(directory):
        run = read_run(directory)
        from .query_reference_analysis import summarize

        report = summarize([run])
        write_report(report, directory)
        (directory / "records.jsonl").write_text("".join(canonical(r) + "\n" for r in run[2]))
        (directory / "examples.md").write_text(examples([run]))
        source = directory / "source/query-reference"
        source.mkdir(parents=True, exist_ok=True)
        for path in (SPEC_PATH, FREEZE):
            shutil.copy2(path, source / path.name)
        shutil.copytree(PREFLIGHT, source / "inputs", dirs_exist_ok=True)
        return portable_archive(directory, destination, report["status"])


def analyze_blocks(directories, destination):
    directories = [Path(p) for p in directories]
    destination = Path(destination)
    if len({p.resolve() for p in directories}) != len(directories):
        raise ValueError("Duplicate run directories")
    with ExitStack() as stack:
        for path in sorted(directories):
            stack.enter_context(run_lock(path))
        runs = [read_run(p) for p in directories]
        from .query_reference_analysis import summarize

        report = summarize(runs)
        destination.mkdir(parents=True, exist_ok=False)
        write_report(report, destination)
        (destination / "examples.md").write_text(examples(runs))
        return report
