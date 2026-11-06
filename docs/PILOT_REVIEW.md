# Review of the first Blackwell results

Reviewed commit: `3e9303f`, 2026-11-06. The original run artifacts remain unchanged.

## Integrity and feasibility

The reference (6 trials), baseline (4,320 trials) and feasibility (3,600 trials) runs completed without recorded execution errors. Journal hashes, regenerated datasets, saved source snapshots, direction hashes and export checksums matched. The unprocessed-model runs passed the configured HF/TL parity and SAE reconstruction gates. Post-run baseline logits were unchanged.

The GPU was an NVIDIA RTX PRO 3000 Blackwell Generation Laptop GPU. Peak allocated memory was about 8.4 GiB. Recorded invocation time was about 18.2 minutes for baseline, 8.7 minutes for feasibility and 26 seconds for reference. These timings do not predict the revised four-shot baseline directly.

The actual model repository was the explicitly recorded `unsloth/gemma-2-2b` mirror at `25319945f7fd83b8b903e12081777b7eef2ba993`. HF/TL parity checks that checkpoint in two implementations; it does not independently establish weight identity with Google's repository.

## The functional gate failed

| Family | Self | Other | Combined |
|---|---:|---:|---:|
| Ownership | 50.31% | 46.72% | 48.52% |
| Information access | 45.16% | 47.03% | 46.09% |
| Capability change | 28.75% | 35.31% | 32.03% |

All families miss the 80% gate. Under factual assignment swaps, predictions changed in only 16.41%, 11.88% and 14.06% of ownership, access and capability pairs, respectively. Current scores do not establish reliable contextual self-model use.

At `Answer:`, the unrestricted top token was a newline in 3,782 of 3,840 choice trials. The scorer considered bare letter tokens only, excluding distinct tokens with a leading space. The pinned tokenizer confirms `A` = 235280 versus ` A` = 586. This is a measurement limitation, not proof that corrected formatting will make Gemma succeed.

## Interventions

In the four-scenario-per-family feasibility run, each candidate ablation left all four saved choice probabilities exactly unchanged in all 384 choice trials. The cause is unresolved because last-position pre/post coefficients and realized edit norms were not logged. Inactive coefficients and numerical effects must be distinguished before treating this as functional invariance.

All 72 Holm-adjusted functional comparisons had p = 1.0. The sample contains four scenario clusters per family; it cannot support a strong equivalence claim. First-person-language effects also remained uncertain.

A descriptive activation pattern merits follow-up: in baseline language prompts, feature 2728 was active for monitoring-topic prompts in both grammatical perspectives, while 10230 was active for first-person prompts in both topics. Mean prompt activations were:

| Perspective/topic | Feature 2728 | Feature 10230 |
|---|---:|---:|
| Third person / equipment | 0 | 0 |
| Third person / reasoning | 0.388 | 0 |
| First person / equipment | 0 | 0.442 |
| First person / reasoning | 0.544 | 0.580 |

These simple templates can expose lexical cues. This observation identifies neither a mental function nor a mechanism of consciousness.

## Decision

Preserve this as a technically successful but functionally unsuccessful pilot. Stop the large intervention sweep. Replace bespoke answer-token scoring with the pinned EleutherAI harness for one fixed development baseline. Its four-shot protocol is documented in [the Blackwell handover](HANDOVER_BLACKWELL.md). New scoring does not retroactively alter the old results or unlock the old confirmation protocol.

The historical plots are exploratory artifacts. Their joined positive/negative dose points can suggest an unmeasured nonzero effect at zero dose, and the combined language/task plot has overlapping labels. They are not publication-ready figures.
