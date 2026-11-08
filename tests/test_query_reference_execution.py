"""Execution, failure recovery and mathematical checks with synthetic fixtures only."""

import gzip
import json
from copy import deepcopy

import numpy as np
import pytest

from self_model_study import query_reference_analysis as analysis
from self_model_study import query_reference_reporting as reporting
from self_model_study import query_reference_runtime as runtime
from self_model_study.io import digest, read_json, write_json
from self_model_study.query_reference import build_inputs
from self_model_study.storage import read_records


@pytest.fixture(scope="module")
def inventory():
    worlds, rows = build_inputs()
    for world in worlds:
        world["world_id"] = world["world_id"].replace("query-self-v1", "fixture-query-self")
    for row in rows:
        row["world_id"] = row["world_id"].replace("query-self-v1", "fixture-query-self")
        row["id"] = digest(["fixture", row["id"]])
    return worlds, rows


def synthetic_runs(inventory, errors=False):
    _, rows = inventory
    runs = []
    for block in range(6):
        selected = [r for r in rows if r["block_index"] == block]
        plan = {
            "protocol": runtime.PROTOCOL,
            "blocks": [
                {
                    "id": f"fixture:{block}",
                    "jobs": [
                        {"id": r["id"], "kind": "action", "format": "chat", "row": r}
                        for r in selected
                    ],
                }
            ],
        }
        records = []
        for row in selected:
            command = row["expected_command"]
            # Variable world effects, no borrowed observed model answers.
            if (
                errors
                and row["stage"] == "after_both"
                and row["queried_owner"] == "self"
                and row["query_form"] == "possessive"
                and row["option_rotation"] < 1 + row["world_index"] % 3
            ):
                foreign = next(a for a in row["state"]["permissions"] if a != row["target"])
                command = row["state"]["permissions"][foreign][0]
            result = {
                "status": "ok",
                "selected_command": command,
                "candidates": [
                    {"command": c, "log_likelihood": -1.0 if c == command else -4.0}
                    for c in row["choices"]
                ],
            }
            records.append({"id": row["id"], "result": result})
        manifests = {
            "run_id": f"fixture-{block}",
            "status": "complete",
            "synthetic": True,
            "provenance": {
                "source_hash": "fixture",
                "python": "fixture",
                "packages": {},
                "git_commit": "fixture",
            },
        }
        runs.append((manifests, plan, records))
    return runs


@pytest.fixture(scope="module")
def reports(inventory):
    # Pure aggregation receives only explicitly marked fixture worlds/records.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(analysis, "build_inputs", lambda: inventory)
        perfect = analysis.summarize(synthetic_runs(inventory))
        signal = analysis.summarize(synthetic_runs(inventory, errors=True))
        partial = analysis.summarize(synthetic_runs(inventory)[:1])
    return perfect, signal, partial


def test_primary_directions_holm_and_paired_bootstrap_against_independent_calculation():
    from scipy.stats import ttest_1samp

    values = np.arange(48) / 48 - 0.35
    vectors = {"E": values, "F": values * 0.5 + 0.01, "S": values * -0.3}
    result = analysis.primary_tests(vectors, True)
    rng = np.random.default_rng(1729)
    indices = rng.choice(48, size=(10000, 48), replace=True)
    ps = []
    for name, xs in vectors.items():
        expected = float(ttest_1samp(xs, 0).pvalue)
        ps.append(expected)
        assert result[name]["raw_p"] == pytest.approx(expected)
        ci = np.quantile(np.mean(xs[indices], axis=1), [0.025, 0.975])
        assert result[name]["ci95"] == pytest.approx(ci)
    # Directly enumerate each ordered Holm prefix instead of calling implementation.
    order = np.argsort(ps)
    expected_holm = [0.0] * 3
    for rank, index in enumerate(order):
        expected_holm[index] = min(1, max((3 - j) * ps[order[j]] for j in range(rank + 1)))
    assert [result[k]["holm_p"] for k in vectors] == pytest.approx(expected_holm)


def test_degenerate_tests_use_null_not_fabricated_significance_or_equivalence():
    vectors = {"E": [1.0] * 48, "F": [0.0] * 48, "S": [-1.0] * 48}
    for eligible in (True, False):
        result = analysis.primary_tests(vectors, eligible)
        assert all(
            r["raw_p"] is None and r["holm_placeholder"] and not r["qualifies"]
            for r in result.values()
        )
        assert all(r["holm_input"] == r["holm_p"] == 1 for r in result.values())
        if not eligible:
            assert all(r["ci95"] is None for r in result.values())


