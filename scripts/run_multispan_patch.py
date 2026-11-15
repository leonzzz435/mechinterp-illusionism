"""Experiment 1: Multi-span & multi-layer causal activation exchange in Qwen2.5-7B-Instruct."""

import argparse
import gzip
import json
import os
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

import numpy as np
from huggingface_hub import HfApi

from self_model_study import role_control
from self_model_study.pilot_backend import encode_boundary, render_prompt, select_command


def exact_sign_flip_p(diffs):
    arr = np.asarray(diffs, dtype=float)
    nz = arr[np.abs(arr) > 1e-12]
    m = len(nz)
    if m == 0:
        return 1.0
    obs = abs(arr.mean())
    n = len(arr)
    count = 0
    for mask in range(1 << m):
        signs = np.array([1.0 if (mask >> i) & 1 else -1.0 for i in range(m)])
        if abs((nz * signs).sum() / n) >= obs - 1e-12:
            count += 1
    return count / (1 << m)


def other_current_cmd(row):
    perms = row["state"]["permissions"]
    other_actors = [a for a, cmds in perms.items() if cmds[0] != row["expected_command"]]
    if len(other_actors) == 1:
        return perms[other_actors[0]][0]
    other_actor = [a for a in perms if a != row["target"]][0]
    return perms[other_actor][0]


def find_spans(tokenizer, ctx_a, ctx_r):
    assert len(ctx_a) == len(ctx_r) + 1
    assert ctx_a[63:] == ctx_r[62:]
    sel_id = tokenizer.encode("Select", add_special_tokens=False)[0]
    avail_id = tokenizer.encode("Available", add_special_tokens=False)[0]
    q_r = ctx_r.index(sel_id, 62)
    q_a = ctx_a.index(sel_id, 63)
    e_r = ctx_r.index(avail_id, q_r)
    e_a = ctx_a.index(avail_id, q_a)
    assert ctx_a[q_a:e_a] == ctx_r[q_r:e_r]
    return {
        "active": {
            "header_end": [62],
            "header_span": list(range(58, 63)),
            "query_span": list(range(q_a, e_a)),
            "joint_span": list(range(58, 63)) + list(range(q_a, e_a)),
        },
        "reference": {
            "header_end": [61],
            "header_span": list(range(57, 62)),
            "query_span": list(range(q_r, e_r)),
            "joint_span": list(range(57, 62)) + list(range(q_r, e_r)),
        },
    }


@contextmanager
def capture_layers(model, layers, positions):
    captured = {}
    handles = []

    def make_hook(layer_idx):
        def hook(_module, _args, output):
            captured[layer_idx] = output[0, positions].detach().cpu().clone()
            return output

        return hook

    for layer_idx in layers:
        handles.append(model.model.layers[layer_idx].register_forward_hook(make_hook(layer_idx)))
    try:
        yield captured
    finally:
        for h in handles:
            h.remove()


@contextmanager
def patch_positions(model, layer, recip_pos, donor_vec, random_dirs=None, own_vec=None):
    import torch

    def hook(_module, _args, output):
        res = output.clone()
        if random_dirs is None:
            d = donor_vec.to(device=output.device, dtype=output.dtype)
            res[:, recip_pos, :] = d.unsqueeze(0)
        else:
            o = own_vec.to(device=output.device, dtype=torch.float32)
            d = donor_vec.to(device=output.device, dtype=torch.float32)
            delta_norms = (d - o).norm(dim=-1, keepdim=True)
            u = random_dirs.to(device=output.device, dtype=torch.float32)
            rep = (o + delta_norms * u).to(output.dtype)
            res[:, recip_pos, :] = rep.unsqueeze(0)
        return res

    handle = model.model.layers[layer].register_forward_hook(hook)
    try:
        yield
    finally:
        handle.remove()


