# Implementation verification

Verified on 2026-11-06. Software tests and real-model evidence are identified separately below.

## Checks

- Current suite: **74 passed in 167.24 seconds**, including eight Qwen-pilot tests and
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


## Bounded Qwen reference/action pilot

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
  recorded failure. No real new cloud dispatch occurred.

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
synthetic result artifacts remain ignored. Human/model findings are pending.

`uv lock --check --offline` and `uv build --wheel --offline` pass; the wheel's pilot modules
and frozen prompt resource match the source files. Ruff and whitespace checks pass.
The read-only HF quote was **USD 1.613293** for the two-hour L4 bound plus one rounding minute;
USD 5 is a proposed per-job budget, not an authorization. No Qwen weights were downloaded here.
