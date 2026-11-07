"""The completed control must reproduce, and plausible altered summaries must fail."""

import importlib
import json
from copy import deepcopy
from pathlib import Path

import pytest


@pytest.fixture
def auditor(monkeypatch):
    monkeypatch.syspath_prepend("scripts")
    return importlib.import_module("review_role_evidence")


def test_completed_role_control_archive(auditor):
    result = auditor.audit()
    assert result == json.loads(Path("review/qwen-role-control-audit.json").read_text())
    assert result["decision"] == "wording_sensitive_candidate"
    assert result["verified_records"] == 2048 and result["verified_quartets"] == 512


def test_audit_rejects_selection_inconsistent_with_likelihoods(auditor):
    files, _, _ = auditor.archive_files(auditor.ARCHIVE, auditor.SHA256)
    record = json.loads(files["run/records.jsonl"].splitlines()[0])
    result = deepcopy(record["result"])
    result["selected_command"] = next(
        c["command"] for c in result["candidates"] if c["command"] != result["selected_command"]
    )
    with pytest.raises(ValueError, match="Selection disagrees"):
        auditor.outcome(record["job"]["row"], result)


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("two_sided_sign_flip_p", 0.001, "Sign-flip p mismatch"),
        ("positive_scenarios", 8, "Scenario effect mismatch"),
    ],
)
def test_audit_rejects_altered_inference_even_if_file_hashes_are_resealed(
    auditor, monkeypatch, field, value, message
):
    files, actual, count = auditor.archive_files(auditor.ARCHIVE, auditor.SHA256)
    report = json.loads(files["run/analysis.json"])
    report["interaction"]["after_relevant"][field] = value
    files["run/analysis.json"] = json.dumps(report).encode()
    # Bypass the file-integrity layer to exercise the independent semantic check.
    monkeypatch.setattr(auditor, "archive_files", lambda *args: (files, actual, count))
    with pytest.raises(ValueError, match=message):
        auditor.audit()
