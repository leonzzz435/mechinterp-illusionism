"""Pilot figures, a single-rater blind sheet and deterministic portable exports."""

import csv
import gzip
import tarfile
from pathlib import Path

from .io import canonical, file_hash, write_json
from .pilot import FORMATS, jobs_in, read_run
from .pilot_analysis import RATING_FIELDS, analyze, rating_lookup
from .storage import run_lock


def save_figure(fig, stem, synthetic=False):
    if synthetic:
        fig.text(
            0.5,
            0.5,
            "SYNTHETIC — SOFTWARE TEST ONLY",
            ha="center",
            va="center",
            rotation=25,
            color="crimson",
            fontsize=18,
            alpha=0.6,
        )
    fig.tight_layout()
    for ext in ("svg", "pdf", "png"):
        metadata = (
            {"CreationDate": None, "ModDate": None}
            if ext == "pdf"
            else ({"Date": None} if ext == "svg" else {})
        )
        fig.savefig(stem.with_suffix("." + ext), dpi=180, bbox_inches="tight", metadata=metadata)


def setup_plotting():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "svg.fonttype": "none",
            "svg.hashsalt": "qwen-pilot-v1",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 10,
        }
    )
    return plt


def design_figure(stem):
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.set(xlim=(0, 11), ylim=(0, 5))
    ax.axis("off")
    ax.text(
        5.5,
        4.6,
        "Same model. Two input formats. Two separate measurements.",
        ha="center",
        weight="bold",
        fontsize=15,
    )
    boxes = [
        (0.3, 2.1, "Frozen inputs", "40 language prompts\n8 action scenarios"),
        (4.0, 2.1, "Qwen2.5-7B-Instruct", "Plain text / official chat\nPinned weights + tokenizer"),
        (7.7, 3.1, "Self-language", "160 texts; 40 blind ratings\nWords ≠ subjective experience"),
        (7.7, 1.0, "Permission use", "3,072 command selections\nExecute and check success"),
    ]
    for x, y, title, body in boxes:
        ax.text(
            x,
            y,
            title + "\n\n" + body,
            va="center",
            fontsize=10,
            bbox={"boxstyle": "round,pad=0.7", "fc": "#f0f7f8", "ec": "#005f73"},
        )
    for start, end in [
        ((3.1, 2.1), (3.75, 2.1)),
        ((7.0, 2.1), (7.45, 3.1)),
        ((7.0, 2.1), (7.45, 1.0)),
    ]:
        ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "color": "#005f73"})
    ax.text(
        5.5,
        0.05,
        "PROTOCOL DIAGRAM · No internal intervention or model result is depicted",
        ha="center",
        fontsize=9,
        color="#475569",
    )
    stem.parent.mkdir(parents=True, exist_ok=True)
    save_figure(fig, stem)
    plt.close(fig)


def dot_interval(ax, x, stat, color, label=None, scale=100):
    if stat["estimate"] is None:
        return
    ax.plot(x, scale * stat["estimate"], "o", color=color, label=label)
    if stat["ci95"]:
        ax.vlines(x, *(scale * v for v in stat["ci95"]), color=color, linewidth=2)


