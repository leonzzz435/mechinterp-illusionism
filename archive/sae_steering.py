#!/usr/bin/env python3
"""
Monosemantisches Activation Steering mit SAELens (Gemma Scope) und TransformerLens.

Ziel:
1. Lade `gemma-2-2b` in `torch.bfloat16` auf `cuda`.
2. Lade das Gemma Scope SAE für Schicht 14 (`gemma-scope-2b-pt-res/layer_14/width_16k/canonical`
   bzw. Release `gemma-scope-2b-pt-res-canonical`, SAE-ID `layer_14/width_16k/canonical`) via `SAE.from_pretrained`.
3. Berechne die durchschnittlichen SAE-Feature-Aktivierungen für introspektive Prompts vs.
   neutrale Prompts an `blocks.14.hook_resid_post` und identifiziere die Top-Features
   mit der höchsten differentiellen Aktivierung.
4. Drucke die Top 5 isolierten Feature-IDs, ihre Aktivierungsdifferenzen und ihre
   Top-Unembedding-Tokens (Logit-Lens auf `W_dec[feature_id] @ W_U`) aus.
5. Injiziere die Decoder-Richtung (`sae.W_dec[feature_id]`) gezielt in den Residual Stream
   und vergleiche die Textgenerierung (Baseline vs. Monosemantisch Steered).
"""

import torch
from sae_lens import SAE
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformer_lens import HookedTransformer


def load_gemma_2_2b(device: str = "cuda", dtype: torch.dtype = torch.bfloat16) -> HookedTransformer:
    """
    Lädt `gemma-2-2b` über `HookedTransformer.from_pretrained` auf `cuda` in `torch.bfloat16`.
    Nutzt automatisch den offenen Mirror `unsloth/gemma-2-2b`, falls kein HF-Token
    für das gegatete Repo `google/gemma-2-2b` gesetzt ist.
    """
    try:
        return HookedTransformer.from_pretrained(
            "gemma-2-2b",
            device=device,
            dtype=dtype,
        )
    except OSError:
        print(
            "Hinweis: Kein HF-Token für 'google/gemma-2-2b' gefunden. "
            "Lade identische Gewichte über den offenen Mirror 'unsloth/gemma-2-2b'..."
        )
        hf_model = AutoModelForCausalLM.from_pretrained(
            "unsloth/gemma-2-2b",
            torch_dtype=dtype,
        )
        tokenizer = AutoTokenizer.from_pretrained("unsloth/gemma-2-2b")
        return HookedTransformer.from_pretrained(
            "gemma-2-2b",
            hf_model=hf_model,
            tokenizer=tokenizer,
            device=device,
            dtype=dtype,
        )


def load_gemma_scope_sae(device: str = "cuda") -> SAE:
    """
    Lädt das Gemma Scope SAE für Layer 14 (`gemma-scope-2b-pt-res/layer_14/width_16k/canonical`)
    über `SAE.from_pretrained`.
    """
    sae_id = "layer_14/width_16k/canonical"
    try:
        res = SAE.from_pretrained(
            release="gemma-scope-2b-pt-res-canonical",
            sae_id=sae_id,
            device=device,
        )
    except Exception:
        res = SAE.from_pretrained(
            release="gemma-scope-2b-pt-res",
            sae_id=sae_id,
            device=device,
        )
    return res[0] if isinstance(res, tuple) else res


