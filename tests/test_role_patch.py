from collections import Counter
from copy import deepcopy

import numpy as np
import pytest

from self_model_study import role_control, role_patch
from self_model_study.action_task import score_command
from self_model_study.cli import main
from self_model_study.io import digest, read_json, source_hash, write_json
from self_model_study.pilot import jobs_in
from self_model_study.role_patch_analysis import decision, summarize
from self_model_study.role_patch_reporting import export
from self_model_study.storage import read_records


@pytest.fixture(scope="module")
def plan():
    return role_patch.build_plan(role_patch.DEFAULT_SPEC)


def test_frozen_count_mapping_order_and_model_input_separation(plan):
    jobs = jobs_in(plan)
    old = {j["id"]: j for j in jobs_in(role_control.build_plan(role_control.DEFAULT_SPEC))}
    assert len(jobs) == len({j["id"] for j in jobs}) == 11296
    assert digest(plan) == role_patch.FROZEN_PLAN_HASH
    assert digest(role_patch.random_directions()) == role_patch.DIRECTIONS_HASH
    assert digest(role_patch.historical_reference()) == role_patch.REFERENCE_HASH
    counts = Counter(j["arm"] for j in jobs)
    assert counts == {
        "baseline": 2048,
        "self": 2048,
        "swap": 2048,
        "repeat": 32,
        **{f"random_{i:02d}": 512 for i in range(10)},
    }
    directions = np.asarray(role_patch.random_directions()["vectors"])
    assert np.allclose(np.linalg.norm(directions, axis=1), 1, atol=1e-7)
    for block in plan["blocks"]:
        assert all(j["arm"] == "baseline" for j in block["jobs"][:256])
        assert all(j["arm"] == "repeat" for j in block["jobs"][-4:])
        for j in block["jobs"]:
            assert j["row"] == old[j["base_id"]]["row"]
            assert not any(x in j["row"]["prompt"] for x in ("expected_command", "scene_id", "arm"))
            if j["arm"].startswith("random_"):
                assert role_control.stratum(j["row"]) == "after_relevant"
            if not j["technical"]:
                donor = old[j["donor_base_id"]]["row"]
                row = j["row"]
                for field in (
                    "scene_id",
                    "mentioned_actor",
                    "choices",
                    "state",
                    "target",
                    "relation",
                ):
                    assert donor[field] == row[field]
                assert donor["frame"] != row["frame"]
    for changed in ({"scenarios": list(range(8))}, {"patch": {}}, {"max_seconds": True}):
        with pytest.raises(ValueError):
            role_patch.validate_spec({**role_patch.DEFAULT_SPEC, **changed})


def test_design_cli_and_deterministic_export(tmp_path):
    directory = tmp_path / "design"
    assert main(["validate", "configs/qwen-role-patch.json", "--freeze", str(directory)]) == 0
    assert not (directory / "trials.sqlite").exists()
    export(directory, tmp_path / "one.tar.gz")
    export(directory, tmp_path / "two.tar.gz")
    assert (tmp_path / "one.tar.gz").read_bytes() == (tmp_path / "two.tar.gz").read_bytes()
    with pytest.raises(ValueError, match="not a model run"):
        role_patch.run(role_patch.DEFAULT_SPEC, directory)
    data = read_json(directory / "random_directions.json")
    data["vectors"][0][0] += 1
    write_json(directory / "random_directions.json", data)
    with pytest.raises(ValueError, match="directions"):
        export(directory, tmp_path / "bad.tar.gz")


def analytical_fixture(plan, mode="transfer"):
    records = []
    for job in jobs_in(plan):
        row, arm = job["row"], job["arm"]
        wrong = False
        if role_control.stratum(row) == "after_relevant" and row["relation"] == "target":
            wrong = row["frame"] == "active" and row["rotation"] == 0
            if arm == "swap":
                wrong = row["frame"] == "reference" and row["rotation"] == 0
                if mode == "one_way":
                    wrong = False
            if mode == "nonspecific" and arm.startswith("random_"):
                wrong = row["frame"] == "reference" and row["rotation"] == 0
        selected = (
            next(c for c in row["choices"] if c != row["expected_command"])
            if wrong
            else row["expected_command"]
        )
        records.append(
            {
                "id": job["id"],
                "job": job,
                "status": "ok",
                "result": {
                    "execution": score_command(row, selected),
                    "technical_checks": [],
                    "candidates": [
                        {
                            "command": c,
                            "log_likelihood": -1.0 if c == selected else -2.0,
                            "patch": {"relative_norm_error": 0.0},
                        }
                        for c in row["choices"]
                    ],
                },
            }
        )
    return records


def manifest():
    return {
        "protocol": role_patch.PROTOCOL,
        "run_id": "synthetic-fixture",
        "status": "complete",
        "synthetic": True,
        "config": role_patch.DEFAULT_SPEC,
        "provenance": {"source_hash": source_hash()},
    }


