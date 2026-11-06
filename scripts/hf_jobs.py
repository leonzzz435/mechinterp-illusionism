# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = ["huggingface-hub[cli]==0.36.2"]
# ///
"""One fixed Gemma baseline on HF Jobs; no automatic submissions or retries."""

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


def quote_budget(hardware, budget):
    """A two-hour provider timeout bounds compute, including environment setup."""
    try:
        budget = Decimal(str(budget))
    except InvalidOperation:
        raise ValueError("Budget must be a number in US dollars") from None
    if not budget.is_finite() or budget <= 0 or budget > 10:
        raise ValueError("This first-run launcher accepts an explicit budget of at most USD 10")
    if hardware["name"] != FLAVOR or hardware["unitLabel"] != "minute":
        raise ValueError("Unexpected hardware/price units; recheck before spending")
    rate = hardware["unitCostMicroUSD"]
    if type(rate) is not int or rate <= 0:
        raise ValueError("Invalid hardware price")
    # One extra billable minute is reserved for rounding. Keep half the approved
    # budget unallocated; this is a compute bound, not an account-wide spend cap.
    maximum = Decimal(rate) * (math.ceil(HARD_TIMEOUT / 60) + 1) / 1_000_000
    if maximum > budget / 2:
        raise ValueError("Quoted compute exceeds half the approved budget; do not submit")
    return {"approved_budget_usd": str(budget), "max_compute_usd": str(maximum)}


def plan(namespace, budget):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,95}", namespace):
        raise ValueError("Use an explicit HF username or organization")
    response = get_session().get("https://huggingface.co/api/jobs/hardware", timeout=30)
    response.raise_for_status()
    hardware = next(h for h in response.json() if h["name"] == FLAVOR)
    return {
        "namespace": namespace,
        "artifact_repo": namespace + "/mechinterp-illusionism-results",
        "commit": git("rev-parse", "HEAD"),
        "working_tree_clean": not bool(git("status", "--porcelain")),
        "git_url": GIT_URL,
        "image": IMAGE,
        "flavor": FLAVOR,
        "hardware": hardware,
        "hard_timeout_seconds": HARD_TIMEOUT,
        "run_limit_seconds": 3600,
        "config": "configs/harness-baseline.json",
        "blocks": 24,
        "scored_variants": 768,
        **quote_budget(hardware, budget),
    }


def submit(proposal, receipt, api, token):
    receipt = Path(receipt)
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
        "run_name": "harness-" + uuid.uuid4().hex[:16],
        "state": "submitting",
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
                "PYTHONUNBUFFERED": "1",
                "HF_HUB_DISABLE_TELEMETRY": "1",
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
        if name == "submit":
            cmd.add_argument("--receipt", type=Path, default=ROOT / ".hf-jobs/first.json")
    for name in ("status", "logs", "cancel", "fetch"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--receipt", type=Path, default=ROOT / ".hf-jobs/first.json")
        if name == "fetch":
            cmd.add_argument("--out", type=Path, default=ROOT / ".hf-jobs/downloads")
    args = parser.parse_args(argv)
    try:
        if args.command in {"plan", "submit"}:
            proposal = plan(args.namespace, args.budget_usd)
            result = (
                proposal
                if args.command == "plan"
                else submit(proposal, args.receipt, HfApi(), get_token())
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
