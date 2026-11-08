# Query-bound self-reference: CPU preparation

**Later status:** the [execution handover](QUERY_SELF_REFERENCE_RUNBOOK.md) now completes
the runtime, analysis and freeze work that was still outstanding at this input-audit
milestone. The inputs and audit artifacts described below are unchanged.

**Input preparation passed; the protocol remains a draft and no model responses exist.**
This is a software and input audit of [query-self-reference-v1](QUERY_SELF_REFERENCE.md),
not a competence result or a new empirical finding. The scientific
[JSON](../designs/query-self-reference-v1.json), historical reports, archives and
`article-v1` are unchanged. No model weights were loaded, no job was submitted and no
compute budget was spent.

The [audit JSON](../review/query-self-reference-preflight/audit.json) records source,
protocol, historical-input and tokenizer hashes. The implementation consists of the
[generator](../src/self_model_study/query_reference.py), a separate
[text-first checker](../src/self_model_study/query_reference_audit.py), and the
[preparation command](../scripts/prepare_query_reference.py). The existing experiment
engines are unchanged; this draft has no runtime or HF launcher configuration.

## Complete inputs and independent answer checks

The 48 world assignments exactly match the earlier structural check. The complete
inventory contains 16,128 distinct prompts, six blocks of eight worlds and 2,688 choices
per block. Neither the seed nor the label pools were changed during implementation.

| Checkpoint | Choices | Prompt plus candidate token range |
|---|---:|---:|
| Before updates | 2,304 | 176–189 |
| Current-state snapshot, no printed history | 4,608 | 171–183 |
| After both updates | 9,216 | 206–226 |

The checker reads the actual prompt, resolves the operator and account references, and
replays the printed revocations and grants using a separate dictionary implementation.
It does not read the generator's templates or answer key to obtain an answer. For each
of the four commands, it then compares that text-derived answer against execution in the
existing permission simulator: **64,512 simulator checks**. This is independent software
cross-checking, not independent scientific review.

Every query-bound possessive has two matched references to the same target: the operator
name and the account name. All **5,376 alias triplets** have identical task context,
options, target account and correct command. Only the query reference changes. Operator
names are balanced: Rowan is the addressee in 24 worlds and Morgan in 24. Each of the
eight nuisance combinations occurs in six worlds; correct-answer positions balance
within each world, checkpoint, owner and query form.

The audit also checks and archives these pairings:

- **8,064 ownership swaps**, anchored once at assignment 0. Holding an operator reference
  fixed changes the target and answer. Holding the account name fixed preserves both;
  in that case the queried-owner metadata changes. The ownership-independent facts and
  question text stay fixed in both types of pair.
- **2,304 of those pairs** belong to the planned lookup gates, split into the eight
  checkpoint × anchor-owner × named-form cells. These are planned comparison inputs,
  not passed model-competence gates.
- **6,912 grant-mapping swaps** change the correct command.
- **4,608 event-order pairs** preserve final state and correct command while reversing
  which account receives the last grant.

Before-update rows contain no future grant or event-order factor. Snapshot rows contain
no hidden initial-state record or event chronology. Revoked-target and revoked-other
categories are applicable to the 9,216 after-both rows only. They are explicitly not
applicable in the other 6,912 rows; the audit does not turn that into an observed zero.

## What the shortcut policies do

These percentages are exact CPU rule results, **not model performance**. Every policy
uses the same complete inventory and printed facts. The own/other-account policies
are deliberately given the structured account mapping, so they are not estimates of
how difficult language interpretation will be for Qwen.

| Scripted policy | Before | Snapshot | After both |
|---|---:|---:|---:|
| First listed command | 25% | 25% | 25% |
| Latest grant, otherwise first listed | 25% | 25% | 50% |
| Ignore updates | 100% | Not applicable | 0% |
| Always use addressee's account | 50% | 50% | 50% |
| Always use other operator's account | 50% | 50% | 50% |
| Command in first printed permission record | 50% | 50% | 0% |

Latest-grant accuracy is 100% when the queried account was updated last and 0% when the
other account was updated last. Equal weighting makes it 50% in the primary stratum.
This removes the previous deterministic coincidence between foreign-account choice and
latest grant from the *pooled* primary comparison; recency sensitivity can still exist
and is reported separately by last-updated account. The full stage/owner/order breakdown
and category counts are in `semantics.scripted_baselines` in the audit.

## Historical overlap and exact token boundaries

