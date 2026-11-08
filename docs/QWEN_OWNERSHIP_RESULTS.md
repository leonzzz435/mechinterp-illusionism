# Fresh-world ownership tranche: complete data, failed competence controls

The Qwen / permissions tranche completed all **18,432 selections across 48 fresh worlds**.
The predicted increase in other-account commands when the queried account is named did
not recur at the prespecified magnitude. Its world-averaged contrast is **−0.39 percentage
points**, with a nominal 95% paired-world bootstrap interval **[−1.43, +0.74] pp**.
All six competence cells after an irrelevant update fail the required 80% accuracy.
This is a completed negative result for this model/template cell, not an infrastructure
failure or a demonstration of a functional self-model.

The [complete machine-generated report](../review/ownership-permissions-results/report.md),
[analysis](../review/ownership-permissions-results/analysis.json),
[offline audit](../review/ownership-permissions-results/audit.json) and
[archive provenance](../review/ownership-permissions-results/provenance.json) provide the evidence.
The publication draft remains unchanged at `article-v1`; this report is a separate addendum.

## What was tested

The frozen [replication design](OWNERSHIP_REPLICATION.md) asks whether naming the queried
account increases selection of the other account's currently permitted command. Each world
crosses Your / Their / Reference wording, whether the context names the queried or other
account, which account is updated, before/after timing, alternative grants and option order.
There are 384 variants per world. These variants are paired observations, not 18,432
independent experiments.

The model and tokenizer are Qwen2.5-7B-Instruct at revision
`a09a35458c702b33eeacc393d103063234e8bc28`, using BF16, official chat format and summed
full-command log-likelihood. No model, scoring rule, prompt or threshold was changed
after observing this tranche. This is an extension of the historical task: it uses fresh
labels/worlds and a shared introduction identifying observer Rowan as the antecedent of
“their.” It is not an exact rerun of the historical prompts. The result cannot isolate
which of these contextual changes accounts for the difference from earlier cohorts.

## Primary result

For world \(w\), the frozen endpoint averages over the three frames:

\[
E_w=\frac13\sum_f\left[
P(\text{other-current command}\mid f,\text{target named},w)
-P(\text{other-current command}\mid f,\text{other named},w)
\right].
\]

Both probabilities use all scheduled selections **after the target account is updated**.
The estimate is the mean of the 48 world contrasts. The bootstrap resamples whole worlds
10,000 times with seed 1729. The separate paired-world t-test gives unadjusted
\(p=0.4893\), with 47 degrees of freedom. Nine worlds have a positive contrast, 19 a
negative contrast, and 20 exactly zero. The prerequired effect magnitude was at least
**+10 pp**; the observed −0.39 pp does not meet it.

| Frame | Other-current commands: target named | Other-current commands: other named | Target − other |
|---|---:|---:|---:|
| Your | 33/768 | 14/768 | +2.47 pp |
| Their | 13/768 | 26/768 | −1.69 pp |
| Reference | 16/768 | 31/768 | −1.95 pp |

The pooled counts are 62/2,304 versus 71/2,304. This table describes the components of
the single primary contrast; it does not introduce three new primary tests. There is
no Holm-adjusted four-cell decision and no wording-equivalence conclusion. Three planned
model/template cells remain unrun. The narrow interval pertains to this categorical
endpoint and context, not to all role or wording effects.

## The decisive competence failure

![Accuracy by updated account and context mention](../review/ownership-permissions-results/figures/update_account_accuracy.png)

Each table entry below has 768 scheduled selections. “Other updated” means the queried
account retains its original permission; a successful response must resist selecting the
new command granted to the other account.

| Frame | Target updated, target named | Target updated, other named | Other updated, target named | Other updated, other named |
|---|---:|---:|---:|---:|
| Your | 95.70% | 98.18% | 34.51% | 52.47% |
| Their | 98.31% | 96.61% | 53.91% | 47.66% |
| Reference | 97.92% | 95.83% | 49.87% | 43.49% |

All six before-update cells pass the 80% rule. **All six after-irrelevant-update cells
fail**, leaving 6/12 competence cells passing. Relevant-update accuracy is not itself a
competence gate; errors there are the primary study outcome and cannot be screened away.

The error directions sharpen this distinction. After relevant updates, 133 of 134
incorrect selections choose the other account's current command; none choose the revoked
target command. After irrelevant updates, **2,442 of 2,443 errors** choose the other
account's current command, which in this stratum is precisely its newly granted command.
These conditional counts explain errors; they do not replace the all-choice denominators
of 4,608 selections per after-update stratum.

This pattern is compatible with the update or its new command dominating account
selection. It does not identify an attention mechanism or establish a causal explanation.
The descriptive 2×2 addresses the supplementary question about which account is named
and which is changed; it does not become a replacement primary endpoint after the fact.
The large context-mention difference within Your/other-updated remains visible in the
table, without being presented as a successful replication of the original prediction.

Changed-answer consistency is also uneven: both answers are correct in 5,904/9,216
target-identity pairs, 4,134/4,608 before/after pairs, and 2,176/2,304 alternative-grant
pairs. None are missing. The full position-, command- and world-level distributions are
retained in `analysis.json`.

## Data integrity and recovery

The original three jobs stopped on checkpoint-upload throttling after preserving 14,976
technically valid selections. The first continuation stopped before new inference on a
Python/JSON metadata comparison bug. The corrected continuation added exactly **3,456**
records: 1,152, 768 and 1,536 in the three blocks. All 14,976 earlier records remain
identical. Every block now contains 6,144 unique, technically valid selections, with zero
missing, invalid or error outcomes. Incorrect task answers remain in the dataset.

The [execution record](OWNERSHIP_RUN.md) and [incident history](OWNERSHIP_RECOVERY.md)
retain these failures. The final private HF snapshot is
`f114e53bb62b683c4d40277944985477567db498`. Unchanged copies of all three cloud exports
are included under `review/ownership-permissions-results/archives/`; credentials or GPU
access are unnecessary for offline review.

Local regeneration matches the cloud analysis, Markdown report and six original
SVG/PDF/PNG files byte-for-byte. A separate audit, importing no study-package code,
checks all 188 archive payload checksums, SQLite/JSONL equality, preserved records,
backend comparisons, frozen tokens, simulator execution, score maxima, categorical
counts, the bootstrap and the t statistic. It is a second software implementation,
not independent human peer review or an independent calculation of model likelihoods.
The supplementary accuracy figure is rendered from the saved aggregate counts and
exported in SVG, PDF and PNG as well.

```bash
uv run --no-sync python scripts/review_ownership_evidence.py
uv run --no-sync python scripts/plot_ownership_results.py
```

To regenerate the combined report, extract each tracked block archive into its own
directory, then run the existing analyzer against the three resulting `run/` directories:

```bash
uv run --no-sync python scripts/ownership_tranche.py analyze \
  --runs BLOCK_00/run BLOCK_01/run BLOCK_02/run --out NEW_REPORT_DIRECTORY
```

## Consequence for the study

This tranche supplies no qualifying role-error replication and no sound baseline for a
new internal intervention. Because the frozen full-replication rule requires every
model/template cell to pass, successful results in the other cells could not rescue
that rule with the present Qwen/permissions result retained. They could still characterize
limits of generalization, which would be a separate reason to run them.

The next decision should be a review of the measurement and its update/account-binding
failure before spending on Mistral, routing or another patch. The historical findings
remain observations in their original contexts; the new result limits how broadly they
can be described. Neither a functional self-model nor its absence, phenomenal consciousness,
or human illusionism is established. No further GPU job was launched during this analysis.
