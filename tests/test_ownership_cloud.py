import importlib
from copy import deepcopy
from types import SimpleNamespace

import pytest


@pytest.fixture
def tranche(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend("scripts")
    module = importlib.import_module("ownership_tranche")
    monkeypatch.setattr(module.hf, "ROOT", tmp_path)
    monkeypatch.setattr(module, "GUARD", tmp_path / ".hf-jobs/ownership-permissions-v1.json")

    def quote(namespace, budget, config):
        index = module.CONFIGS.index(config)
        return {
            "namespace": namespace,
            "approved_budget_usd": budget,
            "max_compute_usd": "1.613293",
            "config": config,
            "engine": "qwen-ownership-permissions",
            "commit": "a" * 40,
            "working_tree_clean": True,
            "receipt_name": f"qwen-ownership-permissions-{index:02d}.json",
        }

    monkeypatch.setattr(module.hf, "plan", quote)
    token = tmp_path / "review/ownership-permissions-inputs.json.gz"
    token.parent.mkdir()
    token.write_bytes(b"fixture")
    module.hf.write_json(
        tmp_path / "review/ownership-permissions-preflight.json",
        {"token_inputs_sha256": module.hf.hashlib.sha256(token.read_bytes()).hexdigest()},
    )
    return module


def test_aggregate_quote_blocks_over_budget_and_old_guards(tranche, monkeypatch):
    result = tranche.plan("fixture", "5")
    assert result["total_compute_ceiling_usd"] == "4.839879"
    assert result["scheduled_choices"] == 18432 and len(result["jobs"]) == 3
    for budget in ["4", "6", "0", "nan", "Infinity"]:
        with pytest.raises(ValueError):
            tranche.plan("fixture", budget)
    tranche.hf.write_json(tranche.GUARD, {"state": "submission_unknown"})
    with pytest.raises(ValueError, match="guard"):
        tranche.plan("fixture", "5")


def test_tranche_exactly_once_and_unknown_dispatch_is_not_retried(tranche, monkeypatch):
    proposal = tranche.plan("fixture", "5")
    calls = []

    def dispatch(job, path, api, token):
        calls.append(job["config"])
        if len(calls) == 2:
            raise RuntimeError("unknown server acceptance")
        return {"job_id": "one", "job_url": "https://example.test/one"}

    monkeypatch.setattr(tranche.hf, "submit", dispatch)
    api = SimpleNamespace(whoami=lambda: {"name": "fixture"})
    with pytest.raises(RuntimeError, match="unknown"):
        tranche.submit(proposal, api, "fixture-token")
    saved = tranche.hf.read_json(tranche.GUARD)
    assert saved["state"] == "stopped_inspect_individual_receipts_no_retry"
    assert len(saved["receipts"]) == 1 and len(calls) == 2
    assert saved["total_compute_ceiling_usd"] == "4.839879"
    with pytest.raises(ValueError):
        tranche.submit(proposal, api, "fixture-token")
    assert len(calls) == 2


def test_successful_tranche_has_three_unique_receipts(tranche, monkeypatch):
    proposal = tranche.plan("fixture", "5")
    calls = []

    def dispatch(job, path, api, token):
        calls.append(str(path))
        assert tranche.hf.read_json(tranche.GUARD)["state"] == "submitting"
        return {"job_id": str(len(calls)), "job_url": "https://example.test/job"}

    monkeypatch.setattr(tranche.hf, "submit", dispatch)
    result = tranche.submit(proposal, SimpleNamespace(whoami=lambda: None), "fixture-token")
    assert result["state"] == "submitted" and len(set(calls)) == 3
    assert len(result["receipts"]) == 3


def test_direct_launcher_cannot_bypass_shared_reservation(tranche):
    proposal = tranche.plan("fixture", "5")
    with pytest.raises(ValueError, match="aggregate"):
        tranche.hf.submit(proposal["jobs"][0], tranche.hf.ROOT / "a.json", None, "fixture-token")
    broken = deepcopy(proposal)
    broken["approved_total_budget_usd"] = "1"
    with pytest.raises(ValueError, match="aggregate"):
        tranche.submit(broken, None, "fixture-token")
    assert not tranche.GUARD.exists()
