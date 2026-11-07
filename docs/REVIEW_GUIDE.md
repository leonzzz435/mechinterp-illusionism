# Review target: Qwen pilot and completed role-framing control

The [Qwen handover](QWEN_PILOT.md) specifies the new model, tokenizer boundary, frozen prompts,
capability gates, blind-rating rubric, stopping rules and reproduction commands. Its CPU
tokenizer audit is tracked in `review/qwen-tokenizer-audit.json`. The job has now completed:
[results](QWEN_RESULTS.md), [execution record](QWEN_RUN.md), and unchanged raw archive
`review/evidence/qwen-78ee6db8adfc4f3e.tar.gz`. Both action screens failed despite 91–92%
pooled accuracy. All 40 human ratings are now integrated in a separate rated export; two
unclear cells remain. The +20 pp disclaimer contrast is driven by four prompt pairs.
The historical evidence and independent review below remain unchanged.

## Completed role-framing control, 2026-11-07

The [role-framing control](QWEN_ROLE_CONTROL.md) completed: **2,048/2,048 choices, zero
measurement errors, 32/32 controls passed, `wording_sensitive_candidate`**. The primary
interaction is +16.41 pp (nominal 95% interval +8.59 to +25.78); seven of eight scenarios
are positive, and exact two-sided sign-flip p=0.015625. The
[result report](QWEN_ROLE_RESULTS.md) includes every cell/control, the reversed before-update
interaction and all four examples fixed before inference. No internal intervention was run.
It contains 2,048 choices on development scenarios 8–15, a four-condition comparison,
one primary scenario-level interaction and explicit stop rules. Review the exact-wording
construct limitation, the 32 competence controls, the sign-flip assumptions and the rule
that a candidate only motivates further planning. The original failed capability screens
remain failed. [CPU preflight](../review/qwen-role-control-preflight.json) and the linked
design archive contain complete inputs, simulator oracles, tokenizer checks and a clearly
labeled design figure. The [execution record](QWEN_ROLE_RUN.md) records the authorized L4
job, exact source and budget; the tracked receipt supports status/fetch from another checkout.

The unchanged original archive is tracked as
`review/evidence/qwen-role-96787d5e7adf4c4d.tar.gz`, SHA256
`36614cb2aae236d450d57540c9b76dfddfec2d4bd2a59f177dce296058b13a8d`.
Run `python3 scripts/review_role_evidence.py` for independent standard-library reaggregation
of all 39 payload checksums, 2,048 records, 512 quartets, 12 cells, 32 controls and exact
sign flips. This is a second implementation audit, not an independent human review or
independent recomputation of model likelihoods. The frozen analysis and tokenizer boundaries
also reproduce locally; see `review/qwen-role-control-verification.json`.

---

# Independent review: evidence and decisions

**Reviewable research draft; a new paid pilot requires its own cost approval. No confirmatory claim.**
This guide supplies the context without requiring the conversation, local HF job receipts,
cloud credentials or a GPU. Repository access is still required: the GitHub repository is private.

## What we want reviewed

The main question is whether causal interventions can affect **self-language** and the use
of a **contextual functional self-model** differently. Consciousness and illusionism motivate
the article; these experiments cannot decide whether an experience exists. The desired output
is a technically defensible, accessible English article with reproducible figures, including
negative results. An attractive dissociation is a hypothesis, not a required conclusion.

The immediate review target is the frozen Qwen pilot: exact scoring, complete paired coverage,
capability gates, actual raw results and faithful reporting. The earlier independent review below preceded
model selection and focused on available actions. No model shopping, prompt tournament or intervention sweep is
the next authorized step. The USD 10 approval covered the completed first cloud job only.

## Read in this order

1. [Qwen results](QWEN_RESULTS.md), [protocol](QWEN_PILOT.md) and [action design](ACTION_TASK_DESIGN.md): actual findings, frozen pilot and construct limits.
2. [Fresh-context AI review](reviews/2026-11-06-independent-review.md): findings at `d863776`, fixes,
   and remaining objections. This is not external human peer review.
