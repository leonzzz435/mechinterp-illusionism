"""Positive and negative gate tests use explicitly fabricated evidence under pytest only."""

from copy import deepcopy

import numpy as np
import pytest

from self_model_study.io import canonical, digest, file_hash, provenance, write_json
from self_model_study.runner import (
    baseline_gate,
    freeze_protocol,
    jobs,
    rows_for,
    scientific_config,
    verify_protocol,
)
from self_model_study.storage import Journal


@pytest.fixture
def evidence(config, tmp_path):
    c = deepcopy(config)
    c.update(backend="torch", phase="exploratory", split="validation")
    c["dataset"].update(
        families=["ownership"],
        include_language=False,
        counts={"development": 40, "validation": 40, "test": 100},
    )
    directory = tmp_path / "fabricated-evidence"
    directory.mkdir()
    records = []
    for trial_id, row, condition, seed in jobs(c, rows_for(c)):
        records.append(
            {
                "trial_id": trial_id,
                "row": row,
                "condition": condition,
                "seed": seed,
                "status": "ok",
                "result": {"correct": True},
                "seconds": 0.0,
            }
        )
    # One transaction for test fixture construction; production commits each actual trial.
    journal = Journal(directory)
    with journal.db:
        journal.db.executemany(
            "INSERT INTO trials VALUES (?, ?, ?)",
            [(r["trial_id"], "ok", canonical(r)) for r in records],
        )
    journal.close()
    np.savez(directory / "directions.npz", dense=np.ones(8))
    write_json(
        directory / "calibration.json",
        {
            "passed": True,
            "synthetic": False,
            "median_norm": 1.0,
            "direction_hash": file_hash(directory / "directions.npz"),
        },
    )
    write_json(
        directory / "manifest.json",
        {
            "config": c,
            "config_hash": digest(scientific_config(c)),
            "status": "complete",
            "run_id": "FABRICATED-TEST-EVIDENCE",
            "provenance": provenance(),
            "assets": {"model_revision": "a" * 40, "sae_revision": "b" * 40},
            "health": {"passed": True},
            "records_hash": digest(sorted(records, key=lambda r: r["trial_id"])),
        },
    )
    return c, directory


def test_freeze_valid_evidence_and_detect_config_or_artifact_changes(evidence, tmp_path):
    config, directory = evidence
    config.update(phase="confirmatory", split="test", protocol=str(tmp_path / "frozen.json"))
    payload = freeze_protocol(config, directory, config["protocol"])
    assert verify_protocol(config)["protocol_hash"] == payload["protocol_hash"]
    changed = deepcopy(config)
    changed["interventions"]["strengths"] = [-0.05]
    with pytest.raises(ValueError, match="Configuration changed"):
        verify_protocol(changed)
    with pytest.raises(ValueError, match="already exists"):
        freeze_protocol(config, directory, config["protocol"])
    (tmp_path / "frozen.artifacts/directions.npz").write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum"):
        verify_protocol(config)


def test_unvalidated_condition_rejected(evidence, tmp_path):
    config, directory = evidence
    config.update(phase="confirmatory", split="test")
    config["interventions"]["strengths"] = [-0.05]
    with pytest.raises(ValueError, match="lack single-condition"):
        freeze_protocol(config, directory, tmp_path / "invalid.json")


def test_baseline_gate_catches_answer_position_shortcut(config):
    records = []
    config["phase"] = "baseline"
    for trial_id, row, condition, seed in jobs(config, rows_for(config)):
        if row["kind"] == "choice":
            records.append(
                {
                    "trial_id": trial_id,
                    "row": row,
                    "condition": condition,
                    "status": "ok",
                    "result": {"correct": row["expected"] == "A"},
                }
            )
    gates = baseline_gate(config, records)
    assert not any(g["passed"] for g in gates.values())
