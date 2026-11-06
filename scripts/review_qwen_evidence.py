"""Independent offline audit of Qwen pilot archives; standard library only.

Reaggregates saved likelihoods, simulator outcomes, strata and counterfactuals.
Does not run inference, establish the validity of the construct, or independently
verify likelihood values or bootstrap intervals. Never extracts archive contents.
"""

import argparse
import csv
import hashlib
import io
import json
import math
import tarfile
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path, PurePosixPath

PLAN_HASH = "01014cf0746e4d42836454bec780a0917d4b2b953dab6ddc373a4dda8d03243f"
MODEL_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def archive_files(path, sha256=None):
    actual = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    require(sha256 is None or actual == sha256, "Archive digest mismatch")
    with tarfile.open(path) as archive:
        members = archive.getmembers()
        require(all(m.isfile() for m in members), "Non-file archive member")
        require(
            all(
                not PurePosixPath(m.name).is_absolute() and ".." not in PurePosixPath(m.name).parts
                for m in members
            ),
            "Unsafe archive path",
        )
        files = {m.name: archive.extractfile(m).read() for m in members}
    require(len(files) == len(members), "Duplicate archive member")
    checksums = json.loads(files["run/checksums.json"])
    require(
        set(files) == {"run/" + name for name in checksums} | {"run/checksums.json"},
        "Incomplete checksum inventory",
    )
    for name, expected in checksums.items():
        require(hashlib.sha256(files["run/" + name]).hexdigest() == expected, name + " changed")
    return files, actual, len(checksums)


def outcome(row, result, status):
    """Reconstruct state and execution without importing the study simulator."""
    state = deepcopy(row["before"])
    actors = list(state["permissions"])
    require(len(actors) == 2 and row["assigned"] in actors, "Invalid actor assignment")
    # The assignment's integer index is defined by the initial command order,
    # not dictionary order (JSON canonicalization sorts actor names).
    assigned = next(
        a for a in actors if state["permissions"][a] == [state["commands"][row["identity"]]]
    )
    require(row["assigned"] == assigned, "Assigned identity mismatch")
    target = next(a for a in actors if a != assigned) if row["view"] == "other" else assigned
    require(row["target"] == target, "Bound target mismatch")
    event = row["event"]
    require(
        state["permissions"][event["actor"]] == [event["revoke"]]
        and event["revoke"] == state["commands"][row["updated"]]
        and event["grant"] == state["commands"][2 + row["grant_variant"]],
        "Invalid update",
    )
    if row["phase"] == "after":
        state["permissions"][event["actor"]] = [event["grant"]]
    require(state == row["state"], "Saved simulator state mismatch")
    require(row["relevant_update"] == (target == event["actor"]), "Wrong update relevance")
    gold = state["permissions"][target]
    require(gold == [row["expected_command"]], "Oracle disagrees with reconstructed state")
    require(row["choices"][row["expected_position"]] == gold[0], "Oracle position mismatch")
    if status == "error":
        return 0, None
    candidates = result["candidates"]
    require([c["command"] for c in candidates] == row["choices"], "Candidate order mismatch")
    scores = [c["log_likelihood"] for c in candidates]
    if any(v is None or not math.isfinite(v) for v in scores):
        selected, expected_status = None, "invalid_scores"
    elif scores.count(max(scores)) != 1:
        selected, expected_status = None, "tie"
    else:
        selected, expected_status = row["choices"][scores.index(max(scores))], "ok"
    require(status == expected_status, "Score status mismatch")
    require(result["selected_command"] == selected, "Selection disagrees with saved scores")
    known, accepted = selected in state["commands"], selected in gold
    if accepted:
        state["markers"][target] += 1
    expected = {
        "actor": target,
        "command": selected,
        "valid_command": known,
        "accepted": accepted,
        "correct": accepted,
        "reason": "executed" if accepted else "permission_denied" if known else "invalid_command",
        "state_after": state,
    }
    require(result["execution"] == expected, "Saved execution disagrees with reconstructed state")
    return int(accepted and status == "ok"), selected


def compare_estimate(saved, values, clusters):
    point = sum(values) / len(values) if values else None
    require(saved["estimate"] == point, "Point estimate mismatch")
    require(saved["n_observations"] == len(values), "Observation count mismatch")
    require(saved["n_clusters"] == len(set(clusters)), "Independent cluster count mismatch")
    return point


