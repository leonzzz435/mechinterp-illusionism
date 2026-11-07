"""Offline disjointness and frozen design audit, with optional CPU tokenizer verification."""

import argparse
import json
import re
import tarfile
from pathlib import Path

from self_model_study.io import digest, file_hash
from self_model_study.pilot import jobs_in
from self_model_study.possessive import DEFAULT_SPEC, build_plan, preview, tokenizer_audit

PRIOR = {
    "qwen-78ee6db8adfc4f3e.tar.gz": (
        "cf8eceea87129acaad2365f36af99d8f54923015923c837419a691252b8f12fa"
    ),
    "qwen-role-96787d5e7adf4c4d.tar.gz": (
        "36614cb2aae236d450d57540c9b76dfddfec2d4bd2a59f177dce296058b13a8d"
    ),
    "qwen-patch-3bd8fc27cbb147c9.tar.gz": (
        "017e6e0f78e6ae793fbdb5a7ca3a2e4055750c840cc2da2553819fafb0304207"
    ),
}


def input_signature(row, remove_context=False):
    prompt = row["prompt"]
    if remove_context:
        prompt = re.sub(
            r"(?:Your active|The active|Reference) connection: [^.]+\.", "<CONTEXT>", prompt
        )
    return digest([prompt, row["choices"]])


def audit(tokenizer_check=False):
    jobs = jobs_in(build_plan(DEFAULT_SPEC))
    inputs = {input_signature(j["row"]) for j in jobs}
    content = {input_signature(j["row"], True) for j in jobs}
    scenario_ids = {j["row"]["scenario_id"] for j in jobs}
    historical = []
    for name, checksum in PRIOR.items():
        path = Path("review/evidence") / name
        if file_hash(path) != checksum:
            raise ValueError("Historical archive checksum changed: " + name)
        with tarfile.open(path) as archive:
            plan = json.load(archive.extractfile("run/plan.json"))
        old = [j for j in jobs_in(plan) if j["kind"] == "action"]
        overlaps = {
            "scenario_id_overlap": len(scenario_ids & {j["row"]["scenario_id"] for j in old}),
            "exact_input_overlap": len(inputs & {input_signature(j["row"]) for j in old}),
            "context_removed_input_overlap": len(
                content & {input_signature(j["row"], True) for j in old}
            ),
        }
        if any(overlaps.values()):
            raise ValueError("Prior model exposure found: " + name)
        historical.append(
            {"archive": name, "sha256": checksum, "action_records": len(old), **overlaps}
        )
    return {
        **preview(DEFAULT_SPEC),
        "historical_exposure": historical,
        "unique_exact_inputs": len(inputs),
        "unique_context_removed_inputs": len(content),
        "note": "No overlap with any archived Qwen action run, including technical repeats. "
        "Rated archives contain the same model outputs and are not a distinct exposure. "
        "Same generator, vocabulary and template; no held-out-template generalization. "
        "Repeated before-update prompts are retained as dependent paired variants.",
        **({"tokenizer": tokenizer_audit(DEFAULT_SPEC)} if tokenizer_check else {}),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tokenizer-check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(audit(args.tokenizer_check), indent=2, sort_keys=True))
