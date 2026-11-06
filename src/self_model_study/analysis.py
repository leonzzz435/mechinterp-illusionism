"""Scenario-clustered paired statistics; no seeds or variants treated as independent samples."""

from collections import defaultdict

import numpy as np

from .io import digest, read_json, source_hash, write_json
from .runner import baseline_gate
from .storage import read_records


def holm(pvalues):
    order = np.argsort(pvalues)
    adjusted = [1.0] * len(pvalues)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(pvalues) - rank) * pvalues[index])
        adjusted[index] = min(1.0, running)
    return adjusted


def paired_statistics(deltas, samples=10000, alpha=0.05, multiplicity=1, seed=42):
    values = np.asarray(deltas, dtype=float)
    if len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("At least two finite independent scenarios are required")
    rng = np.random.default_rng(seed)
    # Bounded memory, even for substantially enlarged follow-up datasets.
    boot, permuted = [], []
    for start in range(0, samples, 250):
        size = min(250, samples - start)
        boot.extend(values[rng.integers(0, len(values), (size, len(values)))].mean(1))
        permuted.extend((values * rng.choice([-1, 1], (size, len(values)))).mean(1))
    tail = alpha / (2 * multiplicity)
    interval = np.quantile(boot, [tail, 1 - tail]).tolist()
    effect = float(values.mean())
    p = (1 + np.count_nonzero(np.abs(permuted) >= abs(effect) - 1e-12)) / (samples + 1)
    return {
        "effect": effect,
        "ci": interval,
        "p_value": float(p),
        "n_scenarios": len(values),
        "degenerate_bootstrap": bool(np.ptp(values) == 0),
        "bootstrap_tail_expected_draws": samples * tail,
        "tail_resolution_ok": samples * tail >= 10,
        "method": "paired scenario bootstrap; scenario sign-flip test",
    }


def paired_deltas(records, condition_id, family, metric, view=None):
    pairs = defaultdict(dict)
    for r in records:
        row = r["row"]
        if row["family"] != family or (view is not None and row["view"] != view):
            continue
        cid = r["condition"]["id"]
        if cid not in {"baseline", condition_id}:
            continue
        key = (row["scenario_id"], row["id"], r["seed"])
        if r["status"] != "ok" or metric not in r.get("result", {}):
            pairs[key][cid] = None
        else:
            pairs[key][cid] = float(r["result"][metric])
    grouped = defaultdict(list)
    for (sid, _, _), pair in pairs.items():
        if len(pair) != 2 or any(v is None for v in pair.values()):
            return None  # Never silently analyze a selectively completed comparison.
        grouped[sid].append(pair[condition_id] - pair["baseline"])
    return {sid: float(np.mean(vals)) for sid, vals in grouped.items()}


