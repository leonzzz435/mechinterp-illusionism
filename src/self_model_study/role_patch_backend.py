"""Native Qwen block-output hooks; candidate-specific lossless donor capture."""

import math
import os
from contextlib import contextmanager
from pathlib import Path

from .io import digest, file_hash, read_json
from .pilot_backend import create_backend as create_pilot_backend
from .pilot_backend import encode_boundary, render_prompt, select_command
from .role_patch import role_position, trial_id
from .storage import read_records


@contextmanager
def audited_forward(model, expected_tokens):
    """Observe the actual native forward, rather than assume harness token placement."""
    seen = []

    def check(_module, args, kwargs):
        ids = args[0] if args else kwargs.get("input_ids")
        if ids is None or ids.shape != (1, len(expected_tokens)):
            raise RuntimeError("Unexpected native candidate input shape")
        if ids[0].tolist() != expected_tokens:
            raise RuntimeError("Native candidate tokens differ from the audited boundary")
        if kwargs.get("use_cache", model.config.use_cache):
            raise RuntimeError("KV caching must remain disabled")
        seen.append(True)

    handle = model.register_forward_pre_hook(check, with_kwargs=True)
    try:
        yield
        if len(seen) != 1:
            raise RuntimeError("Expected exactly one native candidate forward")
    finally:
        handle.remove()


@contextmanager
def patch_site(model, layer, position, width, mode, own=None, donor=None, direction=None):
    """Only one token is cloned/replaced; hooks always come off, including on failure."""
    import torch

    captured = {}

    def hook(_module, _args, output):
        nonlocal own, donor, direction
        if not isinstance(output, torch.Tensor) or output.ndim != 3:
            raise RuntimeError("Expected native Qwen decoder output Tensor [1, sequence, width]")
        if output.shape[0] != 1 or output.shape[2] != width or position >= output.shape[1]:
            raise RuntimeError("Patch tensor shape/position differs from frozen protocol")
        if captured:
            raise RuntimeError("Expected exactly one decoder forward per candidate")
        current = output[0, position].detach()
        if not torch.isfinite(current).all():
            raise RuntimeError("Nonfinite residual activation")
        captured["activation"] = current.cpu().clone()
        metrics = {
            "position": position,
            "layer": layer,
            "width": width,
            "residual_norm": float(current.float().norm()),
            "mode": mode,
        }
        captured["metrics"] = metrics
        if mode in {"baseline", "repeat"}:
            return output
        if (
            own is None
            or donor is None
            or own.shape != current.shape
            or donor.shape != current.shape
        ):
            raise RuntimeError("Missing or mismatched baseline activation")
        own, donor = own.to(current.device), donor.to(current.device)
        if own.dtype != current.dtype or donor.dtype != current.dtype:
            raise RuntimeError("Lossless baseline dtype mismatch")
        metrics["prepatch_max_abs_difference"] = float((current.float() - own.float()).abs().max())
        desired = float((donor.float() - own.float()).norm())
        if mode == "self":
            replacement, desired = own, 0.0
        elif mode == "swap":
            replacement = donor
        elif mode.startswith("random_"):
            if direction is None or direction.shape != current.shape:
                raise RuntimeError("Missing random direction")
            direction = direction.to(device=current.device, dtype=torch.float32)
            if abs(float(direction.norm()) - 1) > 1e-6:
                raise RuntimeError("Random direction is not unit norm")
            replacement = (current.float() + desired * direction).to(current.dtype)
        else:
            raise ValueError("Unknown patch mode")
        actual = float((replacement.float() - current.float()).norm())
        relative = abs(actual - desired) / desired if desired else (0.0 if actual == 0 else None)
        metrics.update(desired_norm=desired, actual_norm=actual, relative_norm_error=relative)
        result = output.clone()
        result[0, position] = replacement
        return result

    handle = model.model.layers[layer].register_forward_hook(hook)
    try:
        yield captured
        if not captured:
            raise RuntimeError("Patch hook did not execute")
    finally:
        handle.remove()


class PatchBackend:
    def __init__(self, lm, layer=13, width=3584):
        self.lm, self.tokenizer, self.layer, self.width = lm, lm.tokenizer, layer, width
        lm.logits_cache = False
        lm.model.config.use_cache = False

    def choice(self, prompt, choices, format_name, *, mode, own=None, donor=None, direction=None):
        rendered = render_prompt(self.tokenizer, prompt, format_name)
        candidates, activations = [], {}
        for i, command in enumerate(choices):
            ctx, cont = encode_boundary(self.tokenizer, rendered, command, self.lm.max_length)
            position = role_position(self.tokenizer, rendered, ctx)
            with patch_site(
                self.lm.model,
                self.layer,
                position,
                self.width,
                mode,
                None if own is None else own[f"candidate_{i}"],
                None if donor is None else donor[f"candidate_{i}"],
                direction,
            ) as captured:
                # One request per forward: no sort-to-candidate ambiguity and no logits cache.
                with audited_forward(self.lm.model, (ctx + cont)[:-1]):
                    native = self.lm._loglikelihood_tokens([(None, ctx, cont)], disable_tqdm=True)
            if len(native) != 1:
                raise RuntimeError("Incomplete native likelihood result")
            score = float(native[0][0])
            activations[f"candidate_{i}"] = captured["activation"]
            candidates.append(
                {
                    "command": command,
                    "token_ids": cont,
                    "token_count": len(cont),
                    "log_likelihood": score if math.isfinite(score) else None,
                    "nonfinite": None if math.isfinite(score) else repr(score),
                    "native_is_greedy": bool(native[0][1]),
                    "forward_input_hash": digest((ctx + cont)[:-1]),
                    "patch": captured["metrics"],
                }
            )
        selected, status = select_command(
            choices,
            [
                c["log_likelihood"] if c["log_likelihood"] is not None else math.nan
                for c in candidates
            ],
        )
        return {
            "rendered_prompt": rendered,
            "prompt_token_ids": ctx,
            "candidates": candidates,
            "selected_command": selected,
            "status": status,
        }, activations


