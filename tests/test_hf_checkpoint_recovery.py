import importlib
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import create_autospec

import pytest
from requests import HTTPError, Response

from self_model_study.io import digest, file_hash, read_json, write_json


@pytest.fixture
def modules(monkeypatch):
    monkeypatch.syspath_prepend("scripts")
    worker = importlib.import_module("hf_worker")
    # Restore global hub state/environment after every test.
    monkeypatch.setattr(worker.constants, "HF_HUB_DISABLE_XET", False)
    monkeypatch.setenv("HF_HUB_DISABLE_XET", "0")
    monkeypatch.setattr(worker.random, "uniform", lambda *args: 0)
    return worker, importlib.import_module("ownership_recovery")


def http_error(status, retry_after=None):
    response = Response()
    response.status_code = status
    if retry_after is not None:
        response.headers["Retry-After"] = retry_after
    return HTTPError("fixture upload", response=response)


def test_upload_retries_honors_header_serializes_and_skips_unchanged(modules, tmp_path):
    worker, _ = modules
    calls, waits = [], []
    write_json(tmp_path / "run/manifest.json", {"records": 384})

    def upload(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise http_error(429, "90")
        return SimpleNamespace(oid="saved")

    # Match the installed SDK's real public signature, rather than accepting any kwargs.
    api = create_autospec(worker.HfApi, instance=True, spec_set=True)
    api.create_commit.side_effect = upload
    uploader = worker.CheckpointUploader(api, "private/data", tmp_path, "run", sleep=waits.append)
    uploader(tmp_path)
    uploader(tmp_path)  # runner finally with the same committed records
    assert len(calls) == 2 and waits == [90]
    assert all(c["num_threads"] == 1 for c in calls)
    assert all(op.path_in_repo.startswith("run/") for c in calls for op in c["operations"])
    from huggingface_hub.utils._runtime import is_xet_available

    assert not is_xet_available()
    write_json(tmp_path / "run/manifest.json", {"records": 768})
    uploader(tmp_path)
    assert len(calls) == 3
    assert [e["state"] for e in read_json(tmp_path / "transport.json")] == [
        "retry",
        "uploaded",
        "uploaded",
    ]


@pytest.mark.parametrize("error", [http_error(401), http_error(403), ValueError("oracle")])
def test_permanent_failure_is_not_retried_by_finally(modules, tmp_path, error):
    worker, _ = modules
    calls = []

    def upload(**kwargs):
        calls.append(kwargs)
        raise error

    uploader = worker.CheckpointUploader(
        SimpleNamespace(create_commit=upload),
        "private/data",
        tmp_path,
        "run",
        sleep=lambda _: pytest.fail("slept"),
    )
    for _ in range(3):
        with pytest.raises(type(error)):
            uploader(tmp_path)
    assert len(calls) == 1


def test_retry_budget_is_shared_and_xet_429_is_recognized(modules, tmp_path):
    worker, _ = modules
    calls, waits = [], []
    error = ConnectionError(
        "Rate limited: Request error: HTTP status client error (429 Too Many Requests)"
    )

    def upload(**kwargs):
        calls.append(kwargs)
        raise error

    uploader = worker.CheckpointUploader(
        SimpleNamespace(create_commit=upload),
        "private/data",
        tmp_path,
        "run",
        sleep=waits.append,
        max_retry_sleep=80,
    )
    with pytest.raises(ConnectionError):
        uploader(tmp_path)
    assert waits == [30] and len(calls) == 2
    with pytest.raises(ConnectionError):
        uploader(tmp_path)
    assert len(calls) == 2


def test_retry_after_cannot_exceed_transfer_budget(modules, tmp_path):
    worker, _ = modules

    def upload(**kwargs):
        raise http_error(429, "1200")

    uploader = worker.CheckpointUploader(
        SimpleNamespace(create_commit=upload),
        "private/data",
        tmp_path,
        "run",
        sleep=lambda _: pytest.fail("slept"),
    )
    with pytest.raises(HTTPError):
        uploader(tmp_path)


@pytest.mark.parametrize("status", [429, 503, 403])
def test_real_sdk_lfs_error_wrapper_preserves_retry_classification(
    modules, monkeypatch, tmp_path, status
):
    worker, _ = modules
    from huggingface_hub import CommitOperationAdd, _commit_api

    file = tmp_path / "checkpoint.bin"
    file.write_bytes(b"fixture")
    operation = CommitOperationAdd(path_in_repo="run/checkpoint.bin", path_or_fileobj=file)
    attempts, waits = [], []

    def transfer(**kwargs):
        attempts.append(kwargs)
        if len(attempts) == 1 or status == 403:
            raise http_error(status, "90")

    monkeypatch.setattr(_commit_api, "lfs_upload", transfer)

    def commit(**kwargs):
        # Exercise the pinned library's actual wrapping, not an invented mock error.
        _commit_api._upload_lfs_files(
            actions=[{"oid": "fixture", "actions": {"upload": {}}}],
            oid2addop={"fixture": operation},
            headers={},
            num_threads=1,
        )

    uploader = worker.CheckpointUploader(
        SimpleNamespace(create_commit=commit), "private/data", tmp_path, "run", sleep=waits.append
    )
    if status == 403:
        with pytest.raises(RuntimeError):
            uploader(tmp_path)
        assert len(attempts) == 1 and waits == []
    else:
        uploader(tmp_path)
        assert len(attempts) == 2 and waits == [90]


def test_recovery_changes_only_copy_and_rejects_trial_failure(modules, monkeypatch, tmp_path):
    _, recovery = modules
    from self_model_study import ownership
    from self_model_study.io import source_hash

    source = tmp_path / "original"
    manifest = {
        "status": "failed",
        "provenance": {"source_hash": source_hash()},
        "config": {"block_index": 0},
        "expected_jobs": 2,
        "run_id": "fixture",
    }
    records = [{"status": "ok", "result": {"selected_command": "mark_violet"}}]
    write_json(source / "manifest.json", manifest)
    write_json(
        source / "error.json",
        {
            "type": "ConnectionError",
            "message": "Rate limited: Request error: HTTP status client error "
            "(429 Too Many Requests), "
            "domain: https://cas-server-direct.xethub.hf.co/v1/xorbs/fixture",
        },
    )
    write_json(source / "checksums.json", {"manifest.json": file_hash(source / "manifest.json")})
    expected = {
        "block_index": 0,
        "record_count": 1,
        "expected_jobs": 2,
        "manifest_sha256": file_hash(source / "manifest.json"),
        "error_sha256": file_hash(source / "error.json"),
        "records_hash": digest(records),
    }
    monkeypatch.setattr(ownership, "read_run", lambda _: (deepcopy(manifest), {}, records))
    recovery.prepare_resume(source, tmp_path / "resumed", expected)
    assert read_json(source / "manifest.json")["status"] == "failed"
    assert read_json(tmp_path / "resumed/manifest.json")["status"] == "paused"
    assert (source / "checksums.json").exists()
    assert not (tmp_path / "resumed/checksums.json").exists()
    assert read_json(tmp_path / "resumed/recovery/original-manifest.json") == manifest
    records[0]["status"] = "error"
    # Even an internally consistent new record hash cannot clear a model failure.
    with pytest.raises(ValueError, match="upload-only"):
        recovery.audit_snapshot(source, {**expected, "records_hash": digest(records)})


def test_recovery_pin_and_limits_are_validated(modules):
    _, recovery = modules
    spec = read_json("configs/qwen-ownership-recovery.json")
    assert recovery.validate_spec(spec) == spec
    for key, value in [
        ("max_seconds", 5400),
        ("hard_timeout_seconds", 7200),
        ("artifact_revision", "main"),
        ("blocks", spec["blocks"][:1]),
    ]:
        with pytest.raises(ValueError):
            recovery.validate_spec({**spec, key: value})


def test_real_journal_continuation_preserves_existing_selection(modules, tmp_path):
    _, recovery = modules
    from self_model_study import ownership
    from self_model_study.storage import read_records

    class Fake:
        def choice(self, prompt, choices, format_name):
            return {
                "status": "ok",
                "selected_command": choices[0],
                "candidates": [
                    {
                        "command": c,
                        "log_likelihood": -float(i + 1),
                        "token_ids": [i],
                        "token_count": 1,
                    }
                    for i, c in enumerate(choices)
                ],
            }

    def factory(_):
        return Fake(), {"synthetic": True}

    source = tmp_path / "original"
    config = ownership.configuration(0)
    manifest = ownership.run(config, source, max_jobs=1, backend_factory=factory)
    original = read_records(source)
    manifest["status"] = "failed"
    write_json(source / "manifest.json", manifest)
    write_json(
        source / "error.json",
        {
            "type": "ConnectionError",
            "message": "Rate limited: Request error: HTTP status client error "
            "(429 Too Many Requests), "
            "domain: https://cas-server-direct.xethub.hf.co/v1/xorbs/fixture",
        },
    )
    expected = {
        "block_index": 0,
        "record_count": 1,
        "expected_jobs": 6144,
        "manifest_sha256": file_hash(source / "manifest.json"),
        "error_sha256": file_hash(source / "error.json"),
        "records_hash": digest(original),
    }
    target = tmp_path / "continuation"
    recovery.prepare_resume(source, target, expected)
    ownership.run(config, target, max_jobs=1, backend_factory=factory)
    continued = read_records(target)
    assert len(continued) == 2 and original[0] in continued
    assert len({r["id"] for r in continued}) == 2
    assert read_records(source) == original
    assert read_json(source / "manifest.json")["status"] == "failed"


def test_recovery_quote_is_one_job_for_only_missing_trials(modules, monkeypatch):
    cloud = importlib.import_module("hf_jobs")
    hardware = {"name": "l4x1", "unitLabel": "minute", "unitCostMicroUSD": 13333}
    monkeypatch.setattr(
        cloud,
        "get_session",
        lambda: SimpleNamespace(
            get=lambda *a, **k: SimpleNamespace(
                raise_for_status=lambda: None, json=lambda: [hardware]
            )
        ),
    )
    monkeypatch.setattr(cloud, "git", lambda *args: "" if args[0] == "status" else "a" * 40)
    proposal = cloud.plan("zett13", "0.62", "configs/qwen-ownership-recovery.json")
    assert proposal["hard_timeout_seconds"] == 2700
    assert proposal["run_limit_seconds"] == 1800
    assert proposal["max_compute_usd"] == "0.613318"
    assert proposal["scored_variants"] == 3456
    assert proposal["receipt_name"] == "qwen-ownership-recovery.json"
    with pytest.raises(ValueError):
        cloud.plan("zett13", "0.60", "configs/qwen-ownership-recovery.json")


@pytest.mark.parametrize("stop_first", [False, True])
def test_recovery_group_runs_sequentially_and_stops_on_model_failure(
    modules, monkeypatch, tmp_path, stop_first
):
    _, recovery = modules
    from self_model_study import ownership, ownership_reporting

    spec = read_json("configs/qwen-ownership-recovery.json")
    calls, audited, prepared, exports = [], [], [], []

    def download(*args, **kwargs):
        assert kwargs["revision"] == spec["artifact_revision"]
        assert kwargs["max_workers"] == 1
        kwargs["local_dir"].mkdir()

    def prepare(source, target, expected):
        assert len(audited) == 3  # No GPU call before all source audits.
        prepared.append(expected["block_index"])
        target.mkdir()

    def run(config, target, checkpoint):
        assert prepared == [0, 1, 2]
        index = config["block_index"]
        assert config == {**ownership.configuration(index), "max_seconds": config["max_seconds"]}
        assert 0 < config["max_seconds"] <= 1800
        calls.append(index)
        return {
            "status": "failed" if stop_first else "complete",
            "records": dict.fromkeys(range(6144)),
        }

    monkeypatch.setattr(recovery, "snapshot_download", download)
    monkeypatch.setattr(
        recovery, "audit_snapshot", lambda path, b: audited.append(b["block_index"])
    )
    monkeypatch.setattr(recovery, "prepare_resume", prepare)
    monkeypatch.setattr(ownership, "run", run)
    monkeypatch.setattr(ownership_reporting, "export", lambda path, out: exports.append(path))
    monkeypatch.setattr(ownership_reporting, "analyze_tranche", lambda *args: None)
    outcome = recovery.run_group(spec, tmp_path / "run", checkpoint=lambda _: None)
    assert calls == ([0] if stop_first else [0, 1, 2])
    assert len(exports) == len(calls)
    assert outcome["status"] == ("failed" if stop_first else "complete")
    if not stop_first:
        assert outcome["new_records"] == 3456 and outcome["original_records"] == 14976


def test_worker_dispatches_recovery_without_requiring_single_run_manifest(
    modules, monkeypatch, tmp_path
):
    worker, recovery = modules
    uploads = []
    monkeypatch.setattr(
        worker,
        "HfApi",
        lambda: SimpleNamespace(
            repo_info=lambda *args, **kwargs: SimpleNamespace(private=True),
            create_commit=lambda **kwargs: uploads.append(kwargs),
        ),
    )
    monkeypatch.setattr(
        worker, "Path", lambda p: tmp_path if p == "/workspace/results" else Path(p)
    )
    monkeypatch.setattr(worker.subprocess, "check_output", lambda *args, **kwargs: "fixture GPU")
    for key, value in {
        "STUDY_CONFIG": "configs/qwen-ownership-recovery.json",
        "STUDY_CONFIG_SHA256": file_hash("configs/qwen-ownership-recovery.json"),
        "STUDY_RUN_NAME": "recovery-fixture",
        "STUDY_ARTIFACT_REPO": "example/results",
        "STUDY_COMMIT": "a" * 40,
        "STUDY_IMAGE": "fixture",
        "STUDY_SOURCE_REVISION": "b" * 40,
        "STUDY_SOURCE_SHA256": "c" * 64,
    }.items():
        monkeypatch.setenv(key, value)

    def run(spec, directory, checkpoint):
        write_json(directory / "recovery-state.json", {"status": "complete"})
        checkpoint(directory)
        return {"status": "complete"}

    monkeypatch.setattr(recovery, "run_group", run)
    worker.main()
    assert len(uploads) == 1  # Identical final checkpoint is skipped.
    assert read_json(tmp_path / "recovery-fixture/run/recovery-state.json")["status"] == "complete"