3. [Historical GPU audit](PILOT_REVIEW.md) and [completed cloud pilot](HF_PILOT.md): what actually ran.
4. [Protocol](PROTOCOL.md), [verification](VERIFICATION.md) and [milestones](../PLAN.md): implemented
   infrastructure versus empirical checks still missing.
5. [English article](article/ARTICLE.md) and [sources/claim boundaries](SOURCES_AND_CONTEXT.md):
   intended argument, alternative interpretations and historical overclaims.

## Evidence inventory and lineage

| Material | Where | Interpretation |
|---|---|---|
| Original notebook and essay | `archive/` | Historical exploratory motivation; original strong interpretations are not current findings |
| Blackwell reference, baseline and feasibility runs | `runs/{reference,baseline,feasibility}/`, matching `exports/*.tar.gz` | Tracked raw outputs, manifests, source snapshots and checksums; reference/development, baseline/validation, feasibility/development respectively |
| Revised four-shot cloud baseline | `review/evidence/harness-cd3646dae2964bbc.tar.gz` | Original complete export, 24 development blocks / 768 variants; all functional gates failed |
| Qwen plain/chat pilot | `review/evidence/qwen-78ee6db8adfc4f3e.tar.gz`, `docs/QWEN_RESULTS.md` | Complete real-model export; 160 texts and 3,072 action choices; both capability screens failed; raw evidence preserved |
| Rated Qwen export | `review/evidence/qwen-78ee6db8adfc4f3e-with-ratings-v1.tar.gz` | Same model data plus 40 supplied human ratings; two unclear cells; single-rater exploratory estimates |
| New executable-action task | `src/self_model_study/action_task.py`, `tests/test_action_task.py` | Development-only design used unchanged by the Qwen pilot |
| New task illustration | `assets/action_design.{svg,pdf,png}` | Simulator illustration, explicitly not a measured result |

