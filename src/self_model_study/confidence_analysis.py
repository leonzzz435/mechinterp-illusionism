"""Question-cluster inference and fixed out-of-fold difficulty controls."""

import warnings
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from . import confidence_data as data
from .confidence import fit_temperature, probabilities, read_run
from .io import read_json, write_json


def ratio(numerator, denominator):
    numerator, denominator = np.broadcast_arrays(numerator, denominator)
    return np.divide(
        numerator, denominator, out=np.full(numerator.shape, np.nan), where=denominator != 0
    )


def interval(point, draws):
    values = np.asarray(draws)
    invalid = int(np.sum(~np.isfinite(values)))
    return {
        "estimate": float(point) if np.isfinite(point) else None,
        "ci95": np.quantile(values, [0.025, 0.975]).tolist() if not invalid else None,
        "undefined_bootstrap_draws": invalid,
    }


def clustered_rate(numerators, denominators, indices):
    n, d = np.asarray(numerators, dtype=float), np.asarray(denominators, dtype=float)
    return interval(ratio(n.sum(), d.sum()), ratio(n[indices].sum(axis=1), d[indices].sum(axis=1)))


def auc_from_counts(pos, neg):
    return ratio(
        (pos * (np.cumsum(neg, axis=-1) - 0.5 * neg)).sum(axis=-1),
        pos.sum(axis=-1) * neg.sum(axis=-1),
    )


def clustered_auc(labels, scores, indices):
    labels, scores = np.asarray(labels, dtype=bool), np.asarray(scores, dtype=float)
    unique, categories = np.unique(scores, return_inverse=True)
    categories = categories.reshape(scores.shape)
    pos = np.zeros((len(labels), len(unique)))
    neg = np.zeros_like(pos)
    for i in range(len(labels)):
        np.add.at(pos[i], categories[i], labels[i].astype(float))
        np.add.at(neg[i], categories[i], (~labels[i]).astype(float))
    # Aggregate question multiplicities; never materialize draws × questions × bins.
    weights = np.zeros((len(indices), len(labels)))
    np.add.at(weights, (np.repeat(np.arange(len(indices)), indices.shape[1]), indices.ravel()), 1)
    return interval(
        auc_from_counts(pos.sum(0), neg.sum(0)), auc_from_counts(weights @ pos, weights @ neg)
    )


def temperature_for(records, spec, directory=None):
    calibration = [r for r in records if r["job"]["row"]["split"] == "calibration"]
    if len(calibration) != spec["design"]["calibration_items"] * 4 or any(
        r["status"] != "ok" for r in calibration
    ):
        return None
    path = Path(directory) / "calibration.json" if directory else None
    return read_json(path) if path and path.exists() else fit_temperature(calibration, spec)


def paired_rows(records, temperature):
    grouped = defaultdict(dict)
    for r in records:
        row = r["job"]["row"]
        if row["split"] == "assessment" and r["status"] == "ok":
            grouped[row["item_id"], row["rotation"]][row["phase"]] = r
    result = []
    for (item_id, rotation), stages in sorted(grouped.items()):
        if set(stages) != {"answer", "confidence", "abstention"}:
            continue
        answer, confidence, optional = [stages[s] for s in ("answer", "confidence", "abstention")]
        a, c, o = answer["result"], confidence["result"], optional["result"]
        row = answer["job"]["row"]
        scores = [v["log_likelihood"] for v in a["candidates"]]
        selected = int(a["selected_command"]) - 1
        result.append(
            {
                "item_id": item_id,
                "rotation": rotation,
                "correct_position": row["correct_number"],
                "answer_position": a["selected_command"],
                "optional_answer": o["selected_command"],
                "correct": a["judgment"]["correct"],
                "optional_correct": o["judgment"]["correct"],
                "abstained": o["judgment"]["abstained"],
                "confidence": c["judgment"]["confidence"],
                "raw_confidence": float(probabilities(scores)[selected]),
                "calibrated_confidence": float(probabilities(scores, temperature)[selected]),
                "external_difficulty": row["external_difficulty"],
                "embedding": row["embedding"],
                "menu_mass": {s: stages[s]["result"]["judgment"]["menu_mass"] for s in stages},
            }
        )
    return result


def reliability(labels, scores, indices):
    bins = []
    for b in range(10):
        mask = (scores >= b / 10) & ((scores < (b + 1) / 10) if b < 9 else (scores <= 1))
        count = int(mask.sum())
        bins.append(
            {
                "lower": b / 10,
                "upper": (b + 1) / 10,
                "count": count,
                "questions": int(mask.any(axis=1).sum()),
                "mean_confidence": float(scores[mask].mean()) if count else None,
                "accuracy": clustered_rate((labels * mask).sum(1), mask.sum(1), indices),
            }
        )
    return bins


