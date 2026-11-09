# All query-reference selections recorded; one exact tie prevents inference

**2026-11-09:** All five newly submitted jobs have ended. Blocks 02–05 have provider
status `COMPLETED`; block 01 has `ERROR` because its manifest is `complete_with_errors`.
Including the earlier block 00, all **16,128/16,128 selections** are recorded and
exported. There are **16,127 valid selections, one exact score tie and no missing cases**.
The data were retrieved and verified; no replacement GPU job was started.

The [combined report](../review/query-reference-results/report.md),
[analysis JSON](../review/query-reference-results/analysis.json),
[fixed examples](../review/query-reference-results/examples.md) and
[verification/archive inventory](../review/query-reference-results/verification.json)
retain the frozen analysis and all six original archives. The five planned figures
are available as SVG/PDF/PNG in [the figures directory](../review/query-reference-results/figures).

## Why one job is marked ERROR

In world `query-self-v1:0011`, after both updates, the self/possessive query gave
`mark_silver` and `mark_ochre` exactly the same stored summed log-likelihood:
**−0.6939487457275391**. The latter is the queried account's current command; the
former belongs to the other account. The other two scores are lower. The scorer
therefore records `tie`, selects no command and counts a failed selection, as required.
The [complete recorded case](../review/query-reference-results/invalid-records.json)
includes the prompt, token IDs, scores and simulator outcome.

All 2,688 cases in block 01 were processed and its archive was uploaded successfully.
The [worker](../scripts/hf_worker.py) deliberately exits with code 2 for
`complete_with_errors`, explaining the provider status. This was not a lost run or a
missing export. The archived equality does not establish why the scores became equal;
no claim about a particular numerical or internal mechanism is made.

Under the unchanged validity rule, this leaves **47/48 valid complete worlds**.
The frozen analyzer returns `incomplete_or_invalid_no_inference`: confidence intervals
and p-values are withheld. Values of 1 in the Holm column are explicitly labeled
placeholders for undefined tests, not observed p-values. The tie is not broken,
rescored, excluded or replaced to obtain an eligible analysis.

## Descriptive results and the separate control failure

These primary-stage accuracies retain every scheduled case, including the tie as a
failed selection:

| Queried owner | Possessive | Operator name | Account name |
|---|---:|---:|---:|
| self | 924/1,536 = 60.16% | 1,096/1,536 = 71.35% | 1,462/1,536 = 95.18% |
| other | 1,095/1,536 = 71.29% | 1,155/1,536 = 75.20% | 1,478/1,536 = 96.22% |

The recorded descriptive contrasts are **E = +35.026 pp**, **F = +35.026 pp** and
**S = +10.091 pp**. They have no inferential interval or qualifying test under this
protocol. Their magnitude is not a passing candidate decision.

Independently of the tie, **three of eight named lookup accuracy cells** and
**five of eight required paired lookup controls** fall below 80%. The affected
accuracy cells are before/self/operator-name, before/other/operator-name and
snapshot/self/operator-name. Failed paired controls include all four operator-name
cells and before/other/account-name. These controls contain no invalid selections;
the tie occurs in the after-both outcome, outside the lookup gate. Resolving that tie
would therefore not fix the observed lookup-control failure.

The [reporting commitment](QUERY_REFERENCE_INTERPRETATION_PLAN.md) remains in force:
report the query-form differences and weak alias controls, without claiming a
functional self-model or a passing specificity result. Human illusionism is not
established by these task errors.

## Verification and provenance

All six archive hashes and **474 internal file checksums** passed. The frozen analyzer
validated all records, token boundaries, simulator outcomes and common execution
provenance before merging. The source commit remains `59061ca`, and the article
remains unchanged at `article-v1`. This retrieval and analysis used only saved data;
no model inference, paid resubmission or protocol change was performed.
