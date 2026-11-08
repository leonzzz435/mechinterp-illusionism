# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = ["huggingface-hub[cli]==0.36.2"]
# ///
"""One aggregate-budgeted Qwen/permissions tranche, exactly three distinct HF jobs."""

import argparse
import json
import uuid
from decimal import Decimal
from pathlib import Path

import hf_jobs as hf

CONFIGS = [f"configs/qwen-ownership-permissions-{i:02d}.json" for i in range(3)]
GUARD = hf.ROOT / ".hf-jobs/ownership-permissions-v1.json"


def plan(namespace, budget):
    if not Decimal(budget).is_finite() or not 0 < Decimal(budget) <= Decimal("5"):
        raise ValueError("This tranche is authorized for at most $5 total")
    jobs = [hf.plan(namespace, budget, config) for config in CONFIGS]
    total = sum(Decimal(p["max_compute_usd"]) for p in jobs)
    if total > Decimal(budget):
        raise ValueError("Combined three-job quote exceeds the total tranche budget")
    if len({p["commit"] for p in jobs}) != 1 or not all(p["working_tree_clean"] for p in jobs):
        raise ValueError("Commit and push the complete preflight before planning this tranche")
    token = hf.ROOT / "review/ownership-permissions-inputs.json.gz"
    preflight = hf.read_json(hf.ROOT / "review/ownership-permissions-preflight.json")
    if hf.hashlib.sha256(token.read_bytes()).hexdigest() != preflight["token_inputs_sha256"]:
        raise ValueError("Missing or changed CPU token preflight")
    existing = [
        str(hf.ROOT / ".hf-jobs" / p["receipt_name"])
        for p in jobs
        if (hf.ROOT / ".hf-jobs" / p["receipt_name"]).exists()
    ]
    if GUARD.exists() or existing:
        raise ValueError("Existing ownership guard/receipt: inspect, never delete to bypass")
    tranche_id = "ownership-permissions-v1-" + uuid.uuid4().hex[:12]
    return {
        "tranche_id": tranche_id,
        "state": "plan_only",
        "commit": jobs[0]["commit"],
        "namespace": namespace,
        "approved_total_budget_usd": str(budget),
        "total_compute_ceiling_usd": str(total),
        "scheduled_choices": 18432,
        "jobs": [
            {
                **p,
                "tranche_id": tranche_id,
                "tranche_total_budget_usd": str(budget),
                "tranche_compute_ceiling_usd": str(total),
            }
            for p in jobs
        ],
    }


def submit(proposal, api, token):
    if GUARD.exists():
        raise ValueError("Tranche already reserved; no automatic second submission")
    if [j["config"] for j in proposal["jobs"]] != CONFIGS:
        raise ValueError("Tranche must contain exactly the three authorized configurations")
    total = sum(Decimal(j["max_compute_usd"]) for j in proposal["jobs"])
    budget = Decimal(proposal["approved_total_budget_usd"])
    if (
        not 0 < total <= budget <= Decimal("5")
        or str(total) != proposal["total_compute_ceiling_usd"]
    ):
        raise ValueError("Invalid aggregate cost reservation")
    if not token:
        raise ValueError("Local HF login required")
    api.whoami()
    state = {**proposal, "state": "submitting", "receipts": []}
    GUARD.parent.mkdir(parents=True, exist_ok=True)
    with GUARD.open("x") as stream:
        json.dump(state, stream, indent=2)
    try:
        for job in proposal["jobs"]:
            receipt = hf.ROOT / ".hf-jobs" / job["receipt_name"]
            result = hf.submit(job, receipt, api, token)
            state["receipts"].append(
                {"path": str(receipt), "job_id": result["job_id"], "job_url": result["job_url"]}
            )
            hf.write_json(GUARD, state)
    except BaseException:
        state["state"] = "stopped_inspect_individual_receipts_no_retry"
        hf.write_json(GUARD, state)
        raise
    state["state"] = "submitted"
    hf.write_json(GUARD, state)
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "submit"):
        p = sub.add_parser(name)
        p.add_argument("--namespace", required=True)
        p.add_argument("--budget-usd", required=True)
    p = sub.add_parser("analyze")
    p.add_argument("--runs", nargs="+", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "analyze":
        from self_model_study.ownership_reporting import analyze_tranche

        result = analyze_tranche(args.runs, args.out)
    else:
        result = plan(args.namespace, args.budget_usd)
        if args.command == "submit":
            result = submit(result, hf.HfApi(), hf.get_token())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
