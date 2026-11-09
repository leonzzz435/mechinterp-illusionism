"""An order-conditioned error count must retain every selection and contrast definition."""

import importlib.util
import json
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def counter():
    path = Path(__file__).resolve().parents[1] / "scripts/count_query_order_errors.py"
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("query_order_errors", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def result(counter):
    return counter.analyze()


def test_order_categories_match_independent_state_lookup(counter, result):
    # Use archived simulator state, not the text parser/category helper under test.
    expected = defaultdict(Counter)
    for record in counter.load_records():
        row = record["job"]["row"]
        if row["stage"] != "after_both":
            continue
        command = record["result"]["selected_command"]
        target = row["target"]
        permissions = row["state"]["permissions"]
        other = next(actor for actor in permissions if actor != target)
        order = "target_last" if row["events"][-1]["actor"] == target else "target_first"
        if command is None:
            category = "invalid"
        elif command == permissions[target][0]:
            category = "correct_target_current"
        elif command == permissions[other][0]:
            category = "other_account_current"
        elif command == row["before"]["permissions"][target][0]:
            category = "revoked_target"
        else:
            assert command == row["before"]["permissions"][other][0]
            category = "revoked_other"
        expected[f"{row['queried_owner']}/{row['query_form']}/{order}"][category] += 1
    cells = result["variants"]["frozen_v1"]["cells"]
    assert set(expected) == set(cells)
    for key, counts in expected.items():
        assert cells[key]["counts"] == {
            category: counts[category] for category in counter.CATEGORIES
        }
        assert sum(counts.values()) == 768


def test_original_counts_partition_every_choice_and_reproduce_pooled_categories(counter, result):
    original = json.loads(
        (counter.ROOT / "review/query-reference-results/analysis.json").read_text()
    )
    cells = result["variants"]["frozen_v1"]["cells"]
    for owner in counter.OWNERS:
        for form in counter.FORMS:
            a, b = [cells[f"{owner}/{form}/{order}"] for order in ("target_first", "target_last")]
            pooled = original["cells"][f"after_both/{owner}/{form}"]
            for category in counter.CATEGORIES:
                assert a["counts"][category] + b["counts"][category] == pooled["counts"][category]
            assert (
                Fraction(a["counts"]["correct_target_current"], a["n"])
                + Fraction(b["counts"]["correct_target_current"], b["n"])
            ) / 2 == Fraction(pooled["counts"]["correct_target_current"], pooled["scheduled"])
    own = [cells[f"self/possessive/{order}"] for order in ("target_first", "target_last")]
    assert sum(c["first_grant_agreement"] for c in own) == 1064
    assert sum(c["latest_grant_agreement"] for c in own) == 451
    assert 1536 - 1064 - 451 == 20 + 1


def test_world_signs_have_correct_scope_and_no_tolerance(counter, result):
    assert counter.sign_counts([Fraction(-1, 10**100), 0, Fraction(1, 10**100)]) == {
        "negative": 1,
        "positive": 1,
        "zero": 1,
    }
    saved = json.loads(counter.STAGES.read_text())
    for variant, view in result["variants"].items():
        for name, signs in view["signs"].items():
            values = saved["variants"][variant]["contrasts"][name]["world_values"]
            assert signs["negative"] == len([v for v in values if v < 0])
            assert signs["positive"] == len([v for v in values if v > 0])
            assert signs["zero"] == values.count(0)
            assert sum(signs[k] for k in ("negative", "positive", "zero")) == view["n_worlds"]
    own = result["variants"]["v2_stored_greedy"]["signs"][counter.CONTRASTS[0]]
    assert (own["negative"], own["positive"], own["zero"]) == (37, 8, 3)
    interaction = result["variants"]["v2_stored_greedy"]["signs"][counter.CONTRASTS[1]]
    assert (interaction["negative"], interaction["positive"], interaction["zero"]) == (34, 8, 6)


def test_latest_policy_reverses_with_target_order_and_tie_stays_visible(result):
    for view in result["variants"].values():
        for key, cell in view["cells"].items():
            target_last = key.endswith("target_last")
            assert cell["latest_grant_correct"] == (cell["n"] if target_last else 0)
            assert cell["foreign_is"] == ("first_grant" if target_last else "latest_grant")
            assert (
                cell["first_grant_agreement"]
                + cell["latest_grant_agreement"]
                + cell["counts"]["revoked_target"]
                + cell["counts"]["revoked_other"]
                + cell["counts"]["invalid"]
            ) == cell["n"]
    raw = result["variants"]["frozen_v1"]["cells"]["self/possessive/target_first"]
    derived = result["variants"]["v2_stored_greedy"]["cells"]["self/possessive/target_first"]
    assert raw["counts"]["invalid"] == 1 and derived["counts"]["invalid"] == 0
    assert raw["errors_including_invalid"] == 151 and derived["errors_including_invalid"] == 150


def test_saved_stage_change_is_rejected_before_loading_archives(counter, tmp_path, monkeypatch):
    changed = tmp_path / "analysis.json"
    changed.write_text("{}")
    monkeypatch.setattr(counter, "STAGES", changed)
    with pytest.raises(ValueError, match="stage analysis changed"):
        counter.analyze()


def test_deterministic_json_and_report(counter, result, tmp_path):
    counter.write_outputs(result, tmp_path / "first")
    counter.write_outputs(result, tmp_path / "second")
    for name in ("analysis.json", "report.md"):
        assert (tmp_path / "first" / name).read_bytes() == (tmp_path / "second" / name).read_bytes()
    assert "no_new_tests_or_decision" in (tmp_path / "first/analysis.json").read_text()
