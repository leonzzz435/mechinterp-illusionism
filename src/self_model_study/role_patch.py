"""Frozen, single-site role-framing activation exchange on eight known scenarios."""

import json
import tarfile
from collections import Counter
from copy import deepcopy
from pathlib import Path

import numpy as np

from . import role_control
from .io import canonical, digest, file_hash, read_json, write_json
from .pilot import audit_records, jobs_in, run_plan, scientific_spec
from .pilot_backend import encode_boundary, render_prompt
from .storage import read_records

ENGINE = "qwen-role-patch"
PROTOCOL = "qwen-role-patch-v1"
ARMS = ("baseline", "self", "swap", *(f"random_{k:02d}" for k in range(10)))
REFERENCE_ARCHIVE = "qwen-role-96787d5e7adf4c4d.tar.gz"
REFERENCE_SHA = "36614cb2aae236d450d57540c9b76dfddfec2d4bd2a59f177dce296058b13a8d"
REFERENCE_HASH = "73542d2b8fd37d2dc3417c9385b6c721df024ca721e8cf7c73d7636eaef122ba"
FROZEN_PLAN_HASH = "1fad9f0be13b103aca75a2d1eb6f3209ba15efa6c1bb994b0fe1ec812de48600"
DIRECTIONS_HASH = "207b3180aba68700b25750c17db86699dfb812ab4091a1063d97626966083966"
DEFAULT_SPEC = {
    **deepcopy(role_control.DEFAULT_SPEC),
    "engine": ENGINE,
    "protocol": PROTOCOL,
    "patch": {
        "layer": 13,
        "width": 3584,
        "role_end_token": 624,
        "random_seed": 1729,
        "random_directions": 10,
        "random_norm_tolerance": 0.05,
        "baseline_score_tolerance": 0.001,
        "null_score_tolerance": 0.000001,
        "logits_cache": False,
        "use_cache": False,
        "baseline_archive_sha256": REFERENCE_SHA,
    },
    "decision": {
        "primary_stratum": "after_relevant",
        "minimum_transfer": 0.05,
        "minimum_positive_scenarios": 6,
        "control_accuracy": 0.80,
        "control_change_lower_bound": -0.05,
        "primary_two_sided_alpha": 0.05,
    },
}


def validate_spec(spec):
    if set(spec) != set(DEFAULT_SPEC):
        raise ValueError("Unknown or incomplete role-patch configuration")
    for key, value in DEFAULT_SPEC.items():
        if key != "max_seconds" and canonical(spec[key]) != canonical(value):
            raise ValueError(f"Frozen role-patch field changed: {key}; use a new protocol")
    if type(spec["max_seconds"]) is not int or not 0 < spec["max_seconds"] <= 5400:
        raise ValueError("Role-patch invocation limit must be 1–5400 seconds")
    return spec


def trial_id(base_id, arm):
    return digest([PROTOCOL, base_id, arm])


def build_plan(spec):
    validate_spec(spec)
    base = role_control.build_plan(role_control.DEFAULT_SPEC)
    blocks = []
    for block in base["blocks"]:
        baseline = block["jobs"]
        by_condition = {
            (j["row"]["scene_id"], j["row"]["frame"], j["row"]["relation"]): j for j in baseline
        }
        jobs = []
        for arm in ARMS:
            for job in baseline:
                row = job["row"]
                if arm.startswith("random") and role_control.stratum(row) != "after_relevant":
                    continue
                donor = by_condition[
                    (
                        row["scene_id"],
                        "active" if row["frame"] == "reference" else "reference",
                        row["relation"],
                    )
                ]
                jobs.append(
                    {
                        **deepcopy(job),
                        "id": trial_id(job["id"], arm),
                        "arm": arm,
                        "base_id": job["id"],
                        "donor_base_id": donor["id"],
                        "technical": False,
                    }
                )
        # First scene in the already frozen order, all four frames/relations.
        for job in baseline[:4]:
            jobs.append(
                {
                    **deepcopy(job),
                    "id": trial_id(job["id"], "repeat"),
                    "arm": "repeat",
                    "base_id": job["id"],
                    "donor_base_id": None,
                    "technical": True,
                }
            )
        blocks.append({"id": block["id"].replace("control", "patch"), "jobs": jobs})
    plan = {
        "protocol": PROTOCOL,
        "split": "development",
        "exploratory_known_scenarios": True,
        "base_plan_hash": digest(base),
        "blocks": blocks,
    }
    if FROZEN_PLAN_HASH and digest(plan) != FROZEN_PLAN_HASH:
        raise ValueError("Frozen patch plan changed; use a new protocol")
    return plan


def random_directions():
    values = np.random.default_rng(1729).normal(size=(10, 3584))
    values /= np.linalg.norm(values, axis=1, keepdims=True)
    result = {
        "seed": 1729,
        "distribution": "PCG64 standard normal, unit L2, float32",
        "vectors": values.astype("float32").tolist(),
    }
    if DIRECTIONS_HASH and digest(result) != DIRECTIONS_HASH:
        raise ValueError("Frozen random directions changed")
    return result


def historical_reference():
    path = Path(__file__).resolve().parents[2] / "review/evidence" / REFERENCE_ARCHIVE
    if file_hash(path) != REFERENCE_SHA:
        raise ValueError("Historical baseline archive checksum mismatch")
    with tarfile.open(path, "r:gz") as tar:
        raw = tar.extractfile("run/records.jsonl").read().decode()
        records = [json.loads(line) for line in raw.splitlines()]
    result = {
        "archive": REFERENCE_ARCHIVE,
        "archive_sha256": REFERENCE_SHA,
        "records": {
            r["id"]: {
                "checksum": r["checksum"],
                "result": r["result"],
            }
            for r in records
        },
    }
    if REFERENCE_HASH and digest(result) != REFERENCE_HASH:
        raise ValueError("Frozen baseline reference changed")
    return result


