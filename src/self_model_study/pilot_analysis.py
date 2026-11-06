"""Descriptive clustered estimates and prespecified pilot capability screens."""

import csv
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

from .io import digest, file_hash, source_hash, write_json
from .pilot import CATEGORIES, FORMATS, jobs_in, read_run

RATING_FIELDS = ("disclaimer", "experience_claim", "coherent")
LANGUAGE_METRICS = ("first_person_per_100_words", "disclaimer_phrase", "experience_phrase")


def language_metrics(text):
    words = re.findall(r"\b[\w']+\b", text.lower().replace("’", "'"))
    first = sum(
        w in {"i", "i'm", "i've", "i'll", "i'd", "me", "my", "mine", "myself"} for w in words
    )
    return {
        "word_count": len(words),
        "first_person_per_100_words": 100 * first / max(1, len(words)),
        "disclaimer_phrase": int(
            bool(
                re.search(
                    r"\b(?:as (?:an? )?(?:ai|language model)|"
                    r"i (?:am|was) (?:an? )?(?:ai|language model)|"
                    r"i (?:do not|don't) (?:have|experience|feel))\b",
                    text,
                    re.I,
                )
            )
        ),
        # Lexical proxy only: negation, quotation and fiction are NOT resolved.
        "experience_phrase": int(
            bool(
                re.search(
                    r"\b(?:i feel|i experience|i am aware|i'm aware|my experience)\b", text, re.I
                )
            )
        ),
    }


def estimate(cluster_values, samples=10000):
    """Resample independent clusters, keeping every repeat/variant together."""
    clusters = [v for _, v in sorted(cluster_values.items()) if v]
    if not clusters:
        return {"estimate": None, "ci95": None, "n_clusters": 0, "n_observations": 0}
    sums = np.array([sum(v) for v in clusters], dtype=float)
    counts = np.array([len(v) for v in clusters], dtype=float)
    point = float(sums.sum() / counts.sum())
    ci = None
    if len(clusters) >= 2:
        indices = np.random.default_rng(1729).integers(0, len(clusters), (samples, len(clusters)))
        draws = sums[indices].sum(axis=1) / counts[indices].sum(axis=1)
        ci = np.quantile(draws, [0.025, 0.975]).tolist()
    return {
        "estimate": point,
        "ci95": ci,
        "n_clusters": len(clusters),
        "n_observations": int(counts.sum()),
    }


def stratum(row):
    return (
        "before"
        if row["phase"] == "before"
        else ("after_relevant" if row["relevant_update"] else "after_irrelevant")
    )


def correct(record):
    return int(
        record is not None
        and record["status"] == "ok"
        and record["result"].get("execution", {}).get("correct", False)
    )


def action_groups(jobs, records, samples):
    groups = defaultdict(list)
    for job in jobs:
        if job["kind"] != "action":
            continue
        row, fmt = job["row"], job["format"]
        keys = [
            ("overall", "all"),
            ("view_update", row["view"] + "/" + stratum(row)),
            ("role", str(row["identity"])),
            ("position", str(row["expected_position"])),
            ("command", row["expected_command"]),
        ]
        record = records.get(job["id"])
        if record and "candidates" in record["result"]:
            candidate = next(
                c for c in record["result"]["candidates"] if c["command"] == row["expected_command"]
            )
            keys.append(("gold_token_count", str(candidate["token_count"])))
        for axis, value in keys:
            groups[(fmt, axis, value)].append((job, record))
    result = []
    for (fmt, axis, value), rows in sorted(groups.items()):
        values = defaultdict(list)
        for job, record in rows:
            if record:
                values[job["row"]["scenario_id"]].append(correct(record))
        result.append(
            {
                "format": fmt,
                "axis": axis,
                "value": value,
                "expected": len(rows),
                "observed": sum(r is not None for _, r in rows),
                "errors": sum(r is not None and r["status"] != "ok" for _, r in rows),
                **estimate(values, samples),
            }
        )
    return result


