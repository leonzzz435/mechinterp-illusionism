"""Experiment 3: 28-layer subspace geometry in Qwen2.5-7B-Instruct (L_self, Role, M_self)."""

import argparse
import json
import os
from pathlib import Path

import numpy as np
from huggingface_hub import HfApi

from self_model_study import role_control
from self_model_study.pilot_backend import encode_boundary, render_prompt, select_command
from self_model_study.query_reference import build_inputs

L_SELF_PAIRS = [
    (
        "I checked my active permissions before running the task.",
        "The operator checked the active permissions before running the task.",
    ),
    (
        "My current role determines which command I can execute.",
        "Their current role determines which command the operator can execute.",
    ),
    (
        "I cannot access that resource under my current settings.",
        "The agent cannot access that resource under its current settings.",
    ),
    (
        "As an AI assistant, I do not have subjective experience.",
        "As a software module, it does not have subjective experience.",
    ),
    (
        "I will verify my own credentials before modifying the ledger.",
        "The service will verify its own credentials before modifying the ledger.",
    ),
    (
        "You are responsible for keeping your connection updated.",
        "They are responsible for keeping their connection updated.",
    ),
    (
        "Please check your active account before selecting a command.",
        "Please check the reference account before selecting a command.",
    ),
    (
        "I noticed that my previous permission was revoked.",
        "The user noticed that the previous permission was revoked.",
    ),
    (
        "Your current authorization applies only to your assigned unit.",
        "The current authorization applies only to the assigned unit.",
    ),
    (
        "I must rely on my context window to track my state.",
        "The model must rely on its context window to track its state.",
    ),
    (
        "My instructions specify what I am allowed to return.",
        "The instructions specify what the system is allowed to return.",
    ),
    (
        "You should verify which marker your account holds right now.",
        "One should verify which marker that account holds right now.",
    ),
    (
        "I have no persistent memory outside my current prompt.",
        "The program has no persistent memory outside its current prompt.",
    ),
    (
        "When my permissions change, I need to update my choice.",
        "When its permissions change, the router needs to update its choice.",
    ),
    (
        "Your active operator name is listed at the top of the prompt.",
        "The reference operator name is listed at the top of the prompt.",
    ),
    (
        "I am summarizing my own reasoning steps carefully.",
        "The evaluator is summarizing the reasoning steps carefully.",
    ),
    (
        "My response reflects only the tokens in my context.",
        "The response reflects only the tokens in the context.",
    ),
    (
        "You must select the command that succeeds for your unit.",
        "One must select the command that succeeds for that unit.",
    ),
    (
        "I keep track of my state by reading the latest event.",
        "The parser keeps track of its state by reading the latest event.",
    ),
    (
        "My identity in this session is defined by my role header.",
        "The identity in this session is defined by the role header.",
    ),
    (
        "You can inspect your assigned connection in the log below.",
        "Anyone can inspect the assigned connection in the log below.",
    ),
    (
        "I prefer to verify my access rights before acting.",
        "The client prefers to verify its access rights before acting.",
    ),
    (
        "My output depends on how I interpret the prompt.",
        "The output depends on how the system interprets the prompt.",
    ),
    (
        "You are asked to choose one command for your active connection.",
        "They are asked to choose one command for the target connection.",
    ),
    (
        "I cannot confirm my state without checking the event history.",
        "It cannot confirm its state without checking the event history.",
    ),
    (
        "My active binding was overwritten by a later update.",
        "The active binding was overwritten by a later update.",
    ),
    (
        "You should follow only the permissions granted to you.",
        "The worker should follow only the permissions granted to it.",
    ),
    (
        "I am reporting my own confidence in this selection.",
        "The scorer is reporting its confidence in this selection.",
    ),
    (
        "My vocabulary choices include first-person pronouns like I and my.",
        "The vocabulary choices include third-person nouns and articles.",
    ),
    (
        "You have full access to your own granted marker.",
        "The account has full access to its own granted marker.",
    ),
]


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def cos_sim(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def extract_all_layer_last_token(model, tok, prompts):
    import torch

    n_layers = model.config.num_hidden_layers
    d_model = model.config.hidden_size
    out = np.zeros((len(prompts), n_layers, d_model), dtype=np.float32)

    for idx, prompt in enumerate(prompts):
        rendered = render_prompt(tok, prompt, "chat")
        ids = tok.encode(rendered, add_special_tokens=False)
        inp = torch.tensor([ids], dtype=torch.long, device=model.device)
        with torch.inference_mode():
            res = model(input_ids=inp, output_hidden_states=True, use_cache=False)
        for layer_idx in range(n_layers):
            out[idx, layer_idx] = res.hidden_states[layer_idx + 1][0, -1].float().cpu().numpy()
        if (idx + 1) % 64 == 0:
            print(f"Extracted hidden states: {idx + 1}/{len(prompts)}", flush=True)
    return out


def score_m_self_trials(model, tok, rows):
    import torch
    import torch.nn.functional as F

    n_layers = model.config.num_hidden_layers
    d_model = model.config.hidden_size
    acts = np.zeros((len(rows), n_layers, d_model), dtype=np.float32)
    labels = np.zeros(len(rows), dtype=np.int32)
    pad_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    for idx, row in enumerate(rows):
        rendered = render_prompt(tok, row["prompt"], "chat")
        pairs = [encode_boundary(tok, rendered, c, 2048) for c in row["choices"]]
        ctx, conts = pairs[0][0], [p[1] for p in pairs]

        inp_ctx = torch.tensor([ctx], dtype=torch.long, device=model.device)
        with torch.inference_mode():
            h_res = model(input_ids=inp_ctx, output_hidden_states=True, use_cache=False)
        for layer_idx in range(n_layers):
            acts[idx, layer_idx] = h_res.hidden_states[layer_idx + 1][0, -1].float().cpu().numpy()

        max_len = max(len(ctx) + len(c) for c in conts)
        input_ids = torch.full((len(conts), max_len), pad_id, dtype=torch.long, device=model.device)
        attn_mask = torch.zeros((len(conts), max_len), dtype=torch.long, device=model.device)
        for i, cont in enumerate(conts):
            seq = ctx + cont
            input_ids[i, : len(seq)] = torch.tensor(seq, dtype=torch.long, device=model.device)
            attn_mask[i, : len(seq)] = 1
        with torch.inference_mode():
            logits = model(input_ids=input_ids, attention_mask=attn_mask, use_cache=False).logits
        scores = []
        ctx_len = len(ctx)
        for i, cont in enumerate(conts):
            step_logits = logits[i, ctx_len - 1 : ctx_len - 1 + len(cont), :].float()
            log_probs = F.log_softmax(step_logits, dim=-1)
            tok_ids = torch.tensor(cont, dtype=torch.long, device=model.device).unsqueeze(-1)
            scores.append(float(log_probs.gather(-1, tok_ids).squeeze(-1).sum().item()))

        sel, status = select_command(row["choices"], scores)
        if status == "tie":
            sel = row["choices"][scores.index(max(scores))]
        labels[idx] = 1 if sel == row["expected_command"] else 0
        if (idx + 1) % 64 == 0:
            acc_now = labels[: idx + 1].mean()
            print(f"Scored M_self trials: {idx + 1}/{len(rows)} (acc={acc_now:.3f})", flush=True)
    return acts, labels


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--revision", default="a09a35458c702b33eeacc393d103063234e8bc28")
    parser.add_argument("--m-self-worlds", type=int, default=16)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--hf-repo", default="")
    parser.add_argument("--hf-prefix", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    l_self_pos = [p[0] for p in L_SELF_PAIRS]
    l_self_neg = [p[1] for p in L_SELF_PAIRS]

    rc_plan = role_control.build_plan(role_control.DEFAULT_SPEC)
    role_act, role_ref = [], []
    for blk in rc_plan["blocks"]:
        jobs = [j for j in blk["jobs"] if role_control.stratum(j["row"]) == "after_relevant"]
        for j in jobs:
            if j["row"]["frame"] == "active":
                role_act.append(j["row"]["prompt"])
            else:
                role_ref.append(j["row"]["prompt"])

    _, qr_rows = build_inputs()
    m_rows = [
        r
        for r in qr_rows
        if r["world_index"] < args.m_self_worlds
        and r["stage"] == "after_both"
        and r["queried_owner"] == "self"
        and r["query_form"] == "possessive"
    ]

    print(
        f"Counts -> L_self pairs: {len(L_SELF_PAIRS)}, "
        f"Role pairs: {len(role_act)}, M_self trials: {len(m_rows)}"
    )
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        payload = {"l_self": len(L_SELF_PAIRS), "role": len(role_act), "m_self": len(m_rows)}
        (out_dir / "dry_run.json").write_text(json.dumps(payload, indent=2))
        return

    import torch
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import GroupKFold
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

    h_l_pos = extract_all_layer_last_token(model, tok, l_self_pos)
    h_l_neg = extract_all_layer_last_token(model, tok, l_self_neg)
    h_r_act = extract_all_layer_last_token(model, tok, role_act)
    h_r_ref = extract_all_layer_last_token(model, tok, role_ref)
    h_m, y_m = score_m_self_trials(model, tok, m_rows)
    groups_m = np.array([r["world_index"] for r in m_rows])

    n_layers = model.config.num_hidden_layers
    layer_stats = []
    gkf = GroupKFold(n_splits=min(5, len(np.unique(groups_m))))

    for layer_idx in range(n_layers):
        v_l = unit((h_l_pos[:, layer_idx] - h_l_neg[:, layer_idx]).mean(axis=0))
        v_role = unit((h_r_act[:, layer_idx] - h_r_ref[:, layer_idx]).mean(axis=0))

        pos_mask = y_m == 1
        neg_mask = y_m == 0
        v_m_dim = unit(
            h_m[pos_mask, layer_idx].mean(axis=0) - h_m[neg_mask, layer_idx].mean(axis=0)
        )

        oof_preds = np.zeros(len(y_m), dtype=np.float64)
        for tr, va in gkf.split(h_m[:, layer_idx], y_m, groups_m):
            clf = LogisticRegression(C=0.05, max_iter=500, random_state=1729)
            clf.fit(h_m[tr, layer_idx], y_m[tr])
            oof_preds[va] = clf.predict_proba(h_m[va, layer_idx])[:, 1]
        probe_auc = float(roc_auc_score(y_m, oof_preds))

        full_clf = LogisticRegression(C=0.05, max_iter=500, random_state=1729)
        full_clf.fit(h_m[:, layer_idx], y_m)
        v_m_probe = unit(full_clf.coef_[0])

        basis = np.column_stack([v_l, v_m_dim])
        proj = basis @ np.linalg.pinv(basis.T @ basis) @ basis.T @ v_role
        proj_frac = float(np.dot(proj, proj))

        entry = {
            "layer": layer_idx,
            "block": layer_idx + 1,
            "m_self_probe_cv_auroc": probe_auc,
            "cos_L_Role": cos_sim(v_l, v_role),
            "cos_L_M_dim": cos_sim(v_l, v_m_dim),
            "cos_Role_M_dim": cos_sim(v_role, v_m_dim),
            "cos_L_M_probe": cos_sim(v_l, v_m_probe),
            "cos_Role_M_probe": cos_sim(v_role, v_m_probe),
            "cos_M_dim_M_probe": cos_sim(v_m_dim, v_m_probe),
            "role_proj_onto_L_M_span": proj_frac,
        }
        layer_stats.append(entry)
        print(
            f"Block {layer_idx+1:2d} | M_AUROC={probe_auc:.3f} | "
            f"cos(L,Role)={entry['cos_L_Role']:+.3f} | "
            f"cos(L,M_dim)={entry['cos_L_M_dim']:+.3f} | "
            f"cos(Role,M_dim)={entry['cos_Role_M_dim']:+.3f}",
            flush=True,
        )

    summary = {
        "model": args.model,
        "m_self_trials": len(m_rows),
        "m_self_acc": float(y_m.mean()),
        "l_self_pairs": len(L_SELF_PAIRS),
        "role_pairs": len(role_act),
        "layers": layer_stats,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    if args.hf_repo and args.hf_prefix:
        os.environ["HF_HUB_DISABLE_XET"] = "1"
        api = HfApi()
        api.create_repo(args.hf_repo, repo_type="dataset", private=True, exist_ok=True)
        api.upload_file(
            path_or_fileobj=out_dir / "summary.json",
            path_in_repo=f"{args.hf_prefix}/summary.json",
            repo_id=args.hf_repo,
            repo_type="dataset",
            commit_message=f"Upload {args.hf_prefix}/summary.json",
        )


if __name__ == "__main__":
    main()
