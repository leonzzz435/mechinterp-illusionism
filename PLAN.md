# Study implementation and evidence status

## Implemented

- [x] Preserve original notebook, outputs, plot, scripts and source notes in `archive/`.
- [x] Separate self-language, contextual self-model use and phenomenal consciousness.
- [x] Shared package, strict JSON configuration, validate/run/analyze/export CLI.
- [x] Deterministic 40/40/100 scenarios, factorial language controls, self/other pairs and counterfactuals.
- [x] Explicit checkpoint revisions and preprocessing; no automatic loading fallback.
- [x] Development-only calibration and directions; HF/TL parity and SAE fidelity checks.
- [x] Positive/negative additions, ten random controls and residual-preserving ablation.
- [x] Transactional trials, bounded invocations, resume, failure retention and audit export.
- [x] Validation gates, protocol freeze and one-run test-set claim.
- [x] Paired scenario statistics, multiplicity corrections and conservative equivalence flags.
- [x] Result-driven figures, blinded rating export, English draft and technical protocol.

## Empirical milestones — pending Blackwell execution

- [ ] Historical reference run and export.
- [ ] HF/TL parity, SAE reconstruction and post-intervention integrity checks pass.
- [ ] Baseline capability and counterfactual consistency established.
- [ ] Development/validation dose-response and degradation analysis complete.
- [ ] Primary contrasts frozen and held-out confirmation run complete.
- [ ] Independent blinded ratings collected and agreement assessed.
- [ ] Conditional follow-ups: combined interventions, circuit tracing, independent replication.
- [ ] Final article written from verified evidence, reviewed and shared.

## Decisions and blockers

The private machine lacks supported CUDA hardware for the study. New empirical results require Blackwell; CPU fixtures do not substitute for them. No remote access is configured.

The canonical layer-14 residual SAE resolves to `average_l0_84`. New runs use unprocessed TransformerLens weights; original processed weights are reference-only. This may change results and must remain visible.

Contextual tasks expose the scene to the model, so they do not establish private-state introspection. Baseline failure ends the current functional pilot rather than triggering an undocumented model switch.

Circuit attribution, another model, private-state introspection and a full novelty review are follow-ups contingent on pilot findings. There is no measured mechanism diagram yet.
