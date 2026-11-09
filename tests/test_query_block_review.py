"""Keep interim observations distinct from a completed fixed-sample result."""

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def reviewer():
    path = Path(__file__).resolve().parents[1] / "scripts/review_query_block.py"
    spec = importlib.util.spec_from_file_location("query_block_reviewer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def reviewed(reviewer):
    return reviewer.audit(reviewer.OUT / "qwen-query-00-4edce03e18d645e7.tar.gz")


def test_complete_block_cannot_become_a_full_sample_success(reviewed):
    assert reviewed["recorded_choices"] == 2688
    assert reviewed["unrun_choices"] == 13440
    assert reviewed["valid_complete_worlds"] == 8
    assert reviewed["technical_errors"] == reviewed["ties"] == 0
    assert reviewed["decision"] == "incomplete_or_invalid_no_inference"
    assert reviewed["observed_block_effects"]["F"]["positive_worlds"] == 8
    for effect in reviewed["observed_block_effects"].values():
        assert effect["ci95"] is None and effect["p_value"] is None


def test_observed_denominators_and_structural_nulls_remain_explicit(reviewed):
    cell = reviewed["cells"]["after_both/self/possessive"]
    assert cell["correct"] == 137 and cell["n"] == 256
    assert cell["accuracy"] == 137 / 256
    assert cell["foreign"] == 114
    assert cell["counts"]["revoked_target"] == 3
    for stage in ("before", "snapshot"):
        counts = reviewed["cells"][f"{stage}/self/possessive"]["counts"]
        assert counts["revoked_target"] is None and counts["revoked_other"] is None
    pair = reviewed["observed_lookup_pairs"]["ownership/before/self/owner_name"]
    assert pair["both_correct"] == 11 and pair["n"] == 32
    assert pair["rate"] < 0.8 < pair["best_possible_full_sample_rate"]


def test_changed_archive_rejected_before_reading_records(reviewer, tmp_path):
    corrupted = tmp_path / "corrupted.tar.gz"
    corrupted.write_bytes(b"not the pinned evidence archive")
    with pytest.raises(ValueError, match="Archive hash changed"):
        reviewer.audit(corrupted)
