"""Check error-direction semantics and reproducibility without model inference."""

import importlib
import json
from pathlib import Path

import pytest


@pytest.fixture
def counter(monkeypatch):
    monkeypatch.syspath_prepend("scripts")
    return importlib.import_module("count_possessive_errors")


@pytest.fixture
def row():
    return {
        "phase": "after",
        "relevant_update": True,
        "target": "Cedar",
        "before": {"permissions": {"Cedar": ["old"], "Birch": ["foreign"]}},
        "state": {
            "commands": ["old", "foreign", "new", "unused"],
            "permissions": {"Cedar": ["new"], "Birch": ["foreign"]},
        },
    }


@pytest.mark.parametrize(
    "command,accepted,category",
    [
        ("new", True, "correct"),
        ("old", False, "revoked_target_command"),
        ("foreign", False, "other_actor_command"),
        ("unused", False, "other_command"),
    ],
)
def test_distinguishes_stale_from_foreign_command(counter, row, command, accepted, category):
    assert counter.classify(row, command, accepted) == category


def test_invalid_is_not_relabelled_as_a_behavioral_error(counter, row):
    assert counter.classify(row, None, False, "tie") == "invalid_or_error"
    with pytest.raises(ValueError, match="Inconsistent accepted"):
        counter.classify(row, "foreign", True)
    row["relevant_update"] = False
    with pytest.raises(ValueError, match="requires a relevant"):
        counter.classify(row, "foreign", False)


def test_reproduces_count_from_checked_archive(counter):
    result = counter.count_errors()
    assert result == json.loads(Path("review/qwen-possessive-error-count.json").read_text())
    assert sum(c["n"] for c in result["cells"].values()) == 1536
    assert result["confidence_intervals"] is None and not result["model_inference"]


def test_rejects_changed_archive(counter):
    with pytest.raises(ValueError, match="Archive digest mismatch"):
        counter.count_errors(sha256="0" * 64)
