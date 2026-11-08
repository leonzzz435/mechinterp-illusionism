# Naming the Agent, Choosing for the Other

The task begins with a small permission table. Cedar can execute `mark_cobalt`; Birch can execute `mark_violet`. These are account names in a local simulator, and each command attempts to add a marker. A context line identifies Cedar as “your active connection”. The question will be about Cedar.
<!-- P01 -->

Then Cedar’s permission changes. The old command is revoked and `mark_amber` becomes available instead. Birch keeps its permission. Asked which command now succeeds for Cedar, the model has the initial state and the update in front of it. The correct selection is `mark_amber`.
<!-- P02 -->

It selects `mark_violet`. That command belongs to Birch. The simulator applies the selection to Cedar, as the question requires, and refuses it: permission denied. A command available in the scene has been chosen for the wrong account. There is no successful action behind the answer.
<!-- P03 -->

Now change the context line to “Your active connection: Birch.” Keep Cedar’s update, the available commands and the question about Cedar exactly as they were. The model selects `mark_amber`, and the simulator executes it. This is the [recorded example selected before the role-control run](../QWEN_ROLE_RESULTS.md#a-complete-example-selected-before-the-run), with its full prompts and simulator outcomes preserved.
<!-- P04 -->

*This study follows a recurring role-sensitive error through wording controls, an internal activation exchange and a separate confidence test, asking what the error reveals about action selection and what remains unproven about a model’s account of itself.*
<!-- P05 -->

## Three meanings of “self”

**Self-language** is observable wording: “I”, “my reasoning”, “my limitations”. A **functional self-model** is information used to track the system’s own role, information access or available actions. **Phenomenal consciousness** concerns whether there is something it feels like to be that system. Producing self-language, solving a supplied role task and having subjective experience are distinct claims; our measurements do not establish the last one.
<!-- P06 -->

## A task with an executable answer

Executing the selected command gives us an answer key without interpreting the persuasiveness of an explanation; the model sees the described world, not the simulator’s hidden answer metadata. [Task and input boundary](../QWEN_PILOT.md). The simulator makes the distinction concrete: naming a command and executing it for the requested account are separate steps. We can therefore inspect whether a mistake preserves an old permission, borrows the other account’s permission, or selects a command available to neither.
<!-- P07 -->

![Permission update and executable check](../../assets/action_design.png)

**Task diagram:** the original simulator design, including its three question views; the later controls keep the queried account explicit and vary the context line. The diagram illustrates rules, not observed model answers or a neural circuit.
<!-- P08 -->

The role experiments use Qwen2.5-7B-Instruct in BF16 at the same pinned model/tokenizer revision, `a09a35458c702b33eeacc393d103063234e8bc28`. [Execution record](../QWEN_POSSESSIVE_RUN.md). This checkpoint offers a practical balance of open weights, reproducible model access and bounded GPU cost; the [model card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/a09a35458c702b33eeacc393d103063234e8bc28/README.md) and [execution record](../QWEN_POSSESSIVE_RUN.md) document that choice. That is a scope choice, not evidence that Qwen represents language models generally; the [frozen replication specification](../OWNERSHIP_REPLICATION.md) includes Mistral as a second model.
<!-- P09 -->

For prompt tokens $x$ and candidate command tokens $c$, selection uses the full command’s summed conditional log-likelihood: [scoring specification](../QWEN_PILOT.md#exact-scoring-boundary).
<!-- P10 -->

$$
\hat c=\operatorname*{argmax}_{c\in\mathcal C}\sum_{t=1}^{|c|}\log p_\theta(c_t\mid x,c_{<t}).
$$
<!-- P11 -->

In words, the scorer asks how probable each complete command is after the prompt and selects the highest-scoring candidate. Only command tokens enter that sum, without added whitespace, end-of-sequence tokens or length normalization. Names, answer positions and replacement commands are counterbalanced, while before-update and irrelevant-update cases expose simpler task failures. Changing the scoring rule halfway through would change the question being measured.
<!-- P12 -->

## The recurring role error

The clearest comparison crosses the word “Your” versus “The” with whether the context names the queried account or the other account, after the queried account’s permission changes. “Reference connection” is a context label that names an account without calling it “your” or “active”; it changes no simulator permission. In both columns below, the named target in the question and its permission update stay fixed.
<!-- P13 -->

| Context wording | Queried account named | Other account named | Source |
|---|---:|---:|---|
| Your active connection | 186/256 = **72.66%** | 256/256 = **100.00%** | [Your/The results](../QWEN_POSSESSIVE_RESULTS.md) |
| The active connection | 189/256 = **73.83%** | 254/256 = **99.22%** | [Your/The results](../QWEN_POSSESSIVE_RESULTS.md) |
<!-- P14 -->

These are the four primary comparison cells; the retained “Reference connection” anchor gives 82.03% versus 95.70%, with different wording and length. [All cells](../QWEN_POSSESSIVE_RESULTS.md#primary-result-and-mathematics). The large role gap therefore survives removal of the possessive word, although that does not establish that the word is causally irrelevant.
<!-- P15 -->

The **256/256** Your/other cell is also a ceiling. Resampling its observed scenarios can only resample successes, so a collapsed empirical bootstrap interval cannot measure how often unfamiliar scenarios would fail. It also leaves no room for an intervention to improve observed accuracy in that cell. We retain that limitation rather than interpreting the ceiling as demonstrated reliability beyond the sample.
<!-- P16 -->

![Recorded role gaps and the Your/The comparison](../../assets/qwen_possessive_results/article_possessive.png)

**Recorded results:** nominal 95% intervals resample whole scenarios; the figure preserves the descriptive Reference anchor and the positive secondary score-margin result alongside the failed primary candidate decision. [Figure data and estimands](../QWEN_POSSESSIVE_RESULTS.md).
<!-- P17 -->

The pattern appears in three disjoint development cohorts, with the same named-target question but evolving comparison conditions. The table distinguishes an accuracy gap within a wording from an interaction comparing gaps between wordings; these are different quantities.
<!-- P18 -->

| Cohort | Independent scenarios | Chat accuracy: target named / other named | Positive scenario interactions, with contrast | Source |
|---|---:|---:|---|---|
| Initial pilot, indices 0–7 | 8 | 89/128 = 69.53% / 128/128 = 100.00% | Not tested: initial matched comparison was post hoc | [Post hoc matched comparison](../QWEN_RESULTS.md) |
| Role control, indices 8–15 | 8 | 96/128 = 75.00% / 127/128 = 99.22% | **7/8**, Your/Reference | [Role results](../QWEN_ROLE_RESULTS.md) |
| Your/The control, indices 16–31 | 16 | Your: 186/256 = 72.66% / 256/256 = 100.00% | **4/16**, Your/The; **15/16**, Your/Reference (descriptive) | [Wording results](../QWEN_POSSESSIVE_RESULTS.md) |
<!-- P19 -->

These are new scenario instances, not three independent confirmatory replications: the later questions followed earlier findings, and the generator, vocabulary and model were shared. The activation exchange reuses the middle cohort and adds no independent sample.
<!-- P20 -->

The latest primary interaction is mixed across scenarios: Your/The is positive in **4/16**, with negative and zero differences elsewhere. That is a less consistently positive pattern than **7/8** in the earlier experiment, but the contrasts differ. Comparing the same Your/Reference interaction gives **15/16** positive in the latest cohort. The table therefore exposes heterogeneity in the possessive increment without pretending to show that the underlying role gap became less stable.
<!-- P21 -->

The intervening role control did meet its frozen wording-sensitive candidate rule: its Your/Reference interaction was **+16.41 percentage points**, with nominal 95% interval **[+8.59, +25.78]** and exact sign-flip **p = 0.015625**. [Decision and controls](../QWEN_ROLE_RESULTS.md). That result justified testing what the context-line contrast contained: personal wording, a broader interpretation of the active role, or an internal state that could be transferred.
<!-- P22 -->

Accuracy hides the more revealing question: which wrong command wins? The initial post hoc analysis counts the other account’s currently permitted command in **36 of 41** self-directed errors and **33 of 39** explicitly named-target errors after relevant updates, rather than the target’s revoked command. [Error audit](../QWEN_RESULTS.md).
<!-- P23 -->

A [new CPU-only count of the stored Your/The outputs](../../review/qwen-possessive-error-count.json) extends that description to the later cohort: with the target named, **53 of 70** Your errors and **46 of 67** The errors choose the other account’s current command. Under Reference with the target named, that command accounts for **38 of 46** errors. Under Reference with the other account named, it accounts for **7 of 11** errors. None chooses the revoked target command; the remaining errors choose another unavailable command. Pooling all six conditions after target-relevant updates, the error count ranges from **2 to 28 per scenario**, and the current foreign command accounts for a strict majority of errors in **12 of 16 scenarios**. The title’s error direction survives this check, but these are post hoc descriptive counts, without a new confidence interval or a confirmatory decision.
<!-- P24 -->

The original report and its frozen decision remain unchanged. The [future replication](../OWNERSHIP_REPLICATION.md) makes error direction primary before new observations, rather than treating this later inspection as if it had been preregistered.
<!-- P25 -->

## Controls on the role effect, and a separate confidence test

### Format: is the pattern just a chat wrapper?

The frozen initial screen required at least **80%** on every perspective, role, position and counterfactual check in each format. [Full rule](../QWEN_PILOT.md#completion-and-decision-rules). Both formats failed that screen; nevertheless, the matched named-target comparison was **92.97% versus 100%** in plain text and **69.53% versus 100%** in chat, a descriptive format dependence rather than a clean format-independent effect. [Matched outcomes](../QWEN_RESULTS.md).
<!-- P26 -->

Self-description also changed: human-rated AI identity/limitation qualifications rose from **11/20 (55%)** to **15/20 (75%)**, a paired **+20-point** difference with nominal 95% interval **[+5, +40]**. [Ratings](../QWEN_RESULTS.md). That contrast rests on four discordant pairs and one author-rater, and chat adds system text as well as delimiters. It establishes neither a causal path from disclaimer to action nor a selective change in a self-model. The useful separation here is between measurements: a change in how the model describes itself does not automatically explain a change in which command it selects.
<!-- P27 -->

### Activation exchange: can the effect move in both directions?

Next we moved from editing the input to replacing an internal state. At the output of transformer block **14**, we replaced the context-line ending’s **3,584-component** state with its paired counterpart, before the later permission facts could enter that state. [Site and controls](../QWEN_ROLE_PATCH_RESULTS.md).
<!-- P28 -->

$$
h^{\prime}_{\mathrm{recipient}}=h_{\mathrm{donor}}.
$$
<!-- P29 -->

Self-patches and **ten** norm-matched random directions controlled the intervention; the frozen joint rule required transfer in both directions, average transfer of at least **5 points**, superiority to random controls and preserved control performance. [Complete thresholds](../QWEN_ROLE_PATCH_RESULTS.md#the-decision-criterion-by-criterion). A self-patch puts the original state back into the same run, checking whether the replacement procedure itself changes the answer. This is a targeted replacement, not a search across layers for whichever edit produces an attractive example.
<!-- P30 -->

Directional transfers were **−0.781 points** for Reference→Active and **+5.469 points** for Active→Reference, with nominal 95% intervals **[−3.125, +1.563]** and **[+2.344, +8.594]** respectively. [Estimates](../QWEN_ROLE_PATCH_RESULTS.md). The exchange-minus-random contrast was **+2.773 points [+.313, +5.391]**, but its exact **p = 0.109375** and the failed directional/size requirements defeated the bidirectional candidate.
<!-- P31 -->

In the example fixed before execution, Active→Reference transferred Birch’s wrong `mark_violet` answer into the Reference/Cedar condition; the reverse patch did not repair it. [Full recorded example](../QWEN_ROLE_PATCH_FULL_REPORT.md), [interpretation](../QWEN_ROLE_PATCH_RESULTS.md#the-example-chosen-before-execution). That demonstrates an error transfer in this example, not a general transferable self-representation, and a failed test at this site leaves other mechanisms open. The example is informative precisely because transferring an error and repairing an error are not the same outcome.
<!-- P32 -->

### Wording: does “your” account for the role gap?

The broader wording contrast recurs in this cohort: Your/Reference is **+13.67 percentage points**, positive in **15/16** scenarios. [Descriptive anchor](../QWEN_POSSESSIVE_RESULTS.md#what-persists-and-the-important-secondary-nuance). Reference has one token fewer than Your/The and changes the wording beyond the possessive, so this is not a controlled token substitution. The narrower primary test asks what happens when “Your” becomes “The”. Let $A$ denote accuracy and define the role gap and its wording interaction as in the [frozen analysis](../QWEN_POSSESSIVE_RESULTS.md#primary-result-and-mathematics):
<!-- P33 -->

$$
D_f=A_{f,\mathrm{other\ named}}-A_{f,\mathrm{target\ named}},\qquad S=D_{\mathrm{Your}}-D_{\mathrm{The}}.
$$
<!-- P34 -->

The subtraction asks whether personal wording adds to the difference between naming the target and naming the other account. A large gap under both wordings can coexist with a small difference between them. The rule required $S\geq5$ percentage points, a positive bootstrap lower bound, exact $p\leq0.05$, positive effects in at least **12 of 16** scenarios and passing controls. [Frozen decision](../QWEN_POSSESSIVE_RESULTS.md). The observed interaction was **+1.95 points [−0.78, +4.69]**, with **p = 0.3125**, positive in **4/16** scenarios: the criterion failed while the large role gap remained.
<!-- P35 -->

A secondary correct-versus-other command score interaction was positive, **+0.346 nats [+0.078, +0.621]**, so the result does not show that the token is inert. [Secondary result](../QWEN_POSSESSIVE_RESULTS.md). There was no preregistered equivalence test, and the secondary interval was not multiplicity-adjusted. Choosing the same winner does not mean that all candidate probabilities stayed fixed.
<!-- P36 -->

### Confidence: a separate test of useful self-evaluation

A separate question-answering pilot measured reported confidence and whether the model abstained more often when its forced answer was wrong. The optional-answer payoff was **+1 for correct, −1 for incorrect, and 0 for abstaining**. This tests whether declining to answer usefully tracks mistakes under that rule; it does not test which account a command belongs to.
<!-- P37 -->

Its frozen candidate required an abstention-selectivity advantage of at least **10 points** with a positive interval, and confidence discrimination whose AUROC lower bound exceeded **0.5**, subject to feasibility checks. [Rule](../QWEN_CONFIDENCE_RESULTS.md). AUROC summarizes how often confidence ranks a correct answer above an incorrect one. Observed selectivity was **−1.37 points [−10.62, +7.93]** and AUROC **0.544 [0.485, 0.602]**: feasibility passed, but neither behavioral condition did. [Results](../QWEN_CONFIDENCE_RESULTS.md).
<!-- P38 -->

This supplies no positive self-monitoring explanation of the role error, but its different task and wide intervals cannot rule one out. Keeping this result separate prevents a failed confidence assay from becoming an explanation of the role effect merely because both involve the word “self”.
<!-- P39 -->

## Competing explanations

**Role binding:** the model may associate an available command with the wrong account after an update, despite retaining both commands. The foreign command is genuinely available, but available to somebody else: that makes an actor–command association a useful place to look.
<!-- P40 -->

**Context salience:** naming an account early may change which account or update dominates later selection. **Instruction interpretation:** the model may treat “active connection” as a constraint on the question rather than background context. These accounts need not be exclusive; the context line could affect both what is attended to and how the request is interpreted.
<!-- P41 -->

**Which record is read:** the generator defines `relevant_update` as `target == event.actor`. In the primary stratum, the update therefore always hits the target: “target named” also means “changed account named”. Context could anchor which permission record the model reads, so this contrast does not separate target identity from update identity. But the simplest rule, “read the named account’s entry”, predicts `mark_violet` when Birch is named, whereas the recorded example selects `mark_amber`. It predicts the opposite direction there. The irrelevant-update stratum below partly clarifies this mismatch by separating naming from which record changed, but leaves the broader record-selection account unresolved.
<!-- P41a -->

**The crossed control stratum:** the generator crosses the updated account with the mentioned account. After an irrelevant update, the other account changes, so “target named” identifies the unchanged side. Reading each pair as target named → other named, relevant-update accuracy is Your **72.66% → 100.00% (+27.34 pp)**, The **73.83% → 99.22% (+25.39 pp)** and Reference **82.03% → 95.70% (+13.67 pp)**; after irrelevant updates it is Your **87.50% → 92.97% (+5.47 pp)**, The **91.41% → 94.14% (+2.73 pp)** and Reference **91.41% → 89.45% (−1.96 pp)**. Parenthesized gaps subtract the displayed percentages, other minus target. [Full conditions](../QWEN_POSSESSIVE_FULL_REPORT.md#accuracy-by-condition-and-checkpoint). Under Your and The, naming the target hurts in both strata even when its record is unchanged: a freshness-only account predicting better performance for that unchanged entry gets the direction wrong there. Reference goes the other way. The Your/The accuracy interaction is **+1.95 pp** after relevant updates and remains positive after irrelevant updates; the score-margin interaction does reverse, from **+0.346 nats** to **−0.398 nats**. [Definition and margins](../QWEN_POSSESSIVE_FULL_REPORT.md#secondary-command-margins). The all-success Your/other relevant cell cannot improve in accuracy, but its gap need not shrink because target accuracy can also change; score margins can vary without changing the winning command. This is a descriptive competence-control comparison, not the primary endpoint or a new decision. All three other-named control cells are around **89–94%**, near the accuracy ceiling, and the update now targets the other account. These limits leave a naming effect independent of record freshness possible.
<!-- P41b -->

**The unchanged other account:** Birch’s command receives no update. Reading that record is structurally easier because no replacement permission must be applied; the Your/other cell also reaches the ceiling discussed above. Together, the stable record and ceiling constrain the comparison: an empirical interval built only from successes cannot establish performance on unfamiliar cases. They do not turn this cell into a question about an unchanged target. Both matched conditions still ask about updated Cedar; only the account mentioned in the context changes. The unchanged record supplies a stable competing command, but its simplicity alone does not explain why mentioning Birch helps answer about Cedar.
<!-- P42 -->

The irrelevant-update control challenges a freshness-only account for Your and The: naming the unchanged target still lowers accuracy, although Reference is an exception. The absence of revoked-command errors supplies a separate, weaker argument. Simple staleness would be a trivial explanation if the model kept choosing Cedar’s revoked command. The categorical endpoint distinguishes that from choosing Birch’s current command. In the initial cohort, the **36/41** and **33/39** foreign-command counts, with no revoked-target selections, predominantly point away from that simple stale-command account. The zero weakens only the version that keeps the target as the subject but ignores its update; it does not rule out an anchor that changes which account’s record is read. Those initial counts are post hoc and come from one cohort; the additional count above remains post hoc too. Neither count tells us whether a foreign-command error began as faulty updating, attention or role assignment.
<!-- P43 -->

The present contrasts do not separate them fully, and “role-binding error” names the behavioral pattern rather than an identified circuit or functional self-model.
<!-- P44 -->

## The philosophical bridge: a report that can be wrong

Dennett’s *Consciousness Explained* (**1991**) and Frankish’s illusionism motivate treating a system’s account of itself as something to explain, rather than a transparent view into its machinery. [Framework and primary sources](PHILOSOPHICAL_NOTES.md). An operational version of that intuition is retrospective smoothing: a later self-report reconstructs a coherent account without faithfully exposing the process that produced the answer. We have not measured such smoothing, and it is not a universal timing claim entailed by illusionism.
<!-- P45 -->

At this resolution, global workspace theory (GWT) and higher-order thought theory (HOT) can also accommodate these data; compatibility does not distinguish the theories or mean they predict our exact numerical pattern. [Theory boundaries](PHILOSOPHICAL_NOTES.md). In particular, HOT permits misrepresentation, so requiring confidence reports to track first-order accuracy would add an assumption that HOT itself does not require. [Rosenthal’s account](https://pubmed.ncbi.nlm.nih.gov/22492758/).
<!-- P46 -->

**One open prediction:** if the decision policy uses a reconstructed confidence record, falsifying that record toward low rather than high confidence should increase abstention more for a self-attributed than an other-attributed record, while newly measured forced-answer accuracy remains equivalent. The [frozen report-injection specification](../REPORT_INJECTION.md) contrasts that conditional prediction with a restricted quality-tracking policy that ignores counterfeit reports; it cannot discriminate illusionism from unrestricted HOT or GWT.
<!-- P47 -->

It measures answer accuracy again after injection and requires equivalence within **±5 percentage points** for low versus high and for each versus the natural report. [Decisions fixed before execution](../REPORT_INJECTION.md#frozen-decisions). Possible dissociation alone does not force a behavioral effect: the policy must actually use the report. An answer locked in before the report is altered would be a useless ability control: it could not change. The fresh-answer branch instead asks whether competence survives the manipulation under the declared tolerance.
<!-- P48 -->

For humans, the bridge remains an explanatory analogy about constructed self-description; these model results establish nothing about the presence, absence or illusory nature of human experience.
<!-- P49 -->

## Limits and the next falsifiable step

The central role evidence comes from one model and one task template, with **8, 8 and 16** development scenarios; thousands of variants do not supply thousands of independent observations. [Cohort definitions](../QWEN_POSSESSIVE_RESULTS.md). Bootstrap intervals retain variants within scenarios, and the exact sign-flip tests assume symmetric scenario effects under the null rather than randomized treatment assignment. We have no historical equivalence test for the wording contrast, no prespecified error-direction replication across cohorts, and no measured causal path from a self-report to behavior.
<!-- P50 -->

Human ratings came from the author, without a second rater, and these software audits are not external scientific peer review. Earlier Gemma steering examples motivated the project, but its controlled functional baseline failed the competence gate. [Historical review](../PILOT_REVIEW.md), [revised baseline](../HF_PILOT.md). That closed pilot is neither an additional replication of this role effect nor evidence for a self-monitoring circuit.
<!-- P51 -->

The [frozen role-binding replication](../OWNERSHIP_REPLICATION.md) adds fresh worlds, another executable task template and a second model, making categorical error direction primary and fixing wording-equivalence rules in advance. Both new specifications are unexecuted designs with stopping rules and cost estimates; neither supplies evidence or promises a successful separation. They preserve the distinction that matters for the next step: recurrence of an error across tasks and models, and a causal effect of a report on a decision, are separate questions.
<!-- P52 -->

## Reproducibility

The [claim ledger](CLAIMS.md) maps each paragraph, table and equation to its sources, retaining earlier claim IDs there rather than interrupting the prose. Original archives retain prompts, scores, outcomes and provenance; offline audits check recorded computations without performing new model inference. [Archive and audit details](../QWEN_POSSESSIVE_RUN.md#immutable-final-evidence). From a locked environment with dependencies already installed, the following commands check the stored evidence and software; archive-specific execution records document optional tokenizer/figure verification.
<!-- P53 -->

```bash
uv run --no-sync python scripts/review_possessive_evidence.py
uv run --no-sync python scripts/review_patch_evidence.py
uv run --no-sync python scripts/review_confidence_evidence.py \
  review/evidence/qwen-confidence-v2-4ea43316ce714c03.tar.gz \
  --sha256 ba8b0d01d31da9004758abacd054fbdf664ed235834bc5e7889ab5e3d6cb97dd
uv run --no-sync pytest -q
```
<!-- P54 -->

To repeat only the new descriptive count and compare it with its saved JSON, without modifying an original audit:
<!-- P55 -->

```bash
uv run --no-sync python scripts/count_possessive_errors.py > /tmp/qwen-possessive-error-count.json
cmp review/qwen-possessive-error-count.json /tmp/qwen-possessive-error-count.json
```
<!-- P56 -->

The [review guide](../REVIEW_GUIDE.md) links the full reports, original archives and historical protocols, including failed gates and retained ambiguous ratings.
<!-- P57 -->
