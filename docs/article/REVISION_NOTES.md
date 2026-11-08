# Publication rewrite: scope, evidence and verification

Revision date: 2026-11-08. Historical base:
`36d9a068b661dff04cf1fa4a29ea47c4f8f48376`.
No new inference, GPU job, HF job or empirical endpoint calculation accompanied this rewrite.

## What changed

- Replaced the chronological experiment chapters with one role-error narrative, in the
  requested sequence: hook, constructs, simulator, recurring result, four challenges,
  alternatives, philosophical bridge, limits and reproduction.
- Added three title proposals and marked a favorite; replaced the old negative-results
  summary with the question connecting the observed pattern and its unresolved explanation.
- Removed the old proposed Figures 2–5 and unexecuted steering equation from the article.
  Those plans are not presented as completed measurements; their historical protocols remain.
- Reduced the Gemma history to two source-linked lines, without revising its failed gates.
- Condensed format, patch, Your/The and confidence details into a methods/challenges section;
  complete results, raw examples and provenance stay in their original linked reports.
- Retained the simulator illustration and the existing measured Your/The figure unchanged.
- Added a 90-entry claim ledger, philosophical source notes and two locally frozen
  specification pairs (JSON plus explanation); changed the review guide's entry point.

## Which numbers come from which record

| Article claim | Existing source |
|---|---|
| Your 72.66% / 100.00%; The 73.83% / 99.22%, with denominators | `docs/QWEN_POSSESSIVE_RESULTS.md:65-69` |
| Reference anchor 82.03% / 95.70% | `docs/QWEN_POSSESSIVE_RESULTS.md:69` |
| Earlier matched chat 69.53% / 100%, plain 92.97% / 100% | `docs/QWEN_RESULTS.md:18-23,84-99` |
| Middle cohort 75.00% / 99.22% | `docs/QWEN_ROLE_RESULTS.md:31-38` |
| Other-account command in 36/41 and 33/39 initial chat errors | `docs/QWEN_RESULTS.md:80` (post hoc) |
| Positive role interaction +16.41 pp, interval and exact p | `docs/QWEN_ROLE_RESULTS.md:3-7,65-79` |
| Disclaimer 11/20 versus 15/20, +20 pp and interval | `docs/QWEN_RESULTS.md:186-196` |
| Patch directions −0.781 / +5.469 pp; C +2.773 pp and p | `docs/QWEN_ROLE_PATCH_RESULTS.md:68-98` |
| Wrong-command transfer in the fixed example | `docs/QWEN_ROLE_PATCH_RESULTS.md:138-153`; `docs/QWEN_ROLE_PATCH_FULL_REPORT.md:438-454` |
| Your/The +1.95 pp, interval, p; secondary +0.346 nats | `docs/QWEN_POSSESSIVE_RESULTS.md:71-109` |
| Confidence selectivity −1.37 pp and AUROC 0.544, intervals | `docs/QWEN_CONFIDENCE_RESULTS.md:53-84` |

The [claim ledger](CLAIMS.md) covers the remaining methods, thresholds, captions and
equations with file/line references. New specification sample sizes, margins and thresholds
are **design choices**, not new findings. Their cost arithmetic is an explicitly labeled
extrapolation from historical execution reports, not a live quote or observed runtime.

## Corrections and unresolved questions

1. **Independent samples:** scenario indices 0–7, 8–15 and 16–31 are disjoint development
   cohorts, not independent confirmatory replications of one frozen protocol. The patch
   reuses 8–15. Repeated variants do not increase the independent sample size.
2. **Error direction:** the initial report counts other-account errors; the patch documents
   their transfer in its fixed example. The Your/The report lacks the matching aggregate
   categorical endpoint. No new count was computed or silently promoted to confirmation.
   The task's cited `QWEN_ROLE_RESULTS.md:210-216` now falls at the controls/scenario-table
   boundary; the useful source locations are cells 31–38 and example 81–97.
3. **Not four null effects:** the role candidate passed, the disclaimer contrast is positive,
   one patch direction is positive, and a secondary Your/The score-margin effect remains.
   The stronger joint criteria failed; that does not erase those observations.
4. **Not pronoun equivalence:** the historical Your/The protocol did not preregister an
   equivalence test. The new replication fixes a margin and corrected TOST family before
   execution, but precision and cross-template/model generalization remain unknown.
5. **Philosophy:** Dennett/Frankish motivate an account of constructed self-reports, not a
   theorem that every report is late or causally effective. HOT explicitly permits
   misrepresentation; “HOT demands confidence track accuracy” was therefore not adopted.
   See the [primary-source checks](PHILOSOPHICAL_NOTES.md). The one proposed discriminating
   prediction separates restricted report-use and quality-tracking policies under added
   assumptions, not illusionism from all HOT/GWT implementations.
6. **Ability control:** the injection specification measures a new forced answer after the
   intervention. An unchanged previously recorded answer would be unchanged by construction
   and cannot demonstrate preserved competence. Even equivalent fresh accuracy would not
   prove that all internal computations are unchanged.

## Consistency searches

Scope is the article's Markdown text, compared with its historical base. Existing reports
and figures deliberately preserve their original numbers; a repository-wide zero-hit rule
would contradict that preservation requirement. The ledger repeats article claims by design.

