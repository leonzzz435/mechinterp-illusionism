# Qwen Your/The control: execution and retrieval

The frozen [wording-control protocol](QWEN_POSSESSIVE_CONTROL.md) completed on 2026-11-07
as one authorized HF Jobs L4 run. All **6,144 choices** are present; zero failed, tied or invalid
outcomes; 48/48 controls passed. The [result](QWEN_POSSESSIVE_RESULTS.md) is
`no_clear_possessive_specificity`. Completion is distinct from a successful scientific test.

## Dispatch and resource record

The single job received an explicit **USD 5 allowance**. The quoted L4 price was
13,333 micro-USD/minute, giving **USD 1.613293 maximum compute** with a two-hour provider
limit plus one minute reserved for billing rounding. This is a recorded quote, not an
inspected invoice. No new job was submitted during retrieval or analysis.

- Job: [`6aef27e1e6320c66fad5b4f1`](https://huggingface.co/jobs/zett13/6aef27e1e6320c66fad5b4f1).
- Created: `2026-11-07 13:30:09.429000+00:00`; final provider status **COMPLETED**.
- Run folder: `qwen-possessive-f2baaa2fb6b74880`; manifest run ID: `qwen-33a5f3f8b0434e38`.
- Source commit: `15e6bf8534b8f8985b941fa164dfcc832ce75c17`, clean and pushed before launch.
- Source bundle SHA256: `f62be4bbd9eeabfada5ed142331990d0fc7ad0e2018e2dbe3abda9509a62ead0`.
- Private source revision: `4d692010078dda6e0acc2bf7aff2f8fb515075b5`.
- Configuration: `configs/qwen-possessive-control.json`, SHA256
  `22451eed4ea1bed314cd9815ac5da6b2282255138deb1331ee21e92e7cae21c5`.
- Frozen plan SHA256: `ab455c85fb4a1c0e237dcbd317f1e0be4401d65dc2cc0a8d9bbe95994d0b511d`.
- Source package SHA256: `c010eed1fccb01572f7ed6316fcb5aa9859059cde4bda13a7eb242e86a6881f4`.
- Qwen2.5-7B-Instruct and tokenizer revision `a09a35458c702b33eeacc393d103063234e8bc28`;
  one L4, unquantized BF16, batch 1, official chat, summed full-command log-likelihood.
- Invocation: 2,567.35 seconds (**42.79 minutes**) within the 90-minute cooperative limit;
  peak allocated GPU memory **15,565,164,032 bytes (14.50 GiB)**. Setup/upload time and billing
  need not equal the measured experiment invocation.

The [credential-free receipt](../review/qwen-possessive-job.json) preserves configuration,
image and source pins. Keep `.hf-jobs/qwen-possessive-control.json`, the local duplicate guard.
The first [startup check](../review/qwen-possessive-startup.json) verified 384 successful
records at private revision `7dbdfea5f00aafaeddf981849e88f80d5b18d493`, including actual L4,
source/plan hashes, matched tokens and checkpoint persistence.

## Immutable final evidence

Final artifacts were retrieved at private dataset revision
`4f707929010cd0603d00f4deb5f9c3e73c88f5f1`. The original archive is tracked unchanged at
`review/evidence/qwen-possessive-f2baaa2fb6b74880.tar.gz` (6,242,214 bytes), SHA256
`d521a63c21c360b33ba8452ab5d572eaf0d06c4e4be02df02425dfc1c2fe3e59`.
All 54 payload checksums passed. The archive includes source, manifest, rendered prompts,
token IDs, all candidate scores, simulator outcomes, SQLite journal, analysis and figures.
The frozen design archive and all earlier run archives remain unchanged.

- [Completion provenance](../review/qwen-possessive-completion.json).
- [Independent saved-output reaggregation](../review/qwen-possessive-audit.json).
- [Frozen source, tokens, journal and figure verification](../review/qwen-possessive-verification.json).
- [Interpreted result](QWEN_POSSESSIVE_RESULTS.md) and [complete exported report](QWEN_POSSESSIVE_FULL_REPORT.md).

## Reproduce from either computer

After pulling Git, the original archive and second implementation audit need no HF credentials
or model weights. A normal `uv sync --locked` installs the base NumPy/plot/test dependencies.
Use `--no-sync` with an existing environment to preserve its installed optional extras.

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 uv run --no-sync python scripts/review_possessive_evidence.py
uv run --no-sync python scripts/plot_qwen_possessive.py
uv run --no-sync pytest -q tests/test_possessive_evidence.py
```

To recheck the frozen analysis, actual tokenizer inputs and original figure bytes:

```bash
# Requires the eval extras and pinned Qwen tokenizer already cached; no weight download.
uv run --no-sync python scripts/verify_possessive_run.py
```

This verifier checks archive integrity before extracting into a temporary directory and runs
the **archived source** in a subprocess, with offline HF access. It must not use future package
changes to reinterpret history. Byte-identical plots require compatible rendering dependencies
and fonts; the archive records package versions. Current verification passed exactly.
Neither verifier independently reruns the expensive model forward computation.

For read-only access to the provider copy, with local HF authentication:

```bash
uv run --script scripts/hf_jobs.py status --receipt review/qwen-possessive-job.json
uv run --script scripts/hf_jobs.py logs --receipt review/qwen-possessive-job.json
uv run --script scripts/hf_jobs.py fetch --receipt review/qwen-possessive-job.json
```

Reporting commits do not change the execution commit. Do not resubmit this completed job.
The bounded experiment is complete; interpretation and external methodological review come
before any proposal for further paid inference.
