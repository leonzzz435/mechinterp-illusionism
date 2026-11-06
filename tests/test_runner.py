from copy import deepcopy
from pathlib import Path

import pytest

from self_model_study.analysis import analyze
from self_model_study.backend import MockBackend
from self_model_study.config import validate_config
from self_model_study.reporting import export_run
from self_model_study.runner import claim_protocol, freeze_protocol, run
from self_model_study.storage import read_records, run_lock


@pytest.fixture
def config(config):
    # Journal integration tests need one family; dataset tests cover all three.
    config["dataset"]["families"] = ["ownership"]
    return config


def test_resume_exactly_once_and_matches_uninterrupted(config, tmp_path):
    first = tmp_path / "resume"
    config["max_jobs"] = 7
    assert run(config, first)["status"] == "paused"
    before = read_records(first)
    config["max_jobs"] = None
    resumed = run(config, first)
    assert resumed["status"] == "complete"
    assert all(r in read_records(first) for r in before)
    count = len(read_records(first))
    assert run(config, first)["completed_jobs"] == count
    other = tmp_path / "full"
    run(config, other)

    def drop_time(rows):
        return [{k: v for k, v in r.items() if k != "seconds"} for r in rows]

    assert drop_time(read_records(first)) == drop_time(read_records(other))


def test_change_of_scientific_configuration_rejected(config, tmp_path):
    config["max_jobs"] = 2
    run(config, tmp_path)
    config["seed"] += 1
    with pytest.raises(ValueError, match="configuration"):
        run(config, tmp_path)


def test_failures_are_retained_and_not_retried(config, tmp_path):
    class Failing(MockBackend):
        def evaluate(self, *args):
            raise RuntimeError("intentional fixture failure")

    run(config, tmp_path, Failing)
    failed = read_records(tmp_path)[0]
    assert failed["status"] == "error"
    run(config, tmp_path)
    assert failed in read_records(tmp_path)
    report = analyze(tmp_path)
    assert not report["scientific_results_eligible"]
    assert report["effects"] == []


def test_synthetic_runs_cannot_freeze(config, tmp_path):
    run(config, tmp_path / "mock")
    config.update(backend="torch", phase="confirmatory", split="test")
    with pytest.raises(ValueError, match="real-model"):
        freeze_protocol(config, tmp_path / "mock", tmp_path / "protocol.json")


def test_test_access_fails_before_loading_backend(config, tmp_path):
    config.update(phase="confirmatory", split="test")
    with pytest.raises(ValueError, match="frozen protocol"):
        run(config, tmp_path)
    assert not (tmp_path / "dataset.json").exists()


def test_claim_cannot_be_reused_for_another_run(tmp_path):
    path = tmp_path / "protocol.json"
    claim_protocol(path, "a")
    claim_protocol(path, "a")
    with pytest.raises(ValueError, match="another run"):
        claim_protocol(path, "b")


def test_lock_excludes_concurrent_writer(tmp_path):
    with run_lock(tmp_path):
        with pytest.raises(RuntimeError):
            with run_lock(tmp_path):
                pass


def test_export_audit_and_blinding(config, tmp_path):
    import csv
    import tarfile

    directory = tmp_path / "run"
    run(config, directory)
    bundle = tmp_path / "bundle.tar.gz"
    export_run(directory, bundle)
    with tarfile.open(bundle) as archive:
        names = archive.getnames()
        assert "run/export/trials.jsonl" in names
        assert "run/export/checksums.json" in names
        assert any(n.endswith(".svg") for n in names)
        assert any(n.endswith(".pdf") for n in names)
        assert any(n.endswith(".png") for n in names)
    ratings = list(csv.DictReader((directory / "export/blind_ratings.csv").open()))
    assert ratings
    assert "condition" not in ratings[0] and "trial_id" not in ratings[0]
    assert "SYNTHETIC" in (directory / "export/report.md").read_text()
    with pytest.raises(ValueError, match="already exists"):
        export_run(directory, bundle)


def test_journal_tamper_detected(config, tmp_path):
    import sqlite3

    run(config, tmp_path)
    with sqlite3.connect(tmp_path / "trials.sqlite") as db:
        db.execute("DELETE FROM trials WHERE id=(SELECT id FROM trials LIMIT 1)")
    with pytest.raises(ValueError, match="checksum"):
        analyze(tmp_path)


@pytest.mark.parametrize(
    "field,value", [("max_seconds", 28801), ("max_jobs", 0), ("phase", "oops")]
)
def test_config_invalid(config, field, value):
    c = deepcopy(config)
    c[field] = value
    with pytest.raises(ValueError):
        validate_config(c)


def test_configs_are_loadable():
    from self_model_study.config import load_config

    for path in Path("configs").glob("*.json"):
        if path.name == "harness-baseline.json":
            from self_model_study.harness import load_spec

            assert load_spec(path)["engine"] == "lm-eval"
            continue
        assert load_config(path)["schema_version"] == 1


def test_strength_rounding_cannot_create_duplicate_trial_ids(config):
    config["interventions"]["strengths"] = [0.0201, 0.0202]
    with pytest.raises(ValueError, match="Pilot strengths"):
        validate_config(config)
