# Publication rewrite, round two: prose and categorical error check

Base: `1a86a12`; date: 2026-11-08. No new model inference or paid job.
This section records the second revision; the first-round record is retained below as history.

Article word count: **1,945 before → 2,885 after**; opening scene: **192 words**.
The count removes HTML comments, link destinations, image markup, fenced reproduction
commands and display equations; it includes headings, prose, captions and table text.
For comparison, whitespace-delimited source counts are 2,304 before and 3,152 after.
Paragraph-level coverage comprises **57 blocks**, including tables, equations and commands.

## Model-choice source check

The pinned [Qwen model card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/a09a35458c702b33eeacc393d103063234e8bc28/README.md)
was checked for publicly available weights and the documented loading interface.
`docs/QWEN_POSSESSIVE_RUN.md:10-29` supplies the historical bounded cost and pinned runtime.
Calling this a practical balance of cost, access and reproducibility is an engineering
rationale, not a measured optimality claim or a comparison against other checkpoints.
`docs/OWNERSHIP_REPLICATION.md:22-38` already fixes Mistral as the second model; that
specification has not been edited or executed in this round.

## Prose, IDs and retained evidence

- Expanded the Cedar/Birch example into a scene: initial permissions, Cedar's replacement,
  the question, Birch's selected command and refusal, then the context-line switch and success.
  All actions and outputs come from `docs/QWEN_ROLE_RESULTS.md:81-97`.
- Removed alternate title proposals C002–C003; retained the favorite as the sole title.
- Removed **all C001–C090 sentence-level markers from the article**. The source ledger retains
  those identifiers and maps their claims to P01–P57 paragraph/block markers; there is no
  factual sentence that quietly loses source coverage. Transitions share their paragraph's
  coverage rather than gaining artificial empirical claim IDs.
- C004–C006 and C012–C014 are expanded into P01–P04. C015 is recast to give the simulator
  paragraph an explicit subject. C036 remains in P23 and is extended by the new count in P24.
  C037–C038 and C080 are updated because a post hoc count now exists, while a prespecified
  categorical replication still does not. C039 moves unchanged into P22, the findings section.
  C040 is replaced by the explicit reason for probing that positive finding; C086 now describes
  paragraph-level coverage. Every other original claim is mapped in the ledger.
- **All 28 original blocks containing numeric evidence, thresholds, equations or reproduction
  identifiers are preserved**, excluding the removed editorial title numbering. Prose numeric
  sentences remain verbatim; tables retain their original cells while adding the interaction
  column. No numerical outcome sentence was dropped to make room for the scene.
- Renamed the methods section to distinguish controls on the role effect from the separate
  confidence test; it now opens directly with format. Added the +1/−1/0 confidence payoff,
  the Reference-label explanation, Qwen rationale and second-model pointer.
- Kept both existing figures, all frozen rules, positive secondary findings and philosophical
  boundaries. Neither the theories nor the empirical claims are strengthened by the rewrite.

## The one new CPU calculation

Script: [`scripts/count_possessive_errors.py`](../../scripts/count_possessive_errors.py).
Deterministic output: [`review/qwen-possessive-error-count.json`](../../review/qwen-possessive-error-count.json).
The script reads the unchanged archive identified by SHA256
`d521a63c21c360b33ba8452ab5d572eaf0d06c4e4be02df02425dfc1c2fe3e59` and verifies its 54 payload checksums.
It checks all 6,144 recorded jobs against the frozen plan and saved score
argmaxes, reconstructs their simulator outcomes, then counts only relevant after-updates:
**1,536 choices from 16 scenarios**.

Classification follows `scripts/review_qwen_evidence.py:381-401` and
`docs/QWEN_RESULTS.md:80`: invalid/error first, then revoked target command, then current
other-account command, then another command. Correct choices are retained separately so
that both the all-choice denominator and the error-only denominator remain visible.
This archive contains no invalid scores; the new test fixtures explicitly cover that category.

| Context cell | All choices | Errors | Current other-account command | Revoked target command | Other unavailable command |
|---|---:|---:|---:|---:|---:|
| your/target | 256 | 70 | 53 | 0 | 17 |
| your/other | 256 | 0 | 0 | 0 | 0 |
| the/target | 256 | 67 | 46 | 0 | 21 |
| the/other | 256 | 2 | 1 | 0 | 1 |
| reference/target | 256 | 46 | 38 | 0 | 8 |
| reference/other | 256 | 11 | 7 | 0 | 4 |

**Title decision:** retain *Naming the Agent, Choosing for the Other*. In the target-named
cells the current other-account command accounts for 53/70 Your errors and 46/67 The errors,
and no error selects the revoked target command. This supports the descriptive direction;
it does not establish a specific neural mechanism, a new effect test or generalization.
Zero errors in Your/other gives no error-composition percentage; the JSON preserves zero
counts without inventing a denominator. Full scenario counts and record-category mappings
remain available in the JSON rather than only a favorable selected subset.

