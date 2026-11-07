"""Independent, standard-library audit of the completed activation-exchange archive.

Reconstructs outcomes, donor matching, parity, scenario estimands and exact sign flips.
Does not rerun model inference, independently compute likelihoods or bootstrap intervals,
or inspect tensor values; the separate post-run verification covers saved BF16 tensors.
"""

import hashlib
import json
import math
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path, PurePosixPath

from review_qwen_evidence import archive_files, compare_estimate, digest, require
from review_role_evidence import outcome, stage

ARCHIVE = Path("review/evidence/qwen-patch-3bd8fc27cbb147c9.tar.gz")
SHA256 = "017e6e0f78e6ae793fbdb5a7ca3a2e4055750c840cc2da2553819fafb0304207"
PLAN_HASH = "1fad9f0be13b103aca75a2d1eb6f3209ba15efa6c1bb994b0fe1ec812de48600"
CONFIG_HASH = "67e37d0b18ce54dc7d2bde6119e8be0ccc33cfd8a4b624515dd0e45ee9de2996"
RANDOM = [f"random_{i:02d}" for i in range(10)]
ARMS = ["baseline", "self", "swap", *RANDOM]


def mean(values):
    return sum(values) / len(values)


def check_stat(saved, values):
    compare_estimate(saved, list(values.values()), list(values))
    require(saved["scenario_means"] == values, "Scenario values mismatch")
    require(
        saved["positive_scenarios"] == sum(v > 0 for v in values.values()),
        "Positive scenario count mismatch",
    )
    observed = abs(sum(values.values()))
    p = sum(
        abs(sum(s * v for s, v in zip(signs, values.values()))) >= observed - 1e-12
        for signs in product((-1, 1), repeat=len(values))
    ) / 2 ** len(values)
    require(saved["two_sided_sign_flip_p"] == p, "Sign-flip p mismatch")


def parity(result, reference, tolerance):
    require(result["selected_command"] == reference["selected_command"], "Parity choice mismatch")
    require(result["prompt_token_ids"] == reference["prompt_token_ids"], "Parity tokens mismatch")
    for candidate, other in zip(result["candidates"], reference["candidates"]):
        require(
            candidate["command"] == other["command"]
            and candidate["token_ids"] == other["token_ids"],
            "Parity candidate mismatch",
        )
        require(
            abs(candidate["log_likelihood"] - other["log_likelihood"]) <= tolerance,
            "Parity score mismatch",
        )


