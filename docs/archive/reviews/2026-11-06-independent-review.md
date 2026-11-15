# Fresh-context AI review, 2026-11-06

The initial reviewer was a separate Codex agent given the repository, review scope and target
commit `d86377690258a0d03a071394b950e9c53fb7ea7a`, without the conversation history. It worked
read-only and ran CPU checks. This is an independent-context AI review, not external human
peer review or a publication endorsement. The findings below preserve the reviewed draft's
defects even though the working tree was subsequently corrected.

**Initial conclusion:** substantive review was possible; another GPU pilot was not ready.
No simulator execution bug was demonstrated. Six existing action-task tests passed despite
two shortcuts that could solve all 3,840 draft variants.

## Findings at d863776

### P1: exported IDs encode the answer-relevant condition

`src/self_model_study/action_task.py:120` built IDs from updated actor, assigned identity,
view, phase and rotation; `model_input()` at lines 145–147 exported them with the choices.
The reviewer reconstructed **3,840/3,840 correct commands using only IDs and choices**, never
reading the prompt. The test at `tests/test_action_task.py:94–95` only excluded a literal
command string from the ID and therefore missed this leak.

No completed experiment was contaminated by this draft: it has no model adapter, and its
prompt text itself omitted IDs. The defect was an exposed interface hazard.

**Correction:** public IDs are opaque digests; oracle metadata remains separate. Tests check
the boundary and ID format. A future adapter must also demonstrate that only its declared
prompt/continuation reaches the model, excluding IDs and other bookkeeping. Hashes are join
keys, not a secrecy mechanism against someone with the generator or oracle dataset.

### P1: list positions reveal the new permission without reading it

In `action_task.py:98,109–115`, actors initially held commands 0/1 and always received command
`updated + 2`. All command-order changes were cyclic rotations. A policy could identify the
target's initial permission, check whether the event concerns that target, and select the
command two list positions later for a relevant after-update. Otherwise it kept the initial
command. This gave **3,840/3,840 successes without reading the granted command value** and
passed the originally proposed role, position and before/after checks.

**Correction:** independently vary the granted value between both initially unavailable
commands, holding the target, initial state and list order fixed. This creates 192 variants
per scenario, 7,680 across 40 development scenarios. In paired grant counterfactuals the answer
must change only for relevant after-updates. The discovered policy is retained in the audit:
it now gets **87.5% pooled, 50% after relevant updates and 100% after irrelevant updates**.
An 80% pooled gate would still admit it; subgroup and paired criteria are necessary.

### P1: the next model experiment is not specified or implemented

The draft only added a `design` CLI. The old cloud configuration/harness still evaluates the
old A/B/C/D tasks. Model/revision, tokenizer/chat boundary, continuation whitespace and
termination, summed versus normalized likelihood, ties, screening subset, numerical paired
criteria, diagnostic decoding and failure denominators were not frozen. The existing native
harness integration verifies its own multi-token scoring, not a future command adapter.

**Still open.** Specify one bounded screen and test its actual rendered inputs, continuations,
token IDs/lengths/scores and executor binding on CPU before spending on it. The failed pilots
do not authorize a model tournament or intervention sweep. Historical scoring and prompt
changes were confounded; no unique cause of low accuracy has been established.

### P2: the construct remains supplied-state permission reasoning

Each prompt supplies the relevant state. The evaluator binds the actor and executes the
command; before and after are separate observations. No persistent learning or feedback is
tested. A lookup policy can succeed. Self/named-self/other controls are useful, but success
alone is not evidence of a privileged neural self-model, introspection or phenomenal experience.
One template and a small vocabulary further limit generalization.

**Still open as a scientific limitation, not a software defect to conceal.** The article must
keep this boundary visible. Later causal claims need matched intervention sites and measured
delivered edits; previous ablation nulls are unresolved.

## Independent recheck of the corrections

The same reviewer was asked to test the fixes read-only, before the final documentation was
complete. It passed all seven action-task tests and independently checked all 7,680 variants:

| Check | Result |
|---|---:|
| Unique opaque IDs | 7,680 |
| Gold commands at each list position | 1,920 |
| Relevant-after grant pairs changing the gold command | 960/960 |
| Other grant pairs preserving the gold command | 2,880/2,880 |
| Simulator oracle | 100% |

All grant pairs preserved initial permissions, command presentation, assigned identity and
target. After prompts differed only in the granted value. The reviewer found no further
blocking simulator flaw. Its verdict remained **ready for further design review, not yet for
another GPU pilot**. These are software/scripted-policy checks, not results from a language model.

The corrected generator is now explicitly versioned `action-permissions-v2.1-draft`, distinct
from the reviewed `action-permissions-v2-draft`. Exported manifests also pin source and data
hashes. Final documentation and evidence packaging were prepared by the primary agent;
the first recheck did not validate those documents.

In a final read-only check, the reviewer also inspected this report and the review guide,
ran the offline archive audit, confirmed the historical raw artifacts are tracked, and
passed all nine targeted action/evidence tests. It found no material correction needed and
rechecked the full design after the version change. The default design checksum is
`5711f0d53a6d67a4874ae4c37f526a469cc6851437139b0ee9c88037dfcd0ffd`.
This check did not repeat model inference or audit every historical Blackwell numerical claim.

## Reviewability changes

The [review guide](../REVIEW_GUIDE.md) now records study scope, philosophical claim boundaries,
protocol lineage, raw evidence inventory, reproduction commands and unfinished decisions.
The complete original cloud archive is included unchanged in Git and has a standard-library
offline verifier. Historical Blackwell raw runs and exports were already tracked. This
supports a review without HF access or chat history; it does not imply a completed novelty
review, power analysis, new-model baseline or external human assessment.