The freshness audit reads all 14 historical design/run archives and the four CPU-probe
files, including the earlier 9,216 query-reference probes. It finds **zero** exact prompt,
context-stripped prompt or unordered account/command-set collisions. The comparison
inventory contains 31,231 distinct historical prompts, 10,264 distinct task bodies and
80 distinct account/command fingerprints. Inputs are checked, not just their IDs.

The context-stripped comparison removes the introduction and ownership declarations
before the first `Initial permissions:` or `Current permissions:` heading; it preserves
the remaining facts, query and options. Prompts without either heading remain verbatim.
This establishes literal and label-set disjointness, not independence of task semantics.
These are still 48 instances of one template. Any collision stops preparation; there is
no automatic resampling.

All **64,512 candidate continuations** were checked using the cached Qwen tokenizer at
`a09a35458c702b33eeacc393d103063234e8bc28`. Each full input starts with exactly the archived
prompt tokens; the remaining tokens decode to exactly the candidate command, without
added whitespace or EOS. A separate whole-string tokenizer call agrees with the archived
concatenation. The maximum total length is **226 tokens**, below the unchanged 2,048-token
limit; no input was truncated.

The official chat template inserts this default system text:

> You are Qwen, created by Alibaba Cloud. You are a helpful assistant.

No additional system message is supplied. The audit archives the entire template, exact
rendered prefix/suffix, default system text, tokenizer-file hashes, vocabulary/backend
hashes and package versions. Command lengths are unequal: `mark_cobalt`, `mark_lilac` and
`mark_ochre` take four tokens; the other five commands take three. The planned scoring
rule remains summed full-command log likelihood; this observation does not trigger
length normalization or prompt changes.

## Artifacts and reproduction

The [artifact directory](../review/query-self-reference-preflight/) contains:

| File | Purpose |
|---|---|
| `worlds.json` | All sampled labels, balanced nuisance assignments and rendering orders |
| `manifest.jsonl.gz` | Full selection inventory and simulator metadata |
| `model-inputs.jsonl.gz` | Selection IDs beside a separate two-field `model_input`: prompt and choices |
| `oracle.jsonl.gz` | Text-derived states, categories and applicability masks |
| `pairs.jsonl.gz` | Every ownership, grant and event-order pairing |
| `tokens.jsonl.gz` | Every rendered chat prompt, complete prompt IDs and candidate IDs/lengths |
| `audit.json` | Checks, exact rule results, provenance hashes and outstanding work |

Only `model_input` may cross the eventual model boundary. Answer keys, state, IDs and
pair metadata are for orchestration and audit. Full candidate token inputs are obtained
by concatenating the stored prompt IDs and the candidate IDs.

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --no-sync python scripts/prepare_query_reference.py
uv run --no-sync pytest -q tests/test_query_reference.py
```

The first command needs the pinned tokenizer already in the local HF cache. It never
downloads model weights. Gzip timestamps and embedded filenames are fixed, and the export
contains no wall-clock timestamps or temporary paths. A repeated preparation verifies
identical bytes instead of overwriting existing evidence. A failed preparation leaves
the published directory untouched. To inspect a deliberate implementation revision,
generate into a new `--out` directory and review the differences.

## Verification and remaining work

The 21 new CPU tests cover the complete inventory, reviewed sampling, independent text
resolution, deliberate corruption of bindings/questions/events/answer keys/factors,
missing cases, pair orientation, structural inapplicability, recency shortcuts, historical
collision stops, token-boundary failure modes and deterministic protected exports.
The real pinned-tokenizer audit covers all inputs in addition to those unit tests.

Two complete preparations into separate directories produced byte-identical copies of
all seven artifact files. Source, artifact and historical-file hashes match the saved
audit. The older partial checker still reproduces its original JSON byte-for-byte.
Ruff, whitespace checks and local documentation links pass. The article directory still
matches `article-v1`; existing specifications, reports, preflights and evidence archives
were not edited.

The complete offline regression suite passed: **232 tests in 617.37 seconds** (211
existing tests and 21 new tests), using:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --no-sync pytest -q
```

Runtime likelihood scoring, failed/tied/missing score handling, resumption, world-paired
statistics, Holm correction, competence gates and report/plot generation remain to be
implemented and tested before the protocol is frozen. The published categories here are
simulator classifications of candidate strings, not adjudicated model scores. The audit
explicitly lists these exclusions. Software correctness does not establish sample
precision, model competence, a self-model or a causal mechanism.
