"""Strict, versioned JSON configuration shared by CPU and GPU workflows."""

from copy import deepcopy
from pathlib import Path

from .io import read_json

DEFAULTS = {
    "schema_version": 1,
    "backend": "torch",
    "phase": "baseline",
    "split": "validation",
    "seed": 42,
    "model": {
        "repo": "unsloth/gemma-2-2b",
        "revision": "main",
        "device": "cuda",
        "dtype": "bfloat16",
        "processing": "none",
    },
    "sae": {
        "repo": "google/gemma-scope-2b-pt-res",
        "revision": "main",
        "path": "layer_14/width_16k/average_l0_84",
        "hook": "blocks.14.hook_resid_post",
        "features": [2728, 10230],
    },
    "dataset": {
        "version": "context-self-v1",
        "seed": 1729,
        "counts": {"development": 40, "validation": 40, "test": 100},
        "families": ["ownership", "access", "capability"],
        "include_language": True,
    },
    "interventions": {
        "directions": ["dense", "feature:2728", "feature:10230"],
        "strengths": [-0.10, -0.05, -0.02, 0.02, 0.05, 0.10],
        "random_count": 10,
        "ablate": [],
        "combine": False,
    },
    "generation": {
        "max_new_tokens": 55,
        "seeds": [42, 43, 44],
        "temperature": 0.7,
        "frequency_penalty": 1.2,
        "position": "all_positions_each_step",
    },
    "calibration": {
        "prompts_per_family": 12,
        "min_explained_variance": 0.5,
        "min_loss_recovered": 0.5,
        "max_hf_logit_abs_error": 0.5,
    },
    "statistics": {
        "bootstrap_samples": 20000,
        "alpha": 0.05,
        "equivalence_margin": 0.05,
        "baseline_min_accuracy": 0.8,
    },
    "max_seconds": 28800,
    "max_jobs": None,
    "protocol": None,
    "evidence_run": None,
}


def merge(base, update, path=""):
    if not isinstance(update, dict):
        raise ValueError("Configuration must be a JSON object")
    for key, value in update.items():
        if key not in base:
            raise ValueError(f"Unknown configuration key: {path}{key}")
        if isinstance(base[key], dict):
            if not isinstance(value, dict):
                raise ValueError(f"Expected object: {path}{key}")
            merge(base[key], value, f"{path}{key}.")
        else:
            base[key] = value
    return base


def load_config(path):
    return validate_config(merge(deepcopy(DEFAULTS), read_json(Path(path))))


def validate_config(c):
    def check(ok, message):
        if not ok:
            raise ValueError(message)

    def types(value, default, path=""):
        if isinstance(default, dict):
            check(isinstance(value, dict), f"Expected object: {path}")
            for key in default:
                check(key in value, f"Missing field: {path}{key}")
                types(value[key], default[key], f"{path}{key}.")
        elif default is not None:
            expected = (int, float) if type(default) is float else (type(default),)
            check(type(value) in expected, f"Wrong type for {path.rstrip('.')}")

    types(c, DEFAULTS)

    check(c["schema_version"] == 1, "Unsupported schema version")
    check(c["backend"] in {"torch", "mock"}, "backend must be torch or mock")
    check(
        c["phase"] in {"reference", "baseline", "exploratory", "confirmatory", "combined"},
        "Unknown phase",
    )
    check(c["split"] in {"development", "validation", "test"}, "Unknown split")
    check(c["phase"] != "confirmatory" or c["split"] == "test", "Confirmation uses test only")
    check(c["split"] != "test" or c["phase"] == "confirmatory", "Test is confirmation-only")
    check(
        c["phase"] != "reference" or c["split"] == "development",
        "Historical reference uses development only",
    )
    check(c["model"]["processing"] in {"none", "historical"}, "Unknown model processing")
    check(
        c["model"]["processing"] != "historical" or c["phase"] == "reference",
        "Processed historical weights are reference-only",
    )
    check(c["model"]["dtype"] in {"float32", "bfloat16"}, "Unsupported dtype")
    check(c["model"]["device"] in {"cpu", "cuda"}, "Explicit cpu or cuda device required")
    check(c["dataset"]["version"] == "context-self-v1", "Unsupported dataset version")
    check(set(c["dataset"]["counts"]) == {"development", "validation", "test"}, "Invalid counts")
    check(
        all(type(n) is int and n > 0 for n in c["dataset"]["counts"].values()),
        "Counts must be positive integers",
    )
    families = c["dataset"]["families"]
    check(
        bool(families)
        and len(families) == len(set(families))
        and set(families) <= {"ownership", "access", "capability"},
        "Invalid families",
    )
    check(0 < c["max_seconds"] <= 28800, "Each invocation must be limited to 1–28800 seconds")
    check(
        c["max_jobs"] is None or (type(c["max_jobs"]) is int and c["max_jobs"] > 0),
        "max_jobs must be null or a positive integer",
    )
    check(c["generation"]["position"] == "all_positions_each_step", "Unknown generation hook")
    check(0 < c["generation"]["max_new_tokens"] <= 256, "Generation limit must be 1–256")
    check(c["generation"]["temperature"] > 0, "Temperature must be positive")
    check(
        bool(c["generation"]["seeds"])
        and len(set(c["generation"]["seeds"])) == len(c["generation"]["seeds"]),
        "Generation seeds must be nonempty and unique",
    )
    iv = c["interventions"]
    check(all(type(x) is str for x in iv["directions"]), "Direction names must be strings")
    check(all(type(x) in (int, float) for x in iv["strengths"]), "Strengths must be numeric")
    check(
        type(iv["random_count"]) is int and 0 <= iv["random_count"] <= 10,
        "random_count must be between 0 and 10",
    )
    check(len(iv["directions"]) == len(set(iv["directions"])), "Duplicate directions")
    check(
        len(iv["strengths"]) == len(set(iv["strengths"]))
        and set(iv["strengths"]) <= {-0.1, -0.05, -0.02, 0.02, 0.05, 0.1},
        "Pilot strengths must be unique values from ±0.02, ±0.05, ±0.10",
    )
    allowed = {"dense"} | {f"feature:{i}" for i in c["sae"]["features"]}
    check(set(iv["directions"]) <= allowed, "Unknown direction or feature")
    check(set(iv["ablate"]) <= set(c["sae"]["features"]), "Unknown ablation feature")
    check(len(iv["ablate"]) == len(set(iv["ablate"])), "Duplicate ablation features")
    check(not iv["combine"] or c["phase"] == "combined", "Combinations require combined phase")
    check(
        c["phase"] != "combined" or c["evidence_run"], "Combination needs single-feature evidence"
    )
    check(0 < c["statistics"]["alpha"] < 0.5, "Invalid alpha")
    check(c["statistics"]["bootstrap_samples"] >= 1000, "At least 1000 bootstrap samples")
    check(c["statistics"]["equivalence_margin"] == 0.05, "Pilot equivalence margin is fixed at .05")
    check(c["statistics"]["baseline_min_accuracy"] == 0.8, "Pilot baseline gate is fixed at .8")
    check(
        c["calibration"]["prompts_per_family"] >= 2, "At least two calibration prompts per family"
    )
    check(c["sae"]["hook"] == "blocks.14.hook_resid_post", "Pilot is restricted to layer 14")
    check(c["sae"]["features"] == [2728, 10230], "Pilot candidates are 2728 and 10230")
    return c
