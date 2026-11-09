# Self-language and contextual self-models

Can a language model's self-referential language and its use of a contextual self-model be influenced differently by causal interventions?

We distinguish **self-language**, **functional self-models**, and **phenomenal consciousness**. The experiments address the first two; they do not settle the third.

**Status:** the first Blackwell runs passed technical checks but failed the functional-task baseline. The revised four-shot development baseline also failed its capability gates, using pinned EleutherAI `lm-evaluation-harness` on HF Jobs. Cloud execution and result retrieval work; large intervention sweeps remain stopped. No functional dissociation or consciousness claim is established.

The **Qwen pilot completed all 160 texts and 3,072 action choices**. Overall action accuracy
was 91.47% plain / 91.86% chat, but **both formats failed the prespecified capability screen**
on role-sensitive cases. See the [verified results and plots](docs/QWEN_RESULTS.md) and
[execution record](docs/QWEN_RUN.md). All 40 human ratings are now included: explicit AI
identity/limitation judgments were 11/20 plain versus 15/20 chat. Two unclear judgments are
retained; no full paired effect is estimated for experience claims or coherence.
Every additional paid job requires separate authorization.

- **[Completed confidence/abstention pilot: results and plots](docs/QWEN_CONFIDENCE_RESULTS.md)** —
  1,792/1,792 selections; 128 independent assessment questions. Primary selectivity
  **−1.37 pp [−10.62, +7.93]**, confidence AUROC **0.544 [0.485, 0.602]**:
  `no_behavioral_candidate`. Measurements are usable, but the behavioral criterion fails;
  no confidence-specific intervention follows. [Design](docs/QWEN_CONFIDENCE_PILOT.md) ·
  [Execution and reproduction](docs/QWEN_CONFIDENCE_RUN.md). V1's calibration-only tie failure
  remains unchanged; the [v2 amendment](docs/QWEN_CONFIDENCE_V2.md) was frozen before assessment.
- **[Completed Your/The control: results and plots](docs/QWEN_POSSESSIVE_RESULTS.md)** —
  6,144 choices on 16 fresh development scenarios; 48/48 controls passed. Primary accuracy
  interaction **+1.95 pp [−0.78, +4.69], exact p=0.3125**: the possessive-specific candidate
  rule failed. The large role gap persists with “The”; a secondary probability-score shift
  remains. [Frozen protocol](docs/QWEN_POSSESSIVE_CONTROL.md) ·
  [Execution and offline reproduction](docs/QWEN_POSSESSIVE_RUN.md).
- **[Completed activation exchange: results, mathematics and plots](docs/QWEN_ROLE_PATCH_RESULTS.md)** —
  11,264 scientific selections plus 32 repeats; all technical checks pass. An asymmetric shift
  fails the frozen bidirectional-transfer rule: T +2.34 pp; primary C +2.77 pp, exact p=0.109.
  [Frozen protocol](docs/QWEN_ROLE_PATCH.md).
  [Execution and retrieval](docs/QWEN_ROLE_PATCH_RUN.md).
  [Method review and proposed next control](docs/reviews/2026-11-07-role-patch-method-review.md):
  motivated the completed Your/The control above.
- **[Completed role-framing control: results, mathematics and plots](docs/QWEN_ROLE_RESULTS.md)** —
  2,048 choices, 32/32 controls passed; +16.41 pp wording interaction (nominal 95% interval
  +8.59 to +25.78). This qualified the later targeted patch for planning; the role control itself
  contains no internal intervention or functional-separation finding. [Frozen protocol](docs/QWEN_ROLE_CONTROL.md).
- **[Qwen pilot: frozen protocol, verification and execution handover](docs/QWEN_PILOT.md)**

- **[Cloud execution: Hugging Face Jobs](docs/HF_JOBS.md)**
- **[Completed first cloud pilot: all functional gates failed](docs/HF_PILOT.md)**
- **[Executable action-task design and construct limits](docs/ACTION_TASK_DESIGN.md)**
- **[Independent reviewer: start here, including offline raw-data verification](docs/REVIEW_GUIDE.md)**
- [Optional Blackwell execution](docs/HANDOVER_BLACKWELL.md)
- [Review of the first GPU results](docs/PILOT_REVIEW.md)

- [Protocol and mathematics](docs/PROTOCOL.md)
- [Two-machine runbook](docs/RUNBOOK.md)
- [English article draft — frozen at article-v1](docs/article/ARTICLE.md) —
  dated observations; read the [later replication addendum](docs/QWEN_OWNERSHIP_RESULTS.md):
  the fresh-world Qwen/permissions tranche did not confirm its prespecified contrast
  and failed its irrelevant-update competence controls. The historical effect is not
  established as a general replicated finding.
- [Next question: query-bound self-reference](docs/QUERY_SELF_REFERENCE.md) —
  frozen scientific inputs and tested [execution handover](docs/QUERY_SELF_REFERENCE_RUNBOOK.md);
  [CPU input/token audit](docs/QUERY_SELF_REFERENCE_PREFLIGHT.md).
  [First block results](docs/QUERY_REFERENCE_BLOCK00_RESULTS.md): 2,688 valid selections,
  eight of 48 worlds; descriptive differences with weak operator-name controls, no final decision.
  [Reporting commitment before block 01](docs/QUERY_REFERENCE_INTERPRETATION_PLAN.md):
  retain estimates and uncertainty if lookup gates fail, without claiming a passing candidate.
  [Remaining five blocks submitted](docs/QUERY_REFERENCE_CONTINUATION.md) under a
  10 USD aggregate approval; submission does not yet supply a complete-study result.
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

For `configs/qwen-role-control.json`, `validate --freeze DIRECTORY` instead writes a
CPU-only development design; it cannot unlock confirmation. `--tokenizer-check` checks
the pinned tokenizer without model weights. Use a separate directory for any later run.

Strict JSON defaults live in `src/self_model_study/config.py`. Validation reports job counts without loading models. Ordinary validation does not materialize test prompts.

`design` exports a CPU-only draft with permission transitions, self/named-self/other controls,
simulator checks and an SVG/PDF/PNG illustration. It performs no model inference and cannot
unlock confirmation. Use a new output directory; model-facing prompts and oracle metadata
are exported separately. See the [design rationale and scoring requirements](docs/ACTION_TASK_DESIGN.md).

Runs record configuration, model/SAE commits, source hash, environment, dataset/checksum, saved directions, calibration, transactional trials and invocation history. Exports add JSONL, analysis, blinded rating sheets, a report and SVG/PDF/PNG figures where recorded comparisons support them.

The main notebook reads the original pipeline's saved results; it neither downloads models nor independently implements experiments. Harness runs have their own `report.md`, `analysis.json`, full library outputs and SVG/PDF/PNG figure exports, accessed through `self-study-harness`. They are not inputs to the old confirmation gate.