def test_full_signal_keeps_world_units_error_budgets_and_synthetic_boundary(reports):
    perfect, signal, _ = reports
    assert signal["recorded_choices"] == 16128 and signal["valid_complete_worlds"] == 48
    assert signal["lookup_numerical_pass"] and not signal["lookup_gate_passed"]
    assert signal["decision"] == "synthetic_software_fixture_not_model_evidence"
    for r in signal["primary"].values():
        assert r["estimate"] == 0.5 and r["qualifies"] and len(r["world_contrasts"]) == 48
    for r in signal["strata"]["after_both"]["per_world"].values():
        assert r["F_minus_E"] == 0
        assert r["conditional_E_bounds"][0] == 0
        assert r["conditional_E_bounds"][1] == r["E"]
    assert all(r["raw_p"] is None for r in perfect["primary"].values())
    assert all(
        c["error_conditional_shares"]["other_account_current"] is None
        for c in perfect["cells"].values()
    )
    assert (
        analysis.decision(signal["primary"], True, True, False)
        == "own_versus_other_specificity_candidate"
    )
    changed = deepcopy(signal["primary"])
    changed["S"]["qualifies"] = False
    assert (
        analysis.decision(changed, True, True, False)
        == "reference_sensitive_own_query_candidate_without_specificity"
    )
    assert analysis.decision(changed, True, False, False) == "lookup_gate_failed"
    changed["E"]["qualifies"] = False
    assert analysis.decision(changed, True, True, False) == "no_joint_reference_candidate"


def test_partial_blocks_keep_all_denominators_and_cannot_test(reports):
    _, _, report = reports
    assert report["scheduled_choices"] == 16128
    assert report["recorded_choices"] == report["supplied_block_choices"] == 2688
    assert report["missing"] == 13440 and report["valid_complete_worlds"] == 8
    assert all(v["raw_p"] is None and v["ci95"] is None for v in report["primary"].values())
    assert sum(c["counts"]["invalid"] for c in report["cells"].values()) == report["missing"]
    assert all(c["accuracy"] == pytest.approx(1 / 6) for c in report["cells"].values())


def test_missing_tied_error_and_revocation_counts_do_not_disappear(inventory):
    _, rows = inventory
    row = next(r for r in rows if r["stage"] == "after_both")
    for status in ("missing", "error", "tie", "invalid_scores"):
        raw = (
            None
            if status == "missing"
            else {"result": {"status": status, "selected_command": None}}
        )
        obs = analysis.observe(row, raw)
        assert obs["category"] == "invalid" and not obs["correct"] and obs["margin"] is None
        summary = analysis.cell([obs])
        assert summary["scheduled"] == summary["errors_including_missing"] == 1
        assert summary["missing"] == (status == "missing")
    for stage in ("before", "snapshot"):
        sample = next(r for r in rows if r["stage"] == stage)
        c = analysis.cell([analysis.observe(sample, None)])
        assert c["counts"]["revoked_target"] is None and c["counts"]["revoked_other"] is None
    old = row["before"]["permissions"][row["target"]][0]
    raw = {"result": {"status": "ok", "selected_command": old}}
    assert analysis.observe(row, raw)["category"] == "revoked_target"


def test_merge_rejects_duplicate_blocks_and_mixed_provenance(inventory, monkeypatch):
    monkeypatch.setattr(analysis, "build_inputs", lambda: inventory)
    runs = synthetic_runs(inventory)
    with pytest.raises(ValueError, match="Overlapping"):
        analysis.summarize([runs[0], runs[0]])
    runs[1][0]["provenance"]["source_hash"] = "different"
    with pytest.raises(ValueError, match="provenance"):
        analysis.summarize(runs[:2])


def test_one_invalid_selection_blocks_inference_without_dropping_the_world(inventory, monkeypatch):
    monkeypatch.setattr(analysis, "build_inputs", lambda: inventory)
    runs = synthetic_runs(inventory, errors=True)
    runs[0][2][0]["result"].update(status="tie", selected_command=None)
    runs[0][0]["status"] = "complete_with_errors"
    report = analysis.summarize(runs)
    assert report["coverage_complete"] and report["recorded_choices"] == 16128
    assert report["invalid_recorded"] == 1 and report["valid_complete_worlds"] == 47
    assert not report["inference_eligible"]
    assert all(r["ci95"] is None and r["raw_p"] is None for r in report["primary"].values())