**Confidence status:** post hoc descriptive inspection of already observed development
outputs. No new confidence interval, p-value, model likelihood or frozen candidate decision
was calculated. Counts recur in another cohort, but this is not a preregistered replication.
The original result report and its decision remain unchanged.

Reproduction without modifying an existing audit:

```bash
uv run --no-sync python scripts/count_possessive_errors.py > /tmp/qwen-possessive-error-count.json
cmp review/qwen-possessive-error-count.json /tmp/qwen-possessive-error-count.json
```

## Where the requested wording needed correction

1. **Unchanged account:** the other account does not receive the update, so asking about it
   would remove an updating demand. But the paired context columns do not switch the queried
   account: both ask about the updated target. The article treats this as an explicit rival
   interpretation and distinguishes a stable competing command from a genuinely easier
   unchanged-target task. The initial 36/41 and 33/39 counts are again shown in that discussion,
   explicitly as post hoc evidence from one cohort; they mainly oppose simple stale-command
   selection, not every possible failure of update processing.
2. **Heterogeneity:** 7/8 concerns Your/Reference, while 4/16 concerns Your/The. Calling the
   change proof of greater heterogeneity of the same effect would compare different estimands.
   The table labels both contrasts and retains the latest 15/16 Your/Reference anchor from
   `docs/QWEN_POSSESSIVE_RESULTS.md:94-98`. Mixed signs and zeros describe the latest primary
   possessive increment; they do not establish reduced stability of the underlying role gap.
3. **Ceiling:** 256/256 successes leave no empirical failures for the scenario bootstrap to
   resample. The article explains why a collapsed empirical interval cannot show reliability
   on unfamiliar scenarios or reveal upward accuracy changes at this ceiling. It does not
   replace the historical interval with a newly calculated one.
4. **Causal interpretation:** error categories alone cannot distinguish misbinding, salience,
   instruction interpretation or upstream update-processing errors. The new count narrows
   the observed output pattern, not its neural cause. Confidence remains a separate assay.

## Verification

Full suite completed successfully, including the unchanged original evidence auditors:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --no-sync pytest -q
# 172 passed in 575.51s (0:09:35)
```

The seven new cases cover error categories and the stored-output counter; the existing
Gemma, Qwen, role, patch, Your/The and confidence evidence tests remain green.

- Ruff check and format checks pass for the new script and tests; `git diff --check` passes.
- Paragraph coverage, source line ranges, local links and numeric-claim preservation pass.
- SHA256 comparison preserves all 387 tracked files outside the three editable article
  documents, including every old script, raw archive, result report, audit/preflight JSON,
  `src/`, both specification pairs and `PHILOSOPHICAL_NOTES.md`.
- The new counter imports no study model backend and makes no network request; tests cover
  stale/foreign/unused/correct distinctions, invalid scoring, archive mutation and exact
  reproduction of the committed JSON.

---

## First-round record (historical, at base 1a86a12)

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

---

# Publication polish, round three: record selection, reading order and count coverage

Base: `3401a81`; date: 2026-11-08. No new model inference, tokenizer execution or paid job.
Earlier revision records above remain unchanged.

Article word count: **2,885 before → 3,167 after**, using the same counting rule as round two
(exclude comments, link destinations, images, fenced commands and display equations;
include headings, prose, captions and tables). Source whitespace counts: 3,152 → 3,432.
The opening scene and title remain unchanged.

## Changed blocks and stable IDs

- **P24:** adds exactly three sentences from the existing error-count JSON: the two
  Reference error compositions, then the scenario error range and strict-majority count.
  Post hoc status and the absence of a new confidence interval or decision remain explicit.
- **P33/P35:** introduces the descriptive Your/Reference contrast (+13.67 percentage points,
  positive in 15/16 scenarios) before the primary Your/The result, positive in 4/16.
  These values were already reported in `docs/QWEN_POSSESSIVE_RESULTS.md:77-98`.
  **The reading order changes, not the numerical results, thresholds or primary contrast.**
  The Reference comparison does not become an alternative route to passing the primary test.
- **P36:** follows that reordered comparison with its content verbatim, including the
  positive secondary margin and its limitations. No secondary statistic was recalculated.
- **P41a (added):** names the target/updated-record coincidence and distinguishes a possible
  anchoring explanation from the simplest named-record lookup rule, which fails the example.
  The suffix preserves all existing P01–P57 identifiers; the ledger now covers 58 blocks.
- **P42/P43:** brings the stable competing record and the Your/other ceiling together,
  preserves the fixed queried target, and narrows what zero revoked-command errors rule out.
- **P16, P22, P37 and P38:** byte-identical. All other unlisted article blocks remain unchanged.
- **Ledger:** updates the complete changed blocks, their sources and all affected line links;
  it labels the proposed mechanism as a hypothesis, not a measured internal computation.
- **Replication prose:** appends one explicitly supplementary paragraph proposing a secondary
  after-update 2×2 of mentioned versus updated account, holding the queried target fixed and
  retaining categorical error direction and the all-choice denominator. The frozen design
  already balances these combinations. The primary endpoint and normative JSON do not change.
- **Review guide:** replaces “sentence-level claim ledger” with “paragraph-level claim ledger”.

## Existing counts, their denominator and uncertainty

The source remains `review/qwen-possessive-error-count.json`, unchanged:
`cells.reference/target` gives **38/46** foreign-current-command errors and
`cells.reference/other` gives **7/11**. For the dispersion sentence, sum errors and
`other_actor_command` across **all six frame/relation conditions within each scenario**
in `per_scenario`, restricted by the saved population to after target-relevant updates.
The resulting error range is **2–28 per scenario**; **12/16** scenarios have a strict
foreign-command majority **among errors**, not among all selections. Ties are not majorities.
This is a descriptive reduction of the existing JSON, not a new subgroup hypothesis test,
confidence interval, independent sample or alteration of any saved result.

Reproduce the permitted reduction from the repository root:

```bash
uv run --no-sync python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path('review/qwen-possessive-error-count.json').read_text())
for key in ('reference/target', 'reference/other'):
    cell = data['cells'][key]
    print(key, cell['other_actor_command'], '/', cell['errors'])
