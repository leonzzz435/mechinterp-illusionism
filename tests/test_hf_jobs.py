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
    assert cloud.quote_budget(hardware, "19")["approved_budget_usd"] == "19"
    assert cloud.quote_budget(hardware, "19")["max_compute_usd"] == "1.613293"
    for budget in ("0", "-1", "nan", "inf", "1"):
        with pytest.raises(ValueError):
            cloud.quote_budget(hardware, budget)
    for change in (
        {"name": "a100x8"},
        {"unitLabel": "second"},
        {"unitCostMicroUSD": 1_000_000},
    ):
        with pytest.raises(ValueError):
            cloud.quote_budget({**hardware, **change}, "10")


def test_explicit_qwen_configuration_and_historical_default(cloud):
    qwen = cloud.config_details("configs/qwen-pilot.json")
    assert qwen["run_limit_seconds"] == 5400 and qwen["blocks"] == 16
    assert qwen["scored_variants"] == 3072 and qwen["generated_texts"] == 160
    assert (
        qwen["config_sha256"]
        == hashlib.sha256(Path("configs/qwen-pilot.json").read_bytes()).hexdigest()
    )
    historical = cloud.config_details("configs/harness-baseline.json")
    assert historical["scored_variants"] == 768 and historical["generated_texts"] == 0
    role = cloud.config_details("configs/qwen-role-control.json")
    assert role["engine"] == "qwen-role-control" and role["blocks"] == 8
    assert role["scored_variants"] == 2048 and role["generated_texts"] == 0
    assert role["run_limit_seconds"] == 5400
    assert role["receipt_name"] == "qwen-role-control.json"
    assert len({c["receipt_name"] for c in (historical, qwen, role)}) == 3
    patch = cloud.config_details("configs/qwen-role-patch.json")
    assert patch["scored_variants"] == 11264 and patch["technical_repeats"] == 32
    assert patch["blocks"] == 8 and patch["run_limit_seconds"] == 5400
    assert patch["receipt_name"] == "qwen-role-patch.json"
    possessive = cloud.config_details("configs/qwen-possessive-control.json")
    assert possessive["scored_variants"] == 6144 and possessive["blocks"] == 16
    assert possessive["run_limit_seconds"] == 5400
    assert possessive["receipt_name"] == "qwen-possessive-control.json"
    for path in ("../elsewhere.json", "configs/development.json"):
        with pytest.raises(ValueError, match="explicitly supported"):
            cloud.config_details(path)


@pytest.mark.parametrize(
    "config,prefix",
    [
        ("qwen-pilot", "qwen-"),
        ("qwen-role-control", "qwen-role-"),
        ("qwen-role-patch", "qwen-patch-"),
        ("qwen-possessive-control", "qwen-possessive-"),
    ],
)
def test_qwen_selection_reaches_worker_without_reusing_first_receipt(
    cloud, proposal, monkeypatch, tmp_path, config, prefix
):
    monkeypatch.setattr(cloud, "git", lambda *args: "a" * 40 + "\trefs/heads/main")
    monkeypatch.setattr(
        cloud,
        "publish_source",
        lambda *args: {
            "source_revision": "c" * 40,
            "source_sha256": "e" * 64,
        },
    )
    api = FakeAPI()
    result = cloud.submit(
        {**proposal, **cloud.config_details(f"configs/{config}.json")},
        tmp_path / f"{config}.json",
        api,
        "fixture-secret",
    )
    assert result["run_name"].startswith(prefix)
    assert api.calls[0]["env"]["STUDY_CONFIG"] == f"configs/{config}.json"
    assert api.calls[0]["env"]["STUDY_CONFIG_SHA256"] == result["config_sha256"]


