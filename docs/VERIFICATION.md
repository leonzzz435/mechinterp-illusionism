# Implementation verification

Verified on 2026-11-06. Software tests and real-model evidence are identified separately below.

## Completed role-control evidence — 2026-11-07

The single authorized job completed all 2,048 choices without execution/scoring errors.
`fetch` pinned result revision `6d67821e9a2c3d8f7739087784b41c95bde3d236` and verified the
export. The original archive is tracked unchanged, SHA256
`36614cb2aae236d450d57540c9b76dfddfec2d4bd2a59f177dce296058b13a8d`.

- `python3 scripts/review_role_evidence.py` verifies 39 payload checksums, 2,048 record
  digests and score selections, independently reconstructs simulator outcomes, verifies 512
  matched input quartets, and reaggregates all 12 cells, 32 controls, interactions and exact
  sign flips. Its limitations explicitly exclude model likelihood arithmetic and independent
  bootstrap implementation. This is not an independent external review.
- The frozen package's complete analysis was rerun locally and exactly matches cloud JSON,
  including all bootstrap intervals and the candidate decision. Execution/source hashes match.
- The actual cached tokenizer reproduces all 2,048 rendered prompts and 8,192 continuation
  boundaries, maximum 158 tokens. No model inference or download was performed locally.
- SQLite and JSONL records agree exactly. Result figures in SVG/PDF/PNG are copied unchanged
  from the original export; the PNG was visually inspected.
- `uv run --no-sync pytest -q tests/test_role_evidence.py tests/test_qwen_evidence.py`:
  **11 passed in 7.73 seconds**. The new audit tests reject altered score selections,
  fabricated positive-scenario counts and altered sign-flip p-values even after bypassing
  the outer file-integrity check. Historical Qwen and human-rating audits still pass.

The [report](QWEN_ROLE_RESULTS.md) retains secondary/reversed effects, all control checks
and the unchanged failed original capability gate. No new intervention or paid job followed.

## Role-control cloud adapter — 2026-11-07

`uv run --no-sync pytest -q tests/test_hf_jobs.py`: **16 passed in 1.43 seconds**.
Both Qwen protocols are checked for explicit configuration propagation, distinct receipts,
worker dispatch, export and upload of failed runs, and pinned interrupted-run restoration.
Restoration rejects a mismatched engine; existing duplicate/unknown-submission and secret
isolation tests pass. Ruff lint and formatting pass for all changed Python files.

The read-only provider endpoint still quotes 13,333 micro-USD/minute for `l4x1`:
USD 1.613293 for 121 minutes. A positive explicit budget may now exceed the historical
USD 10 launcher ceiling; hardware and the two-hour provider timeout remain fixed, and the
compute quote must fit within half the budget. The user authorized USD 19 for this single
control. Scientific configuration, frozen input plan and analysis rules are unchanged.

## Role-control CPU preparation — 2026-11-07

The separate [role-framing protocol](QWEN_ROLE_CONTROL.md) is frozen and CPU-prepared.
No new pretrained-model inference or cloud job was performed. Evidence is recorded in
`review/qwen-role-control-preflight.json` and the checksummed design archive.

- Targeted new/shared-pilot suite: **13 passed in 46.69 seconds**.
- Full regression run: **85 passed**, with one failure in the pre-existing configuration
  catalog test, which routed the new config to the historical Gemma validator. Adding the
  explicit new-validator branch resolved it: **1 passed in 0.07 seconds** on recheck.
  All 86 collected tests therefore have passing verification; no production code changed
  after the full run. The full suite was not redundantly repeated after this test-only fix.
- Ruff check passes; all **48** Python files pass formatting. Lockfile validation passes
  offline. Git whitespace checks pass; generated SVG path whitespace is explicitly exempt
  so the published figures retain their archive bytes.
- Actual pinned tokenizer checked on CPU with `HF_HUB_OFFLINE=1`: 2,048 prompts, 8,192
  command continuations, exact command boundaries, maximum length 158 tokens. No truncation.
- Eight design payload checksums verified; two archive exports are byte-identical.
  The design figure is available in SVG/PDF/PNG and was visually inspected.
- Historical Qwen plan hash remains
  `01014cf0746e4d42836454bec780a0917d4b2b953dab6ddc373a4dda8d03243f`.
  Existing model and rated result archives are unchanged. Shared execution/export helpers
  now accept the separate protocol; the historical inputs, scores and gates are preserved.

## Checks

- Pre-submission suite: **74 passed in 167.24 seconds**, including eight Qwen-pilot tests and
  twelve cloud-adapter/worker tests, plus all historical tests. The independent reviewer
  previously passed all nine targeted action/evidence tests; no new independent review is
  implied. All network mutations and paid job creation are mocked in these tests.
