from collections import Counter, defaultdict
from copy import deepcopy

import pytest

from self_model_study import possessive as study
from self_model_study.action_task import score_command
from self_model_study.cli import main
from self_model_study.io import digest, read_json, source_hash, write_json
from self_model_study.pilot import jobs_in
from self_model_study.possessive_analysis import decision, summarize
from self_model_study.possessive_reporting import export, markdown_report, plots
from self_model_study.storage import read_records


@pytest.fixture(scope="module")
def plan():
    return study.build_plan(study.DEFAULT_SPEC)


def manifest():
    return {
        "config": study.DEFAULT_SPEC,
        "protocol": study.PROTOCOL,
        "run_id": "synthetic-possessive",
        "synthetic": True,
        "status": "complete",
        "provenance": {"source_hash": source_hash()},
    }


def fixture_records(plan, pattern="specific"):
    records = []
    for job in jobs_in(plan):
        row = job["row"]
        # Only a subset of relevant target cases fail, leaving pooled controls above 80%.
        wrong = (
            study.stratum(row) == "after_relevant"
            and row["relation"] == "target"
            and row["rotation"] == 0
            and (row["frame"] == "your" or pattern == "shared" and row["frame"] == "the")
        )
        chosen = (
            next(c for c in row["choices"] if c != row["expected_command"])
            if wrong
            else row["expected_command"]
        )
        records.append(
            {
                "id": job["id"],
                "status": "ok",
                "result": {
                    "selected_command": chosen,
                    "execution": score_command(row, chosen),
                    "candidates": [
                        {"command": c, "log_likelihood": -1.0 if c == chosen else -2.0}
                        for c in row["choices"]
                    ],
                },
            }
        )
    return records


def test_complete_matched_design_and_fixed_question_without_solution_leak(plan):
    jobs = jobs_in(plan)
    assert digest(plan) == study.FROZEN_PLAN_HASH
    assert plan == study.build_plan(study.DEFAULT_SPEC)
    assert len(jobs) == len({j["id"] for j in jobs}) == 6144
    assert [len(b["jobs"]) for b in plan["blocks"]] == [384] * 16
    assert {int(j["row"]["scenario_id"].rsplit(":", 1)[1]) for j in jobs} == set(range(16, 32))
    assert Counter(j["row"]["expected_position"] for j in jobs) == {i: 1536 for i in range(4)}
    groups = defaultdict(list)
    for job in jobs:
        row = job["row"]
        groups[row["scene_id"]].append(row)
        assert score_command(row, row["expected_command"])["correct"]
        assert f"Select one command that would succeed for {row['target']}." in row["prompt"]
        assert all(k not in row for k in ("assigned", "identity", "view", "language_prompt"))
        assert all(
            k not in row["prompt"]
            for k in ("expected_command", "scene_id", "target_identity", "grant_variant")
        )
    assert len(groups) == 1024
    for rows in groups.values():
        assert {(r["frame"], r["relation"]) for r in rows} == set(study.CONDITIONS)
        assert len({r["expected_command"] for r in rows}) == 1
        normalized = set()
        for r in rows:
            line = study.DEFAULT_SPEC["context_lines"][r["frame"]].format(
                actor=r["mentioned_actor"]
            )
            assert r["prompt"].count(line) == 1
            normalized.add(r["prompt"].replace(line, "<CONTEXT>"))
        assert len(normalized) == 1
    assert study.preview(study.DEFAULT_SPEC)["unique_model_inputs"] == 3840


def test_historical_content_disjointness(monkeypatch):
    import importlib

    monkeypatch.syspath_prepend("scripts")
    module = importlib.import_module("review_possessive_design")
    result = module.audit()
    assert result["unique_context_removed_inputs"] == 640
    assert all(
        h["exact_input_overlap"]
        == h["context_removed_input_overlap"]
        == h["scenario_id_overlap"]
        == 0
        for h in result["historical_exposure"]
    )
    row = {"prompt": "Your active connection: Cedar.\nChoose for Dune.", "choices": ["a", "b"]}
    other = {**row, "prompt": row["prompt"].replace("Your active", "The active")}
    assert module.input_signature(row) != module.input_signature(other)
    assert module.input_signature(row, True) == module.input_signature(other, True)


