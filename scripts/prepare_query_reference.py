"""Reproducible CPU input/oracle/token audit. Never imports or loads model weights."""

import argparse
import gzip
import importlib.metadata
import json
import os
import platform
import re
import shutil
import tarfile
import tempfile
from collections import Counter
from pathlib import Path

from self_model_study.io import canonical, digest, file_hash
from self_model_study.pilot_backend import encode_boundary, render_prompt
from self_model_study.query_reference import (
    ROOT,
    SPEC_PATH,
    build_inputs,
    fingerprint,
    model_input,
    specification,
)
from self_model_study.query_reference_audit import audit_inputs, require

DEFAULT_OUT = ROOT / "review/query-self-reference-preflight"
SOURCES = [
    "scripts/prepare_query_reference.py",
    "src/self_model_study/query_reference.py",
    "src/self_model_study/query_reference_audit.py",
    "src/self_model_study/action_task.py",
    "src/self_model_study/pilot_backend.py",
    "src/self_model_study/io.py",
]


def task_body(prompt):
    """Remove text before the first permission heading, preserving facts/query/options.

    This is a literal input-overlap check, not a claim of semantic independence.
    Prompts with neither heading are preserved verbatim.
    """
    match = re.search(r"(?m)^(?:Initial|Current) permissions:\s*\n", prompt)
    return prompt[match.start() :] if match else prompt


def historical_inventory(root=ROOT):
    exact, stripped, fingerprints, inventory = set(), set(), set(), {}
    archives = sorted((root / "review/evidence").glob("*.tar.gz"))
    archives += sorted((root / "review/ownership-permissions-results/archives").glob("*.tar.gz"))
    required = {
        "qwen-78ee6db8adfc4f3e.tar.gz",
        "qwen-role-96787d5e7adf4c4d.tar.gz",
        "qwen-possessive-f2baaa2fb6b74880.tar.gz",
        "block-00.tar.gz",
        "block-01.tar.gz",
        "block-02.tar.gz",
    }
    require(required <= {p.name for p in archives}, "Missing historical action archives")

    def visit(value):
        if isinstance(value, dict):
            prompt = value.get("prompt")
            if isinstance(prompt, str):
                exact.add(digest(prompt))
                stripped.add(digest(task_body(prompt)))
                # Also covers CPU probes without structured state.
                accounts = set(re.findall(r"(?m)^([A-Za-z]+): mark_[a-z]+\.?$", prompt))
                commands = value.get("choices")
                if len(accounts) == 2 and isinstance(commands, list) and len(commands) == 4:
                    fingerprints.add(fingerprint(accounts, commands))
            if isinstance(value.get("permissions"), dict) and isinstance(
                value.get("commands"), list
            ):
                if len(value["permissions"]) == 2 and len(value["commands"]) == 4:
                    fingerprints.add(fingerprint(value["permissions"], value["commands"]))
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    for path in archives:
        with tarfile.open(path) as archive:
            visit(json.load(archive.extractfile("run/plan.json")))
        inventory[str(path.relative_to(root))] = file_hash(path)
    for name in (
        "query_reference_probes.jsonl.gz",
        "named_template_pairs.jsonl.gz",
        "current_snapshot_controls.jsonl.gz",
        "their_reference_probes.json",
    ):
        path = root / "review/ownership-design-audit" / name
        require(path.is_file(), "Missing historical CPU probe archive")
        if path.suffix == ".gz":
            with gzip.open(path, "rt") as stream:
                for line in stream:
                    visit(json.loads(line))
        else:
            visit(json.loads(path.read_text()))
        inventory[str(path.relative_to(root))] = file_hash(path)
    require(exact and fingerprints, "Empty historical input inventory")
    return exact, stripped, fingerprints, inventory


def check_freshness(worlds, rows, historical):
    exact, stripped, old_fingerprints, sources = historical
    current = [fingerprint(w["account_labels"], w["commands"]) for w in worlds]
    require(len(current) == len(set(current)), "Duplicate world fingerprint; no resampling")
    require(not set(current) & old_fingerprints, "Historical world fingerprint collision")
    for row in rows:
        require(digest(row["prompt"]) not in exact, "Historical exact input collision")
        require(
            digest(task_body(row["prompt"])) not in stripped,
            "Historical context-stripped input collision",
        )
    return {
        "sources": sources,
        "historical_unique_prompts": len(exact),
        "historical_unique_task_bodies": len(stripped),
        "historical_unique_world_fingerprints": len(old_fingerprints),
        "exact_collisions": 0,
        "context_stripped_collisions": 0,
        "fingerprint_collisions": 0,
        "normalizer": (
            "suffix starting at first Initial/Current permissions heading; otherwise exact"
        ),
        "limitation": "Literal and label-set disjointness, not semantic task independence",
    }