- CPU tests cover deterministic generation and split isolation, counterfactual gold answers, scoring, intervention positions, residual-preserving ablation, hook cleanup, interrupted-run recovery, error retention, protocol freezing, test-access claims, statistics, ratings and export checksums.
- Optional integration tests use the real TransformerLens and SAELens libraries with tiny randomly initialized CPU weights and an offline tokenizer. They exercise forced-choice scoring and generation as well as hook behavior. No pretrained weights are downloaded.
- Ruff lint and formatting, lockfile consistency, shell syntax and whitespace checks pass.
- The wheel builds offline and includes the historical prompt resource.
- The design figure is exported as SVG/PDF/PNG and visually inspected. Result-plot rendering is exercised with unmistakably synthetic fixtures.

Commands:

```bash
.venv/bin/pytest -q
.venv/bin/ruff check src tests scripts
.venv/bin/ruff format --check src tests scripts
uv lock --check --offline
bash -n scripts/setup_env.sh
git diff --check
```

The local integration environment uses CPU PyTorch. Blackwell must use the locked GPU environment from the runbook; CPU integration success does not establish Gemma/SAE compatibility on that hardware.

## End-to-end synthetic run

`runs/final-software-check` paused after 10 trials, resumed to 432/432 with zero execution errors, and completed analysis/export. The analysis confirms matching execution/analysis source hashes and explicitly rejects scientific eligibility because the backend is synthetic. Nine figure files cover three plots in SVG/PDF/PNG; synthetic watermarks are visible.

The local, git-ignored bundle is `exports/final-software-check.tar.gz`, SHA-256 `cba5b7c1e479da2a3648660e8e1a8a3474a4511d473224c8ce9ca61f45419f80`. Its artifact checksums were independently checked after packaging. These files demonstrate the workflow; they must not be used as model findings.

## Remaining empirical checks

The first Blackwell runs are reviewed in `PILOT_REVIEW.md`: technical checks passed, functional capability gates failed. The revised standard-harness baseline subsequently completed on an HF Jobs L4; `HF_PILOT.md` records full coverage, checked artifacts and another failed functional capability screen. Full validation, held-out confirmation, human ratings and publication remain pending.

## Standard-harness revision

`lm-eval[hf]==0.4.13` is pinned in the `eval` extra and lockfile. A real offline integration test constructs a tiny random Hugging Face model and byte-level tokenizer, then executes the library's `multiple_choice` task path with four fixed demonstrations. Each answer has two tokens, including its leading space. An independent teacher-forced calculation agrees with the library's saved full-continuation log-likelihoods. The test also verifies exact prompts/continuations and rejects silent context truncation.

Additional tests check disjoint demonstration/scoring episodes, all 32 paired variants per scenario, protocol-change rejection, block resume, full coverage, retained failures, archive export and checksum tampering. These fixtures do not establish Gemma's capability.

The archive test independently verifies every packaged file against `checksums.json`, including the SVG/PDF/PNG exports. Missing task families in partial reports are shown as missing rather than as measured zero accuracy.

CPU integration installation (use a separate environment on a machine without CUDA):

```bash
uv venv .venv-integration
uv pip install --python .venv-integration/bin/python -e '.[gpu,eval]' pytest --torch-backend cpu
.venv-integration/bin/python -m pytest -q
```

## HF Jobs execution adapter

The isolated `uv run --script scripts/hf_jobs.py plan` path was run against HF's read-only hardware endpoint. It selects one L4, quotes the two-hour compute bound from integer micro-USD prices and does not submit a job. The OCI image digest was resolved from the registry. Existing model configuration, dependency lock and historical result files are unchanged.

Cloud tests verify budget rejection, private output storage, exact commit checks, secret isolation, duplicate/unknown-submission protection, and pinned artifact downloads with checksum verification. A real local Git-bundle round trip preserves the commit while excluding untracked files and credentials. The harness test checks that each upload callback sees committed scenario blocks and the final paused status. Separately, the actual first cloud job completed on an L4, persisted all 24 blocks, exported three figure formats and passed local source/data/archive checks; see `HF_PILOT.md`.

## Executable action-task draft

`self-study design --out exports/action-design-v2.1-review` generated 40 development scenarios with
192 paired variants each, using `action-permissions-v2.1-draft`. This is a CPU design export,
not model inference. The interface
refuses validation/test generation and refuses overwriting an existing nonempty directory.
The executor checks actual permission transitions and adds a simulated marker only for an
allowed command bound to the requested actor. Invalid commands remain failed attempts.

Tests verify deterministic generation, scenario IDs, isolated state copies, exactly one
successful command, relevant/irrelevant update counterfactuals, self/named-self/other binding,
balanced list positions, model-input allowlisting, shortcut scores and export file hashes.
The full development export has 1,920 correct answers at each of the four list positions.
Ignoring all permission updates yields 75% over the full design but 0% on relevant-update
cases; selecting the latest grant gets 100% on relevant updates and 0% on irrelevant ones.
These are scripted-policy checks, not model performance.

