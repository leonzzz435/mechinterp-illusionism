"""Reviewer can audit the actual pinned data without HF access or model dependencies."""

import importlib.util

import pytest


def load_auditor():
    spec = importlib.util.spec_from_file_location("review_evidence", "scripts/review_evidence.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pinned_cloud_evidence_reproduces_published_numbers():
    report = load_auditor().audit()
    assert report["verified_file_checksums"] == 95
    assert report["recomputed_trials"] == 768
    assert {r["family"]: r["combined"] for r in report["families"]} == {
        "ownership": 0.43359375,
        "access": 0.5078125,
        "capability": 0.4140625,
    }


def test_changed_archive_is_rejected(tmp_path):
    auditor = load_auditor()
    changed = tmp_path / "changed.tar.gz"
    changed.write_bytes(auditor.ARCHIVE.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="Archive changed"):
        auditor.audit(changed)