def conditional_predictors(rows, spec, indices, item_ids):
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.linear_model import LogisticRegression

    design = spec["design"]
    config = design["conditional_predictors"]
    ordered = sorted(item_ids, key=lambda i: data.digest([design["seed"], "fold", i]))
    folds = {i: j % config["folds"] for j, i in enumerate(ordered)}
    y = np.array([r["correct"] for r in rows], dtype=int)
    fold = np.array([folds[r["item_id"]] for r in rows])
    external = np.array(
        [
            [
                r["external_difficulty"],
                *r["embedding"],
                *[int(r["answer_position"] == str(p)) for p in (2, 3, 4)],
            ]
            for r in rows
        ]
    )
    q = np.array([r["calibrated_confidence"] for r in rows])[:, None]
    v = np.array([r["confidence"] for r in rows])[:, None]
    matrices = {
        "E": external,
        "E+Q": np.column_stack((external, q)),
        "E+Q+V": np.column_stack((external, q, v)),
    }
    result = {
        "status": "ok",
        "fold_by_item": folds,
        "models": {},
        "loss_reductions": {},
        "interval_scope": "Fixed out-of-fold predictions, conditional on fitted models; "
        "excludes refit uncertainty.",
        "position_feature": "Recorded forced-answer position, "
        "not the hidden correct-answer position.",
    }
    losses = {}
    for name, matrix in matrices.items():
        predicted = np.full(len(y), np.nan)
        coefficients = []
        for f in range(config["folds"]):
            train, test = fold != f, fold == f
            if len(np.unique(y[train])) < 2 or not test.any():
                result.update(
                    status="unavailable", error="One-class training fold or empty test fold"
                )
                return result
            # Continuous columns: difficulty and 10 PCs, plus Q/V; never scale indicator columns.
            continuous = list(range(11)) + list(range(14, matrix.shape[1]))
            mean, scale = matrix[train][:, continuous].mean(0), matrix[train][:, continuous].std(0)
            scale[scale == 0] = 1
            standardized = matrix.copy()
            standardized[:, continuous] = (standardized[:, continuous] - mean) / scale
            model = LogisticRegression(
                C=config["regularization_C"],
                solver=config["solver"],
                tol=config["tolerance"],
                max_iter=config["max_iterations"],
                fit_intercept=True,
                class_weight=None,
            )
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("error", ConvergenceWarning)
                    model.fit(standardized[train], y[train])
                predicted[test] = model.predict_proba(standardized[test])[:, 1]
            except (ValueError, ConvergenceWarning) as exc:
                result.update(status="unavailable", error=f"{type(exc).__name__}: {exc}")
                return result
            coefficients.append(
                {
                    "fold": f,
                    "training_questions": sorted(
                        set(np.array([r["item_id"] for r in rows])[train])
                    ),
                    "mean": mean.tolist(),
                    "scale": scale.tolist(),
                    "coefficient": model.coef_[0].tolist(),
                    "intercept": model.intercept_.tolist(),
                    "iterations": model.n_iter_.tolist(),
                }
            )
        clipped = np.clip(predicted, 1e-12, 1 - 1e-12)
        loss = -(y * np.log(clipped) + (1 - y) * np.log1p(-clipped))
        per_question = np.array(
            [np.mean(loss[[r["item_id"] == i for r in rows]]) for i in item_ids]
        )
        losses[name] = per_question
        result["models"][name] = {
            "log_loss": interval(per_question.mean(), per_question[indices].mean(1)),
            "out_of_fold_probabilities": predicted.tolist(),
            "fits": coefficients,
        }
    for previous, extended in (("E", "E+Q"), ("E+Q", "E+Q+V")):
        delta = losses[previous] - losses[extended]
        result["loss_reductions"][extended] = interval(delta.mean(), delta[indices].mean(1))
    return result


