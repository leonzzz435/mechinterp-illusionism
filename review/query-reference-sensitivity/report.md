# Retrospective query-reference sensitivity

**Exploratory, after outcome inspection.**
Frozen v1 remains `incomplete_or_invalid_no_inference`; no original record changed.

Post hoc policy and outcome-dependent world exclusion; all variants retained. Nominal paired-world intervals, 10000 draws seed 1729; t df=n-1; Holm E/F/S within each variant only, not across sensitivity analyses or policy selection. No confirmatory candidate, functional dissociation or human-illusionism claim.

## All analyses, no significance-based selection

| Analysis | Contrast | pp | Nominal 95% interval (pp) | Raw p | Holm p |
|---|---|---:|---|---:|---:|
| Frozen v1 (48) | E | 35.0260 | withheld | undefined | placeholder only |
| Frozen v1 (48) | F | 35.0260 | withheld | undefined | placeholder only |
| Frozen v1 (48) | S | 10.0911 | withheld | undefined | placeholder only |
| 47 worlds; exclude 0011 | E | 35.5718 | [32.3138, 38.7633] | 1.47075e-25 | 4.41224e-25 |
| 47 worlds; exclude 0011 | F | 35.3059 | [31.5808, 39.0293] | 8.6071e-23 | 1.72142e-22 |
| 47 worlds; exclude 0011 | S | 10.3723 | [6.1170, 14.6293] | 2.38721e-05 | 2.38721e-05 |
| 48 worlds; stored-greedy v2 | E | 35.0260 | [31.6406, 38.2161] | 5.25432e-25 | 1.5763e-24 |
| 48 worlds; stored-greedy v2 | F | 34.9609 | [31.2500, 38.6068] | 5.67335e-23 | 1.13467e-22 |
| 48 worlds; stored-greedy v2 | S | 10.0260 | [5.7292, 14.1927] | 3.39913e-05 | 3.39913e-05 |
| 48 worlds; other tied command | E | 35.0911 | [31.7708, 38.2812] | 2.98486e-25 | 8.95459e-25 |
| 48 worlds; other tied command | F | 35.0260 | [31.3802, 38.6719] | 4.17176e-23 | 8.34352e-23 |
| 48 worlds; other tied command | S | 10.0911 | [5.8594, 14.2578] | 2.88528e-05 | 2.88528e-05 |

The intervals and p-values above are exploratory. No v1 inference is restored.
Both full-sample assignments keep the lookup decision `lookup_gate_failed`.

## Original error counts (before tie resolution)

| Owner / form | Errors | Foreign current | Revoked target | Revoked other | Tie/invalid |
|---|---:|---:|---:|---:|---:|
| other/account_name | 58 | 42 | 16 | 0 | 0 |
| other/owner_name | 381 | 367 | 14 | 0 | 0 |
| other/possessive | 441 | 440 | 1 | 0 | 0 |
| self/account_name | 74 | 53 | 21 | 0 | 0 |
| self/owner_name | 440 | 315 | 101 | 24 | 0 |
| self/possessive | 612 | 591 | 14 | 6 | 1 |

## Original choices versus the declared shortcut

| Owner / form | Scheduled | Latest-grant baseline correct | Latest agreement | First-grant agreement | Unresolved |
|---|---:|---:|---:|---:|---:|
| other/account_name | 1536 | 768 | 731 | 789 | 0 |
| other/owner_name | 1536 | 768 | 540 | 982 | 0 |
| other/possessive | 1536 | 768 | 632 | 903 | 0 |
| self/account_name | 1536 | 768 | 707 | 808 | 0 |
| self/owner_name | 1536 | 768 | 611 | 800 | 0 |
| self/possessive | 1536 | 768 | 451 | 1064 | 1 |

Agreement counts and the first-grant comparator are retrospective descriptions, not internal mechanisms.

Reproduce: `uv run --no-sync python scripts/analyze_query_sensitivity.py`
