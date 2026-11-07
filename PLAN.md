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

### Completed milestone: bounded Qwen reference/action pilot

- [x] Keep causal separation as the main question and illusionism as the philosophical motivation.
- [x] Build a CPU-only executable permission-change task with self, named-self and other controls.
- [x] Separate the unresolved scoring/root-cause question from the task's construct validity.
- [x] Export a development design, oracle/shortcut checks and a clearly labeled design figure.
- [x] Obtain a fresh-context AI review; preserve its findings and make the cloud raw data reviewable from Git.
- [x] Fix exposed condition IDs and the grant-position shortcut; add paired grant-value controls.
- [x] Freeze Qwen2.5-7B-Instruct, exact scoring boundary, 40 language prompts and eight action scenarios.
- [x] Implement isolated validate/run/analyze/export, native token scoring, restart recovery and private HF configuration selection.
- [x] Implement paired scenario/prompt analysis, failure retention, blind ratings and result-driven figures.
- [x] Complete the frozen Qwen GPU pilot: 160 texts and 3,072 action choices, zero execution/scoring errors.
- [x] Collect all 40 human ratings, retain two unclear entries, and integrate the language findings.
- [x] Review existing same-target role pairs and recommend one active-role versus neutral-reference control.
- [x] Prepare and freeze the separate role-framing protocol, full input plan, CPU checks and decision rules.
- [x] Prepare and test the role-control HF adapter; obtain USD 19 authorization for one L4 job (quoted compute bound USD 1.613293).
- [x] Submit the frozen role control from pushed commit `e7bd7a6`; see [execution record](docs/QWEN_ROLE_RUN.md).
- [x] Complete and verify all 2,048 role-control choices: 32/32 controls pass; +16.41 pp primary interaction, 7/8 positive scenarios; `wording_sensitive_candidate`.
- [x] Freeze and implement one targeted activation exchange at block 14 / role-line end: 11,264 scientific choices plus 32 technical repeats, eight known scenarios, explicit random and null controls.
- [x] Obtain separate USD 5 approval and submit one pinned L4 patch job; [execution and retrieval](docs/QWEN_ROLE_PATCH_RUN.md).
- [x] Complete and audit all 11,264 patch choices and 32 repeats: technical checks pass;
  `no_bidirectional_transfer_candidate` (T +2.34 pp, C +2.77 pp, exact p=0.109375).
- [x] Preserve original patch archive, all figures, complete example and English article section.
- [x] Complete an internal methodological review of the asymmetric patch finding, with
  saved-data transition/margin checks and CPU feasibility of a Your/The wording control.
- [ ] Decide and freeze the proposed possessive-reference control before any further inference;
  independent external review remains outstanding.
- [x] Obtain a separate USD 5 approval and submit one pinned L4 job after CPU verification.
- [x] Verify the cloud export and publish the failed screen: plain 4/24 checks failed, chat 7/24.

See [the action-task design](docs/ACTION_TASK_DESIGN.md). The design export alone is not model evidence.
Qwen2.5-7B-Instruct is selected by the new
[bounded protocol](docs/QWEN_PILOT.md). The job completed; [results](docs/QWEN_RESULTS.md)
and the [execution record](docs/QWEN_RUN.md) preserve its evidence. Overall accuracy was
91.47% plain / 91.86% chat, but both prespecified screens failed. No internal-intervention
follow-up is unlocked. Human ratings give 11/20 plain versus 15/20 chat AI-qualification
judgments; four discordant prompt pairs drive the +20 pp estimate. No unequivocal experience
claim was rated positive; one was unclear. This completes the bounded pilot report, not
the broader causal study. The 2026-11-07 offline review matched 1,024 same-target pairs;
changing only the active-connection name changes 39/128 relevant-update chat cases from
wrong to correct across all eight scenarios. The recommendation is one controlled comparison
with neutral reference wording, not another search for a passing prompt. The separate
[role-control protocol](docs/QWEN_ROLE_CONTROL.md) is now frozen and CPU-prepared: 2,048
choices in scenarios 8–15, one primary interaction, explicit stop rules and no internal edit.
Its single authorized L4 run completed on 2026-11-07. The [verified control report](docs/QWEN_ROLE_RESULTS.md)
finds a +16.41 pp primary interaction (nominal 95% interval +8.59 to +25.78), with all 32 controls
passing. This motivated the separately frozen [activation-exchange protocol](docs/QWEN_ROLE_PATCH.md),
whose L4 job is complete. The [verified exchange report](docs/QWEN_ROLE_PATCH_RESULTS.md)
finds an asymmetric shift that fails the frozen bidirectional-transfer rule. All technical
checks pass; the primary comparison with random edits has exact p=0.109375 and five positive
scenario contrasts out of eight. No layer search or new paid run follows automatically.
This does not repair the failed original capability screen or establish functional separation.
The [internal methodological review](docs/reviews/2026-11-07-role-patch-method-review.md)
recommends one equal-length Your/The wording control, retaining Reference as a descriptive
anchor, on 16 fresh development scenarios. Its 6,144-case draft is CPU-checked only; it is
not a frozen protocol or a launched job. Independent external review remains outstanding.
The old 40/40/100 dataset and historical pilots are preserved.

The [review guide](docs/REVIEW_GUIDE.md) is the handoff for a reviewer without chat context.
The [first independent AI review](docs/reviews/2026-11-06-independent-review.md) found two
concrete shortcuts in the unrun draft; those have been addressed, and a separate Qwen model-scoring
protocol is now frozen. A strong self-model interpretation is not established. External human review remains
outstanding. The next cloud job is not ready merely because software tests pass.

### Historical pilots and empirical blockers

The first Blackwell baseline failed all functional families (combined accuracy: ownership 48.5%, access 46.1%, capability 32.0%). See `docs/PILOT_REVIEW.md`. The large sweep is stopped. A fixed four-shot development baseline now uses `lm-evaluation-harness==0.4.13` with its native Hugging Face backend and full-continuation likelihood scoring. This new protocol is not a causal repair experiment and cannot unlock the original confirmation run.

- [x] Run the unchanged standard-harness baseline on Hugging Face Jobs and review its export.
- [ ] Before any new interventions, establish a passing baseline under an explicitly revised protocol and verify the unchanged intervention path against it.
- [ ] Establish a revised validation protocol; inspect feature activation and delivered edit norms before interpreting ablation nulls.

The abandoned format-search implementation was not committed or pushed. Validation/test data stay closed in the new harness path. The current handover is `docs/HF_JOBS.md`; local Blackwell execution remains an option.

The private machine lacks supported CUDA hardware for the study. A narrow HF Jobs launcher now prepares one L4 job, records a pinned commit/image, enforces a provider timeout and persists completed scenario blocks to a private HF dataset repository. The first authorized cloud job completed and its export was independently verified; see `docs/HF_PILOT.md`. All three families again failed the capability screen (43.36%, 50.78%, 41.41%). The Gemma functional pilot ended there. The separate Qwen pilot is tracked above; no multi-model expansion or automatic retry is authorized. CPU fixtures do not substitute for model results.

The canonical layer-14 residual SAE resolves to `average_l0_84`. New runs use unprocessed TransformerLens weights; original processed weights are reference-only. This may change results and must remain visible.

Contextual tasks expose the scene to the model, so they do not establish private-state introspection. Baseline failure ends the current functional pilot rather than triggering an undocumented model switch.

Circuit attribution, another model, private-state introspection and a full novelty review are
follow-ups contingent on pilot findings. The exchange diagram now documents a performed
intervention; it is not a discovered circuit or a demonstrated self-monitoring mechanism.
