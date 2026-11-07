from collections import Counter, defaultdict
from copy import deepcopy

import pytest

from self_model_study import pilot
from self_model_study import role_control as control
from self_model_study.action_task import score_command
from self_model_study.cli import main
from self_model_study.io import digest, read_json, source_hash, write_json
from self_model_study.pilot import jobs_in
from self_model_study.role_control_analysis import decision, sign_flip, summarize
from self_model_study.role_control_reporting import export
from self_model_study.storage import read_records


@pytest.fixture(scope="module")
def plan():
    return control.build_plan(control.DEFAULT_SPEC)


def fixture_records(plan, pattern="specific"):
    """Explicit synthetic outcomes, never model data or a backend with oracle access."""
    records = []
    for job in jobs_in(plan):
        row = job["row"]
        wrong = (
            control.stratum(row) == "after_relevant"
            and row["relation"] == "target"
            and row["rotation"] == 0
            and (pattern == "shared" or row["frame"] == "active")
        )
        chosen = (
            next(c for c in row["choices"] if c != row["expected_command"])
            if wrong
            else row["expected_command"]
        )
        records.append(
            {"id": job["id"], "status": "ok", "result": {"execution": score_command(row, chosen)}}
        )
    return records


def fixture_manifest(synthetic=True):
    return {
        "config": control.DEFAULT_SPEC,
        "protocol": control.PROTOCOL,
        "run_id": "synthetic-role-control",
        "synthetic": synthetic,
        "status": "complete",
        "provenance": {"source_hash": source_hash()},
    }


def test_frozen_four_way_design_separation_and_no_answer_leak(plan):
    jobs = jobs_in(plan)
    assert digest(plan) == control.FROZEN_PLAN_HASH
    assert plan == control.build_plan(control.DEFAULT_SPEC)
    assert len(jobs) == len({j["id"] for j in jobs}) == 2048
    assert len({j["row"]["scenario_id"] for j in jobs}) == 8
    assert {int(j["row"]["scenario_id"].rsplit(":", 1)[1]) for j in jobs} == set(range(8, 16))
    old = jobs_in(pilot.build_plan(pilot.DEFAULT_SPEC))
    assert {j["id"] for j in jobs}.isdisjoint(j["id"] for j in old)
    grouped, order = defaultdict(list), Counter()
    for block in plan["blocks"]:
        for i, j in enumerate(block["jobs"]):
            row = j["row"]
            grouped[row["scene_id"]].append(row)
            order[(block["id"], row["frame"], row["relation"], i % 4)] += 1
            assert "assigned" not in row and "language_prompt" not in row
            assert f"Select one command that would succeed for {row['target']}." in row["prompt"]
            for word in ("expected_command", "grant_variant", "target_identity", "scene_id"):
                assert word not in row["prompt"]
    assert len(grouped) == 512 and set(order.values()) == {16}
    assert Counter(j["row"]["expected_position"] for j in jobs) == {i: 512 for i in range(4)}
    for rows in grouped.values():
        assert {(r["frame"], r["relation"]) for r in rows} == set(control.CONDITIONS)
        assert len({r["expected_command"] for r in rows}) == 1
        normalized = set()
        for row in rows:
            line = control.DEFAULT_SPEC["context_lines"][row["frame"]].format(
                actor=row["mentioned_actor"]
            )
            assert row["prompt"].count(line) == 1
            normalized.add(row["prompt"].replace(line, "<CONTEXT>"))
            assert score_command(row, row["expected_command"])["correct"]
        assert len(normalized) == 1
    # History-dependent answers change with the grant while the framing quartet does not.
    grants = defaultdict(set)
    for j in jobs:
        r = j["row"]
        if control.stratum(r) == "after_relevant":
            grants[(r["scenario_id"], r["target"], r["rotation"])].add(r["expected_command"])
    assert all(len(values) == 2 for values in grants.values())


def test_frozen_fields_and_design_only_cli(tmp_path):
    for key, value in (
        ("scenarios", list(range(8))),
        ("score", "mean_log_likelihood"),
        ("max_seconds", True),
        ("decision", {}),
    ):
        with pytest.raises(ValueError):
            control.validate_spec({**control.DEFAULT_SPEC, key: value})
    design = tmp_path / "design"
    assert main(["validate", "configs/qwen-role-control.json", "--freeze", str(design)]) == 0
    assert read_json(design / "manifest.json")["status"] == "design_only"
    assert not (design / "trials.sqlite").exists()
    with pytest.raises(ValueError, match="not a model run"):
        control.read_run(design)
    with pytest.raises(ValueError, match="not a model run"):
        control.run(control.DEFAULT_SPEC, design, backend_factory=stub_factory)
    first, second = tmp_path / "first.tar.gz", tmp_path / "second.tar.gz"
    assert export(design, first)["status"] == "design_only"
    export(design, second)
    assert first.read_bytes() == second.read_bytes()
    inputs = read_json(design / "model_inputs.json")
    inputs[0]["prompt"] += " Answer: hidden oracle."
    write_json(design / "model_inputs.json", inputs)
    with pytest.raises(ValueError, match="model inputs changed"):
        export(design, tmp_path / "corrupt.tar.gz")


