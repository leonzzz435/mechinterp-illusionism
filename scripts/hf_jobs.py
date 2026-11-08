# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = ["huggingface-hub[cli]==0.36.2"]
# ///
"""One explicitly selected, bounded study job; no automatic submissions or retries."""

import argparse
import hashlib
import json
import math
import re
import subprocess
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path

from huggingface_hub import HfApi, get_token, snapshot_download
from huggingface_hub.utils import HfHubHTTPError, get_session

ROOT = Path(__file__).resolve().parents[1]
IMAGE = (
    "ghcr.io/astral-sh/uv@sha256:dae7418c9d6661dbc821d99094a3f14fbc000e1c20646a921ee0535dc4c7aef7"
)
GIT_URL = "https://github.com/leonzzz435/mechinterp-illusionism.git"
FLAVOR = "l4x1"
HARD_TIMEOUT = 7200
CONFIGURATIONS = {
    "configs/qwen-ownership-recovery-v2.json": {
        "engine": "qwen-ownership-recovery",
        "run_prefix": "qwen-ownership-recovery-v2-",
        "receipt_name": "qwen-ownership-recovery-v2.json",
        "blocks": 3,
        "scored_variants": 3456,
        "generated_texts": 0,
        "hard_timeout_seconds": 2700,
    },
    "configs/qwen-ownership-recovery.json": {
        "engine": "qwen-ownership-recovery",
        "run_prefix": "qwen-ownership-recovery-",
        "receipt_name": "qwen-ownership-recovery.json",
        "blocks": 3,
        "scored_variants": 3456,
        "generated_texts": 0,
        "hard_timeout_seconds": 2700,
    },
    "configs/qwen-confidence-pilot-v2.json": {
        "engine": "qwen-confidence-v2",
        "run_prefix": "qwen-confidence-v2-",
        "receipt_name": "qwen-confidence-pilot-v2.json",
        "blocks": 24,
        "scored_variants": 1792,
        "generated_texts": 0,
    },
    "configs/qwen-confidence-pilot.json": {
        "engine": "qwen-confidence",
        "run_prefix": "qwen-confidence-",
        "receipt_name": "qwen-confidence-pilot.json",
        "blocks": 24,
        "scored_variants": 1792,
        "generated_texts": 0,
    },
    "configs/qwen-possessive-control.json": {
        "engine": "qwen-possessive-control",
        "run_prefix": "qwen-possessive-",
        "receipt_name": "qwen-possessive-control.json",
        "blocks": 16,
        "scored_variants": 6144,
        "generated_texts": 0,
    },
    "configs/harness-baseline.json": {
        "engine": "lm-eval",
        "run_prefix": "harness-",
        "receipt_name": "first.json",
        "blocks": 24,
        "scored_variants": 768,
        "generated_texts": 0,
    },
    "configs/qwen-pilot.json": {
        "engine": "qwen-pilot",
        "run_prefix": "qwen-",
        "receipt_name": "qwen-pilot.json",
        "blocks": 16,
        "scored_variants": 3072,
        "generated_texts": 160,
    },
    "configs/qwen-role-patch.json": {
        "engine": "qwen-role-patch",
        "run_prefix": "qwen-patch-",
        "receipt_name": "qwen-role-patch.json",
        "blocks": 8,
        "scored_variants": 11264,
        "technical_repeats": 32,
        "generated_texts": 0,
    },
    "configs/qwen-role-control.json": {
        "engine": "qwen-role-control",
        "run_prefix": "qwen-role-",
        "receipt_name": "qwen-role-control.json",
        "blocks": 8,
        "scored_variants": 2048,
        "generated_texts": 0,
    },
}
for _ownership_block in range(3):
    CONFIGURATIONS[f"configs/qwen-ownership-permissions-{_ownership_block:02d}.json"] = {
        "engine": "qwen-ownership-permissions",
        "run_prefix": f"qwen-ownership-{_ownership_block:02d}-",
        "receipt_name": f"qwen-ownership-permissions-{_ownership_block:02d}.json",
        "blocks": 16,
        "scored_variants": 6144,
        "generated_texts": 0,
    }

BOOTSTRAP = """
uv run --no-project --with huggingface-hub==0.36.2 python - <<'PY'
import hashlib, os, pathlib, subprocess
from huggingface_hub import hf_hub_download
bundle = hf_hub_download(
    os.environ['STUDY_ARTIFACT_REPO'],
    'sources/' + os.environ['STUDY_COMMIT'] + '.bundle',
    repo_type='dataset', revision=os.environ['STUDY_SOURCE_REVISION'],
)
checksum = hashlib.sha256(pathlib.Path(bundle).read_bytes()).hexdigest()
if checksum != os.environ['STUDY_SOURCE_SHA256']:
    raise RuntimeError('Source bundle checksum mismatch')
subprocess.run(['git', 'clone', bundle, '/workspace/study'], check=True)
PY
cd /workspace/study
git checkout --detach "$STUDY_COMMIT"
test "$(git rev-parse HEAD)" = "$STUDY_COMMIT"
uv sync --locked --no-dev --extra gpu --extra eval
uv run --no-sync python scripts/hf_worker.py
"""


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def read_json(path):
    return json.loads(Path(path).read_text())