counts = [
    (sum(c['errors'] for c in cells.values()),
     sum(c['other_actor_command'] for c in cells.values()))
    for cells in data['per_scenario'].values()
]
print('error range', min(e for e, f in counts), max(e for e, f in counts))
print('strict majority', sum(2*f > e for e, f in counts), '/', len(counts))
PY
```

## Where the requested interpretation needed qualification

The code defines relevance as `target == event["actor"]`
(`src/self_model_study/action_task.py:138`); the context swap preserves the named query
(`src/self_model_study/role_control.py:97-118`). Thus target-named and changed-account-named
coincide in the primary stratum. That confounding is now explicit.
However, the proposed rule “read the named account's current permission” predicts
`mark_violet` when Birch is named. The recorded example instead selects **`mark_amber`**
for Cedar in that condition (`docs/QWEN_ROLE_RESULTS.md:81-97`). The rule predicts the
opposite direction, so the article cannot state that it explains the observed reversal.
A broader context-dependent record-selection mechanism remains an open hypothesis.
Zero revoked-target errors only weakens the specific account “retain the target as subject,
ignore its update”; it does not identify or exclude other record-selection mechanisms.

The unchanged record is a structurally simpler lookup, but mentioning it does not change
which account the question asks about. P42 therefore connects structural ease with the
ceiling limitation without claiming that the observed easier cell asks an unchanged-target
question or that either fact establishes the mechanism.

## Stored-token verification for the wording caveat

The immutable archive `review/evidence/qwen-possessive-f2baaa2fb6b74880.tar.gz`, SHA256
`d521a63c21c360b33ba8452ab5d572eaf0d06c4e4be02df02425dfc1c2fe3e59`, retains actual token IDs
in `run/records.jsonl`. Pairing by `job.row.scene_id` and `job.row.relation`, the saved
`result.prompt_token_ids` are exactly one token shorter for Reference than for both
Your and The in every matched triple. This checks stored lengths; it performs no new
tokenization or model inference. `docs/QWEN_POSSESSIVE_RESULTS.md:49-51,94-98` supplies
the distinction between the controlled Your/The substitution and the bundled Reference
contrast. The caveat does not attribute the result to length or to any particular word.

## Round-three verification

Full suite, with local thread limits and offline Hugging Face mode:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --no-sync pytest -q
# 172 passed in 574.23s (0:09:34)
```

The unchanged `scripts/review_possessive_evidence.py` passes against the original archive.
The unchanged `scripts/count_possessive_errors.py`, redirected to a temporary file, reproduces
`review/qwen-possessive-error-count.json` byte-for-byte. Neither command rewrites the evidence.

Documentation checks pass: all 58 block texts exactly match their ledger entries, local
links and section anchors resolve, and every cited source line range exists. Comparison with
the base confirms that only P24, P33, P35, P42 and P43 changed, with P41a added; all prior
numeric occurrences survive. P16, P22, P36, P37 and P38 remain byte-identical. SHA256 checks
confirm all 388 other tracked files are unchanged, including `designs/`, `review/evidence/`,
the original error-count JSON, audits, preflights, existing result reports, scripts and `src/`.
The original revision history and replication prose are preserved before the appended
supplements. `git diff --check` passes. Only the five requested documentation files change.

---

