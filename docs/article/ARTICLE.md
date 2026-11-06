# When a Language Model Says “I”, What Is Doing the Work?

*Research article in preparation. Both the original GPU pilot and the revised four-shot development baseline failed their functional capability gates. Confirmatory results remain pending.*

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

We alter an intermediate transformer vector at a specified layer:

$$r'=r+\alpha m v.$$

The direction v has unit length; m is a measured reference scale; α controls size and sign. This defines what changes mathematically. It does not establish the direction's psychological meaning.

We compare a contrast direction, two candidate SAE directions and random controls. We also remove individual encoded contributions while preserving reconstruction error. The controls test whether apparent effects are specific or merely network disturbance.

## What the original pilot showed

Archived examples show Gemma 2 2B continuations becoming more self-related after activation additions. Different SAE directions produced different continuations. These motivated the present study.

The original experiment did not measure self-monitoring ability, establish independent circuits or prove illusionism. Its plot showed vocabulary projections. The original record is retained rather than retrospectively presented as stronger evidence.

## The first controlled pilot: a measurement hurdle

The first Blackwell baseline scored 48.5% on action ownership, 46.1% on information access and 32.0% on capability changes, averaging self and other judgments. All three missed the predefined 80% threshold. Interpreting small intervention effects as changes to a reliable self-model would therefore be premature.

An audit also found a limitation in our answer scoring: it compared bare letter tokens immediately after `Answer:`, while the model usually preferred a newline and could represent space-prefixed letters with different tokens. We preserve those results and introduce a separate, fixed four-shot development protocol using EleutherAI's evaluation harness. This revision changes both prompting and scoring; any improvement cannot be attributed to whitespace alone. The [pilot review](../PILOT_REVIEW.md) records the evidence and unresolved questions.

The revised baseline subsequently completed on an HF Jobs L4: 43.4%, 50.8% and 41.4% accuracy on the same three families, across eight development scenarios per family. It also failed the capability gate. The [cloud pilot report](../HF_PILOT.md) records the fixed protocol and verified artifacts. This ends the current functional pilot; confirmatory results remain pending. The final article will include baseline failures, all task families, controls, uncertainty and degradation, including negative results.

- **Figure 2:** Full continuations chosen by a fixed selection rule.
- **Figure 3:** Dose-response curves with scenario-level uncertainty.
- **Figure 4:** Self-language change alongside contextual-task accuracy change. Separation is a hypothesis, not a promised result.
- **Figure 5:** Random controls, feature ablations and self/other contrasts.

No diagram will be labeled a measured mechanism before circuit-level investigation.

## What would count as separation?

A persuasive result changes one measured property selectively while keeping another within a predefined tolerance, without broadly damaging performance. One significant and one nonsignificant comparison are insufficient.

The current generation and choice assays edit different sets of token positions. This limits a strong dissociation claim and motivates site-matched follow-ups. Independent replication is required before broad claims about language models.

## Returning to consciousness

Illusionist approaches make construction of self-reports an interesting explanatory target. Functional separability could inform that target; other philosophical positions could accommodate it too.

Our question is how observable components of self-related behavior are implemented and connected. A pronoun, a latent feature or a striking quotation cannot establish the presence or absence of subjective experience.

## Reproducibility and limitations

The [protocol](../PROTOCOL.md) defines data, estimands, interventions and stopping rules. Exports contain checkpoint identities, prompts, full outputs and failures. The [runbook](../RUNBOOK.md) separates GPU execution from CPU analysis.

Before publication: complete registered runs, independent ratings, updated novelty review and discussion of task/model limitations. The final title and central figure follow the evidence.
