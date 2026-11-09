# Query-bound self-reference: fixed-sample report

Recorded Qwen2.5-7B-Instruct selections; one permission template.

Status: **incomplete_or_invalid**. Recorded 16128/16128 choices; 47/48 valid complete worlds.
Decision: **incomplete_or_invalid_no_inference**.

All 16128 scheduled cases remain in denominators, including missing as invalid administrative failures. No inferential CI/test with incomplete or invalid worlds. Undefined tests cannot qualify. E and F are correlated. Passing lookup does not establish dynamic competence or authorize interventions. No equivalence, consciousness or human-illusionism conclusion.

## The question

An operator owns one of two accounts. We ask for a successful command using either your/their active connection, the operator's name, or the same account's name. Within each comparison the task facts and correct answer are identical. In the primary checkpoint both accounts have changed permissions; reversing update order keeps the answer fixed. A rule that always chooses the newest grant succeeds on half the primary cases.

## Prespecified contrasts

For each world, $E=q_{self,possessive}-q_{self,account}$, $F=A_{self,account}-A_{self,possessive}$ and $S=F-(A_{other,account}-A_{other,possessive})$.

Positive E means more foreign-account choices; positive F means an accuracy cost. Positive S means a larger cost for the addressee than for the other operator. All three expected directions were fixed before responses. E and F are correlated, not independent replications. F−E is the contrast in remaining errors.

10000 paired world draws, seed 1729; nominal 95% CIs. Two-sided paired-world t tests, df 47, normal-mean approximation; Holm over E,F,S only.

| Contrast | Estimate (pp) | Nominal 95% CI (pp) | Raw p | Holm p | Test status |
|---|---:|---|---:|---:|---|
| E | +35.026 | withheld | None | 1 | incomplete_or_invalid_worlds |
| F | +35.026 | withheld | None | 1 | incomplete_or_invalid_worlds |
| S | +10.091 | withheld | None | 1 | incomplete_or_invalid_worlds |

Undefined tests use a labeled conservative value of 1 only inside Holm; they cannot qualify. Zero variance never proves equivalence.

## Accuracy, foreign choices and error budgets

| Stage / owner / alias | Correct / scheduled | Accuracy (%) | Foreign (%) | Error budget (%) | Margin (nats) | Missing / invalid recorded |
|---|---:|---:|---:|---:|---:|---:|
| after_both/other/account_name | 1478/1536 | 96.22 | 2.73 | 3.78 | +8.561 | 0 / 0 |
| after_both/other/owner_name | 1155/1536 | 75.20 | 23.89 | 24.80 | +2.984 | 0 / 0 |
| after_both/other/possessive | 1095/1536 | 71.29 | 28.65 | 28.71 | +1.682 | 0 / 0 |
| after_both/self/account_name | 1462/1536 | 95.18 | 3.45 | 4.82 | +7.663 | 0 / 0 |
| after_both/self/owner_name | 1096/1536 | 71.35 | 20.51 | 28.65 | +3.293 | 0 / 0 |
| after_both/self/possessive | 924/1536 | 60.16 | 38.48 | 39.84 | +1.089 | 0 / 1 |
| before/other/account_name | 361/384 | 94.01 | 5.73 | 5.99 | +11.659 | 0 / 0 |
| before/other/owner_name | 307/384 | 79.95 | 20.05 | 20.05 | +6.975 | 0 / 0 |
| before/other/possessive | 278/384 | 72.40 | 27.60 | 27.60 | +4.009 | 0 / 0 |
| before/self/account_name | 331/384 | 86.20 | 4.69 | 13.80 | +10.347 | 0 / 0 |
| before/self/owner_name | 295/384 | 76.82 | 9.38 | 23.18 | +6.910 | 0 / 0 |
| before/self/possessive | 280/384 | 72.92 | 26.82 | 27.08 | +4.552 | 0 / 0 |
| snapshot/other/account_name | 743/768 | 96.74 | 3.12 | 3.26 | +14.099 | 0 / 0 |
| snapshot/other/owner_name | 627/768 | 81.64 | 18.23 | 18.36 | +8.581 | 0 / 0 |
| snapshot/other/possessive | 541/768 | 70.44 | 29.56 | 29.56 | +4.452 | 0 / 0 |
| snapshot/self/account_name | 702/768 | 91.41 | 3.12 | 8.59 | +11.834 | 0 / 0 |
| snapshot/self/owner_name | 564/768 | 73.44 | 10.16 | 26.56 | +7.402 | 0 / 0 |
| snapshot/self/possessive | 554/768 | 72.14 | 27.60 | 27.86 | +4.820 | 0 / 0 |

