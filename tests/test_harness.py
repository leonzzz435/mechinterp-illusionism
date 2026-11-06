import hashlib
import json
import tarfile
from copy import deepcopy
from pathlib import Path

import pytest

from self_model_study.harness import (
    audit_samples,
    build_plan,
    evaluate_block,
    export,
    load_spec,
    plain,
    run,
    summarize,
    task_config,
)
from self_model_study.io import read_json, write_json


@pytest.fixture
def spec():
    return load_spec(Path("configs/harness-baseline.json"))


def test_plan_has_disjoint_demos_balanced_complete_development_blocks(spec):
    plan = build_plan(spec)
    assert plan == build_plan(spec)
    assert len(plan["blocks"]) == 24
    assert sum(len(b["rows"]) for b in plan["blocks"]) == 768
    scored = {r["scenario_id"] for b in plan["blocks"] for r in b["rows"]}
    shown = {r["scenario_id"] for demos in plan["demonstrations"].values() for r in demos}
    assert scored.isdisjoint(shown)
    assert all(":development:" in sid for sid in scored | shown)
    for demos in plan["demonstrations"].values():
        assert [d["gold"] for d in demos] == list(range(4))
        assert len({d["scenario_id"] for d in demos}) == 4
        assert sum(d["view"] == "self" for d in demos) == 2
    for block in plan["blocks"]:
        assert len(block["rows"]) == 32
        assert [sum(r["gold"] == i for r in block["rows"]) for i in range(4)] == [8] * 4


def test_config_rejects_protocol_drift(spec, tmp_path):
    for key, value in [
        ("target_delimiter", ""),
        ("num_fewshot", 0),
        ("evaluation_scenarios", [36]),
        ("harness_version", "main"),
    ]:
        changed = {**spec, key: value}
        write_json(tmp_path / "bad.json", changed)
        with pytest.raises(ValueError):
            load_spec(tmp_path / "bad.json")


def fake_evaluate(model, task, spec):
    """Fabricated perfect outputs for journaling tests only; never a CLI backend."""
    rows = read_json(task["dataset_kwargs"]["data_files"]["development"])
    demos = task["fewshot_config"]["samples"]
    prefix = "\n\n".join(d["prompt"] + " " + "ABCD"[d["gold"]] for d in demos) + "\n\n"
    samples = []
    for row in rows:
        samples.append(
            {
                "doc": row,
                "target": row["gold"],
                "acc": 1,
                "arguments": [[prefix + row["prompt"], " " + label] for label in "ABCD"],
                "filtered_resps": [[-0.5 if i == row["gold"] else -2.0, False] for i in range(4)],
            }
        )
    return {"samples": {task["task"]: samples}, "results": {task["task"]: {"acc,none": 1.0}}}


def test_resume_partial_export_error_retention_and_checksum(spec, tmp_path):
    pytest.importorskip("lm_eval")

    def factory(spec):
        return None, {"test_fixture": True}

    directory = tmp_path / "fixture"
    # An interruption before manifest creation must allow initialization again.
    (directory / "source/self_model_study").mkdir(parents=True)
    write_json(directory / "plan.json", {"incomplete_setup_fixture": True})
    assert run(spec, directory, 1, factory, fake_evaluate)["status"] == "paused"
    first = (directory / "blocks/ownership-0000.json").read_bytes()
    assert run(spec, directory, 1, factory, fake_evaluate)["status"] == "paused"
    assert (directory / "blocks/ownership-0000.json").read_bytes() == first
    summary = summarize(directory)
    assert summary["n_trials"] == 64
    assert not summary["development_screen_passed"]
    assert not summary["confirmatory_evidence"]
    export(directory, tmp_path / "partial.tar.gz")
    assert "paused" in (directory / "report.md").read_text()
    assert "| access | 0 | missing | missing | missing |" in (directory / "report.md").read_text()
    with tarfile.open(tmp_path / "partial.tar.gz") as archive:
        checksums = json.load(archive.extractfile("fixture/checksums.json"))
        assert "figures/harness_baseline.svg" in checksums
        assert "figures/harness_baseline.pdf" in checksums
        assert "figures/harness_baseline.png" in checksums
        for name, expected in checksums.items():
            assert (
                hashlib.sha256(archive.extractfile("fixture/" + name).read()).hexdigest()
                == expected
            )
    assert run(spec, directory, None, factory, fake_evaluate)["status"] == "complete"
    assert summarize(directory)["development_screen_passed"]
    assert summarize(directory)["n_trials"] == 768
    assert not summarize(directory)["confirmatory_evidence"]
    changed = deepcopy(spec)
    changed["seed"] += 1
    with pytest.raises(ValueError, match="changed harness"):
        run(changed, directory, 1, factory, fake_evaluate)
    bad = directory / "blocks/ownership-0000.json"
    payload = read_json(bad)
    payload["seconds"] += 1
    write_json(bad, payload)
    with pytest.raises(ValueError, match="checksum"):
        summarize(directory)
    failed = tmp_path / "failed"

    def fails(*args):
        raise RuntimeError("intentional fixture failure")

    with pytest.raises(RuntimeError):
        run(spec, failed, 1, factory, fails)
    with pytest.raises(ValueError, match="No automatic retry"):
        run(spec, failed, 1, factory, fake_evaluate)
    assert read_json(failed / "error.json")["message"] == "intentional fixture failure"


