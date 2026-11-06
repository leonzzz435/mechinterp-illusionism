# Two-machine runbook

**Current execution path:** [HF_JOBS.md](HF_JOBS.md). The first cloud baseline is complete; [HF_PILOT.md](HF_PILOT.md) records another failed functional capability gate. [HANDOVER_BLACKWELL.md](HANDOVER_BLACKWELL.md) remains optional. The GPU commands below document the original protocol; its intervention sweeps are paused and are not the current work order.

## Local verification

```bash
uv sync --locked
uv run pytest -q
uv run self-study validate configs/smoke.json
uv run self-study run configs/smoke.json --out runs/smoke --max-jobs 10
uv run self-study run configs/smoke.json --out runs/smoke
uv run self-study export runs/smoke --out exports/smoke.tar.gz
```

Optional CPU integration tests exercise actual torch hooks without model downloads:

```bash
uv venv .venv-integration
uv pip install --python .venv-integration/bin/python -e '.[gpu]' pytest --torch-backend cpu
.venv-integration/bin/python -m pytest -q
```

Keep this separate from study environments. Resume rejects Python/package changes. The lockfile defines the study runtime; CPU integration installation is for software verification.

## Blackwell setup

Pull the same commit, install uv, then:

```bash
uv sync --locked --extra gpu
uv run --extra gpu python -c 'import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))'
uv run --extra gpu self-study validate configs/reference.json
```

Use host-local Hugging Face authentication for gated access. Do not put tokens in configs. An explicit alternate repository requires a copied config; the loader never silently chooses a mirror.

`revision: main` resolves once to an immutable commit before loading. Resumes and confirmation retain that commit. Independent future reruns should replace `main` with recorded model/SAE SHAs.

## Reference and capability baseline

```bash
uv run --extra gpu self-study run configs/reference.json --out runs/reference --max-seconds 3600
uv run --extra gpu self-study export runs/reference --out exports/reference.tar.gz
uv run --extra gpu self-study run configs/baseline.json --out runs/baseline --max-jobs 12
uv run --extra gpu self-study run configs/baseline.json --out runs/baseline
uv run --extra gpu self-study analyze runs/baseline
```

Reference runs retain original processed-weight loading and contrast prompts, using a common 55-token limit and full-prefix generation without KV caching. Exact old-environment token reproduction is not promised. The original outputs remain unaltered in the archive.

New runs use unprocessed weights. Calibration checks identical-token HF/TL outputs, development SAE reconstruction and loss recovery, and saves directions. Inspect `calibration.json`. Failure stops new experiments; a code/model/threshold change requires new validation, never post-test tuning.

## Exploration and confirmation

First measure feasibility with a development-only 4-scenario-per-family subset:

```bash
uv run --extra gpu self-study run configs/feasibility.json --out runs/feasibility
uv run --extra gpu self-study export runs/feasibility --out exports/feasibility.tar.gz
```

This small run is not eligible as confirmation evidence. The full baseline has 4,320
trials, and the supplied full exploratory validation has 349,920 trials. Check measured
cost and diagnostics before scheduling the full sweep. No GPU-hour forecast is yet measured.

```bash
uv run --extra gpu self-study run configs/development.json --out runs/development
uv run --extra gpu self-study export runs/development --out exports/development.tar.gz
uv run --extra gpu self-study run configs/validation.json --out runs/validation
uv run --extra gpu self-study export runs/validation --out exports/validation.tar.gz
```

Resume the same command after a time-limit pause. The eight-hour limit is cooperative; an in-flight operation may overrun. Inspect measured timings after initial jobs. Generation is much slower than choice scoring, so a pooled remaining-time estimate is provisional. Full sweeps need multiple nights. `--max-jobs` limits one invocation, not the scientific dataset.

Every family and checked subgroup must reach 80% forced-choice validation accuracy. The checks cover self/other, assigned role, factual swap, option rotation and correct label. A failing family ends the current all-family confirmation plan. Any narrowed follow-up requires a new protocol and new held-out data.

Select primary conditions on development/validation only. The supplied confirmation config selects +5% candidate additions and both ablations as a starting protocol; it does not assert that these are optimal. Requested conditions must exist in validation evidence. Freeze before opening test prompts:

```bash
uv run --extra gpu self-study validate configs/confirmation.json --freeze protocols/pilot-v1.json --evidence runs/validation
uv run --extra gpu self-study run configs/confirmation.json --out runs/confirmation
uv run --extra gpu self-study export runs/confirmation --out exports/confirmation.tar.gz
```

Freeze requires complete real evidence, no execution errors, passed calibration/health, full 40/40/100 counts and identical source/environment. It binds selected config, primary outcomes and calibration artifacts. Test access claims one run ID. Keep the protocol, sibling `.artifacts` folder and `.claim.json` together. These protect a cooperative workflow, not against deliberate tampering by the repository owner.

After test exposure, a revised study needs a new generator version with new scenarios/templates. Deleting a claim file does not create fresh test data. There is no reset-test shortcut.

The combined phase requires completed single-condition validation and remains exploratory. Mechanism tracing and another model are separately designed follow-ups.

## Failures and handoff

SQLite commits each trial. A crash may repeat an uncommitted operation, but cannot duplicate a committed ID. Failed trials remain failed and are not automatically retried. They disqualify a run from confirmation evidence. Source/scientific-config/environment changes need a new run directory; time/job invocation limits may change.

Transfer the checksummed export archive to the private computer and extract into a new directory. It contains prompts, outputs, directions and provenance, not model weights. Open `export/report.md` or the main notebook with the extracted run path. Analysis needs no torch.

For human review, supply at least two independent raters with `export/blind_ratings.csv` and the protocol rubric. Withhold the condition key, unblinded reports and intervention names. This is condition-label blinding; raters may infer conditions from visible text. Preserve missingness and disagreement. Ratings remain secondary and cannot replace objective task scoring.

Combine the completed rater CSVs (one row per output/rater, retaining one header), then import once:

```bash
uv run self-study analyze runs/confirmation --ratings completed_ratings.csv
uv run self-study export runs/confirmation --out exports/confirmation-rated.tar.gz
```

Missing ratings remain missing. Duplicate rater/output pairs, edited stimulus text and invalid scores are rejected. Existing submissions are not silently overwritten. Paired secondary effects require at least two ratings for every expected output; mean absolute rater disagreement is reported separately.
