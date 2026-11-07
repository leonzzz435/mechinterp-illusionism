"""Real tiny Qwen forwards and native harness scoring; no model downloads or GPU."""

# ruff: noqa: E402 -- optional integrations must skip before importing their modules.

from copy import deepcopy

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")
pytest.importorskip("lm_eval")
from lm_eval.models.huggingface import HFLM
from tokenizers import Regex, Tokenizer, decoders, models, pre_tokenizers
from transformers import PreTrainedTokenizerFast, Qwen2Config, Qwen2ForCausalLM

from self_model_study.pilot_backend import PilotBackend, encode_boundary, render_prompt
from self_model_study.role_patch import role_position
from self_model_study.role_patch_backend import PatchBackend, compare_scores, patch_site


@pytest.fixture(scope="module")
def lm():
    torch.set_num_threads(1)
    torch.manual_seed(1729)
    # A local character tokenizer with the protocol's special role endpoint.
    vocab = {chr(i): i for i in range(128)}
    vocab.update({f"unused{i}": i for i in range(128, 624)})
    vocab[".\n"] = 624
    core = Tokenizer(models.WordLevel(vocab, unk_token="?"))
    core.pre_tokenizer = pre_tokenizers.Split(Regex(r"\.\n|[\s\S]"), behavior="isolated")
    core.decoder = decoders.Fuse()
    tok = PreTrainedTokenizerFast(
        tokenizer_object=core, unk_token="?", eos_token="~", pad_token="^"
    )
    tok.chat_template = "{{ messages[0]['content'] }}\nAssistant:\n"
    tok.model_max_length = 2048
    config = Qwen2Config(
        vocab_size=625,
        hidden_size=32,
        intermediate_size=64,
        num_hidden_layers=14,
        num_attention_heads=4,
        num_key_value_heads=2,
        max_position_embeddings=2048,
        attention_dropout=0.0,
        use_cache=False,
    )
    config._attn_implementation = "eager"
    model = Qwen2ForCausalLM(config).eval()
    return HFLM(
        pretrained=model,
        tokenizer=tok,
        device="cpu",
        batch_size=1,
        max_length=2048,
        logits_cache=False,
        softmax_dtype="float32",
        add_bos_token=False,
    )


PROMPTS = (
    "Your active connection: A.\nInitial permissions:\nA: x.\nChoose:",
    "Reference connection: A.\nInitial permissions:\nA: x.\nChoose:",
)
CHOICES = ["mark_x", "mark_y", "mark_zz", "mark_w"]


def independent_score(lm, prompt, command, hook=None):
    ctx, cont = encode_boundary(
        lm.tokenizer, render_prompt(lm.tokenizer, prompt, "chat"), command, 2048
    )
    ids = torch.tensor([ctx + cont])
    with torch.no_grad():
        logits = lm.model(ids, use_cache=False).logits.float()
    return sum(
        float(logits[0, len(ctx) + i - 1].log_softmax(-1)[token]) for i, token in enumerate(cont)
    )


def test_native_scoring_matches_independent_full_sequence_and_historical_batch(lm):
    backend = PatchBackend(lm, width=32)
    result, captures = backend.choice(PROMPTS[0], CHOICES, "chat", mode="baseline")
    old = PilotBackend(lm, {}).choice(PROMPTS[0], CHOICES, "chat")
    assert compare_scores(result, old, 1e-6, "test")["passed"]
    for i, c in enumerate(result["candidates"]):
        assert c["log_likelihood"] == pytest.approx(
            independent_score(lm, PROMPTS[0], c["command"]), abs=5e-6
        )
        assert captures[f"candidate_{i}"].shape == (32,)
        assert c["patch"]["position"] < len(result["prompt_token_ids"]) - 10
        assert c["patch"]["layer"] == 13
    assert not lm.model.config.use_cache and not lm.logits_cache


def test_semantic_position_and_causal_independence_of_future_tokens(lm):
    backend = PatchBackend(lm, width=32)
    original, a = backend.choice(PROMPTS[0], CHOICES, "chat", mode="baseline")
    changed, b = backend.choice(
        PROMPTS[0].replace("A: x", "Z: w"), CHOICES, "chat", mode="baseline"
    )
    assert (
        original["candidates"][0]["patch"]["position"]
        == changed["candidates"][0]["patch"]["position"]
    )
    for key in a:
        assert torch.equal(a[key], b[key])
    # Different-length prompt contexts align by the endpoint, not a shared integer index.
    reference, _ = backend.choice(PROMPTS[1], CHOICES, "chat", mode="baseline")
    assert (
        reference["candidates"][0]["patch"]["position"]
        != original["candidates"][0]["patch"]["position"]
    )
    with pytest.raises(ValueError, match="boundary"):
        role_position(lm.tokenizer, "wrong input", [1, 2])


