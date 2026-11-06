"""Bounded, auditable baseline using EleutherAI's scoring and prompt construction.

This module supplies task data, resumes completed scenario blocks, and reports
the harness's results. It does not implement model inference or token scoring.
"""

import argparse
import importlib.metadata
import math
import re
import shutil
import tarfile
import time
import uuid
from copy import deepcopy
from pathlib import Path

from .config import DEFAULTS
from .data import FAMILIES, LABELS, functional_rows
from .io import canonical, digest, file_hash, provenance, read_json, source_hash, write_json
from .runner import baseline_gate
from .storage import run_lock

VERSION = "0.4.13"
PROTOCOL = "context-self-harness-v1"


def load_spec(path):
    spec = read_json(path)
    required = {
        "engine",
        "protocol",
        "harness_version",
        "model",
        "dataset_seed",
        "evaluation_scenarios",
        "demonstration_scenarios",
        "num_fewshot",
        "target_delimiter",
        "batch_size",
        "seed",
        "max_seconds",
    }
    if set(spec) != required or spec["engine"] != "lm-eval" or spec["protocol"] != PROTOCOL:
        raise ValueError("Unknown or incomplete harness protocol")
    if spec["harness_version"] != VERSION:
        raise ValueError(f"This protocol requires lm-eval {VERSION}")
    model = spec["model"]
    if set(model) != {"repo", "revision", "device", "dtype", "max_length", "add_bos_token"}:
        raise ValueError("Unexpected model configuration")
    if not isinstance(model["repo"], str) or not re.fullmatch(
        r"[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+", model["repo"]
    ):
        raise ValueError("Explicit Hugging Face repository required")
    if not isinstance(model["revision"], str) or not re.fullmatch(
        r"[0-9a-f]{40}", model["revision"]
    ):
        raise ValueError("Pin model revision to an immutable 40-character commit")
    if (
        model["device"] != "cuda"
        or model["dtype"] != "bfloat16"
        or model["add_bos_token"] is not True
    ):
        raise ValueError("Study baseline requires explicit CUDA/BF16 with BOS")
    if model["max_length"] != 2048 or spec["batch_size"] != 1:
        raise ValueError("Protocol fixes context length 2048 and batch size 1")
    if spec["num_fewshot"] != 4 or spec["target_delimiter"] != " ":
        raise ValueError("Protocol fixes four demonstrations and a single-space delimiter")
    if spec["evaluation_scenarios"] != list(range(8)) or spec["demonstration_scenarios"] != [
        36,
        37,
        38,
        39,
    ]:
        raise ValueError("Protocol fixes evaluation episodes 0–7 and demonstrations 36–39")
    if type(spec["seed"]) is not int or type(spec["dataset_seed"]) is not int:
        raise ValueError("Seeds must be integers")
    if type(spec["max_seconds"]) is not int or not 0 < spec["max_seconds"] <= 28800:
        raise ValueError("Invocation must be bounded to 1–28800 seconds")
    return spec


def scientific_spec(spec):
    return {k: v for k, v in spec.items() if k != "max_seconds"}


def document(row):
    keys = ("id", "scenario_id", "family", "view", "identity", "swapped", "rotation", "prompt")
    return {**{k: row[k] for k in keys}, "gold": LABELS.index(row["expected"])}