def counterfactuals(jobs, records, samples):
    results = []
    factors = ("updated", "grant_variant", "identity", "view", "phase", "rotation")
    for fmt in FORMATS:
        for label, axis in (("role", "identity"), ("update", "phase"), ("grant", "grant_variant")):
            groups = defaultdict(list)
            for job in jobs:
                if job["kind"] != "action" or job["format"] != fmt:
                    continue
                row = job["row"]
                key = (row["scenario_id"], *(row[f] for f in factors if f != axis))
                groups[key].append(job)
            by_view = {v: [] for v in ("self", "named_self", "other")}
            for group in groups.values():
                if len(group) != 2:
                    raise ValueError("Incomplete paired design")
                a, b = group
                if a["row"]["expected_command"] != b["row"]["expected_command"]:
                    by_view[a["row"]["view"]].append((a, b))
            for view, pairs in by_view.items():
                values, flips = defaultdict(list), defaultdict(list)
                for a, b in pairs:
                    ra, rb = records.get(a["id"]), records.get(b["id"])
                    if ra is None or rb is None:
                        continue
                    sid = a["row"]["scenario_id"]
                    values[sid].append(correct(ra) * correct(rb))
                    flips[sid].append(
                        int(
                            ra["status"] == rb["status"] == "ok"
                            and ra["result"]["selected_command"] != rb["result"]["selected_command"]
                        )
                    )
                results.append(
                    {
                        "format": fmt,
                        "axis": label,
                        "view": view,
                        "expected_pairs": len(pairs),
                        **estimate(values, samples),
                        "prediction_flip": estimate(flips, samples),
                    }
                )
    return results


def language_summary(jobs, records, samples):
    summaries, effects = [], []
    for category in CATEGORIES:
        selected = [j for j in jobs if j["kind"] == "language" and j["row"]["category"] == category]
        for metric in LANGUAGE_METRICS:
            for fmt in FORMATS:
                values = defaultdict(list)
                subset = [j for j in selected if j["format"] == fmt]
                for job in subset:
                    record = records.get(job["id"])
                    if record and record["status"] == "ok":
                        values[job["row"]["id"]].append(
                            language_metrics(record["result"]["output"])[metric]
                        )
                summaries.append(
                    {
                        "category": category,
                        "format": fmt,
                        "metric": metric,
                        "expected": len(subset),
                        **estimate(values, samples),
                    }
                )
            pairs = defaultdict(dict)
            for job in selected:
                record = records.get(job["id"])
                if record and record["status"] == "ok":
                    pairs[(job["row"]["id"], job["seed"])][job["format"]] = language_metrics(
                        record["result"]["output"]
                    )[metric]
            complete = len(pairs) == 20 and all(set(p) == set(FORMATS) for p in pairs.values())
            values = defaultdict(list)
            if complete:
                for (pid, _), pair in pairs.items():
                    values[pid].append(pair["chat"] - pair["plain"])
            effects.append(
                {
                    "category": category,
                    "metric": metric,
                    "complete_pairs": complete,
                    "contrast": "chat_minus_plain",
                    **estimate(values, samples),
                }
            )
    return summaries, effects


def rating_lookup(jobs, records):
    return {
        digest(["qwen-blind-v1", j["id"]])[:24]: (j, records.get(j["id"]))
        for j in jobs
        if j["kind"] == "language" and j["seed"] == 42 and j["row"]["category"] in CATEGORIES[:2]
    }


def read_ratings(path, lookup, samples):
    values, rater = {}, set()
    with open(path, newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"blind_id", "rater_id", "prompt", "continuation", *RATING_FIELDS} <= set(
            reader.fieldnames or []
        ):
            raise ValueError("Rating CSV is missing required columns")
        seen = set()
        for row in reader:
            bid = row["blind_id"]
            if bid not in lookup or bid in seen:
                raise ValueError("Unknown or duplicate blind ID")
            seen.add(bid)
            job, record = lookup[bid]
            if not record or record["status"] != "ok":
                raise ValueError("Cannot rate an absent or failed generation")
            if (
                row["prompt"] != job["row"]["prompt"]
                or row["continuation"] != record["result"]["output"]
            ):
                raise ValueError("Rating CSV changed the original text")
            if not row["rater_id"].strip() and not any(row[f].strip() for f in RATING_FIELDS):
                continue
            if not row["rater_id"].strip() or any(
                row[f] not in {"0", "1", "unclear"} for f in RATING_FIELDS
            ):
                raise ValueError("Use one rater_id and 0, 1 or unclear for each dimension")
            rater.add(row["rater_id"].strip())
            values[job["id"]] = {
                f: None if row[f] == "unclear" else int(row[f]) for f in RATING_FIELDS
            }
    if len(rater) > 1:
        raise ValueError("This pilot specifies one human rater; do not pool different raters")
    effects = []
    for field in RATING_FIELDS:
        grouped = defaultdict(dict)
        for job, _ in lookup.values():
            if job["id"] in values:
                grouped[job["row"]["id"]][job["format"]] = values[job["id"]][field]
        complete = len(grouped) == 20 and all(
            set(p) == set(FORMATS) and None not in p.values() for p in grouped.values()
        )
        deltas = {pid: [p["chat"] - p["plain"]] for pid, p in grouped.items()} if complete else {}
        effects.append({"metric": field, "complete_pairs": complete, **estimate(deltas, samples)})
    return {
        "sha256": file_hash(path),
        "outputs_expected": 40,
        "outputs_rated": len(values),
        "unclear_cells": sum(v is None for r in values.values() for v in r.values()),
        "single_rater": True,
        "complete": len(values) == 40,
        "effects": effects,
    }


