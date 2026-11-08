"""Run one selected protocol and persist committed work to a private HF repo."""

import json
import os
import random
import re
import shutil
import subprocess
import time
from email.utils import parsedate_to_datetime
from pathlib import Path

from huggingface_hub import CommitOperationAdd, HfApi, constants, snapshot_download
from requests.exceptions import ConnectionError as RequestConnectionError
from requests.exceptions import Timeout

from self_model_study.io import digest, file_hash, read_json, write_json


def configure_transfer():
    # Pinned hub 0.36.2 checks this constant before offering the Xet upload transport.
    # Set the environment too, including for subprocesses. No dependency/model change.
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    constants.HF_HUB_DISABLE_XET = True


def upload_cause(exc):
    # Hub 0.36.2 wraps LFS HTTP errors in RuntimeError from the original error.
    seen = set()
    while isinstance(exc, RuntimeError) and exc.__cause__ is not None and id(exc) not in seen:
        seen.add(id(exc))
        exc = exc.__cause__
    return exc


def transient_upload(exc):
    exc = upload_cause(exc)
    response = getattr(exc, "response", None)
    if response is not None:
        return response.status_code in {408, 429, 500, 502, 503, 504}
    if isinstance(exc, (RequestConnectionError, Timeout)):
        return True
    # hf-xet raises a builtin ConnectionError rather than an HTTPError.
    return isinstance(exc, ConnectionError) and bool(
        re.search(r"HTTP status (?:client|server) error \((?:429|50[0234])\b", str(exc))
    )


def retry_delay(exc, attempt):
    exc = upload_cause(exc)
    delay = min(30 * 2**attempt, 240) + random.uniform(0, 5)
    response = getattr(exc, "response", None)
    if response is not None:
        value = response.headers.get("Retry-After")
        if value:
            try:
                seconds = float(value)
            except ValueError:
                try:
                    seconds = parsedate_to_datetime(value).timestamp() - time.time()
                except (ValueError, TypeError, OverflowError):
                    seconds = 0
            delay = max(delay, seconds)
    return delay


class CheckpointUploader:
    """Serialize transfers, skip unchanged snapshots and bound retries across the job."""

    def __init__(self, api, repo, output, name, *, sleep=None, max_retry_sleep=600):
        configure_transfer()
        self.api, self.repo, self.output, self.name = api, repo, Path(output), name
        self.sleep = sleep or time.sleep
        self.max_retry_sleep = max_retry_sleep
        self.waited = 0
        self.last_uploaded = None
        self.failure = None
        self.events = []

    def __call__(self, _directory):
        if self.failure is not None:
            # The runner and worker both call checkpoint in finally. Do not hammer
            # the service again after exhausting this job's transfer budget.
            raise self.failure
        fingerprint = digest(
            {
                str(p.relative_to(self.output)): file_hash(p)
                for p in sorted(self.output.rglob("*"))
                if p.is_file()
                and p.name not in {".lock", "transport.json"}
                and not p.name.endswith(".tmp")
                and not any(part.startswith(".") for part in p.relative_to(self.output).parts)
            }
        )
        if fingerprint == self.last_uploaded:
            return
        for attempt in range(5):
            try:
                # upload_folder in pinned hub 0.36.2 does not expose num_threads;
                # the public commit API does. Build fresh operations on each retry.
                operations = [
                    CommitOperationAdd(
                        path_in_repo=f"{self.name}/{p.relative_to(self.output).as_posix()}",
                        path_or_fileobj=p,
                    )
                    for p in sorted(self.output.rglob("*"))
                    if p.is_file()
                    and p.name != ".lock"
                    and not p.name.endswith(".tmp")
                    and not any(part.startswith(".") for part in p.relative_to(self.output).parts)
                ]
                result = self.api.create_commit(
                    repo_id=self.repo,
                    repo_type="dataset",
                    operations=operations,
                    num_threads=1,
                    commit_message=f"Checkpoint {self.name}",
                )
                self.last_uploaded = fingerprint
                self.events.append({"state": "uploaded", "snapshot": fingerprint})
                write_json(self.output / "transport.json", self.events)
                return result
            except Exception as exc:
                delay = retry_delay(exc, attempt) if transient_upload(exc) else None
                retry = (
                    delay is not None
                    and attempt < 4
                    and self.waited + delay <= self.max_retry_sleep
                )
                self.events.append(
                    {
                        "state": "retry" if retry else "failed",
                        "error_type": type(exc).__name__,
                        "delay_seconds": delay if retry else None,
                        "snapshot": fingerprint,
                    }
                )
                write_json(self.output / "transport.json", self.events)
                if not retry:
                    self.failure = exc
                    raise
                self.waited += delay
                print(
                    f"Checkpoint transfer throttled/unavailable; retry in {delay:.1f}s", flush=True
                )
                self.sleep(delay)


