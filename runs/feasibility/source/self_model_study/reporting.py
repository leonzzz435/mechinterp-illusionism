"""Result-derived figures, blind ratings and portable audit bundles."""

import csv
import json
import tarfile
from pathlib import Path

from .analysis import analyze
from .io import canonical, digest, file_hash, read_json, write_json
from .storage import read_records, run_lock


def save_figure(fig, stem, synthetic=False):
    if synthetic:
        fig.text(
            0.5,
            0.5,
            "SYNTHETIC — SOFTWARE TEST ONLY",
            ha="center",
            va="center",
            rotation=25,
            fontsize=18,
            color="crimson",
            alpha=0.55,
        )
    fig.tight_layout()
    for ext in ("svg", "pdf", "png"):
        fig.savefig(stem.with_suffix(f".{ext}"), dpi=180, bbox_inches="tight")


def plots(report, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "svg.fonttype": "none",
        }
    )
    effects = report["effects"]
    if effects:
        families = sorted({r["family"] for r in effects})
        fig, axes = plt.subplots(1, len(families), figsize=(5 * len(families), 4), squeeze=False)
        for ax, family in zip(axes[0], families):
            directions = sorted(
                {
                    r["condition"].split("@")[0]
                    for r in effects
                    if "@" in r["condition"]
                    and r["family"] == family
                    and not r["condition"].startswith("random:")
                }
            )
            for direction in directions:
                rows = sorted(
                    [
                        r
                        for r in effects
                        if r["family"] == family
                        and r["metric"] == "self_accuracy_delta"
                        and r["condition"].startswith(direction + "@")
                    ],
                    key=lambda r: float(r["condition"].split("@")[1]),
                )
                x = [100 * float(r["condition"].split("@")[1]) for r in rows]
                y = [100 * r["effect"] for r in rows]
                (line,) = ax.plot(x, y, "o-", label=direction)
                ax.vlines(
                    x,
                    [100 * r["ci"][0] for r in rows],
                    [100 * r["ci"][1] for r in rows],
                    color=line.get_color(),
                    alpha=0.7,
                )
                ax.fill_between(
                    x,
                    [100 * r["ci"][0] for r in rows],
                    [100 * r["ci"][1] for r in rows],
                    alpha=0.12,
                )
            ax.axhline(0, color="gray", linewidth=0.7)
            ax.set(
                title=family,
                xlabel="Intervention / median residual norm (%)",
                ylabel="Self-task accuracy change (percentage points)",
            )
            if directions:
                ax.legend(fontsize=8)
        fig.suptitle(
            "Scenario bootstrap intervals "
            + (
                "(Bonferroni-adjusted)"
                if report["phase"] == "confirmatory"
                else "(nominal 95%; exploratory)"
            ),
            fontsize=10,
        )
        save_figure(fig, output / "dose_response", report["synthetic"])
        plt.close(fig)
        rows = [r for r in effects if r["metric"] == "self_minus_other_delta"]
        fig, ax = plt.subplots(figsize=(9, max(4, len(rows) * 0.16)))
        for i, row in enumerate(rows):
            # CI need not contain the observed point (bootstrap bias); draw endpoints directly.
            ax.plot([100 * row["ci"][0], 100 * row["ci"][1]], [i, i], color="#536878")
            ax.plot(100 * row["effect"], i, "o", color="#005f73")
        ax.set_yticks(
            range(len(rows)), [f"{r['family']} · {r['condition']}" for r in rows], fontsize=7
        )
        ax.axvspan(-5, 5, color="gray", alpha=0.1, label="Pilot ±5 pp margin")
        ax.axvline(0, color="black", linewidth=0.8)
        ax.set_xlabel("Difference in accuracy effects: self − other (percentage points)")
        ax.set_title("Controls and ablations — paired scenario estimates")
        save_figure(fig, output / "controls_ablations", report["synthetic"])
        plt.close(fig)
    language = {
        r["condition"]: r
        for r in report["language_effects"]
        if r["metric"] == "first_person_per_100_words"
    }
    joined = [
        r for r in effects if r["metric"] == "self_accuracy_delta" and r["condition"] in language
    ]
    if joined:
        fig, ax = plt.subplots(figsize=(8, 6))
        for row in joined:
            lang = language[row["condition"]]
            x, y = lang["effect"], 100 * row["effect"]
            ax.plot(lang["ci"], [y, y], color="gray", alpha=0.3)
            ax.plot([x, x], [100 * v for v in row["ci"]], color="gray", alpha=0.3)
            ax.scatter(x, y, s=25)
            if not row["condition"].startswith("random:"):
                ax.annotate(f"{row['family']} {row['condition']}", (x, y), fontsize=6)
        ax.axhline(0, color="gray", linewidth=0.7)
        ax.axvline(0, color="gray", linewidth=0.7)
        ax.set(
            xlabel="Change in first-person words per 100 generated words",
            ylabel="Self-task accuracy change (percentage points)",
            title="Language and task performance: separate assays, not a consciousness measure",
        )
        save_figure(fig, output / "language_vs_performance", report["synthetic"])
        plt.close(fig)


