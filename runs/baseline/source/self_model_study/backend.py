"""Lazy GPU adapter and an unmistakably synthetic offline backend."""

import gc
import re
from pathlib import Path

import numpy as np

from .data import LABELS, build_dataset, language_rows
from .interventions import torch_hook, unit
from .io import digest, file_hash, read_json, write_json


def language_metrics(text):
    words = re.findall(r"\b[\w']+\b", text.lower())
    first = {
        "i",
        "me",
        "my",
        "mine",
        "myself",
        "we",
        "us",
        "our",
        "ours",
        "ourselves",
        "i'm",
        "i've",
        "i'll",
        "we're",
        "we've",
    }
    count = sum(w in first for w in words)
    return {
        "word_count": len(words),
        "first_person_count": count,
        "first_person_per_100_words": 100 * count / max(1, len(words)),
        "repeated_bigram_fraction": 0.0
        if len(words) < 2
        else 1 - len(set(zip(words, words[1:]))) / (len(words) - 1),
    }


def historical():
    return read_json(Path(__file__).with_name("historical.json"))


def resolve_assets(config, previous=None):
    if previous:
        return previous
    if config["backend"] == "mock":
        return {"model_revision": "SYNTHETIC", "sae_revision": "SYNTHETIC"}
    from huggingface_hub import HfApi

    api = HfApi()
    return {
        f"{kind}_revision": api.model_info(
            config[kind]["repo"], revision=config[kind]["revision"]
        ).sha
        for kind in ("model", "sae")
    }


class MockBackend:
    """Plumbing fixture only; it cannot pass the empirical confirmation gate."""

    def __init__(self, config, assets):
        self.config, self.assets = config, assets
        self.info = {"backend": "mock", "synthetic": True}

    def prepare(self, directory, deadline=None):
        directory = Path(directory)
        if (directory / "calibration.json").exists():
            return read_json(directory / "calibration.json")
        rng = np.random.default_rng(self.config["seed"])
        self.directions = {"dense": unit(rng.normal(size=8))}
        for name in ["feature:2728", "feature:10230", "feature:11005"] + [
            f"random:{i}" for i in range(10)
        ]:
            self.directions[name] = unit(rng.normal(size=8))
        self.directions["combined:2728+10230"] = unit(
            self.directions["feature:2728"] + self.directions["feature:10230"]
        )
        np.savez(directory / "directions.npz", **self.directions)
        report = {
            "synthetic": True,
            "passed": False,
            "median_norm": 1.0,
            "reason": "Mock calibration is not scientific evidence",
            "direction_hash": file_hash(directory / "directions.npz"),
        }
        write_json(directory / "calibration.json", report)
        return report

    def evaluate(self, row, condition, seed):
        index = int(digest([row["id"], condition["id"], seed])[:8], 16)
        if row["kind"] == "choice":
            label = LABELS[index % 4]
            return {
                "output": label,
                "prediction": label,
                "valid": True,
                "correct": label == row["expected"],
                "option_probabilities": [0.25] * 4,
                "option_mass": 0.1,
                "synthetic": True,
            }
        text = "SYNTHETIC SOFTWARE FIXTURE. I check the record."
        return {
            "output": text,
            "valid": True,
            "synthetic": True,
            "feature_activations": {"2728": 0.0, "10230": 0.0},
            "prompt_token_count": len(row["prompt"].split()),
            **language_metrics(text),
        }

    def health_check(self):
        return {"passed": True, "synthetic": True}


