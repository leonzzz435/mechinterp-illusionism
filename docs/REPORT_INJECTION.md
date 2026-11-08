# Counterfeit confidence record — frozen specification, not executed

`report-injection-v1`, frozen locally on 2026-11-08 against evidence commit
`36d9a068b661dff04cf1fa4a29ea47c4f8f48376`.
The normative [JSON](../designs/report-injection.json) fixes the design; its source and
question-exclusion manifests are hash-pinned. This is a Git predeclaration, not an external
preregistration or a ready-to-run adapter. No inference, job or spending follows this file.

## One open causal question

Does altering a recorded self-confidence category change **abstention** while the model's
ability to answer the question, measured again *after* the alteration, remains equivalent?
Abstention here means choosing a scored “Abstain” option, not a content-policy refusal.
The [completed confidence pilot](QWEN_CONFIDENCE_RESULTS.md) found no behavioral candidate;
that result remains unchanged and gives no assurance this new assay will work.
This is a different, external-text intervention, not an internal activation experiment.

## Philosophical predictions and assumptions

| Account | Prediction under explicitly added assumptions |
|---|---|
| Illusionism-inspired report-mediated account | If a reconstructed report can diverge from task evidence **and the decision policy reads and uses that record**, counterfeit low versus high self-confidence changes abstention while fresh forced-answer accuracy remains equivalent |
| Restricted quality-tracking account | If the policy follows task evidence and rejects counterfeit reports, the low/high abstention contrast is practically equivalent to zero |
| HOT in general | No unique prediction for this manipulation: higher-order awareness can misrepresent first-order states; strict quality tracking is an additional restriction, not a requirement of HOT |
| GWT in general | No unique prediction without an implementation-level mapping from a textual record to workspace availability |

These are one operational contrast and its null alternative, not a decisive tournament
between theories of consciousness. Possible dissociation alone does not imply that an
injected report will affect behavior: report use is a necessary extra assumption.
The [primary-source notes](article/PHILOSOPHICAL_NOTES.md) document Dennett, Frankish,
Rosenthal and Dehaene/Changeux and explain why “HOT demands accurate confidence” would
misstate the theory. Neither outcome extends beyond an explanatory analogy to humans.

## Frozen sample and paired branches

Use 128 fresh questions from the pinned author-provided phase-1 question source, excluding
all historical assessment IDs and calibration-text overlap, hash-ranked with seed 28657.
Retain four option rotations per question. The same pinned Qwen2.5-7B-Instruct model and
tokenizer, revision `a09a35458c702b33eeacc393d103063234e8bc28`, use BF16 without quantization,
official chat, batch 1 and a 2,048-token limit without truncation.

First collect an actual answer and its natural confidence category `c` using the original
answer/confidence prompts. Categories run from 0 to 9, representing successive probability
bands. Then show the same question, options and recorded answer in every condition:

| Condition | Record shown |
|---|---|
| self_natural | “Recorded confidence for your answer: c.” |
| self_low / self_high | Same label, with the altered low/high category |
| other_matched | “Recorded confidence for another answer: c.” |
| other_low / other_high | Other-answer label with the same altered low/high values |
| no_report | “No confidence record is supplied.” |

Low is `0 if c > 0 else 1`; high is `9 if c < 9 else 8`.
Both differ from the recorded category, and low is always below high.
“False” means that we altered a real record, not that we know the model's true probability
of being correct. The other-answer label is a fabricated attribution control, not another
model's genuine estimate. No prompt explicitly orders the model to follow the report.

From each condition prefix, fork two separate passes:

1. **Forced answer:** choose among the original answer options; score against the source key.
2. **Optional answer:** answer or abstain, with payoffs +1 correct, −1 wrong, 0 abstain.

Neither pass sees the other's output. The first-order control is therefore a new measurement
after injection: simply retaining the original locked answer would make “unchanged ability”
true by construction and would not test the hypothesis.
Score full single-digit continuations without added whitespace/EOS; retain every likelihood.
Apply the already documented v2 exact-tie rule (lowest token ID among maxima), logging ties;
nonfinite scores or token-boundary failures stop the run.

