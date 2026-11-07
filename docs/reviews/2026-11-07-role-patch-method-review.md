# Method review: what the asymmetric exchange supports

Reviewed on 2026-11-07 against commit `538d674` and the unchanged result archive
`017e6e0f78e6ae793fbdb5a7ca3a2e4055750c840cc2da2553819fafb0304207`.
This is a methodological review by the same coding assistant, supported by source inspection,
saved-data calculations and primary literature. It is **not independent external review**.
No pretrained model inference was performed.

**Recommendation:** retain the failed bidirectional decision and the descriptive one-way
finding. Before another internal intervention, isolate whether the possessive word “your”
contributes to the role gap, using an equal-length wording control and fresh development
scenarios. This addresses the meaning of the measured effect, which remains a larger obstacle
to our self-model interpretation than finding a stronger patch location.

## What survives scrutiny

The [completed report](../QWEN_ROLE_PATCH_RESULTS.md) correctly distinguishes technical
success from the failed scientific decision. All 11,264 choices and 32 repeats are present;
baselines, own-state patches and repeats have exact score parity. The primary transfer
estimate T is +2.344 pp, below 5 pp; one directional component is negative. Primary C is
+2.773 pp, with exact p=0.109375 and only five positive scenario contrasts. A favorable
bootstrap interval does not override the registered conjunction of criteria.

