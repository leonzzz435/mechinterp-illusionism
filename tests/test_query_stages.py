"""Saved-data stage comparisons must preserve pairing, policy scope and failed gates."""

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture(scope="module")
def stage_module():
    path = Path(__file__).resolve().parents[1] / "scripts/analyze_query_stages.py"
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("query_stages", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def records(stage_module):
    return stage_module.load_records()


@pytest.fixture(scope="module")
def analysis(stage_module):
    return stage_module.analyze()


def test_counts_reproduce_original_cells_without_inferring_through_tie(stage_module, analysis):
    original = json.loads((stage_module.EVIDENCE / "analysis.json").read_text())
    frozen = analysis["variants"]["frozen_v1"]
    assert frozen["n"] == 16128
    assert len(frozen["cells"]) == 18
    for key, cell in frozen["cells"].items():
        assert cell["correct"] == original["cells"][key]["counts"]["correct_target_current"]
        assert cell["accuracy"]["ci95"] is None
    assert original["decision"] == "incomplete_or_invalid_no_inference"


def test_shortcut_scope_is_not_global_chance(analysis):
    for variant in analysis["variants"].values():
        for key, policies in variant["baselines"].items():
            if key.startswith("after_both/"):
                assert policies["latest_grant_only"]["accuracy"] == 0.5
                assert policies["ignore_update"]["accuracy"] == 0
            else:
                assert policies["latest_grant_only"]["accuracy"] is None
                assert policies["latest_grant_only"]["applicable"] == 0
                assert policies["latest_grant_or_first"]["accuracy"] == 0.25
                assert policies["first_grant_only"]["agreement"] is None
            if key.startswith("before/"):
                assert policies["ignore_update"]["accuracy"] == 1
            if key.startswith("snapshot/"):
                assert policies["ignore_update"]["accuracy"] is None


def test_snapshot_and_history_share_final_state_and_key(stage_module, records):
    lookup = {}
    for record in records:
        row = record["job"]["row"]
        key = (
            row["world_id"],
            row["connection_assignment"],
            row.get("grant_mapping"),
            row["option_rotation"],
            row["queried_owner"],
            row["query_form"],
        )
        if row["stage"] == "snapshot":
            lookup[key] = row
    count = 0
    for record in records:
        row = record["job"]["row"]
        if row["stage"] != "after_both":
            continue
        key = (
            row["world_id"],
            row["connection_assignment"],
            row["grant_mapping"],
            row["option_rotation"],
            row["queried_owner"],
            row["query_form"],
        )
        snap = lookup[key]
        assert snap["state"] == row["state"]
        assert snap["expected_command"] == row["expected_command"]
        assert snap["choices"] == row["choices"]
        count += 1
    assert count == 9216


def test_world_paired_interaction_and_bootstrap_match_independent_raw_counts(analysis, records):
    # Independently aggregate raw stored decisions; no parser, audit helpers or saved vectors.
    counts = {}
    for record in records:
        row = record["job"]["row"]
        if row["world_id"] == "query-self-v1:0011" or row["query_form"] != "possessive":
            continue
        key = (row["world_id"], row["stage"], row["queried_owner"])
        counts.setdefault(key, []).append(
            record["result"]["selected_command"] == row["expected_command"]
        )
    values = []
    for world in sorted({k[0] for k in counts}):
        values.append(
            np.average(counts[world, "after_both", "self"])
            - np.average(counts[world, "snapshot", "self"])
            - np.average(counts[world, "after_both", "other"])
            + np.average(counts[world, "snapshot", "other"])
        )
    actual = analysis["variants"]["exclude_world_0011"]["contrasts"][
        "after_minus_snapshot/possessive/self_minus_other"
    ]
    indices = np.random.default_rng(1729).choice(47, size=(10000, 47), replace=True)
    intervals = np.percentile(np.array(values)[indices].mean(axis=1), [2.5, 97.5])
    assert actual["estimate"] == pytest.approx(np.mean(values))
    assert actual["ci95"] == pytest.approx(intervals)
    assert actual["world_values"] == values


def test_two_tie_assignments_change_one_selection_and_no_lookup_cell(analysis):
    a, b = (analysis["variants"][k] for k in ("v2_stored_greedy", "other_tied_command"))
    changed = [k for k in a["cells"] if a["cells"][k]["correct"] != b["cells"][k]["correct"]]
    assert changed == ["after_both/self/possessive"]
    assert a["cells"][changed[0]]["correct"] - b["cells"][changed[0]]["correct"] == 1
    excluded = analysis["variants"]["exclude_world_0011"]
    assert excluded["n"] == 47 * 336
    assert "query-self-v1:0011" not in excluded["worlds"]


def test_order_pair_counts_match_original_paired_controls(stage_module, analysis):
    frozen = json.loads((stage_module.EVIDENCE / "analysis.json").read_text())
    for key, orders in analysis["variants"]["frozen_v1"]["event_orders"].items():
        control = frozen["paired_controls"][f"event_order/after_both/{key}"]
        assert orders["pairs"] == 768
        # Check actual exported schema and independent count against raw published count.
        assert orders["both_correct"] / orders["pairs"] == control["fully_correct_rate"]


def test_prompt_metadata_mismatch_fails_without_mutating_input(stage_module, records):
    record = deepcopy(records[0])
    original = deepcopy(record)
    stage_module.audit_record(record, "frozen_v1")
    assert record == original
    record["job"]["row"]["target"] = "Nonexistent"
    with pytest.raises(ValueError, match="metadata disagree"):
        stage_module.audit_record(record, "frozen_v1")


def test_example_is_disclosed_and_complete(analysis):
    ex = analysis["example"]
    assert ex["selection_status"].startswith("post_hoc")
    assert len(ex["records"]) == 24
    assert len({r["id"] for r in ex["records"]}) == 24
    opening = next(r for r in ex["records"] if r["id"] == ex["opening_record_id"])
    assert opening["result"]["selected_command"] != opening["job"]["row"]["expected_command"]
    assert sum(r["job"]["row"]["stage"] == "after_both" for r in ex["records"]) == 12


def test_exports_are_deterministic(stage_module, analysis, tmp_path):
    stage_module.write_outputs(analysis, tmp_path / "a")
    stage_module.write_outputs(analysis, tmp_path / "b")
    assert {p.name for p in (tmp_path / "a").iterdir()} == {
        p.name for p in (tmp_path / "b").iterdir()
    }
    for path in (tmp_path / "a").iterdir():
        assert path.read_bytes() == (tmp_path / "b" / path.name).read_bytes()
