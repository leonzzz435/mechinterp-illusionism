"""Verify the completed archive and reject plausible altered inference claims."""

import importlib
import json
from pathlib import Path

import pytest


@pytest.fixture
def auditor(monkeypatch):
    monkeypatch.syspath_prepend("scripts")
    return importlib.import_module("review_patch_evidence")


def test_completed_patch_archive(auditor):
    result = auditor.audit()
    assert result == json.loads(Path("review/qwen-role-patch-audit.json").read_text())
    assert result["decision"] == "no_bidirectional_transfer_candidate"
    assert result["verified_records"] == 11296


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("two_sided_sign_flip_p", 0.01, "Sign-flip p mismatch"),
        ("positive_scenarios", 8, "Positive scenario count mismatch"),
    ],
)
def test_rejects_altered_primary_inference(auditor, field, value, message):
    saved = json.loads(Path("review/qwen-role-patch-audit.json").read_text())["primary_contrast"]
    saved[field] = value
    with pytest.raises(ValueError, match=message):
        auditor.check_stat(saved, saved["scenario_means"])


def test_rejects_score_drift_despite_unchanged_decision(auditor):
    reference = {
        "selected_command": "mark_silver",
        "prompt_token_ids": [1, 2],
        "candidates": [{"command": "mark_silver", "token_ids": [3], "log_likelihood": -1.0}],
    }
    changed = json.loads(json.dumps(reference))
    changed["candidates"][0]["log_likelihood"] += 0.01
    with pytest.raises(ValueError, match="Parity score mismatch"):
        auditor.parity(changed, reference, 1e-6)
