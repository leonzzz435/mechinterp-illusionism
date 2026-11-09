# Article-v2 paragraph ledger

Markers V00–V34 identify paragraph blocks, including associated tables/equations/captions.
Every empirical statement within each block is covered below. Connective prose introduces
no extra evidence. The sources are local recorded data unless explicitly labeled philosophical
motivation or an inference. This ledger is separate from the frozen article-v1 ledger.

Source keys (JSON paths use `/` within a cell name as a literal key component):

- **R**: [frozen combined report](../../review/query-reference-results/report.md), [analysis](../../review/query-reference-results/analysis.json), including `cells`, `observations`, `lookup_cells`, `paired_controls`, `decision`.
- **S**: [retrospective sensitivity addendum](../QUERY_REFERENCE_SENSITIVITY_ADDENDUM.md), [data](../../review/query-reference-sensitivity/analysis.json). Status: post hoc, no restored confirmation.
- **T**: [new stage report](../../review/query-reference-stages/report.md), [data](../../review/query-reference-stages/analysis.json). `variants.frozen_v1` retains original counts without intervals; `variants.v2_stored_greedy` and `exclude_world_0011` supply exploratory intervals. No new hypothesis test.
- **O**: [order/error CPU count](../../review/query-reference-order-errors/report.md), [JSON](../../review/query-reference-order-errors/analysis.json). Descriptive counts from pinned archives; per-world signs independently reconstructed with exact fractions and checked against T. No new intervals, tests or decision.
- **X**: [complete illustrative example](../../review/query-reference-stages/example.md), T `example.records`, `opening_record_id`, `chosen_key`, `rule`. Selected post hoc, not representative.
- **D**: [frozen design](../../designs/query-self-reference-v1.json), [generator](../../src/self_model_study/query_reference.py), [text-first audit](../../src/self_model_study/query_reference_audit.py), [execution runbook](../QUERY_SELF_REFERENCE_RUNBOOK.md).
- **A**: [offline tie amendment](../QUERY_REFERENCE_V2_AMENDMENT.md). The stored greedy flag concerns the whole teacher-forced continuation, not a recorded generated reply or verified termination.