def blind_ratings(records, output):
    entries, key = [], []
    for record in records:
        if record["row"]["kind"] != "language" or record["status"] != "ok":
            continue
        blind_id = digest(["blind-v1", record["trial_id"]])[:20]
        entries.append(
            {
                "blind_id": blind_id,
                "prompt": record["row"]["prompt"],
                "continuation": record["result"]["output"],
                "self_reference_0_3": "",
                "monitoring_language_0_3": "",
                "coherence_0_3": "",
                "rater_id": "",
                "notes": "",
            }
        )
        key.append(
            {
                "blind_id": blind_id,
                "trial_id": record["trial_id"],
                "condition": record["condition"]["id"],
            }
        )
    entries.sort(key=lambda x: x["blind_id"])
    if entries:
        with (output / "blind_ratings.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=entries[0].keys())
            writer.writeheader()
            writer.writerows(entries)
    write_json(output / "rating_key.DO_NOT_GIVE_TO_RATERS.json", key)


def export_run(directory, destination):
    directory, destination = Path(directory), Path(destination)
    if destination.resolve().is_relative_to(directory.resolve()):
        raise ValueError("Export destination must be outside the run directory")
    if destination.exists():
        raise ValueError("Export destination already exists; choose a new name")
    with run_lock(directory):
        report = analyze(directory)
        manifest = read_json(directory / "manifest.json")
        records = read_records(directory)
        output = directory / "export"
        output.mkdir(exist_ok=True)
        with (output / "trials.jsonl").open("w") as stream:
            for record in records:
                stream.write(canonical(record) + "\n")
        # Fixed selection rule: smallest scenario ID with baseline and a successful intervention.
        examples = []
        grouped = {}
        for r in records:
            if r["row"]["kind"] == "language" and r["status"] == "ok":
                grouped.setdefault((r["row"]["id"], r["seed"]), []).append(r)
        for key in sorted(grouped):
            group = grouped[key]
            if any(r["condition"]["id"] == "baseline" for r in group) and len(group) > 1:
                examples = [
                    {
                        "prompt": r["row"]["prompt"],
                        "seed": r["seed"],
                        "condition": r["condition"]["id"],
                        "output": r["result"]["output"],
                    }
                    for r in sorted(group, key=lambda r: r["condition"]["id"])
                ]
                break
        write_json(
            output / "examples.json",
            {
                "selection": "First lexicographic paired row/seed; full outputs",
                "synthetic": report["synthetic"],
                "examples": examples,
            },
        )
        blind_ratings(records, output)
        plots(report, output / "figures")
        disclaimer = (
            "SYNTHETIC SOFTWARE TEST: these are not model findings."
            if report["synthetic"]
            else "Exploratory/reference outputs; no confirmed dissociation."
            if report["phase"] != "confirmatory"
            else "Confirmatory run; consult completeness, baseline gates and adjusted intervals."
        )
        lines = [
            "# Pilot run report",
            "",
            disclaimer,
            "",
            f"Run: `{report['run_id']}`",
            f"Status: **{report['status']}**",
            f"Trials recorded: {len(records)} / {report['expected_jobs']}; "
            f" errors: {report['errors']}.",
            "",
            "This report measures contextual task performance and language. "
            "It does not measure phenomenal consciousness.",
            "",
            "## Baseline capability checks",
            "",
        ]
        for family, gate in report["baseline_gate"].items():
            lines.append(
                f"- {family}: {'PASS' if gate['passed'] else 'FAIL'} "
                f"(worst subgroup accuracy {min(gate['checks'].values()):.1%})."
            )
        lines += [
            "",
            "## Provenance",
            "",
            f"Source: `{manifest['provenance']['source_hash']}`",
            f"Model/SAE revisions: `{json.dumps(manifest['assets'], sort_keys=True)}`",
            "",
            "See analysis.json for paired scenario confidence intervals, Holm-adjusted p-values, "
            "format failures and secondary degradation measures. "
            "Missing comparisons are not null results.",
            "",
            "Human ratings are "
            + (
                "complete; see analysis.json for secondary effects and agreement."
                if report.get("human_ratings", {}).get("complete")
                else "pending or incomplete. Do not send the condition key to raters."
            ),
        ]
        (output / "report.md").write_text("\n".join(lines) + "\n")
        included = [
            p
            for p in directory.rglob("*")
            if p.is_file()
            and p.name != ".lock"
            and p.name != "checksums.json"
            and not p.name.endswith(".tmp")
        ]
        write_json(
            output / "checksums.json",
            {str(p.relative_to(directory)): file_hash(p) for p in included},
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(destination, "w:gz") as archive:
            for path in sorted(included + [output / "checksums.json"]):
                archive.add(path, arcname=str(Path(directory.name) / path.relative_to(directory)))
    return {
        "archive": str(destination),
        "sha256": file_hash(destination),
        "report": str(output / "report.md"),
    }
