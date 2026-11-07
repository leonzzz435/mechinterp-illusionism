"""An independent audit must reject plausible but inconsistent saved outcomes."""

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

from self_model_study.action_task import build_design, score_command
from self_model_study.pilot_analysis import rating_lookup, read_ratings


def auditor():
    spec = importlib.util.spec_from_file_location(
        "review_qwen_evidence", "scripts/review_qwen_evidence.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def example():
    row = next(
        r
        for r in build_design(scenarios=1)
        if r["phase"] == "after" and r["relevant_update"] and r["view"] == "other"
    )
    command = row["expected_command"]
    result = {
        "selected_command": command,
        "execution": score_command(row, command),
        "candidates": [
            {"command": c, "log_likelihood": -1 if c == command else -5} for c in row["choices"]
        ],
    }
    return row, result


def test_completed_qwen_archive_and_failed_screen_are_reproducible():
    result = auditor().audit(
        "review/evidence/qwen-78ee6db8adfc4f3e.tar.gz",
        "cf8eceea87129acaad2365f36af99d8f54923015923c837419a691252b8f12fa",
    )
    assert result["verified_file_checksums"] == 48
    assert result["completed_outputs"] == result["expected_outputs"] == 3232
    assert result["recomputed_action_choices"] == 3072
    assert result["recomputed_action_strata"] == 52
    assert result["recomputed_counterfactual_strata"] == 18
    assert result["status"] == "complete" and not result["synthetic"]
    assert result["source_commit"] == "9f1356f139e48c108dbfa5eedb7950fefdf4104a"
    assert result["format_numerical_pass"] == {"plain": False, "chat": False}
    assert not result["action_gate_passed"]
    assert result["post_hoc_relevant_update_errors"]["chat/self"] == {
        "other_actor_command": 36,
        "other_command": 5,
    }
    assert result["post_hoc_relevant_update_errors"]["chat/named_self"] == {
        "other_actor_command": 33,
        "other_command": 6,
    }


def test_actual_human_ratings_preserve_ambiguity_and_model_evidence():
    audit = auditor()
    original, _, _ = audit.archive_files("review/evidence/qwen-78ee6db8adfc4f3e.tar.gz")
    path = "review/evidence/qwen-78ee6db8adfc4f3e-with-ratings-v1.tar.gz"
    sha = "c260bb001dac8841def6bdb28d7b5e418e9f329c44e005602f5467bd40c3aa9b"
    rated, _, _ = audit.archive_files(path, sha)
    assert set(rated) - set(original) == {"run/human_ratings.csv"}
    changed = {name for name in original if original[name] != rated[name]}
    assert changed == {
        "run/analysis.json",
        "run/checksums.json",
        *(f"run/figures/human_ratings.{ext}" for ext in ("svg", "pdf", "png")),
    }
    sheet = Path("review/ratings/qwen-78ee6db8adfc4f3e/human_ratings.csv")
    assert sheet.read_bytes() == rated["run/human_ratings.csv"]
    report = audit.audit(path, sha)
    assert report["verified_file_checksums"] == 49 and not report["action_gate_passed"]
    human = report["human_ratings"]
    assert human["outputs_rated"] == 40 and human["unclear_cells"] == 2
    assert human["counts"]["disclaimer"] == {
        "plain": {"0": 9, "1": 11},
        "chat": {"0": 5, "1": 15},
    }
    assert human["paired_counts_plain_chat"]["experience_claim"] == {"0/0": 19, "unclear/0": 1}
    assert (
        human["post_hoc_disclaimer_exact_sign_check"]["two_sided_probability_under_symmetric_signs"]
        == 0.125
    )
    records = [json.loads(line) for line in rated["run/records.jsonl"].splitlines()]
    jobs = [j for b in json.loads(rated["run/plan.json"])["blocks"] for j in b["jobs"]]
    calculated = read_ratings(sheet, rating_lookup(jobs, {r["id"]: r for r in records}), 10000)
    assert calculated == json.loads(rated["run/analysis.json"])["human_ratings"]
    assert calculated["effects"][0]["ci95"] == [0.05, 0.4]
    assert all(effect["estimate"] is None for effect in calculated["effects"][1:])


def test_same_target_role_review_and_rejection_of_extra_prompt_changes(monkeypatch):
    import importlib

    monkeypatch.syspath_prepend("scripts")
    review = importlib.import_module("review_qwen_role_pairs")
    report = review.review()
    assert report == json.loads(Path("review/qwen-role-pairs.json").read_text())
    assert report["matched_pairs_verified"] == 1024
    assert not report["action_gate_passed"]
    group = report["groups"]["chat/after_relevant"]
    assert group["correctness_named_self_other"] == {"0/1": 39, "1/1": 89}
    assert group["mean_scenario_other_minus_named_self"] == 39 / 128
    assert len(report["examples"]) == len(report["chat_after_relevant_by_scenario"]) == 8
    # A nominally matched pair must fail if anything beyond the role line changed.
    files, _, _ = auditor().archive_files(review.ARCHIVE, review.SHA256)
    records = [json.loads(line) for line in files["run/records.jsonl"].splitlines()]
    _, named, other = review.match_pairs(records)[0]
    corrupted = deepcopy(named)
    corrupted["result"]["rendered_prompt"] += "\nAn extra instruction."
    with pytest.raises(ValueError, match="Prompt differs outside"):
        review.match_pairs([corrupted, other])
    with pytest.raises(ValueError, match="Incomplete matched-role pair"):
        review.match_pairs([named])


def test_reviewer_reconstructs_state_and_rejects_changed_selection():
    check = auditor().outcome
    row, result = example()
    assert check(row, result, "ok") == (1, row["expected_command"])
    corrupted = deepcopy(result)
    next(c for c in corrupted["candidates"] if c["command"] != row["expected_command"])[
        "log_likelihood"
    ] = 0
    with pytest.raises(ValueError, match="Selection disagrees"):
        check(row, corrupted, "ok")
    corrupted = deepcopy(result)
    corrupted["execution"]["state_after"]["markers"][row["target"]] = 99
    with pytest.raises(ValueError, match="Saved execution disagrees"):
        check(row, corrupted, "ok")


def test_reviewer_reconstructs_target_and_update():
    check = auditor().outcome
    row, result = example()
    wrong = deepcopy(row)
    wrong["target"] = row["assigned"]
    with pytest.raises(ValueError, match="Bound target mismatch"):
        check(wrong, result, "ok")
    wrong = deepcopy(row)
    wrong["state"] = deepcopy(row["before"])
    with pytest.raises(ValueError, match="Saved simulator state mismatch"):
        check(wrong, result, "ok")


@pytest.mark.parametrize("invalid", [False, True])
def test_reviewer_counts_ties_and_invalid_scores_as_failures(invalid):
    row, result = example()
    for candidate in result["candidates"]:
        candidate["log_likelihood"] = None if invalid else -1
    result["selected_command"] = None
    result["execution"] = score_command(row, None)
    status = "invalid_scores" if invalid else "tie"
    assert auditor().outcome(row, result, status) == (0, None)
    with pytest.raises(ValueError, match="Score status mismatch"):
        auditor().outcome(row, result, "ok")
