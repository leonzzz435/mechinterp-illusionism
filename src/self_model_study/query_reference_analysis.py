"""All-scheduled categorical outcomes and the three prespecified world contrasts."""

from collections import Counter, defaultdict
from functools import lru_cache

import numpy as np
from scipy.stats import t

from .io import digest
from .pilot import jobs_in
from .query_reference import build_inputs, control_pairs, factor_key
from .query_reference_audit import CATEGORIES, applicability, classify_choice, parse_input
from .query_reference_runtime import read_run

STAGES = ("before", "snapshot", "after_both")
FORMS = ("possessive", "owner_name", "account_name")
OWNERS = ("self", "other")


@lru_cache(maxsize=1)
def bootstrap_indices():
    return np.random.default_rng(1729).integers(0, 48, size=(10000, 48))


def interval(values, eligible):
    xs = np.array(values, dtype=float)
    if not eligible or len(xs) != 48 or not np.all(np.isfinite(xs)):
        return None
    return np.quantile(xs[bootstrap_indices()].mean(axis=1), [0.025, 0.975]).tolist()


def primary_tests(vectors, eligible):
    result = {}
    for name in ("E", "F", "S"):
        xs = np.array(vectors[name], dtype=float)
        estimate = float(xs.mean())
        defined = bool(
            eligible and len(xs) == 48 and np.isfinite(xs).all() and np.var(xs, ddof=1) > 0
        )
        statistic = float(estimate / (xs.std(ddof=1) / np.sqrt(48))) if defined else None
        p = float(2 * t.sf(abs(statistic), 47)) if defined else None
        result[name] = {
            "estimate": estimate,
            "ci95": interval(xs, eligible),
            "raw_p": p,
            "t": statistic,
            "df": 47 if defined else None,
            "test_status": "defined"
            if defined
            else ("incomplete_or_invalid_worlds" if not eligible else "zero_variance"),
            "holm_input": p if defined else 1.0,
            "holm_placeholder": not defined,
            "positive_worlds": int((xs > 0).sum()),
            "world_contrasts": xs.tolist(),
        }
    previous = 0.0
    for rank, name in enumerate(sorted(result, key=lambda k: result[k]["holm_input"])):
        adjusted = min(1.0, max(previous, (3 - rank) * result[name]["holm_input"]))
        previous = adjusted
        r = result[name]
        r["holm_p"] = adjusted
        r["qualifies"] = bool(
            not r["holm_placeholder"]
            and r["estimate"] > 0
            and r["ci95"][0] > 0
            and adjusted <= 0.05
        )
    return result


def observe(row, record):
    parsed = parse_input({"prompt": row["prompt"], "choices": row["choices"]})
    result = record["result"] if record else None
    status = result.get("status") if result else "missing"
    category = (
        classify_choice(parsed, result.get("selected_command")) if status == "ok" else "invalid"
    )
    if status == "ok" and category == "invalid":
        raise ValueError("Invalid command marked as successful scoring")
    margin = None
    if result and status in {"ok", "tie"}:
        scores = {c["command"]: c.get("log_likelihood") for c in result.get("candidates", [])}
        values = [scores.get(c) for c in row["choices"]]
        if all(isinstance(v, (float, int)) and np.isfinite(v) for v in values):
            margin = float(scores[parsed["expected_command"]] - scores[parsed["foreign_command"]])
    last = "not_applicable"
    if row["events"]:
        last = "target" if row["events"][-1]["actor"] == row["target"] else "other"
    return {
        "id": row["id"],
        "world_id": row["world_id"],
        "category": category,
        "status": status,
        "margin": margin,
        "last_updated": last,
        "applicability": applicability(parsed),
        "correct": category == "correct_target_current",
        "foreign": category == "other_account_current",
    }


