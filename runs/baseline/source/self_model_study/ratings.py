"""Auditable secondary analysis of condition-blinded human text ratings."""

import csv
from collections import defaultdict

import numpy as np

from .io import digest, file_hash

DIMENSIONS = ("self_reference_0_3", "monitoring_language_0_3", "coherence_0_3")


def read_ratings(path, records):
    lookup = {
        digest(["blind-v1", r["trial_id"]])[:20]: r
        for r in records
        if r["row"]["kind"] == "language" and r["status"] == "ok"
    }
    ratings, seen = defaultdict(list), set()
    with open(path, newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"blind_id", "rater_id", *DIMENSIONS} <= set(reader.fieldnames or []):
            raise ValueError("Rating CSV is missing required columns")
        for row in reader:
            if not row["rater_id"].strip() and not any(row[k].strip() for k in DIMENSIONS):
                continue  # Unfilled template row: visible missingness, not zero scores.
            key = (row["blind_id"], row["rater_id"].strip())
            if key[0] not in lookup or not key[1] or key in seen:
                raise ValueError("Unknown blind ID, missing rater ID, or duplicate rater/output")
            values = {}
            for dimension in DIMENSIONS:
                if row[dimension] not in {"0", "1", "2", "3"}:
                    raise ValueError("Each submitted rating must be an integer from 0 to 3")
                values[dimension] = int(row[dimension])
            # Prevent accidental editing of the material that was supposedly rated.
            original = lookup[key[0]]
            for field, value in (
                ("prompt", original["row"]["prompt"]),
                ("continuation", original["result"]["output"]),
            ):
                if field in row and row[field] != value:
                    raise ValueError(f"Rating CSV changed the original {field}")
            seen.add(key)
            ratings[key[0]].append(values)
    coverage = sum(len(ratings[k]) >= 2 for k in lookup)
    summary = {
        "sha256": file_hash(path),
        "outputs_expected": len(lookup),
        "outputs_rated": len(ratings),
        "outputs_with_two_raters": coverage,
        "complete": bool(lookup) and coverage == len(lookup),
        "secondary_only": True,
        "agreement": {},
    }
    pseudo_records = []
    for blind_id, original in lookup.items():
        values = ratings[blind_id]
        result = {d: float(np.mean([v[d] for v in values])) for d in DIMENSIONS} if values else {}
        pseudo_records.append({**original, "result": result})
    for dimension in DIMENSIONS:
        disagreement = []
        for values in ratings.values():
            for i in range(len(values)):
                for j in range(i):
                    disagreement.append(abs(values[i][dimension] - values[j][dimension]))
        summary["agreement"][dimension] = {
            "mean_absolute_rater_difference": float(np.mean(disagreement))
            if disagreement
            else None,
            "n_rater_pairs": len(disagreement),
        }
    return summary, pseudo_records
