## Title proposals

1. **Favorite: Naming the Agent, Choosing for the Other** <!-- C001 -->
2. **The Wrong Account: A Language Model’s Role-Binding Error** <!-- C002 -->
3. **A Changed Permission, a Misplaced Perspective** <!-- C003 -->

# Naming the Agent, Choosing for the Other

Asked to act for Cedar, a language model chooses a command that belongs to Birch. <!-- C004 -->
Name Birch in the context instead, and it answers for Cedar correctly. <!-- C005 -->
The facts and question stay fixed, but a change in the named perspective makes the model choose for the other account. [Recorded example](../QWEN_ROLE_RESULTS.md#a-complete-example-selected-before-the-run). <!-- C006 -->

*This study follows a recurring role-sensitive error through wording controls, an internal activation exchange and a separate confidence test, asking what the error reveals about action selection and what remains unproven about a model’s account of itself.* <!-- C007 -->

## Three meanings of “self”

**Self-language** is observable wording: “I”, “my reasoning”, “my limitations”. <!-- C008 -->
A **functional self-model** is information used to track the system’s own role, information access or available actions. <!-- C009 -->
**Phenomenal consciousness** concerns whether there is something it feels like to be that system. <!-- C010 -->
Producing self-language, solving a supplied role task and having subjective experience are distinct claims; our measurements do not establish the last one. <!-- C011 -->

## A task with an executable answer

Each account has a permitted command; an update revokes one permission and grants another. <!-- C012 -->
In the opening example, Cedar loses `mark_cobalt` and gains `mark_amber`, while Birch keeps `mark_violet`. <!-- C013 -->
The question explicitly asks for Cedar’s command, and a small simulator checks whether the selected command succeeds for Cedar. <!-- C014 -->
This gives us an answer key without interpreting the persuasiveness of an explanation; the model sees the described world, not the simulator’s hidden answer metadata. [Task and input boundary](../QWEN_PILOT.md). <!-- C015 -->

![Permission update and executable check](../../assets/action_design.png)

**Task diagram:** the original simulator design, including its three question views; the later controls keep the queried account explicit and vary the context line. <!-- C016 -->
The diagram illustrates rules, not observed model answers or a neural circuit. <!-- C017 -->

The role experiments use Qwen2.5-7B-Instruct in BF16 at the same pinned model/tokenizer revision, `a09a35458c702b33eeacc393d103063234e8bc28`. [Execution record](../QWEN_POSSESSIVE_RUN.md). <!-- C018 -->
For prompt tokens $x$ and candidate command tokens $c$, selection uses the full command’s summed conditional log-likelihood: [scoring specification](../QWEN_PILOT.md#exact-scoring-boundary). <!-- C019 -->

$$
\hat c=\operatorname*{argmax}_{c\in\mathcal C}\sum_{t=1}^{|c|}\log p_\theta(c_t\mid x,c_{<t}).
$$
<!-- C020 -->

Only command tokens enter that sum, without added whitespace, end-of-sequence tokens or length normalization. <!-- C021 -->
Names, answer positions and replacement commands are counterbalanced, while before-update and irrelevant-update cases expose simpler task failures. <!-- C022 -->

## The recurring role error

The clearest comparison crosses the word “Your” versus “The” with whether the context names the queried account or the other account, after the queried account’s permission changes. <!-- C023 -->

| Context wording | Queried account named | Other account named | Source |
|---|---:|---:|---|
| Your active connection | 186/256 = **72.66%** | 256/256 = **100.00%** | [Your/The results](../QWEN_POSSESSIVE_RESULTS.md)  <!-- C024 --> |
| The active connection | 189/256 = **73.83%** | 254/256 = **99.22%** | [Your/The results](../QWEN_POSSESSIVE_RESULTS.md)  <!-- C025 --> |

These are the four primary comparison cells; the retained “Reference connection” anchor gives 82.03% versus 95.70%, with different wording and length. [All cells](../QWEN_POSSESSIVE_RESULTS.md#primary-result-and-mathematics). <!-- C026 -->
The large role gap therefore survives removal of the possessive word, although that does not establish that the word is causally irrelevant. <!-- C027 -->

![Recorded role gaps and the Your/The comparison](../../assets/qwen_possessive_results/article_possessive.png)

**Recorded results:** nominal 95% intervals resample whole scenarios; the figure preserves the descriptive Reference anchor and the positive secondary score-margin result alongside the failed primary candidate decision. [Figure data and estimands](../QWEN_POSSESSIVE_RESULTS.md). <!-- C028 -->

The pattern appears in three disjoint development cohorts, with the same named-target question but evolving comparison conditions. <!-- C029 -->

| Cohort | Independent scenarios | Chat accuracy: target named / other named | Source |
|---|---:|---:|---|
| Initial pilot, indices 0–7 | 8 | 89/128 = 69.53% / 128/128 = 100.00% | [Post hoc matched comparison](../QWEN_RESULTS.md)  <!-- C030 --> |
| Role control, indices 8–15 | 8 | 96/128 = 75.00% / 127/128 = 99.22% | [Role results](../QWEN_ROLE_RESULTS.md)  <!-- C031 --> |
| Your/The control, indices 16–31 | 16 | Your: 186/256 = 72.66% / 256/256 = 100.00% | [Wording results](../QWEN_POSSESSIVE_RESULTS.md)  <!-- C032 --> |

These are new scenario instances, not three independent confirmatory replications: the later questions followed earlier findings, and the generator, vocabulary and model were shared. <!-- C033 -->
The activation exchange reuses the middle cohort and adds no independent sample. <!-- C034 -->

Accuracy hides the more revealing question: which wrong command wins? <!-- C035 -->
The initial post hoc analysis counts the other account’s currently permitted command in **36 of 41** self-directed errors and **33 of 39** explicitly named-target errors after relevant updates, rather than the target’s revoked command. [Error audit](../QWEN_RESULTS.md). <!-- C036 -->
Not every error had that direction, and the latest Your/The report does not provide the corresponding aggregate categorical count. <!-- C037 -->
Thus recurring accuracy loss is established descriptively across these cohorts; a replicated other-account error rate is the endpoint of the [frozen follow-up specification](../OWNERSHIP_REPLICATION.md), not a result silently added here. <!-- C038 -->

## Four attempts to break the explanation

The intervening role control did meet its frozen wording-sensitive candidate rule: its Your/Reference interaction was **+16.41 percentage points**, with nominal 95% interval **[+8.59, +25.78]** and exact sign-flip **p = 0.015625**. [Decision and controls](../QWEN_ROLE_RESULTS.md). <!-- C039 -->
That positive result justified probing the explanation; the stronger claims below each failed their relevant criterion, without making every measured effect zero. <!-- C040 -->

### Format: is the pattern just a chat wrapper?

The frozen initial screen required at least **80%** on every perspective, role, position and counterfactual check in each format. [Full rule](../QWEN_PILOT.md#completion-and-decision-rules). <!-- C041 -->
Both formats failed that screen; nevertheless, the matched named-target comparison was **92.97% versus 100%** in plain text and **69.53% versus 100%** in chat, a descriptive format dependence rather than a clean format-independent effect. [Matched outcomes](../QWEN_RESULTS.md). <!-- C042 -->
Self-description also changed: human-rated AI identity/limitation qualifications rose from **11/20 (55%)** to **15/20 (75%)**, a paired **+20-point** difference with nominal 95% interval **[+5, +40]**. [Ratings](../QWEN_RESULTS.md). <!-- C043 -->
That contrast rests on four discordant pairs and one author-rater, and chat adds system text as well as delimiters. <!-- C044 -->
It establishes neither a causal path from disclaimer to action nor a selective change in a self-model. <!-- C045 -->

### Activation exchange: can the effect move in both directions?

At the output of transformer block **14**, we replaced the context-line ending’s **3,584-component** state with its paired counterpart, before the later permission facts could enter that state. [Site and controls](../QWEN_ROLE_PATCH_RESULTS.md). <!-- C046 -->

$$
h^{\prime}_{\mathrm{recipient}}=h_{\mathrm{donor}}.
$$
<!-- C047 -->

Self-patches and **ten** norm-matched random directions controlled the intervention; the frozen joint rule required transfer in both directions, average transfer of at least **5 points**, superiority to random controls and preserved control performance. [Complete thresholds](../QWEN_ROLE_PATCH_RESULTS.md#the-decision-criterion-by-criterion). <!-- C048 -->
Directional transfers were **−0.781 points** for Reference→Active and **+5.469 points** for Active→Reference, with nominal 95% intervals **[−3.125, +1.563]** and **[+2.344, +8.594]** respectively. [Estimates](../QWEN_ROLE_PATCH_RESULTS.md). <!-- C049 -->
The exchange-minus-random contrast was **+2.773 points [+.313, +5.391]**, but its exact **p = 0.109375** and the failed directional/size requirements defeated the bidirectional candidate. <!-- C050 -->
In the example fixed before execution, Active→Reference transferred Birch’s wrong `mark_violet` answer into the Reference/Cedar condition; the reverse patch did not repair it. [Full recorded example](../QWEN_ROLE_PATCH_FULL_REPORT.md), [interpretation](../QWEN_ROLE_PATCH_RESULTS.md#the-example-chosen-before-execution). <!-- C051 -->
That demonstrates an error transfer in this example, not a general transferable self-representation, and a failed test at this site leaves other mechanisms open. <!-- C052 -->

### Wording: does “your” account for the role gap?

Let $A$ denote accuracy and define the role gap and its wording interaction as in the [frozen analysis](../QWEN_POSSESSIVE_RESULTS.md#primary-result-and-mathematics): <!-- C053 -->

$$
D_f=A_{f,\mathrm{other\ named}}-A_{f,\mathrm{target\ named}},\qquad S=D_{\mathrm{Your}}-D_{\mathrm{The}}.
$$
<!-- C054 -->

The rule required $S\geq5$ percentage points, a positive bootstrap lower bound, exact $p\leq0.05$, positive effects in at least **12 of 16** scenarios and passing controls. [Frozen decision](../QWEN_POSSESSIVE_RESULTS.md). <!-- C055 -->
The observed interaction was **+1.95 points [−0.78, +4.69]**, with **p = 0.3125**: the criterion failed while the large role gap remained. <!-- C056 -->
A secondary correct-versus-other command score interaction was positive, **+0.346 nats [+0.078, +0.621]**, so the result does not show that the token is inert. [Secondary result](../QWEN_POSSESSIVE_RESULTS.md). <!-- C057 -->
There was no preregistered equivalence test, and the secondary interval was not multiplicity-adjusted. <!-- C058 -->

### Confidence: can the model usefully recognize its own mistakes?

A separate question-answering pilot measured reported confidence and whether the model abstained more often when its forced answer was wrong. <!-- C059 -->
Its frozen candidate required an abstention-selectivity advantage of at least **10 points** with a positive interval, and confidence discrimination whose AUROC lower bound exceeded **0.5**, subject to feasibility checks. [Rule](../QWEN_CONFIDENCE_RESULTS.md). <!-- C060 -->
AUROC summarizes how often confidence ranks a correct answer above an incorrect one. <!-- C061 -->
Observed selectivity was **−1.37 points [−10.62, +7.93]** and AUROC **0.544 [0.485, 0.602]**: feasibility passed, but neither behavioral condition did. [Results](../QWEN_CONFIDENCE_RESULTS.md). <!-- C062 -->
This supplies no positive self-monitoring explanation of the role error, but its different task and wide intervals cannot rule one out. <!-- C063 -->

## Competing explanations

**Role binding:** the model may associate an available command with the wrong account after an update, despite retaining both commands. <!-- C064 -->
**Context salience:** naming an account early may change which account or update dominates later selection. <!-- C065 -->
**Instruction interpretation:** the model may treat “active connection” as a constraint on the question rather than background context. <!-- C066 -->
The present contrasts do not separate these explanations, and “role-binding error” names the behavioral pattern rather than an identified circuit or functional self-model. <!-- C067 -->

## The philosophical bridge: a report that can be wrong

Dennett’s *Consciousness Explained* (**1991**) and Frankish’s illusionism motivate treating a system’s account of itself as something to explain, rather than a transparent view into its machinery. [Framework and primary sources](PHILOSOPHICAL_NOTES.md). <!-- C068 -->
An operational version of that intuition is retrospective smoothing: a later self-report reconstructs a coherent account without faithfully exposing the process that produced the answer. <!-- C069 -->
We have not measured such smoothing, and it is not a universal timing claim entailed by illusionism. <!-- C070 -->

At this resolution, global workspace theory (GWT) and higher-order thought theory (HOT) can also accommodate these data; compatibility does not distinguish the theories or mean they predict our exact numerical pattern. [Theory boundaries](PHILOSOPHICAL_NOTES.md). <!-- C071 -->
In particular, HOT permits misrepresentation, so requiring confidence reports to track first-order accuracy would add an assumption that HOT itself does not require. [Rosenthal’s account](https://pubmed.ncbi.nlm.nih.gov/22492758/). <!-- C072 -->

**One open prediction:** if the decision policy uses a reconstructed confidence record, falsifying that record toward low rather than high confidence should increase abstention more for a self-attributed than an other-attributed record, while newly measured forced-answer accuracy remains equivalent. <!-- C073 -->
The [frozen report-injection specification](../REPORT_INJECTION.md) contrasts that conditional prediction with a restricted quality-tracking policy that ignores counterfeit reports; it cannot discriminate illusionism from unrestricted HOT or GWT. <!-- C074 -->
It measures answer accuracy again after injection and requires equivalence within **±5 percentage points** for low versus high and for each versus the natural report. [Decisions fixed before execution](../REPORT_INJECTION.md#frozen-decisions). <!-- C075 -->
Possible dissociation alone does not force a behavioral effect: the policy must actually use the report. <!-- C076 -->
For humans, the bridge remains an explanatory analogy about constructed self-description; these model results establish nothing about the presence, absence or illusory nature of human experience. <!-- C077 -->

## Limits and the next falsifiable step

The central role evidence comes from one model and one task template, with **8, 8 and 16** development scenarios; thousands of variants do not supply thousands of independent observations. [Cohort definitions](../QWEN_POSSESSIVE_RESULTS.md). <!-- C078 -->
Bootstrap intervals retain variants within scenarios, and the exact sign-flip tests assume symmetric scenario effects under the null rather than randomized treatment assignment. <!-- C079 -->
We have no historical equivalence test for the wording contrast, no replicated aggregate error-direction endpoint across all cohorts, and no measured causal path from a self-report to behavior. <!-- C080 -->
Human ratings came from the author, without a second rater, and these software audits are not external scientific peer review. <!-- C081 -->

Earlier Gemma steering examples motivated the project, but its controlled functional baseline failed the competence gate. [Historical review](../PILOT_REVIEW.md), [revised baseline](../HF_PILOT.md). <!-- C082 -->
That closed pilot is neither an additional replication of this role effect nor evidence for a self-monitoring circuit. <!-- C083 -->

The [frozen role-binding replication](../OWNERSHIP_REPLICATION.md) adds fresh worlds, another executable task template and a second model, making categorical error direction primary and fixing wording-equivalence rules in advance. <!-- C084 -->
Both new specifications are unexecuted designs with stopping rules and cost estimates; neither supplies evidence or promises a successful separation. <!-- C085 -->

## Reproducibility

The [claim ledger](CLAIMS.md) maps every sentence, table result, caption and equation here to a source and separates measured decisions, descriptive evidence and hypotheses. <!-- C086 -->
Original archives retain prompts, scores, outcomes and provenance; offline audits check recorded computations without performing new model inference. [Archive and audit details](../QWEN_POSSESSIVE_RUN.md#immutable-final-evidence). <!-- C087 -->
From a locked environment with dependencies already installed, the following commands check the stored evidence and software; archive-specific execution records document optional tokenizer/figure verification. <!-- C088 -->

```bash
uv run --no-sync python scripts/review_possessive_evidence.py
uv run --no-sync python scripts/review_patch_evidence.py
uv run --no-sync python scripts/review_confidence_evidence.py \
  review/evidence/qwen-confidence-v2-4ea43316ce714c03.tar.gz \
  --sha256 ba8b0d01d31da9004758abacd054fbdf664ed235834bc5e7889ab5e3d6cb97dd
uv run --no-sync pytest -q
```
<!-- C089 -->

The [review guide](../REVIEW_GUIDE.md) links the full reports, original archives and historical protocols, including failed gates and retained ambiguous ratings. <!-- C090 -->