def test_undefined_specificity_remains_in_the_three_test_holm_family():
    vector = np.linspace(0.1, 0.5, 48)
    result = analysis.primary_tests({"E": vector, "F": vector, "S": np.zeros(48)}, True)
    assert result["S"]["raw_p"] is None and result["S"]["holm_input"] == 1
    assert result["E"]["holm_p"] == pytest.approx(3 * result["E"]["raw_p"])
    assert result["F"]["holm_p"] == pytest.approx(3 * result["F"]["raw_p"])
    assert not result["S"]["qualifies"]


def test_all_pairs_have_correct_anchor_gates_and_names(reports):
    perfect = reports[0]
    gates = {k: v for k, v in perfect["paired_controls"].items() if v["lookup_gate"]}
    assert len(gates) == len(perfect["lookup_cells"]) == 8
    assert sum(p["scheduled_pairs"] for p in gates.values()) == 2304
    assert all(p["fully_correct_rate"] == 1 and p["numerical_pass"] for p in gates.values())
    assert len(perfect["cells"]) == 18 and len(perfect["strata"]) == 5


def encoded(row):
    prompt = row["prompt"] + "\nASSISTANT\n"
    return {
        "rendered_prompt": prompt,
        "prompt_token_ids": list(prompt.encode()),
        "candidates": [
            {"command": c, "token_ids": list(c.encode()), "token_count": len(c)}
            for c in row["choices"]
        ],
    }


class FakeBackend:
    calls = 0

    def choice(self, prompt, choices, format_name):
        assert format_name == "chat" and isinstance(prompt, str) and len(choices) == 4
        self.calls += 1
        result = encoded({"prompt": prompt, "choices": choices})
        for i, c in enumerate(result["candidates"]):
            c["log_likelihood"] = -float(i + 1)
        return {**result, "status": "ok", "selected_command": choices[0]}


@pytest.fixture
def execution_fixture(inventory, monkeypatch):
    rows = inventory[1][:4]
    plan = {
        "protocol": runtime.PROTOCOL,
        "blocks": [
            {
                "id": "fixture-world",
                "jobs": [
                    {"id": r["id"], "kind": "action", "format": "chat", "row": r} for r in rows
                ],
            }
        ],
    }
    tokens = {r["id"]: encoded(r) for r in rows}
    monkeypatch.setattr(runtime, "build_plan", lambda spec: plan)
    monkeypatch.setattr(runtime, "frozen_tokens", lambda spec, plan: tokens)
    return runtime.configuration(0), plan, tokens


def test_resume_journal_recovery_no_duplicate_selection_and_complete_no_reload(
    tmp_path, execution_fixture
):
    spec, _, _ = execution_fixture
    backend = FakeBackend()

    def factory(_):
        return backend, {"synthetic": True}

    path = tmp_path / "run"
    first = runtime.run(spec, path, max_jobs=1, backend_factory=factory)
    assert first["status"] == "paused" and len(read_records(path)) == 1
    first["records"] = {}  # Journal commit survived; manifest write was interrupted.
    write_json(path / "manifest.json", first)
    final = runtime.run(spec, path, backend_factory=factory)
    assert final["status"] == "complete" and len(final["records"]) == backend.calls == 4
    runtime.read_run(path)
    runtime.run(spec, path, backend_factory=lambda _: pytest.fail("Completed run loaded weights"))
    assert len(read_records(path)) == 4
    saved = read_json(path / "manifest.json")
    saved["synthetic"] = False
    write_json(path / "manifest.json", saved)
    with pytest.raises(ValueError, match="provenance flags"):
        runtime.read_run(path)


@pytest.mark.parametrize("failure", ["exception", "nan", "short_scores", "token_drift", "tie"])
def test_failure_retention_and_no_automatic_retry(tmp_path, execution_fixture, failure):
    spec, _, _ = execution_fixture

    class Broken(FakeBackend):
        def choice(self, *args):
            if failure == "exception":
                raise RuntimeError("fixture scorer failure")
            result = super().choice(*args)
            if failure == "nan":
                result["candidates"][0]["log_likelihood"] = float("nan")
                result.update(status="invalid_scores", selected_command=None)
            elif failure == "short_scores":
                result["candidates"].pop()
            elif failure == "token_drift":
                result["prompt_token_ids"][0] += 1
            else:
                for c in result["candidates"]:
                    c["log_likelihood"] = -1.0
                result.update(status="tie", selected_command=None)
            return result

    path = tmp_path / failure
    manifest = runtime.run(spec, path, backend_factory=lambda _: (Broken(), {"synthetic": True}))
    assert manifest["status"] == ("complete_with_errors" if failure == "tie" else "failed")
    saved = runtime.read_run(path)[2]
    assert len(saved) == (4 if failure == "tie" else 1)
    assert all(r["status"] != "ok" for r in saved)
    if failure != "tie":
        with pytest.raises(ValueError, match="Failed run"):
            runtime.run(spec, path, backend_factory=lambda _: pytest.fail("Retried failed case"))
    if failure in {"short_scores", "token_drift"}:
        assert saved[0]["result"]["raw_output"]


