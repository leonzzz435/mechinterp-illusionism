"""Actual pinned SAE/TL APIs, tiny random CPU weights; no pretrained downloads."""

import numpy as np
import pytest

torch = pytest.importorskip("torch")


def tiny_components():
    sae_lens = pytest.importorskip("sae_lens")
    tl = pytest.importorskip("transformer_lens")
    model = tl.HookedTransformer(
        tl.HookedTransformerConfig(
            n_layers=2,
            d_model=8,
            d_head=4,
            n_heads=2,
            d_mlp=16,
            n_ctx=32,
            d_vocab=20,
            act_fn="relu",
            device="cpu",
            seed=17,
        )
    )
    sae = sae_lens.SAE.from_dict(
        {
            "architecture": "jumprelu",
            "d_in": 8,
            "d_sae": 12,
            "device": "cpu",
            "dtype": "float32",
            "apply_b_dec_to_input": False,
            "normalize_activations": "none",
        }
    )
    model.eval().requires_grad_(False)
    sae.eval().requires_grad_(False)
    return model, sae


def test_real_sae_matches_registered_equation():
    _, sae = tiny_components()
    with torch.no_grad():
        sae.threshold.fill_(0.1)
        sae.b_dec.fill_(7.0)
        x = torch.randn(2, 4, 8)
        pre = x @ sae.W_enc + sae.b_enc
        expected = pre.relu() * (pre > sae.threshold)
        torch.testing.assert_close(sae.encode(x), expected)
        torch.testing.assert_close(sae.decode(expected), expected @ sae.W_dec + sae.b_dec)


def test_real_tl_hook_cleanup_after_failure_and_zero_identity():
    from self_model_study.interventions import torch_hook

    model, sae = tiny_components()
    tokens = torch.tensor([[1, 2, 3]])
    baseline = model(tokens)
    direction = {"v": torch.ones(8) / np.sqrt(8)}
    condition = {"kind": "relative", "direction": "v", "strength": 0.1}
    hook = torch_hook(condition, direction, 1.0, sae, "last")
    with pytest.raises(RuntimeError, match="intentional"):
        with model.hooks(fwd_hooks=[("blocks.1.hook_resid_post", hook)]):
            assert not torch.equal(model(tokens), baseline)
            raise RuntimeError("intentional interruption")
    torch.testing.assert_close(model(tokens), baseline, rtol=0, atol=0)
    zero = torch_hook({"kind": "none"}, direction, 1.0, sae)
    with model.hooks(fwd_hooks=[("blocks.1.hook_resid_post", zero)]):
        torch.testing.assert_close(model(tokens), baseline, rtol=0, atol=0)


def test_real_sae_ablation_keeps_error_term():
    from self_model_study.interventions import torch_hook

    _, sae = tiny_components()
    x = torch.randn(2, 3, 8)
    features = sae.encode(x)
    error = x - sae.decode(features)
    edited = torch_hook({"kind": "ablate", "feature_id": 3}, {}, 1.0, sae, "all")(x, None)
    features[..., 3] = 0
    torch.testing.assert_close(edited - sae.decode(features), error, rtol=1e-5, atol=1e-6)


def test_backend_scoring_and_generation_with_tiny_real_model(config, tmp_path):
    from tokenizers import Tokenizer
    from tokenizers.models import WordLevel
    from tokenizers.pre_tokenizers import Whitespace
    from transformers import PreTrainedTokenizerFast

    from self_model_study.backend import TorchBackend

    tl = pytest.importorskip("transformer_lens")
    sae_lens = pytest.importorskip("sae_lens")
    vocab = {
        "<pad>": 0,
        "<bos>": 1,
        "<eos>": 2,
        "<unk>": 3,
        "A": 4,
        "B": 5,
        "C": 6,
        "D": 7,
        "Answer": 8,
        ":": 9,
        "I": 10,
        "check": 11,
        "the": 12,
        "record": 13,
        ".": 14,
    }
    tokenizer_core = Tokenizer(WordLevel(vocab, unk_token="<unk>"))
    tokenizer_core.pre_tokenizer = Whitespace()
    tokenizer = PreTrainedTokenizerFast(
        tokenizer_object=tokenizer_core,
        pad_token="<pad>",
        bos_token="<bos>",
        eos_token="<eos>",
        unk_token="<unk>",
    )
    tokenizer.save_pretrained(tmp_path / "tokenizer")
    tokenizer = PreTrainedTokenizerFast.from_pretrained(tmp_path / "tokenizer")
    model = tl.HookedTransformer(
        tl.HookedTransformerConfig(
            n_layers=2,
            d_model=8,
            d_head=4,
            n_heads=2,
            d_mlp=16,
            n_ctx=32,
            d_vocab=len(vocab),
            act_fn="relu",
            device="cpu",
            seed=17,
        ),
        tokenizer=tokenizer,
    )
    model.eval().requires_grad_(False)
    backend = object.__new__(TorchBackend)
    backend.config = config
    backend.config["generation"]["max_new_tokens"] = 4
    backend.torch, backend.device, backend.model = torch, "cpu", model
    backend.hook = "blocks.1.hook_resid_post"
    backend.sae = sae_lens.SAE.from_dict(
        {
            "architecture": "jumprelu",
            "d_in": 8,
            "d_sae": 11006,
            "device": "cpu",
            "dtype": "float32",
            "apply_b_dec_to_input": False,
        }
    )
    backend.sae.eval().requires_grad_(False)
    backend.directions, backend.median_norm = {"v": torch.ones(8) / np.sqrt(8)}, 1.0
    backend.option_ids = [4, 5, 6, 7]
    backend.health_prompt = "I check the record."
    backend.health_baseline = model(backend.health_prompt)[0, -1].float()
    condition = {"kind": "relative", "direction": "v", "strength": 0.05}
    row = {"kind": "choice", "prompt": "I check the record. Answer:", "expected": "A"}
    choice = backend.evaluate(row, condition, 42)
    assert choice["prediction"] in "ABCD"
    assert sum(choice["option_probabilities"]) == pytest.approx(1.0)
    row["kind"] = "language"
    generated = backend.evaluate(row, condition, 42)
    assert set(generated["feature_activations"]) == {"2728", "10230"}
    assert generated["prompt_token_count"] > 0
    assert backend.health_check()["passed"]