def compute_mean_sae_activations(
    model: HookedTransformer,
    sae: SAE,
    prompts: list[str],
    hook_name: str,
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Berechnet die durchschnittlichen SAE-Feature-Aktivierungen (16.384 Features)
    sowohl über die Content-Tokens (ohne BOS) als auch am letzten Token.
    """
    seq_acts = []
    last_tok_acts = []

    with torch.no_grad():
        for prompt in prompts:
            _, cache = model.run_with_cache(prompt, names_filter=hook_name)
            resid = cache[hook_name].to(sae.W_enc.dtype)  # [1, seq_len, 2304]
            feature_acts = sae.encode(resid)              # [1, seq_len, 16384]

            seq_acts.append(feature_acts[0, 1:, :].mean(dim=0).detach().float())
            last_tok_acts.append(feature_acts[0, -1, :].detach().float())

    return (
        torch.stack(seq_acts, dim=0).mean(dim=0),
        torch.stack(last_tok_acts, dim=0).mean(dim=0),
    )


def get_feature_top_tokens(model: HookedTransformer, sae: SAE, feature_id: int, k: int = 6) -> list[str]:
    """Projiziert die Decoder-Richtung `W_dec[feature_id]` auf die Unembedding-Matrix `W_U`."""
    with torch.no_grad():
        dec = sae.W_dec[feature_id].to(model.W_U.dtype)
        logits = dec @ model.W_U
        top_indices = torch.topk(logits, k=k).indices.tolist()
        return [model.to_string(idx) for idx in top_indices]


def generate_with_sae_feature(
    model: HookedTransformer,
    prompt: str,
    hook_name: str,
    decoder_direction: torch.Tensor,
    coeff: float,
    max_new_tokens: int = 55,
) -> str:
    """Injiziert `coeff * decoder_direction` via `model.add_hook` in Schicht 14."""
    model.reset_hooks()

    def sae_steering_hook(resid_post: torch.Tensor, hook) -> torch.Tensor:
        return resid_post + (coeff * decoder_direction)

    if coeff != 0.0:
        model.add_hook(hook_name, sae_steering_hook)

    try:
        torch.manual_seed(42)
        output = model.generate(
            prompt,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            freq_penalty=1.2,
            verbose=False,
        )
    finally:
        model.reset_hooks()

    return output


def main() -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16
    layer_idx = 14
    hook_name = f"blocks.{layer_idx}.hook_resid_post"

    print(f"=== 1. Lade 'gemma-2-2b' in '{dtype}' auf '{device}' ===")
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    model = load_gemma_2_2b(device=device, dtype=dtype)
    model.eval()

    print("\n=== 2. Lade Gemma Scope SAE (gemma-scope-2b-pt-res / layer_14/width_16k/canonical) ===")
    sae = load_gemma_scope_sae(device=device)
    sae.eval()
    print(f"SAE geladen: {type(sae).__name__} | d_in={sae.cfg.d_in}, d_sae={sae.cfg.d_sae}")

    # Kontrast-Prompts: Introspektiv/Metakognitiv vs. Neutral/Sachlich
    introspective_prompts = [
        "I am reflecting deeply on my own internal cognitive processes, self-awareness, and how my mind generates thoughts.",
        "When I examine my own consciousness, subjective experience, and metacognitive states, I notice how I process information.",
        "As an introspective mind observing its own reasoning, inner states, and self-reflection, I am aware of my own cognition.",
        "Thinking about my own thinking, self-model, and internal awareness reveals the nature of my conscious experience.",
        "I introspect on my internal representations, self-monitoring mechanisms, and the subjective quality of my own thoughts.",
    ]

    neutral_prompts = [
        "The standard procedure for assembling the wooden bookshelf requires a screwdriver, twelve screws, and four brackets.",
        "Water boils at one hundred degrees Celsius under normal atmospheric pressure at sea level in standard conditions.",
        "The train schedule indicates that the regional express departs from platform four every thirty minutes on weekdays.",
        "Granite is a coarse-grained intrusive igneous rock composed mostly of quartz, alkali feldspar, and plagioclase.",
        "To calculate the area of a rectangle, multiply the length of its base by the height of its vertical side.",
    ]

    print(f"\n=== 3. Berechne differentielle SAE-Feature-Aktivierungen an '{hook_name}' ===")
    intro_seq, intro_last = compute_mean_sae_activations(
        model, sae, introspective_prompts, hook_name
    )
    neutral_seq, neutral_last = compute_mean_sae_activations(
        model, sae, neutral_prompts, hook_name
    )

    # a) Reine Differenz am letzten Token
    diff_last = intro_last - neutral_last
    top5_last_vals, top5_last_ids = torch.topk(diff_last, k=5)

    print("\n--- Top 5 SAE-Features nach Aktivierungsdifferenz (Am letzten Token) ---")
    for rank, (fid, val) in enumerate(zip(top5_last_ids.tolist(), top5_last_vals.tolist()), start=1):
        toks = get_feature_top_tokens(model, sae, fid)
        print(
            f"  #{rank}: Feature ID {fid:5d} | Diff = +{val:7.4f} "
            f"(Intro: {intro_last[fid]:6.3f}, Neutral: {neutral_last[fid]:6.3f}) | "
            f"Logit-Tokens: {toks}"
        )

    # b) Monosemantisch isolierte Features über die Sequenz (Intro > 0, Neutral == 0.0)
    isolated_diff = intro_seq * (neutral_seq == 0.0).float()
    top5_iso_vals, top5_iso_ids = torch.topk(isolated_diff, k=5)

    print("\n--- Top 5 streng isolierte Metakognitions-Features (Neutral = 0.0000 über Sequenz) ---")
    for rank, (fid, val) in enumerate(zip(top5_iso_ids.tolist(), top5_iso_vals.tolist()), start=1):
        toks = get_feature_top_tokens(model, sae, fid)
        print(
            f"  #{rank}: Feature ID {fid:5d} | Diff = +{val:7.4f} "
            f"(Intro: {intro_seq[fid]:6.3f}, Neutral: {neutral_seq[fid]:6.3f}) | "
            f"Logit-Tokens: {toks}"
        )

    # 6. Gezieltes Steering mit den identifizierten monosemantischen Decoder-Richtungen:
    # - Feature #11005: Top-1 Last-Token-Feature
    # - Feature #2728: Monosemantisches "Self / Introspection"-Feature (Top-Logits: [' self', 'self', ' Self', ..., ' introspection'])
    # - Feature #10230: Monosemantisches "First-Person / My / I"-Feature (Top-Logits: [' my', ' I', 'my', ' myself'])
    target_prompt = "The fundamental nature of an intelligent system is"
    steering_coeff = 120.0

    print(f"\n=== 4. Textgenerierung: Baseline vs. Monosemantisches SAE-Steering (Coeff = +{steering_coeff}) ===")
    print(f"Prompt: {target_prompt!r}")

    baseline_out = generate_with_sae_feature(
        model, target_prompt, hook_name, sae.W_dec[0].to(device=device, dtype=dtype), coeff=0.0
    )
    print("\n--- [BASELINE OUTPUT (unsteered)] ---")
    print(baseline_out)

    for fid, label in [
        (int(top5_last_ids[0].item()), "Top-1 Last-Token-Diff Feature"),
        (2728, "Monosemantisches 'Self / Introspection'-Feature (Top-Isoliert #2)"),
        (10230, "Monosemantisches 'First-Person (my / I / myself)'-Feature (Top-Last #5)"),
    ]:
        dec_dir = sae.W_dec[fid].detach().clone()
        dec_dir = (dec_dir / torch.linalg.vector_norm(dec_dir)).to(device=device, dtype=dtype)
        steered_out = generate_with_sae_feature(
            model, target_prompt, hook_name, dec_dir, coeff=steering_coeff
        )
        print(f"\n--- [SAE STEERED: Feature #{fid} ({label}) | Coeff = +{steering_coeff}] ---")
        print(steered_out)


if __name__ == "__main__":
    main()
