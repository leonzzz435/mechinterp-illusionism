# The Fragile Self-Pointer: Mechanistic Interpretability & Illusionism in LLMs

[![Tests](https://img.shields.io/badge/pytest-292%20passed-brightgreen)](tests/)
[![Evaluations](https://img.shields.io/badge/evaluations-92%2C700%2B-blue)](docs/ARTICLE.md)
[![Models](https://img.shields.io/badge/models-Qwen2.5%20%7C%20Gemma--2-orange)](configs/)
[![Python](https://img.shields.io/badge/python-3.12%2B-3776AB)](pyproject.toml)
[![Managed with uv](https://img.shields.io/badge/uv-reproducible-purple)](uv.lock)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Large language models generate fluent first-person self-language (*"I"*, *"my"*, *"your active account"*), yet lack a stable internal self-model. Inspired by philosophical **illusionism** (Dennett, 1991; Frankish, 2016), this repository formalizes and tests the decoupling between superficial self-language ($L_{\text{self}}$) and functional state-tracking ($M_{\text{self}}$) across **14 experimental runs and over 92,700 controlled evaluations** (`67,574` core decisions plus `25,000+` follow-up scaling, multi-span patching, and 28-layer probe evaluations), residual-stream **activation exchange**, and **Sparse Autoencoder (SAE)** interventions in `Qwen/Qwen2.5-7B/14B/32B-Instruct` and `unsloth/gemma-2-2b`.

> **Where to start:**
> - **For Engineers & Product Builders:** Read the accessible essay [**Your AI Has No "Self"—Just a Fragile User Interface**](https://medium.com/@leon_zajchowski/your-ai-has-no-self-just-a-fragile-user-interface-365dad5daf8c) (or [`docs/MEDIUM_ARTICLE.md`](docs/MEDIUM_ARTICLE.md)).
> - **For ML Researchers:** Read the full mathematical paper with LaTeX derivations and Holm-Bonferroni tables in [**`docs/ARTICLE.md`**](docs/ARTICLE.md).

![Multi-Span and Multi-Layer Causal Patching Circuit](assets/followup/qwen_multispan_circuit.png)

## Key Empirical Findings

| Experiment | Model | $N$ | Core Result |
|---|---|---:|---|
| **Query-Reference Indirection** | `Qwen2.5-7B-Instruct` | 16,128 | Account Name `95.18%` (`+7.66 nats`) → Operator `71.35%` → `"your"` `60.16%` (`+1.09 nats`); **$E = +35.03\text{ pp}$** ($p_{\text{Holm}} = 1.58 \times 10^{-24}$) |
| **Paired Update-History Cost** | `Qwen2.5-7B-Instruct` | 16,128 | Identical final state: `"your"` drops **$-11.91\text{ pp}$** after update histories vs. $+0.85\text{ pp}$ for `"their"` (DiD $-12.76\text{ pp}$); `96.57%` errors route to foreign-current |
| **Role-Framing Interaction** | `Qwen2.5-7B-Instruct` | 2,048 | Active self-role vs. detached reference induces **$+16.41\text{ pp}$** error gap (exact sign-flip $p = 0.015625$, `7/8` scenarios) |
| **Your / The Single-Token Swap** | `Qwen2.5-7B-Instruct` | 6,144 | Single token `your` ↔ `the` shifts choice log-likelihood margin by **$+0.346\text{ nats}$** ($-0.398\text{ nats}$ after irrelevant updates) |
| **Layer-14 Activation Exchange** | `Qwen2.5-7B-Instruct` | 11,264 | Patching `Active → Reference` transfers error gap ($+5.47\text{ pp}$, **$+2.063\text{ nats}$**); `Reference → Active` fails ($-0.78\text{ pp}$), exposing distributed asymmetric routing |
| **Irrelevant-Update Collapse** | `Qwen2.5-7B-Instruct` | 18,432 | Updating a bystander collapses target accuracy to `34.51%–53.91%`; `2,442/2,443` (`99.96%`) errors adopt the foreign grant |
| **Confidence & Abstention (v2)** | `Qwen2.5-7B-Instruct` | 1,792 | Blind confidence: abstention gap $-1.37\text{ pp}$, verbal AUROC `0.5444`, CV log-loss gain $-0.00155$ |
| **Layer-14 SAE Orthogonality** | `Gemma-2-2B` | 8,694 | Self-monitoring (`#2728`) and `"I"`-agency (`#10230`) are near-orthogonal ($\cos = 0.06121$); `#10230` ablation shifts 1st-person rate (`-1.05/100w`) with `0.0` functional impact |
| **Scaling Capacity Curve** *(Follow-Up)* | `Qwen2.5-14B` / `32B` | 10,752 | `14B`: `"your"` `97.46%` ($E = +2.34\text{ pp}$, $p = 0.0285$); `32B`: `99.61%` (`2` errors in `target_last`) with monotonic margin decay (`+24.32 → +22.62 → +21.86 nats`) |
| **Multi-Span Circuit Sweep** *(Follow-Up)* | `Qwen2.5-7B-Instruct` | 256 pairs × 7L | Full `header_span` achieves bidirectional rescue at Block 12 (`83.59%`, $T_{\text{R}\to\text{A}} = +10.16\text{ pp}$, $p = 0.0312$) and hands off to `query_span` at Block 18 |
| **28-Layer Subspace Geometry** *(Follow-Up)* | `Qwen2.5-7B-Instruct` | 28 blocks | $M_{\text{self}}$ 5-fold CV AUROC jumps at Blocks `18–20` (peaking at `0.764`), while $\cos(v_{L_{\text{self}}}, v_{M_{\text{self}}}) = +0.051$ confirms direct single-model orthogonality |

## Quickstart (`uv`)

```bash
uv sync --locked --extra gpu --extra eval  # Sync full environment (omit extras for CPU-only analysis)
uv run pytest -q                           # Run full unit & evidence-verification test suite
uv run self-study validate configs/smoke.json
uv run self-study run configs/smoke.json --out runs/smoke
uv run self-study analyze runs/baseline
```

## Repository Structure

- **Main Paper & Formalism:** [`docs/ARTICLE.md`](docs/ARTICLE.md), [`docs/METHODS.md`](docs/METHODS.md), [`docs/PROTOCOL.md`](docs/PROTOCOL.md)
- **Empirical Run Reports:** [`docs/reports/QUERY_REFERENCE_RESULTS.md`](docs/reports/QUERY_REFERENCE_RESULTS.md), [`docs/reports/QWEN_ROLE_RESULTS.md`](docs/reports/QWEN_ROLE_RESULTS.md), [`docs/reports/QWEN_ROLE_PATCH_RESULTS.md`](docs/reports/QWEN_ROLE_PATCH_RESULTS.md), [`docs/reports/QWEN_POSSESSIVE_RESULTS.md`](docs/reports/QWEN_POSSESSIVE_RESULTS.md), [`docs/reports/QWEN_CONFIDENCE_RESULTS.md`](docs/reports/QWEN_CONFIDENCE_RESULTS.md), [`docs/reports/QWEN_OWNERSHIP_RESULTS.md`](docs/reports/QWEN_OWNERSHIP_RESULTS.md)
- **Core Library:** [`src/self_model_study/`](src/self_model_study/) (backends, SAE/residual hooks, exact permutation & bootstrap analysis)
- **Configs & Experimental Designs:** [`configs/`](configs/), [`designs/`](designs/)
- **Verified Data, Plots & Runs:** [`review/`](review/), [`assets/`](assets/), [`runs/`](runs/)
- **Archived Drafts, Runbooks & Legacy:** [`docs/archive/`](docs/archive/)
