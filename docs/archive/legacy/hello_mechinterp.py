#!/usr/bin/env python3
"""Hello-World-Skript für Mechanistic Interpretability mit TransformerLens."""

import torch
from transformer_lens import HookedTransformer


def main() -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Verwendetes Device: {device}")
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    else:
        print(
            "Hinweis: CUDA ist aktuell nicht aktiv (Treiber/Kernel-Mismatch). "
            "Fallback auf CPU zur Verifikation."
        )

    # 1. GPT-2 über TransformerLens laden
    print("\nLade Modell 'gpt2' über HookedTransformer...")
    model = HookedTransformer.from_pretrained("gpt2", device=device)

    # 2. Prompt durch run_with_cache() schicken
    prompt = "I think, therefore I am."
    logits, cache = model.run_with_cache(prompt)

    # a) Tokenisierung der Sequenz extrahieren und ausgeben
    str_tokens = model.to_str_tokens(prompt)
    token_ids = model.to_tokens(prompt)
    print("\n=== a) Tokenisierung der Sequenz ===")
    print(f"Prompt: {prompt!r}")
    print(f"Token-IDs Shape: {tuple(token_ids.shape)}")
    for pos, (tok_id, tok_str) in enumerate(zip(token_ids[0].tolist(), str_tokens)):
        print(f"  Position {pos:2d}: ID={tok_id:6d} | Token={tok_str!r}")

    # b) Residual-Stream-Tensor nach Layer 6 (blocks.6.hook_resid_post)
    resid_post_l6 = cache["blocks.6.hook_resid_post"]  # Shape: [batch, pos, d_model]
    last_token_resid = resid_post_l6[0, -1, :]         # Shape: [d_model] (Token '.')
    am_token_resid = resid_post_l6[0, -2, :]           # Shape: [d_model] (Token ' am')
    l2_norm_last = torch.linalg.vector_norm(last_token_resid).item()
    l2_norm_am = torch.linalg.vector_norm(am_token_resid).item()

    print("\n=== b) Residual Stream nach Layer 6 (blocks.6.hook_resid_post) ===")
    print(f"Gesamter Tensor Shape (Batch, Pos, d_model): {tuple(resid_post_l6.shape)}")
    print(
        f"Letztes Token (Pos {len(str_tokens)-1}: {str_tokens[-1]!r}) -> "
        f"Shape: {tuple(last_token_resid.shape)}, L2-Norm: {l2_norm_last:.6f}"
    )
    print(
        f"Vorletztes Token (Pos {len(str_tokens)-2}: {str_tokens[-2]!r}) -> "
        f"Shape: {tuple(am_token_resid.shape)}, L2-Norm: {l2_norm_am:.6f}"
    )
    print(f"Erste 10 Werte (letztes Token {str_tokens[-1]!r}):\n  {last_token_resid[:10].detach().cpu().numpy().round(4)}")

    # c) Attention-Pattern-Matrix von Layer 0, Head 0 (blocks.0.attn.hook_pattern)
    attn_pattern_l0 = cache["blocks.0.attn.hook_pattern"]  # Shape: [batch, head, dest_pos, src_pos]
    attn_l0_h0 = attn_pattern_l0[0, 0, :, :]               # Shape: [dest_pos, src_pos]

    print("\n=== c) Attention-Pattern-Matrix (Layer 0, Head 0: blocks.0.attn.hook_pattern) ===")
    print(f"Matrix Shape: {tuple(attn_l0_h0.shape)}")
    header = "          " + " ".join(f"{ repr(t):>8s}" for t in str_tokens)
    print(header)
    for row_idx, row_tok in enumerate(str_tokens):
        row_vals = " ".join(f"{val:8.4f}" for val in attn_l0_h0[row_idx].tolist())
        print(f"{repr(row_tok):>9s} {row_vals}")


if __name__ == "__main__":
    main()
