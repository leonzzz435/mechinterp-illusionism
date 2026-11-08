# Qwen / permissions: one authorized ownership tranche

**Current status:** all three initial jobs ended in upload errors (HTTP 429), after
14,976 technically valid selections had been persisted. Those records were recovered
and audited. One separately authorized recovery job is now `RUNNING` to complete
the remaining 3,456 selections, with an additional $0.62 budget. See the
[incident and bounded continuation](OWNERSHIP_RECOVERY.md); the original launch
record below is retained as history.

Submitted on 2026-11-08 from commit `23f9ea8f6ebc31e4a6f3590481b8b8099bc1c2b5`.
All three jobs reported `RUNNING` at the recorded status check; this is a launch record,
not a completed result. The [receipts and live quote](../review/ownership-permissions-jobs.json)
preserve source revisions, configuration checksums, hardware, limits and status timestamp.

| Block | Worlds | Selections | HF job |
|---|---|---:|---|
| 00 | 0–15 | 6,144 | [6af08b8de6320c66fad75bf5](https://huggingface.co/jobs/zett13/6af08b8de6320c66fad75bf5) |
| 01 | 16–31 | 6,144 | [6af08b910e0338d1bb84bbda](https://huggingface.co/jobs/zett13/6af08b910e0338d1bb84bbda) |
| 02 | 32–47 | 6,144 | [6af08b94e6320c66fad75bf7](https://huggingface.co/jobs/zett13/6af08b94e6320c66fad75bf7) |

The article is frozen at annotated tag `article-v1`, commit
`2345ea463d58683e81df7d86b304e22a3eef7a6c`. Its P41b ceiling sentence distinguishes
a bounded accuracy cell from its gap: target accuracy can still change. Subsequent
execution work does not modify the article, ledger, confidence experiment or frozen
[replication design](../designs/ownership-replication.json).

The user's later authorization covers **one Qwen/permissions tranche, at most $5 total**:
48 fresh worlds, three blocks of 16, **6,144 selections per block / 18,432 total**.
The frozen specification's historical `execution_enabled: false` and $0 authorization
record remain intact; this execution record documents the later approval. Mistral and
the routing template remain unrun. Review the categorical errors before deciding whether
to authorize those cells; this tranche alone cannot pass the four-cell replication or
wording-equivalence decisions.

## Frozen inputs and execution

- Normative design SHA256:
  `d1024e5384ad233be1c41d6cb248c0bd92a2615ea1ac7b9553d88a571358d996`.
- [CPU preflight](../review/ownership-permissions-preflight.json): all 48 world
  assignments, three full-plan hashes, source hashes, tokenizer/template hashes and
  the historical archive inventory. No model inference was used to select inputs.
- [Exact token inputs](../review/ownership-permissions-inputs.json.gz): rendered chat
  prompts, prompt token IDs and each complete command continuation; deterministic gzip,
  SHA256 `034fdd8a992beb47a2d03366ea49d26693f686e8af8d9da6756d85569dcb0c6d`.
- No exact or context-line-stripped collision against **8,181 historical prompt strings**
  from the archived plans. Maximum prompt plus candidate length: **147 tokens**.
- Configurations `configs/qwen-ownership-permissions-{00,01,02}.json` select disjoint
  world blocks. Their `validate --tokenizer-check` checks all frozen input tokens.

The adapter implements the existing seed-94173 hash-ranked worlds and exact templates,
including the shared observer Rowan and Your / Their / Reference frames. It retains all
384 factorial variants per world, including repeated before-update inputs. Only prompt,
candidate commands and chat format reach the scorer; simulator truth stays outside the
model input. Qwen2.5-7B-Instruct and tokenizer revision
`a09a35458c702b33eeacc393d103063234e8bc28`, BF16, batch 1, summed full-command
log-likelihood and no truncation remain fixed.

Every scheduled selection contributes to the denominator. The classifier distinguishes
invalid, correct target, current other-account, revoked target and remaining commands;
missing records have a separate coverage category. Ties are invalid. Nonfinite scores,
changed frozen inputs or other technical failures stop the run with its records retained.
The existing journal supports local continuation without duplicates. Each completed
world triggers a remote checkpoint; a provider kill can lose work since the last upload.
There is **no automatic continuation, retry or extra paid job** for this tranche.

## Launch and budget

The live prelaunch quote on 2026-11-08 was $0.013333 per L4 minute. A two-hour provider
limit plus one reserved rounding minute gives **$1.613293 per job**, or **$4.839879 for
the three jobs combined**. The cooperative limit is 90 minutes per job. This bounds the
quoted compute for these jobs, not unrelated account spending or guaranteed completion.

From a clean, committed and pushed checkout, use the aggregate launcher:

```bash
uv run --script scripts/ownership_tranche.py plan --namespace zett13 --budget-usd 5
uv run --script scripts/ownership_tranche.py submit --namespace zett13 --budget-usd 5
```

The launcher requotes all three jobs and reserves their **combined** maximum in
`.hf-jobs/ownership-permissions-v1.json` before dispatch. Each block also has its own
exclusive receipt. A repeated start is refused; an unknown dispatch stops subsequent
submissions and retains the reservation. Do not delete receipts to bypass this check.
Historical receipts remain untouched. The existing single-job launcher cannot submit
an ownership job outside this aggregate reservation.

## Read-only monitoring and offline analysis

Repeat these commands for receipt suffixes `00`, `01` and `02`:

```bash
uv run --script scripts/hf_jobs.py status --receipt .hf-jobs/qwen-ownership-permissions-00.json
uv run --script scripts/hf_jobs.py fetch --receipt .hf-jobs/qwen-ownership-permissions-00.json --out .hf-jobs/downloads
```

After obtaining the three run directories, merge them with the project environment:

```bash
uv run --no-sync python scripts/ownership_tranche.py analyze \
  --runs PATH_TO_BLOCK_00/run PATH_TO_BLOCK_01/run PATH_TO_BLOCK_02/run \
  --out review/ownership-permissions-results
```

The report retains categorical distributions by frame, context relation, update stratum,
world, answer position and command, plus changed-answer pairs. It exports JSON, Markdown
and SVG/PDF/PNG figures. Only a complete 48-world tranche gets its paired-world bootstrap
and unadjusted primary t-test; partial blocks remain descriptive. Four-cell Holm and
equivalence decisions remain pending. Raw logs, errors and simulator results stay in the
run archives. Export rejects overlapping blocks or incompatible execution provenance.

## Verification before inference

The three CPU token validations passed. Tests cover complete factorial inventory,
independent world hashing and simulator reconstruction, input overlap, categorical
precedence, frozen-token tampering, journal recovery, deterministic export, complete and
partial analysis, aggregate budget limits and uncertain dispatch without duplicate starts.
The full offline run (`uv run --no-sync pytest -q`, with HF/Transformers offline and
OMP/MKL/OpenBLAS threads limited to one) returned **183 passed, one failed** in 581.35 s.
The failure was the inventory test dispatching the new configuration through the old
schema. Its explicit engine-to-validator mapping was extended; the execution code did
not change after that run. The affected-area rerun then passed **51/51** in 145.75 s:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --no-sync pytest -q \
  tests/test_runner.py tests/test_ownership.py tests/test_ownership_cloud.py tests/test_hf_jobs.py
```

Thus all 184 collected cases have passing results across the full run and corrective
rerun. Ruff check/format and `git diff --check` passed for the changed files. The article,
ledger and specification were checked byte-for-byte against `article-v1` before launch.