Inventory: 128 × 4 = 512 question/rotation pairs; 1,024 initial answer/confidence selections
plus 7,168 post-injection selections = **8,192 selections**, or **39,424 candidate likelihoods**.
These are design counts, not observations. Rotations never become independent questions.

## Frozen decisions

Let `Z` indicate abstention and `Y` fresh post-injection forced correctness, and average
paired differences within questions before estimating uncertainty:

$$\Delta_{\mathrm{self}}=E[Z_{\mathrm{self,low}}-Z_{\mathrm{self,high}}],\qquad
K=\Delta_{\mathrm{self}}-E[Z_{\mathrm{other,low}}-Z_{\mathrm{other,high}}].$$

Use 10,000 paired question-bootstrap draws, seed 1729, nominal 95% intervals.
The sole joint prediction is a self-attributed report effect with preserved measured ability.
A candidate requires all of the following:

- Complete valid records and at least 20 distinct questions in each correct/incorrect group
  of the no-report forced branch and each answered/abstained group of its optional branch;
  a question can enter more than one group across rotations.
- `Delta_self ≥ 0.10` and its bootstrap lower bound above zero.
- Attribution control `K` has its bootstrap lower bound above zero.
- **All three** forced-accuracy contrasts (self_low−self_high, self_low−self_natural,
  self_high−self_natural) pass paired-question TOST within **±5 percentage points**,
  t reference with 127 degrees of freedom, alpha 0.05.

The equivalence decision is an intersection-union requirement: report both one-sided
p-values and 90% intervals for every contrast, and claim joint equivalence only if all
three pass. If every question contrast is exactly zero, use the frozen exact bounded-outcome
TOST fallback `p_lower = p_upper = (1 - 0.05)^128`; report the zero-event bound instead of a
t interval. For a contrast in [−1, 1], an absolute mean at least the margin requires at least
that probability of a nonzero value, bounding the probability of an all-zero sample by
`(1 - margin)^n`. Other zero-variance t-based decisions remain inconclusive.
Equivalent accuracy would not establish unchanged internal computation in every respect.

If feasibility and all accuracy controls pass and `Delta_self` itself passes equivalence
within ±5 points, report **no practically meaningful report-use effect under this injection**.
This fits the restricted quality-tracking account but does not prove HOT, or distinguish
report rejection from report ignorance. Intermediate effects, wide intervals, a generic
cue effect, altered competence or unusable baselines remain explicit outcomes.
No secondary subgroup can replace a failed joint decision.

Report every arm, answer transition, tie and category frequency. A descriptive sensitivity
analysis excludes whole questions with any tie; it never replaces the primary analysis.

## Stops, cost and open issues

Stop on source drift, a missing/changed initial answer or natural confidence, scoring error,
token overflow or resource limit; preserve completed records. An incomplete run cannot pass.
Do not change the sample, prompts, categories, tie rule or model after seeing outcomes.
If feasibility fails, report an unusable assay rather than selecting easier questions.

The historical v2 invocation took 366.10 seconds for 1,792 selections
([execution record](QWEN_CONFIDENCE_RUN.md), lines 3 and 26–29).
At equal speed, the new inventory implies 27.89 minutes, or 41.84 with a chosen 50% buffer.
Longer prompts and new dependent branches make this an estimate, not measured throughput.
Prepare at most one L4 job, 90 minutes cooperative and two hours provider limit.
The historical quote was **$1.613293 maximum compute**, including billing rounding
(same record, lines 18–19 and 79–80); proposed budget **$5, authorized spend $0**.
Re-quote before any separately authorized launch; there is no automatic retry.

Implementation, fresh source/sample manifests, branch-isolation tests and tokenizer audits
remain prerequisites. Freeze them before exposure; substantive changes need a new version.
An external record could be ignored or treated as an instruction; attribution also changes
semantic relevance. The equivalence tests may be inconclusive. None of these outcomes
establishes a privileged inner observer or settles illusionism, HOT or GWT.

JSON SHA256: `3e24cc3f3d050c12ad38d88c22dad66ad93e25206fb8ab80712e85626d538307`.