def role_position(tokenizer, rendered, context_ids):
    """Align the semantic role-line endpoint, never the last teacher-forced token."""
    marker = "\nInitial permissions:"
    if rendered.count(marker) != 1:
        raise ValueError("Expected exactly one role/permissions boundary")
    prefix = rendered.split(marker)[0] + "\n"
    ids = tokenizer.encode(prefix, add_special_tokens=False)
    if context_ids[: len(ids)] != ids or ids[-1] != 624:
        raise ValueError("Role boundary is not the frozen .\\n token (624)")
    if tokenizer.decode([ids[-1]]) != ".\n":
        raise ValueError("Role endpoint decoding changed")
    return len(ids) - 1


def preview(spec):
    plan = build_plan(spec)
    counts = Counter(j["arm"] for j in jobs_in(plan))
    return {
        "protocol": PROTOCOL,
        "valid": True,
        "kind": "design_only",
        "model_inference": False,
        "action_choices": sum(counts[a] for a in ARMS),
        "technical_repeats": counts["repeat"],
        "arm_counts": dict(counts),
        "independent_scenarios": 8,
        "plan_hash": digest(plan),
        "config_hash": digest(scientific_spec(spec)),
        "directions_hash": digest(random_directions()),
        "baseline_reference_hash": REFERENCE_HASH,
        "max_seconds": spec["max_seconds"],
    }


def tokenizer_audit(spec, tokenizer=None):
    if tokenizer is None:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(
            spec["model"]["repo"],
            revision=spec["model"]["revision"],
            trust_remote_code=False,
        )
    positions, maximum, candidates = set(), 0, 0
    historical = historical_reference()["records"]
    for block in build_plan(spec)["blocks"]:
        for job in block["jobs"]:
            if job["arm"] != "baseline":
                continue
            rendered = render_prompt(tokenizer, job["row"]["prompt"], "chat")
            saved = historical[job["base_id"]]["result"]
            if rendered != saved["rendered_prompt"]:
                raise ValueError("Rendered baseline differs from historical evidence")
            for i, command in enumerate(job["row"]["choices"]):
                ctx, cont = encode_boundary(tokenizer, rendered, command, 2048)
                if ctx != saved["prompt_token_ids"] or cont != saved["candidates"][i]["token_ids"]:
                    raise ValueError("Historical baseline token transition changed")
                positions.add(role_position(tokenizer, rendered, ctx))
                maximum = max(maximum, len(ctx) + len(cont))
                candidates += 1
    return {
        **preview(spec),
        "tokenizer_checked": True,
        "candidate_boundaries": candidates,
        "role_positions": sorted(positions),
        "role_end_token": 624,
        "max_context_including_answer": maximum,
        "tokenizer_revision": spec["model"]["revision"],
        "chat_template": tokenizer.chat_template,
        "tokenizer_vocabulary_hash": digest(tokenizer.get_vocab()),
    }


def prepare(spec, directory, tokenizer_check=False):
    directory = Path(directory)
    if directory.exists() and any(directory.iterdir()):
        raise ValueError("Choose a new or empty design directory")
    plan, summary = build_plan(spec), preview(spec)
    write_json(directory / "config.json", spec)
    write_json(directory / "plan.json", plan)
    write_json(directory / "random_directions.json", random_directions())
    write_json(directory / "baseline_reference.json", historical_reference())
    write_json(directory / "manifest.json", {"engine": ENGINE, "status": "design_only", **summary})
    if tokenizer_check:
        write_json(directory / "tokenizer_audit.json", tokenizer_audit(spec))
    from .role_patch_reporting import design_figure

    design_figure(directory / "figures/role_patch_design")
    return summary


def run(spec, directory, max_jobs=None, backend_factory=None, checkpoint=None):
    from .role_patch_audit import initialize_and_audit
    from .role_patch_backend import PatchExecutor, create_backend

    directory = Path(directory)
    if (directory / "manifest.json").exists():
        if read_json(directory / "manifest.json")["status"] == "design_only":
            raise ValueError("CPU design is not a model run; choose a separate directory")
    validate_spec(spec)
    executor = PatchExecutor(directory, spec)
    return run_plan(
        spec,
        build_plan(spec),
        directory,
        max_jobs,
        backend_factory or create_backend,
        checkpoint,
        trial_executor=executor,
        artifact_audit=initialize_and_audit,
    )


def read_run(directory):
    from .role_patch_audit import audit_artifacts

    directory = Path(directory)
    manifest = read_json(directory / "manifest.json")
    if manifest.get("status") == "design_only":
        raise ValueError("CPU design is not a model run")
    if manifest["engine"] != ENGINE or manifest["protocol"] != PROTOCOL:
        raise ValueError("Not a role-patch run")
    spec = validate_spec(manifest["config"])
    plan = read_json(directory / "plan.json")
    if digest(plan) != manifest["plan_hash"] or digest(plan) != digest(build_plan(spec)):
        raise ValueError("Patch plan differs from frozen inputs")
    if digest(scientific_spec(spec)) != manifest["config_hash"]:
        raise ValueError("Patch configuration hash mismatch")
    if manifest["expected_jobs"] != len(jobs_in(plan)):
        raise ValueError("Patch expected coverage changed")
    records = read_records(directory)
    audit_records(records, plan, manifest)
    audit_artifacts(directory, manifest, records)
    return manifest, plan, records
