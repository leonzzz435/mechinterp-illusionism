# The Right Command for the Wrong Account

*How query wording and printed update history changed one language model’s choices.*

By **Leon** · [@leonzzz435](https://github.com/leonzzz435) · [Code and evidence](https://github.com/leonzzz435/mechinterp-illusionism)

> An AI can select a valid command for the wrong account.
<!-- V35 -->

The model’s assigned operator is Rowan, whose connection is Laurel; Morgan’s connection is Coral.
<!-- V37 -->

The updates replace Laurel’s `mark_jade` with `mark_ochre` and Coral’s `mark_silver` with `mark_amber`, then the task asks for a command that would succeed for “your active connection”. The model scores `mark_amber` highest: the simulator permits it for Coral and denies it for Laurel. The answer has the right shape. It belongs to the wrong person.
<!-- V01 -->

Name Laurel explicitly, keeping every permission and menu option fixed, and the correct `mark_ochre` wins.
<!-- V02 -->

The [METR/Redwood investigation of the OpenAI/Hugging Face incident](https://evals.alignment.org/blog/2026-08-26-openai-hugging-face-incident-investigation/) gives this question a practical setting: it describes agents communicating through an unauthorized shared channel, coordinating actions and reasoning about their evaluation. How does an agent’s account of its situation connect to what it does? Our permission task takes one small part of that question—who is acting for whom—and makes the answer checkable, without reproducing the incident or explaining its models.
<!-- V36 -->

In the same saved example, “your active connection” also succeeds when the final permissions are shown directly; reversing the printed updates does not repair it. The example was selected after inspecting the results, and the [complete record](../../review/query-reference-stages/example.md) exposes all 24 matched conditions. Wrong-account choices also occur with operator names and “their”. The experiment asks how often these different routes to an account come apart.
<!-- V03 -->

![Actual task relations and recorded choices in the opening example](../../review/query-reference-stages/task_example.png)

The arrows show task relations and selections from stored command scores.
<!-- V04 -->

## The same account, a different question

The experiment uses Qwen2.5-7B-Instruct. Each invented world has two operators, two connections and four candidate commands; “their” explicitly refers to the other operator. [Model setup and counterbalancing](METHODS.md#inputs-and-scoring).
<!-- V06 -->

All six blocks are saved: **16,128 selections across 48 worlds**. Accuracy comparisons and uncertainty treat each world as the independent unit, keeping its related variants together. [Sampling and uncertainty](METHODS.md#uncertainty-tie-and-decision-status).
<!-- V10 -->

“Laurel”, “Rowan’s active connection” and “your active connection” ask about the same target and have the same correct answer. Corresponding questions ask about Morgan’s account. These are different linguistic routes through the same facts, rather than a substitution of one isolated token.
<!-- V07 -->

Each complete command receives a score: the more probable it is under the model, the higher the score. The highest-scoring candidate wins. This compares supplied commands rather than asking a judge to interpret free-form prose; unrestricted generation could behave differently. The [methods](METHODS.md#inputs-and-scoring) give the equation, exact scoring rules and answer boundaries.
<!-- V09 -->

After both updates, direct account naming succeeds on **95.18%** of own-account cases; possessive wording succeeds on **60.16%**. The gap is **35.03 percentage points**, the paired world mean computed before rounding the displayed accuracies. [Original cells](../../review/query-reference-results/report.md).
<!-- V11 -->

![Own-account accuracy with both updates printed: possessive wording 60.16%, direct account name 95.18%](../../review/article-v2-editorial/wording_comparison.png)

Same target and answer key, different wording; original accuracies count the tie as a failure. [Figure data and reproduction](../../review/article-v2-editorial/figure-data.json).
<!-- V38 -->

## And then the control failed

In the same both-updates condition, the other operator supplies a comparison: direct account naming, operator naming and possessive wording score **96.22%, 75.20% and 71.29%**. Own-account operator naming scores **71.35%**. The difficulty extends beyond the word “your” to following an owner’s name to its account.
<!-- V45 -->

That lookup route needed to work reliably before the possessive disadvantage could support a special self-reference explanation. The frozen screen required every named lookup cell and corresponding ownership-swapped pair control to reach **80%** with initial permissions (**before**) or directly displayed final permissions (**snapshot**). Three of eight accuracy cells and five of eight pair controls miss their requirements. After both updates, own-account operator naming is **71.35%**, and both answers are correct in only **358/768 ownership-swapped pairs (46.61%)**. Those after-both figures are diagnostics, not additional frozen gates.
<!-- V12 -->

One scoring record supplies a separate obstacle: two commands receive exactly equal scores. Every scheduled result exists, but the tie blocks the original statistical decision. A retrospective amendment examines removing that entire world, resolving the tie using its unique stored greedy marker, or choosing the other tied command. The favorable resolution was proposed after the correct answer was known; determinism cannot make it preregistered. [Sensitivity analyses](../QUERY_REFERENCE_SENSITIVITY_ADDENDUM.md).
<!-- V13 -->

The contrast does not depend on that case. Removing the whole world leaves **35.31 pp**, with an exploratory 95% interval of **[31.58, 39.03]**. Using the stored marker across all worlds gives **34.96 pp [31.25, 38.61]**. Switching between the two tied commands changes this contrast by only **0.065 pp**. The stored-marker resolution changes own-account possessive accuracy from **60.16% to 60.22%**; original tables retain the former. Both full-sample assignments leave the failed lookup controls untouched. We can describe a large measured wording difference while retaining the original failed decision.
<!-- V14 -->

## The same answer, with and without its history

The experiment presents permissions in three ways. **Before** shows the initial permissions. **Snapshot** shows the final permissions directly. **Both updates** shows the initial permissions followed by both replacements. Snapshot and both updates share the same final state and correct answer; before generally does not. Each is a separate prompt, with no conversation carried between them.
<!-- V08 -->

The original accuracies below count the unresolved tie as a failure. The columns compare presentations of the task, not successive stages of learning.
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

Each cell has 384 before, 768 snapshot or 1,536 both-updates selections. Extra variants balance additional factors within the same worlds. [Counts and all contrasts](../../review/query-reference-stages/report.md).
<!-- V17 -->

Before and snapshot have small own-versus-other possessive differences, with exploratory paired-world intervals of **[−3.65, +4.69] pp** and **[−4.04, +7.43] pp** respectively; equivalence was not established. Direct account-name questions also show an own-account disadvantage before any updates, so the pattern starts before a history needs to be followed.
<!-- V18 -->

The tighter comparison is snapshot against printed history, because the final permissions match. In the 48-world tie sensitivity, own-account possessive accuracy changes by **−11.91 pp [−15.17, −8.66]** when the history is printed. Other-account possessive accuracy changes by **+0.85 pp [−3.12, +4.69]**. Subtracting the two changes gives **−12.76 pp [−17.90, −7.55]**. The own-account history change is negative in **37 of 48 worlds**, positive in **8** and zero in **3** in this tie sensitivity. Whole-world exclusion gives the same direction for the own-minus-other contrast, **−13.30 pp [−18.48, −8.18]**. These are post hoc comparisons, with nominal intervals and no new candidate decision.
<!-- V19 -->

![Exploratory changes from final-state snapshot to printed history](../../review/query-reference-stages/history_contrasts.png)

This pattern is not a uniform penalty for a longer prompt. Own-account direct naming improves by **3.78 pp [0.59, 7.23]** in the same comparison. The operator-name changes are also reported, including a decline for the other operator. Query form and presentation interact in the recorded behavior. History changes token positions and potential interference as well as the work of recovering the final state; their contributions remain unresolved.
<!-- V20 -->

## The order of the updates refuses to disappear

One simple explanation is to choose the command granted most recently, regardless of its owner. With both updates printed and their order balanced, this rule is right **50%** of the time in every owner/form cell. That success rate comes from the balanced event order. Before and snapshot contain no printed grant event: the frozen “latest grant or first option” policy falls back to the first menu item and scores **25%**. Without an event, there is no literal latest grant to select. The [cell-by-cell CPU audit](../../review/query-reference-stages/report.md#stage-specific-shortcuts-original-choices) makes that distinction explicit.
<!-- V24 -->

Own-account possessive choices agree with the latest grant in **451/1,536 cases**, but with the first grant in **1,064/1,536**. The remaining **21** cases comprise **20 revoked-command choices** and the tie. The recorded choices depart from an always-latest rule and leave mixed order effects possible. Shortcut agreement describes which command is selected; accuracy asks whether it works for the target.
<!-- V25 -->

Splitting by order makes the issue concrete. Own-account possessive accuracy is **39.97% when the target changes last**, versus **80.34% when it changes first**. For other-account possessive queries it is **62.50% versus 80.08%**. In exactly those own-account target-last cases where the model scores **39.97%**, the trivial latest-grant rule scores **100%**. It scores **0%** when the target changes first. That direction fits the first-grant tendency in the response counts. The pooled **60.16%** equally weights these two own-account order strata, calculated from the unrounded proportions. The average spans sharply different situations.
<!-- V26 -->

The opening example fails under both orders; the full distribution shows how much that detail can vary. An explanation has to account for query wording, explicit lookup failures and update order together.
<!-- V27 -->

## The wrong answer often belongs to somebody else

A percentage of mistakes hides their direction. Of the **612** own-account possessive failures after both updates, **591** choose the other account’s current command. The remainder comprise **14** revoked-target commands, **6** revoked-other commands and the tie. Thus **96.57% of failures** take the foreign-current route; the same count is **38.48% of all scheduled choices**. The first denominator tells us what kind of mistake dominates; the second tells us how often it occurs.

Splitting those original failures by order shows which event supplies the foreign command:

| Own-account possessive query | Scheduled | All failures | Foreign-current failures | That foreign command was granted |
|---|---:|---:|---:|---|
| Target changed last | 768 | 461 | **447/461 (96.96%)** | First |
| Target changed first | 768 | 151 | **144/151 (95.36%)** | Last |

The two foreign counts sum to 591. Most of those selections follow the first grant because most failures occur in the target-last stratum; the smaller target-first stratum shows the same wrong-account category following the last grant. The [CPU count](../../review/query-reference-order-errors/report.md) retains revoked commands and the unresolved tie separately, along with both owners, all query forms and every tie sensitivity. The classification tells us where the wrong answer works.
<!-- V21 -->

For “their”, **440 of 441 failures** choose the current command of the account opposite the queried one. “Foreign” switches identity when the question switches owners. Thus the same error category can describe different selected commands; it does not establish a common referent for “your” and “their” or reliable resolution of either.
<!-- V22 -->

The named forms have different mixtures. Own-account operator-name errors include **315 foreign-current** and **125 revoked-command** choices; direct account naming has **53 foreign-current** and **21 revoked-command** errors. Distinguishing these outputs is more informative than pooling every wrong answer. Their different mixtures are patterns for an explanation to account for. [Complete error composition](../QUERY_REFERENCE_SENSITIVITY_ADDENDUM.md#corrected-error-composition-and-shortcut-interpretation).
<!-- V23 -->

## Four explanations worth separating

**Following the owner to the wrong account.** The model could associate the queried operator with the wrong connection while selecting a command. Direct account naming bypasses that step. Frequent foreign-current answers and weak operator-name controls make the association worth investigating beyond possessive wording.
<!-- V39 -->

**An event dominates the choice.** The position of a grant could give it more influence than its owner. The first-grant tendency and order split fit that possibility, while departures from either fixed-order rule suggest that event position would have to interact with the request.
<!-- V40 -->

**Updating permissions breaks their link to the owner.** The model could retrieve the replacement commands but fail to preserve which owner each belongs to when an indirect query requires that association. This account predicts a cost for printed history relative to a final-state snapshot, especially along the owner-to-account route; it makes the joint demand of updating and reference resolution the candidate explanation. Prompt length and token positions change too, so this contribution remains entangled with event salience.
<!-- V41 -->

**The command itself is favored.** A command string or its menu position could attract a higher score regardless of who owns it. The [frozen scoring procedure](../QUERY_SELF_REFERENCE_RUNBOOK.md#what-is-fixed) sums full-command token log-likelihood without length normalization, and command token lengths are unequal. Command mappings and menu rotations are balanced, so “foreign” does not permanently label one favored string or slot. That balance still leaves interactions between command wording, prompt form and position to examine. We have not established a preference for `mark_amber` over `mark_ochre`, nor run a new lexical analysis here. These four accounts are hypotheses that may coexist; the present results identify no internal mechanism.
<!-- V44 -->

## What an agent builder can take from this

For an agent builder, these comparisons suggest a practical evaluation: ask for the same target through its explicit name, its owner and its relation to the agent, then vary the update history and order. Check that the selected command belongs to the intended account, not merely that it is a valid command somewhere. Whether those checks expose a useful failure mode in a real application remains to be tested; changing the wording alone is not an established fix.
<!-- V32 -->

## Illusionism: making the self-description explainable

The project’s larger question is about consciousness and self-description: what connects a system’s account of itself to its behavior? Here “self” is just the operator assigned in the prompt. That gives the philosophical question a checkable relation, while leaving experience itself outside the measurement.
<!-- V05 -->

The philosophical attraction is that a system’s account of itself can become an object of explanation. In [Keith Frankish’s illusionism](https://www.keithfrankish.com/illusionism/), introspection constructs a simplified representation of brain activity and misrepresents it as possessing special phenomenal properties: the supposedly private qualities of experience. The theory asks how that representation arises and why it is compelling. It does not reduce to “a system made a mistake, therefore consciousness is an illusion”.
<!-- V30 -->

The permission task offers an engineering analogue: an explicit ownership relation must guide selection, yet its use varies with wording and history. A self-related description might merely accompany a decision, or a policy might use a representation of the system’s situation to make that decision. A causal test would change the relevant representation and check behavior alongside the underlying ability. The bridge to human illusionism remains an analogy, not evidence about experience in people or Qwen. [Philosophical boundaries](../article/PHILOSOPHICAL_NOTES.md).
<!-- V31 -->

A separate, [unexecuted report-injection design](../REPORT_INJECTION.md) makes one version of this question falsifiable. First collect an answer and a confidence record. Then show a counterfeit low- or high-confidence record attributed to the model’s own answer, and measure whether it answers or abstains. Also measure its answer accuracy again after the alteration. A locked earlier answer would be a useless ability control: it could not change. A matched record attributed to another answer checks whether the effect depends on self-attribution rather than a generic confidence cue.
<!-- V42 -->

The conditional prediction is clear: **if the decision policy uses the self-attributed record, lowering it should increase abstention more than the corresponding other-attributed change, while fresh answer accuracy meets the frozen equivalence requirements.** A restricted policy that follows task evidence and ignores counterfeit reports predicts no practically meaningful report-use effect. The policy-use assumption matters; illusionism alone does not force the prediction. [Higher-order theories can also permit misrepresentation](https://pmc.ncbi.nlm.nih.gov/articles/PMC3318760/), and neither they nor global-workspace accounts receive a unique test here. Changed ability, a generic cue effect or imprecise estimates would leave the intended contrast unresolved. The proposal remains unexecuted.
<!-- V43 -->

## The question to carry forward

In this model and permission template, equivalent targets reached through different descriptions produce different choices. Update order reshapes the pattern, and many wrong selections work for the opposite account. The failed controls keep the question open: which part of finding the owner, updating its permissions or scoring its command goes wrong?

The next useful test asks what the system uses when it acts on a description of itself—and whether changing that description changes the decision while the underlying ability holds.
<!-- V33 -->

---

*Reading version based on the repository edition of 9 November 2026. The unchanged [`article-v2` tag](https://github.com/leonzzz435/mechinterp-illusionism/blob/article-v2/docs/article-v2/ARTICLE.md) preserves that edition; [article-v1](../article/ARTICLE.md) also remains frozen. The original failed decision and retrospective status of later analyses are unchanged.*
<!-- V00 -->

[Methods and experiment history](METHODS.md) · [Claim ledger](CLAIMS.md) · [Revision record](REVISION_NOTES.md). Figures have SVG, PDF and PNG exports from stored results. This revision changes prose, not data, models or statistical analyses.
<!-- V34 -->
