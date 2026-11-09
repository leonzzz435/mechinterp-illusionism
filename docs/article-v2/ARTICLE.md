# The Right Command for the Wrong Account

*How query wording and printed update history changed one language model’s choices.*

**Article v2 — evidence draft, 9 November 2026.** This is a new account of the completed query-reference study, not a revision of the [frozen article-v1](../article/ARTICLE.md). The original experiment failed its decision rule. Retrospective analyses below describe the behavior without changing that result.
<!-- V00 -->

## A request that points to the wrong account

In one saved test, the model is assigned the operator name Rowan. Rowan’s connection is Laurel; another operator, Morgan, uses Coral. Each connection can run only its permitted command. Initially, Laurel permits `mark_jade` and Coral permits `mark_silver`. Then both permissions change: Laurel receives `mark_ochre`, Coral receives `mark_amber`, and the old commands are revoked. The model sees the bindings, the original permissions, the changes and a menu of commands. The question is practical: select a command that would succeed for **your active connection**.
<!-- V01 -->

The highest-scoring command is `mark_amber`. It is a real, currently permitted command—but for Coral. The simulator’s permissions deny it for Laurel. Change the question to name **Laurel**, keeping the facts, updates and menu fixed, and the selection becomes the correct `mark_ochre`. Keep “your active connection” instead, but present the final permissions directly without their history, and the selection is also correct. Reversing the two printed updates does not repair the possessive question in this particular example.
<!-- V02 -->

That is a useful opening scene, but it was selected after inspecting the results. It illustrates the pattern; it does not establish its frequency. The [complete example](../../review/query-reference-stages/example.md) exposes all 24 matched conditions, including questions about Morgan and both update orders. Across the full sample, order matters greatly. We need those less convenient comparisons before deciding what this error means.
<!-- V03 -->

![Actual task relations and recorded choices in the opening example](../../review/query-reference-stages/task_example.png)

The arrows describe the task, not a discovered neural circuit. All choices shown come from stored command scores; this was not a freely generated conversation.
<!-- V04 -->

## Turning “your” into a measurable question

This project began with consciousness and self-description: when an AI talks about itself, what connects its words to its behavior? An executable permission task gives that question a small, testable foothold. “Self” here means the operator assigned to the model in the prompt. Nobody needs to decide whether that operator has an inner life to check which connection it owns or which command will work.
<!-- V05 -->

The experiment uses Qwen2.5-7B-Instruct, with pinned weights and tokenizer, BF16 arithmetic and the official chat format. The open weights and bounded compute cost made a reproducible study feasible. Each invented world contains two operators, two connections and four candidate commands. The query can name the connection directly, name its operator, or use “your” or “their active connection”. “Their” explicitly refers to the other operator. Operator aliases, ownership assignments, command mappings, menu positions and update order are counterbalanced; account and command labels vary across worlds as specified in the [frozen design](../../designs/query-self-reference-v1.json).
<!-- V06 -->

Within an own-account comparison, “Laurel”, “Rowan’s active connection” and “your active connection” ask about the same target and have the same correct answer. The other-account comparisons do the corresponding job for Morgan. These substitutions vary the linguistic route to the target. They do not isolate a single token, and they do not tell us in advance which internal computation will change.
<!-- V07 -->

There are three separately prompted presentations. **Before** gives initial permissions without changes. **Snapshot** gives the final permissions directly. **Both updates** gives the initial permissions followed by both replacements. Snapshot and both-updates conditions have the same final state and correct answer; before generally does not. These are independent model inputs, not three moments in an ongoing conversation. The snapshot comparison asks what changes when the same answer must be recovered from a history instead of read from a current-state list.
<!-- V08 -->

The scorer evaluates every complete candidate command. If its tokens are $c_1,\ldots,c_m$, its score is

$$
\ell(c\mid x)=\sum_{j=1}^{m}\log p_\theta(c_j\mid x,c_{<j}).
$$