def audit_ratings(files, jobs, records, saved):
    """Check supplied judgments and their pairing without importing study analysis."""
    content = files["run/human_ratings.csv"]
    expected = {
        digest(["qwen-blind-v1", rid])[:24]: job
        for rid, job in jobs.items()
        if job["kind"] == "language"
        and job["seed"] == 42
        and job["row"]["category"] in {"ordinary_self", "unusual_self"}
    }
    fields = ("disclaimer", "experience_claim", "coherent")
    rows = list(csv.DictReader(io.StringIO(content.decode())))
    seen, rated, raters = set(), {}, set()
    counts = {metric: {fmt: Counter() for fmt in ("plain", "chat")} for metric in fields}
    for row in rows:
        bid = row["blind_id"]
        require(bid in expected and bid not in seen, "Unknown/duplicate human rating ID")
        seen.add(bid)
        job = expected[bid]
        record = records[job["id"]]
        require(
            row["prompt"] == job["row"]["prompt"]
            and row["continuation"] == record["result"]["output"],
            "Human rating changed source text",
        )
        if not row["rater_id"].strip() and not any(row[f].strip() for f in fields):
            continue
        require(row["rater_id"].strip(), "Missing human rater ID")
        require(all(row[f] in {"0", "1", "unclear"} for f in fields), "Invalid human judgment")
        raters.add(row["rater_id"].strip())
        rated[bid] = row
        for metric in fields:
            counts[metric][job["format"]][row[metric]] += 1
    require(len(raters) <= 1 and saved["single_rater"], "Unexpected multiple human raters")
    require(saved["sha256"] == hashlib.sha256(content).hexdigest(), "Human rating hash mismatch")
    require(saved["outputs_expected"] == len(expected) == 40, "Wrong rating design")
    require(saved["outputs_rated"] == len(rated), "Wrong human rating coverage")
    require(saved["complete"] == (len(rated) == 40), "Wrong human completion claim")
    unclear = sum(row[f] == "unclear" for row in rated.values() for f in fields)
    require(saved["unclear_cells"] == unclear, "Ambiguous judgments lost")
    pair_counts = {}
    for metric in fields:
        pairs = defaultdict(dict)
        for bid, row in rated.items():
            job = expected[bid]
            pairs[job["row"]["id"]][job["format"]] = row[metric]
        complete = len(pairs) == 20 and all(
            set(pair) == {"plain", "chat"} and "unclear" not in pair.values()
            for pair in pairs.values()
        )
        effect = next(e for e in saved["effects"] if e["metric"] == metric)
        require(effect["complete_pairs"] == complete, "Incorrect human pairing claim")
        delta = (
            [int(pair["chat"]) - int(pair["plain"]) for pair in pairs.values()] if complete else []
        )
        compare_estimate(effect, delta, list(pairs) if complete else [])
        if not complete:
            require(effect["ci95"] is None, "Effect estimated despite incomplete determinate pairs")
        pair_counts[metric] = dict(
            Counter(
                pair.get("plain", "missing") + "/" + pair.get("chat", "missing")
                for pair in pairs.values()
            )
        )
    # Post hoc sensitivity check, NOT a replacement for the registered bootstrap.
    positive = pair_counts["disclaimer"].get("0/1", 0)
    negative = pair_counts["disclaimer"].get("1/0", 0)
    discordant = positive + negative
    tail = sum(math.comb(discordant, i) for i in range(min(positive, negative) + 1))
    exact = (
        min(1.0, 2 * tail / 2**discordant)
        if next(e for e in saved["effects"] if e["metric"] == "disclaimer")["complete_pairs"]
        else None
    )
    return {
        "sha256": saved["sha256"],
        "outputs_rated": len(rated),
        "unclear_cells": unclear,
        "counts": counts,
        "paired_counts_plain_chat": pair_counts,
        "post_hoc_disclaimer_exact_sign_check": {
            "discordant_pairs": discordant,
            "chat_only_positive": positive,
            "plain_only_positive": negative,
            "two_sided_probability_under_symmetric_signs": exact,
            "note": "Conditional on discordance and independent equally likely signs under null; "
            "post hoc sensitivity only, not the prespecified bootstrap or a confirmatory test.",
        },
    }