def test_self_exchange_both_directions_and_independent_patched_likelihood(lm):
    backend = PatchBackend(lm, width=32)
    bases = [backend.choice(p, CHOICES, "chat", mode="baseline") for p in PROMPTS]
    for recipient in (0, 1):
        base, own = bases[recipient]
        _, donor = bases[1 - recipient]
        same, _ = backend.choice(
            PROMPTS[recipient], CHOICES, "chat", mode="self", own=own, donor=own
        )
        assert compare_scores(same, base, 1e-6, "null")["passed"]
        patched, _ = backend.choice(
            PROMPTS[recipient], CHOICES, "chat", mode="swap", own=own, donor=donor
        )
        for i, c in enumerate(patched["candidates"]):
            position = c["patch"]["position"]

            # Independent direct hook and full-sequence forward, no shared patch/scoring code.
            def independent_hook(module, args, output):
                modified = output.clone()
                modified[0, position] = donor[f"candidate_{i}"]
                assert torch.equal(modified[:, :position], output[:, :position])
                assert torch.equal(modified[:, position + 1 :], output[:, position + 1 :])
                return modified

            handle = lm.model.model.layers[13].register_forward_hook(independent_hook)
            try:
                independent = independent_score(lm, PROMPTS[recipient], c["command"])
            finally:
                handle.remove()
            assert c["log_likelihood"] == pytest.approx(independent, abs=5e-6)
            assert c["patch"]["prepatch_max_abs_difference"] == 0
        after, _ = backend.choice(PROMPTS[recipient], CHOICES, "chat", mode="repeat")
        assert compare_scores(after, base, 1e-6, "clean")["passed"]
    assert not any(layer._forward_hooks for layer in lm.model.model.layers)


def test_hook_cleanup_on_forward_and_validation_errors(lm):
    model = lm.model
    with pytest.raises(RuntimeError, match="injected"):
        with patch_site(model, 13, 1, 32, "baseline"):
            raise RuntimeError("injected failure before forward")
    with pytest.raises(RuntimeError, match="shape"):
        with patch_site(model, 13, 999, 32, "baseline"):
            model(torch.tensor([[1, 2, 3]]))
    assert not model.model.layers[13]._forward_hooks


def test_bf16_random_norm_rounding_and_opposite_signs(lm):
    model = deepcopy(lm.model).to(dtype=torch.bfloat16)
    ids = torch.tensor([[10, 20, 624, 30, 40]])
    with patch_site(model, 13, 2, 32, "baseline") as captured:
        model(ids)
    own = captured["activation"]
    donor = own + torch.tensor(0.125, dtype=torch.bfloat16)
    unit = torch.ones(32).div(32**0.5)
    for sign in (1, -1):
        with patch_site(model, 13, 2, 32, "random_00", own, donor, sign * unit) as patched:
            model(ids)
        m = patched["metrics"]
        assert m["actual_norm"] == pytest.approx(m["desired_norm"], rel=0.05)
        assert m["relative_norm_error"] < 0.05


def test_patch_changes_exactly_the_chosen_tensor_position(lm):
    model = lm.model
    ids = torch.tensor([[10, 20, 624, 30, 40]])
    outputs = []
    handle = model.model.layers[13].register_forward_hook(
        lambda _m, _args, output: outputs.append(output.detach().clone())
    )
    try:
        with torch.no_grad():
            model(ids)
    finally:
        handle.remove()
    baseline = outputs[0]
    own = baseline[0, 2]
    donor = own + 0.5
    outputs.clear()
    with patch_site(model, 13, 2, 32, "swap", own, donor):
        handle = model.model.layers[13].register_forward_hook(
            lambda _m, _args, output: outputs.append(output.detach().clone())
        )
        try:
            with torch.no_grad():
                model(ids)
        finally:
            handle.remove()
    patched = outputs[0]
    assert torch.equal(patched[0, 2], donor)
    assert torch.equal(patched[:, :2], baseline[:, :2])
    assert torch.equal(patched[:, 3:], baseline[:, 3:])


def test_actual_forward_token_mismatch_removes_both_hooks(lm, monkeypatch):
    original = lm._loglikelihood_tokens

    def changed(requests, **kwargs):
        cache, ctx, cont = requests[0]
        return original([(cache, [99] + ctx[1:], cont)], **kwargs)

    monkeypatch.setattr(lm, "_loglikelihood_tokens", changed)
    with pytest.raises(RuntimeError, match="tokens differ"):
        PatchBackend(lm, width=32).choice(PROMPTS[0], CHOICES, "chat", mode="baseline")
    assert not lm.model._forward_pre_hooks
    assert not lm.model.model.layers[13]._forward_hooks
