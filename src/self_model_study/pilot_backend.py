"""Pinned native harness scoring with an explicitly preserved response boundary."""

import importlib.metadata
import math

from .io import digest

HARNESS_VERSION = "0.4.13"


def render_prompt(tokenizer, prompt, format_name):
    if format_name == "plain":
        return prompt + "\n"
    if format_name != "chat" or not tokenizer.chat_template:
        raise ValueError("Expected plain or an explicit tokenizer chat template")
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True
    )


def encode_boundary(tokenizer, rendered, command, max_length):
    """Reject boundary merges rather than silently scoring prompt whitespace.

    TemplateLM.loglikelihood moves trailing context whitespace into the answer.
    We instead pass audited tokens to the pinned HFLM token-scoring implementation.
    No likelihood arithmetic is reimplemented here.
    """
    context = tokenizer.encode(rendered, add_special_tokens=False)
    whole = tokenizer.encode(rendered + command, add_special_tokens=False)
    if not context or whole[: len(context)] != context:
        raise ValueError("Token merge across response boundary; protocol revision required")
    continuation = whole[len(context) :]
    if not continuation or tokenizer.decode(continuation) != command:
        raise ValueError("Continuation tokens do not decode to the exact command")
    if len(whole) > max_length:
        raise ValueError("Context limit exceeded; no truncation")
    return context, continuation


def select_command(choices, scores):
    if len(scores) != len(choices) or not all(math.isfinite(s) for s in scores):
        return None, "invalid_scores"
    maximum = max(scores)
    if scores.count(maximum) != 1:
        return None, "tie"
    return choices[scores.index(maximum)], "ok"


class PilotBackend:
    def __init__(self, lm, generation):
        self.lm, self.tokenizer, self.generation = lm, lm.tokenizer, generation

    def choice(self, prompt, choices, format_name):
        rendered = render_prompt(self.tokenizer, prompt, format_name)
        pairs = [encode_boundary(self.tokenizer, rendered, c, self.lm.max_length) for c in choices]
        native = self.lm._loglikelihood_tokens(
            [(None, ctx, cont) for ctx, cont in pairs], disable_tqdm=True
        )
        if len(native) != len(choices):
            raise RuntimeError("Native scorer returned incomplete candidate coverage")
        scores = [float(v[0]) for v in native]
        selected, status = select_command(choices, scores)
        return {
            "rendered_prompt": rendered,
            "prompt_token_ids": pairs[0][0],
            "candidates": [
                {
                    "command": command,
                    "token_ids": pair[1],
                    "token_count": len(pair[1]),
                    "log_likelihood": score if math.isfinite(score) else None,
                    "nonfinite": None if math.isfinite(score) else repr(score),
                    "native_is_greedy": bool(result[1]),
                }
                for command, pair, score, result in zip(choices, pairs, scores, native)
            ],
            "selected_command": selected,
            "status": status,
        }

    def generate(self, prompt, format_name, seed):
        import torch
        from transformers import GenerationConfig, set_seed

        rendered = render_prompt(self.tokenizer, prompt, format_name)
        tokens = self.tokenizer.encode(rendered, add_special_tokens=False)
        if not tokens or len(tokens) + self.generation["max_new_tokens"] > self.lm.max_length:
            raise ValueError("Generation exceeds context limit; no truncation")
        set_seed(seed)  # Per-output seed makes interrupted and uninterrupted runs match.
        # Build explicitly: the repository's generation_config may otherwise add top_k.
        eos = self.lm.model.generation_config.eos_token_id
        if eos is None:
            eos = self.tokenizer.eos_token_id
        config = GenerationConfig(
            do_sample=True,
            temperature=self.generation["temperature"],
            top_p=self.generation["top_p"],
            top_k=0,
            max_new_tokens=self.generation["max_new_tokens"],
            eos_token_id=eos,
            pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,
            use_cache=True,
        )
        ids = torch.tensor([tokens], device=self.lm.device)
        with torch.inference_mode():
            output = self.lm.model.generate(
                input_ids=ids, attention_mask=torch.ones_like(ids), generation_config=config
            )[0, len(tokens) :].tolist()
        stops = eos if isinstance(eos, list) else [eos]
        return {
            "status": "ok",
            "rendered_prompt": rendered,
            "prompt_token_ids": tokens,
            "output_token_ids": output,
            "output": self.tokenizer.decode(output, skip_special_tokens=True),
            "raw_output": self.tokenizer.decode(output, skip_special_tokens=False),
            "finish_reason": "eos" if output and output[-1] in stops else "length",
            "generation_config": config.to_dict(),
        }


def create_backend(spec):
    import torch
    from lm_eval.models.huggingface import HFLM
    from transformers import AutoTokenizer

    if importlib.metadata.version("lm-eval") != HARNESS_VERSION:
        raise RuntimeError(f"Install lm-eval=={HARNESS_VERSION}; no evaluator fallback")
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise RuntimeError("Qwen pilot requires CUDA with BF16; use the prepared L4 job")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.cuda.reset_peak_memory_stats()
    model = spec["model"]
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model["repo"], revision=model["revision"], trust_remote_code=False
        )
        lm = HFLM(
            pretrained=model["repo"],
            revision=model["revision"],
            tokenizer=tokenizer,
            device="cuda",
            dtype="bfloat16",
            softmax_dtype="float32",
            batch_size=1,
            add_bos_token=False,
            max_length=2048,
            truncation=False,
            trust_remote_code=False,
            parallelize=False,
            attn_implementation="eager",
        )
    except Exception as exc:
        raise RuntimeError(
            f"Cannot load pinned Qwen model/tokenizer ({type(exc).__name__}). "
            "Check access, dependencies and GPU memory; no alternative checkpoint was used."
        ) from exc
    lm.model.eval()
    return PilotBackend(lm, spec["generation"]), {
        "synthetic": False,
        "gpu": torch.cuda.get_device_name(0),
        "cuda": torch.version.cuda,
        "attention": "eager",
        "softmax_dtype": "float32",
        "tokenizer_revision": model["revision"],
        "tokenizer_vocabulary_hash": digest(tokenizer.get_vocab()),
        "chat_template": tokenizer.chat_template,
        "chat_template_hash": digest(tokenizer.chat_template),
        "model_config": lm.model.config.to_dict(),
    }
