# Self-language and contextual self-models

Can a language model's self-referential language and its use of a contextual self-model be influenced differently by causal interventions?

We distinguish **self-language**, **functional self-models**, and **phenomenal consciousness**. The experiments address the first two; they do not settle the third.

**Status:** research pipeline implemented; new Gemma pilot findings await execution on Blackwell. Historical outputs are exploratory examples, not evidence of independent consciousness circuits. CPU smoke outputs are explicitly synthetic.

- [Protocol and mathematics](docs/PROTOCOL.md)
- [Two-machine runbook](docs/RUNBOOK.md)
- [English article draft](docs/article/ARTICLE.md)
- [Sources and claim boundaries](docs/SOURCES_AND_CONTEXT.md)
- [Implementation and empirical milestones](PLAN.md)
- [Software verification and remaining empirical checks](docs/VERIFICATION.md)
- [Historical notebook](archive/historical_essay.ipynb), with original outputs and interpretations

## Private computer: install and verify

Python 3.10–3.12 and `uv` are supported. These commands do not download model weights:

```bash
uv sync --locked
uv run self-study validate configs/smoke.json
uv run self-study run configs/smoke.json --out runs/smoke
uv run self-study analyze runs/smoke
uv run self-study export runs/smoke --out exports/smoke.tar.gz
uv run pytest -q
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
```

Smoke outputs are **not scientific results**, cannot unlock confirmation, and carry a watermark. Optional torch integration tests skip when torch is absent; see the runbook for CPU installation.

## Blackwell computer: first real run

```bash
uv sync --locked --extra gpu
uv run --extra gpu self-study validate configs/reference.json
uv run --extra gpu self-study run configs/reference.json --out runs/reference --max-seconds 3600
uv run --extra gpu self-study export runs/reference --out exports/reference.tar.gz
```

The default model is `google/gemma-2-2b`. Accept its access conditions and authenticate locally if required. Tokens are never recorded in manifests. A mirror must be explicitly configured; there is no automatic fallback or assumption of weight identity.

Next run baseline, development and validation experiments as described in the runbook. Invocations are limited to eight hours and resume at trial boundaries. The limit is cooperative: an in-flight operation may finish after the deadline. Loading and calibration count against it.

## Interfaces and artifacts

```text
self-study validate CONFIG [--freeze PROTOCOL.json --evidence VALIDATION_RUN]
self-study run CONFIG --out RUN [--max-jobs N] [--max-seconds N]
self-study analyze RUN [--ratings CSV]
self-study export RUN --out ARCHIVE.tar.gz
```

Strict JSON defaults live in `src/self_model_study/config.py`. Validation reports job counts without loading models. Ordinary validation does not materialize test prompts.

Runs record configuration, model/SAE commits, source hash, environment, dataset/checksum, saved directions, calibration, transactional trials and invocation history. Exports add JSONL, analysis, blinded rating sheets, a report and SVG/PDF/PNG figures where recorded comparisons support them.

The main notebook now reads saved results; it neither downloads models nor independently implements experiments.