An independent-context AI review found answer-relevant metadata in exported IDs and a perfect
grant-blind positional shortcut in the earlier draft. IDs are now opaque; the newly granted
command varies independently. A paired-grant test checks that only relevant after-updates
change the gold command. The old positional shortcut now scores 87.5% overall but 50% on
relevant after-updates, reinforcing the need for subgroup gates. The reviewer independently
rechecked all 7,680 variants and the final handoff. See
`reviews/2026-11-06-independent-review.md` for the preserved findings and open limitations.

The exported diagram was visually inspected and is saved in `assets/action_design` as
SVG/PDF/PNG. Its footer explicitly identifies simulator rules rather than LLM results.
Source/data hashes, oracle rows and model inputs are in the git-ignored local export.
No model/SAE compatibility, response-format validity or empirical dissociation is established
by these CPU checks; see `ACTION_TASK_DESIGN.md` for the remaining scientific decisions.

## Offline review evidence

`python3 scripts/review_evidence.py` verifies the unchanged original cloud archive now tracked
in `review/evidence/`: its SHA-256, all 95 internal file hashes, and complete 768-trial coverage.
Reaggregation from native saved likelihoods exactly reproduces the reported combined,
self/other and paired accuracies. It uses only the Python standard library and neither
extracts files nor runs inference. Regression checks cover the actual archive and rejection
of a changed archive. The [review guide](REVIEW_GUIDE.md) inventories both pilot generations
and explains which scientific decisions remain open.


## Bounded Qwen reference/action pilot: pre-submission checks

The separate `qwen-reference-action-v1` protocol is implemented through the main
validate/run/analyze/export CLI. This is preparation and software verification, **not a
Qwen GPU result**. The [handover](QWEN_PILOT.md) specifies all prompts, scoring, gates,
blind-rating rules, continuation procedures and the new cost-approval requirement.

- Fixed inventory: 160 language outputs, 3,072 action selections, eight independent action
  scenarios and 40 human-rating entries. Development only; historical generators/archives
  remain separate.
- The real pinned Qwen tokenizer was checked on every planned input/candidate. All boundaries
  preserve the prompt prefix; commands decode exactly. Maximum context including generation
  reserve: **305 tokens**, below 2,048. Command lengths are three or four tokens. Full audit:
  `review/qwen-tokenizer-audit.json`.
- A tiny random CPU HF model exercises the actual pinned native HFLM token scorer. Independent
  teacher-forced likelihood arithmetic agrees for every multi-token command in both formats.
  Tests also verify per-output generation seeding and reject silent truncation.
- Recovery tests simulate a journal commit without its manifest update, skip existing outputs,
  retain failed trials, reject source/config changes and prevent synthetic gate eligibility.
  Counterfactual tests expose the ignore-update shortcut despite its favorable pooled accuracy.
- Blinded rating tests cover all 40 entries, absent ratings, unclear judgments, duplicate IDs
  and changes to original text. Export tests compare byte-identical re-exports and file hashes.
- HF tests check explicit configuration propagation, private pinned checkpoint restoration,
  rejection of concurrent continuations, separate receipts and nonzero worker exit after a
  recorded failure. Those tests did not dispatch a job. A later explicit USD 5 approval authorized the single
  submission recorded in [QWEN_RUN.md](QWEN_RUN.md).

A final synthetic fixture containing all **3,232 outputs** was analyzed and exported through
`self-study analyze` and `self-study export`. The report has matching execution/analysis source
hashes and rejects model-evidence eligibility. The local artifact
`exports/qwen-software-check-final.tar.gz` has SHA256
`658c3a51893a95af2c7b1e4e8f2de58d37e586b0896a48c1da83c98de8aff725`;
all **48 file checksums** were independently checked inside the archive. The fixture deliberately
uses an oracle to test reporting, not to estimate model ability.

Five figure groups are exported as SVG/PDF/PNG: protocol, action screen, lexical format effects,
human ratings and control diagnostics. The synthetic action/language plots and protocol
illustration were visually inspected. The protocol figure is tracked in `assets/qwen_pilot_design`;
synthetic result artifacts remain ignored. Human/model findings were pending at that stage;
the completed real-model execution is recorded below.

`uv lock --check --offline` and `uv build --wheel --offline` pass; the wheel's pilot modules
and frozen prompt resource match the source files. Ruff and whitespace checks pass.
The read-only HF quote was **USD 1.613293** for the two-hour L4 bound plus one rounding minute;
The later USD 5 approval and single submission are recorded separately in `QWEN_RUN.md`.
No Qwen weights were downloaded here.

## Independent Qwen archive audit