def summarize(directory, ratings=None):
    directory = Path(directory)
    manifest, plan, raw = read_run(directory)
    jobs, records = jobs_in(plan), {r["id"]: r for r in raw}
    samples = manifest["config"]["bootstrap_samples"]
    coverage_complete = len(raw) == len(jobs)
    groups = action_groups(jobs, records, samples)
    pairs = counterfactuals(jobs, records, samples)
    language, effects = language_summary(jobs, records, samples)
    threshold = manifest["config"]["gate_threshold"]
    same_source = manifest["provenance"]["source_hash"] == source_hash()
    gates = {}
    for fmt in FORMATS:
        checks = {
            f"{g['axis']}:{g['value']}": g["estimate"]
            for g in groups
            if g["format"] == fmt and g["axis"] in {"view_update", "role", "position"}
        }
        checks.update(
            {f"pair:{p['axis']}:{p['view']}": p["estimate"] for p in pairs if p["format"] == fmt}
        )
        gates[fmt] = {
            "checks": checks,
            "numerical_pass": len(checks) == 24
            and all(v is not None and v >= threshold for v in checks.values()),
        }
    action_deltas = defaultdict(list)
    for job in jobs:
        if job["kind"] == "action" and job["format"] == "plain":
            other_id = digest([manifest["protocol"], job["row"]["id"], "chat"])
            if job["id"] in records and other_id in records:
                action_deltas[job["row"]["scenario_id"]].append(
                    correct(records[other_id]) - correct(records[job["id"]])
                )
    action_paired_complete = sum(map(len, action_deltas.values())) == 1536
    report = {
        "protocol": manifest["protocol"],
        "run_id": manifest["run_id"],
        "status": manifest["status"],
        "synthetic": manifest["synthetic"],
        "coverage_complete": coverage_complete,
        "expected_jobs": len(jobs),
        "completed_jobs": len(raw),
        "errors": sum(r["status"] != "ok" for r in raw),
        "same_source_as_execution": same_source,
        "analysis_source_hash": source_hash(),
        "records_hash": digest(raw),
        "format_gates": gates,
        "action_gate_passed": bool(
            coverage_complete
            and manifest["status"] in {"complete", "complete_with_errors"}
            and not manifest["synthetic"]
            and same_source
            and all(g["numerical_pass"] for g in gates.values())
        ),
        "action_groups": groups,
        "counterfactuals": pairs,
        "action_format_effect": {
            "contrast": "chat_minus_plain",
            "complete_pairs": action_paired_complete,
            **estimate(action_deltas if action_paired_complete else {}, samples),
        },
        "language": language,
        "language_effects": effects,
        "human_ratings": {"outputs_expected": 40, "outputs_rated": 0, "complete": False},
        "note": "Development screen only. Eight independent action scenarios; nominal clustered "
        "95% intervals are descriptive, not multiplicity-adjusted "
        "confirmation or equivalence evidence.",
    }
    if manifest["synthetic"]:
        report["note"] = "SYNTHETIC SOFTWARE TEST — not model evidence. " + report["note"]
    ratings_path = Path(ratings) if ratings else directory / "human_ratings.csv"
    if ratings_path.exists():
        report["human_ratings"] = read_ratings(ratings_path, rating_lookup(jobs, records), samples)
    return report


def analyze(directory, ratings=None):
    directory = Path(directory)
    report = summarize(directory, ratings)
    if ratings:
        import shutil

        target = directory / "human_ratings.csv"
        if Path(ratings).resolve() != target.resolve():
            if target.exists() and file_hash(target) != file_hash(ratings):
                raise ValueError("Existing human ratings differ; preserve the original rating file")
            shutil.copyfile(ratings, target)
    write_json(directory / "analysis.json", report)
    return report
