# First Hugging Face Jobs pilot

Completed and independently checked on 2026-11-06. Execution migrated to HF Jobs; the experiment stayed at `context-self-harness-v1` with the unchanged `configs/harness-baseline.json`.

- [Provider job](https://huggingface.co/jobs/zett13/6aedf1390e0338d1bb819399): **COMPLETED**.
- Executed Git commit: `c0ae5521d5bbdcb63e46dcaec615e8add95f10be`.
- [Private artifact snapshot](https://huggingface.co/datasets/zett13/mechinterp-illusionism-results/tree/43c37ecd507a954629cd508b72a8bc08a95f1fb1/harness-cd3646dae2964bbc): run data, report, figures and archive. Access requires the owner's HF account or an authorized token.
- Archive SHA-256: `cd2efc65d71d9f50605a6d2cb57693d189e7778cc6f59a888d24c93976d5e929`.
- [Unchanged original archive in Git](../review/evidence/harness-cd3646dae2964bbc.tar.gz)
  (631,457 bytes): reviewers with repository access need no HF credentials to inspect it.
- Hardware: one NVIDIA L4; driver `580.178.04`; PyTorch `2.15.0+cu132`; BF16, eager attention, FP32 likelihood softmax.
- Harness invocation: **444.92 seconds**, including model loading and checkpoint uploads, excluding environment installation and final export. Peak allocated GPU memory: **6.92 GiB**.
- Coverage: **24/24 scenario blocks, 768/768 variants**, no recorded execution errors. Eight independent scenarios per family; paired variants are not independent observations.

## Result

| Family | Self | Other | Combined | Both factual counterfactuals correct |
|---|---:|---:|---:|---:|
| Action ownership | 47.66% | 39.06% | 43.36% | 2.34% |
| Information access | 53.12% | 48.44% | 50.78% | 7.03% |
| Capability change | 49.22% | 33.59% | 41.41% | 4.69% |

All families fail the 80% development capability screen. The fixed four-shot, full-continuation harness protocol did not establish reliable performance on these contextual tasks. This ends the current functional pilot; no intervention sweep or held-out evaluation follows. A new model or task protocol would be a separate scientific decision.

The comparison with the historical zero-shot run does not isolate a whitespace, demonstration or hardware effect. These results make no claim about consciousness or functional dissociation.

### Follow-up review: possible cross-episode interference

The four demonstrations (indices 36–39) reuse the same four actor-name pairs as evaluation
indices 0–7. This is a plausible interference confound, **not an established root cause**.
An audit of the saved prompts found zero overlap of complete object identifiers between
demonstrations and scored episodes in each family: identifiers include episode-specific
numbers, such as `silver 66247` versus `cobalt 56263`. Color words and actor names do recur.
No controlled name-renaming ablation or attention-head measurement was performed. The low
paired scores do not by themselves identify the mechanism. The separately registered Qwen
action pilot is zero-shot, so it does not introduce this particular demonstration overlap.

## Verification

The private repository and executed source-bundle checksum were checked. Downloading pinned one immutable artifact commit. Every exported file and the archive matched their SHA-256 checksums, including an independent check of the archive's internal files. Source snapshots matched the executed Git commit; regenerating the development plan reproduced its hash. Local re-analysis audited all native harness samples and exactly reproduced the saved analysis. The PNG figure was visually inspected; SVG and PDF are also present.

The original downloaded directory is under `.hf-jobs/downloads/harness-cd3646dae2964bbc/` on
the private computer and remains git-ignored. Its complete archive is now also tracked in
`review/evidence/`, byte-for-byte identical to the pinned private HF snapshot. Run
`python3 scripts/review_evidence.py` from a fresh checkout to verify the archive and all 95
file checksums, then reproduce the table above from the 768 saved likelihood records.
The helper uses only the Python standard library, performs no inference and changes no files.
See [the review guide](REVIEW_GUIDE.md) for source lineage and the distinction from the new task draft.

The first-job authorization was USD 10. The launcher recorded a two-hour provider timeout and a quoted compute bound of USD 1.613293 at submission; these are controls/estimates, not a final provider invoice. No second job was submitted.
