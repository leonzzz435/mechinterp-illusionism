"""Retrospective estimates must not alter records or turn failed controls into success."""

import importlib.util
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import ttest_1samp


@pytest.fixture(scope="module")
def supplement():
    path = Path(__file__).resolve().parents[1] / "scripts/analyze_query_sensitivity.py"
    spec = importlib.util.spec_from_file_location("query_sensitivity", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report(supplement):
    return supplement.analyze()


def candidates(greedy=(False, True, False)):
    return [
        {"command": name, "log_likelihood": score, "native_is_greedy": flag}
        for name, score, flag in zip(("a", "b", "c"), (-1.0, -1.0, -2.0), greedy)
    ]


def test_policy_is_answer_blind_order_invariant_and_does_not_mutate(supplement):
    source = candidates()
    original = deepcopy(source)
    for rotation in range(3):
        rotated = source[rotation:] + source[:rotation]
        assert supplement.resolve_selection(rotated)["selected_command"] == "b"
    assert source == original
    for c in source:
        c["reference_answer"] = "a"
    assert supplement.resolve_selection(source)["selected_command"] == "b"


@pytest.mark.parametrize("flags", [(False, False, True), (True, True, False)])
def test_nonunique_greedy_maximum_remains_unresolved(supplement, flags):
    resolved = supplement.resolve_selection(candidates(flags))
    assert resolved["score_tie"] and not resolved["resolved"]
    assert resolved["selected_command"] is None


def test_near_tie_keeps_unique_maximum_even_if_other_candidate_is_greedy(supplement):
    source = candidates()
    source[1]["log_likelihood"] = np.nextafter(-1.0, -np.inf).item()
    resolved = supplement.resolve_selection(source)
    assert resolved["selected_command"] == "a" and not resolved["score_tie"]


@pytest.mark.parametrize("score", [None, float("nan"), float("inf")])
def test_invalid_scores_never_become_valid_through_tie_policy(supplement, score):
    source = candidates()
    source[0]["log_likelihood"] = score
    with pytest.raises(ValueError, match="Invalid/nonfinite"):
        supplement.resolve_selection(source)


def test_missing_boolean_metadata_cannot_choose_an_answer(supplement):
    source = candidates()
    source[1]["native_is_greedy"] = "true"
    with pytest.raises(ValueError, match="Missing greedy flag"):
        supplement.resolve_selection(source)


def test_world_statistics_match_independent_t_and_bootstrap_calculation(supplement):
    values = np.arange(47) / 100 - 0.17
    vectors = {"E": values, "F": values * -0.4, "S": values + 0.3}
    result, _ = supplement.world_statistics(vectors)
    draws = np.random.default_rng(1729).choice(47, size=(10000, 47), replace=True)
    for name, xs in vectors.items():
        independent = ttest_1samp(xs, 0)
        assert result[name]["df"] == 46
        assert result[name]["raw_p"] == pytest.approx(independent.pvalue)
        assert result[name]["t"] == pytest.approx(independent.statistic)
        expected = np.percentile(np.average(xs[draws], axis=1), [2.5, 97.5])
        assert result[name]["ci95"] == pytest.approx(expected)
    ordered = sorted(result, key=lambda k: result[k]["raw_p"])
    expected_holm = np.maximum.accumulate(
        [result[name]["raw_p"] * (3 - i) for i, name in enumerate(ordered)]
    ).clip(0, 1)
    assert [result[k]["holm_p"] for k in ordered] == pytest.approx(expected_holm)


def test_unresolved_and_degenerate_statistics_remain_explicit(supplement):
    vectors = {name: [0.25] * 48 for name in ("E", "F", "S")}
    constant, _ = supplement.world_statistics(vectors)
    unresolved, _ = supplement.world_statistics(vectors, eligible=False)
    for name in vectors:
        assert constant[name]["raw_p"] is None
        assert constant[name]["test_status"] == "zero_variance"
        assert constant[name]["holm_placeholder"]
        assert unresolved[name]["ci95"] is None and unresolved[name]["raw_p"] is None


def test_evidence_changes_fail_before_archive_loading(supplement, tmp_path):
    changed = tmp_path / "changed.tar.gz"
    changed.write_bytes(b"changed evidence")
    with pytest.raises(ValueError, match="Evidence archive hash changed"):
        supplement.verified_payloads(changed, supplement.ARCHIVE_SHAS[0])


def test_whole_world_exclusion_preserves_clusters_and_expected_mean(report):
    excluded = report["variants"]["exclude_world_0011"]
    assert excluded["n_worlds"] == 47 and excluded["recorded_choices"] == 47 * 336
    assert "query-self-v1:0011" not in excluded["worlds"]
    for name in ("E", "F", "S"):
        original = report["frozen_v1_primary"][name]["world_contrasts"]
        expected = np.mean(original[:11] + original[12:])
        assert excluded["primary"][name]["estimate"] == pytest.approx(expected)
        assert excluded["primary"][name]["df"] == 46
    assert excluded["cells"]["after_both/self/possessive"]["scheduled"] == 47 * 32


def test_both_tie_assignments_bounded_and_gate_failure_preserved(report):
    v2 = report["variants"]["v2_stored_greedy"]
    other = report["variants"]["other_tied_command"]
    assert report["tie"]["resolution"]["selected_command"] == "mark_ochre"
    assert report["tie"]["derived_category"] == "correct_target_current"
    assert report["frozen_v1_valid_worlds"] == 47
    assert report["frozen_v1_decision"] == "incomplete_or_invalid_no_inference"
    for v in (v2, other):
        assert v["n_worlds"] == 48 and v["recorded_choices"] == 16128
        assert v["analysis_decision"] == "lookup_gate_failed"
        assert not v["lookup_numerical_pass"]
    assert v2["lookup_cells"] == other["lookup_cells"]
    assert v2["lookup_pairs"] == other["lookup_pairs"]
    for name in ("E", "F", "S"):
        assert other["primary"][name]["estimate"] - v2["primary"][name][
            "estimate"
        ] == pytest.approx(1 / 1536)
    assert report["frozen_v1_primary"]["F"]["ci95"] is None
    assert report["frozen_v1_cells"]["after_both/self/possessive"]["counts"]["invalid"] == 1


def test_full_sample_math_agrees_with_frozen_functions(report):
    from self_model_study.query_reference_analysis import primary_tests

    primary = report["variants"]["v2_stored_greedy"]["primary"]
    reference = primary_tests({k: v["world_contrasts"] for k, v in primary.items()}, True)
    for name, value in primary.items():
        for field in ("estimate", "ci95", "raw_p", "holm_p"):
            assert value[field] == pytest.approx(reference[name][field])


def test_full_error_inventory_does_not_reuse_block00_counts(report):
    for form, stale in (("possessive", 20), ("owner_name", 125), ("account_name", 21)):
        counts = report["frozen_v1_cells"][f"after_both/self/{form}"]["counts"]
        assert counts["revoked_target"] + counts["revoked_other"] == stale


def test_outputs_are_deterministic_and_label_exploration(supplement, report, tmp_path):
    for sub in ("one", "two"):
        supplement.write_outputs(report, tmp_path / sub)
    for name in (
        "analysis.json",
        "report.md",
        "sensitivity.svg",
        "sensitivity.pdf",
        "sensitivity.png",
    ):
        assert (tmp_path / "one" / name).read_bytes() == (tmp_path / "two" / name).read_bytes()
    assert "Exploratory" in (tmp_path / "one/report.md").read_text()
