"""Run one selected protocol and persist committed work to a private HF repo."""

import json
import os
import shutil
import subprocess
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

from self_model_study.io import file_hash, read_json, write_json


def restore_checkpoint(resume, repo, output, directory):
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
    if manifest.get("engine") != "qwen-pilot" or manifest["status"] == "failed":
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
    config = Path(os.environ.get("STUDY_CONFIG", "configs/harness-baseline.json"))
    if config.as_posix() not in {"configs/harness-baseline.json", "configs/qwen-pilot.json"}:
        raise ValueError("Unsupported worker configuration")
    expected_hash = os.environ.get("STUDY_CONFIG_SHA256")
    if expected_hash and file_hash(config) != expected_hash:
        raise ValueError("Worker configuration differs from approved job plan")
    if read_json(config)["engine"] == "qwen-pilot":
        from self_model_study.pilot import load_spec, run
        from self_model_study.pilot_reporting import export
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

    def checkpoint(_directory):
        api.upload_folder(
            repo_id=repo,
            repo_type="dataset",
            folder_path=output,
            path_in_repo=name,
            ignore_patterns=[".lock", "*.tmp"],
            commit_message=f"Checkpoint {name}",
        )

    directory = output / "run"
    if resume:
        restore_checkpoint(resume, repo, output, directory)
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
