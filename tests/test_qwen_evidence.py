"""An independent audit must reject plausible but inconsistent saved outcomes."""

import importlib.util
from copy import deepcopy

import pytest

from self_model_study.action_task import build_design, score_command


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
