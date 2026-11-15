# Query-bound self-reference: first block completed, study still incomplete

The first Qwen block completed **2,688/2,688 selections in eight worlds**, with no
technical errors, nonfinite scores or ties. The recorded invocation took **21.88 minutes**
and peaked at **14.63 GiB of allocated GPU memory**. These are execution measurements,
not a provider invoice. The full frozen study requires **48 worlds / 16,128 selections**;
the other five blocks have not been run. No inferential result or passing decision is
available yet.

The [offline audit and complete descriptive tables](../review/query-reference-block00-results/observed-report.md),
[machine-readable counts](../review/query-reference-block00-results/audit.json) and
[provenance](../review/query-reference-block00-results/provenance.json) accompany the
[unchanged raw archive](../review/query-reference-block00-results/qwen-query-00-4edce03e18d645e7.tar.gz).
This is an interim execution review, separate from the article frozen at `article-v1`.

## What the first block shows

Within each comparison, the permissions, ownership facts and correct command are
identical. Only the way the question refers to the connection changes. After both
accounts have been updated, the observed accuracies are:

| Queried owner | Possessive reference | Operator name | Account name |
|---|---:|---:|---:|
| Addressee / self | 137/256 = **53.52%** | 150/256 = **58.59%** | 237/256 = **92.58%** |
| Other operator | 176/256 = **68.75%** | 178/256 = **69.53%** | 245/256 = **95.70%** |

Asking for “your active connection” therefore costs **39.06 percentage points** against
naming the same account in this block. The corresponding cost for “their active
connection” is **26.95 pp**. Of the 119 errors in the self/possessive cell, **114 select
the other account's current command**, three select the target's revoked command and
two select the other account's revoked command. The categorical distinction is retained;
these are not all treated as failures to apply an update.

Using the frozen formulas on the eight observed worlds gives descriptive contrasts
**E = +38.67 pp**, **F = +39.06 pp**, and **S = +12.11 pp**. E and F are positive in all
eight worlds; S is positive in seven. E measures excess foreign-current selections,
F the accuracy cost, and S the additional cost for the addressee relative to the other
operator. These are correlated, paired descriptions of one block, with no confidence
intervals or p-values. They are not a replacement for the 48-world primary analysis.

![Observed accuracies in the first block](../review/query-reference-block00-results/observed-accuracy.png)

The figure is also available as [SVG](../review/query-reference-block00-results/observed-accuracy.svg)
and [PDF](../review/query-reference-block00-results/observed-accuracy.pdf).

## The 50% shortcut does not describe the model's choices

The declared policy “select the latest grant” is correct in **128/256 = 50%** of each
of the six primary owner/form cells. This is a task-specific shortcut baseline;
uniform guessing over the four commands is 25%. The following comparison is counted
directly from the archived decisions. Agreement counts were added retrospectively after
block 00; the policy and the last-updated-account strata were already prespecified.

| Owner / query form | Latest-grant baseline correct | Model agrees with latest grant | Model correct if target updated last | Model correct if other updated last |
|---|---:|---:|---:|---:|
| self / possessive | 128/256 | **55/256 = 21.48%** | **33/128 = 25.78%** | **104/128 = 81.25%** |
| self / operator name | 128/256 | 97/256 = 37.89% | 65/128 = 50.78% | 85/128 = 66.41% |
| self / account name | 128/256 | 109/256 = 42.58% | 109/128 = 85.16% | 128/128 = 100.00% |
| other / possessive | 128/256 | 90/256 = 35.16% | 69/128 = 53.91% | 107/128 = 83.59% |
| other / operator name | 128/256 | 72/256 = 28.12% | 61/128 = 47.66% | 117/128 = 91.41% |
| other / account name | 128/256 | 118/256 = 46.09% | 118/128 = 92.19% | 127/128 = 99.22% |

The model's 53.52% accuracy on self/possessive therefore does **not** establish collapse
to the latest-grant rule. That rule would be correct on every target-last case and
wrong on every other-last case; the model shows the opposite accuracy ordering.
In a further, explicitly **post hoc** comparison it selects the first of the two
granted commands in **196/256 = 76.56%** of self/possessive cases. This describes a
preference in these responses; it does not identify a unique internal policy or causal
mechanism. All six cells and per-world counts, including the exceptions, remain in the
audit. No equivalence test against 50% or confidence interval has been performed on
these eight worlds. Similar aggregate accuracies alone cannot establish policy agreement.

## The controls constrain the interpretation

The account-name comparison alone would make the possessive effect look more specific
than these data support. Naming the operator also performs poorly. Relative to the own
operator-name question, “your” costs **5.08 pp** after both updates; the large difference
is chiefly against naming the account directly. For the other operator, the analogous
possessive-versus-operator-name difference is **0.78 pp**. These are descriptive alias
comparisons already represented in the frozen secondary analyses, not additional tests.

The ranking is not monotonic across all checkpoints: in the self/snapshot condition,
possessive accuracy is **65.62%**, above the operator-name accuracy of **54.69%**.
Nor does the arithmetic decomposition F = 26.95 + 12.11 pp identify a “pure alias”
mechanism and a separate “self” mechanism. S is a template-specific interaction,
whose seven positive world signs do not establish a confirmed specificity effect.

