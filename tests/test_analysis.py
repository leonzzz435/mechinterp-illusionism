import numpy as np
import pytest

from self_model_study.analysis import holm, paired_deltas, paired_statistics


def test_holm_known_values():
    np.testing.assert_allclose(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])


def test_clustered_pairing_does_not_count_replicates_as_scenarios():
    rows = []
    for sid in range(4):
        for variant in range(8):
            for seed in [42, 43, 44]:
                for cid in ["baseline", "feature"]:
                    rows.append(
                        {
                            "row": {
                                "scenario_id": str(sid),
                                "id": f"{sid}:{variant}",
                                "family": "ownership",
                                "view": "self",
                            },
                            "condition": {"id": cid},
                            "seed": seed,
                            "status": "ok",
                            "result": {"correct": cid == "feature"},
                        }
                    )
    delta = paired_deltas(rows, "feature", "ownership", "correct", "self")
    assert len(delta) == 4
    assert list(delta.values()) == [1.0] * 4
    rows.pop()
    assert paired_deltas(rows, "feature", "ownership", "correct", "self") is None


def test_statistics_are_deterministic_and_flag_degeneracy():
    a = paired_statistics([-0.1, 0.2, 0.3, 0], samples=1000)
    assert a == paired_statistics([-0.1, 0.2, 0.3, 0], samples=1000)
    assert a["effect"] == pytest.approx(0.1)
    assert a["ci"][0] <= 0.1 <= a["ci"][1]
    assert paired_statistics([0] * 40, samples=1000)["degenerate_bootstrap"]
    assert not paired_statistics([0, 1], samples=1000, multiplicity=100)["tail_resolution_ok"]


def test_small_sample_fails():
    with pytest.raises(ValueError):
        paired_statistics([1])
