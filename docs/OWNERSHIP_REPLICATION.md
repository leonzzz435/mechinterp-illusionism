# Role-binding replication — frozen specification, not executed

`ownership-replication-v1`, frozen locally on 2026-11-08 against evidence commit
`36d9a068b661dff04cf1fa4a29ea47c4f8f48376`.
The normative [JSON](../designs/ownership-replication.json) fixes sampling, exact prompt
templates, models, outcomes, decisions and limits. This is a Git predeclaration, not an
external preregistration. There is no adapter, sample manifest, tokenizer audit or new
inference for this protocol yet. No job submission or spending is authorized by this file.

## Question and existing evidence

Does naming the queried account increase selection of the *other account's currently
successful command*, across wording, executable task rules and models?
The [latest four accuracy cells](QWEN_POSSESSIVE_RESULTS.md#primary-result-and-mathematics) motivate the
question; [the original post hoc error count](QWEN_RESULTS.md) motivates its direction.
The latter report, line 80, counts other-account commands in 36/41 self-directed and
33/39 explicitly named-target errors. The later Your/The report does **not** contain an
aggregate replication of those categorical counts. That is what this new endpoint tests.

## Frozen design

| Component | Choice before execution |
|---|---|
| Independent units | 48 fresh latent worlds, paired across both templates and models |
| Selection | Seed 94173; hash-ranked actor/command labels; exact algorithm in JSON |
| Models and tokenizers | Qwen2.5-7B-Instruct at `a09a35458c702b33eeacc393d103063234e8bc28`; Mistral-7B-Instruct-v0.3 at `c170c708c41dac9275d15a8fff4eca08d52bab71` |
| Execution | BF16, no quantization, batch 1, official chat, maximum 2,048 tokens without truncation |
| Wording | Your / Their / Reference connection; context names target or other account |
| Task templates | Permission replacement; command routing to ACCEPT versus HOLD |
| Balancing | Target identity, updated identity, before/after, alternative grant and option rotation |
| Inventory | 384 selections per world/template/model; 48 × 2 × 2 × 384 = 73,728 |
| Score | Full-command summed log-likelihood; exact continuation, no added space/EOS or length normalization |

The second template changes the executable outcome: a command routes a message to an
inbox rather than passing a permission check. Both still share an abstract two-account
binding problem, so success would demonstrate limited generalization, not broad agency.
The official [Mistral checkpoint](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3/tree/c170c708c41dac9275d15a8fff4eca08d52bab71)
was pinned through repository metadata; no new-model capability or speed was measured.

“Their” has a fixed antecedent, observer Rowan, introduced identically in every condition.
That shared introduction is a new context and must remain visible in the report.
Your/Their/Reference is not the historical one-token Your/The substitution; Reference
also changes length and meaning. New actor labels and prompt-overlap checks precede any
model evaluation. A collision blocks this version instead of triggering silent resampling.

## Categorical endpoint and decisions

Classify every scheduled selection, in this order: invalid; correct current target command;
current other-account command; revoked target command; remaining recognized command.
The categories are mutually exclusive, and the denominator includes failures rather than
conditioning on having made an error. The primary stratum is after a target-relevant update.

For each world, model and template, average across the three wording frames:

$$E=\frac{1}{3}\sum_f\left[
P(\text{other command}\mid f,\text{target named})-
P(\text{other command}\mid f,\text{other named})\right].$$

Keep all variants of a world together in 10,000 paired bootstrap draws (seed 1729).
Report each model × template separately, including the full categorical distribution.
The primary four tests use paired-world t statistics with 47 degrees of freedom and Holm
correction; this normal-mean approximation is an assumption, not a randomization test.

A cross-model, cross-template replication requires **all four** estimates at least
10 percentage points, all nominal 95% bootstrap lower bounds above zero, all Holm-adjusted
p-values at most 0.05, complete coverage and passing competence controls.
Controls require at least 80% accuracy before updates and after irrelevant updates in
each model/template/frame/context cell. Relevant-update errors are the outcome and cannot
be screened out for being difficult. Partial recurrence is reported as partial recurrence.

### Equivalence is a separate decision

For each model/template, compare the target-minus-other error contrast for Your versus
Their and Your versus Reference. Fix a ±5 percentage-point equivalence margin in advance.
Use paired-world TOST with t reference (47 degrees of freedom), taking the larger of the
two one-sided p-values; apply Holm to the eight equivalence tests at alpha 0.05.
Report point estimates, unadjusted 90% intervals, both component p-values and adjusted
TOST p-values. Only an adjusted TOST p below 0.05 licenses that particular equivalence claim.
Failure to establish equivalence is not evidence of a difference. For an entirely zero cluster contrast, the frozen exact TOST fallback uses
`p_lower = p_upper = (1 - 0.05 / 2)^48`, with the same Holm adjustment; other zero-variance
t-based decisions remain inconclusive. This follows because these differences of error contrasts lie in [−2, 2],
so an absolute mean of at least the margin requires at least half that probability of a nonzero
contrast; observing none has probability at most `(1 - margin / 2)^n`. Report that zero-event
bound instead of a t interval. Role-error recurrence does not establish wording equivalence.

## Stops, budget and implementation boundary

Stop on model/source drift, prompt overlap, oracle ambiguity, token overflow or nonfinite
scores; preserve completed records and errors. Ties are invalid outcomes, not arbitrary
winners. Incomplete coverage cannot pass. Do not replace a model, retune a prompt, enlarge
the sample or change thresholds after seeing outcomes.

The inventory partitions into twelve jobs: three consecutive blocks of sixteen worlds
for each model/template, with 6,144 selections per job. Each has a 90-minute cooperative
limit and a two-hour provider limit; no automatic extension or retry follows a timeout.
These are prospective limits, not jobs created by this specification.

Using the historical 6,144-choice invocation of 2,567.35 seconds and the recorded L4 rate
of $0.013333/minute ([execution record](QWEN_POSSESSIVE_RUN.md), lines 10–12 and 25–29),
equal-speed extrapolation gives 513.47 minutes, or 770.205 with a chosen 50% contingency:
roughly **$6.85–$10.27** for that estimated compute time.
Twelve historical two-hour quotes of $1.613293 yield a **$19.36 compute ceiling at that rate**;
the proposed total budget is **$25, authorized spend $0**.
Mistral, routing prompts, setup and exports may differ; this is neither a current quote nor
a guarantee of completion. Re-quote before a separately authorized launch.

CPU simulator/renderer tests, exact manifests, input-disjointness and token-boundary audits
must be committed before inference, without model-based prompt selection. Any substantive
change to this specification needs a new version and an explanation before exposure.
Precision for the equivalence margin is unknown; an inconclusive result is allowed.

JSON SHA256: `d1024e5384ad233be1c41d6cb248c0bd92a2615ea1ac7b9553d88a571358d996`.