`planned`: **4 occurrences before, 0 after**, case-insensitive; the unmeasured figure list
and prospective historical prose were removed, not relabeled as results.

The old article contained **35 occurrences of 26 distinct percentage literals**.
Searching those same literals in the new article yields **12 occurrences**, accounted for
below. New exact report percentages replace some previous display rounding; no source
number was edited.

Commands used, with the old literal list extracted from `git show`:

```bash
git show 36d9a068b661dff04cf1fa4a29ea47c4f8f48376:docs/article/ARTICLE.md
rg -ni 'planned' docs/article/ARTICLE.md
rg -o -f .cache/article-publication/old_percentages.regex docs/article/ARTICLE.md
```

The temporary pattern file contains the 26 escaped literals below, separated by `|`;
the exact numeric-token extraction is `(?<![\d.])\d+(?:\.\d+)?%`.

| Old literal | Old occurrences | New occurrences | Disposition |
|---|---:|---:|---|
| 48.5% | 1 | 0 | Remove Gemma chronology from main narrative; original reports remain unchanged |
| 46.1% | 1 | 0 | Remove Gemma chronology from main narrative; original reports remain unchanged |
| 32.0% | 1 | 0 | Remove Gemma chronology from main narrative; original reports remain unchanged |
| 80% | 5 | 1 | Retained with report citation; 95% denotes interval level, 80% the historical gate, others documented outcome cells |
| 43.4% | 1 | 0 | Remove Gemma chronology from main narrative; original reports remain unchanged |
| 50.8% | 1 | 0 | Remove Gemma chronology from main narrative; original reports remain unchanged |
| 41.4% | 1 | 0 | Remove Gemma chronology from main narrative; original reports remain unchanged |
| 92% | 1 | 0 | Remove pooled/secondary historical detail from main narrative; retain it in the linked original report |
| 91.47% | 1 | 0 | Remove pooled/secondary historical detail from main narrative; retain it in the linked original report |
| 91.86% | 1 | 0 | Remove pooled/secondary historical detail from main narrative; retain it in the linked original report |
| 67.97% | 1 | 0 | Remove pooled/secondary historical detail from main narrative; retain it in the linked original report |
| 69.53% | 1 | 2 | Retained with report citation; 95% denotes interval level, 80% the historical gate, others documented outcome cells |
| 100% | 2 | 2 | Retained with report citation; 95% denotes interval level, 80% the historical gate, others documented outcome cells |
| 68.75% | 1 | 0 | Remove pooled/secondary historical detail from main narrative; retain it in the linked original report |
| 95% | 5 | 4 | Retained with report citation; 95% denotes interval level, 80% the historical gate, others documented outcome cells |
| 75.00% | 1 | 1 | Retained with report citation; 95% denotes interval level, 80% the historical gate, others documented outcome cells |
| 99.22% | 1 | 2 | Retained with report citation; 95% denotes interval level, 80% the historical gate, others documented outcome cells |
| 89.06% | 1 | 0 | Remove pooled/secondary historical detail from main narrative; retain it in the linked original report |
| 96.88% | 1 | 0 | Remove pooled/secondary historical detail from main narrative; retain it in the linked original report |
| 72.7% | 1 | 0 | Replace text rounding with report values 72.66%, 73.83%, 100.00%, 99.22%; original figure retains its own display rounding |
| 73.8% | 1 | 0 | Replace text rounding with report values 72.66%, 73.83%, 100.00%, 99.22%; original figure retains its own display rounding |
| 100.0% | 1 | 0 | Replace text rounding with report values 72.66%, 73.83%, 100.00%, 99.22%; original figure retains its own display rounding |
| 99.2% | 1 | 0 | Replace text rounding with report values 72.66%, 73.83%, 100.00%, 99.22%; original figure retains its own display rounding |
| 44.9% | 1 | 0 | Condense confidence chapter to its registered selectivity and AUROC; detailed rates remain in confidence report |
| 19.5% | 1 | 0 | Condense confidence chapter to its registered selectivity and AUROC; detailed rates remain in confidence report |
| 20.9% | 1 | 0 | Condense confidence chapter to its registered selectivity and AUROC; detailed rates remain in confidence report |

## Verification

Full suite, with thread limits and offline HF mode to keep verification local:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --no-sync pytest -q
# 165 passed in 556.83s (0:09:16)
```

Documentation/specification checks also passed:

- All 90 article claim IDs occur exactly once and have one ledger entry; no unregistered
  prose remains, and all source file/line ranges exist.
- Local article, ledger and specification links resolve, including section anchors.
- Both JSON files parse; factorial counts, candidate totals and counterfeit-category rules
  agree with their prose; source pins and the documented JSON SHA256 values match.
- Both specifications set execution disabled and authorized spend to zero.
- SHA256 comparison of all 116 snapshotted protected files is unchanged, including evidence,
  result/full reports, audit/preflight JSONs, `src/` and `scripts/`.
- `git diff --check` passes; only the requested documentation and new specifications change.

The lightweight checks are consistency checks, not evidence that an unimplemented protocol
will run correctly or have adequate statistical power. No scientific result report or
historical evidence file was rewritten to match the new narrative.