def pinned_tokenizer():
    from huggingface_hub import try_to_load_from_cache
    from transformers import AutoTokenizer

    model = specification()["model"]
    # Fail rather than implicitly accessing a different tokenizer or downloading weights.
    tokenizer = AutoTokenizer.from_pretrained(
        model["repo"],
        revision=model["tokenizer_revision"],
        trust_remote_code=False,
        local_files_only=True,
    )
    files = {}
    for name in ("tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt"):
        path = try_to_load_from_cache(model["repo"], name, revision=model["tokenizer_revision"])
        require(
            isinstance(path, str) and Path(path).is_file(), f"Missing pinned tokenizer file: {name}"
        )
        require(
            Path(path).parent.name == model["tokenizer_revision"], "Tokenizer revision mismatch"
        )
        files[name] = file_hash(path)
    return tokenizer, files


def token_records(rows, tokenizer):
    limit = specification()["model"]["max_total_tokens"]
    for row in rows:
        value = model_input(row)
        rendered = render_prompt(tokenizer, value["prompt"], "chat")
        contexts, candidates = [], []
        for command in value["choices"]:
            context, continuation = encode_boundary(tokenizer, rendered, command, limit)
            # Compare the archived concatenation to an independent whole-string call.
            whole = tokenizer(rendered + command, add_special_tokens=False)["input_ids"]
            require(
                context + continuation == whole, "Archived input differs from full tokenization"
            )
            contexts.append(context)
            candidates.append(
                {
                    "command": command,
                    "token_ids": continuation,
                    "token_count": len(continuation),
                    "total_tokens": len(whole),
                }
            )
        require(all(c == contexts[0] for c in contexts), "Candidate-dependent prompt tokens")
        yield {
            "id": row["id"],
            "rendered_prompt": rendered,
            "prompt_token_ids": contexts[0],
            "prompt_token_count": len(contexts[0]),
            "candidates": candidates,
        }


def _json(path, value):
    path.write_text(
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
    )


def _jsonl_gz(path, records):
    # Empty filename and mtime=0 make gzip headers independent of path and wall clock.
    with path.open("wb") as stream:
        with gzip.GzipFile(filename="", fileobj=stream, mode="wb", mtime=0) as compressed:
            for record in records:
                compressed.write((canonical(record) + "\n").encode())


def publish_artifacts(staging, destination):
    """Whole-directory publication; reruns verify identical bytes and never overwrite."""
    if destination.exists():
        old = {p.name: file_hash(p) for p in destination.iterdir() if p.is_file()}
        new = {p.name: file_hash(p) for p in staging.iterdir() if p.is_file()}
        require(
            old == new and len(list(destination.iterdir())) == len(old),
            "Existing preflight differs; choose a new output directory for review",
        )
        return "verified_identical"
    os.rename(staging, destination)
    return "created"