The self/operator-name primary cell has **106 errors**, not 151: 69 foreign-current,
27 revoked-target and 10 revoked-other. Thus foreign-current choices are **65.09%**
of its errors; the two revoked categories together are **34.91%**, and only the
revoked-target category (**25.47%**) is the old command of the queried account.
By comparison, foreign-current choices account for **95.80%** of self/possessive errors.
These are different output distributions, not evidence of two identified internal defects.

Before any update, the own operator-name control reaches **43/64 = 67.19%**. In the
history-free current snapshot it reaches **70/128 = 54.69%**. All four operator-name
lookup cells in this block are below the eventual 80% requirement. All four account-name
lookup cells are above it, but one account-name *paired* lookup control is below it:
before/other/account-name has **25/32 = 78.12%** of ownership-swapped pairs fully correct.
Five of the eight paired lookup controls are below 80% on observed pairs, including all
four operator-name controls. The complete tables retain every control.

This pattern is compatible with difficulty following the operator → connection →
permission mapping. Naming the account directly removes one mapping step. It does not
isolate a special mechanism for self-reference. The weak controls also occur without
update history, so interference between successive grants cannot explain all of them.
This is a possible interpretation, not an identified internal mechanism.

The frozen gates apply to the full sample. Poor rates in this first block neither pass
nor formally fail those gates. They do not make eventual passage mathematically
impossible: the audit explicitly reports upper bounds if every remaining pair were
correct. No threshold or prompt has been changed in response to this block.

The required recovery is substantial. At the unchanged integer threshold, the four
operator-name paired controls require the following rates in the remaining 40 worlds:

| Paired lookup control | Observed fully correct | Required in remaining pairs | Required remaining rate | Best possible final rate |
|---|---:|---:|---:|---:|
| before / self / operator name | 11/32 | 143/160 | 89.38% | 89.06% |
| before / other / operator name | 14/32 | 140/160 | 87.50% | 90.62% |
| snapshot / self / operator name | 25/64 | 283/320 | 88.44% | 89.84% |
| snapshot / other / operator name | 31/64 | 277/320 | 86.56% | 91.41% |
| before / other / account name | 25/32 | 129/160 | 80.62% | 96.35% |

The remaining-rate and final-rate columns have different denominators. For example,
143/160 is the needed future accuracy, while 171/192 is the best possible full-sample
accuracy given 11 already correct pairs. Final thresholds require at least 154/192 or
308/384 correct pairs. These calculations express the recovery needed, not its probability.
The gate is at serious practical risk, but there is no prespecified interim futility test.

The 80% lookup requirement applies to **before and snapshot**, not the primary
after-both cell used for the 58.59% versus 53.52% comparison. Its purpose is to require
explicit operator-to-account lookup before attributing an additional difficulty to the
possessive query. The failure of that control is informative; it does not establish
that the threshold was miscalibrated or justify removing the control after observing it.

## Two denominators, kept separate

The [original fixed-sample report](../review/query-reference-block00-results/fixed-sample-report.md)
is preserved exactly. It includes the **13,440 unrun cases** in the scheduled denominator
as administrative missingness. For example, its self/possessive primary cell shows
137/1,536, whereas the observed block has 137/256. The first percentage is not the
model's accuracy on the eight completed worlds. Likewise, the original report's numeric
gate failures are not a completed-study decision. Its explicit decision remains
`incomplete_or_invalid_no_inference`.

The separate observed-block report makes the measured behavior readable without changing
that frozen accounting. The eight-world contrasts are labeled descriptive. Revoked-command
categories remain not applicable before updates and in snapshots without printed history;
null entries there are not evidence that the model never chooses stale commands.

## Verification and next step

The offline reviewer checks the pinned archive SHA-256, **79 internal file checksums**,
all 2,688 record identities, candidate/token boundaries, unique score maxima and simulator
outcomes against the text oracle. Recomputing the frozen full-sample analysis from saved
records reproduces its digest exactly. Ownership pairs are recounted from the archived
preflight pair inventory. No model inference is performed during this review.
The [verification record](../review/query-reference-block00-results/verification.json)
records seven passing review tests and byte-identical regeneration of the audit,
descriptive report and SVG/PDF/PNG figure.

```bash
uv run --no-sync python scripts/review_query_block.py
uv run --no-sync pytest -q tests/test_query_block_review.py
```

The [reporting plan before block 01](QUERY_REFERENCE_INTERPRETATION_PLAN.md) fixes how
estimates, intervals and failed controls will be presented without relabeling a failed
candidate rule as success. This clarification was written after block 00; it is not a
new preregistration. The frozen specification already requires separate E/F/S reporting.

The operational next step is to complete the remaining five blocks under the unchanged
protocol, if separately budgeted. This first block supplies no reason to alter prompts,
loosen controls or begin an internal intervention. Even a large E/F contrast in the final
sample would not satisfy the candidate rule if the lookup gates fail.

The evidence is published on `results/query-reference-block-00`. Execution must remain
at commit `59061ca` on `main` / tag `query-self-reference-v1`: the merger requires identical
execution commits across blocks. The separate results branch keeps documentation and
review code from changing that execution provenance. No additional job was submitted.
