# CPU review of the completed ownership tranche

This review uses saved records only. It changes neither the frozen ownership protocol
nor its failed decision. The article remains at `article-v1`. No model or tokenizer was
loaded, and no GPU job was submitted. Proposed prompts below are inspectable artifacts,
not a new executable experiment or a passing competence screen.

Run from the repository root:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  uv run --no-sync python scripts/review_ownership_design.py
```

The script checks the three input archive hashes and the combined record fingerprint,
audits historical archived prompts, and writes
[`review/ownership-design-audit/`](../review/ownership-design-audit/audit.json).
It records source hashes and deterministic compressed prompt artifacts. All proposed
model inputs contain only prompt and choices; oracle metadata is a separate object.
The 48 now-observed worlds are used for design inspection, not called fresh data again.

## 1. Prompt parity: distinguish the two historical questions

The review request identifies a real distinction, but combines different cohorts.
The original pilot had self, named-self and other views. Only self queried “your active
connection.” The later role and Your/The experiments selected named-self rows, then
changed the context line while leaving the named query fixed.

| Archived experiment | Action inputs | Query says “your active connection” | Exact reconstruction of historical named template |
|---|---:|---:|---:|
| Original Qwen pilot, both formats | 3,072 | 1,024 | Not this audit's named-template target |
| Role control | 2,048 | 0 | 2,048/2,048 |
| Your/The control | 6,144 | 0 | 6,144/6,144 |

The 186/256 historical result belongs to the last row. Consequently, the new named
query did not replace a query-bound possessive in that comparison. This is verified
against archived inputs, rather than inferred from the conditional in `action_task.render`.
Archive paths, checksums and examples are in `historical_prompt_audit` in the JSON.

For shared Your/Reference frames, the old form was:

```text
Your active connection: Cedar.
...
Select one command that would succeed for Cedar.
Available commands:
- ...
Return exactly one command from this list.
```

The new form introduces you and observer Rowan, shortens the task instructions and
event syntax, and uses `Query account: Cedar` followed by a fixed question and
`Selected command:`. Labels/worlds and actor-order allocation also differ. A saved-data
comparison cannot identify which change caused the accuracy increase.

Two distinct CPU artifacts address the two questions without confusing them:

- `named_template_pairs.jsonl.gz`: **12,288** current Your/Reference cases paired with
  the historical named-query renderer. The scene, target, choices and correct answer
  are shared; the template bundle changes. This restores template parity for the
  quoted historical result. Their has no historical counterpart and is excluded.
- `query_reference_probes.jsonl.gz`: **9,216** self/named-self/other proposals based on
  Your/target rows. Self and named-self have the same assigned actor and correct answer;
  other queries the other account and changes the oracle and update relevance.
  This restores the original pilot's query-reference comparison as a separate question.

Simply putting “your active connection” into a question whose context names the other
account would change the queried entity. Retaining the old target's answer key would
then mis-score a correct response. The proposals explicitly avoid that substitution.
No claim about Qwen's responses to either artifact has been made. Both would need a
new versioned protocol, token-boundary checks and fresh assessment worlds before
model evaluation; their current purpose is semantic inspection.

## 2. Scripted baselines on the actual new template

The policies use the saved task states, with exactly the draft's meanings for
`latest_grant_or_first` and `ignore_update`. “Always active actor” is defined only in
Your rows: Their defines Rowan's connection, and Reference supplies no owner.
`context_named_actor` is the explicit cross-frame policy, not a silent reinterpretation
of active ownership. Tests compare the corresponding rates with the unchanged
`action_task.design_summary` helper.

| Policy | Before accuracy | Relevant-update accuracy | Irrelevant-update accuracy |
|---|---:|---:|---:|
| latest_grant_or_first | 25% | 100% | 0% |
| ignore_update | 100% | 0% | 100% |
| context_named_actor | 50% | 50% | 50% |
| always_active_actor (Your only) | 50% | 50% | 50% |

The context-named policy gets every target-named case right and every other-named
case wrong. This contrasts with the observed relevant-update Your pattern, where
other-named accuracy is higher. No single one of these deterministic policies describes
all the model's answers.

The latest-grant policy agrees with **4,474/4,608** relevant-update predictions and
**2,442/4,608** irrelevant-update predictions. Its relevant-update agreement is also
model accuracy there: the latest grant is the correct answer. Its irrelevant-update
agreement is also the foreign-command error count: the latest grant belongs to the
other account. Thus **52.99%** agreement in the latter stratum is compatible with
recency, but does not establish that 52.99% of decisions were *caused* by recency.
All 18 cells, three stratum aggregates and policy coverage denominators are in the JSON.

The categorical audit distinguishes observed and structural zeros. `revoked_target`
is applicable in **4,608** relevant-update cases and structurally inapplicable in the
other **13,824** cases. In the former, none of the observed errors select the revoked
target command. In the latter, the target's original permission remains current.
Those structural zeros cannot rule out ignoring updates, and the historical relevant
zero is not evidence about irrelevant-update controls.

## 3. Endpoints: retain total errors as well as their direction

The [results addendum](QWEN_OWNERSHIP_RESULTS.md#ceiling-arithmetic-what-this-negative-result-can-distinguish)
derives the conditional error-budget bound. At the observed accuracies, the categorical
contrast lies within **[−3.125, +2.691] pp**, regardless of how errors are redistributed
between categories. This explains the limited available magnitude without turning
an observed ceiling into a pre-run constraint. High other-named accuracy alone does
not impose the claimed positive ceiling.

The historical Your/target error is **70/256 = 27.34%**; the tranche's is
**33/768 = 4.30%**, a **6.36-fold** reduction. The 29.3% and 6.8-fold values in the
review request do not follow from those counts. This comparison concerns one stratum
under bundled template/world changes, not general competence or a causal explanation.

For a future protocol, retain both per-frame and pooled quantities:

\[
 D_f=A_{f,O}-A_{f,T}=e_{f,T}-e_{f,O},\qquad
 E_f=q_{f,T}-q_{f,O}.
\]

With \(r=e-q\) for all remaining errors, \(D_f=E_f+r_{f,T}-r_{f,O}\).
The current pooled values are **D = −0.434 pp**, **E = −0.391 pp** and residual
**−0.043 pp**. This equality prevents interpreting a composition shift as a change in
total task performance. Conditional error shares should also retain their error
denominators; they are undefined, rather than zero, in an error-free cell.

**Prospective recommendation:** make accuracy gap and the all-selection foreign-command
contrast co-endpoints, retain the full error composition, and report ceiling budgets
alongside them. Accuracy itself remains ceiling-limited. Adding it cannot rescue
the current failed criterion. A future protocol must specify a joint decision and
multiplicity handling before assessment; this review sets no new success threshold.
The existing +10 pp rule and failed competence gate are unchanged.

A pure additive frame effect cancels within each target-minus-other subtraction.
Averaging across frames can further cancel oppositely signed interactions. It is
therefore wrong to read a small pooled endpoint as absence of all wording effects.
The following supplementary contrasts average mention relations, resample the same
48 independent worlds 10,000 times with seed 1729, and use **nominal, unadjusted 95%
bootstrap intervals**. They were selected after the outcomes were known.

| Stratum | Your − Reference, pp | Their − Reference, pp |
|---|---:|---:|
| Before | −8.59 [−10.68, −6.64] | −5.21 [−7.42, −3.12] |
| Relevant update | +0.07 [−0.78, +0.85] | +0.59 [−0.33, +1.50] |
| Irrelevant update | −3.19 [−5.86, −0.65] | +4.10 [+1.56, +6.77] |

There are clear descriptive frame differences, including before any update, but
their direction depends on the stratum. These six comparisons are not additional
confirmatory tests or a successful replication of the frozen categorical prediction.
The JSON retains positive/negative world counts and all frame means.

## 4. Gate proposal: separate lookup from temporal interference

The current result remains **6/12 passing competence cells**; all irrelevant-update
cells fail. The hard control is scientifically relevant: resisting an unrelated update
is part of correct account tracking. Its failure cannot be removed retrospectively
to obtain a passing study. Calling it a construction check does not establish that
the model is competent at the intended dynamic task.

A future, explicitly narrower lookup gate can use **before-update cases plus a
current-permissions snapshot**. `current_snapshot_controls.jsonl.gz` supplies **3,072**
unrun proposals, with only the two current permission records, a named target and
the same choices. It removes the change narrative and ownership context; there is
no newly granted distractor singled out by an event. This checks lookup and the
answer interface, not whether a model correctly applied a change.

Keep the irrelevant-update stratum as a separate temporal-interference diagnostic,
with its failures visible. Before claiming dynamic tracking competence, another
control must independently vary event order/recency and which account is queried,
instead of making the latest grant always either the answer or its foreign-account
distractor. That extension needs its own semantic/oracle and shortcut review.
Neither the proposed snapshot nor a moved gate licenses a new activation patch.

## 5. Their: an owner contrast with a reference-resolution requirement

“Their active connection: X” assigns X to Rowan, following the explicit antecedent
sentence. “Your active connection: X” assigns X to the addressee. They do not merely
rename the same owner; this is also different from the historical Your/The control.
The named query can be answered from the permission records without resolving
either owner, but the ownership and antecedent information still changes the input.
The observed effect of that line does not identify whether ownership, wording or
reference resolution produced it.

`their_reference_probes.json` contains ten unrun examples: two owner assignments,
each queried through Your, Their, Rowan's name, the addressee's account name and
Rowan's account name. Both owners are explicitly bound. Their/Rowan/named-Rowan
query the same target; Your/named-you query the same target. Swapping ownership
changes which answer is correct for a possessive query. Current permission snapshots
isolate this semantic check from update recency.

These examples use the smallest recorded after-update row ID, independent of model
response; they are illustrative, not a preregistered sample. Before a future ownership
comparison, they motivate balanced same-target aliases, counterbalanced owner names
and assignments, and a check that owner swaps change answers when they should.
They do not establish that Qwen can or cannot resolve Their.

## What is ready, and what is not

The CPU audit and inspectable prompt proposals are complete. They clarify the ceiling,
cohort mix-up, update shortcut and category applicability. They do not determine why
performance changed, estimate a causal fraction of recency, or restore a passing
functional-self-model baseline. Proposed gates and co-endpoints are not frozen.
No Mistral/routing experiment, article revision or inference is part of this work.

The next scientific decision is which question to preserve: reproducing the historical
named-query context effect or returning to query-bound self-reference. The artifacts
make that distinction reviewable without paying for another broad batch. Any assessment
after adapting this design requires new worlds; these 48 have now informed the review.

## Verification

The targeted command passes **20 tests**, including eight new review tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  uv run --no-sync pytest -q tests/test_ownership_design_review.py \
  tests/test_ownership.py tests/test_ownership_cloud.py
```

The checks cover the conditional ceiling and its counterexample, historical reconstruction,
query/owner swaps with changed answer keys, baseline semantics and saved-data reaggregation.
A second script invocation reproduces all five output files byte-for-byte. An additional
CPU check verifies the correct answer and input/metadata separation in all 24,576 exported
template-pair, query-reference and snapshot entries. The ten Their examples have explicit
same-target alias and ownership-swap tests.

The unchanged `scripts/review_ownership_evidence.py` also passes again for all 18,432
records and 48 worlds. Git comparisons verify that `docs/article/`, both frozen design
specifications, the replication supplement, `src/`, preflight inputs and all existing
evidence/result artifacts remain unchanged. Ruff and local document-link checks pass.
The complete suite also passes with the same offline/thread settings:
`uv run --no-sync pytest -q` — **211 passed in 594.75 s**. These include synthetic
software/tiny-model tests; no new study-model responses were generated.