def audit(path=ARCHIVE, sha256=SHA256):
    files, actual, checked = archive_files(path, sha256)
    manifest, plan, saved, historical = (
        json.loads(files[f"run/{name}.json"])
        for name in ("manifest", "plan", "analysis", "baseline_reference")
    )
    raw = [json.loads(line) for line in files["run/records.jsonl"].splitlines()]
    require(manifest["plan_hash"] == digest(plan) == PLAN_HASH, "Frozen plan mismatch")
    require(
        manifest["config_hash"]
        == CONFIG_HASH
        == digest({k: v for k, v in manifest["config"].items() if k != "max_seconds"}),
        "Frozen config mismatch",
    )
    require(
        manifest["status"] == saved["status"] == "complete"
        and not manifest["synthetic"]
        and not saved["synthetic"],
        "Not complete real data",
    )
    source = {
        PurePosixPath(n).name: hashlib.sha256(b).hexdigest()
        for n, b in files.items()
        if n.startswith("run/source/self_model_study/")
    }
    require(digest(source) == manifest["provenance"]["source_hash"], "Source snapshot mismatch")
    ordered = [j for b in plan["blocks"] for j in b["jobs"]]
    jobs = {j["id"]: j for j in ordered}
    records = {r["id"]: r for r in raw}
    require(
        len(raw) == len(records) == len(jobs) == len(ordered) == 11296,
        "Incomplete or duplicate records",
    )
    require(records.keys() == jobs.keys() == manifest["records"].keys(), "Coverage mismatch")
    require(
        Counter(r["job"]["arm"] for r in raw)
        == {
            "baseline": 2048,
            "self": 2048,
            "swap": 2048,
            "repeat": 32,
            **{a: 512 for a in RANDOM},
        },
        "Arm coverage mismatch",
    )
    base = {r["job"]["base_id"]: r for r in raw if r["job"]["arm"] == "baseline"}
    grouped, primary = defaultdict(list), defaultdict(list)
    checks = 0
    for record in raw:
        rid, job, result = record["id"], record["job"], record["result"]
        row, arm = job["row"], job["arm"]
        require(job == jobs[rid] and record["config_hash"] == CONFIG_HASH, "Job mismatch")
        require(
            digest({k: v for k, v in record.items() if k != "checksum"})
            == record["checksum"]
            == manifest["records"][rid],
            "Record checksum mismatch",
        )
        require(record["status"] == result["status"] == "ok", "Measurement error")
        correct = outcome(row, result)
        require(
            not result["technical_failure"]
            and all(c["passed"] for c in result["technical_checks"]),
            "Technical failure",
        )
        checks += len(result["technical_checks"])
        own = base[job["base_id"]]["result"]
        require(
            result["rendered_prompt"] == own["rendered_prompt"]
            and result["prompt_token_ids"] == own["prompt_token_ids"],
            "Recipient changed",
        )
        donor = base[job["donor_base_id"] or job["base_id"]]
        drow = donor["job"]["row"]
        require(
            arm == "repeat"
            or (
                drow["frame"] != row["frame"]
                and drow["mentioned_actor"] == row["mentioned_actor"]
                and drow["scene_id"] == row["scene_id"]
                and drow["choices"] == row["choices"]
            ),
            "Mismatched donor scene/actor/candidate",
        )
        if arm == "baseline":
            ref = result["activation_file"]
            require(
                ref["path"] == f"activations/{job['base_id']}.safetensors"
                and hashlib.sha256(files["run/" + ref["path"]]).hexdigest() == ref["sha256"],
                "Activation digest mismatch",
            )
            parity(result, historical["records"][job["base_id"]]["result"], 0.001)
        elif arm in {"self", "repeat"}:
            parity(result, own, 1e-6)
        for i, candidate in enumerate(result["candidates"]):
            m = candidate["patch"]
            require(
                m["layer"] == 13
                and m["width"] == 3584
                and m["mode"] == arm
                and result["prompt_token_ids"][m["position"]] == 624,
                "Wrong patch site",
            )
            require(
                candidate["forward_input_hash"]
                == digest((result["prompt_token_ids"] + candidate["token_ids"])[:-1]),
                "Forward input mismatch",
            )
            if arm in {"baseline", "repeat"}:
                continue
            source_result = own if arm == "self" else donor["result"]
            require(
                m["recipient"] == {**own["activation_file"], "key": f"candidate_{i}"}
                and m["donor"] == {**source_result["activation_file"], "key": f"candidate_{i}"},
                "Wrong donor reference",
            )
            require(
                candidate["command"] == source_result["candidates"][i]["command"],
                "Wrong donor command",
            )
            require(m["prepatch_max_abs_difference"] <= 1e-6, "Prepatch state changed")
            if arm == "self":
                require(m["desired_norm"] == m["actual_norm"] == 0, "Nonzero self edit")
            elif arm in RANDOM:
                require(
                    m["random_index"] == RANDOM.index(arm)
                    and m["random_sign"] == (1 if row["frame"] == "active" else -1),
                    "Wrong random direction/sign",
                )
                error = abs(m["actual_norm"] - m["desired_norm"]) / m["desired_norm"]
                require(
                    math.isclose(error, m["relative_norm_error"], abs_tol=1e-12) and error <= 0.05,
                    "Random norm mismatch",
                )
        if arm == "repeat":
            continue
        sid, checkpoint = row["scenario_id"], stage(row)
        for axis, value in {
            "cell": f"{row['frame']}/{row['relation']}/{checkpoint}",
            "identity": str(row["target_identity"]),
            "position": str(row["expected_position"]),
            "command": row["expected_command"],
        }.items():
            grouped[arm, axis, value].append((sid, correct))
        if checkpoint == "after_relevant":
            primary[arm, sid, row["frame"], row["relation"]].append(correct)
    require(checks == saved["technical_check_count"] == 61472, "Technical coverage mismatch")
    require(
        saved["technical_failures"] == saved["errors"] == 0
        and saved["coverage_complete"]
        and saved["scientific_completed"] == 11264
        and saved["technical_repeats_completed"] == 32,
        "False completion claim",
    )
    require(len(grouped) == len(saved["groups"]), "Group coverage mismatch")
    for group in saved["groups"]:
        entries = grouped[group["arm"], group["axis"], group["value"]]
        require(group["observed"] == group["expected"] == len(entries), "Group coverage mismatch")
        compare_estimate(group, [v for _, v in entries], [s for s, _ in entries])
    scenarios = sorted({r["job"]["row"]["scenario_id"] for r in raw})
    require(
        len(scenarios) == 8 and all(len(v) == 16 for v in primary.values()),
        "Scenario balance mismatch",
    )
    transfers = {}
    for arm in ARMS:
        values = {k: {} for k in ("reference_to_active", "active_to_reference", "total")}
        for sid in scenarios:
            gaps = {
                (a, f): mean(primary[a, sid, f, "other"]) - mean(primary[a, sid, f, "target"])
                for a in {"self", arm}
                for f in ("active", "reference")
            }
            forward = gaps["self", "active"] - gaps[arm, "active"]
            reverse = gaps[arm, "reference"] - gaps["self", "reference"]
            for k, v in zip(values, (forward, reverse, (forward + reverse) / 2)):
                values[k][sid] = v
        for key, v in values.items():
            check_stat(saved["transfer"][arm][key], v)
        transfers[arm] = values["total"]
    contrast = {
        s: transfers["swap"][s] - mean([transfers[a][s] for a in RANDOM]) for s in scenarios
    }
    check_stat(saved["primary_contrast"], contrast)
    controls = [
        g
        for g in saved["groups"]
        if g["arm"] == "swap" and g["axis"] == "cell" and not g["value"].endswith("after_relevant")
    ]
    require(saved["control_cells"] == controls and len(controls) == 8, "Control coverage mismatch")
    require(
        saved["controls_passed"] == all(g["estimate"] >= 0.8 for g in controls),
        "Control decision mismatch",
    )
    paired = [
        outcome(r["job"]["row"], r["result"])
        - outcome(r["job"]["row"], base[r["job"]["base_id"]]["result"])
        for r in raw
        if r["job"]["arm"] == "swap" and stage(r["job"]["row"]) != "after_relevant"
    ]
    require(saved["control_change"]["estimate"] == mean(paired), "Control change mismatch")
    # Bootstrap bounds are checked by exact reproduction with the frozen package separately.
    t, c = saved["transfer"]["swap"], saved["primary_contrast"]
    passed = (
        t["total"]["estimate"] >= 0.05
        and t["total"]["ci95"][0] > 0
        and t["reference_to_active"]["estimate"] > 0
        and t["active_to_reference"]["estimate"] > 0
        and c["ci95"][0] > 0
        and c["two_sided_sign_flip_p"] <= 0.05
        and c["positive_scenarios"] >= 6
    )
    decision = (
        "stop_control_failure"
        if not saved["controls_passed"] or saved["control_change"]["ci95"][0] <= -0.05
        else "bidirectional_transfer_candidate"
        if passed
        else "no_bidirectional_transfer_candidate"
    )
    require(saved["decision"] == decision, "Decision mismatch")
    return {
        "archive_sha256": actual,
        "verified_file_checksums": checked,
        "verified_records": len(raw),
        "scientific_records": 11264,
        "verified_candidate_inputs": 4 * len(raw),
        "verified_technical_checks": checks,
        "verified_accuracy_groups": len(grouped),
        "independent_scenarios": len(scenarios),
        "source_hash": digest(source),
        "transfer": t,
        "primary_contrast": c,
        "control_change": saved["control_change"],
        "controls_passed": saved["controls_passed"],
        "decision": decision,
        "limitations": "Saved-output audit, not independent inference, likelihood calculation, "
        "bootstrap implementation, tensor arithmetic or construct validation.",
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
