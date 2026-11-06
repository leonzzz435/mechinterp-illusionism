# Qwen pilot execution record

This records execution of the frozen [Qwen protocol](QWEN_PILOT.md), separately from its
design and from the historical Gemma results. **The GPU run completed, all artifacts are
verified, and both action-format screens failed.** All 40 human ratings are now integrated
with two unclear entries retained. See [results](QWEN_RESULTS.md).

## Authorized job

The user approved one new L4 job with a maximum budget of USD 5 on 2026-11-06. This approval
is separate from the earlier completed Gemma job and does not authorize another submission,
continuation, automatic retry or model switch.

- Job: [`6aee264e0e0338d1bb820450`](https://huggingface.co/jobs/zett13/6aee264e0e0338d1bb820450),
  created 2026-11-06 19:11:10 UTC.
- Artifact/run folder: `qwen-78ee6db8adfc4f3e`; internal manifest run ID: `qwen-677922e82a154b35`.
  Configuration: `configs/qwen-pilot.json`.
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

The local observer first saw `RUNNING` at 19:25:01 UTC and `COMPLETED` at 20:22:31 UTC
on 2026-11-06. These are polling observations, not exact provider start/stop timestamps.
The runner itself recorded a start at 19:25:11 UTC and 3,416.07 seconds of elapsed time,
including model loading and in-run checkpoints but excluding dependency setup and final export.
It completed all 3,232 outputs with zero execution/scoring errors; peak allocated GPU memory
was 15,572,367,872 bytes (14.50 GiB). No continuation was needed or submitted.

The final export was retrieved at immutable private artifact revision
`634e96e2663b5ecc29bb0592d679ea397cbf551c` and copied unchanged into Git:
`review/evidence/qwen-78ee6db8adfc4f3e.tar.gz`, 4,103,590 bytes, SHA256
`cf8eceea87129acaad2365f36af99d8f54923015923c837419a691252b8f12fa`.
All 48 internal file hashes, the executed source snapshot and all 3,232 record digests pass.
The independent audit reaggregates 3,072 action selections, 52 strata and 18 paired strata.

The job ended within both time limits. The invoice was not inspected; the quoted upper
compute estimate above must not be presented as an actual charge.

[Full action report](QWEN_RESULTS.md) · [independent audit](../review/qwen-audit.json) ·
[post-run CPU verification](../review/qwen-post-run-verification.json).

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

## Human-rating import

The supplied `review/ratings/qwen-78ee6db8adfc4f3e/human_ratings.csv` contains all 40
planned responses, one rater ID and two unclear cells. Exact text/ID validation passed.
Its SHA256 is `9099d43eb24cb1b7b9a2b4d7af63ec620a5fd902e8a11a6a39197b649345cf2b`.
The author supplied judgments through the sheet without format labels, after discussing the
action results. This is a single-author rating, not independent replication or inter-rater agreement.

A separate copy of the original export was analyzed with the unchanged package and exported
as `review/evidence/qwen-78ee6db8adfc4f3e-with-ratings-v1.tar.gz`, SHA256
`c260bb001dac8841def6bdb28d7b5e418e9f329c44e005602f5467bd40c3aa9b` (4,133,763 bytes).
It contains 49 checksummed files. Original raw model data, journal, source snapshot,
manifest, plan and model inputs remain byte-identical; only human analysis and its figures
were added or updated. No additional inference or cloud job was performed.

The paired disclaimer estimate is +20 pp (nominal 95% bootstrap +5 to +40), driven by four
prompt pairs. The other two metrics have no complete determinate paired estimate under the
frozen rule. The action screen remains failed. [Import provenance](../review/qwen-ratings-provenance.json)
and [independent rated audit](../review/qwen-with-ratings-audit.json) preserve the checks.