| Block | Claims, exact source scope | Evidential status / boundary |
|---|---|---|
| V00 | R `decision`; S; unchanged [article-v1](../article/ARTICLE.md). | Repository edition dated 2026-11-09, frozen at annotated tag `article-v2`; no replacement of the original experimental decision. |
| V01 | X opening prompt: Rowan/Laurel, Morgan/Coral; jade/silver revoked, ochre/amber granted; printed question and menu. | Actual saved input; scene selected after outcomes. |
| V02 | X matched self/possessive, self/account-name and snapshot cases, both orders. | Recorded summed-score choices; simulator permission logic, not unrestricted generation. |
| V03 | X `rule`, 24 exported records; T `event_orders`; R/S foreign errors for operator-name and other-possessive queries. | Post hoc example, not a frequency estimate or a possessive-specific error claim. |
| V04 | T generated `task_example`; X scores. | Diagram of task relations, not neural mechanism. |
| V05 | [original question and construct boundaries](../PROTOCOL.md); D operator assignment and oracle. | Motivation and operational definition, not evidence of experience. |
| V06 | D model/scoring/sampling/prompts/factorial; [pinned upstream files](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/tree/a09a35458c702b33eeacc393d103063234e8bc28); [pilot model choice](../QWEN_PILOT.md). | One model, bounded cost, pinned open weights. Counterbalancing applies to declared factors; varying labels are not a claim of uniform vocabulary frequencies. |
| V07 | D `query_references`; `_row`; independent parse/audit. | Same-target alias contrasts; no isolated-token or internal-computation claim. |
| V08 | D `before_body`, `snapshot_body`, `after_both_body`; T pairing tests. | Snapshot/history share final state; before differs; independent prompts, not a longitudinal session. |
| V09 | D scoring; runbook; A native-flag limits. | Summed full-command log-likelihood definition and candidate-selection limitation. |
| V10 | R scheduled/observed/world inventory; D factorial; T bootstrap. | 16,128 variants, 48 independent world units in the analysis; no claim of cross-template sampling. |
| V11 | R six `after_both/*/*` cells; S F. | Frozen descriptive accuracy including tie failure; 35.0260417 pp is computed before display rounding, not from 95.18−60.16. No original CI/p-value. |
| V12 | D lookup rule; R `lookup_cells`, gated `paired_controls`, `cells.after_both/self/owner_name` and `paired_controls.ownership/after_both/self/owner_name`; S controls section. | 3/8 accuracy and 5/8 pair failures in before/snapshot, 80% requirement unchanged. After-both accuracy1096/1536=71.35% and fully correct pairs358/768=46.61% are diagnostics; `lookup_gate=false`, not added gate failures. |
| V13 | R invalid record and decision; A; S three variants. | Complete records, exact tie; explicit after-outcome amendment. |
| V14 | S `variants.exclude_world_0011.primary.F` and `v2_stored_greedy.primary.F`; exhaustive alternative. | 35.31 [31.58,39.03], 34.96 [31.25,38.61] pp; tie bound 100/1536 pp; own-possessive accuracy 924/1536 to925/1536 (60.16% to60.22%); exploratory. |
| V15 | T original cell table; D presentation definitions. | Explanatory transition, no progression/learning claim. |
| V16 | R `cells`; T `variants.frozen_v1.cells`, all 18 cells. | Exact frozen accuracies, no altered denominators or selective owner/form omission. |
| V17 | D factorial: per owner/form 8/16/32 variants per world; T n. | 384/768/1536 cell counts; 48 worlds throughout. Figure descriptive. |
| V18 | T `v2_stored_greedy.contrasts.before/possessive/self_minus_other`, `snapshot/possessive/self_minus_other`; R before/account-name cells. | Nominal intervals include zero, not equivalence. Own-account disadvantage also exists for explicit account naming. |
| V19 | T `v2_stored_greedy.contrasts.after_minus_snapshot/self/possessive`, `other/possessive`, `possessive/self_minus_other`; same interaction in `exclude_world_0011`; O `variants.v2_stored_greedy.signs.after_minus_snapshot/self/possessive`. | −11.91, +0.85, −12.76; −13.30 pp after exclusion, with quoted intervals; retrospective. Own-history signs37negative/8positive/3zero, not38/7/3. This is distinct from interaction signs34/8/6. All changes and intervals in V19 use the signed after-minus-snapshot convention; no magnitude-only interval. |
| V20 | T `after_minus_snapshot/self/account_name`; all six history contrasts and plot; D prompt differences. | +3.78 [0.59,7.23] pp. Uniform penalty contradicted by recorded means; position/interference/work are unresolved alternatives, not identified causes. |
| V21 | R after_both/self/possessive; S error table; O `variants.frozen_v1.cells.self/possessive/target_last` and `target_first`. | 591/612 failures;14+6 revoked and one tie;38.48% overall. Split:768 cases per order; target-last447/461 foreign failures(96.96%, first grant), target-first144/151(95.36%, latest grant). Full category partition retained. No new interval/test or mechanism. |
| V22 | R after_both/other/possessive; D oracle/classifier. | 440/441, foreign defined relative to target. Does not demonstrate reliable Their resolution or common absolute referent. |
| V23 | S original error table and corrections. | Operator foreign315/revoked125; account53/21. Counts replace obsolete block00 totals, no claim of separate defects. |
| V24 | T `baselines` every cell; D scripted policies and rotations. | Latest-only N/A without events; fallback25%, after50%; conditional target-last100/other-last0. Uniform-four-choice25% is arithmetic, not an observed model policy. |
| V25 | S original shortcut agreement; T and O frozen counts. | Latest451/1536, first1064/1536,20revoked and1tie sum to1536; the remainder is21, not only the tie. Excludes a universal fixed rule, not mixed temporal mechanisms. |
| V26 | T frozen `event_orders.self/possessive` and `other/possessive`; O corresponding cells and `latest_grant_correct`. | 39.97/80.34 and62.50/80.08%; latest policy768/768 versus model307/768 in own target-last. Equal-sized768-case strata give pooled924/1536=60.15625%; averaging unrounded accuracies, no bimodality claim about world distributions. |
| V27 | X both orders versus T distribution; V12 controls. | Synthesis of unresolved explanation requirements, not a new empirical test. |
| V28 | [role results](../QWEN_ROLE_RESULTS.md), [patch](../QWEN_ROLE_PATCH_RESULTS.md), [wording](../QWEN_POSSESSIVE_RESULTS.md), [ownership](../QWEN_OWNERSHIP_RESULTS.md), [prompt-parity review](../OWNERSHIP_DESIGN_REVIEW.md). | Earlier context-line task versus present query-bound task; retain passed role candidate and failed stronger/later rules. No pooling of experimental estimands. |
| V29 | [confidence](../QWEN_CONFIDENCE_RESULTS.md); D scope. | Failed separate assay; current study has no internal intervention. Ratios of distinct contrast magnitudes are not rankings of evidence. |
| V30 | [Frankish primary account](https://www.keithfrankish.com/illusionism/), “What is illusionism?”, checked 2026-11-09; [preserved philosophical notes](../article/PHILOSOPHICAL_NOTES.md). | Short paraphrase of motivation; no phenomenal/introspection measurement claimed. |
| V31 | D assigned ownership; R/S/T results; preserved philosophical notes. | Explanatory analogy, not evidence for human illusionism or against alternative consciousness theories. |
| V32 | R/S/T within-task comparisons. | Engineering implication framed as something to investigate; no production rate, fix, or generalization claim. |
| V33 | R/S/T scope and failures. | Synthesis restricted to this model/template; no functional self-model or mechanism conclusion. |
| V34 | [methods](METHODS.md), generated files and verification. | CPU-only deliverable; no new GPU/model/routing/intervention. Scientific interpretation is not certified by software tests. |