def create_backend(spec):
    backend, info = create_pilot_backend(spec)
    config = backend.lm.model.config
    if config.model_type != "qwen2" or config.num_hidden_layers != 28 or config.hidden_size != 3584:
        raise RuntimeError("Unexpected pinned Qwen architecture")
    info.update(
        logits_cache=False,
        use_cache=False,
        patch_layer=13,
        patch_width=3584,
        capture="actual candidate forward, post-block output, lossless BF16",
    )
    return PatchBackend(backend.lm), info


def compare_scores(result, reference, tolerance, kind):
    finite = all(c["log_likelihood"] is not None for c in result["candidates"])
    delta = (
        max(
            abs(c["log_likelihood"] - r["log_likelihood"])
            for c, r in zip(result["candidates"], reference["candidates"])
        )
        if finite
        else None
    )
    same = result["selected_command"] == reference["selected_command"]
    tokens = (
        result.get("rendered_prompt") == reference.get("rendered_prompt")
        and result.get("prompt_token_ids") == reference.get("prompt_token_ids")
        and [(c["command"], c["token_ids"]) for c in result["candidates"]]
        == [(c["command"], c["token_ids"]) for c in reference["candidates"]]
    )
    return {
        "kind": kind,
        "passed": finite and same and tokens and delta <= tolerance,
        "max_score_difference": delta,
        "decisions_match": same,
        "tokens_match": tokens,
        "tolerance": tolerance,
    }


def save_activations(directory, base_id, values):
    from safetensors.torch import save_file

    relative = f"activations/{base_id}.safetensors"
    path = directory / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    save_file(values, str(temporary))
    with temporary.open("rb") as stream:
        os.fsync(stream.fileno())
    temporary.replace(path)
    return {"path": relative, "sha256": file_hash(path)}


def load_activations(directory, reference):
    from safetensors.torch import load_file

    path = (directory / reference["path"]).resolve()
    if not path.is_relative_to(directory.resolve()) or file_hash(path) != reference["sha256"]:
        raise ValueError("Missing or changed donor activation file")
    return load_file(str(path))


class PatchExecutor:
    """Pass only text/tokens and intervention tensors to inference; never the simulator oracle."""

    def __init__(self, directory, spec):
        self.directory, self.spec = Path(directory), spec
        self.results = None

    def __call__(self, backend, job):
        import torch

        if self.results is None:
            self.results = {r["id"]: r["result"] for r in read_records(self.directory)}
            self.reference = read_json(self.directory / "baseline_reference.json")["records"]
            self.directions = torch.tensor(
                read_json(self.directory / "random_directions.json")["vectors"],
                dtype=torch.float32,
            )
        arm, base_id = job["arm"], job["base_id"]
        own = donor = direction = None
        source = recipient = None
        if arm not in {"baseline", "repeat"}:
            recipient = self.results[trial_id(base_id, "baseline")]
            source = (
                recipient
                if arm == "self"
                else self.results[trial_id(job["donor_base_id"], "baseline")]
            )
            own = load_activations(self.directory, recipient["activation_file"])
            donor = load_activations(self.directory, source["activation_file"])
            if arm.startswith("random_"):
                direction = self.directions[int(arm.rsplit("_", 1)[1])]
                direction = direction * (1 if job["row"]["frame"] == "active" else -1)
        result, values = backend.choice(
            job["row"]["prompt"],
            job["row"]["choices"],
            job["format"],
            mode=arm,
            own=own,
            donor=donor,
            direction=direction,
        )
        checks = []
        rules = self.spec["patch"]
        if arm == "baseline":
            result["activation_file"] = save_activations(self.directory, base_id, values)
            checks.append(
                compare_scores(
                    result,
                    self.reference[base_id]["result"],
                    rules["baseline_score_tolerance"],
                    "historical_baseline",
                )
            )
            # Synthetic CPU fixtures cannot pass a scientific decision, and use small random models.
            if getattr(backend, "synthetic", False):
                checks[-1].update(passed=True, synthetic_bypass=True)
        elif arm in {"self", "repeat"}:
            checks.append(
                compare_scores(
                    result,
                    self.results[trial_id(base_id, "baseline")],
                    rules["null_score_tolerance"],
                    "null_score_parity",
                )
            )
        if recipient is not None:
            for i, candidate in enumerate(result["candidates"]):
                metrics = candidate["patch"]
                metrics.update(
                    recipient={**recipient["activation_file"], "key": f"candidate_{i}"},
                    donor={**source["activation_file"], "key": f"candidate_{i}"},
                    donor_position=source["candidates"][i]["patch"]["position"],
                    random_index=int(arm.rsplit("_", 1)[1]) if arm.startswith("random_") else None,
                    random_sign=(1 if job["row"]["frame"] == "active" else -1)
                    if arm.startswith("random_")
                    else None,
                )
                checks.append(
                    {
                        "kind": "prepatch_state_parity",
                        "candidate": i,
                        "passed": metrics["prepatch_max_abs_difference"] <= 1e-6,
                    }
                )
                if arm.startswith("random_"):
                    error = metrics["relative_norm_error"]
                    checks.append(
                        {
                            "kind": "rounded_random_norm",
                            "candidate": i,
                            "passed": error is not None and error <= 0.05,
                        }
                    )
        result["technical_checks"] = checks
        result["technical_failure"] = any(not c["passed"] for c in checks)
        self.results[job["id"]] = result
        return result
