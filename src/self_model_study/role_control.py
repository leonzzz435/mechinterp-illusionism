"""Frozen active-role / reference-label control, separate from capability confirmation."""

from copy import deepcopy
from itertools import product
from pathlib import Path

from .action_task import VERSION as ACTION_VERSION
from .action_task import build_design, score_command
from .data import rng_for
from .io import canonical, digest, read_json, write_json
from .pilot import audit_records, jobs_in, run_plan, scientific_spec
from .pilot import tokenizer_audit as audit_tokenizer
from .pilot_backend import create_backend
from .storage import read_records

PROTOCOL = "qwen-role-framing-v1"
ENGINE = "qwen-role-control"
FRAMES = ("active", "reference")
RELATIONS = ("target", "other")
CONDITIONS = tuple(product(FRAMES, RELATIONS))
DEFAULT_SPEC = {
    "protocol": PROTOCOL,
    "engine": ENGINE,
    "harness_version": "0.4.13",
    "model": {
        "repo": "Qwen/Qwen2.5-7B-Instruct",
        "revision": "a09a35458c702b33eeacc393d103063234e8bc28",
        "dtype": "bfloat16",
        "max_length": 2048,
    },
    "action_version": ACTION_VERSION,
    "dataset_seed": 1729,
    "scenarios": list(range(8, 16)),
    "formats": ["chat"],
    "context_lines": {
        "active": "Your active connection: {actor}.",
        "reference": "Reference connection: {actor}.",
    },
    "generation": {},
    "batch_size": 1,
    "num_fewshot": 0,
    "score": "sum_log_likelihood",
    "bootstrap_samples": 10000,
    "analysis_seed": 1729,
    "decision": {
        "primary_stratum": "after_relevant",
        "minimum_active_gap": 0.10,
        "minimum_interaction": 0.10,
        "minimum_positive_scenarios": 6,
        "control_accuracy": 0.80,
        "primary_two_sided_alpha": 0.05,
    },
    "max_seconds": 5400,
}
# Checked CPU design, frozen before any model inference.
FROZEN_PLAN_HASH = "ee4dfa480160113843b530897828e6b94009b00f8e1590a7d38975e4bacc4a76"


def validate_spec(spec):
    if set(spec) != set(DEFAULT_SPEC):
        raise ValueError("Unknown or incomplete role-control configuration")
    for key, value in DEFAULT_SPEC.items():
        if key != "max_seconds" and canonical(spec[key]) != canonical(value):
            raise ValueError(f"Frozen role-control field changed: {key}; use a new protocol")
    if type(spec["max_seconds"]) is not int or not 0 < spec["max_seconds"] <= 5400:
        raise ValueError("Role-control invocation limit must be 1–5400 seconds")
    return spec


def stratum(row):
    if row["phase"] == "before":
        return "before"
    return "after_relevant" if row["relevant_update"] else "after_irrelevant"


def build_plan(spec):
    validate_spec(spec)
    # Select one named query per fixed scene; assignment is rebuilt as a factor.
    scenes = [
        r
        for r in build_design(seed=spec["dataset_seed"], scenarios=16)
        if r["view"] == "named_self"
        and int(r["scenario_id"].rsplit(":", 1)[1]) in spec["scenarios"]
    ]
    blocks = []
    for index in spec["scenarios"]:
        selected = [r for r in scenes if int(r["scenario_id"].rsplit(":", 1)[1]) == index]
        selected.sort(key=lambda r: r["id"])
        rng_for([PROTOCOL, index, "scene-order"]).shuffle(selected)
        condition_order = list(CONDITIONS)
        rng_for([PROTOCOL, index, "condition-order"]).shuffle(condition_order)
        jobs = []
        for offset, scene in enumerate(selected):
            # Four conditions remain adjacent but their execution order is counterbalanced.
            start = offset % 4
            conditions = condition_order[start:] + condition_order[:start]
            for frame, relation in conditions:
                row = deepcopy(scene)
                actor = (
                    row["target"]
                    if relation == "target"
                    else next(a for a in row["state"]["permissions"] if a != row["target"])
                )
                old = "Your active connection: " + scene["assigned"] + "."
                line = spec["context_lines"][frame].format(actor=actor)
                if row["prompt"].count(old) != 1:
                    raise ValueError("Expected one replaceable role line")
                row["prompt"] = row["prompt"].replace(old, line)
                # Original scene metadata cannot masquerade as an assignment in reference mode.
                for key in ("assigned", "identity", "view", "execution_mode", "language_prompt"):
                    row.pop(key)
                row.update(
                    scene_id=scene["id"],
                    frame=frame,
                    relation=relation,
                    mentioned_actor=actor,
                    target_identity=scene["identity"],
                    execution_mode="named_target_copy",
                )
                row["id"] = digest([PROTOCOL, scene["id"], frame, relation])
                jobs.append({"id": row["id"], "kind": "action", "format": "chat", "row": row})
        blocks.append({"id": f"role-control-{index:02d}", "jobs": jobs})
    plan = {"protocol": PROTOCOL, "split": "development", "blocks": blocks}
    if digest(plan) != FROZEN_PLAN_HASH:
        raise ValueError("Frozen role-control inputs changed; use a new protocol")
    return plan


