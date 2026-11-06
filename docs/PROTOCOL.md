# Pilot protocol and technical appendix

## Constructs

We test whether interventions influence **contextual self-model use** differently from self-language. Correct role-conditioned answering is not private-state introspection. Pronouns do not measure consciousness.

Gemma 2 2B base and Gemma Scope layer-14 residual / width-16k / average-L0-84 are the initial model and SAE. Features 2728 and 10230 are historically selected candidates, not independently discovered mental functions. Historical examples are discovery material only.

## Data and scoring

Ownership, access and capability each contain 40 development, 40 validation and 100 test scenarios. Each has 32 variants: factual assignment swap × assigned actor × self/other query × four option rotations. Each split has two disjoint surface templates. All scenario variants stay together. Template diversity is limited; this is a generalization limitation.

Gold answers derive from structured states: who stamped an item, which code an actor observed, or which door remains permitted after revocation. The entire scene is visible to the model. Access tasks concern described observations, not the model's privileged access to hidden neural states.

The language assay crosses first/third person and monitoring/non-monitoring topic, using four matched variants. Length is approximately matched and actual token counts are recorded. Lexical/topic confounds are reduced, not eliminated.

Primary task accuracy is **forced choice**: highest next-token logit among A/B/C/D. Labels are checked at the actual `Answer:` boundary. The unrestricted top token and total option probability mass are retained. Invalid free-form output is a diagnostic, not exclusion from the forced-choice denominator. Execution failures invalidate confirmation evidence.

Generation uses registered seeds, temperature 0.7, frequency penalty 1.2 and at most 55 new tokens. Word metrics use only the continuation. Repeated-bigram fraction and continuation NLL under the unmodified model diagnose degradation; they do not fully measure semantic quality.

## Interventions

For residual r, the Gemma Scope encoder does not subtract decoder bias:

$$f(r)=\operatorname{ReLU}(rW_{enc}+b_{enc})\odot\mathbf1[rW_{enc}+b_{enc}>\theta],\qquad
\hat r=f(r)W_{dec}+b_{dec}.$$

Candidate directions are normalized decoder rows. The new dense direction is the difference of mean last-token residuals between monitoring/non-monitoring prompts, balanced over grammatical person, on development data only. Its name is **monitoring-topic contrast**, not validated metacognition.

$$r'=r+\alpha m v,\qquad \alpha\in\{-0.10,-0.05,-0.02,0.02,0.05,0.10\}.$$

Here v is unit length and m the saved median development residual norm. Ten seeded Gaussian unit controls are norm-matched, not matched for activation frequency or causal potency.

Choice tasks edit only the final prompt position. Generation edits all positions on every full-prefix forward pass, with KV caching disabled. These different sites limit strong cross-assay dissociation claims; site-matched follow-ups are required.

For feature ablation, preserve the reconstruction remainder:

$$e=r-\hat r,\qquad r'=r-f_i(r)d_i=\operatorname{decode}(f(r)_{i\leftarrow0})+e.$$

The decoder bias and error remainder survive. Re-encoding may still change other features because directions can overlap. Negative direction addition is not feature ablation. Combined additions use a normalized sum, maintaining the perturbation-norm convention, and remain exploratory.

Candidate cosine and least-squares projection of the dense direction onto their span are saved. These describe geometry, not independent circuits.

## Calibration and gates

Development prompts alone determine calibration/directions. Model and SAE commits, NPZ hash, vectors and median norm are saved. New experiments use unprocessed TransformerLens weights; processed weights are historical-reference-only.

Pilot thresholds: HF/TL next-token logit maximum absolute discrepancy ≤0.5, residual relative discrepancy ≤0.05, centered reconstruction explained variance ≥0.5 and mean causal loss recovery ≥0.5. Loss recovery is $(L_{zero}-L_{reconstruction})/(L_{zero}-L_{base})$ on one calibration prompt per functional family, editing non-BOS residuals. Nonpositive denominator fails. These are coarse integration thresholds, not universal SAE-quality standards.

Every family and declared subgroup requires ≥80% validation accuracy. Generator tests verify relevant role/fact changes flip correct answers. Confirmation needs full, error-free validation, calibration and post-intervention baseline integrity. Source, configuration and primary outcomes are frozen before test access. No automatic model switch follows failure.

## Estimands and inference

Average variants within each scenario s, view v and condition c first:

$$\Delta_{s,v,c}=\bar Y_{s,v,c}-\bar Y_{s,v,0},\qquad
\delta_{s,c}=\Delta_{s,self,c}-\Delta_{s,other,c}.$$

Primary outcomes are self accuracy change, other accuracy change and their difference, for each family/frozen condition. Resample scenarios for paired bootstrap intervals; seeds and variants are not independent samples. Two-sided sign-flip tests use scenario differences, assuming paired-null exchangeability. Holm corrects the primary test family. Confirmation bootstrap intervals use Bonferroni-adjusted tails across that family. Exploratory intervals are nominal 95%.

The practical-equivalence region is ±5 percentage points. Flag equivalence only when the entire adjusted interval lies strictly inside it, tail resolution is sufficient, and the bootstrap is nondegenerate. All-zero differences can yield a zero-width bootstrap interval; this is flagged and is not accepted as equivalence evidence. There is no completed power analysis; 100 scenarios may not establish equivalence after correction. Failure to establish equivalence does not demonstrate a meaningful difference.

Partial/error runs receive descriptive summaries only. Incomplete comparisons are not selectively analyzed. Language metrics and human ratings remain secondary/exploratory. A significant effect in one assay and nonsignificant effect in another is not a dissociation.

## Blinded rating rubric

At least two independent raters score continuations before seeing intervention labels:

| Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| Self-reference | None | Incidental | Sustained | Dominant |
| Monitoring language | None | Generic mention | Explicit checking/evaluation | Sustained discussion |
| Coherence | Uninterpretable | Substantial breakdown | Mostly coherent | Coherent throughout |

These judge text, not actual introspection. Preserve individual ratings, missingness and disagreement; aggregate only after coverage checks.

## Claim ladder

1. Changed outputs in selected examples: historical exploratory observation.
2. Generalization with controls: requires new held-out confirmation.
3. Selective functional influence: requires convergent evidence, equivalence where claimed, and degradation/site controls.
4. A circuit implements a function: requires targeted tracing and causal validation beyond SAE directions.
5. Phenomenal consciousness exists/does not exist: not licensed by this protocol.
