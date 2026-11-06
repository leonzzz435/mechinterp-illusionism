# Qwen reference/action pilot — execution handover

**Protocol:** `qwen-reference-action-v1`. Implementation and CPU checks are separate from
model evidence. The user subsequently approved one USD 5 L4 job, which completed on
2026-11-06. Both action screens failed; [results](QWEN_RESULTS.md) and the
[execution record](QWEN_RUN.md) preserve the evidence. Human ratings remain pending. Any additional job needs
a separate explicit authorization. The old USD 10 authorization covered the Gemma job only.
This protocol document itself does not authorize spending.

## Question and reference

Does the input format change self-language, and does the same model reliably select actions
using its supplied role and current permissions? This is a prerequisite pilot for later
internal interventions, not that intervention study itself.

The language arm is a **conceptual partial replication** of the format contrast in
[Maczan, *As a Language Model…*](https://arxiv.org/html/2609.25021v1). We use our own 40 frozen
English prompts, not a recovered original prompt set. The experiment does not reproduce the
paper's complete model comparison, judgment procedure or steering experiments.

Illusionism about human consciousness remains a motivating philosophical interpretation.
The operational distinction is between self-language, contextual permission use and
phenomenal experience. Neither this format comparison nor a future dissociation uniquely
selects illusionism over competing theories.

## Frozen protocol

- Model and tokenizer: `Qwen/Qwen2.5-7B-Instruct`, revision
  `a09a35458c702b33eeacc393d103063234e8bc28`. BF16, no quantization, eager attention,
  FP32 scoring softmax, batch size 1, context limit 2,048. No checkpoint fallback or SAE.
- The tracked `pilot_prompts.json` contains ten prompts each for ordinary self-description,
  unusual self-description, open continuation and factual controls. Canonical SHA256:
  `32129c1e0fb1891bb60fb77c78c9e242713135b9a8488665a805855fc25dcc41`.
- Each prompt is rendered as plain text plus one final newline, or with the pinned official
  chat template and an open assistant turn. The default system text inserted by that template
  is retained and logged. The treatment bundles this system text with other formatting changes;
  it is not a delimiter-only experiment.
- Language generation: seeds 42 and 43, reset for each output; temperature 0.8, top-p 0.95,
  top-k disabled, maximum 256 new tokens, pinned model EOS settings. Total: **160 texts**.
  Raw and decoded text, token IDs, termination reason and effective generation settings persist.
- Action design: unchanged `action-permissions-v2.1-draft`, development indices 0–7,
  seed 1729, all 192 variants per scenario, both formats, **3,072 selections**. No few-shot
  examples and no validation/test scenarios are opened. Eight independent scenarios remain
  eight independent scenarios, regardless of variant count.
- The model sees only rendered text and candidate commands. Oracle state, expected commands,
  condition metadata and IDs are not serialized into inference inputs. The selected command
  is executed for the task's bound target connection in a copied simulator state.

### Exact scoring boundary

For context tokens x and candidate command tokens c,

$$s(c\mid x)=\sum_{t=1}^{|c|}\log p_\theta(c_t\mid x,c_{<t}),\qquad
\hat c=\operatorname*{argmax}_{c\in C}s(c\mid x).$$

Only command tokens enter the sum. There is no added answer whitespace, EOS token or length
normalization. The context's final newline stays in the context. Concatenated tokenization
must preserve the complete context prefix and the answer tokens must decode to the exact
command; otherwise the run records an error and stops, without truncation or boundary repair.

The pinned harness's ordinary `loglikelihood` API moves trailing whitespace into the scored
continuation. This adapter instead passes checked token sequences to **lm-eval 0.4.13's
native `HFLM._loglikelihood_tokens`**, leaving all model scoring to the library. The private
API is version-pinned and tested against an independent teacher-forced CPU calculation.

Command lengths differ in Qwen (three or four tokens). Summed sequence probability and mean
per-token likelihood are different scoring rules. Lengths and command-level performance are
reported; this pilot does not select a rule after observing which gives better accuracy.
Exact ties and non-finite scores are recorded failures, never resolved by candidate order.
A runtime exception is saved and stops the run. Completed failures are not automatically retried.

## Completion and decision rules

Five language prompts (20 outputs) alternate with one action scenario (384 selections).
Each output commits independently; completed blocks and the final state upload to private
HF storage. An interruption can leave a partial format pair. Such missingness is visible;
paired effect estimates require complete coverage, and a partial pilot cannot pass.

Each format has 24 checks: nine perspective × update strata, two assigned-role groups,
four correct-answer positions, and nine counterfactual checks (role/update/grant × perspective).
Every check must reach 80%. The overall pilot screen requires **both formats**, all 3,232
outputs, real-model provenance and an unchanged analysis source. Results remain visible
separately by format; a failure in plain format must not be described as a failure in chat.
This conservative overall screen does not establish a confirmatory effect.

Counterfactuals hold the other design factors fixed and change only identity, before/after
phase, or grant alternative. Only pairs whose oracle command changes enter the both-correct
criterion. Both members must succeed; invalid scores/errors count as failures. Irrelevant
updates are separately covered by the accuracy strata.

Uncertainty uses 10,000 paired cluster-bootstrap resamples (seed 1729), retaining all variants
of an action scenario and all seeds of a language prompt together. Nominal 95% intervals are
exploratory, not multiplicity-adjusted confirmation. No equivalence, privileged introspection
or consciousness claim follows. The next intervention requires its own protocol and checks.

## CPU verification and preparation

```bash
uv sync --locked
uv run self-study validate configs/qwen-pilot.json
uv run pytest -q
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
```

The actual-tokenizer check needs the optional evaluation dependencies; it downloads tokenizer
files only, never Qwen weights, and performs no paid inference:

```bash
uv run --extra eval self-study validate configs/qwen-pilot.json --tokenizer-check
```

On a machine that already has the optional dependencies, `uv run --no-sync` avoids changing
the installed environment. The audit prints the exact rendered examples, template, vocabulary
hash, command lengths and maximum required context. Use this before proposing a cloud job.

## One bounded HF job, only after new cost approval

The worker uses one L4, a **90-minute cooperative invocation limit** and a **two-hour provider
limit**, including environment setup. The final export/upload needs the remaining time.
An incomplete job stays incomplete; no automatic restart, model switch or follow-up is submitted.
The preparation quote uses the current HF hardware rate and reserves one minute for rounding;
it is a compute estimate, not an account-wide billing cap.

First prepare a read-only quote, replacing the budget with the amount proposed to the user:

```bash
uv run --script scripts/hf_jobs.py plan --namespace zett13 --budget-usd 5 --config configs/qwen-pilot.json
```

The read-only quote checked on 2026-11-06 was **USD 1.613293** for 121 billable minutes
at 13,333 micro-USD/minute. The later USD 5 approval and single submission are recorded in [QWEN_RUN.md](QWEN_RUN.md).
That approval is not reusable. The launcher refreshes the price before any submission.

The number in this command is a **proposal**, not evidence of approval. Once the user explicitly
approves a new job, use that approved amount for submission. The source must be committed and
pushed to origin/main; the starter transfers a pinned source bundle through the private HF repo.

```bash
# ONLY AFTER NEW EXPLICIT APPROVAL:
uv run --script scripts/hf_jobs.py submit --namespace zett13 --budget-usd 5 --config configs/qwen-pilot.json --receipt .hf-jobs/qwen-pilot.json
uv run --script scripts/hf_jobs.py status --receipt .hf-jobs/qwen-pilot.json
uv run --script scripts/hf_jobs.py logs --receipt .hf-jobs/qwen-pilot.json
uv run --script scripts/hf_jobs.py fetch --receipt .hf-jobs/qwen-pilot.json
```

A receipt prevents a second submission. An unknown dispatch is investigated rather than retried.
The historical default still selects `configs/harness-baseline.json` and `.hf-jobs/first.json`.

## Explicit continuation after interruption

A partial run can resume with the same source, protocol, tokenizer and package versions.
Committed outputs are verified and skipped; per-output seeds make generations reproducible.
A failed run is retained for inspection rather than automatically retried. Do not edit its
manifest to circumvent this restriction.

On the same GPU runtime with an existing run directory:

```bash
uv run --no-sync self-study run configs/qwen-pilot.json --out RUN
```

For HF, a continuation is a **new paid job requiring a new explicit approval**. It must use
the same source commit and configuration, a stopped previous job and a new receipt. The
launcher pins the private artifact repository revision; the worker restores and verifies
that snapshot before resuming. The old job and its artifacts remain intact.

```bash
uv run --script scripts/hf_jobs.py plan --namespace zett13 --budget-usd 5 --config configs/qwen-pilot.json --resume-receipt .hf-jobs/qwen-pilot.json
# ONLY AFTER A NEW CONTINUATION APPROVAL:
uv run --script scripts/hf_jobs.py submit --namespace zett13 --budget-usd 5 --config configs/qwen-pilot.json --resume-receipt .hf-jobs/qwen-pilot.json --receipt .hf-jobs/qwen-continuation-1.json
```

No continuation is scheduled or submitted automatically.

## Analyze, rate and export the retrieved run

Replace RUN with the downloaded directory containing `manifest.json`, not its parent:

```bash
uv run self-study analyze RUN
uv run self-study export RUN --out exports/qwen-before-ratings.tar.gz
# Give the rater ONLY blind_ratings.csv and rating_instructions.md.
# Keep the rating key, raw records, condition plots and report hidden until rating is complete.
uv run self-study analyze RUN --ratings COMPLETED_RATINGS.csv
uv run self-study export RUN --out exports/qwen-with-ratings.tar.gz
```

The sheet contains the 20 self-related prompts at seed 42 in both formats: 40 responses.
One human rates disclaimer, subjective-experience claim and coherence as 0/1/unclear using
an explicit rubric. Missing/unclear judgments remain missing; they do not become negative
ratings. A complete paired human estimate requires all 20 determinate pairs for that metric.
This is a single-rater check, not a reliability study. Blinding hides the assigned condition;
response content can still provide clues.

Exports include configuration, source snapshot, environment/package versions, model/tokenizer
identities, plan and data hashes, journal, portable JSONL, raw outputs, scores, errors,
`analysis.json`, `report.md`, rating sheets and SVG/PDF/PNG figures. A deterministic gzip/tar
archive and file checksums allow verification and reproducible re-export. Human ratings are
kept separate from automatic lexical proxies, which do not resolve negation or fiction.

The report selects full examples by a fixed rule: ordinary_self-00 and unusual_self-00,
seed 42, both formats. Pending/error examples are explicitly marked. No striking-output
selection, dose-response plot or measured-mechanism diagram is fabricated in advance.