def build_plan(spec):
    dataset = deepcopy(DEFAULTS["dataset"])
    dataset.update(seed=spec["dataset_seed"], include_language=False)
    # Generate DEVELOPMENT only; validation and test templates are never touched.
    rows = functional_rows(dataset, "development")
    blocks, demonstrations = [], {}
    for family in FAMILIES:
        family_rows = [r for r in rows if r["family"] == family]
        demonstrations[family] = []
        for j, index in enumerate(spec["demonstration_scenarios"]):
            # One per episode, answer-balanced A/B/C/D, balanced identities and views.
            selected = next(
                r
                for r in family_rows
                if int(r["scenario_id"].rsplit(":", 1)[1]) == index
                and r["identity"] == j % 2
                and r["swapped"] == bool(j // 2)
                and r["view"] == ("self" if j % 2 == 0 else "other")
                and r["expected"] == LABELS[j]
            )
            demonstrations[family].append(document(selected))
        for index in spec["evaluation_scenarios"]:
            selected = [
                document(r) for r in family_rows if int(r["scenario_id"].rsplit(":", 1)[1]) == index
            ]
            blocks.append({"id": f"{family}-{index:04d}", "family": family, "rows": selected})
    return {
        "protocol": PROTOCOL,
        "split": "development",
        "blocks": blocks,
        "demonstrations": demonstrations,
        "dataset_spec": dataset,
    }


def task_config(block, demonstrations, data_path):
    return {
        "task": "context_self_" + block["family"],
        "dataset_path": "json",
        "dataset_kwargs": {"data_files": {"development": str(data_path.resolve())}},
        "validation_split": "development",
        "test_split": None,
        "output_type": "multiple_choice",
        "doc_to_text": "prompt",
        "doc_to_target": "gold",
        "doc_to_choice": list(LABELS),
        "target_delimiter": " ",
        "fewshot_delimiter": "\n\n",
        "fewshot_config": {"sampler": "first_n", "samples": demonstrations},
        "num_fewshot": 4,
        "metric_list": [{"metric": "acc", "aggregation": "mean", "higher_is_better": True}],
        "metadata": {"version": 1, "study_split": "development", "protocol": PROTOCOL},
    }


def plain(value):
    """Convert library scalar types without silently stringifying unknown objects."""
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    if hasattr(value, "item"):
        return plain(value.item())
    if type(value).__module__ == "torch" and type(value).__name__ in {"dtype", "device"}:
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"Unsupported harness result value: {type(value).__name__}")


def evaluate_block(model, task, spec):
    from lm_eval import simple_evaluate
    from lm_eval.tasks import TaskManager

    # Reject oversize prompts before the harness's loglikelihood path can
    # left-truncate them. Prompt construction itself remains in the harness.
    demos = task["fewshot_config"]["samples"]
    prefix = "\n\n".join(d["prompt"] + " " + LABELS[d["gold"]] for d in demos) + "\n\n"
    rows = read_json(task["dataset_kwargs"]["data_files"]["development"])
    longest = max(
        len(model.tok_encode(prefix + r["prompt"] + " " + label)) for r in rows for label in LABELS
    )
    if longest > model.max_length:
        raise ValueError(
            f"Prompt exceeds context limit ({longest} > {model.max_length}); no truncation"
        )
    result = simple_evaluate(
        model=model,
        tasks=[task],
        num_fewshot=4,
        bootstrap_iters=0,
        log_samples=True,
        apply_chat_template=False,
        cache_requests=False,
        random_seed=spec["seed"],
        numpy_random_seed=spec["seed"],
        torch_random_seed=spec["seed"],
        fewshot_random_seed=spec["seed"],
        task_manager=TaskManager(include_defaults=False),
    )
    result["study_preflight"] = {
        "max_tokens_with_answer": longest,
        "context_limit": model.max_length,
    }
    return plain(result)


def audit_samples(result, block, demonstrations):
    """Audit coverage and saved harness decisions; no replacement scoring path."""
    task = "context_self_" + block["family"]
    samples = result["samples"][task]
    expected = {r["id"]: r for r in block["rows"]}
    ids = [s["doc"]["id"] for s in samples]
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise ValueError("Harness sample coverage differs from the complete scenario block")
    prefix = "\n\n".join(d["prompt"] + " " + LABELS[d["gold"]] for d in demonstrations) + "\n\n"
    for sample in samples:
        row = expected[sample["doc"]["id"]]
        if sample["doc"] != row or sample["target"] != row["gold"]:
            raise ValueError("Harness document/gold changed")
        arguments = sample["arguments"]
        if arguments != [[prefix + row["prompt"], " " + label] for label in LABELS]:
            raise ValueError("Harness prompt/continuation differs from the fixed protocol")
        scores = [r[0] for r in sample["filtered_resps"]]
        if len(scores) != 4 or not all(math.isfinite(v) for v in scores):
            raise ValueError("Missing or non-finite harness likelihoods")
        predicted = max(range(4), key=scores.__getitem__)
        if sample["acc"] != int(predicted == row["gold"]):
            raise ValueError("Saved harness accuracy disagrees with its likelihoods")
    if not math.isclose(
        result["results"][task]["acc,none"], sum(s["acc"] for s in samples) / len(samples)
    ):
        raise ValueError("Harness aggregate accuracy disagrees with samples")
    return samples


