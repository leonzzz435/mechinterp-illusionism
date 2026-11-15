# Query-reference v2 offline amendment: retrospective tie sensitivity

**2026-11-09, after all 48 worlds and the tie outcome were inspected.** This is an
exploratory reanalysis of saved outputs, not a preregistered replacement experiment.
The frozen v1 design, records, manifests, report, decision and `article-v1` remain
unchanged. No model is loaded and no cloud job is authorized or needed.

The all-or-nothing v1 validity rule withholds inference for the entire sample when
one complete world contains a tied selection. That is a brittle rule for describing
otherwise recorded behavior, rather than missing data. This amendment permits an
explicit sensitivity analysis; it does not retroactively make v1 eligible.

## Analyses to retain together

1. **Frozen v1, 48 worlds:** retain its failed-selection treatment, estimates and
   withheld intervals/tests exactly.
2. **Whole-world exclusion:** remove every variant of world `query-self-v1:0011`,
   leaving 47 worlds. Recompute E/F/S, cells and controls. Selection of this world is
   outcome-dependent; the resulting uncertainty is exploratory.
3. **v2 offline, 48 worlds:** among commands tied for the exact maximum summed
   log-likelihood, select a command only when exactly one has the saved boolean
   `native_is_greedy: true`. Otherwise the tie stays unresolved and statistical
   eligibility remains blocked. Unique maxima are unchanged; near ties are never
   rounded into equality. No length normalization, answer-key access, option-order
   tiebreak or newly generated output enters selection.
4. **Other tied-command assignment:** also report the alternative maximal command
   in this single observed tie. This is a sensitivity bound, not another selection
   policy or a second chance at a favorable result. The two assignments exhaust the
   possible categorical resolutions of this tie.

The tied record is in the self/possessive primary cell. The uniquely marked command,
`mark_ochre`, is correct; the other, `mark_silver`, belongs to the other account. Both
outcomes were known when this policy was chosen. Preserve the original status, scores,
candidate flags, derived choice and all tie assignments in the supplement. Original
raw validity remains 47/48; only the derived v2 analysis resolves all 48 worlds.

## What the stored greedy flag establishes

In the pinned harness, `native_is_greedy` checks whether **every candidate token**
matches the tokenwise argmax along its scored, teacher-forced continuation. It is not
an answer token index, an observed generated response or a guarantee that generation
would stop after the command. The stored record contains no EOS evaluation or sampled
response. Equal summed scores also do not locate the source of rounding or establish
that a specific numerical mechanism caused the equality.

The [Confidence-v2 precedent](QWEN_CONFIDENCE_V2.md) used the lowest vocabulary token
ID among tied **single-token** menu choices, before assessment exposure. It motivates
explicit tie handling, but neither that rule nor its prospective status transfers
unchanged to this multi-token, already-inspected sample. The new rule is identified
as `exact_max_then_unique_stored_greedy`; unresolved ties do not get a fallback.

## Statistics and unchanged claim boundaries

For each resolved sensitivity dataset, average variants within each world first.
Use 10,000 paired world-bootstrap draws, seed 1729, nominal percentile 95% intervals,
and two-sided one-sample t tests on world contrasts with n−1 degrees of freedom
(46 for the exclusion, 47 for the full sample). Apply Holm across E/F/S within each
analysis. These are **post hoc sensitivity statistics**, not confirmatory p-values;
Holm does not correct for choosing this amendment or inspecting multiple analyses.
Report every analysis together, with no selection by significance. Undefined tests
remain undefined. Alias contrasts receive descriptive intervals, not additional tests.

Keep all 80% accuracy and paired-control requirements. The tie occurs outside the
before/snapshot lookup controls, so its resolution cannot repair their failures.
The derived full-sample decision remains `lookup_gate_failed`. Estimating S does not
require passing that gate mathematically; the frozen specificity-candidate claim does.
No label, including the protocol's gated `reference-sensitive own-query behavior`
candidate, is awarded by bypassing its failed requirements. Describe query-form
differences and unsuccessful explicit alias controls directly.

Distinct error distributions do not identify distinct internal defects or a functional
dissociation. Behavioral reference sensitivity does not establish a mechanism of human
illusionism. The article stays frozen; the new results belong in a linked addendum.

Reproduction uses `scripts/analyze_query_sensitivity.py` on the six unchanged archives.
The resulting JSON, report and SVG/PDF/PNG figure are saved separately under
`review/query-reference-sensitivity/`.