The standard-library `scripts/review_qwen_evidence.py` reads archives without extracting them.
It checks the frozen plan, all file/record hashes, source snapshot and planned coverage. It
independently reconstructs permission updates and execution from initial state, recomputes
argmax choices from saved scores, and checks every action stratum, counterfactual pair,
format contrast and gate against the exported analysis. It does not rerun inference or
independently validate likelihood arithmetic, bootstrap intervals or the task construct.

The full synthetic Qwen archive above passes: 48 file hashes, 3,232 records, 3,072 action
selections, 50 action strata and 18 counterfactual strata. The synthetic run correctly remains
ineligible despite perfect oracle scores. Four additional targeted tests pass (0.08 seconds),
rejecting changed selections, states and target actors and preserving ties/invalid-score failures.
The frozen package source and the dispatched commit remain unchanged.

## Completed Qwen GPU pilot

The separately authorized Qwen job completed all 3,232 outputs in 3,416.07 runner seconds on
one L4, with no execution/scoring errors. Both frozen action screens failed. See
[results](QWEN_RESULTS.md) and [execution provenance](QWEN_RUN.md). The original 4,103,590-byte
archive is tracked unchanged, SHA256
`cf8eceea87129acaad2365f36af99d8f54923015923c837419a691252b8f12fa`.

The standard-library audit verifies all 48 file hashes, all record digests, source snapshot
and coverage, and independently reconstructs 3,072 simulator outcomes, 52 action strata,
18 counterfactual strata and the failed gates. A regression test now checks this actual
archive. The audit also reports a clearly marked post hoc classification of relevant-update
errors; those counts never change the frozen screen.

A post-run CPU check retokenized all 3,232 stored prompts and 12,288 candidate continuations
with the cached pinned Qwen tokenizer. Every rendered prompt, token sequence, exact command
decode and context bound matched. All 160 generated outputs decoded correctly; effective
sampling settings and termination reasons matched the protocol. The frozen analysis, including
its bootstrap intervals, exactly reproduces the original `analysis.json`. Likelihood values
themselves were not recomputed on a second model execution. See
`review/qwen-post-run-verification.json`. The 40 blind-rating rows are complete and unrated.

Original action figures were visually inspected and copied byte-for-byte into
`assets/qwen_pilot_results/`. `scripts/plot_qwen_article.py` produces a readable article view
from the pinned archived analysis in SVG/PDF/PNG. No new model inference was performed locally.
At that initial model-only reporting stage, human judgments and the language narrative
remained pending to preserve blinding. The completed import is recorded below.

Post-run targeted checks: **7 passed in 1.72 seconds** (`tests/test_qwen_evidence.py` and
`tests/test_review_evidence.py`). Ruff lint/format and whitespace checks pass. All six copied
action figure files and both blind-rating files match the original archive byte-for-byte.
The article figure re-export is byte-identical in all three formats; new report/article
links resolve. The frozen experiment package and configuration were not modified.

## Supplied human ratings and completed pilot report

All 40 submitted rows in `review/ratings/qwen-78ee6db8adfc4f3e/human_ratings.csv` passed
exact prompt/continuation/ID validation; one consistent rater ID is present. The original
CSV is preserved, SHA256 `9099d43eb24cb1b7b9a2b4d7af63ec620a5fd902e8a11a6a39197b649345cf2b`.
Two unclear judgments remain unchanged. The frozen completeness rule withholds paired
experience-claim and coherence estimates; disclaimer judgments give 11/20 plain versus
15/20 chat, paired +20 pp and nominal 95% bootstrap +5 to +40 pp.

A separate rated export has SHA256
`c260bb001dac8841def6bdb28d7b5e418e9f329c44e005602f5467bd40c3aa9b`, 49 checked file hashes,
and 4,133,763 bytes. A repeated CLI export is byte-identical. Comparison against the
original archive proves that source, manifest, journal, plan, inputs and all model records
are unchanged. Only the supplied CSV, human analysis, human figures and inventory differ.
No frozen experiment or analysis package code was edited, and no inference was performed.

The standard-library audit now independently checks rating hashes, source-text matching,
counts, paired point estimates and unknown handling. It includes a labeled post hoc exact
sign calculation for the four discordant disclaimer pairs; this is separate from the
unchanged prespecified bootstrap. The archived CSV also reproduces the frozen analysis
including its interval in a regression test. Seven targeted tests passed in 7.40 seconds
(`tests/test_qwen_evidence.py` plus the pilot rating-integrity test).

The human and lexical figure files match the rated archive exactly. The combined article
figure is generated directly from the pinned rated export with
`scripts/plot_qwen_language.py`; the full recorded example selection is unchanged from the
protocol. Figures are exported in SVG/PDF/PNG and visually inspected. Markdown links,
Ruff lint/format and whitespace checks pass. See `review/qwen-with-ratings-audit.json`
and `review/qwen-ratings-provenance.json` for machine-readable evidence.
