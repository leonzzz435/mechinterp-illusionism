# Reporting decision after block 00, before block 01

**Status: 2026-11-09.** This clarification follows inspection of the eight completed
worlds in the [block-00 report](QUERY_REFERENCE_BLOCK00_RESULTS.md). The other 40 worlds
have not been run. It is a reporting commitment made after observing block 00, not a
new preregistration. It changes no prompt, endpoint, threshold, world, model or stopping
rule in the [frozen specification](../designs/query-self-reference-v1.json).

## Deliverable and decision

Complete the remaining five blocks under the unchanged protocol once their aggregate
budget is authorized. The deliverable is the full 48-world comparison of query forms,
its uncertainty and the explicit outcome of the lookup controls. Completion is useful
even if those controls fail; it is not a promise of a passing candidate rule.

| Final data and controls | Required report | Claim boundary |
|---|---|---|
| Complete, valid worlds; lookup gates pass | E, F and S, their intervals and tests; every control and secondary contrast | Apply the frozen joint candidate rule and the additional specificity rule as written. Passing lookup alone is insufficient. |
| Complete, valid worlds; lookup gates fail | The same E/F/S estimates, intervals and tests, plus the failed cells and paired controls | Report query-form effects with unsuccessful explicit alias controls. The candidate rule failed even if an individual contrast passes its statistical criteria. |
| Incomplete or invalid worlds | Coverage, errors and clearly separated observed-case descriptions | No inferential intervals, tests or final candidate conclusion from the partial sample. |
| Complete data with a degenerate contrast | Preserve its estimate and the frozen analysis's interval/status | An undefined test remains undefined and cannot qualify; do not manufacture a p-value. |

This reporting is already required by `analysis.partial_results`. In the
[frozen analysis implementation](../src/self_model_study/query_reference_analysis.py),
inferential eligibility depends on complete, valid worlds and completed manifests;
it does not depend on passing the lookup gate. A gate failure changes the decision
to `lookup_gate_failed`, without suppressing the estimates or uncertainty.

For eligible data, keep the 10,000 paired world-bootstrap draws, seed 1729, nominal
95% intervals, paired-world t tests with 47 degrees of freedom, and Holm correction
over E/F/S. Worlds remain the independent units. The declared secondary alias
contrasts receive their world-level intervals as descriptive results; do not promote
them into replacement primary tests. Report all stages and both queried owners,
including reversals in the ordering of query forms. Do not assume a universal alias
hierarchy from the primary-stage table.

## What a failed control means

The operator-name control asks whether the model can follow an explicit
operator → connection → permission mapping. It is a substantive comparison for
interpreting an additional possessive-query cost. Its weak performance is a finding
about this task, not evidence that the frozen 80% requirement was necessarily wrong.
Keep both individual accuracy and fully-correct ownership-swapped pair requirements
in the before and snapshot stages. Do not exclude operator names or lower the gate
after seeing block 00.

The specification reserves **“reference-sensitive own-query behavior”** as the
candidate interpretation when the lookup gates and the co-primary E/F rule pass.
Do not use that candidate label to bypass a failed gate. With failed lookup controls,
describe the measured query-form differences and the unresolved alias difficulty
directly. S is an own-versus-other interaction; neither its arithmetic nor its sign
isolates a self-reference mechanism. None of these outcomes establishes a functional
self-model, consciousness or a mechanism in the human brain. Human illusionism remains
a philosophical motivation, not a conclusion supported by a failed lookup control.

## Retrospective diagnostics stay labeled

The latest-grant policy and last-updated-account stratification were specified before
execution. The new response-agreement counts and comparison with the first of the two
grants were added after block 00 and remain retrospective descriptive diagnostics.
Similar aggregate accuracies do not establish the same response policy. Choosing an
other-account command describes the output; it does not identify the model's internal
reference resolution. Report revoked-target and revoked-other choices separately.

There is no new interim futility rule, selective continuation by condition or promise
that the weak controls will recover. The remaining data determine the complete-sample
estimates and gate outcome under the original rules. Any later redesign would require
new worlds and a separate protocol, not a reinterpretation of this sample.

## Execution and provenance

Execution remains at `59061cacf191f737689997b1bb327e75accc71fa` / tag
`query-self-reference-v1`. Results and this clarification live on
`results/query-reference-block-00`; do not merge them into the execution checkout
before the remaining blocks. The article stays frozen at `article-v1`.
The [offline audit](../review/query-reference-block00-results/observed-report.md)
retains the unchanged evidence archive and original fixed-sample export alongside
the new counts. No additional model inference was needed for this clarification.