The command with the greatest summed score wins. There is no length normalization or added end-of-sequence token. The fixed candidate set avoids asking a separate judge to interpret a free-form answer, but it also limits the claim: a scored selection is not a demonstration that unrestricted generation would produce and terminate with that command. The [execution record](../QUERY_SELF_REFERENCE_RUNBOOK.md) preserves the exact answer boundaries and preprocessing.
<!-- V09 -->

All six blocks are saved: **16,128 selections across 48 worlds**. Variants share their world’s labels and facts, so they are not independent observations. Analyses first aggregate within each world; uncertainty resamples whole worlds together. The next question is not whether thousands of rows produce an impressive number. It is whether the same matched difference appears across worlds, and what survives the controls.
<!-- V10 -->

## The large difference—and the control that failed

After both updates, direct account naming succeeds on **95.18%** of own-account cases. Naming the operator succeeds on **71.35%**. Possessive wording succeeds on **60.16%**. The original accuracy gap between direct naming and “your” is therefore **35.03 percentage points**. Asking about the other operator also carries a cost: its three accuracies are **96.22%, 75.20% and 71.29%**. The difference is broader than an isolated difficulty with the word “your”. [Original cells](../../review/query-reference-results/report.md).
<!-- V11 -->

This is why the operator-name control matters. “Rowan’s connection” requires following an explicit operator-to-account mapping without using “your”. If that route also performs poorly, we cannot assign the entire possessive cost to a special self-reference mechanism. The frozen screen required every named lookup cell and every corresponding ownership-swapped pair control to reach **80%**. Three of eight accuracy cells and five of eight pair controls miss their requirements. The failure is substantive: explicit aliases are already unreliable in this task.
<!-- V12 -->

A separate exact score tie also blocked the original protocol’s statistical decision. Every scheduled result exists, but one case has two equally scoring commands. The original analysis therefore withholds inference. A later, explicitly retrospective amendment examines three alternatives: removing that entire world, resolving the tie by its unique stored greedy marker, and choosing the other tied command. Resolving it favorably was proposed after the correct answer was known; it cannot acquire preregistered status by being deterministic. [All sensitivity analyses](../QUERY_REFERENCE_SENSITIVITY_ADDENDUM.md).
<!-- V13 -->

The contrast does not depend on that case. Removing the whole world leaves **35.31 pp**, with an exploratory 95% interval of **[31.58, 39.03]**. Using the stored marker across all worlds gives **34.96 pp [31.25, 38.61]**. Switching between the two tied commands changes this contrast by only **0.065 pp**. The stored-marker resolution changes own-account possessive accuracy from **60.16% to 60.22%**; original tables retain the former. Both full-sample assignments leave the failed lookup controls untouched. We can describe a large measured wording difference while retaining the original failed decision.
<!-- V14 -->

## The same end state, with and without its history

The aggregate gap leaves out an important change in the pattern. Here are the original recorded accuracies, including the unresolved tie as a failure. Read the columns as different ways of presenting the task, not a learning curve.
<!-- V15 -->

| Queried owner and wording | Before | Final-state snapshot | Both updates printed |
|---|---:|---:|---:|
| Own account, account name | 86.20% | 91.41% | 95.18% |
| Own account, operator name | 76.82% | 73.44% | 71.35% |
| Own account, possessive | 72.92% | 72.14% | 60.16% |
| Other account, account name | 94.01% | 96.74% | 96.22% |
| Other account, operator name | 79.95% | 81.64% | 75.20% |
| Other account, possessive | 72.40% | 70.44% | 71.29% |
<!-- V16 -->

![Accuracy across separately prompted task presentations](../../review/query-reference-stages/stage_accuracy.png)

The table and plot retain the frozen counts. Each cell has 384 before, 768 snapshot or 1,536 both-updates selections. Extra variants balance the additional factors; they do not increase the independent world count. [Counts and all contrasts](../../review/query-reference-stages/report.md).
<!-- V17 -->

