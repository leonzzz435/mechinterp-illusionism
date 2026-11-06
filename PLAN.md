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

## Empirical milestones

- [x] Historical reference run and export.
- [x] HF/TL parity, SAE reconstruction and post-intervention integrity checks pass.
- [ ] Baseline capability and counterfactual consistency established.
- [ ] Development/validation dose-response and degradation analysis complete.
- [ ] Primary contrasts frozen and held-out confirmation run complete.
- [ ] Independent blinded ratings collected and agreement assessed.
- [ ] Conditional follow-ups: combined interventions, circuit tracing, independent replication.
- [ ] Final article written from verified evidence, reviewed and shared.

## Decisions and blockers

### Current next step: action-task design before another model run

- [x] Keep causal separation as the main question and illusionism as the philosophical motivation.
- [x] Build a CPU-only executable permission-change task with self, named-self and other controls.
- [x] Separate the unresolved scoring/root-cause question from the task's construct validity.
- [x] Export a development design, oracle/shortcut checks and a clearly labeled design figure.
- [x] Obtain a fresh-context AI review; preserve its findings and make the cloud raw data reviewable from Git.
- [x] Fix exposed condition IDs and the grant-position shortcut; add paired grant-value controls.
- [ ] Review the concrete task; freeze model, scoring, counterfactual criteria and a small screening protocol.
- [ ] Authorize and run a new bounded cloud job only after that protocol is concrete.

See [the action-task design](docs/ACTION_TASK_DESIGN.md). This is a draft development pool,
not new model evidence. No instruction-tuned/larger model was selected and no new GPU job
was launched. The old 40/40/100 dataset and completed pilots are preserved.

The [review guide](docs/REVIEW_GUIDE.md) is the handoff for a reviewer without chat context.
The [first independent AI review](docs/reviews/2026-11-06-independent-review.md) found two
concrete shortcuts in the unrun draft; those have been addressed, but neither a model-scoring
protocol nor a strong self-model interpretation is established. External human review remains
outstanding. The next cloud job is not ready merely because software tests pass.

### Historical pilots and empirical blockers

The first Blackwell baseline failed all functional families (combined accuracy: ownership 48.5%, access 46.1%, capability 32.0%). See `docs/PILOT_REVIEW.md`. The large sweep is stopped. A fixed four-shot development baseline now uses `lm-evaluation-harness==0.4.13` with its native Hugging Face backend and full-continuation likelihood scoring. This new protocol is not a causal repair experiment and cannot unlock the original confirmation run.

- [x] Run the unchanged standard-harness baseline on Hugging Face Jobs and review its export.
- [ ] Before any new interventions, establish a passing baseline under an explicitly revised protocol and verify the unchanged intervention path against it.
- [ ] Establish a revised validation protocol; inspect feature activation and delivered edit norms before interpreting ablation nulls.

The abandoned format-search implementation was not committed or pushed. Validation/test data stay closed in the new harness path. The current handover is `docs/HF_JOBS.md`; local Blackwell execution remains an option.

The private machine lacks supported CUDA hardware for the study. A narrow HF Jobs launcher now prepares one L4 job, records a pinned commit/image, enforces a provider timeout and persists completed scenario blocks to a private HF dataset repository. The first authorized cloud job completed and its export was independently verified; see `docs/HF_PILOT.md`. All three families again failed the capability screen (43.36%, 50.78%, 41.41%). The current functional pilot ends here. No second job, multi-model expansion or automatic retry was performed. CPU fixtures do not substitute for model results.

The canonical layer-14 residual SAE resolves to `average_l0_84`. New runs use unprocessed TransformerLens weights; original processed weights are reference-only. This may change results and must remain visible.

Contextual tasks expose the scene to the model, so they do not establish private-state introspection. Baseline failure ends the current functional pilot rather than triggering an undocumented model switch.

Circuit attribution, another model, private-state introspection and a full novelty review are follow-ups contingent on pilot findings. There is no measured mechanism diagram yet.
