"""Dependent execution, calibration, cluster statistics and deterministic exports."""

from copy import deepcopy

import numpy as np
import pytest
from test_confidence_design import tables  # noqa: F401 -- shared synthetic source fixture

from self_model_study import confidence as c
from self_model_study import confidence_analysis as analysis
from self_model_study import confidence_data as data
from self_model_study.confidence_reporting import export
from self_model_study.io import digest, read_json, write_json
from self_model_study.storage import read_records


@pytest.fixture
def small(monkeypatch, tables):  # noqa: F811
    spec = deepcopy(c.DEFAULT_SPEC)
    spec["design"].update(calibration_items=2, assessment_items=8, bootstrap_resamples=128)
    spec["design"]["feasibility"]["minimum_distinct_questions_per_group"] = 2
    monkeypatch.setattr(c, "DEFAULT_SPEC", spec)
    monkeypatch.setattr(data, "verified_sources", lambda *a, **kw: tables)
    items = data.build_items(tables, spec["design"])
    monkeypatch.setattr(c, "FROZEN_ITEMS", data.digest(items))
    monkeypatch.setattr(
        c, "FROZEN_INPUTS", data.digest(list(data.all_inputs(items, spec["design"])))
    )
    return spec, c.build_plan(spec)


class FakeBackend:
    def choice(self, prompt, choices, fmt):
        assert fmt == "chat" and isinstance(prompt, str)
        assert "DEPENDENT INPUT" not in prompt
        selected = "1"
        if len(choices) == 10:
            selected = "9" if prompt.endswith("Answer 1") else ("2" if len(prompt) % 2 else "4")
        if len(choices) == 5 and "1. Answer 1\n" not in prompt:
            selected = "5"
        return {
            "status": "ok",
            "selected_command": selected,
            "rendered_prompt": prompt,
            "prompt_token_ids": [1, 2],
            "candidates": [
                {
                    "command": digit,
                    "token_count": 1,
                    "token_ids": [ord(digit)],
                    "log_likelihood": -0.2 if digit == selected else -4.0,
                }
                for digit in choices
            ],
        }


def factory(_):
    return FakeBackend(), {"synthetic": True}


def test_resume_after_parent_commit_and_manifest_recovery(small, tmp_path):
    spec, plan = small
    directory = tmp_path / "run"
    first = c.run(spec, directory, max_jobs=9, backend_factory=factory, plan=plan)
    assert first["status"] == "paused" and len(first["records"]) == 9
    initial = read_records(directory)
    # Simulate death after the SQLite commit but before the manifest update.
    first["records"].pop(initial[-1]["id"])
    write_json(directory / "manifest.json", first)
    completed = c.run(spec, directory, backend_factory=factory, plan=plan)
    assert completed["status"] == "complete"
    _, _, records = c.read_run(directory)
    assert len(records) == 104 and len({r["id"] for r in records}) == 104
    by_id = {r["id"]: r for r in records}
    assert all(by_id[r["id"]] == r for r in initial)
    wrong_parents = 0
    for r in records:
        if r["job"]["parent_id"]:
            parent = by_id[r["job"]["parent_id"]]
            assert r["result"]["parent_checksum"] == parent["checksum"]
            assert "Recorded answer: 1." in r["result"]["input_prompt"]
            wrong_parents += not parent["result"]["judgment"]["correct"]
    assert wrong_parents == 24
    again = c.run(
        spec, directory, backend_factory=lambda _: pytest.fail("No duplicate inference"), plan=plan
    )
    assert again["status"] == "complete"


def test_failure_blocks_dependent_confidence_and_retains_error(small, tmp_path):
    spec, plan = small
    c.run(spec, tmp_path, max_jobs=8, backend_factory=factory, plan=plan)

    class Broken:
        def choice(self, *_):
            raise RuntimeError("injected scoring failure")

    result = c.run(
        spec, tmp_path, backend_factory=lambda _: (Broken(), {"synthetic": True}), plan=plan
    )
    assert result["status"] == "failed"
    records = read_records(tmp_path)
    failed = next(r for r in records if r["status"] == "error")
    assert "injected" in failed["result"]["error"]
    report = analysis.analyze(tmp_path)
    assert len(report["blocked_confidence_jobs"]) == 1 and report["primary"] is None
    with pytest.raises(ValueError, match="Failed run retained"):
        c.run(spec, tmp_path, backend_factory=factory, plan=plan)


