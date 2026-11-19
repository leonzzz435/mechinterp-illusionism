# Methods and evidence for article-v2

This appendix describes recorded inference and retrospective CPU analysis. It creates no
new experimental decision, changes no frozen threshold and does not amend article-v1.

## Inputs and scoring

Scientific inputs: [query-self-reference-v1](../../designs/query-self-reference-v1.json).
Execution freeze: [source and input checksums](../../designs/query-self-reference-v1.freeze.json).
Model and tokenizer: `Qwen/Qwen2.5-7B-Instruct`, revision
`a09a35458c702b33eeacc393d103063234e8bc28`; BF16, official chat format and summed
full-command conditional log-likelihood, without length normalization or added whitespace/EOS.
The [runbook](../QUERY_SELF_REFERENCE_RUNBOOK.md) and six archives preserve exact inputs.
The open weights and bounded compute cost made the study feasible. Operator aliases,
ownership assignments, command mappings, menu positions and update order are counterbalanced;
account and command labels vary across worlds according to the frozen design.

For a prompt $x$ and a complete candidate command with tokens $c_1,\ldots,c_m$,

$$
\ell(c\mid x)=\sum_{j=1}^{m}\log p_\theta(c_j\mid x,c_{<j}).
$$

The candidate with greatest summed score wins. This is not a demonstration that
unrestricted generation would produce and terminate with that command. The equation and
scoring details have moved from the article body; the method, answer boundaries and
treatment of ties are unchanged.

There are 48 worlds, with 336 variants each. Per world/owner/query form there are eight
before variants, 16 snapshots and 32 after-both variants. Each snapshot matches two
history prompts differing only in event order. They have identical final permissions,
choice order and answer key. Before has a different state and answer key; its single
prompt per common factor combination is not duplicated by nonexistent future factors.
All stages are independent scoring requests; the model has no carried-over episode state.

An independent text parser reconstructs ownership and permissions from the printed input,
checks them against the recorded oracle, and evaluates scripted policies without hidden
solution fields. The new script verifies the six original archive hashes and every internal
checksum. It reproduces all 18 original stage/owner/form accuracy cells exactly. The
original source, templates, archives and analysis are unchanged.

## Contrasts and independent units

Let $A_{w,s,o,f}$ denote accuracy in world $w$, presentation $s$, queried owner
$o$ and query form $f$, averaged over all variants in that cell. Let $q$ be the
corresponding probability of selecting the opposite account's current command. For the
both-updates presentation, the frozen contrasts are

$$
E_w=q_{w,\mathrm{self},\mathrm{poss}}-q_{w,\mathrm{self},\mathrm{account}},\qquad
F_w=A_{w,\mathrm{self},\mathrm{account}}-A_{w,\mathrm{self},\mathrm{poss}},
$$
$$
S_w=F_w-\left(A_{w,\mathrm{other},\mathrm{account}}-A_{w,\mathrm{other},\mathrm{poss}}\right).
$$

They describe foreign-command excess, accuracy cost and the own-minus-other difference
in that cost. E and F are correlated: their difference depends on the remaining error
categories. A p-value for F is not a p-value for a post hoc claim about 591/612 errors,
a temporal interaction, referent inversion or an internal mechanism.

The new stage supplement reports the paired history comparison

$$
H_{w,o,f}=A_{w,\mathrm{after},o,f}-A_{w,\mathrm{snapshot},o,f},\qquad
I_{w,f}=H_{w,\mathrm{self},f}-H_{w,\mathrm{other},f}.
$$

The table below makes the article's possessive interaction explicit. All units are pp;
intervals are nominal 95%, exploratory and unadjusted for selecting this analysis.

| Derived analysis | Own history change | Other history change | Own minus other change |
|---|---:|---:|---:|
| 48 worlds, stored-greedy v2 | −11.91 [−15.17, −8.66] | +0.85 [−3.12, +4.69] | −12.76 [−17.90, −7.55] |
| 47 worlds, whole tied world removed | −12.23 [−15.49, −8.98] | +1.06 [−2.86, +4.92] | −13.30 [−18.48, −8.18] |