At the **fixed observed accuracies**, the categorical contrast E is bounded by [-4.818, +39.844] pp. This is not a pre-run generator bound. All-success cells and all error budgets are retained in analysis.json. The accuracy endpoint remains ceiling-limited too.

Revoked-target/other categories are not applicable before updates or in snapshots without printed history. Missing observations are administrative invalids, included in all-scheduled denominators and identified separately. Error-conditional shares use scheduled failures including missing cases; with no errors they are undefined. Incomplete-data estimates are descriptive and have no inferential CI or test.

## Lookup and paired controls

Lookup numerical thresholds passed: **False**. Eligible model gate passed: **False**.

| Control | Fully correct pairs / scheduled | Rate | Required gate |
|---|---:|---:|---|
| event_order/after_both/other/account_name | 713/768 | 92.84% | False |
| event_order/after_both/other/owner_name | 434/768 | 56.51% | False |
| event_order/after_both/other/possessive | 403/768 | 52.47% | False |
| event_order/after_both/self/account_name | 698/768 | 90.89% | False |
| event_order/after_both/self/owner_name | 436/768 | 56.77% | False |
| event_order/after_both/self/possessive | 294/768 | 38.28% | False |
| grant_mapping/after_both/other/account_name | 711/768 | 92.58% | False |
| grant_mapping/after_both/other/owner_name | 483/768 | 62.89% | False |
| grant_mapping/after_both/other/possessive | 389/768 | 50.65% | False |
| grant_mapping/after_both/self/account_name | 697/768 | 90.76% | False |
| grant_mapping/after_both/self/owner_name | 398/768 | 51.82% | False |
| grant_mapping/after_both/self/possessive | 323/768 | 42.06% | False |
| grant_mapping/snapshot/other/account_name | 359/384 | 93.49% | False |
| grant_mapping/snapshot/other/owner_name | 248/384 | 64.58% | False |
| grant_mapping/snapshot/other/possessive | 165/384 | 42.97% | False |
| grant_mapping/snapshot/self/account_name | 320/384 | 83.33% | False |
| grant_mapping/snapshot/self/owner_name | 218/384 | 56.77% | False |
| grant_mapping/snapshot/self/possessive | 197/384 | 51.30% | False |
| ownership/after_both/other/account_name | 714/768 | 92.97% | False |
| ownership/after_both/other/owner_name | 400/768 | 52.08% | False |
| ownership/after_both/other/possessive | 337/768 | 43.88% | False |
| ownership/after_both/self/account_name | 700/768 | 91.15% | False |
| ownership/after_both/self/owner_name | 358/768 | 46.61% | False |
| ownership/after_both/self/possessive | 194/768 | 25.26% | False |
| ownership/before/other/account_name | 135/192 | 70.31% | True |
| ownership/before/other/owner_name | 115/192 | 59.90% | True |
| ownership/before/other/possessive | 87/192 | 45.31% | False |
| ownership/before/self/account_name | 184/192 | 95.83% | True |
| ownership/before/self/owner_name | 108/192 | 56.25% | True |
| ownership/before/self/possessive | 90/192 | 46.88% | False |
| ownership/snapshot/other/account_name | 344/384 | 89.58% | True |
| ownership/snapshot/other/owner_name | 243/384 | 63.28% | True |
| ownership/snapshot/other/possessive | 157/384 | 40.89% | False |
| ownership/snapshot/self/account_name | 349/384 | 90.89% | True |
| ownership/snapshot/self/owner_name | 217/384 | 56.51% | True |
| ownership/snapshot/self/possessive | 178/384 | 46.35% | False |

Every one of eight named lookup cells and eight corresponding pair cells must reach 80%. Possessive errors are outcomes, not screening exclusions. Passing those controls does not establish dynamic update competence or authorize an intervention. After-both named controls and both event orders remain visible.

## Scope and reading guide

The report retains all stage/order contrasts, both owner-name comparisons, score margins, world-level effects, and accuracy by account, operator, answer position, command and order in analysis.json. Those are descriptive analyses, not replacement endpoints. examples.md uses the example selected before responses; it does not select an unusually strong model answer.

If E and F pass but S does not, the candidate concerns reference-sensitive own-query behavior without demonstrated own-versus-other specificity. A negative or incomplete result cannot establish unchanged behavior. This task does not measure private internal access, subjective experience or human illusionism.
