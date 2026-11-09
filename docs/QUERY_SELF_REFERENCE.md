# Query-bound self-reference: protocol v1

**Execution update:** [Block 00 is complete](QUERY_REFERENCE_BLOCK00_RESULTS.md), with 2,688 valid selections in eight of 48 worlds. The study remains incomplete; the pre-run freeze and its verification records below remain unchanged.

**Decision:** pursue query-bound self-reference from the original pilot. The question is
whether asking for **your active connection** changes account selection relative to
naming **that same connection**, with matched third-person aliases as controls.
The named-query context-line branch is closed as a follow-up priority. Named questions
remain necessary controls here; they are not a second experiment on context-line wording.

This is `query-self-reference-v1`. The unchanged
[original JSON](../designs/query-self-reference-v1.json) records the question, prompts,
directions, sample, controls and decision rules against evidence commit `381c7e6`.
Its historical draft metadata is preserved. The separate
[freeze record](../designs/query-self-reference-v1.freeze.json) now seals that scientific
content, the prepared inputs and tested execution code. The
[execution runbook](QUERY_SELF_REFERENCE_RUNBOOK.md) documents commands, eligibility
details and remaining launch steps. No pretrained assessment, paid allocation or article
revision is implied by this software freeze. Previous failed decisions remain intact.

## Why this question, and what the evidence does not establish

The ownership tranche did not confirm its frozen prediction. It did expose substantial
descriptive frame differences. The reported before-update Your−Reference contrast
was **−8.59 pp [−10.68, −6.64]**, a post hoc nominal interval in that dataset.
Comparing it with historical **after-relevant-update, other-named** cells mixes both
checkpoint and mention relation; that comparison alone does not establish reversal.

A matched descriptive comparison *does* reverse: the historical Your/The cohort's
before-update Your accuracy was **1,016/1,024**, Reference **1,000/1,024**, averaging
the two mention relations equally. Thus its Your−Reference difference was **+1.56 pp**,
versus **−8.59 pp** for the same aggregate in the tranche. These counts are reproduced
from archived records by the [structural checker](../scripts/check_query_reference_protocol.py).
They show sensitivity across bundled template/world changes, not the cause of reversal
or an independently replicated, stable frame effect. Before updates there is no newest
grant, but another account's command and the unused commands are still distractors.

The proposed question has a different evidential starting point. In the original chat
pilot, relevant-update self accuracy was **67.97%**, named-self **69.53%**: a **1.56 pp**
same-target alias gap. The corresponding foreign-command errors were **36/128** and
**33/128**. See the [original pilot results](QWEN_RESULTS.md). The large historical
context-mention gap is not an expected effect size for this query-form comparison.
The directions below are prospective hypotheses; these observations do not guarantee
their recurrence, useful precision or a practically large effect.

## Task and matched references

Use the same pinned Qwen2.5-7B-Instruct model and tokenizer revision
`a09a35458c702b33eeacc393d103063234e8bc28`, BF16, official chat, batch one and complete
summed command likelihoods. One permission task, no new model or internal intervention.

Every prompt explicitly names both operators and binds each to one connection. One
operator is the addressee; the other is the stated antecedent of “their.” Both bindings
remain in every query condition. An illustrative fixture, **not an assessment world**:

```text
Your operator name is Rowan. The other operator is Morgan.
In this task, the word their refers only to Morgan.
Owner bindings:
Rowan's active connection: Cedar.
Morgan's active connection: Birch.
```

For each queried owner, render three questions while keeping the context and answer fixed:

| Queried owner | Possessive query | Owner-name alias | Direct account alias |
|---|---|---|---|
| Self | your active connection | Rowan's active connection | Cedar |
| Other | their active connection | Morgan's active connection | Birch |

The question is `Select one command that would succeed for {query_reference}.`
The direct account alias is the reference condition; there is no separate
`Reference connection` context-line arm. Same-target comparisons change only the query
reference. Switching from own to other account changes the correct answer and oracle.
The literal name Rowan is not permanently associated with the other owner: Rowan and
Morgan each name the addressee in 24 worlds and the other operator in 24. Owner-to-connection
assignments cross within every world. These are two fixed operator names, not a claim
of generalization over arbitrary antecedents.

Possessive versus owner-name aliases examines pronoun resolution; owner-name versus
account-name aliases examines the extra owner-to-connection lookup. Neither is an
equal-token substitution. Even a differential cost may reflect language processing or
reference resolution; it does not establish a privileged self-monitoring mechanism.

## Break the newest-grant shortcut without hiding the hard cases

Initially each account permits a distinct command. Two other commands are available as
replacement grants. The main checkpoint follows **two updates, one per account**; both
event orders occur with equal weight. Both orders produce the same final state.

