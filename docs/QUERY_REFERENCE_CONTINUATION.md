# Remaining query-reference blocks: authorized and submitted

On 2026-11-09 the user approved **10 USD total** for the five remaining jobs, blocks
01–05. All five requests were accepted. They cover 40 worlds and 13,440 selections;
together with completed block 00 this is the frozen 48-world / 16,128-selection sample.
Submission is not completion or a scientific result.

The [launch record](../review/query-reference-remaining-launch.json) preserves the
authorization, current price, aggregate reservation, source/config hashes, run names
and a timestamped provider-status snapshot. Its status fields are not a live monitor.

| Block | Worlds | Job |
|---|---|---|
| 01 | 0008–0015 | [HF job](https://huggingface.co/jobs/zett13/6af19f62ab34849891a7c549) |
| 02 | 0016–0023 | [HF job](https://huggingface.co/jobs/zett13/6af19f669737d9a9e08c37b3) |
| 03 | 0024–0031 | [HF job](https://huggingface.co/jobs/zett13/6af19f6b9737d9a9e08c37b8) |
| 04 | 0032–0039 | [HF job](https://huggingface.co/jobs/zett13/6af19f6eab34849891a7c54e) |
| 05 | 0040–0047 | [HF job](https://huggingface.co/jobs/zett13/6af19f72ab34849891a7c552) |

## Cost and execution boundary

The refreshed [HF hardware quote](https://huggingface.co/api/jobs/hardware) was
13,333 micro-USD per L4 minute. Five two-hour provider limits, each with one extra
rounding minute, give a combined compute bound of **8.066465 USD**. This is below
the approved 10 USD aggregate budget. It is not an invoice or an account-wide cap.
Individual launcher receipts refer to that same aggregate approval, not five separate
10 USD allowances. No automatic job retry, additional model or replacement block is
authorized. Existing bounded checkpoint-transfer retries remain part of the frozen worker.

Jobs may run concurrently subject to hardware availability. About 110 minutes of
summed worker time, extrapolated from block 00, is neither elapsed waiting time nor
a guaranteed runtime. Setup, transfers and provider scheduling remain variable.

Every job uses execution commit `59061cacf191f737689997b1bb327e75accc71fa`, the frozen
Qwen/model/tokenizer revisions and its original configuration. The reporting commitment
was pushed as `e90eef6` **before** these jobs were submitted. Keep execution `main`
at `59061ca` and results on `results/query-reference-block-00`. The article remains
at `article-v1`; thresholds and sample size have not changed.

## Retrieval and final analysis

Inspect the existing jobs and receipts; do not run `submit` again. Once they finish,
fetch the saved artifacts from the execution checkout:

```bash
for block in 00 01 02 03 04 05; do
  uv run --no-sync python scripts/hf_jobs.py fetch \
    --receipt ".hf-jobs/qwen-query-reference-${block}.json"
done
```

Each fetch pins a repository revision and checks the downloaded export when present.
Verify the terminal job states, complete manifests, all records/checksums and common
execution provenance before interpreting a combined result. Preserve all six original
archives and their receipts. An incomplete or failed block stays visible and is not
silently replaced.

The frozen CPU analysis command for these exact run names is:

```bash
uv run --no-sync self-study analyze \
  .hf-jobs/downloads/qwen-query-00-4edce03e18d645e7/run \
  --additional-runs \
    .hf-jobs/downloads/qwen-query-01-3e8146c179334aed/run \
    .hf-jobs/downloads/qwen-query-02-35f38f414794405a/run \
    .hf-jobs/downloads/qwen-query-03-66fe986cf6bf4755/run \
    .hf-jobs/downloads/qwen-query-04-9979bdcdc3b54eb2/run \
    .hf-jobs/downloads/qwen-query-05-8a4e517e46f84899/run \
  --out .hf-jobs/query-reference-combined
```

Apply the [reporting commitment](QUERY_REFERENCE_INTERPRETATION_PLAN.md) regardless
of whether lookup controls pass. Complete, valid data receive the frozen estimates,
intervals and tests even if the gate fails; the failed candidate decision remains
explicit. Incomplete data do not receive inferential intervals or a final candidate claim.
