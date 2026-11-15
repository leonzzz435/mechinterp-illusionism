# The Fragile Self-Pointer: Mechanistic Interpretability & Illusionism in LLMs

Large language models generate fluent first-person self-language (*"I"*, *"my"*, *"your active account"*), yet lack a stable internal self-model. Inspired by philosophical **illusionism** (Dennett, 1991; Frankish, 2016), this repository formalizes and tests the decoupling between superficial self-language ($L_{\text{self}}$) and functional state-tracking ($M_{\text{self}}$) across **67,574 controlled evaluations**, residual-stream **activation exchange**, and **Sparse Autoencoder (SAE)** interventions in `Qwen/Qwen2.5-7B-Instruct` and `unsloth/gemma-2-2b`.

👉 **[Read the Full Paper (`docs/ARTICLE.md`)](docs/ARTICLE.md)** · **[Accessible Overview (`docs/MEDIUM_ARTICLE.md`)](docs/MEDIUM_ARTICLE.md)**

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

## Quickstart (`uv`)

```bash
uv sync --locked --extra gpu --extra eval  # Sync full environment (omit extras for CPU-only analysis)
uv run pytest -q                           # Run full unit & evidence-verification test suite
uv run self-study validate configs/smoke.json
uv run self-study run configs/smoke.json --out runs/smoke
uv run self-study analyze runs/baseline
```

## Repository Structure

- **Main Paper & Formalism:** [`docs/ARTICLE.md`](docs/ARTICLE.md), [`docs/article-v2/METHODS.md`](docs/article-v2/METHODS.md), [`docs/PROTOCOL.md`](docs/PROTOCOL.md)
- **Empirical Run Reports:** [`docs/QUERY_REFERENCE_RESULTS.md`](docs/QUERY_REFERENCE_RESULTS.md), [`docs/QWEN_ROLE_RESULTS.md`](docs/QWEN_ROLE_RESULTS.md), [`docs/QWEN_ROLE_PATCH_RESULTS.md`](docs/QWEN_ROLE_PATCH_RESULTS.md), [`docs/QWEN_POSSESSIVE_RESULTS.md`](docs/QWEN_POSSESSIVE_RESULTS.md), [`docs/QWEN_CONFIDENCE_RESULTS.md`](docs/QWEN_CONFIDENCE_RESULTS.md), [`docs/QWEN_OWNERSHIP_RESULTS.md`](docs/QWEN_OWNERSHIP_RESULTS.md)
- **Core Library:** [`src/self_model_study/`](src/self_model_study/) (backends, SAE/residual hooks, exact permutation & bootstrap analysis)
- **Configs & Experimental Designs:** [`configs/`](configs/), [`designs/`](designs/)
- **Verified Data, Plots & Archives:** [`review/`](review/), [`assets/`](assets/), [`runs/`](runs/), [`archive/`](archive/)
- **Archived Runbooks & Governance:** [`docs/archive/`](docs/archive/)