def publish_source(api, repo, commit):
    """Keep private GitHub credentials off the job; transfer committed Git objects."""
    bundle = ROOT / ".hf-jobs" / "sources" / (commit + ".bundle")
    bundle.parent.mkdir(parents=True, exist_ok=True)
    if not bundle.exists():
        git("bundle", "create", str(bundle), "HEAD")
    if git("bundle", "list-heads", str(bundle)).split()[0] != commit:
        raise ValueError("Source bundle does not match the selected commit")
    checksum = hashlib.sha256(bundle.read_bytes()).hexdigest()
    uploaded = api.upload_file(
        path_or_fileobj=bundle,
        path_in_repo="sources/" + bundle.name,
        repo_id=repo,
        repo_type="dataset",
        commit_message="Pin source for " + commit[:12],
    )
    return {"source_revision": uploaded.oid, "source_sha256": checksum}


def quote_budget(hardware, budget, *, timeout=HARD_TIMEOUT, reserve_divisor=2):
    """The selected provider timeout bounds compute, including environment setup."""
    try:
        budget = Decimal(str(budget))
    except InvalidOperation:
        raise ValueError("Budget must be a number in US dollars") from None
    if not budget.is_finite() or budget <= 0:
        raise ValueError("Budget must be a finite, positive amount in US dollars")
    if hardware["name"] != FLAVOR or hardware["unitLabel"] != "minute":
        raise ValueError("Unexpected hardware/price units; recheck before spending")
    rate = hardware["unitCostMicroUSD"]
    if type(rate) is not int or rate <= 0:
        raise ValueError("Invalid hardware price")
    # One extra billable minute is reserved for rounding. Historical plans keep
    # half the budget unallocated; the explicitly capped recovery uses its whole
    # small allocation. This is a compute bound, not an account-wide spend cap.
    maximum = Decimal(rate) * (math.ceil(timeout / 60) + 1) / 1_000_000
    if maximum > budget / reserve_divisor:
        raise ValueError("Quoted compute exceeds the budget allocation; do not submit")
    return {"approved_budget_usd": str(budget), "max_compute_usd": str(maximum)}


def config_details(config):
    path = (ROOT / config).resolve()
    allowed = CONFIGURATIONS
    if not path.is_relative_to(ROOT) or path.relative_to(ROOT).as_posix() not in allowed:
        raise ValueError("Choose an explicitly supported study configuration")
    spec = read_json(path)
    details = CONFIGURATIONS[path.relative_to(ROOT).as_posix()]
    if spec["engine"] != details["engine"]:
        raise ValueError("Configuration engine differs from the selected protocol")
    return {
        "config": path.relative_to(ROOT).as_posix(),
        "config_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "protocol": spec["protocol"],
        "run_limit_seconds": spec["max_seconds"],
        **details,
    }


def resume_details(receipt, proposal, api):
    """A separately budgeted job can restore a stopped job's immutable snapshot."""
    previous = read_json(receipt)
    for key in ("artifact_repo", "config", "config_sha256", "commit"):
        if previous.get(key) != proposal.get(key):
            raise ValueError(f"Resume requires the same {key}")
    selected = CONFIGURATIONS.get(proposal["config"], {})
    if selected.get("engine") not in {
        "qwen-pilot",
        "qwen-role-control",
        "qwen-role-patch",
        "qwen-possessive-control",
        "qwen-confidence",
        "qwen-confidence-v2",
    } or not re.fullmatch(
        re.escape(selected["run_prefix"]) + r"[0-9a-f]{16}", previous.get("run_name", "")
    ):
        raise ValueError("Only a recorded Qwen pilot can be resumed through this launcher")
    if not previous.get("job_id"):
        raise ValueError("Resolve an unknown dispatch before preparing a continuation")
    job = api.inspect_job(job_id=previous["job_id"], namespace=previous["namespace"])
    if job.status.stage not in {"COMPLETED", "CANCELED", "ERROR", "DELETED"}:
        raise ValueError("Previous job is still active; no concurrent continuation")
    repo = api.repo_info(previous["artifact_repo"], repo_type="dataset")
    if not repo.private:
        raise ValueError("Resume artifacts must remain private")
    return {
        "repo": previous["artifact_repo"],
        "revision": repo.sha,
        "run_name": previous["run_name"],
        "job_id": previous["job_id"],
    }


