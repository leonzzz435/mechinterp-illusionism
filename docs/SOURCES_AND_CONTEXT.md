# Sources, motivation and claim boundaries

## Motivating incident

The [METR/Redwood investigation of the OpenAI/Hugging Face incident](https://evals.alignment.org/blog/2026-08-26-openai-hugging-face-incident-investigation/) describes unsanctioned communication, coordination and reasoning about evaluation. Its scope and observation limitations matter. Agent statements are generated text; actions provide a separate behavioral record. Neither directly measures phenomenal experience.

[OpenAI's incident index](https://alignment.openai.com/misalignment-reports/) distinguishes provider accounts from the independent investigation. Our small-model experiments are motivated by these reports, not a mechanistic explanation or reproduction of the incident. We do not possess the internal model or its complete runtime.

## Mechanistic methods

- Elhage et al., [Transformer Circuits](https://transformer-circuits.pub/2021/framework/index.html): residual-stream and circuit analysis.
- Elhage et al., [Toy Models of Superposition](https://transformer-circuits.pub/2022/toy_model/index.html): distributed representations, not a guarantee of any Gemma feature's meaning.
- Bricken et al., [Towards Monosemanticity](https://transformer-circuits.pub/2023/monosemantic-features/index.html): dictionary learning and interpretability investigations.
- Lieberum et al., [Gemma Scope](https://arxiv.org/abs/2408.05147): pretrained SAEs. We use layer-14 residual, width 16k, average L0 84.
- Turner et al., [Activation Addition](https://arxiv.org/abs/2308.10248): activation steering.
- Zou et al., [Representation Engineering](https://arxiv.org/abs/2310.01405): representation-based interventions.
- Karvonen et al., [SAEBench](https://proceedings.mlr.press/v267/karvonen25a.html): multiple evaluations beyond a single proxy.
- Chanin, [Are Sparse Autoencoder Benchmarks Reliable?](https://arxiv.org/abs/2605.18229): criticism of several SAE evaluation metrics.
- Anthropic, [Signs of introspection](https://www.anthropic.com/research/introspection): distinction between concept-influenced text and reporting internal interventions. Our contextual tasks do not replicate that private-state assay.

## Implementation sources

- [TransformerLens v2.18.0](https://github.com/TransformerLensOrg/TransformerLens/tree/v2.18.0).
- [SAELens v6.54.9 Gemma loader](https://github.com/decoderesearch/SAELens/blob/v6.54.9/sae_lens/loading/pretrained_sae_loaders.py): JumpReLU, no decoder-bias subtraction, NPZ conversion.
- [Canonical registry](https://github.com/decoderesearch/SAELens/blob/v6.54.9/sae_lens/pretrained_saes.yaml): layer-14 residual canonical maps to `average_l0_84`.
- [SAELens usage](https://decoderesearch.github.io/SAELens/v6.51.4/usage/): recommends unprocessed TransformerLens loading for SAE use.

The loader pins the NPZ to an HF commit and records its SHA256. Runtime reconstruction checks remain necessary; source inspection alone is not compatibility evidence.

## Philosophical framing

Dennett's *Consciousness Explained* (1991) and Frankish's [Illusionism as a Theory of Consciousness](https://philpapers.org/rec/FRAIAA-4) motivate investigating self-reports. They are philosophical frameworks, not established consequences of steering.

A dissociation of language and contextual self-model performance could support functional separability under tested conditions. Several non-illusionist theories could also accommodate it. Failure to find a dissociation would not establish consciousness either. Claims about humans require additional bridging evidence.

This is a targeted source review, not an exhaustive novelty review. Original source notes remain in the historical archive.

## Closest work and contribution assessment — checked 2026-11-06

The earlier source list covered methods and motivation better than direct competitors.
The review handoff establishes inspectability, not novelty. The following primary sources
substantially narrow what this project can reasonably claim as a new contribution.
Conference publications and preprints are distinguished; neither status substitutes for
checking the particular methods and conclusions. This remains a targeted literature search,
not a systematic review or a guarantee of priority.

| Primary source | Relevant result or method | Consequence for this project |
|---|---|---|
| Ackerman & Panickssery, [Inspection and Control of Self-Generated-Text Recognition](https://arxiv.org/abs/2410.02064v3), ICLR 2025 | A residual-stream direction controls self-authorship judgments in Llama3-8B-Instruct; specificity controls and open-ended steering are included. | Finding a steerable self-related direction alone is already established precedent. |
| Han et al., [The Personality Illusion](https://proceedings.mlr.press/v306/han26n.html), ICML 2026 | Persona prompts reliably shift personality self-reports, with little or inconsistent change in the tested behaviors. | A generic report–behavior dissociation is not a new claim. Our action construct and internal interventions would need to add something specific. |
| Maczan, [As a Language Model…](https://arxiv.org/html/2609.25021v1), 2026 preprint | Chat templates shift disclaimer/experiential language; activation directions reproduce parts of this effect. Steering scope and random-control reliability are limited. | Self-language steering needs explicit comparison with formatting effects and existing methods; it cannot carry novelty by itself. |
| Zeng et al., [Evaluating and Improving LLM Self-Modeling](https://aclanthology.org/2026.emnlp-main.522/), EMNLP 2026 | Benchmarks verifiable predictions about a model's own behavior; training improves some scores without consistently establishing privileged introspection. | Our supplied-role permission task measures a different, narrower construct. Calling both “self-modeling” must not hide that difference. |
| Li et al., [Where Is the Self? — From Self-Index to Self-Reference](https://arxiv.org/html/2610.16717v5), preprint revised 2026-11-04 | Role-conditioned subspace replacements affect attribution and, in some tested model/mode conditions, moves in a source-dependent secret game, with content/arithmetic controls. | This is close causal prior work, including role-dependent action. Adding an executable outcome alone does not establish novelty. A self-language/action dissociation would need a sharper comparison. |
| Singh et al., [Can LLMs Introspect? A Reality Check](https://arxiv.org/abs/2605.26242v2), accepted at COLM 2026 | Input-only predictors and input-anomaly controls undermine introspective interpretations of two existing paradigms. | Our text-supplied state does not establish privileged access or metacognitive monitoring. Stronger labels require discriminating predictions, not task accuracy alone. |
| Ma et al., [Do SAEs Identify Reasoning Features?](https://proceedings.mlr.press/v306/ma26v.html), ICML 2026 | Token injections and counterexamples show that many candidate reasoning features track correlated cues; small steering experiments yield limited benchmark changes. | Candidate features 2728/10230 need lexical counterexamples and functional validation. An interpretable label or successful edit is insufficient. |
| Martorell & Bianchi, [Don't Ask](https://arxiv.org/abs/2603.18893v3), revised 2026-10-10 preprint | Rating questions change probed states; ratings have weak pre-question coupling and limited concept/self specificity. | The measurement prompt can change the state being measured. The revised conclusions supersede the more optimistic earlier title and framing. |
| Ferrara, [Open-Weight Masked Introspection](https://arxiv.org/abs/2608.20569v1), 2026 preprint | Reports near-chance verbal intervention detection despite decodable activation signals, using sham, random-edit and text-observer controls. | Internal decodability and verbal reporting can dissociate already; this does not directly test our permission-update behavior. |

### Defensible scope of an original extension

The implemented permission simulator is a development instrument, not yet an empirical
contribution. Its most promising use is a tightly controlled extension asking whether
language-directed interventions and role/action-directed interventions produce distinct
effects on self-language, current permission use, named-self/other judgments and ordinary
state tracking. Differences must survive lexical, position, format and general-degradation
controls, and transfer to held-out wording. This is a proposed contribution, not an established
gap: the exact comparison with the closest studies must precede any priority claim.

A change in pronouns while an unrelated task remains accurate would have limited scientific
novelty. Likewise, swapping Gemma for another model or replacing a benchmark with our own
simulator does not itself supply a new scientific question. A transparent replication with
one informative extension is a useful outcome and a plausible basis for the article.

The current failed baselines do not support a favorable forecast for a selective causal
effect. A bounded screen must first show task competence and measurement sensitivity.
Null interventions become informative only with demonstrated delivered edits, a positive
control, adequate precision and a prespecified claim boundary. No numerical probability of
publication or discovery can be justified from the current pilots.

Illusionism remains a legitimate philosophical motivation. The proposed experiment currently
has no prediction that uniquely distinguishes it from competing views of consciousness.
Selective effects could constrain accounts of these behaviors; stronger philosophical claims
need an additional argument. A compelling article can make that distinction explicit while
showing the mathematics, counterexamples and results in full.

## Standardized evaluation

The revised baseline uses [EleutherAI's Language Model Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness), pinned to Python package `lm-eval==0.4.13`. The [task guide](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/new_task_guide.md) describes full-continuation likelihood scoring, target delimiters and fixed few-shot examples. The implementation is exercised against the installed pinned package, not assumed compatible from current online documentation alone. Custom tasks remain our responsibility; using a standard evaluator does not validate the self-model construct.