def create_model(spec):
    import torch
    from lm_eval.models.huggingface import HFLM

    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise RuntimeError("This run requires CUDA/BF16 on the Blackwell host; no fallback")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.cuda.reset_peak_memory_stats()
    torch.manual_seed(spec["seed"])
    model = spec["model"]
    lm = HFLM(
        pretrained=model["repo"],
        revision=model["revision"],
        device="cuda",
        dtype=model["dtype"],
        softmax_dtype="float32",
        batch_size=1,
        add_bos_token=True,
        max_length=2048,
        truncation=False,
        trust_remote_code=False,
        parallelize=False,
        attn_implementation="eager",
    )
    return lm, {
        "gpu": torch.cuda.get_device_name(0),
        "cuda": torch.version.cuda,
        "torch": torch.__version__,
        "harness_version": VERSION,
        "attention": "eager",
        "softmax_dtype": "float32",
    }


def result_payload(path, block, demonstrations, fingerprint):
    payload = read_json(path)
    body = {k: v for k, v in payload.items() if k != "checksum"}
    if payload["checksum"] != digest(body) or payload["config_hash"] != fingerprint:
        raise ValueError("Completed block checksum/configuration mismatch")
    if payload["block_id"] != block["id"]:
        raise ValueError("Wrong block identity")
    audit_samples(payload["harness"], block, demonstrations)
    return payload


def run(
    spec,
    directory,
    max_blocks=None,
    model_factory=create_model,
    evaluator=evaluate_block,
    checkpoint=None,
):
    directory = Path(directory)
    if max_blocks is not None and (type(max_blocks) is not int or max_blocks < 1):
        raise ValueError("max_blocks must be a positive integer")
    if importlib.metadata.version("lm-eval") != VERSION:
        raise RuntimeError(
            f"Install pinned evaluator: uv sync --locked --extra eval (lm-eval {VERSION})"
        )
    with run_lock(directory):
        return _run(spec, directory, max_blocks, model_factory, evaluator, checkpoint)