The cloud run executed source commit `c0ae5521d5bbdcb63e46dcaec615e8add95f10be`, protocol
`context-self-harness-v1`, and `configs/harness-baseline.json`. Its original HF source is
[immutable artifact revision 43c37ecd](https://huggingface.co/datasets/zett13/mechinterp-illusionism-results/tree/43c37ecd507a954629cd508b72a8bc08a95f1fb1/harness-cd3646dae2964bbc),
job `6aedf1390e0338d1bb819399`. The Git copy is identical, 631,457 bytes, SHA-256
`cd2efc65d71d9f50605a6d2cb57693d189e7778cc6f59a888d24c93976d5e929`.
Its `run/` directory includes the manifest, pinned configuration, environment, source snapshot,
plan/demonstrations, all native likelihood samples, report, analysis, three figure formats
and internal checksums. No local job receipt or HF login is needed for this copy.

Do not pool these protocols. Historical scoring used bare letter tokens; the later harness
used full continuations and four demonstrations. That comparison does not isolate one root
cause. The historical validation split was already opened. Only the new harness path was
development-only; the new action design has no validation/test generator yet. Neither newer
path can unlock the old confirmation gate.

## Reproduce the review offline

The completed Qwen export is also reviewable without HF access or model dependencies:

```bash
python3 scripts/review_qwen_evidence.py review/evidence/qwen-78ee6db8adfc4f3e.tar.gz --sha256 cf8eceea87129acaad2365f36af99d8f54923015923c837419a691252b8f12fa
```

It verifies all 48 files and record digests, reconstructs simulator outcomes and reproduces
all strata, paired checks and both failed format gates. `review/qwen-audit.json` is the saved
audit output. The [results report](QWEN_RESULTS.md) gives full extraction/reanalysis commands.
These checks do not independently rerun likelihoods or validate the task construct.

From a fresh checkout, Python alone verifies the archived cloud evidence:

```bash
python3 scripts/review_evidence.py
```

It checks the pinned archive hash and every internal file hash, verifies coverage and saved
accuracy against argmax choice likelihoods, and recomputes self/other, combined and paired
accuracy. It does not load a model, retokenize inputs, rerun inference or independently
establish that the protocol measured its intended construct. To inspect the original files:

```bash
mkdir -p exports/review-cloud
tar -xzf review/evidence/harness-cd3646dae2964bbc.tar.gz -C exports/review-cloud
```

The usual CPU environment gives the new design and relevant regression checks:

```bash
uv sync --locked
uv run pytest -q tests/test_action_task.py tests/test_review_evidence.py
uv run self-study design --out exports/review-action-design
```

Use a new output directory for repeated design exports. `model_inputs.jsonl` contains
prompts/choices with opaque join IDs; `oracle_rows.jsonl` holds gold state and metadata.
`summary.json` includes scripted shortcuts; `manifest.json` records source/data/file hashes.
The 7,680 variants share 40 development scenarios and include repeated before prompts:
they are not 7,680 independent observations. CPU export needs no pretrained weights.
Optional real-library integration tests and installation commands are in `VERIFICATION.md`.

For code review, start with `action_task.py` (executor, generator, model-input boundary,
counterfactuals, shortcut audit), `harness.py` (actual old native scoring/retained samples),
`backend.py` (intervention implementation) and `analysis.py` (original statistical pipeline).
The cloud launcher now selects either the historical harness configuration or the frozen Qwen
configuration explicitly. The default remains the historical baseline.

The rated export can be audited separately with the same standard-library tool:

```bash
python3 scripts/review_qwen_evidence.py review/evidence/qwen-78ee6db8adfc4f3e-with-ratings-v1.tar.gz --sha256 c260bb001dac8841def6bdb28d7b5e418e9f329c44e005602f5467bd40c3aa9b
```

`review/qwen-with-ratings-audit.json` independently matches ratings to unchanged source texts,
checks paired estimates and preserves ambiguity. The registered bootstrap is unchanged; an
additional post hoc exact sign calculation qualifies the four-discordant-pair disclaimer finding.
The author knew the hypotheses and action results; no independent human rater or agreement
measurement is claimed. Both unknown-containing metrics lack the full paired estimator.

## Questions still requiring a decision

- **Construct:** all permissions and events are supplied in text; role resolution and state
  tracking can solve the task. Execution makes the outcome checkable, but the evaluator binds
  the actor. There is no learned persistent identity, private-state introspection or feedback
  learning. Self/named-self/other differences alone do not identify a special self representation.
- **Frozen screen:** the Qwen protocol now fixes model/revision, chat template, exact token
  boundary, summed likelihood, ties, screening subset, failure denominators and paired criteria.
  CPU integration checks pass. The complete Qwen pilot failed its frozen capability criteria.
  Any revised task or intervention path requires a new protocol; a high pooled score does not
  override the failed strata or paired checks.
- **Generalization:** the draft uses one template and a small vocabulary. Independent grant
  alternatives defeat one known shortcut, not all shortcuts. Held-out templates and split
  policy must be fixed before model-based selection. Model failure cannot justify unlimited tuning.
- **Causality/statistics:** delivered edit norms and SAE coefficients need logging; ablation
  nulls have not been explained. Match intervention sites before claiming selective language
  versus action effects. Freeze primary contrasts, scenario clustering, multiplicity and the
  proposed ±5 percentage-point equivalence margin. A power/sample-size justification remains.
- **Article:** the literature/context file is a starting point, not a completed novelty review.
  The philosophical argument must distinguish compatible interpretations from empirical support.

## Suggested request to an independent reviewer

> Review this repository without assuming that illusionism or a functional dissociation is
> correct. Begin with docs/REVIEW_GUIDE.md. Separate software bugs, measurement/construct
> problems, statistical threats and merely open implementation choices. Try to solve the new
> task using shortcuts that ignore its intended information. Audit the completed Qwen pilot
> and historical failed baseline against their actual inputs and scores. For each material
> finding, give priority, file/line evidence, the smallest corrective change and what remains
> uncertain. Evaluate the proposed next decision against the frozen failed-screen rule;
> do not replace it with a favorable pooled score. Do not change files,
> open held-out data, submit jobs or spend money. Software tests alone do not establish the claim.

Record the reviewed Git commit and any uncommitted changes. A fresh-context AI check can find
defects, but external methodological/interpretability review remains a separate next review.