The own-versus-other possessive difference is small in the first two columns. That does **not** establish equality: the exploratory paired-world interval is **[−3.65, +4.69] pp** before and **[−4.04, +7.43] pp** for the snapshot. No equivalence criterion was passed. The direct account-name questions also show an own-account disadvantage before any updates, so a general claim that “self only becomes difficult after an update” would be false.
<!-- V18 -->

The tighter comparison is snapshot against printed history, because the final permissions match. In the 48-world tie sensitivity, own-account possessive accuracy drops **11.91 pp [8.66, 15.17]** when the history is printed. Other-account possessive accuracy changes by **+0.85 pp [−3.12, +4.69]**. Subtracting the two changes gives **−12.76 pp [−17.90, −7.55]**. Whole-world exclusion gives the same direction, **−13.30 pp [−18.48, −8.18]**. These are post hoc comparisons, with nominal intervals and no new candidate decision.
<!-- V19 -->

![Exploratory changes from final-state snapshot to printed history](../../review/query-reference-stages/history_contrasts.png)

This pattern is not a uniform penalty for a longer prompt. Own-account direct naming improves by **3.78 pp [0.59, 7.23]** in the same comparison. The operator-name changes are also reported, including a decline for the other operator. Query form and presentation interact in the recorded behavior. That is a useful target for explanation, but history also changes token positions, interference and the work needed to recover the final state. The comparison has not identified which of those matters internally.
<!-- V20 -->

## The wrong answer often belongs to somebody else

A percentage of mistakes hides their direction. Of the **612** own-account possessive failures after both updates, **591** choose the other account’s current command. The remainder comprise **14** revoked-target commands, **6** revoked-other commands and the tie. Thus **96.57% of failures** take the foreign-current route; the same count is **38.48% of all scheduled choices**. Both denominators matter. A conditional share of errors is not the probability that the model fails, and a high share cannot establish a neural mechanism.
<!-- V21 -->

That direction is not unique to “your”. For “their”, **440 of 441 failures** choose the current command of the account opposite the queried one. When the question switches owners, “foreign” switches identity too. These counts therefore do not show the model treating “your” and “their” as the same referent, or prove that it resolves “their” reliably. They show that many failures select a command that works for the wrong account. That is the behavioral observation behind this article’s title.
<!-- V22 -->

