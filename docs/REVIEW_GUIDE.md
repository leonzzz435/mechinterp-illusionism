# Review target: publication draft on a recurring role error

**Execution update:** [All six blocks are retrieved and combined](QUERY_REFERENCE_RESULTS.md): 16,128 recorded selections, one exact tie, no missing cases. The frozen analysis remains ineligible for inference; lookup controls also miss their thresholds. The pre-run freeze and its verification records below remain unchanged.

The [separate retrospective sensitivity addendum](QUERY_REFERENCE_SENSITIVITY_ADDENDUM.md)
reports exploratory uncertainty after whole-world exclusion and both tied assignments.
It preserves the original analysis and article, and does not turn failed lookup controls into success.

Start with [Article v2: The Right Command for the Wrong Account](article-v2/ARTICLE.md),
its [paragraph ledger](article-v2/CLAIMS.md) and [technical appendix](article-v2/METHODS.md).
It centers the completed query-reference comparison, keeps the failed lookup controls
visible, and separates original counts from retrospective inference. The new
[stage/shortcut report](../review/query-reference-stages/report.md) includes every form,
both owners, presentation-specific baselines, and event-order splits.

The earlier [Naming the Agent, Choosing for the Other](article/ARTICLE.md) and its
[ledger](article/CLAIMS.md) remain frozen at `article-v1`; they describe the historical
context-line experiments. Read their subsequent addenda before interpreting generalization.

**New evidence after the article freeze:** the [completed Qwen/permissions tranche](QWEN_OWNERSHIP_RESULTS.md)
contains 18,432 choices on 48 fresh worlds. The categorical primary contrast is −0.39 pp
[−1.43, +0.74], unadjusted p=0.4893; all six irrelevant-update competence cells fail.
The article remains unchanged at `article-v1`; read this addendum before assessing
generalization. Three raw archives and an audit requiring neither cloud access nor inference
are included in `review/ownership-permissions-results/`. Run
`uv run --no-sync python scripts/review_ownership_evidence.py` to verify them.
The [CPU design review](OWNERSHIP_DESIGN_REVIEW.md) adds the conditional error-budget
bound (+2.69 pp at fixed observed accuracies), exact historical prompt checks and
scripted shortcut results. It distinguishes the pilot's query-bound self view from
the later named-query cohorts. Its proposed endpoints and gates do not amend the
frozen protocol. Reproduce it with `uv run --no-sync python scripts/review_ownership_design.py`.

**Completed query-reference question:** [query-bound self-reference](QUERY_SELF_REFERENCE.md), with
same-target named aliases and balanced third-person references. Its
[versioned JSON](../designs/query-self-reference-v1.json) is preserved from the review draft.
The separate [freeze record](../designs/query-self-reference-v1.freeze.json) seals its
scientific content, prepared inputs and tested execution. All six blocks have since
completed; see the [combined results](QUERY_REFERENCE_RESULTS.md), followed by the
retrospective supplements. The preflight alone is not behavioral evidence.
The frame-accuracy contrast is a co-endpoint.
The original [partial structural check](../review/query-self-reference-protocol-check.json)
is preserved. The later [complete CPU input audit](QUERY_SELF_REFERENCE_PREFLIGHT.md)
adds rendered inputs, independent text-oracle/simulator checks, paired controls, shortcut
baselines, historical overlap checks and every candidate's token boundary. It does not
evaluate model behavior. The [execution runbook](QUERY_SELF_REFERENCE_RUNBOOK.md) now
covers scoring, resumption, statistics, exports and the HF selection path. The new question
does not turn the tranche's post hoc frame
contrast into an independently replicated finding.

The article preserves positive findings as well as failed stronger criteria. Three disjoint
development cohorts are not three independent confirmatory replications; the patch reuses
the middle cohort. “Your” versus “The” was not an equivalence experiment. The
[philosophical source notes](article/PHILOSOPHICAL_NOTES.md) distinguish a restricted
report-use prediction from illusionism, HOT and GWT in general.

Two locally frozen specifications are separately reviewable:

- [Role-binding replication](OWNERSHIP_REPLICATION.md) and [JSON](../designs/ownership-replication.json):
  categorical errors, fresh scenarios, another template/model and prospective equivalence tests.
- [Confidence-record injection](REPORT_INJECTION.md) and [JSON](../designs/report-injection.json):
  abstention and fresh post-injection forced accuracy, with explicit theory assumptions.

The role-binding protocol now has one completed Qwen/permissions cell; Mistral and routing
remain unrun. The confidence-record injection specification remains unimplemented and unrun.
[Revision and verification notes](article/REVISION_NOTES.md) account for removed
sections, retained numbers, consistency searches and unchanged protected files.
The evidence inventory below remains available in full.

## Completed confidence baseline

The [completed confidence/abstention results](QWEN_CONFIDENCE_RESULTS.md) contain:
1,792 valid selections, usable measurement groups, S −1.37 pp [−10.62, +7.93], verbal AUROC
0.544 [0.485, 0.602], `no_behavioral_candidate`. The full analysis and all nine original
figure files reproduce exactly. The [raw-score audit](../review/qwen-confidence-audit.json)
also checks the primary statistic and AUROC using a separate implementation.