def test_actual_pinned_tokenizer_pairs_and_output_audit(plan):
    transformers = pytest.importorskip("transformers")
    try:
        tokenizer = transformers.AutoTokenizer.from_pretrained(
            study.DEFAULT_SPEC["model"]["repo"],
            revision=study.DEFAULT_SPEC["model"]["revision"],
            local_files_only=True,
        )
    except OSError:
        pytest.skip("Pinned tokenizer is not cached; run validate --tokenizer-check to obtain it")
    inputs = study.token_inputs(study.DEFAULT_SPEC, tokenizer)
    assert len(inputs) == 3840
    prompt, item = next(iter(inputs.items()))
    result = {k: item[k] for k in ("rendered_prompt", "prompt_token_ids")}
    result["candidates"] = [
        {"command": c, "token_ids": ids, "token_count": len(ids)}
        for c, ids in item["continuations"].items()
    ]
    study.check_output(prompt, result, inputs)
    for key in ("rendered_prompt", "prompt_token_ids"):
        corrupt = deepcopy(result)
        corrupt[key] = corrupt[key][:-1]
        with pytest.raises(ValueError, match="audited possessive tokens"):
            study.check_output(prompt, corrupt, inputs)
    corrupt = deepcopy(result)
    corrupt["candidates"][0]["token_ids"].append(123)
    with pytest.raises(ValueError, match="audited tokens"):
        study.check_output(prompt, corrupt, inputs)


@pytest.fixture(scope="module")
def report(plan):
    return summarize(manifest(), plan, fixture_records(plan))


def test_primary_scenario_inference_and_descriptive_anchor(plan, report):
    stat = report["interaction"]["after_relevant"]
    assert report["decision"] == "synthetic_only"
    assert stat["estimate"] == 0.25 and stat["ci95"] == [0.25, 0.25]
    assert stat["n_clusters"] == 16 and stat["n_observations"] == 256
    assert stat["two_sided_sign_flip_p"] == 2 / 65536
    assert stat["positive_scenarios"] == 16
    assert report["controls_passed"] and len(report["controls"]) == 48
    assert len(report["counterfactuals"]) == 18
    assert report["counterfactuals"]["your/target/grant_variant"]["estimate"] == 0.75
    rules = study.DEFAULT_SPEC["decision"]
    eligible = {**report, "synthetic": False}
    assert decision(eligible, rules) == "possessive_wording_candidate"
    # An arbitrarily large Reference contrast cannot rescue a zero Your/The effect.
    shared = summarize(manifest(), plan, fixture_records(plan, "shared"))
    assert shared["reference_anchor"]["after_relevant"]["estimate"] == 0.25
    assert shared["interaction"]["after_relevant"]["estimate"] == 0
    assert decision({**shared, "synthetic": False}, rules) == "no_clear_possessive_specificity"
    for changes, wanted in (
        ({"coverage_complete": False}, "incomplete"),
        ({"errors": 1}, "measurement_failure"),
        ({"controls_passed": False}, "stop_control_failure"),
        ({"same_source_as_execution": False}, "source_mismatch"),
    ):
        assert decision({**eligible, **changes}, rules) == wanted
    # One opposite scene does not get lost in an average or a secondary margin.
    for key, value in (
        ("estimate", 0.049),
        ("ci95", [0.0, 0.5]),
        ("positive_scenarios", 11),
        ("two_sided_sign_flip_p", 0.051),
    ):
        altered = deepcopy(eligible)
        altered["interaction"]["after_relevant"][key] = value
        assert decision(altered, rules) == "no_clear_possessive_specificity"
    assert not report["original_capability_screen_changed"]


