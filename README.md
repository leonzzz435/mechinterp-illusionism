# Self-language and contextual self-models

Can a language model's self-referential language and its use of a contextual self-model be influenced differently by causal interventions?

We distinguish **self-language**, **functional self-models**, and **phenomenal consciousness**. The experiments address the first two; they do not settle the third.

**Status:** the first Blackwell runs passed technical checks but failed the functional-task baseline. The revised four-shot development baseline also failed its capability gates, using pinned EleutherAI `lm-evaluation-harness` on HF Jobs. Cloud execution and result retrieval work; large intervention sweeps remain stopped. No functional dissociation or consciousness claim is established.

The bounded **Qwen reference/action pilot has been submitted as one authorized L4 job**.
It compares plain/chat self-language and zero-shot permission use. The
[execution record](docs/QWEN_RUN.md) tracks its status and evidence; human ratings remain
pending. Every additional paid job requires separate authorization.

- **[Qwen pilot: frozen protocol, verification and execution handover](docs/QWEN_PILOT.md)**

- **[Cloud execution: Hugging Face Jobs](docs/HF_JOBS.md)**
- **[Completed first cloud pilot: all functional gates failed](docs/HF_PILOT.md)**
- **[Executable action-task design and construct limits](docs/ACTION_TASK_DESIGN.md)**
- **[Independent reviewer: start here, including offline raw-data verification](docs/REVIEW_GUIDE.md)**
- [Optional Blackwell execution](docs/HANDOVER_BLACKWELL.md)
- [Review of the first GPU results](docs/PILOT_REVIEW.md)

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

## Cloud: standard-harness baseline

The first Hugging Face Jobs execution completed all 768 variants on one L4 GPU. All functional gates still failed; see the [pilot report](docs/HF_PILOT.md). The [cloud handover](docs/HF_JOBS.md) covers local login, bounded submission, logs and automatic checkpoint persistence to a private HF repository. The launcher does not install GPU dependencies on this computer. The commands below document reproduction; the first authorized job is already complete.

```bash
uv run --script scripts/hf_jobs.py plan --namespace YOUR_HF_NAME --budget-usd 10
uv run --script scripts/hf_jobs.py submit --namespace YOUR_HF_NAME --budget-usd 10
uv run --script scripts/hf_jobs.py status
uv run --script scripts/hf_jobs.py fetch
```

Cloud execution, artifact persistence and local download/re-analysis have now been verified. No further job or intervention sweep is authorized by this report.

## Optional Blackwell execution

```bash
uv sync --locked --extra gpu --extra eval
uv run --extra gpu --extra eval self-study-harness validate configs/harness-baseline.json
uv run --extra gpu --extra eval self-study-harness run configs/harness-baseline.json --out runs/harness-baseline-v1
uv run --extra gpu --extra eval self-study-harness export runs/harness-baseline-v1 --out exports/harness-baseline-v1.tar.gz
```

The new configuration pins the same `unsloth/gemma-2-2b` commit as the first GPU runs. No automatic model fallback or assumption of weight identity is made. Local authentication, if needed, stays outside configurations and exports.

This baseline has 24 resumable scenario blocks and a one-hour cooperative invocation limit. It opens no validation or test data. Follow the handover to return the result archive through Git. Do not start the historical development/validation sweeps after it automatically.

## Interfaces and artifacts

The Qwen pilot uses the main CLI with `configs/qwen-pilot.json`. Its own versioned protocol,
analysis and export are isolated from the original confirmation workflow. An optional
`self-study validate configs/qwen-pilot.json --tokenizer-check` audits the actual tokenizer
on CPU without loading weights. See the Qwen handover before any submission.

```text
self-study validate CONFIG [--freeze PROTOCOL.json --evidence VALIDATION_RUN]
self-study run CONFIG --out RUN [--max-jobs N] [--max-seconds N]
self-study analyze RUN [--ratings CSV]
self-study export RUN --out ARCHIVE.tar.gz
self-study design --out DIRECTORY [--seed 1729] [--scenarios 40]
```

Strict JSON defaults live in `src/self_model_study/config.py`. Validation reports job counts without loading models. Ordinary validation does not materialize test prompts.

`design` exports a CPU-only draft with permission transitions, self/named-self/other controls,
simulator checks and an SVG/PDF/PNG illustration. It performs no model inference and cannot
unlock confirmation. Use a new output directory; model-facing prompts and oracle metadata
are exported separately. See the [design rationale and scoring requirements](docs/ACTION_TASK_DESIGN.md).

Runs record configuration, model/SAE commits, source hash, environment, dataset/checksum, saved directions, calibration, transactional trials and invocation history. Exports add JSONL, analysis, blinded rating sheets, a report and SVG/PDF/PNG figures where recorded comparisons support them.

The main notebook reads the original pipeline's saved results; it neither downloads models nor independently implements experiments. Harness runs have their own `report.md`, `analysis.json`, full library outputs and SVG/PDF/PNG figure exports, accessed through `self-study-harness`. They are not inputs to the old confirmation gate.
