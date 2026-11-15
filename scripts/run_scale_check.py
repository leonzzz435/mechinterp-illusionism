"""Scale check: evaluate 16-world Query-Reference subset on larger Qwen2.5 models."""

import argparse
import gzip
import json
import os
from collections import defaultdict
from pathlib import Path

import numpy as np
from huggingface_hub import HfApi

from self_model_study.pilot_backend import encode_boundary, render_prompt, select_command
from self_model_study.query_reference import build_inputs


def mean_ci_boot(values, seed=1729, n_boot=5000):
    arr = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(arr), size=(n_boot, len(arr)))
    boots = arr[idx].mean(axis=1)
    return float(arr.mean()), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))


def paired_t_pvalue(values):
    from scipy import stats

    arr = np.asarray(values, dtype=float)
    t_stat, p_val = stats.ttest_1samp(arr, 0.0)
    return float(t_stat), float(p_val)


def other_current_cmd(row):
    other_acct = row["other_account"] if row["queried_owner"] == "self" else row["own_account"]
    return row["state"]["permissions"][other_acct][0]


def update_order_label(row):
    events = row.get("events") or []
    if len(events) >= 2:
        return "target_first" if events[0]["actor"] == row["own_account"] else "target_last"
    return None


def summarize_records(records):
    by_cell = defaultdict(list)
    by_world = defaultdict(lambda: defaultdict(list))
    for r in records:
        key = (r["stage"], r["queried_owner"], r["query_form"])
        by_cell[key].append(r)
        by_world[r["world_index"]][key].append(r)

    cells = {}
    for (stage, owner, form), rows in sorted(by_cell.items()):
        acc = sum(1 for x in rows if x["correct"]) / len(rows)
        margin = sum(x["margin"] for x in rows) / len(rows)
        cells[f"{stage}|{owner}|{form}"] = {
            "n": len(rows),
            "correct": sum(1 for x in rows if x["correct"]),
            "accuracy": acc,
            "mean_margin": margin,
        }

    worlds = sorted(by_world.keys())
    e_vals, f_vals, s_vals, h_self_poss, h_other_poss, i_poss = [], [], [], [], [], []
    for w in worlds:
        def wacc(stage, owner, form, world=w):
            rs = by_world[world][(stage, owner, form)]
            return sum(1 for x in rs if x["correct"]) / len(rs)

        e = wacc("after_both", "self", "account_name") - wacc("after_both", "self", "possessive")
        f_other = wacc("after_both", "other", "account_name") - wacc(
            "after_both", "other", "possessive"
        )
        f = e - f_other
        s_self = wacc("after_both", "self", "owner_name") - wacc(
            "after_both", "self", "possessive"
        )
        s_other = wacc("after_both", "other", "owner_name") - wacc(
            "after_both", "other", "possessive"
        )
        s = s_self - s_other
        hs = wacc("after_both", "self", "possessive") - wacc("snapshot", "self", "possessive")
        ho = wacc("after_both", "other", "possessive") - wacc("snapshot", "other", "possessive")
        e_vals.append(e * 100.0)
        f_vals.append(f * 100.0)
        s_vals.append(s * 100.0)
        h_self_poss.append(hs * 100.0)
        h_other_poss.append(ho * 100.0)
        i_poss.append((hs - ho) * 100.0)

    contrasts = {}
    for name, vals in [
        ("E_pp", e_vals),
        ("F_pp", f_vals),
        ("S_pp", s_vals),
        ("H_self_poss_pp", h_self_poss),
        ("H_other_poss_pp", h_other_poss),
        ("I_poss_pp", i_poss),
    ]:
        m, lo, hi = mean_ci_boot(vals)
        t_stat, p_val = paired_t_pvalue(vals)
        contrasts[name] = {
            "mean": m,
            "ci95": [lo, hi],
            "t_stat": t_stat,
            "p_value": p_val,
            "n_worlds": len(worlds),
        }

    order_split = {}
    for order in ("target_first", "target_last"):
        sub = [
            r
            for r in records
            if r["stage"] == "after_both"
            and r["queried_owner"] == "self"
            and r["query_form"] == "possessive"
            and r.get("update_order") == order
        ]
        if sub:
            order_split[order] = {
                "n": len(sub),
                "correct": sum(1 for x in sub if x["correct"]),
                "accuracy": sum(1 for x in sub if x["correct"]) / len(sub),
            }

    return {"cells": cells, "contrasts": contrasts, "order_split": order_split}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--world-count", type=int, default=16)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--hf-repo", default="")
    parser.add_argument("--hf-prefix", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    _, rows = build_inputs()
    subset = [r for r in rows if r["world_index"] < args.world_count]
    print(f"Loaded {len(subset)} trials across {args.world_count} worlds for {args.model}")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        fake = [
            {
                "id": r["id"],
                "world_index": r["world_index"],
                "stage": r["stage"],
                "queried_owner": r["queried_owner"],
                "query_form": r["query_form"],
                "update_order": update_order_label(r),
                "correct": True,
                "margin": 1.0,
            }
            for r in subset
        ]
        summary_test = summarize_records(fake)
        payload = {
            "model": args.model,
            "trials": len(subset),
            "worlds": args.world_count,
            "sample_other_cmd": other_current_cmd(subset[0]),
            "contrasts_keys": sorted(summary_test["contrasts"].keys()),
        }
        (out_dir / "dry_run.json").write_text(json.dumps(payload, indent=2))
        return

    import torch
    from lm_eval.models.huggingface import HFLM
    from transformers import AutoTokenizer

    torch.backends.cuda.matmul.allow_tf32 = False
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=False)
    lm = HFLM(
        pretrained=args.model,
        tokenizer=tokenizer,
        device="cuda",
        dtype="bfloat16",
        softmax_dtype="float32",
        batch_size=args.batch_size,
        add_bos_token=False,
        max_length=2048,
        truncation=False,
        trust_remote_code=False,
        parallelize=False,
        attn_implementation="sdpa",
    )
    lm.model.eval()

    records = []
    for start in range(0, len(subset), 64):
        chunk = subset[start : start + 64]
        requests, meta = [], []
        for row in chunk:
            rendered = render_prompt(tokenizer, row["prompt"], "chat")
            pairs = [encode_boundary(tokenizer, rendered, c, 2048) for c in row["choices"]]
            meta.append((row, len(pairs)))
            for ctx, cont in pairs:
                requests.append((None, ctx, cont))
        native = lm._loglikelihood_tokens(requests, disable_tqdm=True)
        offset = 0
        for row, k in meta:
            scores = [float(native[offset + i][0]) for i in range(k)]
            offset += k
            selected, status = select_command(row["choices"], scores)
            if status == "tie":
                selected = row["choices"][scores.index(max(scores))]
            score_map = dict(zip(row["choices"], scores))
            correct_cmd = row["expected_command"]
            other_cmd = other_current_cmd(row)
            margin = float(score_map[correct_cmd] - score_map[other_cmd])
            records.append(
                {
                    "id": row["id"],
                    "world_index": row["world_index"],
                    "stage": row["stage"],
                    "queried_owner": row["queried_owner"],
                    "query_form": row["query_form"],
                    "update_order": update_order_label(row),
                    "correct": selected == correct_cmd,
                    "selected": selected,
                    "expected_command": correct_cmd,
                    "other_current_command": other_cmd,
                    "margin": margin,
                    "status": status,
                }
            )
        print(f"Progress: {len(records)}/{len(subset)} trials scored", flush=True)

    summary = {
        "model": args.model,
        "world_count": args.world_count,
        "total_trials": len(records),
        "gpu": torch.cuda.get_device_name(0),
        **summarize_records(records),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with gzip.open(out_dir / "records.jsonl.gz", "wt") as gz:
        for r in records:
            gz.write(json.dumps(r) + "\n")

    print("SUMMARY:", json.dumps(summary["contrasts"], indent=2), flush=True)

    if args.hf_repo and args.hf_prefix:
        os.environ["HF_HUB_DISABLE_XET"] = "1"
        api = HfApi()
        api.create_repo(args.hf_repo, repo_type="dataset", private=True, exist_ok=True)
        for fname in ("summary.json", "records.jsonl.gz"):
            api.upload_file(
                path_or_fileobj=out_dir / fname,
                path_in_repo=f"{args.hf_prefix}/{fname}",
                repo_id=args.hf_repo,
                repo_type="dataset",
                commit_message=f"Upload {args.hf_prefix}/{fname}",
            )


if __name__ == "__main__":
    main()