def _run(spec, directory, max_blocks, model_factory, evaluator, checkpoint):
    started = time.monotonic()
    plan, prov = build_plan(spec), provenance()
    fingerprint = digest(scientific_spec(spec))
    path = directory / "manifest.json"
    if path.exists():
        manifest = read_json(path)
        if manifest["config_hash"] != fingerprint or manifest["plan_hash"] != digest(plan):
            raise ValueError("Cannot resume a changed harness protocol/dataset")
        if digest(read_json(directory / "plan.json")) != manifest["plan_hash"]:
            raise ValueError("Saved task plan checksum mismatch")
        for key in ("source_hash", "python", "packages"):
            if manifest["provenance"][key] != prov[key]:
                raise ValueError(f"Cannot resume after {key} changes")
        if manifest["status"] == "failed":
            raise ValueError("Failed run retained; inspect error.json. No automatic retry")
    else:
        manifest = {
            "engine": "lm-eval",
            "run_id": str(uuid.uuid4()),
            "config": spec,
            "config_hash": fingerprint,
            "plan_hash": digest(plan),
            "provenance": prov,
            "status": "prepared",
            "blocks": {},
            "invocations": [],
        }
        write_json(directory / "plan.json", plan)
        snapshot = directory / "source/self_model_study"
        snapshot.mkdir(parents=True, exist_ok=True)
        for item in Path(__file__).parent.iterdir():
            if item.suffix in {".py", ".json"}:
                shutil.copy2(item, snapshot / item.name)
        for name in ("pyproject.toml", "uv.lock"):
            shutil.copy2(Path(__file__).resolve().parents[2] / name, directory / "source" / name)
        # Commit initialization last: a crash during snapshots can be resumed
        # without leaving a manifest that refers to incomplete required files.
        write_json(path, manifest)
    # Verify completed blocks before loading a model. Recover a block atomically
    # saved immediately before a process crash but not yet listed in the manifest.
    pending = []
    for block in plan["blocks"]:
        target = directory / "blocks" / (block["id"] + ".json")
        if target.exists():
            payload = result_payload(
                target, block, plan["demonstrations"][block["family"]], fingerprint
            )
            if (
                block["id"] in manifest["blocks"]
                and manifest["blocks"][block["id"]] != payload["checksum"]
            ):
                raise ValueError("Block differs from committed manifest checksum")
            manifest["blocks"][block["id"]] = payload["checksum"]
        elif block["id"] in manifest["blocks"]:
            raise ValueError("A completed block is missing")
        else:
            pending.append(block)
    if not pending:
        manifest["status"] = "complete"
        write_json(path, manifest)
        return manifest
    invocation = {
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "max_seconds": spec["max_seconds"],
        "max_blocks": max_blocks,
        "new_blocks": 0,
    }
    manifest["invocations"].append(invocation)
    manifest["status"] = "running"
    write_json(path, manifest)
    try:
        if checkpoint:
            checkpoint(directory)
        model, manifest["backend_info"] = model_factory(spec)
        for block in pending:
            if time.monotonic() - started >= spec["max_seconds"] or (
                max_blocks and invocation["new_blocks"] >= max_blocks
            ):
                manifest["status"] = "paused"
                break
            demos = plan["demonstrations"][block["family"]]
            data = directory / "tasks" / (block["id"] + ".data.json")
            write_json(data, block["rows"])
            task = task_config(block, demos, data)
            write_json(directory / "tasks" / (block["id"] + ".task.json"), task)
            tick = time.monotonic()
            result = evaluator(model, task, spec)
            audit_samples(result, block, demos)
            payload = {
                "block_id": block["id"],
                "config_hash": fingerprint,
                "seconds": time.monotonic() - tick,
                "harness": result,
            }
            payload["checksum"] = digest(payload)
            write_json(directory / "blocks" / (block["id"] + ".json"), payload)
            manifest["blocks"][block["id"]] = payload["checksum"]
            invocation["new_blocks"] += 1
            write_json(path, manifest)
            if checkpoint:
                checkpoint(directory)
            print(
                f"Completed {len(manifest['blocks'])}/{len(plan['blocks'])} scenario blocks",
                flush=True,
            )
        else:
            manifest["status"] = "complete"
    except KeyboardInterrupt:
        manifest["status"] = "interrupted"
    except Exception as exc:
        manifest["status"] = "failed"
        write_json(directory / "error.json", {"type": type(exc).__name__, "message": str(exc)})
        raise
    finally:
        invocation["elapsed_seconds"] = time.monotonic() - started
        if manifest.get("backend_info", {}).get("gpu"):
            import torch

            manifest["backend_info"]["peak_allocated_bytes"] = torch.cuda.max_memory_allocated()
        write_json(path, manifest)
        if checkpoint:
            checkpoint(directory)
    return manifest


