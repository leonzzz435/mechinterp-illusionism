"""Second-implementation statistics and tamper rejection for confidence evidence."""

import importlib
import json
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from self_model_study.confidence_analysis import clustered_auc, interval, ratio


@pytest.fixture
def auditor(monkeypatch):
    monkeypatch.syspath_prepend("scripts")
    return importlib.import_module("review_confidence_evidence")


@pytest.fixture
def statistics():
    rng = np.random.default_rng(381)
    correct = rng.random((32, 4)) < np.linspace(0.2, 0.9, 32)[:, None]
    abstain = rng.random((32, 4)) < np.where(correct, 0.1, 0.6)
    confidence = (rng.integers(0, 5, (32, 4)) + 4 * correct + 0.5) / 10
    index = np.random.default_rng(1729).integers(0, 32, (10000, 32))
    wn, wd = ((~correct) & abstain).sum(1), (~correct).sum(1)
    rn, rd = (correct & abstain).sum(1), correct.sum(1)
    saved = {
        "primary": interval(
            ratio(wn.sum(), wd.sum()) - ratio(rn.sum(), rd.sum()),
            ratio(wn[index].sum(1), wd[index].sum(1)) - ratio(rn[index].sum(1), rd[index].sum(1)),
        ),
        "metrics": {"confidence_auroc": clustered_auc(correct, confidence, index)},
    }
    return saved, correct, abstain, confidence


def test_pairwise_auc_and_question_bootstrap_agree(auditor, statistics):
    auditor.check_candidate_statistics(*statistics)


@pytest.mark.parametrize(
    "key,value,message",
    [
        ("estimate", 0.99, "Estimate mismatch"),
        ("ci95", [0.9, 1.0], "Question-bootstrap interval"),
        ("undefined_bootstrap_draws", 1, "Undefined bootstrap count"),
    ],
)
def test_rejects_altered_candidate_statistics(auditor, statistics, key, value, message):
    saved, *arrays = statistics
    changed = deepcopy(saved)
    changed["primary"][key] = value
    with pytest.raises(ValueError, match=message):
        auditor.check_candidate_statistics(changed, *arrays)


def test_auditor_handles_undefined_primary_and_auc(auditor):
    absent = {"estimate": None, "ci95": None, "undefined_bootstrap_draws": 10000}
    auditor.check_candidate_statistics(
        {"primary": absent, "metrics": {"confidence_auroc": absent}},
        np.ones((8, 4), dtype=bool),
        np.zeros((8, 4), dtype=bool),
        np.full((8, 4), 0.95),
    )


def test_completed_real_confidence_archive(auditor):
    result = auditor.audit(
        "review/evidence/qwen-confidence-v2-4ea43316ce714c03.tar.gz",
        "ba8b0d01d31da9004758abacd054fbdf664ed235834bc5e7889ab5e3d6cb97dd",
    )
    assert result == json.loads(Path("review/qwen-confidence-audit.json").read_text())
    assert result["verified_records"] == 1792
    assert result["decision"] == "no_behavioral_candidate"