@pytest.mark.parametrize(
    "config", ["qwen-pilot", "qwen-role-control", "qwen-role-patch", "qwen-possessive-control"]
)
def test_qwen_worker_routes_exports_failed_runs_and_exits_nonzero(monkeypatch, tmp_path, config):
    pytest.importorskip("huggingface_hub")
    if config == "qwen-pilot":
        from self_model_study import pilot, pilot_reporting
    elif config == "qwen-possessive-control":
        from self_model_study import possessive as pilot
        from self_model_study import possessive_reporting as pilot_reporting
    elif config == "qwen-role-patch":
        from self_model_study import role_patch as pilot
        from self_model_study import role_patch_reporting as pilot_reporting
    else:
        from self_model_study import role_control as pilot
        from self_model_study import role_control_reporting as pilot_reporting
    from self_model_study.io import file_hash, write_json

    spec = importlib.util.spec_from_file_location("hf_worker", "scripts/hf_worker.py")
    worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker)
    uploads = []
    api = SimpleNamespace(
        repo_info=lambda *a, **k: SimpleNamespace(private=True),
        upload_folder=lambda **kwargs: uploads.append(kwargs),
    )
    monkeypatch.setattr(worker, "HfApi", lambda: api)
    monkeypatch.setattr(
        worker, "Path", lambda p: tmp_path if p == "/workspace/results" else Path(p)
    )
    monkeypatch.setattr(worker.subprocess, "check_output", lambda *a, **k: "fixture GPU")
    for key, value in {
        "STUDY_CONFIG": f"configs/{config}.json",
        "STUDY_CONFIG_SHA256": file_hash(f"configs/{config}.json"),
        "STUDY_RUN_NAME": "fixture",
        "STUDY_ARTIFACT_REPO": "example/results",
        "STUDY_COMMIT": "a" * 40,
        "STUDY_IMAGE": "fixture",
        "STUDY_SOURCE_REVISION": "b" * 40,
        "STUDY_SOURCE_SHA256": "c" * 64,
    }.items():
        monkeypatch.setenv(key, value)

    def fake_run(config, directory, checkpoint):
        assert config["protocol"] == pilot.PROTOCOL
        write_json(directory / "manifest.json", {"status": "failed"})
        checkpoint(directory)
        return {"status": "failed"}

    def fake_export(directory, archive):
        assert (directory / "manifest.json").exists()
        archive.parent.mkdir(parents=True)
        archive.write_bytes(b"fixture archive")
        return {"archive": str(archive), "sha256": file_hash(archive)}

    monkeypatch.setattr(pilot, "run", fake_run)
    monkeypatch.setattr(pilot_reporting, "export", fake_export)
    with pytest.raises(SystemExit) as exc:
        worker.main()
    assert exc.value.code == 2 and len(uploads) == 2
    assert (tmp_path / "fixture/export.json").exists()


@pytest.mark.parametrize(
    "config,prefix",
    [
        ("qwen-pilot", "qwen-"),
        ("qwen-role-control", "qwen-role-"),
        ("qwen-role-patch", "qwen-patch-"),
        ("qwen-possessive-control", "qwen-possessive-"),
    ],
)
def test_cloud_continuation_is_pinned_and_rejects_active_or_changed_jobs(
    cloud, proposal, tmp_path, config, prefix
):
    selected = {**proposal, **cloud.config_details(f"configs/{config}.json")}
    receipt = tmp_path / "prior.json"
    previous = {**selected, "run_name": prefix + "d" * 16, "job_id": "prior"}
    cloud.write_json(receipt, previous)
    api = FakeAPI()
    api.inspect_job = lambda **_: SimpleNamespace(status=SimpleNamespace(stage="COMPLETED"))
    resume = cloud.resume_details(receipt, selected, api)
    assert resume["revision"] == "c" * 40 and resume["run_name"] == previous["run_name"]
    api.inspect_job = lambda **_: SimpleNamespace(status=SimpleNamespace(stage="RUNNING"))
    with pytest.raises(ValueError, match="still active"):
        cloud.resume_details(receipt, selected, api)
    with pytest.raises(ValueError, match="same commit"):
        cloud.resume_details(receipt, {**selected, "commit": "f" * 40}, api)


@pytest.mark.parametrize("engine", ["qwen-pilot", "qwen-role-control", "qwen-role-patch"])
def test_worker_restores_verified_partial_snapshot_without_overwriting_source(
    monkeypatch, tmp_path, engine
):
    pytest.importorskip("huggingface_hub")
    from self_model_study.io import file_hash, read_json, write_json

    spec = importlib.util.spec_from_file_location("restore_worker", "scripts/hf_worker.py")
    worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker)
    resume = {"repo": "example/results", "revision": "c" * 40, "run_name": "qwen-" + "d" * 16}

    def download(*args, **kwargs):
        assert kwargs["revision"] == resume["revision"]
        source = Path(kwargs["local_dir"]) / resume["run_name"] / "run"
        write_json(
            source / "manifest.json",
            {
                "engine": engine,
                "status": "paused",
                "records": {"a": "b"},
                "expected_jobs": 3232,
            },
        )
        write_json(
            source / "checksums.json", {"manifest.json": file_hash(source / "manifest.json")}
        )

    monkeypatch.setattr(worker, "snapshot_download", download)
    output = tmp_path / "new-job"
    other_engine = "qwen-pilot" if engine == "qwen-role-control" else "qwen-role-control"
    with pytest.raises(ValueError, match="Only interrupted"):
        worker.restore_checkpoint(
            resume, "example/results", output, output / "run", expected_engine=other_engine
        )
    worker.restore_checkpoint(
        resume, "example/results", output, output / "run", expected_engine=engine
    )
    assert read_json(output / "run/manifest.json")["records"] == {"a": "b"}
    assert not (output / ".restore").exists()
    assert not (output / "run/checksums.json").exists()
    with pytest.raises(ValueError, match="differs"):
        worker.restore_checkpoint(resume, "different/results", output, output / "run")


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