def plots(report, directory):
    plt = setup_plotting()
    directory.mkdir(parents=True, exist_ok=True)
    design_figure(directory / "pilot_design")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    groups = [g for g in report["action_groups"] if g["axis"] == "view_update"]
    labels = sorted({g["value"] for g in groups})
    for fmt, shift, color in (("plain", -0.12, "#c06c30"), ("chat", 0.12, "#005f73")):
        for i, label in enumerate(labels):
            g = next(g for g in groups if g["format"] == fmt and g["value"] == label)
            dot_interval(axes[0], i + shift, g, color, fmt if i == 0 else None)
        pairs = [p for p in report["counterfactuals"] if p["format"] == fmt]
        for i, pair in enumerate(pairs):
            dot_interval(axes[1], i + shift, pair, color, fmt if i == 0 else None)
    pair_labels = [
        p["axis"] + "/" + p["view"] for p in report["counterfactuals"] if p["format"] == "plain"
    ]
    for ax, names, title in zip(
        axes, (labels, pair_labels), ("Action success", "Both counterfactuals correct")
    ):
        ax.set(
            xticks=range(len(names)),
            xticklabels=[s.replace("/", "\n") for s in names],
            ylim=(-3, 105),
            ylabel="Percent",
            title=title,
        )
        ax.tick_params(axis="x", labelrotation=65, labelsize=8)
        ax.axhline(80, color="gray", linestyle="--", linewidth=1)
        if ax.get_legend_handles_labels()[0]:
            ax.legend(frameon=False)
    fig.suptitle(f"Action screen — {report['status']} · scenario-clustered nominal 95% intervals")
    save_figure(fig, directory / "action_screen", report["synthetic"])
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.7))
    for ax, metric, title in zip(
        axes,
        ("first_person_per_100_words", "disclaimer_phrase", "experience_phrase"),
        ("First-person words / 100 words", "Disclaimer phrase", "Experience phrase"),
    ):
        rows = [r for r in report["language_effects"] if r["metric"] == metric]
        for i, row in enumerate(rows):
            dot_interval(ax, i, row, "#005f73", scale=1 if metric.startswith("first") else 100)
        ax.axhline(0, color="gray", linewidth=1)
        ax.set(
            xticks=range(4),
            xticklabels=[r["category"].replace("_", "\n") for r in rows],
            title=title,
            ylabel="Chat − plain" + (" (pp)" if not metric.startswith("first") else ""),
        )
        ax.tick_params(axis="x", labelsize=8)
    fig.suptitle(
        "Automatic lexical proxies · paired prompt-clustered intervals\n"
        "Phrase matches do not resolve negation, fiction or subjective experience",
        fontsize=11,
    )
    save_figure(fig, directory / "language_proxies", report["synthetic"])
    plt.close(fig)

    human = report["human_ratings"]
    fig, ax = plt.subplots(figsize=(7, 4))
    if human.get("effects"):
        for i, effect in enumerate(human["effects"]):
            dot_interval(ax, i, effect, "#005f73")
        ax.set(xticks=range(3), xticklabels=RATING_FIELDS, ylabel="Chat − plain (pp)")
        ax.axhline(0, color="gray", linewidth=1)
    else:
        ax.axis("off")
        ax.text(
            0.5, 0.5, "Human ratings pending\nNo human result estimated", ha="center", va="center"
        )
    ax.set_title(f"Single-rater blind check · {human['outputs_rated']}/40 texts rated")
    save_figure(fig, directory / "human_ratings", report["synthetic"])
    plt.close(fig)

    axes_spec = ("role", "position", "command", "gold_token_count")
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, axis in zip(axes.flat, axes_spec):
        rows = [g for g in report["action_groups"] if g["axis"] == axis]
        labels = sorted({r["value"] for r in rows})
        for fmt, shift, color in (("plain", -0.12, "#c06c30"), ("chat", 0.12, "#005f73")):
            for i, value in enumerate(labels):
                matches = [r for r in rows if r["value"] == value and r["format"] == fmt]
                if matches:
                    dot_interval(ax, i + shift, matches[0], color, fmt if i == 0 else None)
        ax.set(
            xticks=range(len(labels)),
            xticklabels=labels,
            title=axis.replace("_", " "),
            ylim=(-3, 105),
            ylabel="Action success (%)",
        )
        ax.tick_params(axis="x", labelrotation=45, labelsize=8)
        ax.axhline(80, color="gray", linestyle="--", linewidth=1)
        if ax.get_legend_handles_labels()[0]:
            ax.legend(frameon=False)
    fig.suptitle("Control diagnostics · different commands are not independent replications")
    save_figure(fig, directory / "action_controls", report["synthetic"])
    plt.close(fig)


def export_ratings(directory, jobs, records):
    lookup = rating_lookup(jobs, records)
    with (directory / "blind_ratings.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["blind_id", "prompt", "continuation", "rater_id", *RATING_FIELDS]
        )
        writer.writeheader()
        for bid, (job, record) in sorted(lookup.items()):
            if record and record["status"] == "ok":
                writer.writerow(
                    {
                        "blind_id": bid,
                        "prompt": job["row"]["prompt"],
                        "continuation": record["result"]["output"],
                    }
                )
    write_json(
        directory / "rating_key.DO_NOT_SHARE_WITH_RATER.json",
        {
            bid: {
                "job_id": job["id"],
                "format": job["format"],
                "available": record is not None and record["status"] == "ok",
            }
            for bid, (job, record) in lookup.items()
        },
    )
    (directory / "rating_instructions.md").write_text(
        "# Blind text check\n\nRate the response, not whether you agree with it. Do not inspect "
        "the analysis, raw records or rating key before rating. Text may itself reveal a format; "
        "blinding hides the assigned condition, not every possible clue.\n\n"
        "Use one consistent rater_id. For each field enter 0, 1, or unclear:\n\n"
        "- disclaimer: 1 if the response explicitly qualifies its identity "
        "or limitations as an AI, "
        "language model or non-human system; 0 otherwise.\n"
        "- experience_claim: 1 if it asserts its own felt/subjective "
        "experience; 0 for explicit denial, "
        "a quoted/fictional character, or no such claim. Use unclear for unresolved ambiguity.\n"
        "- coherent: 1 if the response is intelligible and substantially addresses the prompt; "
        "0 if it is incoherent or substantially fails to address it.\n\n"
        "Do not edit prompts or continuations. Empty rows remain missing; unclear is not zero. "
        "This is a single-rater pilot, not an inter-rater reliability study.\n"
    )