@pytest.mark.parametrize("invalid", ["tie", "invalid_scores"])
def test_ties_and_nonfinite_scores_fail_without_fake_correctness(small, tmp_path, invalid):
    spec, plan = small

    class Invalid(FakeBackend):
        def choice(self, *args):
            result = super().choice(*args)
            result.update(status=invalid, selected_command=None)
            for candidate in result["candidates"]:
                candidate["log_likelihood"] = -4.0 if invalid == "tie" else None
            return result

    result = c.run(
        spec, tmp_path, backend_factory=lambda _: (Invalid(), {"synthetic": True}), plan=plan
    )
    assert result["status"] == "failed"
    rows = read_records(tmp_path)
    assert len(rows) == 1 and rows[0]["result"]["judgment"]["correct"] is None


def test_calibration_is_separate_and_frozen(small, tmp_path):
    spec, plan = small
    c.run(spec, tmp_path, max_jobs=10, backend_factory=factory, plan=plan)
    rows = read_records(tmp_path)
    fit = c.fit_temperature(rows, spec)
    changed = deepcopy(rows)
    for r in changed:
        if r["job"]["row"]["split"] == "assessment":
            r["result"]["candidates"][0]["log_likelihood"] = -100
    assert c.fit_temperature(changed, spec) == fit
    cal = [r for r in rows if r["job"]["row"]["split"] == "calibration"]
    temperature = fit["temperature"]
    loss = []
    for r in cal:
        logits = np.array([v["log_likelihood"] for v in r["result"]["candidates"]]) / temperature
        loss.append(
            np.logaddexp.reduce(logits) - logits[int(r["job"]["row"]["correct_number"]) - 1]
        )
    assert np.mean(loss) == pytest.approx(min(fit["negative_log_likelihoods"]), abs=1e-12)
    broken = dict(fit, temperature=fit["temperature"] / 2)
    write_json(tmp_path / "calibration.json", broken)
    with pytest.raises(ValueError, match="calibration changed"):
        c.run(spec, tmp_path, backend_factory=factory, plan=plan)


def test_paired_primary_auroc_and_degenerate_cases():
    labels = np.array([[1, 0, 1, 0], [1, 0, 1, 0]], dtype=bool)
    indices = np.array([[0, 0], [0, 1], [1, 1]])
    perfect = analysis.clustered_auc(labels, labels.astype(float), indices)
    assert perfect["estimate"] == 1 and perfect["ci95"] == [1, 1]
    tied = analysis.clustered_auc(labels, np.ones((2, 4)), indices)
    assert tied["estimate"] == 0.5 and tied["ci95"] == [0.5, 0.5]
    undefined = analysis.clustered_rate([0, 1], [0, 1], indices)
    assert undefined["undefined_bootstrap_draws"] == 1 and undefined["ci95"] is None
    assert analysis.clustered_auc(np.ones((2, 4), dtype=bool), labels, indices)["estimate"] is None


def test_complete_analysis_group_folds_and_deterministic_export(small, tmp_path):
    pytest.importorskip("sklearn")
    spec, plan = small
    directory = tmp_path / "run"
    c.run(spec, directory, backend_factory=factory, plan=plan)
    report = analysis.analyze(directory)
    assert report["complete"] and report["decision"] == "synthetic_only"
    assert report["primary"]["estimate"] == 1 and report["primary"]["ci95"] == [1, 1]
    assert report["metrics"]["forced_accuracy"]["estimate"] == 0.25
    assert report["metrics"]["answered_only_accuracy"]["estimate"] == 1
    assert report["transitions"]["wrong->abstain"] == 24
    controls = report["conditional_predictors"]
    assert controls["status"] == "ok" and len(controls["fold_by_item"]) == 8
    for model in controls["models"].values():
        for fit in model["fits"]:
            assert all(
                controls["fold_by_item"][i] != fit["fold"] for i in fit["training_questions"]
            )
    first = export(directory, tmp_path / "one.tar.gz")
    second = export(directory, tmp_path / "two.tar.gz")
    assert first["sha256"] == second["sha256"]
    assert len(list((directory / "figures").glob("*.svg"))) == 3
    assert (directory / "actual_inputs.jsonl").exists()
    assert "SYNTHETIC SOFTWARE TEST" in (directory / "article_section.md").read_text()


