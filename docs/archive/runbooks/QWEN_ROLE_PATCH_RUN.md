# Qwen role activation-exchange execution record

The frozen [activation-exchange protocol](QWEN_ROLE_PATCH.md) completed on
2026-11-07 as **one authorized HF Jobs L4 run**. All 11,264 scientific trials and 32 technical
repeats are present, with no failed technical checks. The
[result](QWEN_ROLE_PATCH_RESULTS.md) is `no_bidirectional_transfer_candidate`.

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
The completed job used the source commit above; reporting commits do not change its provenance.

The worker uploads an initial checkpoint, each completed scenario block and a final export
when it can exit cooperatively. Local trial commits are atomic; after a provider kill the
last uploaded checkpoint remains available. Resuming is a separately approved job, not an
automatic retry. A technical failure stops execution and retains available scores and errors.

## Completion and immutable evidence

The provider reports **COMPLETED**. The final archive was downloaded at private dataset
revision `69e255415d2ad29036f216c3428bcb7688ddd3c3`, with SHA256
`017e6e0f78e6ae793fbdb5a7ca3a2e4055750c840cc2da2553819fafb0304207`.
It is preserved unchanged as `review/evidence/qwen-patch-3bd8fc27cbb147c9.tar.gz`
(45,093,102 bytes; 2,098 verified payload hashes). The manifest's internal run ID is
`qwen-68dd86357ea64825`; the HF folder name above is a separate dispatch identifier.

The full-snapshot downloader hit HF's HTTP 429 limit while downloading separate activation
files. The complete archive had already arrived, matched its export receipt and pinned
download metadata, and passed its full checksum inventory. A separate local extraction was
used for verification. No GPU restart, new paid job or altered archive was needed.

Runtime was 4,689.73 seconds (78.16 minutes), with 15,475,621,376 bytes peak allocated GPU
memory. The quoted compute bound above is retained; actual billing has not been inspected.

- [Completion and retrieval provenance](../review/qwen-role-patch-completion.json).
- [Independent saved-output audit](../review/qwen-role-patch-audit.json).
- [Frozen analysis, tokenizer, tensor and journal verification](../review/qwen-role-patch-verification.json).
- [Interpreted results](QWEN_ROLE_PATCH_RESULTS.md) and [complete exported report](QWEN_ROLE_PATCH_FULL_REPORT.md).

From either computer, the checked-in archive can now be audited without HF credentials:

```bash
uv run --no-sync python scripts/review_patch_evidence.py
```

## Completed inspection

1. Coverage: 11,264 scientific trials and 32 technical repeats, with errors visible.
2. Historical baseline parity, own-state/repeat parity, candidate mappings and BF16 edit norms.
3. The sole primary contrast C, both transfer directions, eight scenario effects and controls.
4. Generated report, complete prespecified example, article section and SVG/PDF/PNG figures.

No inference about transfer is justified from job status alone. An incomplete or technically
invalid run cannot pass the frozen decision. The original capability-screen failure remains
unchanged, and this exploratory intervention cannot establish consciousness or human illusionism.
