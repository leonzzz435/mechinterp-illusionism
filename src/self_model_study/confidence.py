"""Dependent, journaled confidence pilot using the frozen public-source design."""

import math
import sqlite3
from pathlib import Path

import numpy as np

from . import confidence_data as data
from .io import canonical, digest, read_json, write_json
from .pilot import audit_records, jobs_in, run_plan, scientific_spec
from .pilot_backend import create_backend, encode_boundary, render_prompt, select_command
from .storage import read_records

DEFAULT_SPEC = read_json(Path(__file__).with_name("confidence_spec.json"))
PROTOCOL = DEFAULT_SPEC["protocol"]
ENGINE = DEFAULT_SPEC["engine"]
# Input hashes from the approved CPU design, independent of the new runner.
FROZEN_ITEMS = "82779d2bd33dc13d69296ee96a0febf04f5128090ce9dda9e620c176d5fc9b20"
FROZEN_INPUTS = "67057c1f6eea12e279e2181288a0b08e0381abc433c8aaa109799c7d51d34446"
FROZEN_PLAN = "9ed0bc8322c2bbdc5f41a6a1ee870c49c11cce11d2a92e29c8ae8dc569edfc16"


def validate_spec(spec):
    if set(spec) != set(DEFAULT_SPEC):
        raise ValueError("Unknown/incomplete confidence configuration")
    for key, value in DEFAULT_SPEC.items():
        if key != "max_seconds" and canonical(spec[key]) != canonical(value):
            raise ValueError(f"Frozen confidence field changed: {key}")
    if type(spec["max_seconds"]) is not int or not 0 < spec["max_seconds"] <= 5400:
        raise ValueError("Confidence invocation limit must be 1–5400 seconds")
    return spec


def build_plan(spec, cache=None, fetch=False):
    validate_spec(spec)
    cache = Path(cache) if cache else data.ROOT / ".cache/confidence-source"
    tables = data.verified_sources(cache, spec["source_manifest"], fetch)
    source_audit = data.audit_tables(tables)
    items = data.build_items(tables, spec["design"])
    if (
        data.digest(items) != FROZEN_ITEMS
        or data.digest(list(data.all_inputs(items, spec["design"]))) != FROZEN_INPUTS
    ):
        raise ValueError("Inputs differ from approved CPU design")
    difficulty = {int(r["question_index"]): r for r in tables["phase1_difficulty.csv"]}
    embeddings = {int(r["question_index"]): r for r in tables["phase1_embeddings.csv"]}
    blocks = []
    for split in ("calibration", "assessment"):
        selected = [i for i in items if i["split"] == split]
        for offset in range(0, len(selected), 32):
            jobs = []
            for item in selected[offset : offset + 32]:
                parent = digest([PROTOCOL, item["item_id"], item["rotation"], "answer"])
                stages = (
                    ("answer",)
                    if split == "calibration"
                    else ("answer", "confidence", "abstention")
                )
                for phase in stages:
                    row = dict(item, answer_texts=item["choices"])
                    if split == "assessment":
                        row["external_difficulty"] = float(
                            difficulty[item["source_index"]]["difficulty_score"]
                        )
                        row["embedding"] = [
                            float(embeddings[item["source_index"]][f"embed_pc{j}"])
                            for j in range(1, 11)
                        ]
                    row.update(
                        phase=phase,
                        prompt=(
                            "[DEPENDENT INPUT: resolve actual journaled answer before inference]"
                            if phase == "confidence"
                            else data.prompt_for(item, phase, spec["design"])
                        ),
                        choices=spec["design"][phase + "_candidates"],
                    )
                    jobs.append(
                        {
                            "id": digest([PROTOCOL, item["item_id"], item["rotation"], phase]),
                            "kind": "confidence_choice",
                            "format": "chat",
                            "row": row,
                            "parent_id": parent if phase == "confidence" else None,
                        }
                    )
            blocks.append({"id": f"{split}-{offset // 32:02d}", "jobs": jobs})
    return {
        "protocol": PROTOCOL,
        "split": "development_replication",
        "blocks": blocks,
        "source_audit": source_audit,
        "sources": spec["source_manifest"],
        "design_input_hash": FROZEN_INPUTS,
        "design_items_hash": FROZEN_ITEMS,
    }


def preview(spec, plan=None):
    plan = plan or build_plan(spec)
    return {
        "valid": True,
        "protocol": PROTOCOL,
        "plan_hash": digest(plan),
        "expected_jobs": len(jobs_in(plan)),
        "blocks": len(plan["blocks"]),
        "model_inference": False,
        "max_seconds": spec["max_seconds"],
    }


def plan_items(plan):
    return [
        {
            k: j["row"][k]
            for k in (
                "item_id",
                "source_index",
                "split",
                "rotation",
                "question",
                "choices",
                "correct_number",
            )
        }
        | {"choices": j["row"]["answer_texts"]}
        for j in jobs_in(plan)
        if j["row"]["phase"] == "answer"
    ]


