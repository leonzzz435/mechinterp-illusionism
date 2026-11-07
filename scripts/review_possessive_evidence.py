"""Offline audit of saved Qwen wording-control outputs, without study-package imports.

Reconstructs simulator outcomes, all groups, matched contrasts, counterfactuals and the
frozen decision. NumPy reproduces the seeded scenario bootstrap; a separate sign enumeration
checks the exact test. Does not rerun inference or independently recompute model likelihoods.
"""

import argparse
import hashlib
import json
import math
from collections import defaultdict
from itertools import product
from pathlib import Path, PurePosixPath

import numpy as np
from review_qwen_evidence import archive_files, digest, require
from review_role_evidence import outcome, stage

ARCHIVE = Path("review/evidence/qwen-possessive-f2baaa2fb6b74880.tar.gz")
SHA256 = "d521a63c21c360b33ba8452ab5d572eaf0d06c4e4be02df02425dfc1c2fe3e59"
PLAN_HASH = "ab455c85fb4a1c0e237dcbd317f1e0be4401d65dc2cc0a8d9bbe95994d0b511d"
CONFIG_HASH = "da751b797867be9a56dbb05ec205c0b81e4fd46594a62cb40bdc640c3dbfef73"
FRAMES = ("your", "the", "reference")
CONDITIONS = set(product(FRAMES, ("target", "other")))


def check_stat(saved, clusters, primary=False, paired=False):
    """Bootstrap scenario sums/counts; no call to the production estimator."""
    ids = sorted(clusters)
    means = {s: math.fsum(clusters[s]) / len(clusters[s]) for s in ids}
    total = math.fsum(v for s in ids for v in clusters[s])
    n = sum(len(clusters[s]) for s in ids)
    require(
        saved["n_clusters"] == len(ids) and saved["n_observations"] == n,
        "Independent unit/observation count mismatch",
    )
    require(math.isclose(saved["estimate"], total / n, abs_tol=1e-12), "Estimate mismatch")
    if paired:
        require(
            saved["complete_pairs"] and saved["expected_sextets"] == saved["observed_sextets"] == n,
            "Incomplete sextet statistic",
        )
        require(saved["scenario_means"].keys() == means.keys(), "Scenario inventory mismatch")
        require(
            all(
                math.isclose(saved["scenario_means"][s], v, abs_tol=1e-12) for s, v in means.items()
            ),
            "Scenario contrast mismatch",
        )
        require(
            saved["positive_scenarios"] == sum(v > 0 for v in means.values()),
            "Positive scenario count mismatch",
        )
    if len(ids) >= 2:
        # Sample scenario identities; retain every observation from a sampled scenario.
        sampled = np.random.default_rng(1729).choice(ids, size=(10000, len(ids)), replace=True)
        positions = {s: i for i, s in enumerate(ids)}
        weights = np.zeros((10000, len(ids)), dtype=int)
        for j in range(len(ids)):
            column = np.array([positions[s] for s in sampled[:, j]])
            weights[np.arange(10000), column] += 1
        sums = np.array([math.fsum(clusters[s]) for s in ids])
        counts = np.array([len(clusters[s]) for s in ids])
        draws = (weights @ sums) / (weights @ counts)
        expected_ci = np.quantile(draws, [0.025, 0.975])
        require(
            np.allclose(saved["ci95"], expected_ci, rtol=0, atol=1e-12),
            "Bootstrap interval mismatch",
        )
    else:
        require(saved["ci95"] is None, "Interval from fewer than two scenarios")
    if primary:
        xs = list(means.values())
        observed = abs(math.fsum(xs))
        p = sum(
            abs(math.fsum(sign * x for sign, x in zip(signs, xs))) >= observed - 1e-12
            for signs in product((-1, 1), repeat=len(xs))
        ) / 2 ** len(xs)
        require(saved["two_sided_sign_flip_p"] == p, "Sign-flip p mismatch")
    elif paired:
        require(saved["two_sided_sign_flip_p"] is None, "Undeclared secondary test")


