"""Audit real outputs and reject favorable changes to the frozen statistical result."""

import importlib
import json
from copy import deepcopy
from pathlib import Path

import pytest


@pytest.fixture
def auditor(monkeypatch):
    monkeypatch.syspath_prepend("scripts")
    return importlib.import_module("review_possessive_evidence")


def test_completed_possessive_archive(auditor):
    result = auditor.audit()
    assert result == json.loads(Path("review/qwen-possessive-audit.json").read_text())
    assert result["verified_records"] == 6144
    assert result["decision"] == "no_clear_possessive_specificity"


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("two_sided_sign_flip_p", 0.01, "Sign-flip p mismatch"),
        ("ci95", [0.001, 0.05], "Bootstrap interval mismatch"),
        ("positive_scenarios", 12, "Positive scenario count mismatch"),
        ("n_clusters", 256, "Independent unit/observation count mismatch"),
    ],
)
def test_rejects_altered_primary_inference(auditor, field, value, message):
    primary = json.loads(Path("review/qwen-possessive-audit.json").read_text())[
        "primary_interaction"
    ]
    # All scenarios have 16 matched sextets. Their recorded means suffice to
    # reproduce this equal-sized cluster bootstrap, without resampling variants.
    clusters = {s: [v] * 16 for s, v in primary["scenario_means"].items()}
    changed = deepcopy(primary)
    changed[field] = value
    with pytest.raises(ValueError, match=message):
        auditor.check_stat(changed, clusters, paired=True, primary=True)
