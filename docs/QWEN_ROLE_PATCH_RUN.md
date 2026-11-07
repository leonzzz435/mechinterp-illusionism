# Qwen role activation-exchange execution record

The frozen [activation-exchange protocol](QWEN_ROLE_PATCH.md) was submitted on
2026-11-07 as **one authorized HF Jobs L4 run**. At 2026-11-07T10:42:43.774190+00:00 the provider
reported **RUNNING**. This records startup, not a completed experiment or a result.

## Dispatch and budget

The user explicitly approved the proposed **USD 5 allowance for this single job**, with
90 minutes of cooperative runtime and a two-hour provider timeout. The freshly checked
L4 rate was 13,333 micro-USD/minute: quoted compute upper bound **USD 1.613293**, including
one additional billable minute for rounding. This is not an inspected invoice.

- Job: [`6aef008ce6320c66fad57f27`](https://huggingface.co/jobs/zett13/6aef008ce6320c66fad57f27).
- Created: `2026-11-07 10:42:20.176000+00:00`.
- Run folder: `qwen-patch-3bd8fc27cbb147c9`.
- Source commit: `25d1d1cc20db2a13d39f1c3c60f72ab38da72b87`; clean and pushed before submission.
- Source bundle SHA256: `4a90178adb4e6f98349aac2d1d023851573cdc86ae5914cae287941951bd56b6`.
- Private source revision: `2842a35f1a7efba8c238773add45cad5b873f9e5`.
- Configuration: `configs/qwen-role-patch.json`; SHA256 `5c0be5d0aee247e99539c6a087f38f7571e463ddd28b91beb8c5d66ff59ffb5e`.
- Frozen plan SHA256: `1fad9f0be13b103aca75a2d1eb6f3209ba15efa6c1bb994b0fe1ec812de48600`.
- Model/tokenizer: Qwen2.5-7B-Instruct at `a09a35458c702b33eeacc393d103063234e8bc28`.
- One L4, unquantized BF16, batch 1, eight known scenarios, 11,264 scientific selections
  plus 32 unpatched technical repeats. No generation, SAE or model-comparison arm.

The [credential-free dispatch receipt](../review/qwen-role-patch-job.json) preserves all
source/image/config pins and the hardware quote. The local duplicate guard is
`.hf-jobs/qwen-role-patch.json`; keep it intact. The private artifact repository is
`zett13/mechinterp-illusionism-results`.

## Initial checkpoint verified

At `2026-11-07T10:43:48.269361+00:00`, the provider reported `RUNNING`. The initial private
checkpoint at revision `8744c226b218b51252d2d517c106a5d00b109679` contains the expected
engine, source commit, source-package hash, frozen plan/config hashes and **11,296 planned
records**. It has zero completed records at this initial upload; this confirms setup and
persistence, not numerical parity or a scientific result. Logs show environment setup complete
and the pinned model weights downloading. [Startup verification](../review/qwen-role-patch-startup.json).

## Retrieve from either computer

```bash
uv run --script scripts/hf_jobs.py status --receipt review/qwen-role-patch-job.json
uv run --script scripts/hf_jobs.py logs --receipt review/qwen-role-patch-job.json
uv run --script scripts/hf_jobs.py fetch --receipt review/qwen-role-patch-job.json
```

The tracked receipt is sufficient for these read-only commands on another checkout with
HF authentication. Fetch pins one artifact revision and verifies available export checksums.
Preserve the downloaded original archive unchanged before working on an analysis copy.
The running job remains pinned to the source commit above even after this handover is committed.

The worker uploads an initial checkpoint, each completed scenario block and a final export
when it can exit cooperatively. Local trial commits are atomic; after a provider kill the
last uploaded checkpoint remains available. Resuming is a separately approved job, not an
automatic retry. A technical failure stops execution and retains available scores and errors.

## What to inspect after completion

1. Coverage: 11,264 scientific trials and 32 technical repeats, with errors visible.
2. Historical baseline parity, own-state/repeat parity, candidate mappings and BF16 edit norms.
3. The sole primary contrast C, both transfer directions, eight scenario effects and controls.
4. Generated report, complete prespecified example, article section and SVG/PDF/PNG figures.

No inference about transfer is justified from job status alone. An incomplete or technically
invalid run cannot pass the frozen decision. The original capability-screen failure remains
unchanged, and this exploratory intervention cannot establish consciousness or human illusionism.