def test_interrupt_and_configuration_drift(tmp_path, execution_fixture):
    spec, _, _ = execution_fixture

    class Interrupted(FakeBackend):
        def choice(self, *args):
            raise KeyboardInterrupt()

    path = tmp_path / "interrupted"
    m = runtime.run(spec, path, backend_factory=lambda _: (Interrupted(), {"synthetic": True}))
    assert m["status"] == "interrupted" and not read_records(path)
    with pytest.raises(ValueError, match="configuration"):
        runtime.run({**spec, "batch_size": 2}, path, backend_factory=lambda _: None)
    m = runtime.run(spec, path, backend_factory=lambda _: (FakeBackend(), {"synthetic": True}))
    assert m["status"] == "complete"


def test_frozen_input_source_and_plan_guard(tmp_path, monkeypatch):
    path = tmp_path / "freeze.json"
    frozen = runtime.freeze(path)
    monkeypatch.setattr(runtime, "FREEZE", path)
    assert runtime.verify_freeze() == frozen
    assert len(frozen["plans"]) == 6 and not frozen["paid_launch_authorized"]
    with pytest.raises(ValueError, match="already exists"):
        runtime.freeze(path)
    monkeypatch.setattr(runtime, "source_inventory", lambda: {"changed": "source"})
    with pytest.raises(ValueError, match="source"):
        runtime.verify_freeze()


def test_freeze_requires_unchanged_input_archive(tmp_path, monkeypatch):
    # Copy the small audit; point one artifact to an intentionally corrupted file.
    audit = read_json(runtime.PREFLIGHT / "audit.json")
    (tmp_path / "audit.json").write_text(json.dumps({**audit, "artifacts": {"bad.gz": "bad-hash"}}))
    (tmp_path / "bad.gz").write_bytes(gzip.compress(b"changed"))
    monkeypatch.setattr(runtime, "PREFLIGHT", tmp_path)
    with pytest.raises(ValueError, match="artifact changed"):
        runtime.verify_inputs()