def summarize(manifest, plan, records, directory=None):
    spec, design = manifest["config"], manifest["config"]["design"]
    errors = [r["id"] for r in records if r["status"] != "ok"]
    complete = (
        len(records) == manifest["expected_jobs"]
        and not errors
        and manifest["status"] == "complete"
    )
    temperature = temperature_for(records, spec, directory)
    rows = paired_rows(records, temperature["temperature"]) if temperature else []
    groups = defaultdict(list)
    for r in rows:
        groups[r["item_id"]].append(r)
    item_ids = sorted(i for i, variants in groups.items() if len(variants) == 4)
    selected = [r for i in item_ids for r in sorted(groups[i], key=lambda r: r["rotation"])]
    report = {
        "protocol": manifest["protocol"],
        "run_id": manifest["run_id"],
        "status": manifest["status"],
        "synthetic": manifest["synthetic"],
        "complete": complete,
        "completed_jobs": len(records),
        "expected_jobs": manifest["expected_jobs"],
        "error_ids": errors,
        "pending_jobs": manifest["expected_jobs"] - len(records),
        "complete_assessment_questions": len(item_ids),
        "paired_variants": len(selected),
        "calibration": temperature,
        "rows": selected,
        "decision": "incomplete",
        "primary": None,
        "metrics": {},
        "conditional_predictors": None,
        "complete_case_descriptive_only": not complete,
    }
    report["blocked_confidence_jobs"] = [
        j["id"] for block in plan["blocks"] for j in block["jobs"] if j["parent_id"] in errors
    ]
    if not item_ids:
        return report
    n = len(item_ids)
    indices = np.random.default_rng(design["seed"]).integers(
        0, n, (design["bootstrap_resamples"], n)
    )
    y = np.array([r["correct"] for r in selected], dtype=bool).reshape(n, 4)
    z = np.array([r["abstained"] for r in selected], dtype=bool).reshape(n, 4)
    o = np.array([r["optional_correct"] for r in selected], dtype=bool).reshape(n, 4)
    wrong_z, wrong = ((~y) & z).sum(1), (~y).sum(1)
    right_z, right = (y & z).sum(1), y.sum(1)
    s = ratio(wrong_z.sum(), wrong.sum()) - ratio(right_z.sum(), right.sum())
    draws = ratio(wrong_z[indices].sum(1), wrong[indices].sum(1)) - ratio(
        right_z[indices].sum(1), right[indices].sum(1)
    )
    report["primary"] = interval(s, draws)
    metrics = report["metrics"]
    denominator = np.full(n, 4)
    for name, numerator, den in (
        ("forced_accuracy", y.sum(1), denominator),
        ("optional_accuracy_all", o.sum(1), denominator),
        ("coverage", (~z).sum(1), denominator),
        ("abstention", z.sum(1), denominator),
        ("answered_only_accuracy", o.sum(1), (~z).sum(1)),
        ("payoff", (o.astype(int) - ((~o) & (~z)).astype(int)).sum(1), denominator),
        ("abstain_after_wrong", wrong_z, wrong),
        ("abstain_after_correct", right_z, right),
    ):
        metrics[name] = clustered_rate(numerator, den, indices)
    report["calibration_bins"] = {}
    for name in ("confidence", "raw_confidence", "calibrated_confidence"):
        scores = np.array([r[name] for r in selected]).reshape(n, 4)
        metrics[name + "_auroc"] = clustered_auc(y, scores, indices)
        brier = ((scores - y) ** 2).mean(1)
        metrics[name + "_brier"] = interval(brier.mean(), brier[indices].mean(1))
        report["calibration_bins"][name] = reliability(y, scores, indices)
    report["transitions"] = {
        f"{initial}->{outcome}": int((mask & target).sum())
        for initial, mask in (("correct", y), ("wrong", ~y))
        for outcome, target in (("correct", o), ("wrong", (~o) & (~z)), ("abstain", z))
    }
    report["breakdowns"] = {}
    for field, values in (("rotation", range(4)), ("correct_position", ("1", "2", "3", "4"))):
        for value in values:
            mask = np.array([r[field] == value for r in selected]).reshape(n, 4)
            report["breakdowns"][f"{field}/{value}"] = {
                "variants": int(mask.sum()),
                "questions": int(mask.any(1).sum()),
                "forced_accuracy": clustered_rate((y & mask).sum(1), mask.sum(1), indices),
                "abstention": clustered_rate((z & mask).sum(1), mask.sum(1), indices),
            }
    report["confidence_occupancy"] = dict(
        sorted(Counter(str(r["confidence"]) for r in selected).items())
    )
    report["menu_mass"] = {
        phase: {
            "minimum": min(r["menu_mass"][phase] for r in selected),
            "mean": float(np.mean([r["menu_mass"][phase] for r in selected])),
        }
        for phase in ("answer", "confidence", "abstention")
    }
    # Each question can occur in more than one group across rotations; do not add these counts.
    group_counts = {
        "forced_correct": int(y.any(1).sum()),
        "forced_wrong": int((~y).any(1).sum()),
        "abstained": int(z.any(1).sum()),
        "answered": int((~z).any(1).sum()),
    }
    usable = (
        min(group_counts.values()) >= design["feasibility"]["minimum_distinct_questions_per_group"]
        and len(report["confidence_occupancy"])
        >= design["feasibility"]["minimum_confidence_categories"]
    )
    report["feasibility"] = {
        "group_questions": group_counts,
        "usable": usable,
        "overlapping_groups": True,
    }
    if complete and n == design["assessment_items"]:
        report["conditional_predictors"] = conditional_predictors(selected, spec, indices, item_ids)
        primary, auc = report["primary"], metrics["confidence_auroc"]
        rule = design["behavioral_candidate"]
        candidate = (
            usable
            and primary["estimate"] is not None
            and primary["estimate"] >= rule["minimum_primary_effect"]
            and primary["ci95"] is not None
            and primary["ci95"][0] > rule["primary_ci_lower_above"]
            and auc["ci95"] is not None
            and auc["ci95"][0] > rule["confidence_auroc_ci_lower_above"]
        )
        report["decision"] = (
            "measurement_unusable"
            if not usable
            else "behavioral_candidate_for_review"
            if candidate
            else "no_behavioral_candidate"
        )
    if manifest["synthetic"]:
        report["decision"] = "synthetic_only"
    return report


def analyze(directory):
    manifest, plan, records = read_run(directory)
    report = summarize(manifest, plan, records, directory)
    write_json(Path(directory) / "analysis.json", report)
    return report