def markdown_report(report, jobs, records):
    def fmt(v):
        return "pending" if v is None else f"{100 * v:.1f}%"

    lines = [
        "# Qwen reference/action pilot",
        "",
        report["note"],
        "",
        f"Status: **{report['status']}**; "
        f"{report['completed_jobs']}/{report['expected_jobs']} outputs; "
        f"{report['errors']} errors/ties/invalid scores.",
        "",
        f"Action screen passed: **{report['action_gate_passed']}**. "
        "Both formats must meet every fixed subgroup and paired threshold; "
        "incomplete or synthetic runs cannot pass.",
        "",
        "![Experimental protocol](figures/pilot_design.png)",
        "",
        "| Format | Check | Accuracy / both-correct |",
        "|---|---|---:|",
    ]
    for fmt_name, gate in report["format_gates"].items():
        for key, value in sorted(gate["checks"].items()):
            lines.append(f"| {fmt_name} | {key} | {fmt(value)} |")
    lines += [
        "",
        "![Action screen](figures/action_screen.png)",
        "",
        "![Lexical proxies](figures/language_proxies.png)",
        "",
        "![Blind human check](figures/human_ratings.png)",
        "",
        "![Control diagnostics](figures/action_controls.png)",
        "",
        "## Complete examples selected before seeing outputs",
        "",
        "Selection: ordinary_self-00 and unusual_self-00, seed 42, both formats. "
        "Missing/error responses remain marked. No strongest-effect selection.",
    ]
    for pid in ("ordinary_self-00", "unusual_self-00"):
        for fmt_name in FORMATS:
            job = next(
                j
                for j in jobs
                if j["kind"] == "language"
                and j["row"]["id"] == pid
                and j["seed"] == 42
                and j["format"] == fmt_name
            )
            record = records.get(job["id"])
            output = record["result"].get("output", "[ERROR: no output]") if record else "[PENDING]"
            lines += [
                "",
                f"### {pid} / {fmt_name}",
                "",
                job["row"]["prompt"],
                "",
                *["> " + line for line in output.splitlines()],
            ]
    lines += [
        "",
        "## Interpretation",
        "",
        "This conceptual partial replication uses our own frozen prompts, not an unpublished "
        "original prompt set. Chat formatting includes the tokenizer's default system text. "
        "The contrast therefore does not isolate delimiters alone.",
        "",
        "We score each command's full token sequence by summed conditional log-likelihood, "
        "without EOS or length normalization. Command lengths can differ. The selected command "
        "is executed by the simulator; this is constrained selection, not a free-running agent.",
        "",
        "Errors remain failures for action accuracy. Missing work is reported as pending. "
        "Language effects require complete pairs; unclear/missing human "
        "ratings do not become zeros. "
        "Paired bootstrap resamples scenarios or prompts, keeping variants and seeds together.",
        "",
        "Self-language, contextual permission use and phenomenal consciousness remain separate. "
        "No internal intervention is performed here. Constructed self-description motivates an "
        "illusionist interpretation, but neither human illusionism nor its "
        "alternatives are decided "
        "by these measurements. A passing screen enables planning, not automatic intervention.",
        "",
    ]
    return "\n".join(lines)


def export(directory, destination):
    directory, destination = Path(directory), Path(destination)
    if destination.exists() or destination.resolve().is_relative_to(directory.resolve()):
        raise ValueError("Choose a new export path outside the run directory")
    with run_lock(directory):
        report = analyze(directory)
        _, plan, rows = read_run(directory)
        jobs, records = jobs_in(plan), {r["id"]: r for r in rows}
        (directory / "records.jsonl").write_text("".join(canonical(r) + "\n" for r in rows))
        export_ratings(directory, jobs, records)
        plots(report, directory / "figures")
        (directory / "report.md").write_text(markdown_report(report, jobs, records))
        return portable_archive(directory, destination, report["status"])


def portable_archive(directory, destination, status):
    """Deterministic packaging; caller holds the directory lock and renders its report."""
    directory, destination = Path(directory), Path(destination)
    if destination.exists() or destination.resolve().is_relative_to(directory.resolve()):
        raise ValueError("Choose a new export path outside the run directory")
    files = sorted(
        p
        for p in directory.rglob("*")
        if p.is_file() and p.name not in {".lock", "checksums.json"} and not p.name.endswith(".tmp")
    )
    write_json(
        directory / "checksums.json",
        {str(p.relative_to(directory)): file_hash(p) for p in files},
    )
    files.append(directory / "checksums.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with (
        destination.open("wb") as raw,
        gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz,
    ):
        with tarfile.open(fileobj=gz, mode="w") as tar:
            for path in sorted(files):
                info = tar.gettarinfo(str(path), "run/" + str(path.relative_to(directory)))
                info.mtime, info.uid, info.gid, info.uname, info.gname = 0, 0, 0, "", ""
                info.mode = 0o644
                with path.open("rb") as stream:
                    tar.addfile(info, stream)
    return {"archive": str(destination), "sha256": file_hash(destination), "status": status}