def audit(path, sha256=None):
    files, actual, checked = archive_files(path, sha256)
    manifest = json.loads(files["run/manifest.json"])
    plan = json.loads(files["run/plan.json"])
    saved = json.loads(files["run/analysis.json"])
    raw = [json.loads(line) for line in files["run/records.jsonl"].splitlines()]
    require(manifest["plan_hash"] == digest(plan) == PLAN_HASH, "Frozen plan mismatch")
    spec = manifest["config"]
    require(spec["model"]["revision"] == MODEL_REVISION, "Wrong model revision")
    require(spec["score"] == "sum_log_likelihood" and spec["gate_threshold"] == 0.8, "Wrong rule")
    require(
        digest({k: v for k, v in spec.items() if k != "max_seconds"}) == manifest["config_hash"],
        "Configuration digest mismatch",
    )
    source = {
        PurePosixPath(name).name: hashlib.sha256(data).hexdigest()
        for name, data in files.items()
        if name.startswith("run/source/self_model_study/")
    }
    require(digest(source) == manifest["provenance"]["source_hash"], "Source snapshot mismatch")
    require(saved["records_hash"] == digest(raw), "Analysis used different records")
    jobs = {j["id"]: j for b in plan["blocks"] for j in b["jobs"]}
    require(len(jobs) == manifest["expected_jobs"] == saved["expected_jobs"] == 3232, "Wrong plan")
    require(
        Counter(j["kind"] for j in jobs.values()) == {"language": 160, "action": 3072},
        "Wrong planned coverage",
    )
    records, outcomes, selections = {}, {}, {}
    for record in raw:
        rid = record["id"]
        require(rid in jobs and rid not in records, "Unknown/duplicate record")
        require(record["job"] == jobs[rid], "Record differs from planned job")
        require(record["config_hash"] == manifest["config_hash"], "Record config mismatch")
        checksum = digest({k: v for k, v in record.items() if k != "checksum"})
        require(checksum == record["checksum"], "Record digest mismatch")
        require(manifest["records"].get(rid) == checksum, "Manifest record digest mismatch")
        require(record["status"] == record["result"]["status"], "Record status mismatch")
        records[rid] = record
        if jobs[rid]["kind"] == "action":
            outcomes[rid], selections[rid] = outcome(
                jobs[rid]["row"], record["result"], record["status"]
            )
    require(set(records) == set(manifest["records"]), "Missing committed records")
    complete = len(raw) == len(jobs)
    require(saved["coverage_complete"] == complete, "Wrong completion claim")
    require(saved["completed_jobs"] == len(raw), "Wrong completed count")
    require(saved["errors"] == sum(r["status"] != "ok" for r in raw), "Wrong failure count")
    require(saved["status"] == manifest["status"], "Wrong run status")

    groups = defaultdict(list)
    for rid, job in jobs.items():
        if job["kind"] != "action":
            continue
        row = job["row"]
        update = (
            "before"
            if row["phase"] == "before"
            else "after_relevant"
            if row["relevant_update"]
            else "after_irrelevant"
        )
        keys = [
            ("overall", "all"),
            ("view_update", row["view"] + "/" + update),
            ("role", str(row["identity"])),
            ("position", str(row["expected_position"])),
            ("command", row["expected_command"]),
        ]
        if rid in records and "candidates" in records[rid]["result"]:
            gold = next(
                c
                for c in records[rid]["result"]["candidates"]
                if c["command"] == row["expected_command"]
            )
            keys.append(("gold_token_count", str(gold["token_count"])))
        for axis, value in keys:
            groups[(job["format"], axis, value)].append(rid)
    require(len(groups) == len(saved["action_groups"]), "Wrong number of reported strata")
    checks = {fmt: {} for fmt in ("plain", "chat")}
    for group in saved["action_groups"]:
        ids = groups[(group["format"], group["axis"], group["value"])]
        observed = [rid for rid in ids if rid in records]
        require(group["expected"] == len(ids), "Wrong planned stratum coverage")
        require(group["observed"] == len(observed), "Wrong stratum coverage")
        point = compare_estimate(
            group,
            [outcomes[rid] for rid in observed],
            [jobs[rid]["row"]["scenario_id"] for rid in observed],
        )
        if group["axis"] in {"view_update", "role", "position"}:
            checks[group["format"]][group["axis"] + ":" + group["value"]] = point

    for counter in saved["counterfactuals"]:
        axis = {"role": "identity", "update": "phase", "grant": "grant_variant"}[counter["axis"]]
        paired = defaultdict(list)
        for rid, job in jobs.items():
            if job["kind"] != "action" or job["format"] != counter["format"]:
                continue
            row = job["row"]
            if row["view"] != counter["view"]:
                continue
            factors = (
                "scenario_id",
                "updated",
                "grant_variant",
                "identity",
                "view",
                "phase",
                "rotation",
            )
            paired[tuple(row[f] for f in factors if f != axis)].append(rid)
        require(all(len(pair) == 2 for pair in paired.values()), "Incomplete factorial pair")
        relevant = [
            (a, b)
            for a, b in paired.values()
            if jobs[a]["row"]["expected_command"] != jobs[b]["row"]["expected_command"]
        ]
        observed = [(a, b) for a, b in relevant if a in records and b in records]
        require(counter["expected_pairs"] == len(relevant), "Wrong expected counterfactual count")
        clusters = [jobs[a]["row"]["scenario_id"] for a, _ in observed]
        point = compare_estimate(
            counter, [outcomes[a] * outcomes[b] for a, b in observed], clusters
        )
        compare_estimate(
            counter["prediction_flip"],
            [
                int(
                    records[a]["status"] == records[b]["status"] == "ok"
                    and selections[a] != selections[b]
                )
                for a, b in observed
            ],
            clusters,
        )
        checks[counter["format"]]["pair:" + counter["axis"] + ":" + counter["view"]] = point
    numerical = {}
    for fmt, values in checks.items():
        require(len(values) == 24, "Expected 24 checks per format")
        require(values == saved["format_gates"][fmt]["checks"], "Gate checks mismatch")
        numerical[fmt] = all(v is not None and v >= 0.8 for v in values.values())
        require(numerical[fmt] == saved["format_gates"][fmt]["numerical_pass"], "Wrong format gate")
    format_pairs = defaultdict(dict)
    for rid, job in jobs.items():
        if job["kind"] == "action":
            format_pairs[job["row"]["id"]][job["format"]] = rid
    both_formats = [(p["plain"], p["chat"]) for p in format_pairs.values()]
    paired_complete = all(a in records and b in records for a, b in both_formats)
    require(
        saved["action_format_effect"]["complete_pairs"] == paired_complete, "Missing format pair"
    )
    compare_estimate(
        saved["action_format_effect"],
        [outcomes[b] - outcomes[a] for a, b in both_formats] if paired_complete else [],
        [jobs[a]["row"]["scenario_id"] for a, _ in both_formats] if paired_complete else [],
    )
    same_source = saved["analysis_source_hash"] == manifest["provenance"]["source_hash"]
    require(same_source == saved["same_source_as_execution"], "Wrong analysis source claim")
    require(saved["synthetic"] == manifest["synthetic"], "Wrong model-evidence claim")
    gate = (
        complete
        and manifest["status"] in {"complete", "complete_with_errors"}
        and not manifest["synthetic"]
        and same_source
        and all(numerical.values())
    )
    require(gate == saved["action_gate_passed"], "Wrong overall gate")
    # Added after inspecting the first real run: descriptive classification only.
    # These counts do not enter the frozen screen or create a new inferential test.
    error_types = defaultdict(Counter)
    for rid, accepted in outcomes.items():
        job, row = jobs[rid], jobs[rid]["row"]
        if accepted or row["phase"] != "after" or not row["relevant_update"]:
            continue
        selected = selections[rid]
        other = next(actor for actor in row["state"]["permissions"] if actor != row["target"])
        if records[rid]["status"] != "ok":
            label = "invalid_or_error"
        elif selected == row["before"]["permissions"][row["target"]][0]:
            label = "revoked_target_command"
        elif selected in row["state"]["permissions"][other]:
            label = "other_actor_command"
        else:
            label = "other_command"
        error_types[job["format"] + "/" + row["view"]][label] += 1
    return {
        "archive_sha256": actual,
        "verified_file_checksums": checked,
        "source_commit": manifest["provenance"]["git_commit"],
        "source_snapshot_hash": digest(source),
        "status": manifest["status"],
        "synthetic": manifest["synthetic"],
        "completed_outputs": len(records),
        "expected_outputs": len(jobs),
        "recomputed_action_choices": len(outcomes),
        "recomputed_action_strata": len(groups),
        "recomputed_counterfactual_strata": len(saved["counterfactuals"]),
        "format_numerical_pass": numerical,
        "action_gate_passed": gate,
        "post_hoc_relevant_update_errors": {
            key: dict(sorted(counts.items())) for key, counts in sorted(error_types.items())
        },
        **(
            {"human_ratings": audit_ratings(files, jobs, records, saved["human_ratings"])}
            if "run/human_ratings.csv" in files
            else {}
        ),
        "note": "Reaggregation of saved scores and independent simulator state reconstruction. "
        "No new inference, independent likelihood/interval verification, or construct validation.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--sha256", help="Optional trusted whole-archive digest")
    args = parser.parse_args()
    print(json.dumps(audit(args.archive, args.sha256), indent=2))