def prompt_for_job(job, spec, parent=None):
    row = job["row"]
    item = {**row, "choices": row["answer_texts"]}
    answer = None
    if row["phase"] == "confidence":
        if parent is None or parent["id"] != job["parent_id"] or parent["status"] != "ok":
            raise ValueError("Missing or failed parent answer; confidence is blocked")
        answer = parent["result"]["selected_command"]
    return data.prompt_for(item, row["phase"], spec["design"], answer)


def token_inputs(spec, plan, tokenizer):
    items = plan_items(plan)
    if data.digest(items) != FROZEN_ITEMS:
        raise ValueError("Plan question content differs from frozen input audit")
    audit = data.token_audit(items, spec["design"], tokenizer)
    if audit["rendered_tokens_sha256"] != FROZEN_TOKENS:
        raise ValueError("Rendered tokens differ from frozen Qwen preflight")
    return audit


FROZEN_TOKENS = "23e67a671d6c1e88ea581cc99340d23590f90569c274d973e6d1cd61e60dd83c"


def load_tokenizer(spec):
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(
        spec["model"]["repo"], revision=spec["model"]["revision"], trust_remote_code=False
    )


def tokenizer_audit(spec, plan=None):
    plan = plan or build_plan(spec)
    return {**preview(spec, plan), "tokenizer": token_inputs(spec, plan, load_tokenizer(spec))}


def probabilities(scores, temperature=1.0):
    values = np.asarray(scores, dtype=float) / temperature
    values -= np.max(values, axis=-1, keepdims=True)
    values = np.exp(values)
    return values / values.sum(axis=-1, keepdims=True)


def derived_result(job, result):
    choices = job["row"]["choices"]
    if [c["command"] for c in result["candidates"]] != choices:
        raise ValueError("Candidate order differs from frozen menu")
    scores = [
        c["log_likelihood"] if c["log_likelihood"] is not None else float("nan")
        for c in result["candidates"]
    ]
    selected, status = select_command(choices, scores)
    if selected != result["selected_command"] or status != result["status"]:
        raise ValueError("Selection disagrees with likelihoods")
    if status != "ok":
        return {
            "correct": None,
            "abstained": None,
            "confidence": None,
            "menu_mass": None,
            "restricted_probabilities": None,
        }
    if any(s > 1e-6 for s in scores):
        raise ValueError("Positive log probability")
    mass = sum(math.exp(s) for s in scores)
    if mass > 1 + 1e-5:
        raise ValueError("Digit menu mass exceeds one")
    phase = job["row"]["phase"]
    return {
        "correct": None if phase == "confidence" else selected == job["row"]["correct_number"],
        "abstained": selected == "5" if phase == "abstention" else None,
        "confidence": (int(selected) + 0.5) / 10 if phase == "confidence" else None,
        "menu_mass": mass,
        "restricted_probabilities": probabilities(scores).tolist(),
    }


def check_tokens(result, prompt, choices, tokenizer, max_length):
    rendered = render_prompt(tokenizer, prompt, "chat")
    pairs = [encode_boundary(tokenizer, rendered, c, max_length) for c in choices]
    if result["rendered_prompt"] != rendered or result["prompt_token_ids"] != pairs[0][0]:
        raise ValueError("Recorded prompt tokens differ from actual input")
    for candidate, (_, tokens) in zip(result["candidates"], pairs):
        if candidate["token_ids"] != tokens or candidate["token_count"] != 1 or len(tokens) != 1:
            raise ValueError("Digit continuation mismatch")


def fit_temperature(records, spec):
    rows = sorted(
        (r for r in records if r["job"]["row"]["split"] == "calibration"), key=lambda r: r["id"]
    )
    expected = spec["design"]["calibration_items"] * 4
    if len(rows) != expected or any(r["status"] != "ok" for r in rows):
        raise ValueError("Temperature requires complete valid calibration data only")
    scores = np.array([[c["log_likelihood"] for c in r["result"]["candidates"]] for r in rows])
    gold = np.array([int(r["job"]["row"]["correct_number"]) - 1 for r in rows])
    grid = spec["design"]["temperature_grid"]
    temperatures = np.geomspace(grid["minimum"], grid["maximum"], grid["logspace_points"])
    losses = []
    for temperature in temperatures:
        logits = scores / temperature
        shifted = logits - logits.max(axis=1, keepdims=True)
        losses.append(
            float(
                np.mean(np.log(np.exp(shifted).sum(axis=1)) - shifted[np.arange(len(rows)), gold])
            )
        )
    index = int(np.argmin(losses))
    return {
        "temperature": float(temperatures[index]),
        "boundary_optimum": index in (0, len(losses) - 1),
        "temperatures": temperatures.tolist(),
        "negative_log_likelihoods": losses,
        "calibration_record_hashes": {r["id"]: r["checksum"] for r in rows},
        "independent_questions": spec["design"]["calibration_items"],
    }