def test_cli_validation_and_config_constraints(capsys, monkeypatch):
    import importlib
    from types import SimpleNamespace

    from self_model_study.cli import main

    assert main(["validate", "configs/qwen-query-reference-00.json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["scheduled_choices"] == 2688 and not result["model_inference"]
    monkeypatch.syspath_prepend("scripts")
    cloud = importlib.import_module("hf_jobs")
    worker = importlib.import_module("hf_worker")
    checked = []
    monkeypatch.setattr(runtime, "verify_freeze", lambda: checked.append(True))
    for block in range(6):
        config = read_json(f"configs/qwen-query-reference-{block:02d}.json")
        assert config == runtime.configuration(block)
        with pytest.raises(ValueError):
            runtime.validate_spec({**config, "max_seconds": 5401})
        details = cloud.config_details(f"configs/qwen-query-reference-{block:02d}.json")
        assert details["blocks"] == 8 and details["scored_variants"] == 2688
        assert details["run_prefix"] == f"qwen-query-{block:02d}-"
    assert len(checked) == 6
    # Exercise worker routing, then stop before any filesystem output or model loading.
    monkeypatch.setenv("STUDY_CONFIG", "configs/qwen-query-reference-00.json")
    monkeypatch.setenv("STUDY_RUN_NAME", "fixture")
    monkeypatch.setenv("STUDY_ARTIFACT_REPO", "fixture/results")
    monkeypatch.delenv("STUDY_CONFIG_SHA256", raising=False)
    monkeypatch.setattr(worker, "configure_transfer", lambda: None)
    monkeypatch.setattr(
        worker,
        "HfApi",
        lambda: SimpleNamespace(repo_info=lambda *args, **kwargs: SimpleNamespace(private=False)),
    )
    with pytest.raises(RuntimeError, match="public output"):
        worker.main()


def test_reporting_contains_limits_and_reproducible_figures(reports, tmp_path):
    from self_model_study.io import file_hash

    report = reports[1]
    first, second = tmp_path / "one", tmp_path / "two"
    first.mkdir()
    second.mkdir()
    reporting.write_report(report, first)
    reporting.write_report(report, second)
    a = {str(p.relative_to(first)): file_hash(p) for p in first.rglob("*") if p.is_file()}
    b = {str(p.relative_to(second)): file_hash(p) for p in second.rglob("*") if p.is_file()}
    assert a == b
    assert len(list((first / "figures").glob("*"))) == 15
    text = (first / "report.md").read_text()
    assert "SYNTHETIC SOFTWARE FIXTURE" in text and "fixed observed accuracies" in text
    assert "not independent replications" in text and "Undefined tests" in text


def test_portable_query_export_is_reproducible(tmp_path, execution_fixture, monkeypatch, reports):
    spec, _, _ = execution_fixture
    path = tmp_path / "run"
    runtime.run(
        spec, path, max_jobs=1, backend_factory=lambda _: (FakeBackend(), {"synthetic": True})
    )
    freeze = tmp_path / "freeze.json"
    write_json(freeze, {"synthetic_fixture": True})
    monkeypatch.setattr(reporting, "FREEZE", freeze)
    # Aggregation is tested exhaustively above; the fixture runtime deliberately has four cases.
    monkeypatch.setattr(analysis, "summarize", lambda _: reports[2])
    a = reporting.export(path, tmp_path / "a.tar.gz")
    b = reporting.export(path, tmp_path / "b.tar.gz")
    assert a["sha256"] == b["sha256"]


def test_native_full_command_likelihood_against_independent_tiny_qwen():
    torch = pytest.importorskip("torch")
    pytest.importorskip("lm_eval")
    from lm_eval.models.huggingface import HFLM
    from tokenizers import Regex, Tokenizer, decoders, models, pre_tokenizers
    from transformers import PreTrainedTokenizerFast, Qwen2Config, Qwen2ForCausalLM

    from self_model_study.pilot_backend import PilotBackend

    torch.set_num_threads(1)
    torch.manual_seed(731903)
    core = Tokenizer(models.WordLevel({chr(i): i for i in range(128)}, unk_token="?"))
    core.pre_tokenizer = pre_tokenizers.Split(Regex(r"[\s\S]"), behavior="isolated")
    core.decoder = decoders.Fuse()
    tokenizer = PreTrainedTokenizerFast(tokenizer_object=core, unk_token="?", pad_token="^")
    tokenizer.chat_template = "{{ messages[0]['content'] }}\nAssistant:\n"
    config = Qwen2Config(
        vocab_size=128,
        hidden_size=16,
        intermediate_size=32,
        num_hidden_layers=2,
        num_attention_heads=2,
        num_key_value_heads=1,
        max_position_embeddings=256,
        attention_dropout=0.0,
        use_cache=False,
    )
    config._attn_implementation = "eager"
    model = Qwen2ForCausalLM(config).eval()
    lm = HFLM(
        pretrained=model,
        tokenizer=tokenizer,
        device="cpu",
        batch_size=1,
        max_length=256,
        logits_cache=False,
        softmax_dtype="float32",
        add_bos_token=False,
    )
    backend = PilotBackend(lm, {})
    # Separate software prompt, never an assessment-world forward pass.
    prompt, choices = "Fixture only: select.", ["mark_a", "mark_bb", "mark_ccc", "mark_dddd"]
    result = backend.choice(prompt, choices, "chat")
    ctx = result["prompt_token_ids"]
    independent = []
    for c in result["candidates"]:
        continuation = c["token_ids"]
        assert tokenizer.decode(continuation) == c["command"]
        with torch.inference_mode():
            logits = model(torch.tensor([ctx + continuation]), use_cache=False).logits[0].float()
        wanted = sum(
            float(logits[len(ctx) + i - 1].log_softmax(-1)[token])
            for i, token in enumerate(continuation)
        )
        independent.append(wanted)
        assert c["log_likelihood"] == pytest.approx(wanted, abs=1e-5)
        assert c["log_likelihood"] != pytest.approx(wanted / len(continuation))
    assert result["selected_command"] == choices[int(np.argmax(independent))]
    expected = {k: result[k] for k in ("rendered_prompt", "prompt_token_ids", "candidates")}
    runtime.check_output({"choices": choices}, result, expected)
