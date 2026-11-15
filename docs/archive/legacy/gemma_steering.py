#!/usr/bin/env python3
"""
Activation Steering Experiment mit Google DeepMind's Gemma 2 2B via TransformerLens.

Schritte:
1. Lade `gemma-2-2b` über `HookedTransformer.from_pretrained` auf `cuda` in `torch.bfloat16`.
2. Berechne die Mean-Difference zwischen introspektiven und neutralen Prompts an Schicht 14
   (`blocks.14.hook_resid_post`) am letzten Token -> 2304-dimensionaler Metakognitions-Vektor.
3. Normalisiere den Vektor auf L2-Norm = 1.0.
4. Injiziere den Vektor mit Koeffizient +4.0 (sowie zusätzlich norm-skaliert) über `model.add_hook`
   in Schicht 14 während der Generierung für "The fundamental nature of an intelligent system is".
5. Drucke den Baseline-Output im Vergleich zum Steered-Output aus.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformer_lens import HookedTransformer


def load_gemma_2_2b(device: str = "cuda", dtype: torch.dtype = torch.bfloat16) -> HookedTransformer:
    """
    Lädt `gemma-2-2b` über `HookedTransformer.from_pretrained` auf `cuda` in `torch.bfloat16`.
    Falls kein Hugging-Face-Token für das gegatete Repo `google/gemma-2-2b` hinterlegt ist,
    wird automatisch das identische, frei zugängliche Mirror-Repo `unsloth/gemma-2-2b` genutzt.
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


def generate_with_steering(
    model: HookedTransformer,
    prompt: str,
    hook_name: str,
    steering_vec: torch.Tensor,
    coeff: float,
    max_new_tokens: int = 50,
) -> str:
    """Führt `model.generate` mit einem via `model.add_hook` registrierten Steering-Hook aus."""
    model.reset_hooks()

    def steering_hook(resid_post: torch.Tensor, hook) -> torch.Tensor:
        return resid_post + (coeff * steering_vec)

    if coeff != 0.0:
        model.add_hook(hook_name, steering_hook)

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

    print(f"=== 1. Lade 'gemma-2-2b' auf '{device}' in '{dtype}' ===")
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    model = load_gemma_2_2b(device=device, dtype=dtype)
    model.eval()

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

    print(f"\n=== 2. Berechne Metakognitions-Vektor an '{hook_name}' (letztes Token) ===")
    intro_vecs = []
    for p in introspective_prompts:
        _, cache = model.run_with_cache(p, names_filter=hook_name)
        intro_vecs.append(cache[hook_name][0, -1, :].detach().float())

    neutral_vecs = []
    for p in neutral_prompts:
        _, cache = model.run_with_cache(p, names_filter=hook_name)
        neutral_vecs.append(cache[hook_name][0, -1, :].detach().float())

    mean_intro = torch.stack(intro_vecs, dim=0).mean(dim=0)
    mean_neutral = torch.stack(neutral_vecs, dim=0).mean(dim=0)

    # Mean-Difference Vektor (2304-dimensional)
    metacog_vec = mean_intro - mean_neutral
    raw_norm = torch.linalg.vector_norm(metacog_vec).item()
    print(f"Vektor-Shape: {tuple(metacog_vec.shape)} (d_model = {model.cfg.d_model})")
    print(f"L2-Norm vor Normalisierung: {raw_norm:.6f}")

    # 3. Normalisiere den Vektor auf L2-Norm = 1.0
    metacog_vec = metacog_vec / torch.linalg.vector_norm(metacog_vec)
    norm_after = torch.linalg.vector_norm(metacog_vec).item()
    print(f"L2-Norm nach Normalisierung: {norm_after:.6f}")

    metacog_vec = metacog_vec.to(device=device, dtype=dtype)

    # Prüfe zusätzlich die natürliche Residual-Stream-Norm in Layer 14 von Gemma 2 2B
    target_prompt = "The fundamental nature of an intelligent system is"
    _, prompt_cache = model.run_with_cache(target_prompt, names_filter=hook_name)
    resid_norm_l14 = prompt_cache[hook_name][0, -1, :].float().norm().item()
    print(f"Natürliche Residual-Stream L2-Norm an Layer 14: {resid_norm_l14:.2f}")

    # 4. & 5. Generierung: Baseline vs. Steered (+4.0 auf Einheitsvektor & +180.0 ~ 1x Residual-Norm)
    print(f"\n=== 3. Generierung für Prompt: {target_prompt!r} ===")

    baseline_out = generate_with_steering(
        model, target_prompt, hook_name, metacog_vec, coeff=0.0
    )
    steered_out_4 = generate_with_steering(
        model, target_prompt, hook_name, metacog_vec, coeff=4.0
    )
    steered_out_scaled = generate_with_steering(
        model, target_prompt, hook_name, metacog_vec, coeff=180.0
    )

    print("\n--- [1] BASELINE OUTPUT (Coeff = 0.0) ---")
    print(baseline_out)

    print("\n--- [2] STEERED OUTPUT (Coeff = +4.0 auf L2=1.0 Einheitsvektor) ---")
    print(steered_out_4)

    print(
        "\n--- [3] STEERED OUTPUT (Coeff = +180.0 auf L2=1.0 Vektor, "
        "passend zur Gemma-2 Layer-14 Residual-Norm ~193) ---"
    )
    print(steered_out_scaled)


if __name__ == "__main__":
    main()
