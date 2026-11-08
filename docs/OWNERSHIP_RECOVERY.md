# Ownership tranche: upload failure and bounded continuation

The three initial jobs failed while uploading checkpoints, after successful model
evaluation had already produced most of the scheduled records. This is an infrastructure
failure, not a failed scientific endpoint. No conclusion is drawn from the incomplete
tranche. The article remains frozen at `article-v1`.

**Continuation launched on 2026-11-08:** after explicit approval of the additional
$0.62 budget, [one L4 job](https://huggingface.co/jobs/zett13/6af09fc30e0338d1bb84c173)
was submitted from commit `846e274fcef7a55f6a1fc5d9a1f82f543f93350a`. The provider
reported `RUNNING`; startup logs showed the preserved snapshot restored and model
weights downloading. This is a launch observation, not a completed result. The
[launch receipt](../review/ownership-recovery-job.json) records the source and limits.

## What failed and what survived

All three logs identify `ConnectionError: ... (429 Too Many Requests)` in
`huggingface_hub._commit_api._upload_xet_files`, at the Xet CAS upload service. The
exception propagated through the scenario checkpoint callback in `pilot.py`, which
marked the run failed. The worker then attempted additional uploads in finalization.
The old code had no bounded handling of this failure. Concurrent uploads are a plausible
contributor, but the logs do not identify the server's exact quota or prove that
concurrency alone caused it.

The [recovery audit](../review/ownership-recovery-audit.json) pins the private dataset
snapshot `60a71b30b5a86c1931653b20f968431118b76435`, original manifest/error hashes,
all recorded trial checksums and the simulator/token audit. All recovered trial statuses
are `ok`; that means technically valid selections, not necessarily correct answers.

| Original block | Persisted selections | Still missing | Original final export |
|---|---:|---:|---|
| 00 | 4,992 | 1,152 | No; journal and manifest recovered |
| 01 | 5,376 | 768 | Present and checksums verified |
| 02 | 4,608 | 1,536 | Present and checksums verified |
| Total | **14,976 / 18,432 (81.25%)** | **3,456** | |

The recovered originals remain unchanged in that pinned revision and under
`.hf-jobs/recovered-ownership/`. A second private backup contains all three original
run directories and the audit. The [CPU upload/download receipt](../review/ownership-upload-check.json)
records its SHA256 and immutable revision. Its 12,753,049-byte archive was successfully
uploaded using the corrected transfer path and downloaded with a matching checksum;
this check incurred no GPU compute. A single successful transfer does not guarantee
future service availability.

## Transport correction

The worker disables the optional Xet client using
[`HF_HUB_DISABLE_XET`](https://huggingface.co/docs/huggingface_hub/en/package_reference/environment_variables#hfhubdisablexet).
The installed, pinned Hub 0.36.2 implementation was inspected: this removes Xet from
the offered transfer protocols and leaves its HTTP/LFS path available. The worker uses
the public `create_commit(..., num_threads=1)` API, because that version's
`upload_folder` does not expose a thread limit. An initial CPU probe caught that API
distinction before any recovery GPU job; the tests now enforce the installed SDK's
actual method signature.

Checkpoint retries are restricted to transient connection/time-out failures and
HTTP 408, 429, 500, 502, 503 or 504. They use exponential waiting with jitter, respect
`Retry-After` when supplied, allow at most five attempts per changed snapshot and
at most 600 seconds of retry sleep across the job. Authentication, validation and model
errors are not retried. After transfer exhaustion, finalization cannot start another
upload burst. Repeated checkpoints with unchanged files are skipped. These are retries
of storing existing results, not model calls or new jobs.

Hugging Face documents [429 throttling and spreading requests over time](https://huggingface.co/docs/hub/en/rate-limits).
Its documented Hub request buckets do not establish the precise quota for the CAS
endpoint in these logs. No dependency upgrade or scientific-source change was made.

## One continuation, only the missing cases

[The recovery configuration](../configs/qwen-ownership-recovery.json) selects **one L4
job** that continues blocks 00, 01 and 02 sequentially. It pins the original repository
revision and each block's manifest, error and record hashes. Before loading weights,
it audits every source block and requires the specific upload-only failure and zero
failed selections. A model failure cannot be cleared by this path.

Only a new working copy changes from `failed` to `paused`. The original failed manifest,
error and export checksums are preserved in its `recovery/` history; continuation
provenance records the new worker commit separately. Model, tokenizer, prompts, scores,
scientific package source and all existing records remain fixed. The existing journal
skips saved IDs. Each completed block is exported; a failed or paused block stops the
group. No second recovery is automatic.

The cooperative limit is 30 minutes across the group, with a 45-minute provider limit.
At the refreshed $0.013333/minute quote, reserving 46 billable minutes bounds this new
job's compute at **$0.613318**. The user approved **$0.62 additional** for this one
continuation; the quote is not an invoice for the initial jobs. The original
three-job receipts and aggregate guard are retained.

Commands used for this approved continuation from a clean, pushed checkout:

```bash
uv run --script scripts/hf_jobs.py plan --namespace zett13 --budget-usd 0.62 \
  --config configs/qwen-ownership-recovery.json
uv run --script scripts/hf_jobs.py submit --namespace zett13 --budget-usd 0.62 \
  --config configs/qwen-ownership-recovery.json
```

The separate receipt `.hf-jobs/qwen-ownership-recovery.json` prevents duplicate starts.
The job has been submitted; do not resubmit it. Read-only monitoring and download:

```bash
uv run --script scripts/hf_jobs.py status --receipt .hf-jobs/qwen-ownership-recovery.json
uv run --script scripts/hf_jobs.py fetch --receipt .hf-jobs/qwen-ownership-recovery.json \
  --out .hf-jobs/downloads
```

The downloaded group has `run/recovery-state.json`, `run/block-00` through `block-02`,
per-block archives under `exports/`, and `run/combined/` for the combined report and plots.
Unlike the single-run layout, the top-level fetch receipt does not certify all nested
exports. Verify the nested run journals and regenerate the combined report with:

```bash
uv run --no-sync python scripts/ownership_tranche.py analyze \
  --runs RECOVERY_JOB/run/block-00 RECOVERY_JOB/run/block-01 RECOVERY_JOB/run/block-02 \
  --out review/ownership-recovered-results
```

Complete coverage and the original analysis gates remain mandatory. The article,
designs, confidence work and scientific package under `src/` were not modified by this
repair. Mistral and routing remain outside this continuation.

## Verification

Targeted tests passed **46/46**, covering the actual SDK call contract, serial transfers,
retry/header limits, unchanged-snapshot skipping, permanent failures, source tampering,
preservation of original failed records, exactly-once journal continuation, sequential
block handling, early stop on model failure and the recovery quote/worker dispatch.
The real private-repository round trip passed separately. The complete offline suite
passed **197/197 in 579.23 seconds**. A final inspection of Hub 0.36.2 found that its LFS
helper wraps HTTP errors in `RuntimeError`; the worker now follows that explicit cause
chain for retry classification and `Retry-After`. Three additional tests exercise the
installed SDK's real wrapper for 429, 503 and permanent 403 errors. The final affected-area
run passed **46/46 in 10.15 seconds**, including those additions:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --no-sync pytest -q \
  tests/test_hf_checkpoint_recovery.py tests/test_hf_jobs.py \
  tests/test_ownership_cloud.py tests/test_runner.py::test_configs_are_loadable
```

Ruff check/format and `git diff --check` passed. Frozen article/design files match
`article-v1`; scientific source and the original preflight match execution commit
`23f9ea8`. No recovery model inference was used as a software test.