def restore_checkpoint(resume, repo, output, directory, expected_engine="qwen-pilot"):
    if resume["repo"] != repo:
        raise ValueError("Resume source differs from selected private result repository")
    staging = output / ".restore"
    snapshot_download(
        repo,
        repo_type="dataset",
        revision=resume["revision"],
        allow_patterns=[resume["run_name"] + "/run/**"],
        local_dir=staging,
    )
    source = staging / resume["run_name"] / "run"
    manifest = read_json(source / "manifest.json")
    if (
        expected_engine
        not in {
            "qwen-pilot",
            "qwen-role-control",
            "qwen-role-patch",
            "qwen-possessive-control",
            "qwen-confidence",
            "qwen-confidence-v2",
            "qwen-query-reference",
        }
        or manifest.get("engine") != expected_engine
        or manifest["status"] == "failed"
    ):
        raise ValueError(
            "Only interrupted/paused Qwen work can resume; failures require inspection"
        )
    if len(manifest["records"]) >= manifest["expected_jobs"]:
        raise ValueError("All outputs are already recorded; no continuation needed")
    checksums = source / "checksums.json"
    if checksums.exists():
        for name, expected in read_json(checksums).items():
            path = (source / name).resolve()
            if not path.is_relative_to(source.resolve()) or file_hash(path) != expected:
                raise ValueError("Resume artifact checksum mismatch")
    shutil.copytree(source, directory)
    # Previous derived checksums describe the old partial result. The original
    # remains intact in its pinned repository revision and previous job directory.
    (directory / "checksums.json").unlink(missing_ok=True)
    shutil.rmtree(staging)


def main():
    configure_transfer()
    config = Path(os.environ.get("STUDY_CONFIG", "configs/harness-baseline.json"))
    if config.as_posix() not in {
        "configs/harness-baseline.json",
        "configs/qwen-pilot.json",
        "configs/qwen-role-control.json",
        "configs/qwen-role-patch.json",
        "configs/qwen-possessive-control.json",
        "configs/qwen-confidence-pilot.json",
        "configs/qwen-confidence-pilot-v2.json",
        "configs/qwen-ownership-permissions-00.json",
        "configs/qwen-ownership-permissions-01.json",
        "configs/qwen-ownership-permissions-02.json",
        "configs/qwen-ownership-recovery.json",
        "configs/qwen-ownership-recovery-v2.json",
        *{f"configs/qwen-query-reference-{i:02d}.json" for i in range(6)},
    }:
        raise ValueError("Unsupported worker configuration")
    expected_hash = os.environ.get("STUDY_CONFIG_SHA256")
    if expected_hash and file_hash(config) != expected_hash:
        raise ValueError("Worker configuration differs from approved job plan")
    engine = read_json(config)["engine"]
    if engine == "qwen-query-reference":
        from self_model_study.query_reference_reporting import export
        from self_model_study.query_reference_runtime import run, validate_spec

        def load_spec(path):
            return validate_spec(read_json(path))
    elif engine == "qwen-ownership-recovery":
        from ownership_recovery import run_group as run
        from ownership_recovery import validate_spec

        def load_spec(path):
            return validate_spec(read_json(path))
    elif engine == "qwen-ownership-permissions":
        from self_model_study.ownership import run, validate_spec
        from self_model_study.ownership_reporting import export

        def load_spec(path):
            return validate_spec(read_json(path))
    elif engine in {"qwen-confidence", "qwen-confidence-v2"}:
        from self_model_study.confidence import build_plan, run, validate_spec
        from self_model_study.confidence_reporting import export

        def load_spec(path):
            spec = validate_spec(read_json(path))
            # Public, versioned data only; never execute the author's notebook.
            build_plan(spec, fetch=True)
            return spec
    elif engine == "qwen-pilot":
        from self_model_study.pilot import load_spec, run
        from self_model_study.pilot_reporting import export
    elif engine == "qwen-possessive-control":
        from self_model_study.possessive import run, validate_spec
        from self_model_study.possessive_reporting import export

        def load_spec(path):
            return validate_spec(read_json(path))
    elif engine == "qwen-role-patch":
        from self_model_study.role_patch import run, validate_spec
        from self_model_study.role_patch_reporting import export

        def load_spec(path):
            return validate_spec(read_json(path))
    elif engine == "qwen-role-control":
        from self_model_study.role_control import run, validate_spec
        from self_model_study.role_control_reporting import export

        def load_spec(path):
            return validate_spec(read_json(path))
    else:
        from self_model_study.harness import export, load_spec, run
    name, repo = os.environ["STUDY_RUN_NAME"], os.environ["STUDY_ARTIFACT_REPO"]
    api = HfApi()
    if not api.repo_info(repo, repo_type="dataset").private:
        raise RuntimeError("Refusing to upload to a public output repository")
    output = Path("/workspace/results") / name
    output.mkdir(parents=True, exist_ok=False)
    resume = json.loads(os.environ.get("STUDY_RESUME", "null"))
    write_json(
        output / "job.json",
        {
            "job_id": os.environ.get("JOB_ID"),
            "run_name": name,
            "git_commit": os.environ["STUDY_COMMIT"],
            "image": os.environ["STUDY_IMAGE"],
            "source_revision": os.environ["STUDY_SOURCE_REVISION"],
            "source_sha256": os.environ["STUDY_SOURCE_SHA256"],
            "accelerator": os.environ.get("ACCELERATOR"),
            "config": str(config),
            "config_sha256": file_hash(config),
            "resume": resume,
            "nvidia_smi": subprocess.check_output(["nvidia-smi"], text=True),
        },
    )

    checkpoint = CheckpointUploader(api, repo, output, name)

    directory = output / "run"
    if resume:
        restore_checkpoint(resume, repo, output, directory, expected_engine=engine)
    outcome = None
    try:
        outcome = run(load_spec(config), directory, checkpoint=checkpoint)
    finally:
        # Export errors and partial results too. A provider kill may bypass this;
        # earlier committed scenario checkpoints remain in the private repo.
        if (directory / "manifest.json").exists():
            archive = output / "exports" / (name + ".tar.gz")
            result = export(directory, archive)
            write_json(
                output / "export.json",
                {**result, "archive": str(archive.relative_to(output))},
            )
        checkpoint(directory)
    if outcome and outcome["status"] in {"failed", "complete_with_errors"}:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
