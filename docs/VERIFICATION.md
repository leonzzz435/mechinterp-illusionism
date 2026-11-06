# Implementation verification

Verified locally on 2026-11-06. This is software evidence, not a Gemma experiment.

## Checks

- Final full suite: **41 passed in 190.38 seconds**, including four real-library CPU integration tests.
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

No new Gemma outputs, GPU memory measurements, empirical effect sizes or human ratings are available. HF/TransformerLens parity, SAE reconstruction quality, actual task accuracy and runtime must pass on Blackwell. The first empirical deliverable is the historical reference export followed by the bounded feasibility and capability checks. Full validation, held-out confirmation and publication remain pending.
