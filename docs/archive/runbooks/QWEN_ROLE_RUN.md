# Qwen role-framing execution record

The frozen [role-framing control](QWEN_ROLE_CONTROL.md) was submitted as one HF Jobs L4
run on 2026-11-07. **The run completed and its original export is verified: 2,048 choices,
zero measurement errors, and the decision `wording_sensitive_candidate`.** See the
[results and figures](QWEN_ROLE_RESULTS.md). The earlier Qwen capability screen remains
failed; this control measures a wording interaction and contains no internal intervention.

## Dispatch and budget

The user authorized this control within USD 19 of available credit. The provider quoted
13,333 micro-USD per minute: a two-hour limit plus one rounding minute bounds quoted compute
at **USD 1.613293**. This is an estimate, not an inspected invoice. The experiment has its
own 90-minute cooperative limit and eight independently uploaded scenario blocks.

- Job: [`6aeef0a50e0338d1bb82fb92`](https://huggingface.co/jobs/zett13/6aeef0a50e0338d1bb82fb92).
- Created: **2026-11-07 09:34:29 UTC**. Initial observed state: `SCHEDULING`, pulling image.
- Run folder: `qwen-role-96787d5e7adf4c4d`.
- Source commit: `e7bd7a64692110bafca86021b56f4bf535641a80` (pushed before dispatch).
- Source bundle SHA256: `1bffc46c061cde96db12399fff42fc40cc2c22df6d1895ca8cba64bcae1a5f41`.
- Private source revision: `2a9b9fc46a6a968e88b20daab6cc269e9a6baa83`.
- Config: `configs/qwen-role-control.json`; file SHA256
  `c551a25a250a460ab5c62709f875d7d3e87702b6eca809acf35924d96557e325`.
- Frozen plan SHA256: `ee4dfa480160113843b530897828e6b94009b00f8e1590a7d38975e4bacc4a76`.
- Model/tokenizer: Qwen2.5-7B-Instruct at `a09a35458c702b33eeacc393d103063234e8bc28`.
- One L4, BF16, batch 1, 2,048 command selections, no generation, four context conditions.

At 09:35 UTC the provider reported `RUNNING`; dependency setup completed and the pinned
model weights were downloading. At 09:35:35 UTC the initial private checkpoint was verified
at repository revision `486dc081227d3ad211300a420d566043280ca9a7`: the correct engine and
2,048 expected records, with zero completed outputs at that initial checkpoint. This confirms
startup and persistence; the completed evidence is recorded below.

## Completed evidence

The provider now reports `COMPLETED`. The runner records one invocation starting at
09:35:08 UTC, lasting **850.13 seconds**, with all 2,048 choices saved and no failures,
ties or invalid scores. Peak allocated GPU memory was **15,572,063,744 bytes** (14.50 GiB).
This elapsed time includes loading and in-run checkpoints, excluding setup and final export.
No continuation was needed. The actual invoice was not inspected.

The original archive was fetched at private result revision
`6d67821e9a2c3d8f7739087784b41c95bde3d236` and copied byte-for-byte into Git as
`review/evidence/qwen-role-96787d5e7adf4c4d.tar.gz` (2,271,948 bytes), SHA256
`36614cb2aae236d450d57540c9b76dfddfec2d4bd2a59f177dce296058b13a8d`.
All 39 payload hashes and 2,048 record digests pass. A separate audit reconstructs every
score selection and simulator outcome, all 512 quartets, 12 accuracy cells, 32 controls,
scenario interactions and exact sign flips. Local frozen analysis matches the cloud result
exactly. All 2,048 rendered prompts and 8,192 continuation boundaries match the pinned
tokenizer, and the SQLite journal agrees with the JSONL export.

The primary interaction is +16.41 pp (nominal 95% scenario-bootstrap +8.59 to +25.78),
positive in seven scenarios with one zero; two-sided sign-flip p=0.015625. All 32 controls
pass, with minimum accuracy 82.81%. This meets the planning rule, not the original functional
capability gate. No internal intervention or additional paid run followed this analysis.

The [dispatch receipt](../review/qwen-role-control-job.json) retains the image, hardware
quote, source/config pins and job identity, without credentials. The local duplicate guard
is `.hf-jobs/qwen-role-control.json`; do not remove it or resubmit the original command.
The private artifact repository is `zett13/mechinterp-illusionism-results`.

## Retrieve and evaluate

```bash
uv run --script scripts/hf_jobs.py status --receipt .hf-jobs/qwen-role-control.json
uv run --script scripts/hf_jobs.py logs --receipt .hf-jobs/qwen-role-control.json
uv run --script scripts/hf_jobs.py fetch --receipt .hf-jobs/qwen-role-control.json
```

On another checkout, the tracked `review/qwen-role-control-job.json` can be used as the
`--receipt` for these read-only commands. Fetch pins one result-repository revision and
checks available export hashes. The final worker export includes raw outputs, all scores,
tokenization records, simulator outcomes, analysis, report and SVG/PDF/PNG figures.
Keep the downloaded original archive unchanged before making any local analysis copy.

Evaluate coverage and all frozen controls before interpreting the primary interaction.
Incomplete/invalid data cannot nominate a mechanistic follow-up. A substantive stop
decision closes this diagnostic branch; no prompt search or internal edit follows
automatically. The protocol documents the exact thresholds and limitations.
