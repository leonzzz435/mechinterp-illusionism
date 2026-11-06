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