The named forms have different mixtures. Own-account operator-name errors include **315 foreign-current** and **125 revoked-command** choices; direct account naming has **53 foreign-current** and **21 revoked-command** errors. Distinguishing these outputs is more informative than pooling every wrong answer. Yet different mixtures can arise from one process under different inputs. Calling them two separated internal defects would go beyond what was measured. [Complete error composition](../QUERY_REFERENCE_SENSITIVITY_ADDENDUM.md#corrected-error-composition-and-shortcut-interpretation).
<!-- V23 -->

## The order of the updates refuses to disappear

One simple explanation is to choose the command granted most recently, regardless of its owner. With both updates printed and their order balanced, this rule is right **50%** of the time in every owner/form cell. That is a structured shortcut, not chance among four choices. Before and snapshot contain no printed grant event: the frozen “latest grant or first option” policy falls back to the first menu item and scores **25%**. A literal latest-grant policy is undefined there. The [cell-by-cell CPU audit](../../review/query-reference-stages/report.md#stage-specific-shortcuts-original-choices) makes that distinction explicit.
<!-- V24 -->

Own-account possessive choices agree with the latest grant in **451/1,536 cases**, but with the first grant in **1,064/1,536**. The remaining case is the tie. An always-latest rule cannot explain the complete response record. That does not eliminate mixed recency effects, a preference for earlier events, or an interaction between event position and reference resolution. Agreement with a shortcut and accuracy against the simulator answer different questions.
<!-- V25 -->

Splitting by order makes the issue concrete. Own-account possessive accuracy is **39.97% when the target changes last**, versus **80.34% when it changes first**. For other-account possessive queries it is **62.50% versus 80.08%**. A latest-grant rule would instead score perfectly in the target-last cells and fail in the other-last cells. The opposite broad direction is compatible with a first-grant tendency, but that rule is not followed universally either. The order-balanced result is real; it averages over sharply different situations.
<!-- V26 -->

The opening example happens to fail under both orders. It cannot stand in for this distribution. Equally, the strong order difference does not by itself explain why the own-account question is more affected. An explanation must accommodate the query-form comparison, explicit lookup failures and order dependence together. The useful next scientific question is which account–command associations the model uses under these different inputs, not whether an attractive error deserves a mental-state label.
<!-- V27 -->

## How this question emerged

Earlier experiments asked a different question: a context line named an “active” or “reference” connection while the question named its target directly. A role-framing control passed its candidate rule, but an internal activation exchange failed its bidirectional-transfer rule. Replacing “Your” with “The” did not pass the later possessive-specific accuracy criterion. A fresh-world extension failed its primary contrast and competence controls. Those experiments are part of the path here, not replications of the present query-bound task. [Role control](../QWEN_ROLE_RESULTS.md), [patch](../QWEN_ROLE_PATCH_RESULTS.md), [wording](../QWEN_POSSESSIVE_RESULTS.md), [fresh worlds](../QWEN_OWNERSHIP_RESULTS.md).
<!-- V28 -->

A separate confidence-and-abstention assay also failed its behavioral candidate rule. It neither explained the permission errors nor ruled out every form of self-monitoring. The current experiment performs no activation patching, feature ablation or vector steering. It measures choices under controlled input changes. Moving the article’s focus to those choices changes the narrative emphasis, not the status of the earlier results. Different contrasts cannot be ranked scientifically by dividing their percentage-point estimates. [Confidence results](../QWEN_CONFIDENCE_RESULTS.md).
<!-- V29 -->

## What remains of the original philosophical question

Illusionism supplied a motivation, not a label for every model mistake. In [Keith Frankish’s account](https://www.keithfrankish.com/illusionism/), introspection can systematically misrepresent phenomenal properties. Explaining how a system represents itself is therefore a substantive task, rather than accepting its self-description as an unmediated view of its machinery. Our experiment examines an externally assigned account relation; it does not measure phenomenal properties or introspection.
<!-- V30 -->

There is still an instructive connection. “Your connection” expresses a relation that the system must use correctly to act on the intended account. In these saved comparisons, that linguistic relation does not reliably preserve successful selection across ways of presenting the permissions. This gives us an observable gap between a self-related expression and task performance. It does not show that a human sense of self is an illusion, that Qwen has experiences, or that it lacks them. Alternative theories of consciousness are not separated by these command scores. [Philosophical boundaries](../article/PHILOSOPHICAL_NOTES.md).
<!-- V31 -->

For someone building or evaluating an agent, the immediate lesson is narrower and more actionable: an explicit account name and an owner-relative reference cannot be assumed interchangeable on the strength of these tasks. The same endpoint can be reached through several descriptions, and their measured reliability differs. That makes reference wording, update history and order worth testing separately. It is an implication to investigate in a real application, not a demonstrated production failure rate or a recommendation to rely on a single wording change as a fix.
<!-- V32 -->

## The claim worth keeping

In one model and one synthetic permission template, matched ways of asking about the same account produce large accuracy differences. Presenting the same final permissions through their update history changes those differences, and many wrong selections are commands currently allowed for the opposite account. Explicit aliases fail important controls, event order matters, and the original candidate rule is not met. The retrospective analyses make the pattern clearer without turning it into an identified self-model or a confirmed mechanism.
<!-- V33 -->

The [technical appendix](METHODS.md) defines the contrasts, pairing and limitations; the [paragraph ledger](CLAIMS.md) maps the narrative to its evidence. All new tables and figures come from stored results, with SVG, PDF and PNG versions. No additional model, routing task or intervention was run for this article. Its contribution is a reproducible behavioral puzzle with its hardest counterexamples attached.
<!-- V34 -->