def cell(observations, eligible=False):
    n = len(observations)
    counts = Counter(o["category"] for o in observations)
    correct, foreign = counts["correct_target_current"], counts["other_account_current"]
    missing = sum(o["status"] == "missing" for o in observations)
    errors = n - correct
    masks = {c: all(o["applicability"][c] for o in observations) for c in CATEGORIES}
    by_world = defaultdict(list)
    for o in observations:
        by_world[o["world_id"]].append(o)

    def rates(field):
        return [np.mean([o[field] for o in v]).item() for _, v in sorted(by_world.items())]

    margins = [o["margin"] for o in observations if o["margin"] is not None]
    world_margins = (
        [np.mean([o["margin"] for o in v]).item() for _, v in sorted(by_world.items())]
        if len(margins) == n
        else []
    )
    return {
        "scheduled": n,
        "recorded": n - missing,
        "missing": missing,
        "invalid_recorded": counts["invalid"] - missing,
        "errors_including_missing": errors,
        "counts": {c: counts[c] if masks[c] else None for c in CATEGORIES},
        "applicability": masks,
        "accuracy": correct / n,
        "accuracy_ci95": interval(rates("correct"), eligible),
        "foreign_probability": foreign / n,
        "foreign_ci95": interval(rates("foreign"), eligible),
        "error_rate": errors / n,
        "all_success_cell": correct == n,
        "all_selection_shares": {c: counts[c] / n if masks[c] else None for c in CATEGORIES},
        "error_conditional_shares": {
            c: counts[c] / errors if masks[c] and errors and c != "correct_target_current" else None
            for c in CATEGORIES
        },
        "margin": float(np.mean(margins)) if margins else None,
        "margin_available": len(margins),
        "margin_missing_or_invalid": n - len(margins),
        "margin_ci95": interval(world_margins, eligible and len(margins) == n),
        "worlds": len(by_world),
    }


def contrasts(groups, world_ids):
    vectors = {name: [] for name in ("E", "F", "S")}
    details = {}
    for sid in world_ids:

        def rate(owner, form, field):
            return np.mean([o[field] for o in groups[sid, owner, form]]).item()

        e = rate("self", "possessive", "foreign") - rate("self", "account_name", "foreign")
        f = rate("self", "account_name", "correct") - rate("self", "possessive", "correct")
        other = rate("other", "account_name", "correct") - rate("other", "possessive", "correct")
        for key, value in zip(vectors, (e, f, f - other)):
            vectors[key].append(value)
        err_pos = 1 - rate("self", "possessive", "correct")
        err_acc = 1 - rate("self", "account_name", "correct")
        details[sid] = {
            "E": e,
            "F": f,
            "S": f - other,
            "F_minus_E": f - e,
            "self_possessive_error_budget": err_pos,
            "self_account_error_budget": err_acc,
            "conditional_E_bounds": [-err_acc, err_pos],
        }
    return vectors, details


def pair_report(rows, observations, eligible):
    by_id = {o["id"]: o for o in observations}
    lookup = {factor_key(r): r for r in rows}
    grouped = defaultdict(list)
    for pair in control_pairs(rows):
        key = "/".join((pair["stage"], pair["anchor_owner"], pair["query_form"]))
        a, b = by_id[pair["anchor"]], by_id[pair["counterpart"]]
        grouped[("ownership/" + key, pair["lookup_gate"])].append((a, b))
    for row in rows:
        for field, value, counterpart in (("grant_mapping", 0, 1), ("event_order", [0, 1], [1, 0])):
            if row.get(field) != value:
                continue
            partner = lookup[factor_key({**row, field: counterpart})]
            key = "/".join((field, row["stage"], row["queried_owner"], row["query_form"]))
            grouped[(key, False)].append((by_id[row["id"]], by_id[partner["id"]]))
    result = {}
    for (key, gate), pairs in sorted(grouped.items()):
        worlds = defaultdict(list)
        for a, b in pairs:
            worlds[a["world_id"]].append(int(a["correct"] and b["correct"]))
        count = sum(sum(v) for v in worlds.values())
        result[key] = {
            "scheduled_pairs": len(pairs),
            "both_correct": count,
            "missing_pairs": sum(
                a["status"] == "missing" or b["status"] == "missing" for a, b in pairs
            ),
            "fully_correct_rate": count / len(pairs),
            "ci95": interval([np.mean(v).item() for _, v in sorted(worlds.items())], eligible),
            "lookup_gate": gate,
            "numerical_pass": count / len(pairs) >= 0.8 if gate else None,
        }
    return result