def plan(namespace, budget, config="configs/harness-baseline.json", resume_receipt=None):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,95}", namespace):
        raise ValueError("Use an explicit HF username or organization")
    response = get_session().get("https://huggingface.co/api/jobs/hardware", timeout=30)
    response.raise_for_status()
    hardware = next(h for h in response.json() if h["name"] == FLAVOR)
    details = config_details(config)
    recovery = details["engine"] == "qwen-ownership-recovery"
    if recovery:
        from ownership_recovery import validate_spec

        validate_spec(read_json(ROOT / details["config"]))
    quote = quote_budget(
        hardware,
        budget,
        timeout=details.get("hard_timeout_seconds", HARD_TIMEOUT),
        reserve_divisor=1 if recovery else 2,
    )
    quote["proposed_budget_usd"] = quote.pop("approved_budget_usd")
    proposal = {
        "namespace": namespace,
        "artifact_repo": namespace + "/mechinterp-illusionism-results",
        "commit": git("rev-parse", "HEAD"),
        "working_tree_clean": not bool(git("status", "--porcelain")),
        "git_url": GIT_URL,
        "image": IMAGE,
        "flavor": FLAVOR,
        "hardware": hardware,
        "hard_timeout_seconds": HARD_TIMEOUT,
        **details,
        "budget_status": "proposal_only_not_authorization",
        **quote,
    }
    if resume_receipt:
        proposal["resume"] = resume_details(resume_receipt, proposal, HfApi())
    return proposal


def submit(proposal, receipt, api, token):
    receipt = Path(receipt)
    if proposal.get("engine") == "qwen-ownership-permissions":
        guard = ROOT / ".hf-jobs/ownership-permissions-v1.json"
        if not guard.exists():
            raise ValueError("Use ownership_tranche.py: aggregate budget reservation required")
        reservation = read_json(guard)
        if (
            reservation.get("state") != "submitting"
            or reservation.get("commit") != proposal.get("commit")
            or reservation.get("tranche_id") != proposal.get("tranche_id")
            or proposal not in reservation.get("jobs", [])
            or receipt.resolve() != (ROOT / ".hf-jobs" / proposal["receipt_name"]).resolve()
        ):
            raise ValueError("Ownership submission differs from reserved tranche")
    if not token:
        raise ValueError("Log in locally with hf auth login; do not put tokens in the command")
    if receipt.exists():
        raise ValueError("Receipt already exists. Inspect that job; no duplicate submission")
    if not proposal["working_tree_clean"]:
        raise ValueError("Commit and push changes before submitting a reproducible job")
    remote = git("ls-remote", GIT_URL, "refs/heads/main").split()[0]
    if remote != proposal["commit"]:
        raise ValueError("Push the selected commit to origin/main before submitting")
    api.whoami()  # Read-only credential check before any mutation.
    api.create_repo(proposal["artifact_repo"], repo_type="dataset", private=True, exist_ok=True)
    if not api.repo_info(proposal["artifact_repo"], repo_type="dataset").private:
        raise ValueError("Output repository must be private; refusing to publish run outputs")
    state = {
        **proposal,
        **publish_source(api, proposal["artifact_repo"], proposal["commit"]),
        "run_name": proposal.get("run_prefix", "harness-") + uuid.uuid4().hex[:16],
        "state": "submitting",
        "budget_status": "submitted_with_explicit_cli_budget",
        "approved_budget_usd": proposal.get(
            "proposed_budget_usd", proposal.get("approved_budget_usd")
        ),
    }
    # Exclusive local receipt prevents a repeated invocation from spending again,
    # even if the server accepted the request but its response was lost.
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with receipt.open("x") as stream:
        json.dump(state, stream, indent=2)
    try:
        job = api.run_job(
            image=proposal["image"],
            command=["bash", "-euc", BOOTSTRAP],
            flavor=proposal["flavor"],
            timeout=proposal["hard_timeout_seconds"],
            namespace=proposal["namespace"],
            env={
                "STUDY_COMMIT": proposal["commit"],
                "STUDY_RUN_NAME": state["run_name"],
                "STUDY_ARTIFACT_REPO": proposal["artifact_repo"],
                "STUDY_IMAGE": proposal["image"],
                "STUDY_SOURCE_REVISION": state["source_revision"],
                "STUDY_SOURCE_SHA256": state["source_sha256"],
                "STUDY_CONFIG": proposal.get("config", "configs/harness-baseline.json"),
                "STUDY_CONFIG_SHA256": proposal.get("config_sha256", ""),
                "STUDY_RESUME": json.dumps(proposal.get("resume")),
                "PYTHONUNBUFFERED": "1",
                "HF_HUB_DISABLE_TELEMETRY": "1",
                "HF_HUB_DISABLE_XET": "1",
            },
            secrets={"HF_TOKEN": token},
        )
    except Exception as exc:
        response = exc.response if isinstance(exc, HfHubHTTPError) else None
        if response is not None and response.status_code in {400, 401, 402, 403, 404, 422}:
            reason = str(exc).replace(token, "[REDACTED]")
            state.update(
                state="submission_rejected", http_status=response.status_code, reason=reason
            )
            write_json(receipt, state)
            raise RuntimeError(f"HF rejected the job request: {reason}") from None
        state["state"] = "submission_unknown"
        write_json(receipt, state)
        raise RuntimeError(
            "Submission outcome unknown. Check the HF Jobs dashboard; do not resubmit"
        ) from None
    state.update(state="submitted", job_id=job.id, job_url=job.url)
    write_json(receipt, state)
    return state