# Publication polish, round four: the crossed control stratum

Base: `7784d1b`; date: 2026-11-08. No new model inference or analysis of raw outputs.
All added empirical values come from the existing full report; no interval, significance
test or candidate decision has been added. Earlier revision records remain unchanged.

Article word count: **3,167 before → 3,415 after**, using the same rule as preceding rounds:
exclude comments, link destinations, images, fenced commands and display equations;
include headings, prose, captions and tables. Source whitespace counts: 3,432 → 3,677.

## Exact scope and stable IDs

- **P41a:** changes only the final sentence to introduce the partial clarification from
  irrelevant updates. The observation that the simplest named-record rule predicts the
  opposite direction in the Cedar/Birch example remains verbatim.
- **P41b (new):** gives the relevant and irrelevant target-named → other-named accuracy
  pairs for Your, The and Reference, the conditional freshness argument, the distinction
  between accuracy and score-margin interactions, and the limits in the same paragraph.
  Its ledger sources are exclusively `docs/QWEN_POSSESSIVE_FULL_REPORT.md:3-9,24-40,43-91,172-189`.
- **P43:** adds the irrelevant-update challenge to a freshness-only account for Your/The,
  with Reference explicitly excepted. Zero revoked-target errors remain a separate,
  weaker argument against ignoring an update while retaining the target as subject.
- **P44:** changes “do not separate these explanations” to “do not separate them fully”.
- **Replication supplement:** adds one sentence explaining why the existing control
  stratum only partly anticipates the prospective categorical-error analysis; the 2×2
  stays in place. No frozen endpoint, threshold or normative JSON changes.
- **Ledger:** updates those blocks and shifted line links; all previous P identifiers
  remain stable. P41b brings coverage to 59 blocks. No other article block changes,
  including P16, P22, P37, P38 and the gap definition in P34.

## Corrections required by the source

The requested parenthesized irrelevant-update differences used the reverse of the article's
existing **other minus target** subtraction. P41b keeps that definition in both strata:
the control gaps are **+5.47**, **+2.73** and **−1.96** percentage points for Your, The and
Reference, respectively. These are explicitly differences of the report's displayed,
rounded percentages, not newly estimated unrounded effects.

The requested signs can instead describe unchanged-account-named minus changed-account-named:
that orientation coincides with other minus target after relevant updates, but reverses it
after irrelevant updates. This would change the contrast being compared across strata;
it is not a sign reversal of the unchanged P34 accuracy interaction.

Consequently, **the accuracy interaction does not reverse sign**: the Your gap remains
larger than the The gap in both strata. The requested negative accuracy interaction cannot
be stated consistently with the listed cells and the unchanged P34 definition.
The article reports its positive direction in the control stratum without adding a new
numeric interaction estimate. In contrast, the score-margin interaction really does change
from **+0.346** to **−0.398 nats**, as recorded at full-report lines 188–189.

The claim that target naming hurts in both strata also needs a frame restriction:
it holds for **Your and The**, whereas Reference has higher target-named accuracy after
irrelevant updates. This exception is retained in P41b and P43, so the freshness-only
challenge is not presented as an identical pattern across all formulations.
Reference/other accuracies occur at full-report lines **24–25**, outside the suggested
27–40 range; the ledger cites the actual rows rather than an incomplete range.

## Explicit ceiling limit and interpretation boundary

The irrelevant-update other-named cells are around **89–94%**, near the accuracy ceiling.
They have limited upward headroom, but they are not all-success cells; the new paragraph
does not extend P16's all-success bootstrap argument to them. The stratum also changes
which account receives the update and is a competence control, not the primary endpoint.
The existing crossing therefore supplies a partial descriptive check, not a complete
identification of a mechanism or a new decision. Naming effects without a freshness
component remain possible. These limits are explicit in P41b and motivate retaining the
prospective crossed categorical-error comparison in the replication supplement.

## Round-four verification

Full suite, with local thread limits and offline Hugging Face mode:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --no-sync pytest -q
# 172 passed in 568.64s (0:09:28)
```

Documentation checks pass: all 59 block texts match their ledger entries, local links and
section anchors resolve, and cited line ranges exist. The six displayed accuracy pairs
and their signed differences agree with the full report; arithmetic on those displayed
cells confirms positive Your/The accuracy interactions in both strata, while the saved
margin interaction changes sign. P41b uses only full-report sources.

The scope check confirms that only P41a, P43 and P44 changed and P41b was added; all other
article blocks and all prior numeric occurrences are preserved. The replication supplement
contains exactly one added sentence. SHA256 checks confirm that all 389 protected tracked
files remain unchanged, including both design JSONs, every result report, evidence archive,
audit, preflight, `src/` and `scripts/`. Existing revision-history text is preserved.
`git diff --check` passes. Only the four requested documentation files change.