def summarize(directory):
    directory = Path(directory)
    manifest, plan = read_json(directory / "manifest.json"), read_json(directory / "plan.json")
    if manifest["engine"] != "lm-eval" or manifest["plan_hash"] != digest(plan):
        raise ValueError("Invalid harness manifest or changed plan")
    if manifest["config_hash"] != digest(scientific_spec(manifest["config"])):
        raise ValueError("Harness configuration checksum mismatch")
    records = []
    for block in plan["blocks"]:
        if block["id"] not in manifest["blocks"]:
            continue
        payload = result_payload(
            directory / "blocks" / (block["id"] + ".json"),
            block,
            plan["demonstrations"][block["family"]],
            manifest["config_hash"],
        )
        if payload["checksum"] != manifest["blocks"][block["id"]]:
            raise ValueError("Block changed since manifest commit")
        for sample in payload["harness"]["samples"]["context_self_" + block["family"]]:
            row = {**sample["doc"], "expected": LABELS[sample["doc"]["gold"]]}
            scores = [v[0] for v in sample["filtered_resps"]]
            prediction = LABELS[max(range(4), key=scores.__getitem__)]
            records.append(
                {
                    "row": row,
                    "condition": {"id": "baseline"},
                    "status": "ok",
                    "result": {"correct": bool(sample["acc"]), "prediction": prediction},
                }
            )
    gates = baseline_gate({"dataset": {"families": list(FAMILIES)}}, records)
    complete = manifest["status"] == "complete" and len(manifest["blocks"]) == len(plan["blocks"])
    families = []
    for family in FAMILIES:
        rows = [r for r in records if r["row"]["family"] == family]
        paired = {
            (
                r["row"]["scenario_id"],
                r["row"]["identity"],
                r["row"]["view"],
                r["row"]["rotation"],
                r["row"]["swapped"],
            ): r
            for r in rows
        }
        pairs = [
            (
                r,
                paired[
                    (
                        r["row"]["scenario_id"],
                        r["row"]["identity"],
                        r["row"]["view"],
                        r["row"]["rotation"],
                        True,
                    )
                ],
            )
            for r in rows
            if not r["row"]["swapped"]
        ]
        families.append(
            {
                "family": family,
                "n_trials": len(rows),
                "n_scenarios": len({r["row"]["scenario_id"] for r in rows}),
                "scenario_accuracy": [
                    {
                        "scenario_id": sid,
                        **{
                            view: sum(
                                r["result"]["correct"]
                                for r in rows
                                if r["row"]["scenario_id"] == sid and r["row"]["view"] == view
                            )
                            / 16
                            for view in ("self", "other")
                        },
                    }
                    for sid in sorted({r["row"]["scenario_id"] for r in rows})
                ],
                "accuracy": sum(r["result"]["correct"] for r in rows) / len(rows) if rows else None,
                "counterfactual_pairs": len(pairs),
                "both_correct_rate": sum(
                    a["result"]["correct"] and b["result"]["correct"] for a, b in pairs
                )
                / len(pairs)
                if pairs
                else None,
                "prediction_flip_rate": sum(
                    a["result"]["prediction"] != b["result"]["prediction"] for a, b in pairs
                )
                / len(pairs)
                if pairs
                else None,
                **gates[family],
            }
        )
    return {
        "engine": "lm-eval",
        "protocol": PROTOCOL,
        "status": manifest["status"],
        "run_id": manifest["run_id"],
        "complete": complete,
        "n_trials": len(records),
        "expected_trials": sum(len(b["rows"]) for b in plan["blocks"]),
        "families": families,
        "development_screen_passed": complete and all(g["passed"] for g in gates.values()),
        "confirmatory_evidence": False,
        "analysis_source_hash": source_hash(),
        "note": "Development-only four-shot baseline. Passing does not validate a self-model "
        "construct, establish a mechanism, or unlock confirmation.",
    }


def plot_report(report, directory):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from .reporting import save_figure

    fig, ax = plt.subplots(figsize=(9, 5))
    for view, shift, color in (("self", -0.18, "#206a8a"), ("other", 0.18, "#d88b32")):
        for i, family in enumerate(report["families"]):
            if not family["n_trials"]:
                continue
            ax.bar(
                i + shift,
                100 * family["checks"]["view:" + view],
                width=0.32,
                color=color,
                label=view if i == 0 else None,
            )
            scenarios = family["scenario_accuracy"]
            offsets = (
                [0.0]
                if len(scenarios) == 1
                else [0.18 * (j / (len(scenarios) - 1) - 0.5) for j in range(len(scenarios))]
            )
            ax.scatter(
                [i + shift + x for x in offsets],
                [100 * r[view] for r in scenarios],
                s=18,
                color="white",
                edgecolor="black",
                linewidth=0.5,
                zorder=3,
            )
    ax.axhline(80, linestyle="--", color="gray", linewidth=1, label="80% screen threshold")
    ax.set(
        xticks=range(3),
        xticklabels=["Action ownership", "Information access", "Capability change"],
        ylim=(0, 105),
        ylabel="Accuracy (%)",
        title=f"Four-shot development baseline — {report['status']}",
    )
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=3, frameon=False)
    fig.text(
        0.5,
        -0.04,
        "Dots: scenario means. Paired variants are not independent samples.\n"
        "Descriptive screening; no confirmatory inference.",
        ha="center",
        fontsize=9,
    )
    directory.mkdir(exist_ok=True)
    save_figure(fig, directory / "harness_baseline")
    plt.close(fig)