def summarize(directory):
    manifest = read_json(directory / "manifest.json")
    config = manifest["config"]
    records = read_records(directory)
    if manifest.get("records_hash") != digest(records):
        raise ValueError("Trial journal differs from the recorded manifest checksum")
    complete = manifest["status"] == "complete" and not manifest["error_jobs"]
    real = not manifest["synthetic"]
    calibration = read_json(directory / "calibration.json")
    matching_source = manifest["provenance"]["source_hash"] == source_hash()
    scientific = (
        complete
        and real
        and manifest.get("health", {}).get("passed", False)
        and calibration.get("passed", False)
        and matching_source
    )
    report = {
        "schema_version": 1,
        "run_id": manifest["run_id"],
        "synthetic": not real,
        "status": manifest["status"],
        "complete": complete,
        "scientific_results_eligible": bool(scientific),
        "phase": config["phase"],
        "split": config["split"],
        "records_hash": digest(records),
        "analysis_source_hash": source_hash(),
        "same_source_as_execution": matching_source,
        "completed_jobs": len(records),
        "expected_jobs": manifest["expected_jobs"],
        "errors": manifest["error_jobs"],
        "baseline_gate": baseline_gate(config, records) if config["phase"] != "reference" else {},
        "effects": [],
        "language_effects": [],
        "descriptive": [],
    }
    ratings_path = directory / "ratings.csv"
    rating_records = None
    if ratings_path.exists():
        from .ratings import read_ratings

        report["human_ratings"], rating_records = read_ratings(ratings_path, records)
    grouped = defaultdict(list)
    for record in records:
        row = record["row"]
        grouped[(row["family"], row["view"], record["condition"]["id"])].append(record)
    for (family, view, cid), rows in sorted(grouped.items()):
        stat = {
            "family": family,
            "view": view,
            "condition": cid,
            "n_trials": len(rows),
            "n_scenarios": len({r["row"]["scenario_id"] for r in rows}),
            "errors": sum(r["status"] != "ok" for r in rows),
            "invalid_format": sum(not r.get("result", {}).get("valid", False) for r in rows),
        }
        for metric in (
            "correct",
            "first_person_per_100_words",
            "repeated_bigram_fraction",
            "unmodified_model_continuation_nll",
            "option_mass",
        ):
            vals = [r.get("result", {}).get(metric) for r in rows]
            vals = [float(v) for v in vals if v is not None]
            if vals:
                stat[metric] = float(np.mean(vals))
        report["descriptive"].append(stat)
    if not complete:
        report["notice"] = "Partial/error run: descriptive counts only; no inferential claims."
        return report
    if not real:
        report["notice"] = "SYNTHETIC SOFTWARE TEST — not model evidence."
    ids = sorted({r["condition"]["id"] for r in records} - {"baseline"})
    comparisons = []
    for family in config["dataset"]["families"]:
        for cid in ids:
            own = paired_deltas(records, cid, family, "correct", "self")
            other = paired_deltas(records, cid, family, "correct", "other")
            if not own or not other or own.keys() != other.keys():
                continue
            for metric, values in [
                ("self_accuracy_delta", own),
                ("other_accuracy_delta", other),
                ("self_minus_other_delta", {k: own[k] - other[k] for k in own}),
            ]:
                comparisons.append((family, cid, metric, list(values.values())))
    stats = config["statistics"]
    confirm = config["phase"] == "confirmatory"
    multiplicity = max(1, len(comparisons)) if confirm else 1
    for family, cid, metric, values in comparisons:
        if len(values) < 2:
            continue
        result = paired_statistics(
            values, stats["bootstrap_samples"], stats["alpha"], multiplicity, config["seed"]
        )
        result.update(
            family=family,
            condition=cid,
            metric=metric,
            ci_multiplicity=multiplicity,
            confirmatory=confirm and scientific,
        )
        lo, hi = result["ci"]
        result["within_equivalence_margin"] = bool(
            confirm
            and scientific
            and result["tail_resolution_ok"]
            and not result["degenerate_bootstrap"]
            and lo > -stats["equivalence_margin"]
            and hi < stats["equivalence_margin"]
        )
        report["effects"].append(result)
    adjusted = holm([r["p_value"] for r in report["effects"]])
    for effect, p in zip(report["effects"], adjusted):
        effect["p_holm"] = p
    # Language effects are secondary and exploratory, including in the confirmation report.
    for cid in ids:
        for metric in (
            "first_person_per_100_words",
            "repeated_bigram_fraction",
            "unmodified_model_continuation_nll",
        ):
            values = paired_deltas(records, cid, "language", metric)
            if values and len(values) >= 2:
                stat = paired_statistics(
                    list(values.values()),
                    stats["bootstrap_samples"],
                    stats["alpha"],
                    1,
                    config["seed"],
                )
                stat.update(condition=cid, metric=metric, confirmatory=False)
                report["language_effects"].append(stat)
    if rating_records is not None and report["human_ratings"]["complete"]:
        from .ratings import DIMENSIONS

        report["human_ratings"]["effects"] = []
        for cid in ids:
            for metric in DIMENSIONS:
                values = paired_deltas(rating_records, cid, "language", metric)
                if values and len(values) >= 2:
                    stat = paired_statistics(
                        list(values.values()),
                        stats["bootstrap_samples"],
                        stats["alpha"],
                        1,
                        config["seed"],
                    )
                    stat.update(condition=cid, metric=metric, confirmatory=False)
                    report["human_ratings"]["effects"].append(stat)
    return report


def analyze(directory, ratings=None):
    import shutil
    from pathlib import Path

    directory = Path(directory)
    if ratings is not None:
        from .ratings import read_ratings

        read_ratings(ratings, read_records(directory))
        target = directory / "ratings.csv"
        if target.exists() and target.read_bytes() != Path(ratings).read_bytes():
            raise ValueError(
                "Ratings already recorded; do not silently overwrite a rater submission"
            )
        if not target.exists():
            shutil.copy2(ratings, target)
    report = summarize(directory)
    write_json(directory / "analysis.json", report)
    return report
