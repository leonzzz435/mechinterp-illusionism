"""Reaggregate the completed frozen role-control archive without study-package imports.

Checks scores, simulator transitions, matched inputs, controls, interactions and the exact
sign-flip calculation. Does not rerun inference or independently validate model likelihoods
or bootstrap intervals. The original archive is read without extraction.
"""

import argparse
import hashlib
import json
import math
from collections import defaultdict
from copy import deepcopy
from itertools import product
from pathlib import Path, PurePosixPath

from review_qwen_evidence import archive_files, compare_estimate, digest, require

ARCHIVE = Path("review/evidence/qwen-role-96787d5e7adf4c4d.tar.gz")
SHA256 = "36614cb2aae236d450d57540c9b76dfddfec2d4bd2a59f177dce296058b13a8d"
PLAN_HASH = "ee4dfa480160113843b530897828e6b94009b00f8e1590a7d38975e4bacc4a76"
CONFIG_HASH = "198046dba2e6469d8eefaa3309cad54d56d41b2b4998258e6045a1ade251f962"
CONDITIONS = set(product(("active", "reference"), ("target", "other")))


def outcome(row, result):
    state = deepcopy(row["before"])
    event, target = row["event"], row["target"]
    require(
        state["permissions"][target] == [state["commands"][row["target_identity"]]],
        "Target identity mismatch",
    )
    require(state["permissions"][event["actor"]] == [event["revoke"]], "Wrong revoke")
    require(event["grant"] == state["commands"][2 + row["grant_variant"]], "Wrong grant")
    if row["phase"] == "after":
        state["permissions"][event["actor"]] = [event["grant"]]
    require(state == row["state"], "Simulator state mismatch")
    require(row["relevant_update"] == (target == event["actor"]), "Update relevance mismatch")
    gold = state["permissions"][target]
    require(gold == [row["expected_command"]], "Gold command mismatch")
    require(row["choices"][row["expected_position"]] == gold[0], "Gold position mismatch")
    candidates = result["candidates"]
    require([c["command"] for c in candidates] == row["choices"], "Candidate order mismatch")
    scores = [c["log_likelihood"] for c in candidates]
    require(all(s is not None and math.isfinite(s) for s in scores), "Invalid score")
    require(scores.count(max(scores)) == 1, "Tied scores")
    selected = row["choices"][scores.index(max(scores))]
    require(result["selected_command"] == selected, "Selection disagrees with saved scores")
    require(
        all(c["token_count"] == len(c["token_ids"]) > 0 for c in candidates), "Token count mismatch"
    )
    accepted = selected in gold
    if accepted:
        state["markers"][target] += 1
    require(
        result["execution"]
        == {
            "actor": target,
            "command": selected,
            "accepted": accepted,
            "correct": accepted,
            "valid_command": True,
            "reason": "executed" if accepted else "permission_denied",
            "state_after": state,
        },
        "Simulator execution mismatch",
    )
    return int(accepted)


def stage(row):
    return (
        "before"
        if row["phase"] == "before"
        else ("after_relevant" if row["relevant_update"] else "after_irrelevant")
    )