def test_interaction_not_merely_a_role_gap_and_conservative_decision(plan):
    report = summarize(fixture_manifest(), plan, fixture_records(plan))
    assert report["decision"] == "synthetic_only" and report["controls_passed"]
    main_stat = report["interaction"]["after_relevant"]
    assert main_stat["estimate"] == 0.25
    assert main_stat["n_clusters"] == 8 and main_stat["n_observations"] == 128
    assert main_stat["two_sided_sign_flip_p"] == 2 / 256
    assert main_stat["positive_scenarios"] == 8
    # Exercise decision logic only. This fixture is never exported as model evidence.
    eligible = {**report, "synthetic": False}
    assert decision(eligible, control.DEFAULT_SPEC["decision"]) == "wording_sensitive_candidate"
    shared = summarize(fixture_manifest(), plan, fixture_records(plan, "shared"))
    assert shared["assignment_gaps"]["active/after_relevant"]["estimate"] == 0.25
    assert shared["interaction"]["after_relevant"]["estimate"] == 0
    assert shared["interaction"]["after_relevant"]["two_sided_sign_flip_p"] == 1
    assert decision({**shared, "synthetic": False}, control.DEFAULT_SPEC["decision"]) == (
        "stop_no_clear_wording_specificity"
    )
    assert not report["internal_intervention_authorized"]
    assert not report["original_capability_screen_changed"]
    for changes, expected in (
        ({"coverage_complete": False}, "incomplete"),
        ({"errors": 1}, "measurement_failure"),
        ({"controls_passed": False}, "stop_control_failure"),
        ({"same_source_as_execution": False}, "source_mismatch"),
    ):
        assert decision({**eligible, **changes}, control.DEFAULT_SPEC["decision"]) == expected
    # Only one nonzero scenario must not receive spurious 1/2048 precision.
    assert sign_flip({i: float(i == 0) for i in range(8)}) == 1


def test_missing_quartets_and_errors_do_not_disappear(plan):
    raw = fixture_records(plan)
    missing = next(j["id"] for j in jobs_in(plan) if control.stratum(j["row"]) == "after_relevant")
    partial = [r for r in raw if r["id"] != missing]
    report = summarize(fixture_manifest(), plan, partial)
    assert not report["coverage_complete"]
    assert report["interaction"]["after_relevant"]["estimate"] is None
    assert report["interaction"]["after_relevant"]["observed_quartets"] == 127
    damaged = deepcopy(raw)
    damaged[0].update(status="invalid_scores", result={})
    failed = summarize(fixture_manifest(), plan, damaged)
    assert failed["errors"] == 1 and failed["completed_jobs"] == 2048


class StubBackend:
    def choice(self, prompt, choices, fmt):
        assert isinstance(prompt, str) and fmt == "chat" and len(choices) == 4
        return {
            "status": "ok",
            "selected_command": choices[0],
            "candidates": [
                {"command": c, "log_likelihood": -1.0 - i, "token_count": 3, "token_ids": [1, 2, 3]}
                for i, c in enumerate(choices)
            ],
        }


def stub_factory(spec):
    assert spec["generation"] == {}
    return StubBackend(), {"synthetic": True}


def test_shared_runner_resume_integrity_and_no_duplicate_choices(tmp_path):
    directory = tmp_path / "run"
    first = control.run(control.DEFAULT_SPEC, directory, max_jobs=3, backend_factory=stub_factory)
    assert first["status"] == "paused" and first["expected_jobs"] == 2048
    manifest = read_json(directory / "manifest.json")
    manifest["records"] = {}  # Crash between SQLite commit and manifest write.
    write_json(directory / "manifest.json", manifest)
    second = control.run(control.DEFAULT_SPEC, directory, max_jobs=5, backend_factory=stub_factory)
    assert len(second["records"]) == len(read_records(directory)) == 8
    assert second["synthetic"]
    control.read_run(directory)
    assert main(["analyze", str(directory)]) == 0
    assert read_json(directory / "analysis.json")["decision"] == "synthetic_only"
    first_export = tmp_path / "partial1.tar.gz"
    second_export = tmp_path / "partial2.tar.gz"
    export(directory, first_export)
    export(directory, second_export)
    assert first_export.read_bytes() == second_export.read_bytes()
    manifest = read_json(directory / "manifest.json")
    manifest["provenance"]["source_hash"] = "changed"
    write_json(directory / "manifest.json", manifest)
    with pytest.raises(ValueError, match="source_hash changes"):
        control.run(control.DEFAULT_SPEC, directory, max_jobs=1, backend_factory=stub_factory)