def test_real_harness_multitoken_likelihood_and_task_scoring(spec, tmp_path):
    torch = pytest.importorskip("torch")
    pytest.importorskip("lm_eval")
    from lm_eval.models.huggingface import HFLM
    from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers
    from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast

    # Byte-level tokenizer without merges: " A" has TWO tokens. This catches
    # regressions to the historical single-token-only scoring assumption.
    core = Tokenizer(models.BPE(unk_token="<unk>"))
    core.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    core.decoder = decoders.ByteLevel()
    core.train_from_iterator(
        ["Question: Answer: A B C D"],
        trainers.BpeTrainer(
            vocab_size=260,
            initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
            special_tokens=["<pad>", "<bos>", "<eos>", "<unk>"],
        ),
    )
    tokenizer = PreTrainedTokenizerFast(
        tokenizer_object=core,
        pad_token="<pad>",
        bos_token="<bos>",
        eos_token="<eos>",
        unk_token="<unk>",
    )
    assert len(tokenizer.encode(" A", add_special_tokens=False)) == 2
    torch.manual_seed(17)
    model = GPT2LMHeadModel(
        GPT2Config(
            vocab_size=len(tokenizer),
            n_layer=1,
            n_embd=8,
            n_head=1,
            n_positions=512,
            bos_token_id=1,
            eos_token_id=2,
        )
    ).eval()
    lm = HFLM(
        pretrained=model,
        tokenizer=tokenizer,
        device="cpu",
        batch_size=1,
        max_length=512,
        add_bos_token=True,
        softmax_dtype="float32",
    )
    plan = build_plan(spec)
    block = deepcopy(plan["blocks"][0])
    block["rows"] = block["rows"][:2]
    demos = deepcopy(plan["demonstrations"]["ownership"])
    for i, row in enumerate(demos + block["rows"]):
        row["prompt"] = f"Question {i}. Answer:"
    data = tmp_path / "development.json"
    write_json(data, block["rows"])
    result = evaluate_block(lm, task_config(block, demos, data), spec)
    samples = audit_samples(result, block, demos)
    assert len(samples) == 2
    assert result["configs"]["context_self_ownership"]["output_type"] == "multiple_choice"
    # Independent teacher-forced oracle checks the complete continuation,
    # including the leading space; only a test implements this arithmetic.
    context, continuation = samples[0]["arguments"][0]
    ctx, cont = lm._encode_pair(context, continuation)
    assert len(cont) == 2
    tokens = torch.tensor([ctx + cont])
    with torch.inference_mode():
        logp = model(tokens).logits[0].log_softmax(-1)
        expected = sum(logp[len(ctx) - 1 + i, token].item() for i, token in enumerate(cont))
    assert samples[0]["filtered_resps"][0][0] == pytest.approx(expected, abs=1e-5)
    tampered = deepcopy(result)
    tampered["samples"]["context_self_ownership"][0]["arguments"][0][1] = "A"
    with pytest.raises(ValueError, match="prompt/continuation"):
        audit_samples(tampered, block, demos)
    assert plain(result) == result
    lm._max_length = 10
    with pytest.raises(ValueError, match="no truncation"):
        evaluate_block(lm, task_config(block, demos, data), spec)