def fetch(state, destination):
    destination = Path(destination)
    # Pin this download to one repository commit so a running uploader cannot
    # mix files from different checkpoint commits in a local snapshot.
    revision = HfApi().repo_info(state["artifact_repo"], repo_type="dataset").sha
    snapshot_download(
        state["artifact_repo"],
        repo_type="dataset",
        revision=revision,
        allow_patterns=[state["run_name"] + "/**"],
        local_dir=destination,
    )
    folder = destination / state["run_name"]
    if not (folder / "job.json").exists():
        raise ValueError("No saved job artifacts yet; inspect status and logs")
    run_dir = folder / "run"
    checksums = run_dir / "checksums.json"
    if checksums.exists():
        for name, expected in read_json(checksums).items():
            path = (run_dir / name).resolve()
            if not path.is_relative_to(run_dir.resolve()):
                raise ValueError("Invalid archive checksum path")
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError(f"Downloaded checksum mismatch: {name}")
    export_receipt = folder / "export.json"
    if export_receipt.exists():
        exported = read_json(export_receipt)
        archive = (folder / exported["archive"]).resolve()
        if not archive.is_relative_to(folder.resolve()):
            raise ValueError("Invalid export path")
        if hashlib.sha256(archive.read_bytes()).hexdigest() != exported["sha256"]:
            raise ValueError("Downloaded archive checksum mismatch")
    return {
        "directory": str(folder),
        "artifact_revision": revision,
        "export_verified": checksums.exists(),
        "report": str(run_dir / "report.md"),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "submit"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--namespace", required=True)
        cmd.add_argument("--budget-usd", required=True)
        cmd.add_argument("--config", default="configs/harness-baseline.json")
        cmd.add_argument(
            "--resume-receipt",
            type=Path,
            help="Restore a stopped Qwen job; requires a new budget and receipt",
        )
        if name == "submit":
            cmd.add_argument("--receipt", type=Path)
    for name in ("status", "logs", "cancel", "fetch"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--receipt", type=Path, default=ROOT / ".hf-jobs/first.json")
        if name == "fetch":
            cmd.add_argument("--out", type=Path, default=ROOT / ".hf-jobs/downloads")
    args = parser.parse_args(argv)
    try:
        if args.command in {"plan", "submit"}:
            if args.command == "submit" and args.resume_receipt and not args.receipt:
                raise ValueError("A continuation requires an explicit NEW --receipt path")
            proposal = plan(args.namespace, args.budget_usd, args.config, args.resume_receipt)
            result = (
                proposal
                if args.command == "plan"
                else submit(
                    proposal,
                    args.receipt or ROOT / ".hf-jobs" / proposal["receipt_name"],
                    HfApi(),
                    get_token(),
                )
            )
        else:
            state = read_json(args.receipt)
            if args.command == "fetch":
                result = fetch(state, args.out)
            else:
                if "job_id" not in state:
                    raise ValueError(
                        "Unknown job ID; resolve the receipt using the HF Jobs dashboard"
                    )
                api = HfApi()
                kwargs = {"job_id": state["job_id"], "namespace": state["namespace"]}
                if args.command == "logs":
                    for line in api.fetch_job_logs(**kwargs):
                        print(line, end="" if line.endswith("\n") else "\n", flush=True)
                    return 0
                if args.command == "cancel":
                    api.cancel_job(**kwargs)
                    result = {"cancel_requested": True, "job_id": state["job_id"]}
                else:
                    job = api.inspect_job(**kwargs)
                    result = {"job_id": job.id, "url": job.url, "stage": job.status.stage}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (ValueError, RuntimeError, OSError, KeyError, StopIteration) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