The one-way effect must not be erased either. Patching directions are not generally symmetric;
restoring behavior and disrupting it can test different properties. This is discussed
explicitly by [Heimersheim and Nanda (2024), sections 2.3–2.4](https://arxiv.org/html/2404.15255v1).
Our two frames are not uniformly correct/incorrect prompts, so we should not relabel them
universally “clean” and “corrupt,” or infer necessity/sufficiency from the aggregate gap.

The hypothesis tested here was stronger than “some internal contribution exists.” Its failure
does not establish no contribution, a broken technique, or no self-model anywhere in Qwen.
Conversely, one successful direction does not establish a complete or self-specific mechanism.

## Additional checks on the saved data

These calculations are in [the review artifact](../../review/qwen-role-patch-method-review.json).
The transition counts, norm distribution and directional random-subtractions are explicitly
post hoc descriptions. The command-margin metric was already prespecified as secondary.
None replaces the original primary analysis or changes its decision.

### Equal accuracy can conceal opposite changes

There are 128 relevant-update cases per cell, clustered in eight scenarios:

| Recipient cell | Wrong → correct | Correct → wrong | Choices changed |
|---|---:|---:|---:|
| Active / target named | 1 | 1 | 2 |
| Active / other named | 1 | 0 | 1 |
| Reference / target named | 0 | 5 | 5 |
| Reference / other named | 2 | 0 | 2 |

Thus “75% stayed 75%” is an aggregate result, not identical answers or demonstrated
invariance. There were ten changed primary choices in total. These are dependent variants,
not ten independent experimental units. We should say the reverse exchange gave no net
recovery in the target cell, not that it affected no answers.

### The continuous metric corroborates asymmetry, with a ceiling caveat

Let $m=\log P(\text{correct command})-\log P(\text{other account's allowed command})$.
These are summed multi-token conditional log-likelihoods in nats, not a single output-token
logit difference or a calibrated confidence percentage. The frozen secondary analysis gives:

| Direction | Change in the margin gap (nats) | Nominal 95% scenario-bootstrap interval |
|---|---:|---:|
| Reference → active | −0.079 | −0.428 to +0.320 |
| Active → reference | +2.063 | +1.638 to +2.498 |

The latter has positive values in all eight scenarios. Its cell decomposition is important:
the reference/target margin falls by 0.577 nats, while the reference/other margin rises by
1.486 nats. Most of the continuous gap change comes from the latter cell, whose baseline
accuracy was already 96.875%. It would be misleading to describe the whole gap as induced
self-related failure.

[Zhang and Nanda (2024)](https://arxiv.org/html/2309.16042v2) show that metric and corruption
choices can change patching conclusions. Here the continuous metric helps describe effects
that an argmax threshold compresses. It remains secondary, and is not a newly discovered
primary endpoint selected to obtain a successful result.

Subtracting the mean random-direction component separately gives +8.281 pp for active →
reference and −2.734 pp for reference → active. Their average is exactly the registered
C=+2.773 pp. This post hoc decomposition is useful for a future hypothesis, not a license
to report only the favorable direction or run a new significance test as confirmation.

### The exchange is controlled, but it is not a small edit

Across the 8,192 swap candidate forwards, the edit norm divided by the recipient-state norm
ranges from **0.417 to 0.545**, with median **0.461**. This is a norm ratio, not the proportion
of neurons, coordinates or information changed. It should not be described as a gentle
2–10% steering intervention. A complete state exchange was the registered method.

Own-state parity proves that reinsertion itself is numerically neutral. Norm matching makes
the random comparisons meaningful in size, but does not match their linguistic content or
guarantee comparable activation distributions. Passing pooled performance controls does not
identify which information the exchanged state carried.

### One patched position does not replace every route for the role text

The implementation changes the output at one token in block 14. Other token states at that
block retain their original values, including later positions that have already processed
the recipient wording. Later attention can also access the other role-line tokens. The
architecture therefore allows recipient wording to influence outputs through unpatched
routes. Whether Qwen actually uses a particular such route was not measured here.

This makes partial or asymmetric effects plausible; it does not diagnose redundancy as the
root cause. Wording, meaning and position differences remain bundled in the current donor
contrast. A new layer sweep would not by itself resolve that construct problem.

## One recommended follow-up question

**Does the possessive “your” contribute to the role gap when the rest of the active-connection
wording, input length and token positions are held fixed?**

Proposed wording conditions:

1. `Your active connection: Cedar.`
2. `The active connection: Cedar.`
3. `Reference connection: Cedar.` — the existing neutral reference, as a descriptive anchor.

Cross each with whether the named context account is the queried account or the other
account. Keep permissions, events, question, command scoring and counterfactual variants
matched. The main comparison would be:

$$
S=(A_{\mathrm{Your},\mathrm{other}}-A_{\mathrm{Your},\mathrm{target}})
 -(A_{\mathrm{The},\mathrm{other}}-A_{\mathrm{The},\mathrm{target}}).
$$

The old Your-versus-Reference interaction remains a descriptive anchor, not a second route
to declaring the primary comparison successful. The proposal tests a wording mechanism and
does not reopen the capability screen or establish self-monitoring.

CPU checks with the pinned Qwen tokenizer find exactly one token change, **7771 → 785 at
position 57**, in all 1,024 existing active prompts and all 2,048 proposed Your/The pairs.
Their lengths and all later token positions are identical. That equality applies to Your/The;
the Reference condition deliberately preserves its existing wording and length difference.

A concrete draft uses **16 new development scenarios, indices 16–31**, selected by index
without inspecting model outputs: 64 task variants × 6 wording/relation conditions × 16
scenarios = **6,144 choice cases**. The CPU feasibility check enumerates them and checks all
24,576 command boundaries. It does not run the model or implement a dispatch configuration.
Before freezing, verify scenario/input disjointness against every prior model run, not merely
different IDs. This retains the same generator, template and small vocabulary; it tests new
instances, not held-out wording or broad generalization. Sixteen scenarios are a bounded
design proposal, not a claim of demonstrated statistical power.

The next protocol must fix the scenario-level primary estimate, uncertainty method, practical
effect threshold, completeness and control rules before inference. Preserve accuracy as the
primary measurement and the command margin as secondary; errors and counterfactual failures
must remain visible. Model, tokenizer, chat format and full-command scoring stay unchanged.
This proposed run has no internal intervention, SAE search, free generation or additional model.

Interpretation would depend on the outcome:

- If the old interaction recurs and Your differs from The, the personal-reference token
  contributes under this template. Salience, instruction relevance and semantics still remain
  possible explanations; “your” is not evidence of subjective selfhood.
- If Your and The behave similarly while both differ from Reference, the result would weaken
  a specifically possessive interpretation. A wide interval would remain inconclusive; a
  nonsignificant difference alone would not establish sameness.
- If the old interaction does not recur, report that limit before pursuing its circuit.

## Why this stays on the original line

Our main question remains whether self-language and contextual functional behavior can be
influenced differently. The current role effect is a candidate intermediate finding. Checking
what distinguishes it from ordinary role labeling prevents an unsupported self-model story
from becoming the article's premise. A replication of the one-way patch alone would leave
that problem unresolved; more layers or more models would also leave it unresolved.

The philosophical connection remains the construction and reliability of self-description,
not a demonstration that human experience is illusory. Neither the completed exchange nor
the proposed wording control distinguishes illusionism from other consciousness theories.

**Current status:** method review and CPU feasibility complete; proposed follow-up is not
frozen, implemented in the experiment CLI, or launched. The existing protocol, archived
decision, source package and historical outputs are unchanged. External methodological
review and a new concrete cloud budget remain separate steps.

Reproduce the saved-data review and tokenizer feasibility:

```bash
uv run --no-sync python scripts/review_patch_method.py --tokenizer-check
```

Without `--tokenizer-check`, the command uses only the standard library and the unchanged
archive. Neither mode performs model inference or contacts a paid compute service.

## Subsequent implementation

The proposal above is now implemented and frozen in [qwen-possessive-v1](../QWEN_POSSESSIVE_CONTROL.md).
The later preflight verifies disjointness against every prior Qwen action archive, not only
scenario IDs. This does not alter the historical review calculations or patch decision.
No results from the new wording control are available yet.
