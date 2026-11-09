# Query-bound self-reference: frozen execution and handover

**Execution update:** [Block 00 is complete](QUERY_REFERENCE_BLOCK00_RESULTS.md), with 2,688 valid selections in eight of 48 worlds. The study remains incomplete; the pre-run freeze and its verification records below remain unchanged.

The generator, scorer integration, resumable execution, analysis and report exporter
are implemented. **At the software freeze, no pretrained-model assessment had run.** The original
[scientific JSON](../designs/query-self-reference-v1.json) and
[CPU input audit](../review/query-self-reference-preflight/audit.json) remain unchanged.
The separate [freeze record](../designs/query-self-reference-v1.freeze.json) seals their
scientific content together with the execution source and six block plans. The draft's
historical administrative fields are preserved; the freeze record is the current status.
It allocates no spend and authorizes no paid launch.

## What is fixed

- Qwen2.5-7B-Instruct and tokenizer revision
  `a09a35458c702b33eeacc393d103063234e8bc28`; BF16, no quantization or fallback.
- The same 48 worlds and 16,128 prepared selections. Six explicitly selected blocks
  contain eight worlds / 2,688 selections each. No sampling, prompt or endpoint changes.
- The official chat template, its recorded default system message and an open assistant
  turn. Each candidate is the exact full command, without added whitespace or EOS.
- Native `lm-eval==0.4.13` summed conditional likelihood, batch size one, eager attention
  and FP32 softmax. Logit reuse and KV caching are disabled. The unequal command lengths
  remain visible; there is no length normalization.
- All three directional hypotheses E, F and S, the eight named accuracy gates and eight
  paired lookup gates, and the prespecified secondary analyses.

The [runtime](../src/self_model_study/query_reference_runtime.py) reuses the existing
native scorer and transactional journal. It verifies source and input checksums and
checks every selected block's tokenizer inputs before weights load. Each scored result
is compared against the archived prompt/candidate IDs. The backend receives only prompt,
candidate strings and format, never an answer key or simulator state.

## Interruptions, failures and coverage

SQLite commits each completed selection before updating the manifest. If an interruption
falls between those writes, resumption recovers the committed record and skips it. A
completed run does not reload the model. The same configuration, source, Python/package
environment and backend metadata are required for continuation. The provider checkpoint
callback persists completed worlds; a provider hard kill can lose work since the latest
successful remote checkpoint, not the already uploaded checkpoints.

There are no automatic trial retries. A nonfinite score, input/token mismatch or scoring
exception is saved and stops the block. For a malformed scorer response, its raw output
is retained in the error record. Exact finite ties have no arbitrary winner: they remain
invalid selections and the block can finish with errors. Failed runs require inspection,
not an automatic paid retry. Interrupted/paused runs can resume from their saved state.

Analysis always includes **all 16,128 scheduled selections**, even when only one block
is supplied. Missing observations count as administrative invalids and are separately
identified; they are not described as observed model errors. Recorded invalid outputs
remain failures in accuracy. This execution freeze makes the conservative eligibility
rule explicit: a missing, tied, failed or nonfinite selection prevents inferential
eligibility. All descriptive counts and contrasts remain available. There is no
complete-case deletion or reconstruction of a successful sample.

Revoked-target and revoked-other categories are not applicable before updates or in
snapshots without history. Error-conditional shares use scheduled failures, including
explicitly marked missing cases; they are undefined in zero-error cells. Margins retain
their number of available and missing/invalid scores.

## Analysis and decision

For each world after both updates:

\[
E=q_{self,possessive}-q_{self,account},\qquad
F=A_{self,account}-A_{self,possessive},
\]
\[
S=F-(A_{other,account}-A_{other,possessive}).
\]

Each world receives equal weight. Nominal 95% percentile intervals use 10,000 paired
world draws with seed 1729. The same world resampling is used across E, F and S. Their
two-sided paired-world t tests use 47 degrees of freedom and the stated normal-mean
approximation; Holm adjustment includes all three hypotheses.

With fewer than 48 valid complete worlds, intervals and tests are withheld. Zero
variance gives an undefined raw p-value, not an invented standard error. A value of one
is used only as a labeled conservative Holm placeholder; an undefined test cannot
qualify. Point-mass bootstrap intervals in constant fixtures do not establish equivalence.