def test_transfer_arithmetic_primary_random_contrast_and_scenario_units(plan):
    report = summarize(manifest(), plan, analytical_fixture(plan))
    assert report["decision"] == "synthetic_only"
    assert report["transfer"]["swap"]["total"]["estimate"] == 0.25
    assert report["transfer"]["swap"]["reference_to_active"]["estimate"] == 0.25
    assert report["transfer"]["swap"]["active_to_reference"]["estimate"] == 0.25
    primary = report["primary_contrast"]
    assert primary["estimate"] == 0.25 and primary["ci95"] == [0.25, 0.25]
    assert primary["n_clusters"] == primary["n_observations"] == 8
    assert primary["positive_scenarios"] == 8 and primary["two_sided_sign_flip_p"] == 2 / 256
    rules = role_patch.DEFAULT_SPEC["decision"]
    eligible = {**report, "synthetic": False}
    assert decision(eligible, rules) == "bidirectional_transfer_candidate"
    for changes, expected in (
        ({"coverage_complete": False}, "incomplete"),
        ({"errors": 1}, "measurement_failure"),
        ({"technical_failures": 1}, "technical_failure"),
        ({"controls_passed": False}, "stop_control_failure"),
    ):
        assert decision({**eligible, **changes}, rules) == expected
    for mode in ("one_way", "nonspecific"):
        failed = summarize(manifest(), plan, analytical_fixture(plan, mode))
        assert (
            decision({**failed, "synthetic": False}, rules) == "no_bidirectional_transfer_candidate"
        )
    # Exactly the lower control margin does not satisfy the strict > -5 pp rule.
    changed = deepcopy(eligible)
    changed["control_change"]["ci95"][0] = -0.05
    assert decision(changed, rules) == "stop_control_failure"


def test_missing_data_and_invalid_scores_visible(plan):
    raw = analytical_fixture(plan)
    remove = next(r for r in raw if r["job"]["arm"] == "random_00")
    raw.remove(remove)
    raw[0].update(status="invalid_scores", result={})
    report = summarize(manifest(), plan, raw)
    assert not report["coverage_complete"] and report["errors"] == 1
    assert report["primary_contrast"]["n_clusters"] == 7
    assert len(report["control_cells"]) == 8


class StubBackend:
    synthetic = True
    calls = []
    fail_self = False

    def choice(self, prompt, choices, format_name, *, mode, own=None, donor=None, direction=None):
        import torch

        assert set(locals()) == {
            "self",
            "prompt",
            "choices",
            "format_name",
            "mode",
            "own",
            "donor",
            "direction",
            "torch",
        }
        assert format_name == "chat" and isinstance(prompt, str)
        self.calls.append(mode)
        value = 1.0 if "Your active connection:" in prompt else 1.125
        activation = torch.full((3584,), value, dtype=torch.bfloat16)
        ctx = [1, 624, 2]
        candidates = []
        for i, c in enumerate(choices):
            cont = [3, i + 4]
            metrics = {
                "layer": 13,
                "position": 1,
                "width": 3584,
                "mode": mode,
                "residual_norm": float(activation.float().norm()),
            }
            if own is not None:
                target = (
                    float((donor[f"candidate_{i}"].float() - activation.float()).norm())
                    if mode != "self"
                    else 0.0
                )
                metrics.update(
                    prepatch_max_abs_difference=0.0,
                    desired_norm=target,
                    actual_norm=target,
                    relative_norm_error=0.0,
                )
            candidates.append(
                {
                    "command": c,
                    "token_ids": cont,
                    "token_count": 2,
                    "log_likelihood": -1.0 - i - (1 if self.fail_self and mode == "self" else 0),
                    "patch": metrics,
                    "forward_input_hash": digest((ctx + cont)[:-1]),
                }
            )
        result = {
            "rendered_prompt": prompt,
            "prompt_token_ids": ctx,
            "candidates": candidates,
            "selected_command": choices[0],
            "status": "ok",
        }
        return result, {f"candidate_{i}": activation.clone() for i in range(4)}


def factory(spec):
    pytest.importorskip("torch")
    return StubBackend(), {"synthetic": True}


def test_resume_after_journal_commit_and_corrupt_donor_stops_before_model(tmp_path):
    directory = tmp_path / "run"
    first = role_patch.run(role_patch.DEFAULT_SPEC, directory, max_jobs=2, backend_factory=factory)
    assert first["status"] == "paused" and len(first["records"]) == 2
    first["records"] = {}  # Crash after journal commit, before manifest update.
    write_json(directory / "manifest.json", first)
    second = role_patch.run(role_patch.DEFAULT_SPEC, directory, max_jobs=1, backend_factory=factory)
    assert len(second["records"]) == len(read_records(directory)) == 3
    role_patch.read_run(directory)
    assert main(["analyze", str(directory)]) == 0
    export(directory, tmp_path / "partial1.tar.gz")
    export(directory, tmp_path / "partial2.tar.gz")
    assert (tmp_path / "partial1.tar.gz").read_bytes() == (
        tmp_path / "partial2.tar.gz"
    ).read_bytes()
    donor = next((directory / "activations").iterdir())
    donor.write_bytes(b"corruption")
    calls = len(StubBackend.calls)
    with pytest.raises(ValueError, match="donor"):
        role_patch.run(role_patch.DEFAULT_SPEC, directory, max_jobs=1, backend_factory=factory)
    assert len(StubBackend.calls) == calls


def test_resume_crosses_baseline_to_patch_and_preserves_failed_null(tmp_path, monkeypatch):
    directory = tmp_path / "run"
    first = role_patch.run(
        role_patch.DEFAULT_SPEC, directory, max_jobs=256, backend_factory=factory
    )
    assert len(first["records"]) == 256
    second = role_patch.run(role_patch.DEFAULT_SPEC, directory, max_jobs=1, backend_factory=factory)
    assert len(second["records"]) == 257
    role_patch.read_run(directory)
    monkeypatch.setattr(StubBackend, "fail_self", True)
    failed = role_patch.run(role_patch.DEFAULT_SPEC, directory, max_jobs=2, backend_factory=factory)
    assert failed["status"] == "failed" and len(failed["records"]) == 258
    _, _, records = role_patch.read_run(directory)
    assert sum(r["result"]["technical_failure"] for r in records) == 1
    with pytest.raises(ValueError, match="Failed run retained"):
        role_patch.run(role_patch.DEFAULT_SPEC, directory, backend_factory=factory)
