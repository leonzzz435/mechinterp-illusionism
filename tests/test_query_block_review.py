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


def test_accuracy_near_half_does_not_imply_latest_grant_policy(reviewed):
    for key, cell in reviewed["shortcut_comparison"].items():
        expected = 0.5 if key.startswith("after_both/") else 0.25
        assert cell["baseline_correct"] / cell["n"] == expected
    cell = reviewed["shortcut_comparison"]["after_both/self/possessive"]
    assert cell["model_correct"] == 137
    assert cell["model_agrees_with_policy"] == 55
    assert cell["first_grant_agreement_post_hoc"] == 196
    assert cell["by_last_updated"]["target"]["model_correct"] == 33
    assert cell["by_last_updated"]["other"]["model_correct"] == 104
    for world in reviewed["shortcut_comparison_per_world"].values():
        for key, c in world.items():
            if key.startswith("after_both/"):
                assert c["baseline_correct"] * 2 == c["n"]


def test_gate_remainder_uses_integer_threshold_and_separate_denominators(reviewer):
    before = reviewer.gate_remainder(11, 32, 192)
    assert before["required_correct_total"] == 154
    assert before["required_correct_remaining"] == 143
    assert before["remaining"] == 160
    assert before["required_remaining_rate"] == 143 / 160
    snapshot = reviewer.gate_remainder(31, 64, 384)
    assert snapshot["required_correct_total"] == 308
    assert snapshot["required_correct_remaining"] == 277
    assert snapshot["required_remaining_rate"] == 277 / 320


def test_error_types_do_not_identify_internal_mechanisms(reviewed):
    cell = reviewed["cells"]["after_both/self/owner_name"]
    assert cell["n"] - cell["correct"] == 106
    assert cell["foreign"] == 69
    assert cell["counts"]["revoked_target"] == 27
    assert cell["counts"]["revoked_other"] == 10
    assert (
        reviewed["cells"]["snapshot/self/possessive"]["accuracy"]
        > reviewed["cells"]["snapshot/self/owner_name"]["accuracy"]
    )


def test_full_sample_statistics_do_not_override_failed_lookup_gate():
    from self_model_study.query_reference_analysis import decision, primary_tests

    # Pure mathematical fixture, not additional or extrapolated model responses.
    vectors = {name: [0.1 + i / 1000 for i in range(48)] for name in ("E", "F", "S")}
    primary = primary_tests(vectors, eligible=True)
    for effect in primary.values():
        assert effect["ci95"] is not None and effect["raw_p"] is not None
        assert effect["qualifies"]
    assert decision(primary, eligible=True, gates=False, synthetic=False) == "lookup_gate_failed"