For example, Cedar changes from `mark_silver` to `mark_amber`, and Birch from
`mark_ivory` to `mark_violet`. Asking for Cedar must yield `mark_amber` whether its
update is first or last. Asking for Birch must yield `mark_violet` in either order.
Unlike the completed tranche, “latest grant” and “other account's current command”
are not always the same option. The latest-grant policy has **50% rule-level accuracy**
in this balanced primary stratum. That arithmetic is not a model-performance result.

Three checkpoints have distinct purposes:

| Checkpoint | Contents | Planned choices per world | Purpose |
|---|---|---:|---|
| Before | Initial permissions; no update | 48 | Initial lookup and alias controls |
| Snapshot | Final current permissions; no event history | 96 | Lookup without update chronology |
| After both | Initial permissions and both ordered updates | 192 | Primary dynamic reference test |

The snapshot has no event-order factor; before has neither event-order nor grant-mapping
factors. Identical prompts are not multiplied by invisible future events. Final grant
mapping, owner-to-account assignment and answer position are crossed where applicable.
The exact two-update task is a **measurement redesign**, not an exact replication or
repair of the old pilot. It preserves the query-bound reference question while removing
the deterministic latest-grant/foreign-command coincidence in the primary stratum.
Remaining event-order effects stay visible.

## Co-endpoints and decisions, before responses

For world \(w\), owner \(o\) and query form \(a\), let \(A_{w,o,a}\) denote accuracy and
\(q_{w,o,a}\) the fraction selecting the other account's current command. Use all scheduled
selections, including invalid/missing outcomes in the denominator. Average all factorial
variants equally within a world in **after both**, including both event orders.

The two co-primary quantities are:

\[
E_w=q_{w,\mathrm{self},\mathrm{possessive}}
    -q_{w,\mathrm{self},\mathrm{account}},
\qquad
F_w=A_{w,\mathrm{self},\mathrm{account}}
    -A_{w,\mathrm{self},\mathrm{possessive}}.
\]

**Directions fixed in advance:** \(E>0\), more foreign commands under query-bound Your;
\(F>0\), lower accuracy under Your than the explicit name of the same account.
The frame contrast is thus a co-endpoint, not an appendix diagnostic. It is a **query**
frame contrast, not a claim to replicate the old Your/Reference context contrast.

The separately identified specificity contrast is also fixed in advance:

\[
S_w=F_w-\left[
A_{w,\mathrm{other},\mathrm{account}}
-A_{w,\mathrm{other},\mathrm{possessive}}
\right],\qquad S>0.
\]

It asks whether the own-reference cost exceeds the matched Their-reference cost.
Without support for \(S\), positive \(E,F\) cannot be described as an own-specific deficit.
Report all six owner/form cells, including the owner-name aliases, regardless of outcome.

For each quantity average the 48 world estimates. Use 10,000 paired world-bootstrap
draws, seed 1729, for nominal 95% intervals. Test \(E,F,S\) with two-sided paired-world
t tests, 47 degrees of freedom, and **Holm correction over all three tests** at 0.05.
The t reference is a normal-mean approximation, not an exact randomization test.
Zero variance makes that test inconclusive, with an undefined raw p-value. Use 1 only
as a labeled conservative placeholder for its Holm family entry; an undefined test
cannot qualify. No invented standard error or equivalence claim follows.

- A **reference-sensitive own-query candidate** requires complete data, passed lookup
  gates, positive \(E,F\), positive nominal bootstrap lower bounds for both, and both
  Holm-adjusted p-values at most 0.05.
- An **own-versus-other specificity candidate** additionally requires that same
  directional/interval/adjusted-test rule for \(S\).
- Otherwise report partial, negative, technically incomplete or gate-failed outcomes
  as applicable. No successful checkpoint or event order is selected after the fact.

There is no borrowed +10 pp cutoff, equivalence test, power guarantee or optional sample
enlargement. Magnitudes and intervals determine how small or uncertain a detected
difference is. \(E,F\) may be nearly identical if foreign commands dominate errors;
meeting both rules is not independent replication. Their difference is the contrast in
remaining errors. Both remain ceiling-limited: always show total errors and algebraic
bounds, including error-free cells. Conditional error shares are undefined when no errors
occur. Before/snapshot contrasts, score margins and all order-specific effects are
predeclared descriptive results, not substitute endpoints.

## Gates, error categories and interpretation

The lookup gate requires at least 80% accuracy in **each owner × named-form cell** for
before and snapshot: owner-name and direct account aliases, eight cells in total.
For those named controls, at least 80% of owner-swap changed-answer pairs and fixed-account
invariance pairs must be fully correct, evaluated separately by checkpoint, owner and
named form. Possessive errors remain study outcomes and are not screened away.

