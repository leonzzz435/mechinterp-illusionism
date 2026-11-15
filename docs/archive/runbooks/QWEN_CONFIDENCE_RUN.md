# Qwen confidence pilot: execution record

**V2 completed all 1,792 selections; its behavioral candidate rule failed.**
See the [results, mathematics and figures](QWEN_CONFIDENCE_RESULTS.md).
V1 ended with a retained calibration tie; no assessment data were collected in that run.
The [v2 amendment](QWEN_CONFIDENCE_V2.md) defines the reviewed replacement under the same
total USD 5 cap. V1's raw data and decision are not revised.

## V2 dispatch

- Job [`6af060e70e0338d1bb84b03c`](https://huggingface.co/jobs/zett13/6af060e70e0338d1bb84b03c),
  created 2026-11-08 11:45:43 UTC; final provider status `COMPLETED`. Separate receipt and
  fresh calibration stage.
- Pushed source commit `0d0670fe542f0a7148aa15c4afeeddb67d16267c`; clean working tree at dispatch.
- Run folder `qwen-confidence-v2-4ea43316ce714c03`;
  [credential-free receipt](../review/qwen-confidence-v2-job.json).
- Configuration SHA256 `9974c8cd5094aec09996892d691c7b47698afc6c2b2f5632b02a2c1b0a1e7425`.
- L4, 90-minute cooperative limit, two-hour provider limit. Its USD 1.613293 maximum
  compute quote plus the entire reserved v1 quote totals USD 3.226586 within the USD 5 cap.
  These are compute bounds, not invoiced spend. No automatic third job follows.

The [v2 preflight](../review/qwen-confidence-v2-preflight.json) and amendment were committed
before dispatch. Only exact-tie selection and its reporting change; the original model,
question sample and hypotheses remain frozen.

The model invocation took **366.10 seconds**, including loading/checkpoints, with peak
allocated GPU memory 15,703,265,792 bytes. Provider setup and final report/upload time are
additional; this is not an invoice. All 1,792 selections completed without failed or invalid
scores; 39 exact ties were retained under the v2 rule. No third job was launched.

Retrieved private artifact revision `f7b3929fa4788a9ca5386654222ca7fc087ae0f6`.
The unchanged 3,340,358-byte [archive](../review/evidence/qwen-confidence-v2-4ea43316ce714c03.tar.gz)
has SHA256 `ba8b0d01d31da9004758abacd054fbdf664ed235834bc5e7889ab5e3d6cb97dd`.
All 61 payload checksums pass. The [score/statistics audit](../review/qwen-confidence-audit.json)
and [archived-source verification](../review/qwen-confidence-verification.json) agree with
the cloud report; all nine original figures reproduce byte-for-byte.

Offline reproduction from Git (no HF account, model weights or inference charges):

```bash
uv run --no-sync python scripts/review_confidence_evidence.py \
  review/evidence/qwen-confidence-v2-4ea43316ce714c03.tar.gz \
  --sha256 ba8b0d01d31da9004758abacd054fbdf664ed235834bc5e7889ab5e3d6cb97dd
# Requires eval extras and the pinned tokenizer already in the local cache.
uv run --no-sync python scripts/verify_confidence_run.py \
  review/evidence/qwen-confidence-v2-4ea43316ce714c03.tar.gz \
  --sha256 ba8b0d01d31da9004758abacd054fbdf664ed235834bc5e7889ab5e3d6cb97dd
uv run --no-sync python scripts/plot_qwen_confidence.py \
  review/evidence/qwen-confidence-v2-4ea43316ce714c03.tar.gz \
  --sha256 ba8b0d01d31da9004758abacd054fbdf664ed235834bc5e7889ab5e3d6cb97dd
```

The first script imports no study-package code. The second uses the checksum-verified
archived source, rechecks every actual token boundary and recomputes the full analysis.
The raw score values are not recomputed with a second pretrained model execution.

## V1 dispatch and outcome

- Job [`6af05c9de6320c66fad74947`](https://huggingface.co/jobs/zett13/6af05c9de6320c66fad74947),
  created 2026-11-08 11:27:25 UTC; final provider status `ERROR`, study status `failed`.
- Pushed source commit `491cf64dbe34b41472968149dcb00547780c12bc`.
- Run folder `qwen-confidence-3ec0b47c7d324b58`; 32/1,792 selections: 31 valid, one tied.
  All 32 are calibration selections; none is an assessment question.
- Model invocation 117.47 seconds, peak allocated GPU memory 15,440,193,024 bytes.
- Retrieved private dataset revision `a2b7db41c2dfef9a95aa9001d09fb8815e428041`;
  export checksums verified. [Job receipt](../review/qwen-confidence-job.json) and
  [immutable original archive](../review/evidence/qwen-confidence-3ec0b47c7d324b58.tar.gz).

The equal top scores were retained; v1 did not invent an answer or proceed to its dependent
confidence prompt. This is a measurement-policy failure, not a negative result on the main
scientific question. The source, evidence and failed decision remain reviewable.

The user authorized implementation and the bounded pilot on 2026-11-08
(“ja go is alles freigegeben”). The selected scope is one L4 job, no automatic continuation,
90 minutes cooperative execution and a two-hour provider limit. A separate **USD 5 budget**
was set for this milestone. After inspecting v1, one versioned replacement was allocated
within that same cap; see the amendment for the conservative arithmetic.

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
