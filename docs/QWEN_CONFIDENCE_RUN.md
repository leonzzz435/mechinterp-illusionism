# Qwen confidence pilot: execution record

The user authorized implementation and the bounded pilot on 2026-11-08
(“ja go is alles freigegeben”). The selected scope is one L4 job, no automatic continuation,
90 minutes cooperative execution and a two-hour provider limit. A separate **USD 5 budget**
is used for this dispatch. This document will retain the actual job ID and source pins
after submission; it is not evidence that a job has already run.

The live HF hardware quote on 2026-11-08 is 13,333 micro-USD per minute. Including one extra
minute for billing rounding gives **USD 1.613293 maximum compute**. This is a quote, not an
invoice. Prelaunch tests and tokenizer checks are complete; see [verification](VERIFICATION.md).
The previous 6,144-choice run took 42.79 minutes for its model invocation. This
pilot has fewer selections and shorter single-digit continuations, but confidence prompts
are longer and there are dependency/calibration checks. No measured runtime for this new
workload exists before its first job; the fixed limits bound the feasibility attempt.

## Frozen scope

- Protocol `qwen-confidence-pilot-v1`, engine `qwen-confidence`.
- Qwen2.5-7B-Instruct and tokenizer revision
  `a09a35458c702b33eeacc393d103063234e8bc28`, BF16, official chat, batch 1.
- 64 calibration + 128 assessment questions, four rotations per question.
- 1,792 selections, 10,752 candidate likelihoods, 24 checkpoint blocks.
- Frozen plan SHA256:
  `9ed0bc8322c2bbdc5f41a6a1ee870c49c11cce11d2a92e29c8ae8dc569edfc16`.
- Token-input fingerprint remains identical to the original approved CPU design:
  `23e67a671d6c1e88ea581cc99340d23590f90569c274d973e6d1cd61e60dd83c`.
- Actual execution preparation: [CPU audit](../review/qwen-confidence-execution-preflight.json).

Eight calibration blocks precede sixteen assessment blocks. Temperature is frozen using
only all 256 calibration records before the first assessment selection. Every confidence
record references its real parent-answer checksum; assessment records additionally pin the
calibration checksum. Block uploads preserve completed work in the private HF dataset.
A hard provider kill can lose work since the last successful upload. Failed scoring stops
the run and remains in the export; no automatic retry or replacement question is used.

## Commands

Preparation and validation (no pretrained model inference):

```bash
uv run --no-sync python scripts/review_confidence_design.py --fetch
uv run --no-sync self-study validate configs/qwen-confidence-pilot.json --tokenizer-check \
  --freeze .hf-jobs/confidence-design-v1
uv run --no-sync pytest -q
uv run --no-sync ruff check src tests scripts
uv run --no-sync ruff format --check src tests scripts
```

The following dispatch command spends the separately authorized allowance once. An existing
receipt refuses duplicate submission, including an unknown provider response. Do not run it
again as a way of checking status.

```bash
uv run --script scripts/hf_jobs.py submit --namespace zett13 --budget-usd 5 \
  --config configs/qwen-confidence-pilot.json
uv run --script scripts/hf_jobs.py status --receipt .hf-jobs/qwen-confidence-pilot.json
uv run --script scripts/hf_jobs.py fetch --receipt .hf-jobs/qwen-confidence-pilot.json
```

After retrieval, use the returned run directory with `self-study analyze` or `export`.
The raw journal, actual dependent prompts, all digit scores and failures, calibration fit,
fold membership, out-of-fold predictions, report, article section and SVG/PDF/PNG figures
are archived together. This pilot has no activation intervention or automatic follow-up job.