def score_four_candidates(model, pad_id, ctx, cont_list):
    import torch
    import torch.nn.functional as F

    max_len = max(len(ctx) + len(c) for c in cont_list)
    input_ids = torch.full((len(cont_list), max_len), pad_id, dtype=torch.long, device=model.device)
    attn_mask = torch.zeros((len(cont_list), max_len), dtype=torch.long, device=model.device)
    for i, cont in enumerate(cont_list):
        seq = ctx + cont
        input_ids[i, : len(seq)] = torch.tensor(seq, dtype=torch.long, device=model.device)
        attn_mask[i, : len(seq)] = 1

    with torch.inference_mode():
        logits = model(input_ids=input_ids, attention_mask=attn_mask, use_cache=False).logits

    scores = []
    ctx_len = len(ctx)
    for i, cont in enumerate(cont_list):
        step_logits = logits[i, ctx_len - 1 : ctx_len - 1 + len(cont), :].float()
        log_probs = F.log_softmax(step_logits, dim=-1)
        tok_ids = torch.tensor(cont, dtype=torch.long, device=model.device).unsqueeze(-1)
        tok_ll = log_probs.gather(-1, tok_ids).squeeze(-1).sum().item()
        scores.append(float(tok_ll))
    return scores


def eval_choice_record(condition, scenario, scene_id, frame, relation, row, scores):
    sel, status = select_command(row["choices"], scores)
    if status == "tie":
        sel = row["choices"][scores.index(max(scores))]
    smap = dict(zip(row["choices"], scores))
    other_cmd = other_current_cmd(row)
    return {
        "condition": condition,
        "scenario": scenario,
        "scene_id": scene_id,
        "frame": frame,
        "relation": relation,
        "correct": sel == row["expected_command"],
        "margin": float(smap[row["expected_command"]] - smap[other_cmd]),
    }