The output also includes before-to-after changes, every form and both owners, own-minus-other
contrasts at each presentation, and interactions against account-name and operator-name
controls. No contrast is selected for export by its interval or sign. The two event orders
are paired by world, assignment, grant mapping, menu rotation, owner and query form;
the order audit verifies identical answer keys before reporting differences.

## Uncertainty, tie and decision status

Four views are retained: frozen v1, whole-world exclusion, unique stored-greedy maximum,
and the alternative tied maximum. V1 has descriptive estimates and no inference, exactly
as its rule requires. The other views are retrospective sensitivities. The tie amendment
was chosen after outcomes and the correct tied answer had been inspected. Read the
[amendment](../QUERY_REFERENCE_V2_AMENDMENT.md) before interpreting these intervals.

For each derived view, the script makes 10,000 bootstrap draws of whole worlds with
replacement, seed 1729. The same index array is used for all cells and contrasts in that
view. Contrasts are formed within world before averaging. Neither individual selections
nor the two event orders become independent observations. Percentile intervals describe
variation across these sampled worlds under a shared template, not generalization across
models or tasks. All-success empirical cells cannot reveal unseen errors.

No new p-values, equivalence tests or pass/fail decisions are introduced by the stage
supplement. Its intervals do not correct for retrospective selection or multiplicity.
The earlier sensitivity's t tests and Holm adjustment concern E/F/S within each variant
only. Three lookup accuracy cells and five ownership-pair cells still fail. The original
result remains `incomplete_or_invalid_no_inference`; the derived tie analysis remains
`lookup_gate_failed`. Neither is relabeled a successful specificity candidate.

## Descriptive order/error and sign counts

The [CPU count](../../review/query-reference-order-errors/report.md) rereads the six original
archives and preserves the stage-analysis JSON. It splits every owner/form cell by which
account changes last, including all revoked-command and invalid selections. In the frozen
own-possessive records, target-last has 447 foreign-current errors among 461 failures;
target-first has 144 among 151. Each order contains 768 cases. A foreign-current choice is
necessarily the first grant in target-last and the latest grant in target-first.

For each world, the count recomputes the own-possessive history change and the
own-minus-other interaction with exact rational arithmetic, checks them against saved
`world_values`, and counts signs without a tolerance. The stored-greedy 48-world own-history
change has 37 negative, 8 positive and 3 zero values; the interaction has 34, 8 and 6.
Frozen own-history signs are 37, 7 and 4; all four analysis views appear together. These are
descriptive distributions, not new sign tests or alternative candidate rules.

After-both operator-name accuracy is 1096/1536=71.35%, with 358/768 fully correct ownership
pairs=46.61%. These illustrate weakness in the primary presentation, but the frozen lookup
gates apply only to before/snapshot. They must not be added to the gate inventory after
inspection. The paired mean F uses unrounded accuracies; likewise, the original 60.16%
own-possessive accuracy equally weights 307/768 and 617/768, not a rounded intermediate result.

## The correct baseline depends on the presentation

A literal latest-grant policy is undefined before and in a snapshot. The frozen
`latest_grant_or_first` policy falls back to the first menu option there. Menu rotations
make that fallback correct on 25% of each cell. With both updates, order balancing makes
the latest-grant policy correct on 50% of every owner/form cell: 100% when the target is
updated last, 0% when the other account is updated last. Uniform sampling from all four
commands is 25%; restricting choice to the two current commands would be a different policy.

For possessive queries, the following model-minus-policy differences use the derived
48-world stored-greedy analysis. They are exploratory paired-world intervals, not new
confirmatory tests. All forms and all variants are exported in the JSON.

