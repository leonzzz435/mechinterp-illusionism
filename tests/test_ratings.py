import csv

import pytest

from self_model_study.io import digest
from self_model_study.ratings import read_ratings


def test_rating_coverage_agreement_and_duplicate_detection(tmp_path):
    record = {
        "trial_id": "x",
        "row": {"kind": "language", "prompt": "Context"},
        "status": "ok",
        "result": {"output": "I check."},
    }
    blind_id = digest(["blind-v1", "x"])[:20]
    rows = [
        {
            "blind_id": blind_id,
            "rater_id": rater,
            "self_reference_0_3": score,
            "monitoring_language_0_3": "1",
            "coherence_0_3": "3",
            "prompt": "Context",
            "continuation": "I check.",
        }
        for rater, score in [("reader1", "2"), ("reader2", "3")]
    ]
    path = tmp_path / "ratings.csv"

    def save(values):
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0])
            writer.writeheader()
            writer.writerows(values)

    save(rows[:1])
    assert not read_ratings(path, [record])[0]["complete"]
    save(rows)
    summary, scored = read_ratings(path, [record])
    assert summary["complete"]
    assert summary["agreement"]["self_reference_0_3"]["mean_absolute_rater_difference"] == 1.0
    assert scored[0]["result"]["self_reference_0_3"] == 2.5
    save(rows + rows[:1])
    with pytest.raises(ValueError, match="duplicate"):
        read_ratings(path, [record])
    rows[0]["continuation"] = "edited text"
    save(rows)
    with pytest.raises(ValueError, match="changed"):
        read_ratings(path, [record])