def prepare(destination=DEFAULT_OUT):
    destination = Path(destination)
    worlds, rows = build_inputs()
    print("Checking all printed inputs, simulator outcomes and paired controls...", flush=True)
    semantic, oracles, pairs = audit_inputs(worlds, rows)
    freshness = check_freshness(worlds, rows, historical_inventory())
    tokenizer, files = pinned_tokenizer()
    sentinel = "QUERY_REFERENCE_TEMPLATE_SENTINEL"
    wrapper = render_prompt(tokenizer, sentinel, "chat")
    require(wrapper.count(sentinel) == 1, "Ambiguous chat template wrapper")
    prefix, suffix = wrapper.split(sentinel)
    require(
        prefix.startswith("<|im_start|>system\n")
        and prefix.endswith("<|im_start|>user\n")
        and suffix == "<|im_end|>\n<|im_start|>assistant\n",
        "Unexpected official chat wrapper",
    )
    default_system = prefix.split("<|im_start|>system\n", 1)[1].split("<|im_end|>", 1)[0]
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".query-preflight-", dir=destination.parent))
    try:
        _json(staging / "worlds.json", worlds)
        _jsonl_gz(staging / "manifest.jsonl.gz", rows)
        _jsonl_gz(
            staging / "model-inputs.jsonl.gz",
            ({"id": r["id"], "model_input": model_input(r)} for r in rows),
        )
        _jsonl_gz(staging / "oracle.jsonl.gz", oracles)
        _jsonl_gz(
            staging / "pairs.jsonl.gz",
            ({"kind": kind, "pair": p} for kind, values in pairs.items() for p in values),
        )
        count, max_tokens, min_tokens = 0, 0, 2048
        command_lengths, stage_lengths = {}, {}

        def measured():
            nonlocal count, max_tokens, min_tokens
            for row, encoded in zip(rows, token_records(rows, tokenizer)):
                count += 1
                if count % 2688 == 0:
                    print(f"Token audit: {count}/{len(rows)} selections", flush=True)
                for c in encoded["candidates"]:
                    command_lengths.setdefault(c["command"], set()).add(c["token_count"])
                    lengths = stage_lengths.setdefault(row["stage"], [2048, 0])
                    lengths[0] = min(lengths[0], c["total_tokens"])
                    lengths[1] = max(lengths[1], c["total_tokens"])
                    max_tokens = max(max_tokens, c["total_tokens"])
                    min_tokens = min(min_tokens, c["total_tokens"])
                yield encoded

        _jsonl_gz(staging / "tokens.jsonl.gz", measured())
        require(count == len(rows), "Incomplete token audit")
        manifest_equivalent = {
            "worlds": {
                w["world_id"]: {
                    k: w[k] for k in ("account_labels", "operator_labels", "command_labels")
                }
                for w in worlds
            },
            "nuisance": {w["world_id"]: w["nuisance"] for w in worlds},
        }
        prior = json.loads((ROOT / "review/query-self-reference-protocol-check.json").read_text())
        require(
            digest(manifest_equivalent) == prior["world_assignment_hash"],
            "World assignments differ from the reviewed draft",
        )
        audit = {
            "protocol": specification()["protocol"],
            "status": "cpu_inputs_passed_not_frozen",
            "execution_enabled": False,
            "model_inference": False,
            "authorized_spend_usd": 0,
            "protocol_sha256": file_hash(SPEC_PATH),
            "evidence_base_commit": specification()["evidence_base_commit"],
            "source_files": {p: file_hash(ROOT / p) for p in SOURCES},
            "python": platform.python_version(),
            "packages": {
                n: importlib.metadata.version(n)
                for n in ("transformers", "tokenizers", "huggingface-hub")
            },
            "world_assignment_hash": digest(manifest_equivalent),
            "operator_name_as_self": dict(Counter(w["self_name"] for w in worlds)),
            "nuisance_counts": dict(Counter(str(w["nuisance"]) for w in worlds)),
            "order_convention": (
                "permission order starts with ranked accounts; binding order with declared "
                "operators; reverse according to bits 0/1"
            ),
            "semantics": semantic,
            "freshness": freshness,
            "tokenizer": {
                "repo": specification()["model"]["repo"],
                "revision": specification()["model"]["tokenizer_revision"],
                "files_sha256": files,
                "vocabulary_sha256": digest(tokenizer.get_vocab()),
                "backend_sha256": digest(tokenizer.backend_tokenizer.to_str()),
                "chat_template": tokenizer.chat_template,
                "chat_template_sha256": digest(tokenizer.chat_template),
                "default_system_text": default_system,
                "default_system_sha256": digest(default_system),
                "rendered_prefix": prefix,
                "rendered_suffix": suffix,
                "manually_added_system_message": False,
                "selections_checked": count,
                "candidate_boundaries_checked": count * 4,
                "min_total_tokens": min_tokens,
                "max_total_tokens": max_tokens,
                "stage_total_token_range": stage_lengths,
                "command_token_lengths": {c: sorted(v) for c, v in sorted(command_lengths.items())},
                "truncation": False,
                "scoring": specification()["model"]["score"],
            },
            "artifacts": {p.name: file_hash(p) for p in sorted(staging.iterdir())},
            "not_checked": [
                "model scores, performance, sample precision or scientific hypotheses",
                "runtime/scoring, interrupted-run resume and score-failure adjudication",
                "world-paired statistics, multiplicity, gates, reports and plots",
                "final protocol freeze, current provider quote or launch authorization",
            ],
        }
        _json(staging / "audit.json", audit)
        result = publish_artifacts(staging, destination)
        print(f"{result}: {destination}", flush=True)
        return audit
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    try:
        prepare(args.out)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"CPU preflight stopped: {exc}\n")


if __name__ == "__main__":
    main()