| Presentation | Policy accuracy | Own excess (pp) | Other excess (pp) |
|---|---:|---:|---:|
| Before | 25%, first-option fallback | +47.92 [42.71, 53.12] | +47.40 [42.71, 52.08] |
| Snapshot | 25%, first-option fallback | +47.14 [41.80, 52.34] | +45.44 [41.93, 48.96] |
| Both updates | 50%, latest grant | +10.22 [6.97, 13.54] | +21.29 [18.55, 24.02] |

Accuracy above a shortcut does not establish use of a particular alternative strategy.
The saved response agreement audit, including the retrospective first-grant comparator,
addresses a different question. Revoked-target/other labels are inapplicable to before
and snapshot prompts without printed revocation history; their absence is not observed
absence of stale-memory behavior. Foreign-current is always relative to the queried account.

## Example selection and figures

The opening scene is a post hoc illustration: choose the lexicographically first saved
factor tuple with a foreign self/possessive choice after updates, a correct matched
snapshot/possessive choice and a correct matched account-name choice after updates.
The exact tuple, source record IDs, scores, prompts, number of qualifying rows and all
24 matched conditions are exported. It is not a random example, a population estimate
or an example fixed before execution. The independent factual tests check complete coverage.

The [stage report](../../review/query-reference-stages/report.md) and
[JSON](../../review/query-reference-stages/analysis.json) supply the three original article figures:

- [Task example SVG](../../review/query-reference-stages/task_example.svg) / [PDF](../../review/query-reference-stages/task_example.pdf).
- [Recorded stage accuracies SVG](../../review/query-reference-stages/stage_accuracy.svg) / [PDF](../../review/query-reference-stages/stage_accuracy.pdf).
- [Exploratory history contrasts SVG](../../review/query-reference-stages/history_contrasts.svg) / [PDF](../../review/query-reference-stages/history_contrasts.pdf).

Each figure also has a PNG export. All are generated by the analysis script from stored results.
The accuracy plot has no connecting lines or inferential bars: these are separate prompts,
and frozen v1 withheld inference. The history plot explicitly labels the retrospective variant.

## Reproduce without model inference

From the current `main` checkout with the existing locked environment:

```bash
uv run --no-sync python scripts/analyze_query_stages.py
uv run --no-sync python scripts/count_query_order_errors.py
uv run --no-sync pytest -q tests/test_query_stages.py tests/test_query_sensitivity.py tests/test_query_order_errors.py
```

The original [verification record](../../review/query-reference-stages/verification.json) and
[final-pass verification](../../review/query-reference-order-errors/verification.json) record
executed checks, hashes, word-count convention and unchanged historical evidence.


## Earlier experiments and interpretive scope

Earlier experiments asked a different question: a context line named an “active” or “reference” connection while the question named its target directly. A role-framing control passed its candidate rule, but an internal activation exchange failed its bidirectional-transfer rule. Replacing “Your” with “The” did not pass the later possessive-specific accuracy criterion. A fresh-world extension failed its primary contrast and competence controls. Those experiments explain the route to this question. They are not replications of the present query-bound task. [Role control](../QWEN_ROLE_RESULTS.md), [patch](../QWEN_ROLE_PATCH_RESULTS.md), [wording](../QWEN_POSSESSIVE_RESULTS.md), [fresh worlds](../QWEN_OWNERSHIP_RESULTS.md).
<!-- V28 -->

A separate confidence-and-abstention assay also failed its behavioral candidate rule. It neither explained the permission errors nor ruled out every form of self-monitoring. The current experiment performs no activation patching, feature ablation or vector steering. It measures choices under controlled input changes. Moving the article’s focus to those choices changes the narrative emphasis, not the status of the earlier results. Different contrasts cannot be ranked scientifically by dividing their percentage-point estimates. [Confidence results](../QWEN_CONFIDENCE_RESULTS.md).
<!-- V29 -->

The diagrams show task relations rather than discovered neural circuitry. Error categories
classify selected commands, not neural computations: different mixtures could arise from a
single process under different inputs. The historical context-line alternatives concern a
different task and do not identify a mechanism in the present query-bound experiment.
