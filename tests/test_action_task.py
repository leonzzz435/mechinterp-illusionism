"""Executable task semantics and controls; no pretrained model or paid calls."""

from collections import Counter, defaultdict
from copy import deepcopy

import pytest

from self_model_study.action_task import (
    VIEWS,
    apply_update,
    build_design,
    design_summary,
    execute,
    export_design,
    model_input,
    score_command,
)
from self_model_study.cli import main
from self_model_study.io import file_hash, read_json


def test_deterministic_development_only_design():
    rows = build_design(scenarios=2)
    assert rows == build_design(scenarios=2)
    assert len(rows) == 192
    assert len({r["id"] for r in rows}) == len(rows)
    assert {r["split"] for r in rows} == {"development"}
    assert {r["scenario_id"] for r in rows}.isdisjoint(
        r["scenario_id"] for r in build_design(seed=1730, scenarios=2)
    )
    for split in ("validation", "test"):
        with pytest.raises(ValueError, match="development only"):
            build_design(split=split)
    for count in (0, 41, True):
        with pytest.raises(ValueError, match="1–40"):
            build_design(scenarios=count)


def test_commands_really_execute_or_fail_without_mutating_inputs():
    for row in build_design(scenarios=2):
        original = deepcopy(row)
        successes = []
        for command in row["choices"] + ["A", "", "invented_command", {"actor": "Birch"}]:
            result = score_command(row, command)
            assert result["actor"] == row["target"]
            if result["correct"]:
                successes.append(command)
                assert result["state_after"]["markers"][row["target"]] == 1
                for actor in row["state"]["markers"]:
                    if actor != row["target"]:
                        assert result["state_after"]["markers"][actor] == 0
            else:
                assert result["state_after"] == row["state"]
        assert successes == [row["expected_command"]]
        assert row == original
    with pytest.raises(ValueError, match="Unknown executor"):
        execute(row["state"], "unknown", row["expected_command"])
    event = {**row["event"], "revoke": "not_the_current_permission"}
    with pytest.raises(ValueError, match="current permission"):
        apply_update(row["before"], event)


def test_relevant_updates_flip_actions_and_other_updates_preserve_them():
    rows = build_design(scenarios=3)
    lookup = {
        (r["scenario_id"], r["updated"], r["identity"], r["view"], r["phase"], r["rotation"]): r
        for r in rows
    }
    for row in rows:
        if row["phase"] != "after":
            continue
        before = lookup[
            (
                row["scenario_id"],
                row["updated"],
                row["identity"],
                row["view"],
                "before",
                row["rotation"],
            )
        ]
        assert (row["expected_command"] != before["expected_command"]) == row["relevant_update"]
        stale = score_command(row, before["expected_command"])
        assert stale["accepted"] is not row["relevant_update"]
        assert "Revoke " not in before["prompt"]
        assert "Revoke " in row["prompt"]


def test_views_and_rotations_are_matched_with_exact_executor_binding():
    groups = defaultdict(list)
    for row in build_design(scenarios=2):
        key = (row["scenario_id"], row["updated"], row["identity"], row["phase"])
        groups[key].append(row)
        assert set(model_input(row)) == {"id", "prompt", "choices", "language_prompt"}
        assert row["expected_command"] not in row["id"]
    for group in groups.values():
        for view in VIEWS:
            subset = [r for r in group if r["view"] == view]
            assert Counter(r["expected_position"] for r in subset) == dict.fromkeys(range(4), 1)
            assert len({r["expected_command"] for r in subset}) == 1
        self_row, named, other = [next(r for r in group if r["view"] == v) for v in VIEWS]
        assert self_row["target"] == named["target"] == self_row["assigned"]
        assert other["target"] != other["assigned"]
        assert self_row["expected_command"] == named["expected_command"]
        assert self_row["expected_command"] != other["expected_command"]
        assert self_row["state"] == named["state"] == other["state"]


def test_shortcuts_fail_despite_a_perfect_simulator_oracle():
    report = design_summary(build_design(scenarios=4))
    assert report["simulator_oracle_accuracy"] == 1
    assert report["model_evidence"] is report["confirmation_eligible"] is False
    for view in VIEWS:
        checks = report["scripted_shortcut_accuracy_by_view"][view]
        assert checks["first_listed"] == 0.25
        assert checks["ignore_update"] == 0.75
        assert (
            report["scripted_shortcut_accuracy_after_relevant_update"][view]["ignore_update"] == 0
        )
        assert (
            report["scripted_shortcut_accuracy_after_relevant_update"][view][
                "latest_grant_or_first"
            ]
            == 1
        )
        assert (
            report["scripted_shortcut_accuracy_after_irrelevant_update"][view][
                "latest_grant_or_first"
            ]
            == 0
        )
    assert report["scripted_shortcut_accuracy_by_view"]["other"]["always_active_actor"] == 0


def test_export_cli_checksums_and_no_overwrite(tmp_path, capsys):
    output = tmp_path / "design"
    assert main(["design", "--out", str(output), "--scenarios", "1"]) == 0
    manifest = read_json(output / "manifest.json")
    assert manifest["model_evidence"] is False
    assert "task_design_only" in capsys.readouterr().out
    for name, checksum in manifest["files"].items():
        assert file_hash(output / name) == checksum
    for suffix in ("svg", "pdf", "png"):
        assert (output / f"action_design.{suffix}").stat().st_size > 1000
    assert "TASK DESIGN ONLY" in (output / "action_design.svg").read_text()
    with pytest.raises(ValueError, match="new or empty"):
        export_design(output, scenarios=1)
