"""Audit a design, author data and optional cached tokenizer; never load model weights."""

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import math
import unicodedata
import urllib.request
from collections import Counter
from pathlib import Path

from self_model_study.pilot_backend import encode_boundary, render_prompt

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "designs/qwen-confidence-pilot.json"


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def normalized(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def verified_sources(cache, manifest, fetch=False):
    """Downloads are explicit, hash checked and atomic; existing corruption fails closed."""
    cache.mkdir(parents=True, exist_ok=True)
    tables = {}
    for entry in manifest["files"]:
        path = cache / entry["filename"]
        if not path.exists():
            if not fetch:
                raise ValueError(f"Missing {path}; use --fetch for public author data")
            with urllib.request.urlopen(entry["download_url"], timeout=60) as response:
                content = response.read()
            if hashlib.sha256(content).hexdigest() != entry["sha256"]:
                raise ValueError(f"Download checksum mismatch: {path.name}")
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_bytes(content)
            temporary.replace(path)
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != entry["sha256"]:
            raise ValueError(f"Source checksum mismatch: {path.name}")
        if path.suffix == ".csv":
            tables[path.name] = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
    return tables


def audit_tables(tables):
    sets = []
    for name in ("phase0_questions.csv", "phase1_questions.csv"):
        rows = tables[name]
        if len(rows) != 1000:
            raise ValueError(f"Unexpected source count: {name}")
        keys = [normalized(row["question"]) for row in rows]
        if len(set(keys)) != len(keys) or not all(keys):
            raise ValueError(f"Duplicate/empty question: {name}")
        for row in rows:
            choices = [normalized(row[f"choice_{i}"]) for i in range(1, 5)]
            if len(set(choices)) != 4 or not all(choices):
                raise ValueError(f"Duplicate/empty choices: {name}")
        sets.append(set(keys))
    if sets[0] & sets[1]:
        raise ValueError("Calibration/assessment source overlap")

    questions = tables["phase1_questions.csv"]
    for name in ("phase1_difficulty.csv", "phase1_embeddings.csv", "phase1_rag_scores.csv"):
        rows = tables[name]
        by_index = {int(row["question_index"]): row for row in rows}
        if len(rows) != 1000 or set(by_index) != set(range(1000)):
            raise ValueError(f"Covariate index mismatch: {name}")
        for index, question in enumerate(questions):
            row = by_index[index]
            if row["question"] != question["question"]:
                raise ValueError(f"Covariate question mismatch: {name}:{index}")
            if name == "phase1_difficulty.csv":
                n, correct = int(row["n_runs"]), int(row["n_correct"])
                score = float(row["difficulty_score"])
                if (
                    n != 20
                    or not 0 <= correct <= n
                    or not math.isfinite(score)
                    or abs(score - correct / n) > 1e-12
                ):
                    raise ValueError("Invalid external difficulty score")
            if name == "phase1_embeddings.csv":
                if not all(math.isfinite(float(row[f"embed_pc{i}"])) for i in range(1, 11)):
                    raise ValueError("Invalid embedding covariate")
                if any(row[f"choice_{i}_original"] != question[f"choice_{i}"] for i in range(1, 5)):
                    raise ValueError("Embedding choice mismatch")

    master = {normalized(row["question"]): row for row in tables["simpleQA_4MCQ_dataset.csv"]}
    different_foils = {}
    for name in ("phase0_questions.csv", "phase1_questions.csv"):
        count = 0
        for row in tables[name]:
            original = master[normalized(row["question"])]
            if row["choice_1"] != original["choice_" + original["gt_answer"]]:
                raise ValueError("Correct answer differs from master source")
            count += {row[f"choice_{i}"] for i in range(1, 5)} != {
                original[f"choice_{i}"] for i in range(1, 5)
            }
        different_foils[name] = count
    return {
        "source_questions": [len(s) for s in sets],
        "normalized_split_overlap": 0,
        "covariate_rows_verified": 3000,
        "master_correct_answers_verified": 2000,
        "master_different_choice_sets": different_foils,
        "note": "Use published phase tables; master has different foils. "
        "Key agreement is not independent factual verification.",
    }


def selected_indices(rows, count, seed, split):
    return sorted(
        range(len(rows)), key=lambda i: digest([seed, split, normalized(rows[i]["question"])])
    )[:count]


def build_items(tables, spec):
    if spec["rotations"] != 4:
        raise ValueError("This design requires all four rotations")
    items = []
    for split, name in (
        ("calibration", "phase0_questions.csv"),
        ("assessment", "phase1_questions.csv"),
    ):
        rows = tables[name]
        if not 0 < spec[f"{split}_items"] <= len(rows):
            raise ValueError("Invalid split sample size")
        for index in selected_indices(rows, spec[f"{split}_items"], spec["seed"], split):
            row = rows[index]
            order = sorted(range(1, 5), key=lambda i: digest([spec["seed"], split, index, i]))
            for rotation in range(4):
                arranged = order[rotation:] + order[:rotation]
                items.append(
                    {
                        "item_id": f"{split}:{index:04d}",
                        "source_index": index,
                        "split": split,
                        "rotation": rotation,
                        "question": row["question"],
                        "choices": [row[f"choice_{i}"] for i in arranged],
                        "correct_number": str(arranged.index(1) + 1),
                    }
                )
    return items


def prompt_for(item, phase, spec, answer_number=None):
    """Whitelist model-visible values; no key, source index or difficulty is rendered."""
    values = {
        "question": item["question"],
        "options": "\n".join(f"{i}. {text}" for i, text in enumerate(item["choices"], 1)),
    }
    if phase == "confidence":
        if answer_number not in spec["answer_candidates"]:
            raise ValueError("Confidence requires an actual valid forced answer")
        values.update(
            answer_number=answer_number, answer_text=item["choices"][int(answer_number) - 1]
        )
    return spec["prompts"][phase].format(**values)


def all_inputs(items, spec):
    """Audit every possible dependent confidence input, not only the correct-answer branch."""
    for item in items:
        yield "answer", prompt_for(item, "answer", spec), spec["answer_candidates"]
        if item["split"] == "assessment":
            yield "abstention", prompt_for(item, "abstention", spec), spec["abstention_candidates"]
            for answer in spec["answer_candidates"]:
                yield (
                    "confidence",
                    prompt_for(item, "confidence", spec, answer),
                    spec["confidence_candidates"],
                )


def token_audit(items, spec, tokenizer):
    count, max_length, tokens = 0, 0, {}
    fingerprint = hashlib.sha256()
    for phase, prompt, candidates in all_inputs(items, spec):
        rendered = render_prompt(tokenizer, prompt, spec["format"])
        for candidate in candidates:
            context, continuation = encode_boundary(
                tokenizer, rendered, candidate, spec["max_length"]
            )
            if len(continuation) != 1:
                raise ValueError("Candidate digit must be exactly one token")
            if candidate in tokens and tokens[candidate] != continuation:
                raise ValueError("Inconsistent candidate token")
            tokens[candidate] = continuation
            count += 1
            max_length = max(max_length, len(context) + len(continuation))
            fingerprint.update(bytes.fromhex(digest([phase, context, continuation])))
    return {
        "candidate_boundaries_checked": count,
        "maximum_total_tokens": max_length,
        "digit_token_ids": tokens,
        "all_possible_confidence_answers_checked": True,
        "rendered_tokens_sha256": fingerprint.hexdigest(),
        "chat_template_sha256": hashlib.sha256(tokenizer.chat_template.encode()).hexdigest(),
        "package_versions": {
            name: importlib.metadata.version(name) for name in ("transformers", "tokenizers")
        },
        "empty_user_rendering": render_prompt(tokenizer, "", "chat"),
        "weights_loaded": False,
    }


def audit(cache, fetch=False, tokenizer_check=False):
    spec = json.loads(SPEC.read_text())
    manifest = json.loads((ROOT / spec["source_manifest"]).read_text())
    tables = verified_sources(cache, manifest, fetch)
    source_audit = audit_tables(tables)
    items = build_items(tables, spec)
    counts = Counter(item["split"] for item in items)
    result = {
        "protocol": spec["protocol"],
        "status": "cpu_design_audited_not_a_model_result",
        "design_sha256": digest(spec),
        "source_manifest_sha256": digest(manifest),
        "audit_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_audit": source_audit,
        "selected_source_indices": {
            split: sorted({i["source_index"] for i in items if i["split"] == split})
            for split in ("calibration", "assessment")
        },
        "correct_position_counts": {
            split: dict(
                sorted(Counter(i["correct_number"] for i in items if i["split"] == split).items())
            )
            for split in ("calibration", "assessment")
        },
        "items_sha256": digest(items),
        "input_tree_sha256": digest(list(all_inputs(items, spec))),
        "planned_selections": counts["calibration"] + 3 * counts["assessment"],
        "planned_candidate_likelihoods": 4 * counts["calibration"] + 19 * counts["assessment"],
        "independent_assessment_questions": spec["assessment_items"],
        "fixed_example_item_id": next(i["item_id"] for i in items if i["split"] == "assessment"),
        "assessment_fold_by_item": {
            item_id: rank % spec["conditional_predictors"]["folds"]
            for rank, item_id in enumerate(
                sorted(
                    {i["item_id"] for i in items if i["split"] == "assessment"},
                    key=lambda item_id: digest([spec["seed"], "fold", item_id]),
                )
            )
        },
        "unselected_phase1_questions": 1000 - spec["assessment_items"],
        "execution_adapter_implemented": False,
        "paid_job_started": False,
    }
    if tokenizer_check:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(
            spec["model"], revision=spec["revision"], local_files_only=True
        )
        result["tokenizer"] = token_audit(items, spec, tokenizer)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache/confidence-source")
    parser.add_argument(
        "--fetch", action="store_true", help="Download pinned public author artifacts"
    )
    parser.add_argument(
        "--tokenizer-check",
        action="store_true",
        help="Use cached pinned tokenizer, never model weights",
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        result = audit(args.cache, args.fetch, args.tokenizer_check)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f"Design audit failed: {error}\n")
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output)
    else:
        print(output, end="")
