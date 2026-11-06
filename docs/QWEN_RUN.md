# Qwen pilot execution record

This records execution of the frozen [Qwen protocol](QWEN_PILOT.md), separately from its
design and from the historical Gemma results. Human ratings and real-model results remain
pending until explicitly recorded below.

## Authorized job

The user approved one new L4 job with a maximum budget of USD 5 on 2026-11-06. This approval
is separate from the earlier completed Gemma job and does not authorize another submission,
continuation, automatic retry or model switch.

- Job: [`6aee264e0e0338d1bb820450`](https://huggingface.co/jobs/zett13/6aee264e0e0338d1bb820450),
  created 2026-11-06 19:11:10 UTC.
- Run: `qwen-78ee6db8adfc4f3e`; configuration: `configs/qwen-pilot.json`.
- Executed source is pinned to `9f1356f139e48c108dbfa5eedb7950fefdf4104a`.
- Source bundle SHA256: `62d25f10d904b474e9eac96a3ea03e82d3ecacadee61e4935e16319c5ad63537`.
- Private source artifact revision: `e37a38cebd9d53938dcfa811f2a83130b2d7aae7`.
- Config file SHA256: `c38c2f89c6d9deb97ebbf5dce7c5453c11da5b46074257bb50d051adc0db91c1`.
- Frozen plan SHA256: `01014cf0746e4d42836454bec780a0917d4b2b953dab6ddc373a4dda8d03243f`.
- One NVIDIA L4, BF16, batch 1; 90-minute cooperative invocation limit, two-hour provider limit.
- Submission-time quote: USD 1.613293 for 121 billable minutes including rounding reserve.
  This is a compute estimate, not a measured invoice or account-wide billing cap.

The local receipt is `.hf-jobs/qwen-pilot.json` (ignored by Git). It records the existing
dispatch and prevents duplicate submission. The private artifact repository is
`zett13/mechinterp-illusionism-results`. No credentials are included in this document.

## Observed status

At 2026-11-06 19:19:52 UTC, HF reported `SCHEDULING` with the message
“Waiting for requested hardware to become available.” No worker logs or Qwen outputs
were available at that check. Submission is not completion.

## Evidence workflow

```bash
uv run --script scripts/hf_jobs.py status --receipt .hf-jobs/qwen-pilot.json
uv run --script scripts/hf_jobs.py logs --receipt .hf-jobs/qwen-pilot.json
uv run --script scripts/hf_jobs.py fetch --receipt .hf-jobs/qwen-pilot.json
```

Fetch pins the artifact revision and verifies the exported archive and internal file hashes.
The original export must remain unchanged. A separate standard-library audit also checks
the frozen plan, source snapshot and record digests, reconstructs permission transitions
and execution, and reaggregates scores, strata, counterfactual pairs and format contrasts:

```bash
python3 scripts/review_qwen_evidence.py PATH_TO_ORIGINAL_ARCHIVE --sha256 RECORDED_ARCHIVE_SHA256
```

This audit neither reruns inference nor independently verifies likelihood arithmetic,
bootstrap intervals or construct validity. A partial run is reported as partial; it cannot
pass the screen. An error must be inspected before any separately authorized next job.

The 40 blind ratings are a remaining human task. Share only `blind_ratings.csv` and
`rating_instructions.md` with the rater before rating. Condition keys, example comparisons,
language plots and the full report would compromise that blinding.
