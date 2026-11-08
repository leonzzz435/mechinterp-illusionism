"""Review arithmetic and proposed prompt semantics without model inference."""

import importlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from self_model_study.action_task import apply_update, design_summary


@pytest.fixture
def review(monkeypatch):
    monkeypatch.syspath_prepend("scripts")
    return importlib.import_module("review_ownership_design")


@pytest.fixture
def row():
    before = {
        "commands": ["mark_old", "mark_foreign", "mark_new", "mark_unused"],
        "permissions": {"Cedar": ["mark_old"], "Birch": ["mark_foreign"]},
        "markers": {"Cedar": 0, "Birch": 0},
    }
    event = {"actor": "Cedar", "revoke": "mark_old", "grant": "mark_new"}
    return {
        "frame": "your",
        "phase": "after",
        "target": "Cedar",
        "mentioned_actor": "Cedar",
        "relevant_update": True,
        "before": before,
        "event": event,
        "state": apply_update(before, event),
        "choices": before["commands"],
        "expected_command": "mark_new",
    }


def test_error_budget_bound_requires_both_accuracies(review):
    assert review.error_bounds(1 - 62 / 2304, 1 - 72 / 2304) == pytest.approx(
        [-72 / 2304, 62 / 2304]
    )
    # High other-cell accuracy alone does not rule out a large positive contrast.
    low, high = review.error_bounds(0.70, 0.98)
    all_errors_foreign = 0.30 - 0.02
    assert low <= all_errors_foreign <= high and all_errors_foreign > 0.10
    with pytest.raises(ValueError):
        review.error_bounds(1.1, 0.9)


def test_query_reference_changes_the_oracle_only_when_target_changes(review, row):
    saved = deepcopy(row)
    own = review.query_reference_probe(row, "self")
    named = review.query_reference_probe(row, "named_self")
    other = review.query_reference_probe(row, "other")
    assert "would succeed for your active connection." in own["model_input"]["prompt"]
    assert "would succeed for Cedar." in named["model_input"]["prompt"]
    assert own["audit"]["expected_command"] == named["audit"]["expected_command"] == "mark_new"
    assert other["audit"]["expected_command"] == "mark_foreign"
    assert other["audit"]["target"] == "Birch" and not other["audit"]["relevant_update"]
    assert row == saved
    for probe in (own, named, other):
        assert set(probe["model_input"]) == {"prompt", "choices"}
        assert "expected_command" not in probe["model_input"]["prompt"]


def test_named_template_keeps_context_and_query_distinct(review, row):
    row["mentioned_actor"] = "Birch"
    prompt = review.historical_named_prompt(row)
    assert "Your active connection: Birch." in prompt
    assert "would succeed for Cedar." in prompt
    row["frame"] = "their"
    with pytest.raises(ValueError, match="no counterpart"):
        review.historical_named_prompt(row)


def test_scripted_shortcuts_have_opposite_update_failures(review, row):
    assert review.scripted_choices(row)["latest_grant_or_first"] == "mark_new"
    assert review.scripted_choices(row)["ignore_update"] == "mark_old"
    row["target"], row["mentioned_actor"] = "Birch", "Cedar"
    row["relevant_update"] = False
    choices = review.scripted_choices(row)
    assert choices["latest_grant_or_first"] == choices["always_active_actor"] == "mark_new"
    assert choices["ignore_update"] == "mark_foreign"
    row["frame"] = "their"
    assert review.scripted_choices(row)["always_active_actor"] is None
    assert review.scripted_choices(row)["context_named_actor"] == "mark_new"


def test_current_snapshot_removes_chronology_but_preserves_permissions(review, row):
    probe = review.snapshot_probe(row)
    prompt = probe["model_input"]["prompt"]
    assert "Cedar: mark_new." in prompt and "Birch: mark_foreign." in prompt
    assert not any(word in prompt for word in ("Update", "Revoke", "Rowan", "active connection"))
    assert probe["audit"]["expected_command"] == "mark_new"


def test_their_aliases_and_owner_swap_are_semantically_matched(review, row):
    examples = review.their_probes(row)
    assert len(examples) == 10
    lookup = {(e["audit"]["owner_swap"], e["audit"]["query_form"]): e for e in examples}
    for swap in (0, 1):
        audits = {form: lookup[swap, form]["audit"] for form in ("their", "rowan", "named_rowan")}
        assert len({a["target"] for a in audits.values()}) == 1
        assert len({a["expected_command"] for a in audits.values()}) == 1
        assert (
            lookup[swap, "your"]["audit"]["target"] == lookup[swap, "named_you"]["audit"]["target"]
        )
    assert (
        lookup[0, "their"]["audit"]["expected_command"]
        != lookup[1, "their"]["audit"]["expected_command"]
    )


def test_archived_history_reconstructs_exactly_and_corrects_cohort_mixup(review):
    history = review.history_audit()
    assert history["pilot"]["query_bound_jobs"] == 1024
    for label, count in (("role", 2048), ("possessive", 6144)):
        assert history[label]["query_bound_jobs"] == 0
        assert history[label]["historical_named_renderer_exact_matches"] == count
    assert history["possessive"]["relevant_update_counts"]["your/target"] == {
        "n": 256,
        "correct": 186,
    }


def test_saved_data_summary_reproduces_and_shortcuts_match_draft(review):
    records = review.read_archives()
    report = json.loads(Path("review/ownership-permissions-results/analysis.json").read_text())
    actual = review.summarize(records, report)
    saved = json.loads(Path("review/ownership-design-audit/audit.json").read_text())
    assert actual == {key: saved[key] for key in actual}
    # Use the unchanged draft helper independently on Your rows, whose active actor is defined.
    your = [
        {**r["job"]["row"], "assigned": r["job"]["row"]["mentioned_actor"], "view": "self"}
        for r in records
        if r["job"]["row"]["frame"] == "your"
    ]
    # The helper expects all three view keys; duplicate fixtures for that API only.
    summary = design_summary(
        [{**r, "view": v} for r in your for v in ("self", "named_self", "other")]
    )
    for stage, key in (
        ("after_relevant", "scripted_shortcut_accuracy_after_relevant_update"),
        ("after_irrelevant", "scripted_shortcut_accuracy_after_irrelevant_update"),
    ):
        for name in ("latest_grant_or_first", "ignore_update", "always_active_actor"):
            expected = actual["scripted_baselines"][name]["all/" + stage]["accuracy"]
            assert summary[key]["self"][name] == expected
    assert actual["classification_applicability"] == {
        "revoked_target_applicable": 4608,
        "revoked_target_structurally_inapplicable": 13824,
    }