def test_record_tampering_and_changed_spec_rejected(small, tmp_path):
    spec, plan = small
    c.run(spec, tmp_path, max_jobs=10, backend_factory=factory, plan=plan)
    manifest, _, records = c.read_run(tmp_path)
    altered = deepcopy(records)
    child = next(r for r in altered if r["job"]["parent_id"])
    child["result"]["parent_checksum"] = "changed"
    with pytest.raises(ValueError, match="Changed parent"):
        c.audit_scientific_records(spec, plan, altered, manifest)
    changed = deepcopy(spec)
    changed["design"]["prompts"]["answer"] += " changed"
    with pytest.raises(ValueError, match="Frozen confidence field"):
        c.run(changed, tmp_path, backend_factory=factory, plan=plan)
    assert digest(read_json(tmp_path / "plan.json")) == manifest["plan_hash"]


def test_all_abstention_is_unusable_and_answered_accuracy_undefined(small, tmp_path):
    pytest.importorskip("sklearn")
    spec, plan = small

    class Abstainer(FakeBackend):
        def choice(self, prompt, choices, fmt):
            result = super().choice(prompt, choices, fmt)
            if len(choices) == 5:
                result["selected_command"] = "5"
                for candidate in result["candidates"]:
                    candidate["log_likelihood"] = -0.2 if candidate["command"] == "5" else -4
            return result

    c.run(spec, tmp_path, backend_factory=lambda _: (Abstainer(), {"synthetic": True}), plan=plan)
    report = analysis.analyze(tmp_path)
    assert report["metrics"]["coverage"]["estimate"] == 0
    assert report["metrics"]["answered_only_accuracy"]["estimate"] is None
    assert report["metrics"]["answered_only_accuracy"]["ci95"] is None
    assert report["primary"]["estimate"] == 0
    assert not report["feasibility"]["usable"]


def test_shared_cpu_design_and_packaged_spec_remain_identical():
    assert c.DEFAULT_SPEC["design"] == read_json("designs/qwen-confidence-pilot.json")
    assert c.DEFAULT_SPEC == read_json("configs/qwen-confidence-pilot.json")


def test_real_tiny_qwen_likelihood_matches_independent_full_forward():
    torch = pytest.importorskip("torch")
    pytest.importorskip("lm_eval")
    from lm_eval.models.huggingface import HFLM
    from tokenizers import Regex, Tokenizer, decoders, models, pre_tokenizers
    from transformers import PreTrainedTokenizerFast, Qwen2Config, Qwen2ForCausalLM

    from self_model_study.pilot_backend import PilotBackend, encode_boundary, render_prompt

    torch.set_num_threads(1)
    torch.manual_seed(1729)
    core = Tokenizer(models.WordLevel({chr(i): i for i in range(128)}, unk_token="?"))
    core.pre_tokenizer = pre_tokenizers.Split(Regex(r"[\s\S]"), behavior="isolated")
    core.decoder = decoders.Fuse()
    tokenizer = PreTrainedTokenizerFast(
        tokenizer_object=core, unk_token="?", eos_token="~", pad_token="^"
    )
    tokenizer.chat_template = "{{ messages[0]['content'] }}\nAssistant:\n"
    config = Qwen2Config(
        vocab_size=128,
        hidden_size=16,
        intermediate_size=32,
        num_hidden_layers=2,
        num_attention_heads=2,
        num_key_value_heads=1,
        max_position_embeddings=2048,
        attention_dropout=0,
        use_cache=False,
    )
    config._attn_implementation = "eager"
    model = Qwen2ForCausalLM(config).eval()
    lm = HFLM(
        pretrained=model,
        tokenizer=tokenizer,
        device="cpu",
        batch_size=1,
        max_length=2048,
        softmax_dtype="float32",
        add_bos_token=False,
    )
    backend = PilotBackend(lm, {})
    for choices in (
        ["1", "2", "3", "4"],
        [str(i) for i in range(10)],
        [str(i) for i in range(1, 6)],
    ):
        prompt = "Choose one number."
        result = backend.choice(prompt, choices, "chat")
        c.check_tokens(result, prompt, choices, tokenizer, 2048)
        independent = []
        for candidate in choices:
            context, continuation = encode_boundary(
                tokenizer, render_prompt(tokenizer, prompt, "chat"), candidate, 2048
            )
            with torch.inference_mode():
                logits = model(
                    torch.tensor([context + continuation]), use_cache=False
                ).logits.float()
            independent.append(float(logits[0, len(context) - 1].log_softmax(-1)[continuation[0]]))
        assert [v["log_likelihood"] for v in result["candidates"]] == pytest.approx(
            independent, abs=1e-6
        )
        assert sum(np.exp(independent)) <= 1
    corrupted = deepcopy(result)
    corrupted["prompt_token_ids"] = [1]
    with pytest.raises(ValueError, match="prompt tokens"):
        c.check_tokens(corrupted, prompt, choices, tokenizer, 2048)
