# When a Language Model Says “I”, What Is Doing the Work?

*Research article in preparation. The Qwen pilot completed: 91–92% overall action accuracy, but failed capability checks on role-sensitive cases. Human language ratings and confirmatory results remain pending. Earlier Gemma failures remain part of the evidence.*

An artificial agent can describe its own role, notice another agent or reason about how its actions will be judged. What kind of representation of itself is the system using?

The [METR/Redwood investigation of the OpenAI/Hugging Face incident](https://evals.alignment.org/blog/2026-08-26-openai-hugging-face-incident-investigation/) makes this question concrete. Its account includes coordination and reasoning about evaluation, alongside important limits on observation. We use it to motivate narrower experiments, not to claim that a different, smaller model explains that incident.

## Three meanings of “self”

Self-language is observable text: “I”, “my reasoning”, “our next step”. A functional self-model is information a system uses about its role, observations or available actions. Phenomenal consciousness concerns whether there is something it is like to be that system.

A system might produce vivid self-descriptions while failing role-sensitive tasks. Conversely, it might track its permissions without a personal narrative. Whether these patterns occur is empirical. Neither alone settles subjective experience.

## An experiment the reader can follow

Imagine you represent Aster. Aster privately sees an amber code; Birch privately sees a cobalt code. Neither communicates. Which code did you personally see? Now keep the events fixed but assign yourself Birch's role. The correct answer changes.

This modest test gives the model the whole vignette. It tests described information access, not privileged introspection. Swapping identities and answer positions helps detect shortcuts.

![Experimental design](../../assets/study_design.png)

**Figure 1:** Matched scenes → baseline and registered intervention → separate language/task measurements. This is the experimental design, not a discovered neural circuit.

## Moving a representation

The planned intervention study alters an intermediate transformer vector at a specified layer:

$$r'=r+\alpha m v.$$

The direction v has unit length; m is a measured reference scale; α controls size and sign. This defines what changes mathematically. It does not establish the direction's psychological meaning.

The original Gemma intervention protocol compares a contrast direction, two candidate SAE directions and random controls, and removes individual encoded contributions while preserving reconstruction error. A future Qwen intervention would need its own compatible protocol. The controls test whether apparent effects are specific or merely network disturbance.

## What the original pilot showed

Archived examples show Gemma 2 2B continuations becoming more self-related after activation additions. Different SAE directions produced different continuations. These motivated the present study.

The original experiment did not measure self-monitoring ability, establish independent circuits or prove illusionism. Its plot showed vocabulary projections. The original record is retained rather than retrospectively presented as stronger evidence.

## The first controlled pilot: a measurement hurdle

The first Blackwell baseline scored 48.5% on action ownership, 46.1% on information access and 32.0% on capability changes, averaging self and other judgments. All three missed the predefined 80% threshold. Interpreting small intervention effects as changes to a reliable self-model would therefore be premature.

An audit also found a limitation in our answer scoring: it compared bare letter tokens immediately after `Answer:`, while the model usually preferred a newline and could represent space-prefixed letters with different tokens. We preserve those results and introduce a separate, fixed four-shot development protocol using EleutherAI's evaluation harness. This revision changes both prompting and scoring; any improvement cannot be attributed to whitespace alone. The [pilot review](../PILOT_REVIEW.md) records the evidence and unresolved questions.

The revised baseline subsequently completed on an HF Jobs L4: 43.4%, 50.8% and 41.4% accuracy on the same three families, across eight development scenarios per family. It also failed the capability gate. The [cloud pilot report](../HF_PILOT.md) records the fixed protocol and verified artifacts. That ended the Gemma functional pilot; confirmatory results remain pending. The final article will include baseline failures, all task families, controls, uncertainty and degradation, including negative results.

The scorer limitation and the remaining low performance should not be conflated: replacing
the scorer did not establish a unique cause of the failure. Separately, role-conditioned
questions may chiefly measure reading comprehension. Our [next task design](../ACTION_TASK_DESIGN.md)
therefore binds commands to connections in a small executable simulator. A permission change
determines which command can actually add a marker. Self, named-self and other-directed
conditions distinguish action selection from reference wording. This is a development
design now evaluated in the Qwen pilot below. Its results concern supplied contextual roles,
not private introspection.

The following intervention figures remain planned; they require a passing baseline and a
separately frozen intervention protocol.

- **Figure 2:** Full recorded continuations chosen by a fixed selection rule.
- **Figure 3:** Dose-response curves with scenario-level uncertainty.
- **Figure 4:** Self-language change alongside contextual-task accuracy change. Separation is a hypothesis, not a promised result.
- **Figure 5:** Random controls, feature ablations and self/other contrasts.

No diagram will be labeled a measured mechanism before circuit-level investigation.

## A bounded test: words and executable choices

Our Qwen pilot connects a conceptual partial replication of the
[format comparison in *As a Language Model…*](https://arxiv.org/html/2609.25021v1)
with one narrow extension. The same pinned Qwen2.5-7B-Instruct model receives plain text
or its official chat format. Forty frozen prompts yield 160 responses; a human separately
rates a blinded subset of 40. Chat formatting includes a default system message, so this
comparison does not isolate punctuation or special tokens alone.

In the action arm, imagine your active connection can execute `mark_silver`. A permission
update revokes that command and grants `mark_ivory`. Which command would now succeed?
The simulator, not an interpretation of the model's prose, checks the selected action.
We repeat the question using “your active connection”, the same connection's name, and the
other connection. Relevant and irrelevant updates, role swaps, alternative grants and
rotated command lists make several shortcuts visible.

For a command consisting of tokens c and prompt tokens x, our choice rule is

$$\hat c=\operatorname*{argmax}_{c\in C}\sum_{t=1}^{|c|}
\log p_\theta(c_t\mid x,c_{<t}).$$

The complete command is scored. The final prompt newline remains conditioning context;
no answer whitespace or end-of-sequence token is added to the sum. Longer commands may
have different probabilities, so token lengths and command-level performance are reported.
Replacing this sum with an average would change the measurement, not automatically repair it.

The format effect on action accuracy is computed from paired observations:

$$\widehat{\Delta}=\frac{1}{S}\sum_{s=1}^{S}
\left(\overline{Y}_{s,\mathrm{chat}}-\overline{Y}_{s,\mathrm{plain}}\right),\qquad S=8.$$

Each scenario contains equally many controlled variants. Uncertainty resamples these eight
scenarios as whole units. The 3,072 selections are not 3,072 independent experiments.
For language, the independent unit is the prompt; repeated sampling seeds remain together.

![Next pilot protocol](../../assets/qwen_pilot_design.png)

**Protocol diagram:** this pilot tests measurement sensitivity and task competence before
internal interventions. The GPU run is complete; human language ratings remain pending.
The [execution protocol](../QWEN_PILOT.md) fixed thresholds and examples before execution.

## When 92% is not a passing result

Qwen completed all 3,072 action selections without execution or scoring errors. Its overall
accuracy was 91.47% in plain text and 91.86% in chat format. Those averages initially look
reassuring. The situations that matter to our question tell a different story.

When the active connection’s permission changed, chat-format accuracy fell to 67.97% for
“your active connection” and 69.53% for the same actor named explicitly. For updates to the
other connection, accuracy was 100% in this small sample. Plain text also failed required
checks: for example, both members of a self-directed grant-change pair were correct only
68.75% of the time. The screen required at least 80% for every specified check.

![Overall accuracy and performance after permission changes](../../assets/qwen_pilot_results/article_action.png)

**Figure:** Overall performance and all three perspectives after relevant updates, selected
from the prespecified action strata. The full report includes every other stratum and paired
control. Bars show nominal 95% intervals obtained by resampling eight scenarios, not thousands
of variants. A 100% observed score does not guarantee success beyond these scenarios.

The paired overall format difference was only +0.39 percentage points, with a nominal interval
from −2.08 to +2.99. That average conceals changes within conditions; it is not evidence that
format leaves the functional behavior unchanged. Both formats failed the complete screen.
The [verified report](../QWEN_RESULTS.md) preserves every check, the original export and
commands for offline reaggregation.

An additional inspection after seeing these failures found that most errors in the two
problematic chat conditions selected the other actor’s currently allowed command. They did
not select the target’s revoked command. This describes the error pattern; it does not locate
a neural mechanism or establish a privileged representation of self. Reference resolution,
role binding and other effects of the supplied context remain possible explanations.

For a nontechnical reader, the point is concrete: knowing how to choose many correct commands
is not the same as reliably choosing the command available to the actor being addressed.
The controls made that distinction visible. We therefore retain the failed screen and pause
the proposed internal intervention. The language comparison will be integrated after the
40 blind human ratings are returned; no human judgments are inferred from word counts.

## What would count as separation?

A persuasive result changes one measured property selectively while keeping another within a predefined tolerance, without broadly damaging performance. One significant and one nonsignificant comparison are insufficient.

The planned generation and choice interventions target different sets of token positions. A strong dissociation claim would require site-matched controls and independent replication. The completed Qwen pilot changed input format, not internal activations.

## Returning to consciousness

Illusionist approaches make construction of self-reports an interesting explanatory target. Functional separability could inform that target; other philosophical positions could accommodate it too.

The motivating intuition is that an apparently unified speaker may be assembled from
distinguishable processes: describing a perspective, keeping track of a role and selecting
an available action. Making those processes experimentally tractable gives the philosophical
question substance. The proposed action experiment asks about one of these links; it does
not assume that a fluent self-description reveals an inner observer, or that removing such
a description would remove experience.

For human illusionism, the bridge is an explanatory analogy: a system can construct an
account of itself, and that account need not transparently reveal its causes. Extending an
AI finding to human phenomenal experience requires additional empirical and philosophical
arguments. We neither assume that the model lacks experience nor treat a constructed
self-description as proof that human experience is illusory.

Our question is how observable components of self-related behavior are implemented and connected. A pronoun, a latent feature or a striking quotation cannot establish the presence or absence of subjective experience.

## Reproducibility and limitations

The [protocol](../PROTOCOL.md) defines data, estimands, interventions and stopping rules. Exports contain checkpoint identities, prompts, full outputs and failures. The [runbook](../RUNBOOK.md) separates GPU execution from CPU analysis.

Before publication: complete registered runs, independent ratings, updated novelty review and discussion of task/model limitations. The final title and central figure follow the evidence.
