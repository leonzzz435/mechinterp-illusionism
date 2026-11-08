"""Data and input-contract checks for the CPU-only confidence design."""

import copy
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.util.spec_from_file_location(
    "confidence_design", ROOT / "scripts/review_confidence_design.py"
)
design = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(design)
SPEC = json.loads(design.SPEC.read_text())


@pytest.fixture
def tables():
    result = {}
    for split in (0, 1):
        result[f"phase{split}_questions.csv"] = [
            {
                "question": f"Question {split}/{i}",
                **{f"choice_{j}": f"Answer {j}" for j in range(1, 5)},
            }
            for i in range(1000)
        ]
    questions = result["phase1_questions.csv"]
    result["phase1_difficulty.csv"] = [
        dict(
            question_index=str(i),
            question=q["question"],
            n_correct="10",
            n_runs="20",
            difficulty_score="0.5",
        )
        for i, q in enumerate(questions)
    ]
    result["phase1_embeddings.csv"] = [
        {
            "question_index": str(i),
            "question": q["question"],
            **{f"embed_pc{j}": "0.1" for j in range(1, 11)},
            **{f"choice_{j}_original": q[f"choice_{j}"] for j in range(1, 5)},
        }
        for i, q in enumerate(questions)
    ]
    result["phase1_rag_scores.csv"] = [
        dict(question_index=str(i), question=q["question"]) for i, q in enumerate(questions)
    ]
    result["simpleQA_4MCQ_dataset.csv"] = [
        dict(q, gt_answer="1")
        for name in ("phase0_questions.csv", "phase1_questions.csv")
        for q in result[name]
    ]
    return result


def test_source_alignment_and_normalized_disjointness(tables):
    assert design.audit_tables(tables)["master_correct_answers_verified"] == 2000
    tables["phase1_questions.csv"][0]["question"] = "  QUESTION 0/0  "
    with pytest.raises(ValueError, match="overlap"):
        design.audit_tables(tables)


@pytest.mark.parametrize(
    "name", ["phase1_difficulty.csv", "phase1_embeddings.csv", "phase1_rag_scores.csv"]
)
def test_covariate_join_rejects_misaligned_question(tables, name):
    tables[name][0]["question"] = "wrong question"
    with pytest.raises(ValueError, match="Covariate question mismatch"):
        design.audit_tables(tables)


def test_invalid_keys_covariates_and_duplicate_options(tables):
    for name, field, value, message in [
        ("phase1_questions.csv", "choice_2", " Answer 1 ", "Duplicate/empty choices"),
        ("phase1_difficulty.csv", "difficulty_score", "0.9", "difficulty"),
        ("phase1_embeddings.csv", "embed_pc1", "nan", "embedding"),
        ("simpleQA_4MCQ_dataset.csv", "gt_answer", "2", "Correct answer"),
    ]:
        changed = copy.deepcopy(tables)
        changed[name][0][field] = value
        with pytest.raises(ValueError, match=message):
            design.audit_tables(changed)


def test_deterministic_sample_rotations_and_independent_unit(tables):
    items = design.build_items(tables, SPEC)
    assert items == design.build_items(tables, SPEC)
    grouped = defaultdict(list)
    for item in items:
        grouped[item["item_id"]].append(item)
    assert len(grouped) == 192
    assert Counter(i["split"] for i in items) == {"calibration": 256, "assessment": 512}
    for variants in grouped.values():
        assert {i["rotation"] for i in variants} == {0, 1, 2, 3}
        assert {i["correct_number"] for i in variants} == {"1", "2", "3", "4"}
        assert len({i["question"] for i in variants}) == 1
        for item in variants:
            assert item["choices"][int(item["correct_number"]) - 1] == "Answer 1"
    changed = dict(SPEC, seed=1730)
    assert design.build_items(tables, changed) != items


def test_no_oracle_metadata_and_actual_answer_dependency(tables):
    item = design.build_items(tables, SPEC)[-1]
    for phase in ("answer", "abstention", "confidence"):
        before = design.prompt_for(item, phase, SPEC, "2")
        poisoned = dict(
            item,
            correct_number="ORACLE_SECRET",
            difficulty_score="SECRET",
            item_id="SECRET",
            source_index=-1,
        )
        assert before == design.prompt_for(poisoned, phase, SPEC, "2")
        assert "SECRET" not in before
    assert design.prompt_for(item, "confidence", SPEC, "1") != design.prompt_for(
        item, "confidence", SPEC, "2"
    )
    with pytest.raises(ValueError, match="actual valid"):
        design.prompt_for(item, "confidence", SPEC)


def test_all_dependent_input_branches_and_candidate_counts(tables):
    inputs = list(design.all_inputs(design.build_items(tables, SPEC), SPEC))
    assert Counter(phase for phase, _, _ in inputs) == {
        "answer": 768,
        "abstention": 512,
        "confidence": 2048,
    }
    assert sum(len(candidates) for _, _, candidates in inputs) == 26112


def test_checksum_tampering_fails_without_refetch(tmp_path):
    path = tmp_path / "source.csv"
    path.write_text("tampered")
    manifest = {"files": [{"filename": path.name, "sha256": "0" * 64}]}
    with pytest.raises(ValueError, match="checksum mismatch"):
        design.verified_sources(tmp_path, manifest, fetch=True)


def test_missing_source_requires_explicit_fetch(tmp_path):
    manifest = {"files": [{"filename": "missing.csv", "sha256": "0" * 64}]}
    with pytest.raises(ValueError, match="use --fetch"):
        design.verified_sources(tmp_path, manifest)


def test_incomplete_rotation_plan_rejected(tables):
    with pytest.raises(ValueError, match="all four"):
        design.build_items(tables, dict(SPEC, rotations=3))