Build each control pair once, anchored at owner-to-connection assignment 0. Its counterpart
uses assignment 1, with task state, options and question text unchanged. For an owner-name
query the correct command changes; for a fixed account-name query it stays the same and
the queried owner's role changes. Classify that pair by the anchor owner's role, rather
than counting both orientations as separate evidence.

This gate establishes only explicit alias/permission lookup. Report after-both named
controls by event order as dynamic diagnostics. Passing before/snapshot cannot establish
reliable update tracking, excuse failures there or unlock an internal intervention.

Retain invalid responses, correct current target commands, current foreign commands,
revoked target commands, revoked other commands and remaining valid commands. Revoked
categories apply only where event history exists, **after both**. In before/snapshot,
mark them not applicable rather than presenting structural zeros as observed evidence.
Ties remain invalid; no arbitrary winner. Incomplete or failed scoring cannot pass.

The experiment concerns a contextual reference used to choose an action. It cannot
establish subjective experience, internal-state introspection, general agency or human
illusionism. Those remain motivation and later interpretation, not measured endpoints.

## Fresh sample, CPU preparation and reporting

The proposed fixed sample is **48 new worlds**, namespace `query-self-v1`, seed 731903:
**16,128 selections**, partitionable into six blocks of eight worlds. These are design
counts, not jobs or a cost quote. The 9,216 earlier probes over observed ownership worlds
are semantic examples only; none becomes a new assessment case.

The JSON specifies label pools and hash ranking. Permission-record order, binding order
and operator-name role assignment use eight balanced nuisance combinations, six worlds
each. Correct-answer positions rotate within each world; both owner-to-account mappings
and final-grant assignments are crossed. A new ID alone does not establish freshness.
Reject duplicate account/command fingerprints and historical input overlap before running.

A preliminary CPU check found an unordered account/command-set collision in the initial
eight-account-label draft. Before any inference or freeze, the pool was explicitly
expanded to sixteen labels; the seed stayed fixed. The present draft has 48 unique sets
and no account-pair overlap with the checked historical action cohorts. This was a
documented design revision, not silent resampling or model-guided selection.

Reproduce the **partial structural audit**:

```bash
uv run --no-sync python scripts/check_query_reference_protocol.py
```

Its [output](../review/query-self-reference-protocol-check.json) checks inventory arithmetic,
balanced nuisance assignments, account-set uniqueness, historical account-pair separation,
the latest-grant rule and the matched historical before contrast. It does **not** claim
that rendered inputs or token boundaries have been checked.

The isolated generator, text-first oracle and complete input/token preparation are now
implemented. The [CPU preparation report](QUERY_SELF_REFERENCE_PREFLIGHT.md) records
the actual checks and artifacts; the older partial check above remains unchanged.
The scientific JSON remains byte-identical to the reviewed draft; the separate freeze
record governs execution. The first block now has observed responses, linked above;
the complete fixed sample remains unrun.

The implementation makes the order convention explicit: permission records start in
hash-ranked account order; owner bindings start in the declared Rowan/Morgan order.
Nuisance bits 0 and 1 reverse those respective lists. Bit 2 independently determines
which operator is the addressee. This resolves rendering order without changing the
reviewed assignments, wording, factors or endpoints.

For every candidate, preparation requires exact prefix token agreement, exact decoded
continuation and a total length at most 2,048, with no truncation. It saves rendered
text, token IDs/lengths, the official default system text, template and package hashes.
Unequal command lengths do not license post hoc length normalization. Reproduce all
inputs and check an existing artifact directory byte-for-byte with:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --no-sync python scripts/prepare_query_reference.py
```

This command uses only the locally cached pinned tokenizer. It cannot load model weights,
perform inference or submit a job. If a saved artifact differs, it stops without overwriting
it; use `--out` with a new directory to inspect a proposed revision.

The future report must show \(E,F,S\) together, all alias cells, event-order splits,
world-level effects, error composition/applicability and failed gates. Include a diagram
of the actual query/ownership manipulation and SVG/PDF/PNG plots from saved records.
Freeze the generator, manifest, scoring, resume/analysis tests and this specification
before assessment responses. Only then prepare a current quote for a separately
authorized run. Mistral, routing, steering and article rewriting are outside this step.

The initial protocol-writing verification covered the partial structural checker and eight
ownership-review tests. The new implementation's verification is listed separately in the
[CPU preparation report](QUERY_SELF_REFERENCE_PREFLIGHT.md). Runtime scoring, interrupted-run
resume, world-paired statistics, report generation and synthetic failure tests are now
complete in the
[execution handover](QUERY_SELF_REFERENCE_RUNBOOK.md); see the
[verification record](../review/query-self-reference-execution-check.json).
Input correctness alone does not establish model competence or authorize paid execution.