def test_missing_pairs_and_error_denominators(plan):
    raw = fixture_records(plan)
    index = next(
        i for i, j in enumerate(jobs_in(plan)) if study.stratum(j["row"]) == "after_relevant"
    )
    partial = raw[:index] + raw[index + 1 :]
    report = summarize(manifest(), plan, partial)
    assert not report["coverage_complete"]
    assert report["interaction"]["after_relevant"]["estimate"] is None
    assert report["interaction"]["after_relevant"]["observed_sextets"] == 255
    assert report["reference_anchor"]["after_relevant"]["estimate"] is None
    raw[index].update(status="invalid_scores", result={})
    failed = summarize(manifest(), plan, raw)
    assert failed["completed_jobs"] == 6144 and failed["errors"] == 1
    assert failed["interaction"]["after_relevant"]["observed_sextets"] == 256
    assert failed["margin_effects_nats"]["interaction/after_relevant"]["estimate"] is None


class StubBackend:
    def choice(self, prompt, choices, fmt):
        assert isinstance(prompt, str) and len(choices) == 4 and fmt == "chat"
        assert "expected_command" not in prompt
        return {
            "status": "ok",
            "selected_command": choices[0],
            "candidates": [
                {"command": c, "log_likelihood": -1.0 - i, "token_count": 3, "token_ids": [1, 2, 3]}
                for i, c in enumerate(choices)
            ],
        }


def stub_factory(spec):
    assert spec["generation"] == {} and spec["num_fewshot"] == 0
    return StubBackend(), {"synthetic": True}


def test_resume_cli_and_reproducible_partial_export(tmp_path):
    directory = tmp_path / "run"
    study.run(study.DEFAULT_SPEC, directory, max_jobs=3, backend_factory=stub_factory)
    saved = read_json(directory / "manifest.json")
    saved["records"] = {}  # Crash after SQLite commit, before manifest flush.
    write_json(directory / "manifest.json", saved)
    result = study.run(study.DEFAULT_SPEC, directory, max_jobs=5, backend_factory=stub_factory)
    assert result["status"] == "paused" and len(read_records(directory)) == 8
    study.read_run(directory)
    assert main(["analyze", str(directory)]) == 0
    assert read_json(directory / "analysis.json")["decision"] == "synthetic_only"
    a, b = tmp_path / "a.tar.gz", tmp_path / "b.tar.gz"
    export(directory, a)
    export(directory, b)
    assert a.read_bytes() == b.read_bytes()
    assert "SYNTHETIC" in (directory / "article_section.md").read_text()
    saved = read_json(directory / "manifest.json")
    saved["provenance"]["source_hash"] = "changed"
    write_json(directory / "manifest.json", saved)
    with pytest.raises(ValueError, match="source_hash changes"):
        study.run(study.DEFAULT_SPEC, directory, max_jobs=1, backend_factory=stub_factory)


def test_frozen_fields_design_cli_and_tamper_rejection(tmp_path):
    for key, val in (
        ("scenarios", list(range(8))),
        ("score", "mean_log_likelihood"),
        ("max_seconds", True),
        ("context_lines", {}),
        ("decision", {}),
    ):
        with pytest.raises(ValueError):
            study.validate_spec({**study.DEFAULT_SPEC, key: val})
    directory = tmp_path / "design"
    assert (
        main(["validate", "configs/qwen-possessive-control.json", "--freeze", str(directory)]) == 0
    )
    with pytest.raises(ValueError, match="not a model run"):
        study.run(study.DEFAULT_SPEC, directory, backend_factory=stub_factory)
    assert main(["export", str(directory), "--out", str(tmp_path / "design.tar.gz")]) == 0
    data = read_json(directory / "model_inputs.json")
    data[0]["prompt"] += " hidden solution"
    write_json(directory / "model_inputs.json", data)
    with pytest.raises(ValueError, match="model inputs changed"):
        export(directory, tmp_path / "bad.tar.gz")


def test_complete_report_preserves_all_six_fixed_examples(plan, report, tmp_path):
    text = markdown_report(report, plan, fixture_records(plan))
    assert text.count("```text") == 6 and text.count("```json") == 6
    assert "All quality controls" in text and "SYNTHETIC SOFTWARE TEST ONLY" in text
    plots(report, tmp_path)
    assert len(list(tmp_path.iterdir())) == 12