The joint E/F rule requires positive estimates, positive nominal lower bounds and
Holm-adjusted p-values at most 0.05, complete valid data and all lookup gates passing.
S must meet that same directional rule for the stronger own-versus-other specificity
candidate. A positive E/F result without S is reported without a specificity claim.
Synthetic software fixtures can never qualify as model evidence.

The report includes all aliases, checkpoints, event-order splits, owner-name comparisons,
world effects, categorical outcomes, margins, account/operator identity, answer position
and command diagnostics. It retains error budgets, all-success cells and the conditional
E bounds at fixed observed accuracies. F−E exposes the contrast in remaining errors.
Secondary comparisons do not replace a failed primary result. Lookup competence does
not establish dynamic update competence or authorize an internal intervention.

## Offline commands

Validate a block without model weights:

```bash
uv run --no-sync self-study validate configs/qwen-query-reference-00.json
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --no-sync self-study validate \
  configs/qwen-query-reference-00.json --tokenizer-check
```

The tokenizer check uses the local pinned cache. Configurations `00` through `05` select
disjoint fixed blocks. The freeze record pins every block's plan; changing time limits
within 1–5,400 seconds does not change the scientific configuration.

After separately authorized GPU execution, start or resume the same block directory:

```bash
uv run --no-sync self-study run configs/qwen-query-reference-00.json \
  --out runs/query-reference-00
```

This is a real model command, not an offline check. `--max-jobs` is an invocation limit,
not a way to shrink the fixed study or obtain a passing partial decision.

Analyze/export any block, including incomplete or failed work:

```bash
uv run --no-sync self-study analyze runs/query-reference-00
uv run --no-sync self-study export runs/query-reference-00 \
  --out exports/query-reference-00.tar.gz
```

Combine the fixed sample in a new output directory:

```bash
uv run --no-sync self-study analyze runs/query-reference-00 \
  --additional-runs runs/query-reference-01 runs/query-reference-02 \
    runs/query-reference-03 runs/query-reference-04 runs/query-reference-05 \
  --out review/query-reference-results
```

Duplicate/overlapping blocks and incompatible execution provenance are rejected.
Partial combinations retain the full-sample denominator and cannot pass. Per-block
archives include raw records, the journal, manifest, source snapshot, frozen inputs,
report, deterministic example and figures. Preserve all six archives beside a combined
report; the combined report does not replace raw evidence.

Five figures are generated from saved analysis as SVG, PDF and PNG: the actual task
diagram, E/F/S with intervals, alias/checkpoint performance, world effects and lookup
controls. Synthetic figures are labeled accordingly; incomplete figures say so and
do not invent intervals. `examples.md` always uses world 0000, assignment 0, after-both,
grant mapping 0, event order `[0,1]` and option rotation 0, for both owners/all aliases.
The example is fixed before responses, not selected for effect size.

## Hugging Face handover

The existing starter and worker explicitly support the six configurations and paused-run
continuation. Each configuration has a separate run prefix and receipt; selecting one
does not submit the remaining five. The worker uses the same checkpoint uploader and
private artifact repository as the existing studies. Cooperative runtime is 90 minutes;
the current starter's provider limit is two hours. These are limits, not a new price quote.

The first selected block has now completed, as documented in the execution update above.
Further blocks require their own current quote and explicit launch budget. This runbook
and the original software freeze do not allocate further spend.
An old completed job's budget is not reused. The fixed sample stays 48 worlds even if
execution is scheduled across multiple separately budgeted invocations.

## Verification

The new tests use synthetic records with separate fixture IDs. They exercise the
complete factorial sample, known positive and negative contrasts, exact zero-variance
cases, Holm placeholders, all-scheduled missingness, gates, pairing, atomic journal
recovery, interrupted runs, nonfinite/tied/malformed outputs, token drift, source/config
drift, deterministic exports and synthetic/model provenance separation.

A separate test compares native multi-token likelihood against full-sequence forwards
and independent log-softmax summation in a tiny randomly initialized Qwen model on a
software-only prompt. It uses no pretrained weights or assessment-world inference.
HF routing is tested with mocked services; no network submission occurs. The completed
verification commands/results are recorded in the execution verification JSON linked
from the protocol overview.