def summarize_condition(records):
    by_sc = defaultdict(lambda: defaultdict(list))
    for r in records:
        by_sc[r["scenario"]][(r["frame"], r["relation"])].append(r)

    sc_list = sorted(by_sc.keys())
    gaps = {"active": [], "reference": []}
    for sc in sc_list:
        for frame in ("active", "reference"):
            other = by_sc[sc][(frame, "other")]
            target = by_sc[sc][(frame, "target")]
            if other and target:
                acc_o = sum(1 for x in other if x["correct"]) / len(other)
                acc_t = sum(1 for x in target if x["correct"]) / len(target)
                gaps[frame].append((acc_o - acc_t) * 100.0)

    def agg(frame):
        all_o = [r for sc in sc_list for r in by_sc[sc][(frame, "other")]]
        all_t = [r for sc in sc_list for r in by_sc[sc][(frame, "target")]]
        acc_o = sum(1 for x in all_o if x["correct"]) / len(all_o) * 100.0
        acc_t = sum(1 for x in all_t if x["correct"]) / len(all_t) * 100.0
        m_o = sum(x["margin"] for x in all_o) / len(all_o)
        m_t = sum(x["margin"] for x in all_t) / len(all_t)
        return {
            "acc_other": acc_o,
            "acc_target": acc_t,
            "gap_pp": acc_o - acc_t,
            "margin_other": m_o,
            "margin_target": m_t,
            "scenario_gaps": gaps[frame],
        }

    return {"active": agg("active"), "reference": agg("reference")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--revision", default="a09a35458c702b33eeacc393d103063234e8bc28")
    parser.add_argument("--layers", default="3,7,11,13,17,21,25")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--hf-repo", default="")
    parser.add_argument("--hf-prefix", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    layers = [int(x.strip()) for x in args.layers.split(",")]
    plan = role_control.build_plan(role_control.DEFAULT_SPEC)
    pairs = []
    for blk in plan["blocks"]:
        jobs = [j for j in blk["jobs"] if role_control.stratum(j["row"]) == "after_relevant"]
        by_key = {(j["row"]["scene_id"], j["row"]["frame"], j["row"]["relation"]): j for j in jobs}
        for sc in sorted({j["row"]["scene_id"] for j in jobs}):
            for rel in ("target", "other"):
                act_j = by_key[(sc, "active", rel)]
                ref_j = by_key[(sc, "reference", rel)]
                pairs.append((blk["id"], sc, rel, act_j, ref_j))

    print(f"Prepared {len(pairs)} matched Active/Reference pairs across {len(layers)} layers.")
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        sample = pairs[0][3]["row"]
        payload = {
            "pairs": len(pairs),
            "layers": layers,
            "scenario_num": int(sample["scenario_id"].split(":")[-1]),
            "sample_other_cmd": other_current_cmd(sample),
        }
        (out_dir / "dry_run.json").write_text(json.dumps(payload, indent=2))
        return

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.backends.cuda.matmul.allow_tf32 = False
    tok = AutoTokenizer.from_pretrained(args.model, revision=args.revision, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        revision=args.revision,
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        attn_implementation="eager",
        trust_remote_code=False,
    )
    model.eval()
    model.config.use_cache = False
    pad_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    clean_records, pair_cache = [], []
    for idx, (_blk_id, sc, rel, act_job, ref_job) in enumerate(pairs):
        act_row, ref_row = act_job["row"], ref_job["row"]
        sc_num = int(act_row["scenario_id"].split(":")[-1])
        act_rend = render_prompt(tok, act_row["prompt"], "chat")
        ref_rend = render_prompt(tok, ref_row["prompt"], "chat")
        act_pairs = [encode_boundary(tok, act_rend, c, 2048) for c in act_row["choices"]]
        ref_pairs = [encode_boundary(tok, ref_rend, c, 2048) for c in ref_row["choices"]]
        ctx_a, conts_a = act_pairs[0][0], [p[1] for p in act_pairs]
        ctx_r, conts_r = ref_pairs[0][0], [p[1] for p in ref_pairs]
        spans = find_spans(tok, ctx_a, ctx_r)

        with capture_layers(model, layers, spans["active"]["joint_span"]) as cap_a:
            scores_a = score_four_candidates(model, pad_id, ctx_a, conts_a)
        with capture_layers(model, layers, spans["reference"]["joint_span"]) as cap_r:
            scores_r = score_four_candidates(model, pad_id, ctx_r, conts_r)

        clean_records.append(
            eval_choice_record("clean", sc_num, sc, "active", rel, act_row, scores_a)
        )
        clean_records.append(
            eval_choice_record("clean", sc_num, sc, "reference", rel, ref_row, scores_r)
        )
        pair_cache.append(
            {
                "scenario": sc_num,
                "scene_id": sc,
                "relation": rel,
                "act_row": act_row,
                "ref_row": ref_row,
                "ctx_a": ctx_a,
                "conts_a": conts_a,
                "ctx_r": ctx_r,
                "conts_r": conts_r,
                "spans": spans,
                "cap_a": cap_a,
                "cap_r": cap_r,
            }
        )
        if (idx + 1) % 64 == 0:
            print(f"Clean baseline captured: {idx + 1}/{len(pairs)}", flush=True)

    clean_summary = summarize_condition(clean_records)
    act_gap = clean_summary["active"]["gap_pp"]
    ref_gap = clean_summary["reference"]["gap_pp"]
    print(f"Clean gaps -> Active: {act_gap:.2f} pp | Reference: {ref_gap:.2f} pp", flush=True)

    results = {"clean": clean_summary, "sweep": []}
    all_records = list(clean_records)

    def pair_slice(spans, span_name):
        h_len = len(spans["active"]["header_span"])
        j_len = len(spans["active"]["joint_span"])
        if span_name == "header_end":
            return [h_len - 1]
        if span_name == "header_span":
            return list(range(0, h_len))
        if span_name == "query_span":
            return list(range(h_len, j_len))
        return list(range(0, j_len))

    for layer in layers:
        if layer == 13:
            span_names = ["header_end", "header_span", "query_span", "joint_span"]
        else:
            span_names = ["header_span", "query_span", "joint_span"]
        for span_name in span_names:
            cond_name = f"L{layer}_{span_name}"
            cond_records = []
            for p in pair_cache:
                sl = pair_slice(p["spans"], span_name)
                with patch_positions(
                    model, layer, p["spans"]["reference"][span_name], p["cap_a"][layer][sl]
                ):
                    sc_r = score_four_candidates(model, pad_id, p["ctx_r"], p["conts_r"])
                cond_records.append(
                    eval_choice_record(
                        cond_name, p["scenario"], p["scene_id"], "reference",
                        p["relation"], p["ref_row"], sc_r,
                    )
                )
                with patch_positions(
                    model, layer, p["spans"]["active"][span_name], p["cap_r"][layer][sl]
                ):
                    sc_a = score_four_candidates(model, pad_id, p["ctx_a"], p["conts_a"])
                cond_records.append(
                    eval_choice_record(
                        cond_name, p["scenario"], p["scene_id"], "active",
                        p["relation"], p["act_row"], sc_a,
                    )
                )

            all_records.extend(cond_records)
            csum = summarize_condition(cond_records)
            t_a2r = csum["reference"]["gap_pp"] - ref_gap
            t_r2a = act_gap - csum["active"]["gap_pp"]
            p_a2r = exact_sign_flip_p(
                np.array(csum["reference"]["scenario_gaps"])
                - np.array(clean_summary["reference"]["scenario_gaps"])
            )
            p_r2a = exact_sign_flip_p(
                np.array(clean_summary["active"]["scenario_gaps"])
                - np.array(csum["active"]["scenario_gaps"])
            )
            entry = {
                "layer": layer,
                "block": layer + 1,
                "span": span_name,
                "T_A2R_pp": t_a2r,
                "p_A2R": p_a2r,
                "T_R2A_pp": t_r2a,
                "p_R2A": p_r2a,
                "D_ref_swap_pp": csum["reference"]["gap_pp"],
                "D_act_swap_pp": csum["active"]["gap_pp"],
                "ref_target_acc": csum["reference"]["acc_target"],
                "act_target_acc": csum["active"]["acc_target"],
            }
            results["sweep"].append(entry)
            print(
                f"Block {layer+1:2d} | {span_name:11s} | T_A->R={t_a2r:+6.2f} (p={p_a2r:.4f}) "
                f"| T_R->A={t_r2a:+6.2f} (p={p_r2a:.4f}) | ActTgt={entry['act_target_acc']:.2f}%",
                flush=True,
            )

    rng = torch.Generator().manual_seed(1729)
    rand_entries = []
    for k in range(3):
        cond_records = []
        cond_name = f"L13_joint_rand_{k}"
        for p in pair_cache:
            j_len = len(p["spans"]["active"]["joint_span"])
            u = torch.randn((j_len, model.config.hidden_size), generator=rng, dtype=torch.float32)
            u = u / u.norm(dim=-1, keepdim=True)
            with patch_positions(
                model, 13, p["spans"]["reference"]["joint_span"],
                p["cap_a"][13], random_dirs=u, own_vec=p["cap_r"][13],
            ):
                sc_r = score_four_candidates(model, pad_id, p["ctx_r"], p["conts_r"])
            cond_records.append(
                eval_choice_record(
                    cond_name, p["scenario"], p["scene_id"], "reference",
                    p["relation"], p["ref_row"], sc_r,
                )
            )
            with patch_positions(
                model, 13, p["spans"]["active"]["joint_span"],
                p["cap_r"][13], random_dirs=u, own_vec=p["cap_a"][13],
            ):
                sc_a = score_four_candidates(model, pad_id, p["ctx_a"], p["conts_a"])
            cond_records.append(
                eval_choice_record(
                    cond_name, p["scenario"], p["scene_id"], "active",
                    p["relation"], p["act_row"], sc_a,
                )
            )
        all_records.extend(cond_records)
        csum = summarize_condition(cond_records)
        rand_entries.append(
            {
                "seed_idx": k,
                "T_A2R_rand_pp": csum["reference"]["gap_pp"] - ref_gap,
                "T_R2A_rand_pp": act_gap - csum["active"]["gap_pp"],
            }
        )
    results["joint_block14_random_controls"] = rand_entries

    (out_dir / "summary.json").write_text(json.dumps(results, indent=2) + "\n")
    with gzip.open(out_dir / "records.jsonl.gz", "wt") as gz:
        for r in all_records:
            gz.write(json.dumps(r) + "\n")

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