def export(directory, destination):
    directory, destination = Path(directory), Path(destination)
    if destination.exists() or destination.resolve().is_relative_to(directory.resolve()):
        raise ValueError("Choose a new export path outside the run directory")
    with run_lock(directory):
        report = summarize(directory)
        write_json(directory / "analysis.json", report)
        lines = [
            "# Standard-harness development baseline",
            "",
            report["note"],
            "",
            f"Status: **{report['status']}**; "
            f"{report['n_trials']}/{report['expected_trials']} scored variants.",
            "",
            "| Family | Scenarios | Accuracy | Worst subgroup | Both counterfactuals correct |",
            "|---|---:|---:|---:|---:|",
        ]

        def fmt(value):
            return "missing" if value is None else f"{value:.1%}"

        for r in report["families"]:
            lines.append(
                f"| {r['family']} | {r['n_scenarios']} | {fmt(r['accuracy'])} | "
                f"{fmt(min(r['checks'].values()) if r['n_trials'] else None)} | "
                f"{fmt(r['both_correct_rate'])} |"
            )
        lines += [
            "",
            f"Complete development screen passed: **{report['development_screen_passed']}**.",
            "",
            "This is a revised measurement protocol: four fixed demonstrations and harness "
            "likelihood scoring. Differences from the historical zero-shot run cannot be "
            "attributed to whitespace alone.",
            "",
            "No automatic intervention sweep follows this report. "
            "Keep failed and incomplete results.",
        ]
        (directory / "report.md").write_text("\n".join(lines) + "\n")
        if report["n_trials"]:
            plot_report(report, directory / "figures")
        files = [
            p
            for p in directory.rglob("*")
            if p.is_file()
            and p.name not in {".lock", "checksums.json"}
            and not p.name.endswith(".tmp")
        ]
        write_json(
            directory / "checksums.json",
            {str(p.relative_to(directory)): file_hash(p) for p in files},
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream, tarfile.open(fileobj=stream, mode="w:gz") as archive:
            for path in sorted(files + [directory / "checksums.json"]):
                archive.add(
                    path,
                    arcname=str(Path(directory.name) / path.relative_to(directory)),
                    recursive=False,
                )
    return {
        "archive": str(destination),
        "sha256": file_hash(destination),
        "status": report["status"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Pinned lm-evaluation-harness development baseline"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "run"):
        command = commands.add_parser(name)
        command.add_argument("config", type=Path)
        if name == "run":
            command.add_argument("--out", type=Path, required=True)
            command.add_argument("--max-blocks", type=int)
            command.add_argument("--max-seconds", type=int)
    for name in ("analyze", "export"):
        command = commands.add_parser(name)
        command.add_argument("run", type=Path)
        if name == "export":
            command.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command in {"validate", "run"}:
            spec = load_spec(args.config)
        if args.command == "validate":
            plan = build_plan(spec)
            result = {
                "valid": True,
                "engine": "lm-eval",
                "split": "development",
                "blocks": len(plan["blocks"]),
                "scored_variants": sum(len(b["rows"]) for b in plan["blocks"]),
                "plan_hash": digest(plan),
            }
        elif args.command == "run":
            if args.max_seconds is not None:
                if not 0 < args.max_seconds <= 28800:
                    raise ValueError("max_seconds must be 1–28800")
                spec["max_seconds"] = args.max_seconds
            manifest = run(spec, args.out, args.max_blocks)
            result = {
                "run_id": manifest["run_id"],
                "status": manifest["status"],
                "completed_blocks": len(manifest["blocks"]),
            }
        elif args.command == "analyze":
            with run_lock(args.run):
                result = summarize(args.run)
                write_json(args.run / "analysis.json", result)
        else:
            result = export(args.run, args.out)
        print(canonical(result))
        return 0
    except (ValueError, RuntimeError, OSError, ImportError, KeyError, TypeError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