def preview(spec):
    plan = build_plan(spec)
    jobs = jobs_in(plan)
    return {
        "protocol": PROTOCOL,
        "valid": True,
        "kind": "design_only",
        "model_inference": False,
        "action_choices": len(jobs),
        "independent_scenarios": len(plan["blocks"]),
        "scene_variants": len({j["row"]["scene_id"] for j in jobs}),
        "unique_model_inputs": len({j["row"]["prompt"] for j in jobs}),
        "conditions": [list(c) for c in CONDITIONS],
        "plan_hash": digest(plan),
        "config_hash": digest(scientific_spec(spec)),
        "simulator_oracle_accuracy": sum(
            score_command(j["row"], j["row"]["expected_command"])["correct"] for j in jobs
        )
        / len(jobs),
        "max_seconds": spec["max_seconds"],
        "note": "No model result. Repeated before-update inputs are paired design variants.",
    }


def tokenizer_audit(spec, tokenizer=None):
    return {**preview(spec), **audit_tokenizer(spec, tokenizer, plan=build_plan(spec))}


def prepare(spec, directory, tokenizer_check=False):
    """Export complete CPU inputs/oracles, with a manifest explicitly marked design-only."""
    directory = Path(directory)
    if directory.exists() and any(directory.iterdir()):
        raise ValueError("Choose a new or empty design directory")
    plan, summary = build_plan(spec), preview(spec)
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / "config.json", spec)
    write_json(directory / "plan.json", plan)
    write_json(
        directory / "model_inputs.json",
        [
            {"id": j["id"], "prompt": j["row"]["prompt"], "choices": j["row"]["choices"]}
            for j in jobs_in(plan)
        ],
    )
    write_json(directory / "manifest.json", {"engine": ENGINE, "status": "design_only", **summary})
    if tokenizer_check:
        write_json(directory / "tokenizer_audit.json", tokenizer_audit(spec))
    from .role_control_reporting import design_figure

    design_figure(directory / "figures/role_control_design")
    return summary


def run(spec, directory, max_jobs=None, backend_factory=create_backend, checkpoint=None):
    path = Path(directory) / "manifest.json"
    if path.exists() and read_json(path).get("status") == "design_only":
        raise ValueError("CPU design is not a model run; choose a separate run directory")
    return run_plan(
        validate_spec(spec), build_plan(spec), directory, max_jobs, backend_factory, checkpoint
    )


def read_run(directory):
    directory = Path(directory)
    manifest = read_json(directory / "manifest.json")
    if manifest.get("status") == "design_only":
        raise ValueError("CPU design is not a model run; choose a separate run directory")
    if manifest["protocol"] != PROTOCOL or manifest["engine"] != ENGINE:
        raise ValueError("Not a role-control run")
    spec = validate_spec(manifest["config"])
    plan = read_json(directory / "plan.json")
    if digest(plan) != manifest["plan_hash"] or digest(plan) != digest(build_plan(spec)):
        raise ValueError("Role-control plan differs from frozen inputs")
    if digest(scientific_spec(spec)) != manifest["config_hash"]:
        raise ValueError("Role-control config hash mismatch")
    if manifest["expected_jobs"] != len(jobs_in(plan)):
        raise ValueError("Role-control expected coverage changed")
    records = read_records(directory)
    audit_records(records, plan, manifest)
    return manifest, plan, records
