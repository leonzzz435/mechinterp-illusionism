"""Run the existing baseline once and persist committed blocks to a private HF repo."""

import os
import subprocess
from pathlib import Path

from huggingface_hub import HfApi

from self_model_study.harness import export, load_spec, run
from self_model_study.io import write_json


def main():
    name, repo = os.environ["STUDY_RUN_NAME"], os.environ["STUDY_ARTIFACT_REPO"]
    api = HfApi()
    if not api.repo_info(repo, repo_type="dataset").private:
        raise RuntimeError("Refusing to upload to a public output repository")
    output = Path("/workspace/results") / name
    output.mkdir(parents=True, exist_ok=False)
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
    try:
        run(load_spec("configs/harness-baseline.json"), directory, checkpoint=checkpoint)
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


if __name__ == "__main__":
    main()
