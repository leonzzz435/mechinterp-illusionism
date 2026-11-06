import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def cloud():
    pytest.importorskip("huggingface_hub")
    spec = importlib.util.spec_from_file_location("hf_jobs", "scripts/hf_jobs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def proposal():
    return {
        "namespace": "example",
        "artifact_repo": "example/mechinterp-illusionism-results",
        "commit": "a" * 40,
        "working_tree_clean": True,
        "image": "registry/image@sha256:" + "b" * 64,
        "flavor": "l4x1",
        "hard_timeout_seconds": 7200,
    }


class FakeAPI:
    def __init__(self, private=True, unknown=False):
        self.private, self.unknown = private, unknown
        self.calls = []

    def whoami(self):
        return {"name": "example"}

    def create_repo(self, *args, **kwargs):
        assert kwargs == {"repo_type": "dataset", "private": True, "exist_ok": True}

    def repo_info(self, *args, **kwargs):
        return SimpleNamespace(private=self.private, sha="c" * 40)

    def run_job(self, **kwargs):
        self.calls.append(kwargs)
        if self.unknown:
            raise OSError("fixture response lost after dispatch")
        return SimpleNamespace(id="fixture-job", url="https://huggingface.co/jobs/example/fixture")


def test_fixed_hardware_quote_rejects_unbounded_or_expensive_jobs(cloud):
    hardware = {"name": "l4x1", "unitLabel": "minute", "unitCostMicroUSD": 13333}
    assert cloud.quote_budget(hardware, "10")["max_compute_usd"] == "1.613293"
    for budget in ("0", "-1", "nan", "inf", "11", "1"):
        with pytest.raises(ValueError):
            cloud.quote_budget(hardware, budget)
    for change in (
        {"name": "a100x8"},
        {"unitLabel": "second"},
        {"unitCostMicroUSD": 1_000_000},
    ):
        with pytest.raises(ValueError):
            cloud.quote_budget({**hardware, **change}, "10")


def test_submit_secret_is_not_persisted_and_cannot_repeat(cloud, proposal, monkeypatch, tmp_path):
    monkeypatch.setattr(cloud, "git", lambda *args: "a" * 40 + "\trefs/heads/main")
    monkeypatch.setattr(
        cloud,
        "publish_source",
        lambda *args: {"source_revision": "c" * 40, "source_sha256": "e" * 64},
    )
    api = FakeAPI()
    receipt = tmp_path / "receipt.json"
    result = cloud.submit(proposal, receipt, api, "fixture-secret")
    assert result["state"] == "submitted"
    assert "fixture-secret" not in receipt.read_text()
    assert api.calls[0]["secrets"] == {"HF_TOKEN": "fixture-secret"}
    assert "HF_TOKEN" not in api.calls[0]["env"]
    assert api.calls[0]["timeout"] == 7200
    assert api.calls[0]["flavor"] == "l4x1"
    with pytest.raises(ValueError, match="already exists"):
        cloud.submit(proposal, receipt, api, "fixture-secret")
    assert len(api.calls) == 1


def test_unknown_dispatch_is_retained_and_never_retried(cloud, proposal, monkeypatch, tmp_path):
    monkeypatch.setattr(cloud, "git", lambda *args: "a" * 40 + "\trefs/heads/main")
    monkeypatch.setattr(
        cloud,
        "publish_source",
        lambda *args: {"source_revision": "c" * 40, "source_sha256": "e" * 64},
    )
    api = FakeAPI(unknown=True)
    receipt = tmp_path / "unknown.json"
    with pytest.raises(RuntimeError, match="outcome unknown"):
        cloud.submit(proposal, receipt, api, "fixture-secret")
    assert json.loads(receipt.read_text())["state"] == "submission_unknown"
    with pytest.raises(ValueError):
        cloud.submit(proposal, receipt, api, "fixture-secret")
    assert len(api.calls) == 1


def test_definite_provider_rejection_is_recorded_without_secrets(
    cloud, proposal, monkeypatch, tmp_path
):
    from requests import Response

    monkeypatch.setattr(cloud, "git", lambda *args: "a" * 40 + "\trefs/heads/main")
    monkeypatch.setattr(
        cloud,
        "publish_source",
        lambda *args: {"source_revision": "c" * 40, "source_sha256": "e" * 64},
    )

    class Rejected(FakeAPI):
        def run_job(self, **kwargs):
            response = Response()
            response.status_code = 403
            response._content = b"{}"
            raise cloud.HfHubHTTPError("Denied fixture-secret", response=response)

    receipt = tmp_path / "rejected.json"
    with pytest.raises(RuntimeError, match="HF rejected"):
        cloud.submit(proposal, receipt, Rejected(), "fixture-secret")
    assert cloud.read_json(receipt)["state"] == "submission_rejected"
    assert "fixture-secret" not in receipt.read_text()


def test_unpublished_code_public_storage_or_missing_auth_cannot_dispatch(
    cloud, proposal, monkeypatch, tmp_path
):
    monkeypatch.setattr(cloud, "git", lambda *args: "a" * 40 + "\trefs/heads/main")
    for changes, token, private in (
        ({"working_tree_clean": False}, "fixture", True),
        ({"commit": "d" * 40}, "fixture", True),
        ({}, None, True),
        ({}, "fixture", False),
    ):
        api = FakeAPI(private=private)
        with pytest.raises(ValueError):
            cloud.submit({**proposal, **changes}, tmp_path / "receipt.json", api, token)
        assert not api.calls


def test_fetch_pins_snapshot_and_verifies_artifacts(cloud, monkeypatch, tmp_path):
    state = {"artifact_repo": "example/results", "run_name": "fixture"}
    monkeypatch.setattr(cloud, "HfApi", FakeAPI)

    def download(*args, **kwargs):
        assert kwargs["revision"] == "c" * 40
        assert kwargs["allow_patterns"] == ["fixture/**"]
        folder = Path(kwargs["local_dir"]) / "fixture"
        cloud.write_json(folder / "job.json", {"fixture": True})
        cloud.write_json(folder / "run/manifest.json", {"status": "paused"})
        data = (folder / "run/manifest.json").read_bytes()
        cloud.write_json(
            folder / "run/checksums.json", {"manifest.json": hashlib.sha256(data).hexdigest()}
        )

    monkeypatch.setattr(cloud, "snapshot_download", download)
    assert cloud.fetch(state, tmp_path)["export_verified"]
    monkeypatch.setattr(cloud, "snapshot_download", lambda *args, **kwargs: None)
    (tmp_path / "fixture/run/manifest.json").write_text("corrupted")
    with pytest.raises(ValueError, match="checksum mismatch"):
        cloud.fetch(state, tmp_path)


def test_private_source_bundle_preserves_commit_and_excludes_untracked_files(
    cloud, monkeypatch, tmp_path
):
    source, clone = tmp_path / "source", tmp_path / "clone"
    source.mkdir()
    monkeypatch.setattr(cloud, "ROOT", source)
    cloud.git("init")
    (source / "program.py").write_text("print('fixture')\n")
    cloud.git("add", "program.py")
    cloud.git(
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-m",
        "fixture",
    )
    commit = cloud.git("rev-parse", "HEAD")
    (source / "local-secret.txt").write_text("not for upload")
    uploaded = {}

    def upload(**kwargs):
        uploaded.update(kwargs)
        return SimpleNamespace(oid="c" * 40)

    result = cloud.publish_source(SimpleNamespace(upload_file=upload), "example/results", commit)
    bundle = uploaded["path_or_fileobj"]
    assert result["source_sha256"] == hashlib.sha256(bundle.read_bytes()).hexdigest()
    assert result["source_revision"] == "c" * 40
    subprocess.run(["git", "clone", str(bundle), str(clone)], check=True, capture_output=True)
    assert (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=clone, text=True).strip()
        == commit
    )
    assert (clone / "program.py").exists()
    assert not (clone / "local-secret.txt").exists()
