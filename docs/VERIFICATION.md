# Implementation verification

Verified on 2026-11-06. Software tests and real-model evidence are identified separately below.

## Checks

- Current suite: **52 passed in 141.34 seconds**, including the original real-library CPU integrations, native-harness integration and seven cloud-adapter tests. All network mutations and paid job creation are mocked in these tests.
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