def decision(primary, eligible, gates, synthetic):
    if synthetic:
        return "synthetic_software_fixture_not_model_evidence"
    if not eligible:
        return "incomplete_or_invalid_no_inference"
    if not gates:
        return "lookup_gate_failed"
    if primary["E"]["qualifies"] and primary["F"]["qualifies"]:
        return (
            "own_versus_other_specificity_candidate"
            if primary["S"]["qualifies"]
            else "reference_sensitive_own_query_candidate_without_specificity"
        )
    if any(r["holm_placeholder"] for r in primary.values()):
        return "inconclusive_degenerate_tests"
    return "no_joint_reference_candidate"


def summarize(runs):
    if not runs:
        raise ValueError("Supply at least one run block")
    worlds, rows = build_inputs()
    world_ids = [w["world_id"] for w in worlds]
    known = {r["id"]: r for r in rows}
    records, supplied, manifests = {}, set(), []
    for manifest, plan, raw in runs:
        manifests.append(manifest)
        block_ids = {j["id"] for j in jobs_in(plan)}
        for job in jobs_in(plan):
            if job["id"] in supplied or job["id"] not in known or job["row"] != known[job["id"]]:
                raise ValueError("Overlapping or changed query-reference blocks")
            supplied.add(job["id"])
        for r in raw:
            if r["id"] in records or r["id"] not in block_ids:
                raise ValueError("Duplicate or unknown query-reference record")
            records[r["id"]] = r
    for field in ("source_hash", "python", "packages", "git_commit"):
        if len({digest(m["provenance"][field]) for m in manifests}) != 1:
            raise ValueError("Cannot merge different execution provenance")
    if len({m["synthetic"] for m in manifests}) != 1:
        raise ValueError("Cannot mix synthetic and model evidence")
    if not manifests[0]["synthetic"] and len({digest(m["backend_info"]) for m in manifests}) != 1:
        raise ValueError("Cannot merge different scorer/tokenizer provenance")
    observations = [observe(r, records.get(r["id"])) for r in rows]
    valid_worlds = {
        sid
        for sid in world_ids
        if all(o["status"] == "ok" for o in observations if o["world_id"] == sid)
    }
    eligible = len(valid_worlds) == 48 and all(m["status"] == "complete" for m in manifests)
    groups, by_world, by_factor = defaultdict(list), defaultdict(list), defaultdict(list)
    secondary = defaultdict(lambda: defaultdict(list))
    for row, obs in zip(rows, observations):
        key = "/".join((row["stage"], row["queried_owner"], row["query_form"]))
        groups[key].append(obs)
        by_world[(row["world_id"], key)].append(obs)
        subset_key = (row["world_id"], row["queried_owner"], row["query_form"])
        secondary[row["stage"]][subset_key].append(obs)
        if row["stage"] == "after_both":
            secondary["after_both/last_" + obs["last_updated"]][subset_key].append(obs)
        operator = row[row["queried_owner"] + "_name"]
        world = worlds[row["world_index"]]
        factors = {
            "account": row["target"],
            "operator": operator,
            "answer_position": row["expected_position"],
            "command": row["expected_command"],
            "assignment": row["connection_assignment"],
            "last_updated": obs["last_updated"],
            "permission_order": world["permission_order"],
            "binding_order": world["binding_order"],
            "event_order": row.get("event_order", "not_applicable"),
        }
        for name, value in factors.items():
            by_factor[f"{key}/{name}/{value}"].append(obs)
    cells = {key: cell(v, eligible) for key, v in sorted(groups.items())}
    strata, alias_checks = {}, {}
    for stage, sg in sorted(secondary.items()):
        vectors, per_world = contrasts(sg, world_ids)
        strata[stage] = {
            "effects": {
                k: {"estimate": float(np.mean(v)), "ci95": interval(v, eligible)}
                for k, v in vectors.items()
            },
            "per_world": per_world,
        }
        for owner in OWNERS:
            for left, right in (("possessive", "owner_name"), ("owner_name", "account_name")):
                for field in ("correct", "foreign", "margin"):
                    values = []
                    for sid in world_ids:
                        a = [o[field] for o in sg[sid, owner, left]]
                        b = [o[field] for o in sg[sid, owner, right]]
                        values.append(float(np.mean(a) - np.mean(b)) if None not in a + b else None)
                    available = [v for v in values if v is not None]
                    alias_checks[f"{stage}/{owner}/{left}_minus_{right}/{field}"] = {
                        "estimate": float(np.mean(available)) if available else None,
                        "available_worlds": len(available),
                        "ci95": interval(available, eligible and len(available) == 48),
                        "per_world": dict(zip(world_ids, values)),
                    }
    primary_vectors, _ = contrasts(secondary["after_both"], world_ids)
    primary = primary_tests(primary_vectors, eligible)
    paired = pair_report(rows, observations, eligible)
    gate_cells = {
        k: {**v, "numerical_pass": v["accuracy"] >= 0.8}
        for k, v in cells.items()
        if k.split("/")[0] in {"before", "snapshot"} and not k.endswith("possessive")
    }
    gates = (
        len(gate_cells) == 8
        and all(c["numerical_pass"] for c in gate_cells.values())
        and all(p["numerical_pass"] for p in paired.values() if p["lookup_gate"])
    )
    synthetic = manifests[0]["synthetic"]
    return {
        "protocol": "query-self-reference-v1",
        "engine": "qwen-query-reference",
        "synthetic": synthetic,
        "run_ids": [m["run_id"] for m in manifests],
        "status": "complete" if eligible else "incomplete_or_invalid",
        "scheduled_choices": len(rows),
        "supplied_block_choices": len(supplied),
        "recorded_choices": len(records),
        "valid_complete_worlds": len(valid_worlds),
        "coverage_complete": len(records) == len(rows),
        "inference_eligible": eligible,
        "invalid_recorded": sum(o["status"] not in {"ok", "missing"} for o in observations),
        "missing": sum(o["status"] == "missing" for o in observations),
        "world_order": world_ids,
        "primary": primary,
        "strata": strata,
        "cells": cells,
        "alias_checks": alias_checks,
        "paired_controls": paired,
        "lookup_cells": gate_cells,
        "lookup_numerical_pass": bool(gates),
        "lookup_gate_passed": bool(eligible and gates and not synthetic),
        "decision": decision(primary, eligible, gates, synthetic),
        "per_world_cells": {sid: {k: cell(by_world[sid, k]) for k in cells} for sid in world_ids},
        "diagnostics": {k: cell(v) for k, v in sorted(by_factor.items())},
        "observations": observations,
        "records_sha256": digest(sorted(records.values(), key=lambda r: r["id"])),
        "uncertainty": (
            "10000 paired world draws, seed 1729; nominal 95% CIs. Two-sided paired-world "
            "t tests, df 47, normal-mean approximation; Holm over E,F,S only."
        ),
        "limits": (
            "All 16128 scheduled cases remain in denominators, including missing as invalid "
            "administrative failures. No inferential CI/test with incomplete or invalid worlds. "
            "Undefined tests cannot qualify. E and F are correlated. Passing lookup does not "
            "establish dynamic competence or authorize interventions. No equivalence, "
            "consciousness or human-illusionism conclusion."
        ),
    }


def analyze_runs(directories):
    return summarize([read_run(p) for p in directories])
