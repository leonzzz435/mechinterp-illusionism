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
