# Query-bound self-reference: fixed-sample report

Recorded Qwen2.5-7B-Instruct selections; one permission template.

Status: **incomplete_or_invalid**. Recorded 2688/16128 choices; 8/48 valid complete worlds.
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
| E | +6.445 | withheld | None | 1 | incomplete_or_invalid_worlds |
| F | +6.510 | withheld | None | 1 | incomplete_or_invalid_worlds |
| S | +2.018 | withheld | None | 1 | incomplete_or_invalid_worlds |

Undefined tests use a labeled conservative value of 1 only inside Holm; they cannot qualify. Zero variance never proves equivalence.

## Accuracy, foreign choices and error budgets

| Stage / owner / alias | Correct / scheduled | Accuracy (%) | Foreign (%) | Error budget (%) | Margin (nats) | Missing / invalid recorded |
|---|---:|---:|---:|---:|---:|---:|
| after_both/other/account_name | 245/1536 | 15.95 | 0.46 | 84.05 | +8.434 | 1280 / 0 |
| after_both/other/owner_name | 178/1536 | 11.59 | 5.01 | 88.41 | +2.183 | 1280 / 0 |
| after_both/other/possessive | 176/1536 | 11.46 | 5.21 | 88.54 | +1.228 | 1280 / 0 |
| after_both/self/account_name | 237/1536 | 15.43 | 0.98 | 84.57 | +7.491 | 1280 / 0 |
| after_both/self/owner_name | 150/1536 | 9.77 | 4.49 | 90.23 | +2.175 | 1280 / 0 |
| after_both/self/possessive | 137/1536 | 8.92 | 7.42 | 91.08 | +0.611 | 1280 / 0 |
| before/other/account_name | 61/384 | 15.89 | 0.78 | 84.11 | +12.183 | 320 / 0 |
| before/other/owner_name | 46/384 | 11.98 | 4.69 | 88.02 | +5.326 | 320 / 0 |
| before/other/possessive | 37/384 | 9.64 | 7.03 | 90.36 | +2.227 | 320 / 0 |
| before/self/account_name | 58/384 | 15.10 | 1.04 | 84.90 | +10.120 | 320 / 0 |
| before/self/owner_name | 43/384 | 11.20 | 2.60 | 88.80 | +5.192 | 320 / 0 |
| before/self/possessive | 41/384 | 10.68 | 5.99 | 89.32 | +3.379 | 320 / 0 |
| snapshot/other/account_name | 124/768 | 16.15 | 0.52 | 83.85 | +13.334 | 640 / 0 |
| snapshot/other/owner_name | 95/768 | 12.37 | 4.30 | 87.63 | +6.238 | 640 / 0 |
| snapshot/other/possessive | 88/768 | 11.46 | 5.21 | 88.54 | +3.564 | 640 / 0 |
| snapshot/self/account_name | 109/768 | 14.19 | 0.39 | 85.81 | +11.127 | 640 / 0 |
| snapshot/self/owner_name | 70/768 | 9.11 | 2.21 | 90.89 | +5.584 | 640 / 0 |
| snapshot/self/possessive | 84/768 | 10.94 | 5.47 | 89.06 | +3.343 | 640 / 0 |

At the **fixed observed accuracies**, the categorical contrast E is bounded by [-84.570, +91.081] pp. This is not a pre-run generator bound. All-success cells and all error budgets are retained in analysis.json. The accuracy endpoint remains ceiling-limited too.

Revoked-target/other categories are not applicable before updates or in snapshots without printed history. Missing observations are administrative invalids, included in all-scheduled denominators and identified separately. Error-conditional shares use scheduled failures including missing cases; with no errors they are undefined. Incomplete-data estimates are descriptive and have no inferential CI or test.

## Lookup and paired controls

Lookup numerical thresholds passed: **False**. Eligible model gate passed: **False**.

| Control | Fully correct pairs / scheduled | Rate | Required gate |
|---|---:|---:|---|
| event_order/after_both/other/account_name | 117/768 | 15.23% | False |
| event_order/after_both/other/owner_name | 60/768 | 7.81% | False |
| event_order/after_both/other/possessive | 60/768 | 7.81% | False |
| event_order/after_both/self/account_name | 109/768 | 14.19% | False |
| event_order/after_both/self/owner_name | 50/768 | 6.51% | False |
| event_order/after_both/self/possessive | 30/768 | 3.91% | False |
| grant_mapping/after_both/other/account_name | 117/768 | 15.23% | False |
| grant_mapping/after_both/other/owner_name | 74/768 | 9.64% | False |
| grant_mapping/after_both/other/possessive | 62/768 | 8.07% | False |
| grant_mapping/after_both/self/account_name | 110/768 | 14.32% | False |
| grant_mapping/after_both/self/owner_name | 45/768 | 5.86% | False |
| grant_mapping/after_both/self/possessive | 48/768 | 6.25% | False |
| grant_mapping/snapshot/other/account_name | 60/384 | 15.62% | False |
| grant_mapping/snapshot/other/owner_name | 35/384 | 9.11% | False |
| grant_mapping/snapshot/other/possessive | 26/384 | 6.77% | False |
| grant_mapping/snapshot/self/account_name | 47/384 | 12.24% | False |
| grant_mapping/snapshot/self/owner_name | 25/384 | 6.51% | False |
| grant_mapping/snapshot/self/possessive | 27/384 | 7.03% | False |
| ownership/after_both/other/account_name | 117/768 | 15.23% | False |
| ownership/after_both/other/owner_name | 52/768 | 6.77% | False |
| ownership/after_both/other/possessive | 51/768 | 6.64% | False |
| ownership/after_both/self/account_name | 113/768 | 14.71% | False |
| ownership/after_both/self/owner_name | 33/768 | 4.30% | False |
| ownership/after_both/self/possessive | 19/768 | 2.47% | False |
| ownership/before/other/account_name | 25/192 | 13.02% | True |
| ownership/before/other/owner_name | 14/192 | 7.29% | True |
| ownership/before/other/possessive | 6/192 | 3.12% | False |
| ownership/before/self/account_name | 31/192 | 16.15% | True |
| ownership/before/self/owner_name | 11/192 | 5.73% | True |
| ownership/before/self/possessive | 9/192 | 4.69% | False |
| ownership/snapshot/other/account_name | 57/384 | 14.84% | True |
| ownership/snapshot/other/owner_name | 31/384 | 8.07% | True |
| ownership/snapshot/other/possessive | 24/384 | 6.25% | False |
| ownership/snapshot/self/account_name | 52/384 | 13.54% | True |
| ownership/snapshot/self/owner_name | 25/384 | 6.51% | True |
| ownership/snapshot/self/possessive | 22/384 | 5.73% | False |

Every one of eight named lookup cells and eight corresponding pair cells must reach 80%. Possessive errors are outcomes, not screening exclusions. Passing those controls does not establish dynamic update competence or authorize an intervention. After-both named controls and both event orders remain visible.

## Scope and reading guide

The report retains all stage/order contrasts, both owner-name comparisons, score margins, world-level effects, and accuracy by account, operator, answer position, command and order in analysis.json. Those are descriptive analyses, not replacement endpoints. examples.md uses the example selected before responses; it does not select an unusually strong model answer.

If E and F pass but S does not, the candidate concerns reference-sensitive own-query behavior without demonstrated own-versus-other specificity. A negative or incomplete result cannot establish unchanged behavior. This task does not measure private internal access, subjective experience or human illusionism.