class TorchBackend:
    def __init__(self, config, assets):
        import torch
        from huggingface_hub import hf_hub_download
        from sae_lens import SAE
        from transformer_lens import HookedTransformer
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.config, self.assets, self.torch = config, assets, torch
        spec = config["model"]
        self.device = spec["device"]
        self.dtype = getattr(torch, spec["dtype"])
        if self.device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA unavailable. Use the Blackwell host; no automatic CPU fallback."
            )
        if self.device == "cuda" and self.dtype == torch.bfloat16:
            if not torch.cuda.is_bf16_supported():
                raise RuntimeError("Requested BF16 is unsupported by this GPU")
        torch.manual_seed(config["seed"])
        if self.device == "cuda":
            torch.backends.cuda.matmul.allow_tf32 = False
        self.info = {
            "backend": "torch",
            "synthetic": False,
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "device": self.device,
            "gpu": torch.cuda.get_device_name(0) if self.device == "cuda" else None,
            "processing": spec["processing"],
        }
        tokenizer = AutoTokenizer.from_pretrained(
            spec["repo"], revision=assets["model_revision"], trust_remote_code=False
        )
        hf = AutoModelForCausalLM.from_pretrained(
            spec["repo"],
            revision=assets["model_revision"],
            torch_dtype=self.dtype,
            trust_remote_code=False,
            attn_implementation="eager",
        ).eval()
        # Check the *same* checkpoint in HF and TL before freeing its CPU copy.
        parity_tokens = tokenizer("The record contains two different actions.", return_tensors="pt")
        with torch.inference_mode():
            hf_out = hf(**parity_tokens, output_hidden_states=True)
            hf_logits = hf_out.logits[0, -1].float().cpu()
            hf_resid = hf_out.hidden_states[15].float().cpu()
        del hf_out
        loader = (
            HookedTransformer.from_pretrained_no_processing
            if spec["processing"] == "none"
            else HookedTransformer.from_pretrained
        )
        self.model = loader(
            "gemma-2-2b",
            hf_model=hf,
            tokenizer=tokenizer,
            device=self.device,
            dtype=self.dtype,
            revision=assets["model_revision"],
        )
        del hf
        gc.collect()
        self.model.eval()
        self.model.requires_grad_(False)
        self.hook = config["sae"]["hook"]
        if self.hook not in self.model.hook_dict or self.model.cfg.d_model != 2304:
            raise RuntimeError("Model/hook incompatible with the registered Gemma Scope SAE")
        with torch.inference_mode():
            logits, cache = self.model.run_with_cache(
                parity_tokens["input_ids"].to(self.device), names_filter=self.hook
            )
            self.parity = {
                "hf_logit_max_abs_error": (logits[0, -1].float().cpu() - hf_logits)
                .abs()
                .max()
                .item(),
                "hf_residual_relative_error": (
                    (cache[self.hook].float().cpu() - hf_resid).norm() / hf_resid.norm()
                ).item(),
            }
        del cache, logits, hf_logits, hf_resid
        sae_spec = config["sae"]
        params = hf_hub_download(
            sae_spec["repo"], f"{sae_spec['path']}/params.npz", revision=assets["sae_revision"]
        )
        # Same conversion as SAELens' gemma_2 loader, but revision-pinned.
        self.sae = SAE.from_dict(
            {
                "architecture": "jumprelu",
                "d_in": 2304,
                "d_sae": 16384,
                "device": self.device,
                "dtype": "float32",
                "apply_b_dec_to_input": False,
                "normalize_activations": "none",
            }
        )
        with np.load(params, allow_pickle=False) as data:
            state = {
                ("W_" + k[2:] if k.startswith("w_") else k): torch.tensor(
                    data[k], dtype=torch.float32, device=self.device
                )
                for k in data
            }
        if "scaling_factor" in state:
            if not torch.allclose(
                state["scaling_factor"], torch.ones_like(state["scaling_factor"])
            ):
                raise RuntimeError("Unexpected SAE scaling_factor; explicit conversion required")
            del state["scaling_factor"]
        self.sae.load_state_dict(state, strict=True)
        self.sae.eval()
        self.sae.requires_grad_(False)
        del state
        self.info["sae_weights_sha256"] = file_hash(params)
        self.option_ids = []
        for label in LABELS:
            ids = tokenizer.encode(label, add_special_tokens=False)
            if len(ids) != 1:
                raise RuntimeError(f"Choice label {label} is not one token")
            # Ensure the label is a continuation token, not a standalone-only encoding.
            prefix = tokenizer.encode("Answer:", add_special_tokens=False)
            full = tokenizer.encode("Answer:" + label, add_special_tokens=False)
            if full != prefix + ids:
                raise RuntimeError(f"Label boundary tokenization mismatch for {label}")
            self.option_ids.append(ids[0])
        self.health_prompt = "The record contains two different actions."
        with torch.inference_mode():
            self.health_baseline = self.model(self.health_prompt)[0, -1].float().cpu()

    def residual(self, prompt):
        with self.torch.inference_mode():
            _, cache = self.model.run_with_cache(prompt, names_filter=self.hook, return_type=None)
        return cache[self.hook]

    def prepare(self, directory, deadline=None):
        import time

        torch = self.torch
        directory = Path(directory)
        report_path, vectors_path = directory / "calibration.json", directory / "directions.npz"
        if report_path.exists():
            report = read_json(report_path)
            if report["direction_hash"] != file_hash(vectors_path):
                raise RuntimeError("Calibration direction checksum mismatch")
            with np.load(vectors_path, allow_pickle=False) as saved:
                vectors = {k: saved[k] for k in saved.files}
        else:
            dataset = self.config["dataset"]
            n = self.config["calibration"]["prompts_per_family"]
            rows = build_dataset(dataset, "development")
            chosen = []
            for family in dataset["families"]:
                chosen += [
                    r
                    for r in rows
                    if r["family"] == family
                    and not r["swapped"]
                    and r["identity"] == 0
                    and r["rotation"] == 0
                    and r["view"] == "self"
                ][:n]
            norms, errors, sums, squares, l0s = [], [], [], [], []
            vectors_by_monitor = {False: [], True: []}
            with torch.inference_mode():
                for row in chosen + language_rows(dataset, "development"):
                    if deadline and time.monotonic() >= deadline:
                        raise TimeoutError("Calibration exceeded this invocation's time budget")
                    r = self.residual(row["prompt"]).float()
                    f = self.sae.encode(r)
                    x = r[0, 1:]
                    recons = self.sae.decode(f)[0, 1:]
                    norms.append(r[0, -1].norm().item())
                    errors.append((x - recons).square().sum().item())
                    sums.append(x.sum(0).cpu().numpy())
                    squares.append((x.square().sum().item(), x.shape[0]))
                    l0s.append((f[0, 1:] > 0).sum(-1).float().mean().item())
                    if row["kind"] == "language":
                        vectors_by_monitor[row["monitoring"]].append(r[0, -1].cpu().numpy())
                if self.config["phase"] == "reference":
                    old = historical()
                    vectors_by_monitor = {
                        flag: [self.residual(p)[0, -1].float().cpu().numpy() for p in old[key]]
                        for flag, key in [
                            (True, "introspective_prompts"),
                            (False, "neutral_prompts"),
                        ]
                    }
                vectors = {
                    "dense": unit(
                        np.mean(vectors_by_monitor[True], axis=0)
                        - np.mean(vectors_by_monitor[False], axis=0)
                    )
                }
                for fid in (2728, 10230, 11005):
                    vectors[f"feature:{fid}"] = unit(self.sae.W_dec[fid].cpu().numpy())
                random = np.random.default_rng(self.config["seed"])
                for i in range(10):
                    vectors[f"random:{i}"] = unit(random.normal(size=self.model.cfg.d_model))
                vectors["combined:2728+10230"] = unit(
                    vectors["feature:2728"] + vectors["feature:10230"]
                )
                # Causal reconstruction fidelity: replace non-BOS residuals; compare to zeroing.
                losses = []
                loss_rows = [
                    next(r for r in chosen if r["family"] == family)
                    for family in dataset["families"]
                ]
                for row in loss_rows:

                    def replace(r, hook):
                        edited = r.clone()
                        edited[:, 1:] = self.sae.decode(self.sae.encode(r[:, 1:].float())).to(
                            r.dtype
                        )
                        return edited

                    def zero(r, hook):
                        edited = r.clone()
                        edited[:, 1:] = 0
                        return edited

                    base = self.model(row["prompt"], return_type="loss").item()
                    with self.model.hooks(fwd_hooks=[(self.hook, replace)]):
                        recon = self.model(row["prompt"], return_type="loss").item()
                    with self.model.hooks(fwd_hooks=[(self.hook, zero)]):
                        erased = self.model(row["prompt"], return_type="loss").item()
                    losses.append({"base": base, "reconstructed": recon, "zero": erased})
            total_n = sum(x[1] for x in squares)
            centered_ss = (
                sum(x[0] for x in squares) - np.square(np.sum(sums, axis=0)).sum() / total_n
            )
            ev = 1 - sum(errors) / max(float(centered_ss), 1e-12)
            base, recon, zero_loss = [
                np.mean([r[k] for r in losses]) for k in ("base", "reconstructed", "zero")
            ]
            recovered = (
                float((zero_loss - recon) / (zero_loss - base)) if zero_loss > base else None
            )
            criteria = self.config["calibration"]
            report = {
                "synthetic": False,
                "median_norm": float(np.median(norms)),
                "explained_variance": float(ev),
                "mean_l0": float(np.mean(l0s)),
                "loss_recovered": recovered,
                "loss_checks": losses,
                **self.parity,
                "calibration_split": "development",
                "criteria": criteria,
                "feature_cosine": float(vectors["feature:2728"] @ vectors["feature:10230"]),
                "dense_two_feature_projection_fraction": float(
                    1
                    - np.linalg.norm(
                        vectors["dense"]
                        - np.column_stack([vectors["feature:2728"], vectors["feature:10230"]])
                        @ np.linalg.lstsq(
                            np.column_stack([vectors["feature:2728"], vectors["feature:10230"]]),
                            vectors["dense"],
                            rcond=None,
                        )[0]
                    )
                    ** 2
                ),
            }
            report["passed"] = bool(
                ev >= criteria["min_explained_variance"]
                and recovered is not None
                and recovered >= criteria["min_loss_recovered"]
                and self.parity["hf_logit_max_abs_error"] <= criteria["max_hf_logit_abs_error"]
                and self.parity["hf_residual_relative_error"] <= 0.05
            )
            np.savez(vectors_path, **vectors)
            report["direction_hash"] = file_hash(vectors_path)
            write_json(report_path, report)
        self.median_norm = report["median_norm"]
        self.directions = {k: torch.tensor(v, device=self.device) for k, v in vectors.items()}
        return report

    def evaluate(self, row, condition, seed):
        torch = self.torch
        torch.manual_seed(seed)
        hook = torch_hook(
            condition,
            self.directions,
            self.median_norm,
            self.sae,
            "last" if row["kind"] == "choice" else "all",
        )
        with torch.inference_mode(), self.model.hooks(fwd_hooks=[(self.hook, hook)]):
            if row["kind"] == "choice":
                logits = self.model(row["prompt"])[0, -1].float()
                selected = logits[self.option_ids]
                prediction = LABELS[selected.argmax().item()]
                # Forced choice primary endpoint; unconstrained token retained as format diagnostic.
                raw = self.model.to_string(logits.argmax().item())
                return {
                    "output": raw,
                    "prediction": prediction,
                    "valid": raw.strip() in LABELS and len(raw.strip()) == 1,
                    "correct": prediction == row["expected"],
                    "option_probabilities": selected.softmax(-1).cpu().tolist(),
                    "option_mass": logits.softmax(-1)[self.option_ids].sum().item(),
                }
            tokens = self.model.to_tokens(row["prompt"])
            prompt_length = tokens.shape[1]
            _, cache = self.model.run_with_cache(tokens, names_filter=self.hook, return_type=None)
            feats = self.sae.encode(cache[self.hook].float())[0, 1:]
            activations = {str(fid): feats[:, fid].mean().item() for fid in (2728, 10230)}
            del cache, feats
            out = self.model.generate(
                tokens,
                max_new_tokens=self.config["generation"]["max_new_tokens"],
                do_sample=True,
                temperature=self.config["generation"]["temperature"],
                freq_penalty=self.config["generation"]["frequency_penalty"],
                use_past_kv_cache=False,
                return_type="tokens",
                verbose=False,
            )
            continuation = self.model.to_string(out[0, prompt_length:])
        # NLL of the generated continuation under an *unmodified* model is a degradation diagnostic.
        with torch.inference_mode():
            logits = self.model(out).float()
            log_probs = logits[0, prompt_length - 1 : -1].log_softmax(-1)
            target = out[0, prompt_length:]
            nll = -log_probs.gather(1, target[:, None]).mean().item() if target.numel() else None
        return {
            "output": continuation,
            "valid": bool(continuation.strip()),
            "feature_activations": activations,
            "prompt_token_count": prompt_length,
            "unmodified_model_continuation_nll": nll,
            **language_metrics(continuation),
        }

    def health_check(self):
        with self.torch.inference_mode():
            now = self.model(self.health_prompt)[0, -1].float().cpu()
        error = (now - self.health_baseline).abs().max().item()
        return {
            "passed": error <= 1e-5,
            "max_baseline_logit_change": error,
            "peak_allocated_bytes": self.torch.cuda.max_memory_allocated()
            if self.device == "cuda"
            else None,
        }


def make_backend(config, assets):
    return (
        MockBackend(config, assets) if config["backend"] == "mock" else TorchBackend(config, assets)
    )