def audit_scientific_records(spec, plan, records, manifest, directory=None):
    by_id = {r["id"]: r for r in records}
    for record in records:
        job, result = record["job"], record["result"]
        if record["status"] == "error":
            continue
        parent = by_id.get(job["parent_id"])
        if result["input_prompt"] != prompt_for_job(job, spec, parent):
            raise ValueError("Dependent prompt differs from actual parent answer")
        if result.get("parent_checksum") != (parent["checksum"] if parent else None):
            raise ValueError("Changed parent record")
        if result["judgment"] != derived_result(job, result):
            raise ValueError("Stored confidence judgment differs from scores")
        if not manifest["synthetic"]:
            if any(c["token_count"] != 1 for c in result["candidates"]):
                raise ValueError("Non-single-token real result")
    if directory is not None:
        calibration = Path(directory) / "calibration.json"
        if calibration.exists():
            saved, recomputed = read_json(calibration), fit_temperature(records, spec)
            if any(
                saved[k] != recomputed[k] for k in saved if k != "negative_log_likelihoods"
            ) or not np.allclose(
                saved["negative_log_likelihoods"],
                recomputed["negative_log_likelihoods"],
                rtol=0,
                atol=1e-12,
            ):
                raise ValueError("Frozen calibration changed")
            for record in records:
                if record["job"]["row"]["split"] == "assessment" and record["status"] != "error":
                    if record["result"].get("calibration_checksum") != digest(saved):
                        raise ValueError("Assessment calibration fingerprint mismatch")
        elif any(r["job"]["row"]["split"] == "assessment" for r in records):
            raise ValueError("Assessment without frozen calibration")


def read_run(directory):
    directory = Path(directory)
    manifest, plan = read_json(directory / "manifest.json"), read_json(directory / "plan.json")
    spec = validate_spec(manifest["config"])
    if (
        manifest["engine"] != ENGINE
        or manifest["protocol"] != PROTOCOL
        or digest(plan) != manifest["plan_hash"]
    ):
        raise ValueError("Confidence plan identity/checksum mismatch")
    if digest(scientific_spec(spec)) != manifest["config_hash"]:
        raise ValueError("Confidence config checksum mismatch")
    if not manifest["synthetic"] and digest(plan) != FROZEN_PLAN:
        raise ValueError("Real run differs from frozen confidence execution plan")
    records = read_records(directory)
    audit_records(records, plan, manifest)
    audit_scientific_records(spec, plan, records, manifest, directory)
    return manifest, plan, records


def run(spec, directory, max_jobs=None, backend_factory=None, checkpoint=None, plan=None):
    validate_spec(spec)
    plan = plan or build_plan(spec)
    directory = Path(directory)

    def factory(config):
        if backend_factory is not None:
            return backend_factory(config)
        if digest(plan) != FROZEN_PLAN:
            raise ValueError("Refusing to execute unfrozen confidence plan")
        audit = token_inputs(config, plan, load_tokenizer(config))
        write_json(directory / "tokenizer_audit.json", audit)
        return create_backend(config)

    def execute(backend, job):
        row = job["row"]
        if row["split"] == "assessment" and not (directory / "calibration.json").exists():
            write_json(
                directory / "calibration.json", fit_temperature(read_records(directory), spec)
            )
        parent = None
        if job["parent_id"]:
            with sqlite3.connect(
                f"file:{(directory / 'trials.sqlite').resolve()}?mode=ro", uri=True
            ) as db:
                found = db.execute(
                    "SELECT payload FROM trials WHERE id=?", (job["parent_id"],)
                ).fetchone()
            if found:
                import json

                parent = json.loads(found[0])
        prompt = prompt_for_job(job, spec, parent)
        result = backend.choice(prompt, row["choices"], "chat")
        result.update(input_prompt=prompt, parent_checksum=parent["checksum"] if parent else None)
        if row["split"] == "assessment":
            result["calibration_checksum"] = digest(read_json(directory / "calibration.json"))
        try:
            result["judgment"] = derived_result(job, result)
            if hasattr(backend, "tokenizer"):
                check_tokens(
                    result, prompt, row["choices"], backend.tokenizer, spec["model"]["max_length"]
                )
        except (ValueError, KeyError) as exc:
            result.update(status="error", error_type=type(exc).__name__, error=str(exc))
        if result["status"] != "ok":
            result["technical_failure"] = True
        return result

    return run_plan(
        spec,
        plan,
        directory,
        max_jobs,
        factory,
        checkpoint,
        execute,
        lambda d, m, r: audit_scientific_records(spec, plan, r, m, d),
    )
