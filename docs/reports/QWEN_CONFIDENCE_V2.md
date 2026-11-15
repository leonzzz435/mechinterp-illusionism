# Confidence pilot v2: deterministic ties, before assessment exposure

**Amendment on 2026-11-08, after a calibration-only v1 failure.** The first job stopped
at selection 32: two digits shared the highest log-likelihood exactly
(`−0.6943995356559753`). The v1 rule required a unique maximum and therefore stopped as
specified. This exposed an unnecessarily brittle measurement policy, not a GPU loading
failure or a finding about self-evaluation. No assessment question was presented.

The v1 run, configuration and [raw archive](../review/evidence/qwen-confidence-3ec0b47c7d324b58.tar.gz)
remain unchanged. There are 31 valid calibration selections, one retained tie, and zero
assessment selections. The new version is a fresh run, not a relabeling or continuation of
those records. Calibration is recomputed entirely within v2.

## One decision-policy amendment

For a menu of single-token candidates, use

\[
j^*=\mathop{\arg\min}_{j\in\operatorname{argmax}_k\ell_k}\operatorname{tokenID}(j).
\]

This follows the vocabulary-order convention of greedy argmax: PyTorch chooses the first
maximum index when maxima tie ([official argmax documentation](https://docs.pytorch.org/docs/2.15/generated/torch.argmax.html)).
It applies to the restricted menu, not unrestricted text generation. In the observed v1
case, digit 2 wins under this convention; the native harness also marked that digit as
greedy. Neither of the tied digits was the reference answer in this example.

Every v2 record retains `score_tie`, the full list of tied commands, the original scorer
status, selected token ID and all unmodified likelihoods. A tie is an observable model
decision under a fixed policy, not a missing answer. Nonfinite scores, boundary mismatches,
missing parents and other technical errors still stop the run. **Near ties are not rounded
into ties**: the selection rule uses exact score equality.

Model/checkpoint, BF16, prompts, sample IDs, rotations, scoring, temperature calibration,
primary S, grouped bootstrap, feasibility requirements and candidate rule are unchanged.
The 128 assessment questions remain unexposed at this amendment. The primary question is
still whether selective answering tracks forced-answer errors; this is not a prompt search.

## Additional descriptive transparency

Report tie counts by split and stage. Also recompute S and verbal-confidence AUROC after
excluding **whole assessment questions** with any tie in any rotation/stage, with the same
question-bootstrap method and seed. Report how many questions remain; zero remaining means
undefined. This selection-sensitive description does not replace the full-data primary or
create another route to a positive candidate.

A separate portability fix permits absolute error up to 1e−12 when rechecking already
stored derived menu masses/probabilities on another CPU environment. Reading v1 revealed
last-bit differences in those recomputations. Raw scores, chosen digits, correctness,
dependency checksums and exact-tie detection remain exact. The original archive is not
rewritten. Regression tests accept roundoff and reject changed decisions or 1e−6 changes.

## Version and bounded execution

- [Configuration](../configs/qwen-confidence-pilot-v2.json): `qwen-confidence-pilot-v2`,
  engine `qwen-confidence-v2`; separate journal, receipt and archive prefix.
- Plan SHA256: `c6b66f80b92502b237bd3734dfbbc970cf367dfd5b0c72473e6e2bf365bc6e90`.
- Token fingerprint: `23e67a671d6c1e88ea581cc99340d23590f90569c274d973e6d1cd61e60dd83c`,
  identical to the original design; 1,792 selections and 24 upload blocks.
- User authorization covers implementation and the bounded pilot. One reviewed replacement
  job uses the remaining allocation inside the **same USD 5 total cap**. Reserving the
  entire v1 compute bound leaves USD 3.386707; the v2 two-hour quote is USD 1.613293.
  Both worst-case compute bounds sum to USD 3.226586. No third job or automatic retry follows.

```bash
uv run --no-sync self-study validate configs/qwen-confidence-pilot-v2.json --tokenizer-check
uv run --script scripts/hf_jobs.py submit --namespace zett13 --budget-usd 3.386707 \
  --config configs/qwen-confidence-pilot-v2.json
uv run --script scripts/hf_jobs.py status --receipt .hf-jobs/qwen-confidence-pilot-v2.json
uv run --script scripts/hf_jobs.py fetch --receipt .hf-jobs/qwen-confidence-pilot-v2.json
```

The command is documented for the single reviewed replacement; an existing receipt prevents
duplicates. Actual dispatch and final status belong in the [execution record](QWEN_CONFIDENCE_RUN.md).