def audit(path=ARCHIVE, sha256=SHA256):
    files, actual, checked = archive_files(path, sha256)
    manifest = json.loads(files["run/manifest.json"])
    plan = json.loads(files["run/plan.json"])
    saved = json.loads(files["run/analysis.json"])
    raw = [json.loads(line) for line in files["run/records.jsonl"].splitlines()]
    require(manifest["plan_hash"] == digest(plan) == PLAN_HASH, "Frozen plan mismatch")
    spec = manifest["config"]
    require(
        manifest["config_hash"]
        == CONFIG_HASH
        == digest({k: v for k, v in spec.items() if k != "max_seconds"}),
        "Frozen configuration mismatch",
    )
    require(
        spec["scenarios"] == list(range(16, 32))
        and spec["analysis_seed"] == 1729
        and spec["bootstrap_samples"] == 10000,
        "Changed inference protocol",
    )
    require(
        manifest["status"] == saved["status"] == "complete" and not manifest["synthetic"],
        "Requires the completed real-model archive",
    )
    source = {
        PurePosixPath(n).name: hashlib.sha256(b).hexdigest()
        for n, b in files.items()
        if n.startswith("run/source/self_model_study/")
    }
    require(
        digest(source) == manifest["provenance"]["source_hash"] == saved["analysis_source_hash"],
        "Source snapshot mismatch",
    )
    require(saved["records_hash"] == digest(raw), "Analysis record hash mismatch")
    ordered = [j for b in plan["blocks"] for j in b["jobs"]]
    jobs = {j["id"]: j for j in ordered}
    require(
        len(plan["blocks"]) == 16 and all(len(b["jobs"]) == 384 for b in plan["blocks"]),
        "Scenario block structure changed",
    )
    require(
        len(jobs) == len(ordered) == len(raw) == manifest["expected_jobs"] == 6144,
        "Incomplete/duplicate coverage",
    )
    require(
        json.loads(files["run/model_inputs.json"])
        == [
            {
                "id": j["id"],
                "prompt": j["row"]["prompt"],
                "format": "chat",
                "choices": j["row"]["choices"],
            }
            for j in ordered
        ],
        "Model input inventory mismatch",
    )
    records, accuracy, margins = {}, {}, {}
    groups = {k: defaultdict(list) for k in ("cells", "controls", "command_accuracy")}
    sextets = defaultdict(dict)
    for record in raw:
        rid = record["id"]
        require(rid in jobs and rid not in records, "Unknown/duplicate record")
        require(
            record["job"] == jobs[rid] and record["config_hash"] == CONFIG_HASH,
            "Record differs from frozen job",
        )
        require(
            digest({k: v for k, v in record.items() if k != "checksum"})
            == record["checksum"]
            == manifest["records"].get(rid),
            "Record digest mismatch",
        )
        require(record["status"] == record["result"]["status"] == "ok", "Failed measurement")
        row, result = jobs[rid]["row"], record["result"]
        records[rid] = record
        accuracy[rid] = outcome(row, result)
        scores = {c["command"]: c["log_likelihood"] for c in result["candidates"]}
        other = next(a for a in row["state"]["permissions"] if a != row["target"])
        margins[rid] = (
            scores[row["expected_command"]] - scores[row["state"]["permissions"][other][0]]
        )
        prefix = f"{row['frame']}/{row['relation']}/"
        groups["cells"][prefix + stage(row)].append(rid)
        groups["command_accuracy"][prefix + row["expected_command"]].append(rid)
        for axis, value in (
            ("target_identity", row["target_identity"]),
            ("answer_position", row["expected_position"]),
        ):
            groups["controls"][prefix + axis + "/" + str(value)].append(rid)
        if stage(row) != "after_relevant":
            groups["controls"][prefix + "checkpoint/" + stage(row)].append(rid)
        cond = row["frame"], row["relation"]
        require(cond not in sextets[row["scene_id"]], "Duplicate sextet member")
        sextets[row["scene_id"]][cond] = rid
    require(set(records) == set(manifest["records"]) == set(jobs), "Missing outputs")
    require(
        saved["completed_jobs"] == saved["expected_jobs"] == 6144
        and saved["errors"] == 0
        and saved["coverage_complete"]
        and not saved["synthetic"],
        "Wrong coverage claim",
    )
    for label, cells in groups.items():
        require(cells.keys() == saved[label].keys(), "Missing reported groups")
        for key, ids in cells.items():
            stat, clusters = saved[label][key], defaultdict(list)
            for rid in ids:
                clusters[jobs[rid]["row"]["scenario_id"]].append(accuracy[rid])
            require(stat["observed"] == stat["expected"] == len(ids), "Group coverage mismatch")
            check_stat(stat, clusters)
    require(len(groups["cells"]) == 18 and len(groups["controls"]) == 48, "Wrong group counts")
    contrasts = {k: defaultdict(lambda: defaultdict(list)) for k in ("accuracy", "margin")}
    pairs_checked = 0
    for sextet in sextets.values():
        require(set(sextet) == CONDITIONS, "Incomplete sextet")
        prompts, rendered = set(), set()
        for (frame, relation), rid in sextet.items():
            row, result = jobs[rid]["row"], records[rid]["result"]
            actor = row["mentioned_actor"]
            require(
                actor in row["state"]["permissions"]
                and (actor == row["target"]) == (relation == "target"),
                "Wrong context actor",
            )
            line = spec["context_lines"][frame].format(actor=actor)
            prompt, full = row["prompt"], result["rendered_prompt"]
            require(
                prompt.count(line) == full.count(line) == 1 and prompt in full,
                "Missing prompt/context line",
            )
            prompts.add(prompt.replace(line, "<CONTEXT>"))
            rendered.add(full.replace(line, "<CONTEXT>"))
        require(len(prompts) == len(rendered) == 1, "Extra matched-prompt differences")
        for relation in ("target", "other"):
            a, b = [records[sextet[f, relation]]["result"] for f in ("your", "the")]
            x, y = a["prompt_token_ids"], b["prompt_token_ids"]
            require(
                len(x) == len(y)
                and [(i, u, v) for i, (u, v) in enumerate(zip(x, y)) if u != v]
                == [(57, 7771, 785)],
                "Your/The token contrast changed",
            )
            require(
                [c["token_ids"] for c in a["candidates"]]
                == [c["token_ids"] for c in b["candidates"]],
                "Candidate token contrast changed",
            )
            pairs_checked += 1
        checkpoint, sid = stage(row), row["scenario_id"]
        for metric, values in (("accuracy", accuracy), ("margin", margins)):
            gaps = {f: values[sextet[f, "other"]] - values[sextet[f, "target"]] for f in FRAMES}
            gaps.update(
                interaction=gaps["your"] - gaps["the"],
                reference_anchor=gaps["your"] - gaps["reference"],
            )
            for key, value in gaps.items():
                contrasts[metric][key + "/" + checkpoint][sid].append(value)
    for metric, stats in contrasts.items():
        for key, clusters in stats.items():
            label, checkpoint = key.split("/")
            stat = (
                saved["margin_effects_nats"][key]
                if metric == "margin"
                else saved[label][checkpoint]
                if label in ("interaction", "reference_anchor")
                else saved["assignment_gaps"][key]
            )
            check_stat(
                stat,
                clusters,
                paired=True,
                primary=metric == "accuracy" and key == "interaction/after_relevant",
            )
    # Rebuild changed-answer pairs independently, without the production grouping helper.
    pair_stats = defaultdict(lambda: defaultdict(list))
    factors = ("updated", "grant_variant", "target_identity", "phase", "rotation")
    for axis in ("target_identity", "phase", "grant_variant"):
        pairs = defaultdict(list)
        for rid, j in jobs.items():
            row = j["row"]
            key = (
                row["scenario_id"],
                row["frame"],
                row["relation"],
                *(row[f] for f in factors if f != axis),
            )
            pairs[key].append(rid)
        for ids in pairs.values():
            require(len(ids) == 2, "Counterfactual inventory mismatch")
            if jobs[ids[0]]["row"]["expected_command"] == jobs[ids[1]]["row"]["expected_command"]:
                continue
            row = jobs[ids[0]]["row"]
            pair_stats[f"{row['frame']}/{row['relation']}/{axis}"][row["scenario_id"]].append(
                int(all(accuracy[r] for r in ids))
            )
    require(pair_stats.keys() == saved["counterfactuals"].keys(), "Missing counterfactual groups")
    for key, clusters in pair_stats.items():
        stat = saved["counterfactuals"][key]
        require(
            stat["observed_pairs"] == stat["expected_pairs"] == sum(map(len, clusters.values())),
            "Counterfactual coverage mismatch",
        )
        check_stat(stat, clusters)
    controls_pass = all(stat["estimate"] >= 0.8 for stat in saved["controls"].values())
    require(controls_pass == saved["controls_passed"], "Wrong control decision")
    primary, rules = saved["interaction"]["after_relevant"], spec["decision"]
    candidate = (
        primary["estimate"] >= rules["minimum_interaction"]
        and primary["ci95"][0] > 0
        and primary["positive_scenarios"] >= rules["minimum_positive_scenarios"]
        and primary["two_sided_sign_flip_p"] <= rules["primary_two_sided_alpha"]
    )
    decision = (
        "stop_control_failure"
        if not controls_pass
        else "possessive_wording_candidate"
        if candidate
        else "no_clear_possessive_specificity"
    )
    require(
        saved["same_source_as_execution"] and saved["decision"] == decision, "Wrong frozen decision"
    )
    require(
        not saved["internal_intervention_authorized"]
        and not saved["original_capability_screen_changed"],
        "Overstated authorization",
    )
    return {
        "archive_sha256": actual,
        "verified_payloads": checked,
        "verified_records": len(raw),
        "verified_sextets": len(sextets),
        "matched_token_pairs": pairs_checked,
        "verified_accuracy_groups": sum(len(g) for g in groups.values()),
        "verified_counterfactual_groups": len(pair_stats),
        "verified_paired_statistics": 30,
        "bootstrap_intervals_recomputed": sum(len(g) for g in groups.values())
        + len(pair_stats)
        + 30,
        "controls_passed": controls_pass,
        "primary_interaction": primary,
        "reference_anchor": saved["reference_anchor"]["after_relevant"],
        "decision": decision,
        "source_hash": digest(source),
        "limitations": "Independent saved-output reaggregation, including the seeded bootstrap "
        "and exact sign test; not an independent researcher, new model inference, independent "
        "likelihood arithmetic or construct validation.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", nargs="?", type=Path, default=ARCHIVE)
    parser.add_argument("--sha256", default=SHA256)
    args = parser.parse_args()
    print(json.dumps(audit(args.archive, args.sha256), indent=2, sort_keys=True))