The [confidence/abstention protocol](QWEN_CONFIDENCE_PILOT.md) remains frozen.
Its [design JSON](../designs/qwen-confidence-pilot.json),
[author-source pins](../review/confidence-sources.json) and
[CPU preflight](../review/qwen-confidence-preflight.json) are reviewable without running Qwen.
The [execution record and reproduction commands](QWEN_CONFIDENCE_RUN.md) cover both versions.
V1 stopped during calibration before assessment exposure; review the explicit
[v2 exact-tie amendment](QWEN_CONFIDENCE_V2.md), all retained ties and whole-question sensitivity.
The [execution preflight](../review/qwen-confidence-execution-preflight.json) preserves
the original token-input fingerprint. Review the interpretation of fresh-pass
self-evaluation, generic-difficulty predictors, answer revisions, grouped uncertainty and
deviations from the source study. This is a conceptual partial replication, not evidence
against all self-monitoring or the source paper's causal findings. The failed candidate rule
does not justify an internal intervention or another prompt search. A different measurement
needs a reasoned decision. Software cross-checks are not independent scientific peer review.

## Completed empirical evidence

Start with [the Your/The results](QWEN_POSSESSIVE_RESULTS.md),
[full report](QWEN_POSSESSIVE_FULL_REPORT.md), [frozen protocol](QWEN_POSSESSIVE_CONTROL.md)
and [execution provenance](QWEN_POSSESSIVE_RUN.md). All 6,144 choices completed, zero errors,
48/48 controls passed. The sole primary accuracy interaction is **+1.95 pp [−0.78, +4.69]**,
exact p=0.3125, positive in 4/16 scenarios: **`no_clear_possessive_specificity`**.
The large role gap persists with nonpossessive The; a positive secondary margin remains.
Review why neither the descriptive +13.67 pp Your/Reference anchor nor the margin replaces
the primary endpoint, and why pooled controls do not restore the original capability gate.

The unchanged archive `review/evidence/qwen-possessive-f2baaa2fb6b74880.tar.gz` has SHA256
`d521a63c21c360b33ba8452ab5d572eaf0d06c4e4be02df02425dfc1c2fe3e59`.
`uv run --no-sync python scripts/review_possessive_evidence.py` reaggregates all outcomes,
matched comparisons, 162 bootstrap intervals and the exact test without study-package imports.
`scripts/verify_possessive_run.py` reproduces the archived analysis and original figures,
checks SQLite/JSONL parity and all real tokenizer boundaries (eval extras and cached tokenizer).
The [preflight](../review/qwen-possessive-preflight.json) preserves the pre-run input-disjointness
checks. These are two software paths, not external peer review or new likelihood computation.
Independent external review remains outstanding; the next decision concerns the original
self-language/function operationalization, not an automatic follow-up GPU job.

For the prior empirical finding, start with the [exchange results](QWEN_ROLE_PATCH_RESULTS.md),
the [single-site patch protocol](QWEN_ROLE_PATCH.md) and
`configs/qwen-role-patch.json`. It uses eight already observed scenarios to investigate the
known wording interaction, not to claim held-out confirmation. Review donor/candidate mapping,
causal role-end alignment, full-command scoring, BF16 norm controls, source integrity, the
sole primary transfer-vs-random contrast and conservative decision rules. The implementation
and CPU checks are separate from the [completed GPU run](QWEN_ROLE_PATCH_RUN.md).
All 11,264 choices and 32 repeats are present; technical checks pass. The frozen
bidirectional-transfer decision fails: T=+2.34 pp, C=+2.77 pp, exact p=0.109375, 5/8
positive scenario contrasts. Review the asymmetric directional findings and the difference
between the positive bootstrap interval and failed joint decision. Historical archives below
are unchanged; the original failed capability screen remains failed.

The [2026-11-07 internal method review](reviews/2026-11-07-role-patch-method-review.md)
examines the asymmetry, answer transitions, prespecified secondary command margins and
edit size. It recommends a one-token Your/The comparison before another internal patch.
Its [reproducible review artifact](../review/qwen-role-patch-method-review.json) includes
CPU feasibility of 6,144 proposed cases, without model inference. This review was written
by the same coding assistant, not an independent reviewer. Its unfrozen proposal has now
been superseded by the frozen protocol linked above; the review artifact remains historical.

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
interaction and all four examples fixed before inference. No internal intervention was run in that role-control experiment.
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

The immediate review target is the completed wording control, exchange and their evidence chain: exact scoring,
paired coverage, frozen gates, raw results and faithful reporting. The earlier independent review below preceded
model selection and focused on available actions. No model shopping, prompt tournament or intervention sweep is
the next authorized step. The USD 10 approval covered the completed first cloud job only.

## Read in this order

0. [Completed Your/The control](QWEN_POSSESSIVE_RESULTS.md), its full report and audit commands
   above; then [completed exchange](QWEN_ROLE_PATCH_RESULTS.md), [complete cloud report](QWEN_ROLE_PATCH_FULL_REPORT.md),
   [frozen protocol](QWEN_ROLE_PATCH.md) and [execution provenance](QWEN_ROLE_PATCH_RUN.md).
   Run `uv run --no-sync python scripts/review_patch_evidence.py` for the standard-library audit.
   `scripts/verify_patch_run.py` additionally reproduces the frozen bootstrap, checks the journal,
   retokenizes all baselines and reconstructs saved BF16 edit norms on CPU (eval extras and cached
   tokenizer required; no inference). This is software reaggregation, not external human review.
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
| Completed Your/The control | `review/evidence/qwen-possessive-f2baaa2fb6b74880.tar.gz`, `docs/QWEN_POSSESSIVE_RESULTS.md` | 6,144 choices, 16 fresh development instances; failed possessive-specific accuracy candidate, descriptive role contrast persists, positive secondary margin |
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