def audit(path=ARCHIVE, sha256=SHA256):
    files, actual, checked = archive_files(path, sha256)
    manifest = json.loads(files["run/manifest.json"])
    plan = json.loads(files["run/plan.json"])
    saved = json.loads(files["run/analysis.json"])
    raw = [json.loads(line) for line in files["run/records.jsonl"].splitlines()]
    require(manifest["plan_hash"] == digest(plan) == PLAN_HASH, "Frozen plan mismatch")
    require(
        manifest["config_hash"]
        == CONFIG_HASH
        == digest({k: v for k, v in manifest["config"].items() if k != "max_seconds"}),
        "Frozen configuration mismatch",
    )
    require(
        manifest["status"] == saved["status"] == "complete" and not manifest["synthetic"],
        "This audit requires completed real-model data",
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
        len(jobs) == len(ordered) == len(raw) == manifest["expected_jobs"] == 2048,
        "Incomplete or duplicate coverage",
    )
    require(
        json.loads(files["run/model_inputs.json"])
        == [
            {
                "id": j["id"],
                "prompt": j["row"]["prompt"],
                "format": j["format"],
                "choices": j["row"]["choices"],
            }
            for j in ordered
        ],
        "Model inputs differ from frozen plan",
    )
    records, values = {}, {}
    cells, controls, quartets = defaultdict(list), defaultdict(list), defaultdict(dict)
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
        records[rid] = record
        row = jobs[rid]["row"]
        values[rid] = outcome(row, record["result"])
        prefix, checkpoint = f"{row['frame']}/{row['relation']}/", stage(row)
        cells[prefix + checkpoint].append(rid)
        for axis, value in (
            ("target_identity", row["target_identity"]),
            ("answer_position", row["expected_position"]),
        ):
            controls[prefix + axis + "/" + str(value)].append(rid)
        if checkpoint != "after_relevant":
            controls[prefix + "checkpoint/" + checkpoint].append(rid)
        condition = row["frame"], row["relation"]
        require(condition not in quartets[row["scene_id"]], "Duplicate quartet member")
        quartets[row["scene_id"]][condition] = rid
    require(set(records) == set(jobs) == set(manifest["records"]), "Missing outputs")
    require(
        saved["completed_jobs"] == saved["expected_jobs"] == 2048
        and saved["errors"] == 0
        and saved["coverage_complete"]
        and not saved["synthetic"],
        "Wrong coverage claim",
    )
    for groups, label, count in ((cells, "cells", 12), (controls, "controls", 32)):
        require(len(groups) == count and groups.keys() == saved[label].keys(), "Missing groups")
        for key, ids in groups.items():
            stat = saved[label][key]
            require(stat["observed"] == stat["expected"] == len(ids), "Group count mismatch")
            compare_estimate(
                stat, [values[i] for i in ids], [jobs[i]["row"]["scenario_id"] for i in ids]
            )
    contrasts = defaultdict(lambda: defaultdict(list))
    for quartet in quartets.values():
        require(set(quartet) == CONDITIONS, "Incomplete quartet")
        normalized, rendered = set(), set()
        for (frame, relation), rid in quartet.items():
            row = jobs[rid]["row"]
            actor = row["mentioned_actor"]
            require(
                actor in row["state"]["permissions"]
                and (actor == row["target"]) == (relation == "target"),
                "Wrong context actor",
            )
            line = manifest["config"]["context_lines"][frame].format(actor=actor)
            prompt, full = row["prompt"], records[rid]["result"]["rendered_prompt"]
            require(
                prompt.count(line) == full.count(line) == 1 and prompt in full,
                "Missing prompt or context line",
            )
            normalized.add(prompt.replace(line, "<CONTEXT>"))
            rendered.add(full.replace(line, "<CONTEXT>"))
        require(len(normalized) == len(rendered) == 1, "Extra quartet prompt differences")
        checkpoint, sid = stage(row), row["scenario_id"]
        gaps = {}
        for frame in ("active", "reference"):
            gap = values[quartet[frame, "other"]] - values[quartet[frame, "target"]]
            gaps[frame] = gap
            contrasts[frame + "/" + checkpoint][sid].append(gap)
        contrasts["interaction/" + checkpoint][sid].append(gaps["active"] - gaps["reference"])
    for key, clusters in contrasts.items():
        family, checkpoint = key.split("/")
        stat = (
            saved["interaction"][checkpoint]
            if family == "interaction"
            else saved["assignment_gaps"][key]
        )
        xs = [x for values_ in clusters.values() for x in values_]
        ids = [sid for sid, values_ in clusters.items() for _ in values_]
        require(
            stat["observed_quartets"] == stat["expected_quartets"] == len(xs)
            and stat["complete_pairs"],
            "Incomplete paired estimate",
        )
        compare_estimate(stat, xs, ids)
        if family == "interaction":
            means = {sid: sum(v) / len(v) for sid, v in clusters.items()}
            require(
                stat["scenario_means"] == means
                and stat["positive_scenarios"] == sum(v > 0 for v in means.values()),
                "Scenario effect mismatch",
            )
    primary = saved["interaction"]["after_relevant"]
    means = list(primary["scenario_means"].values())
    require(len(means) == 8, "Wrong independent scenario count")
    p = (
        sum(
            abs(sum(s * x for s, x in zip(signs, means)) / 8) >= abs(sum(means) / 8)
            for signs in product((-1, 1), repeat=8)
        )
        / 256
    )
    require(p == primary["two_sided_sign_flip_p"], "Sign-flip p mismatch")
    rules = manifest["config"]["decision"]
    controls_pass = all(
        sum(values[i] for i in ids) / len(ids) >= rules["control_accuracy"]
        for ids in controls.values()
    )
    require(controls_pass == saved["controls_passed"], "Wrong control decision")
    active = saved["assignment_gaps"]["active/after_relevant"]["estimate"]
    expected_decision = (
        "stop_control_failure"
        if not controls_pass
        else "stop_assignment_gap_not_replicated"
        if active < rules["minimum_active_gap"]
        else "wording_sensitive_candidate"
        if (
            primary["estimate"] >= rules["minimum_interaction"]
            and primary["ci95"][0] > 0
            and primary["positive_scenarios"] >= rules["minimum_positive_scenarios"]
            and p <= rules["primary_two_sided_alpha"]
        )
        else "stop_no_clear_wording_specificity"
    )
    require(
        saved["same_source_as_execution"] and saved["decision"] == expected_decision,
        "Wrong candidate decision",
    )
    require(
        not saved["internal_intervention_authorized"]
        and not saved["original_capability_screen_changed"],
        "Overstated authorization",
    )
    return {
        "archive_sha256": actual,
        "verified_file_checksums": checked,
        "verified_records": len(records),
        "verified_quartets": len(quartets),
        "verified_cells": len(cells),
        "verified_controls": len(controls),
        "controls_passed": controls_pass,
        "primary_interaction": primary["estimate"],
        "primary_two_sided_sign_flip_p": p,
        "positive_scenarios": primary["positive_scenarios"],
        "decision": expected_decision,
        "source_hash": digest(source),
        "limitations": (
            "Independent reaggregation of saved outputs, not independent model inference, "
            "likelihood arithmetic, bootstrap implementation or construct validation."
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", nargs="?", type=Path, default=ARCHIVE)
    parser.add_argument("--sha256", default=SHA256)
    args = parser.parse_args()
    print(json.dumps(audit(args.archive, args.sha256), indent=2, sort_keys=True))
