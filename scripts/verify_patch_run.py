"""Read-only CPU verification of the pinned cloud archive; never runs model inference.

Requires the project's eval extras and the pinned tokenizer in the local HF cache.
Uses a temporary extraction after validating all archive paths and checksums.
"""

import json
import math
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

import torch
from review_patch_evidence import ARCHIVE, SHA256
from review_qwen_evidence import archive_files, require
from safetensors.torch import load_file
from transformers import AutoTokenizer

from self_model_study.role_patch import read_run
from self_model_study.role_patch_analysis import summarize


def verify():
    files, _, count = archive_files(ARCHIVE, SHA256)
    with TemporaryDirectory(prefix="patch-verification-") as tmp:
        for name, data in files.items():
            dest = Path(tmp) / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        directory = Path(tmp) / "run"
        manifest, plan, records = read_run(directory)
        require(
            summarize(manifest, plan, records) == json.loads(files["run/analysis.json"]),
            "Frozen analysis does not reproduce exactly",
        )
        with sqlite3.connect(f"file:{directory}/trials.sqlite?mode=ro", uri=True) as con:
            journal = con.execute("SELECT id,status,payload FROM trials ORDER BY id").fetchall()
        require(
            [(r["id"], r["status"], r) for r in sorted(records, key=lambda r: r["id"])]
            == [(rid, status, json.loads(payload)) for rid, status, payload in journal],
            "SQLite differs from JSONL",
        )
        spec = manifest["config"]
        tokenizer = AutoTokenizer.from_pretrained(
            spec["model"]["repo"], revision=spec["model"]["revision"], local_files_only=True
        )
        baseline = [r for r in records if r["job"]["arm"] == "baseline"]
        tensors = {}
        max_length = 0
        for record in baseline:
            row, result = record["job"]["row"], record["result"]
            rendered = tokenizer.apply_chat_template(
                [{"role": "user", "content": row["prompt"]}],
                tokenize=False,
                add_generation_prompt=True,
            )
            context = tokenizer.encode(rendered, add_special_tokens=False)
            require(
                rendered == result["rendered_prompt"] and context == result["prompt_token_ids"],
                "Rendered prompt/token mismatch",
            )
            line = spec["context_lines"][row["frame"]].format(actor=row["mentioned_actor"]) + "\n"
            end = rendered.index(line) + len(line)
            prefix = tokenizer.encode(rendered[:end], add_special_tokens=False)
            require(
                prefix == context[: len(prefix)] and prefix[-1] == 624, "Role boundary mismatch"
            )
            ref = result["activation_file"]["path"]
            tensors[ref] = load_file(directory / ref, device="cpu")
            require(
                set(tensors[ref]) == {f"candidate_{i}" for i in range(4)}, "Tensor keys mismatch"
            )
            for i, candidate in enumerate(result["candidates"]):
                whole = tokenizer.encode(rendered + candidate["command"], add_special_tokens=False)
                require(
                    whole == context + candidate["token_ids"]
                    and tokenizer.decode(candidate["token_ids"]) == candidate["command"]
                    and candidate["patch"]["position"] == len(prefix) - 1,
                    "Candidate boundary/site mismatch",
                )
                max_length = max(max_length, len(whole))
                vector = tensors[ref][f"candidate_{i}"]
                require(
                    vector.dtype == torch.bfloat16
                    and vector.shape == (3584,)
                    and bool(torch.isfinite(vector).all()),
                    "Bad BF16 tensor",
                )
        directions = torch.tensor(
            json.loads(files["run/random_directions.json"])["vectors"], dtype=torch.float32
        )
        require(
            directions.shape == (10, 3584)
            and bool(((directions.norm(dim=1) - 1).abs() <= 1e-6).all()),
            "Nonunit directions",
        )
        max_deltas = {"residual_norm": 0.0, "desired_norm": 0.0, "actual_norm": 0.0}
        recomputed = 0
        for record in records:
            arm = record["job"]["arm"]
            if arm in {"baseline", "repeat"}:
                continue
            for candidate in record["result"]["candidates"]:
                m = candidate["patch"]
                own = tensors[m["recipient"]["path"]][m["recipient"]["key"]].float()
                donor = tensors[m["donor"]["path"]][m["donor"]["key"]].float()
                desired = float((donor.double() - own.double()).norm())
                if arm.startswith("random_"):
                    direction = directions[m["random_index"]] * m["random_sign"]
                    replacement = (own + m["desired_norm"] * direction).bfloat16().float()
                else:
                    replacement = donor
                actual = float((replacement.double() - own.double()).norm())
                for key, value in {
                    "residual_norm": float(own.double().norm()),
                    "desired_norm": desired,
                    "actual_norm": actual,
                }.items():
                    max_deltas[key] = max(max_deltas[key], abs(value - m[key]))
                    require(
                        math.isclose(value, m[key], rel_tol=1e-6, abs_tol=1e-5),
                        "CPU/GPU tensor norm discrepancy: " + key,
                    )
                recomputed += 1
        return {
            "archive_sha256": SHA256,
            "verified_payloads": count,
            "local_frozen_analysis_exactly_matches_cloud": True,
            "journal_matches_jsonl": True,
            "baseline_prompts_retokenized": len(baseline),
            "candidate_boundaries_retokenized": 4 * len(baseline),
            "all_intervention_inputs_match_baseline": True,
            "max_prompt_plus_command_tokens": max_length,
            "bf16_activation_files_checked": len(tensors),
            "bf16_activation_vectors_checked": 4 * len(tensors),
            "candidate_edit_norms_recomputed": recomputed,
            "max_cpu_vs_gpu_norm_absolute_difference": max_deltas,
            "norm_recomputation_tolerance": {"relative": 1e-6, "absolute": 1e-5},
            "note": "CPU reduction tolerance is a verification tolerance, not a change "
            "to the frozen 5% random edit-norm gate. GPU desired norm is used "
            "to reconstruct the delivered random BF16 edit.",
            "source_hash": manifest["provenance"]["source_hash"],
            "tokenizer_revision": spec["model"]["revision"],
            "no_additional_model_inference": True,
        }


if __name__ == "__main__":
    torch.set_num_threads(1)
    print(json.dumps(verify(), indent=2, sort_keys=True))
