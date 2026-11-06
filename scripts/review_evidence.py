"""Offline audit of the pinned first cloud pilot; Python standard library only.

Reads the original archive without extracting or changing it. Reaggregates saved
choice likelihoods, not model inference. This does not validate the task construct.
"""

import hashlib
import json
import math
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "review/evidence/harness-cd3646dae2964bbc.tar.gz"
SHA256 = "cd2efc65d71d9f50605a6d2cb57693d189e7778cc6f59a888d24c93976d5e929"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(path=ARCHIVE):
    require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == SHA256, "Archive changed")
    with tarfile.open(path) as archive:
        members = archive.getmembers()
        require(all(m.isfile() for m in members), "Unexpected non-file archive member")
        files = {m.name: archive.extractfile(m).read() for m in members}
    require(len(files) == len(members), "Duplicate archive paths")
    checksums = json.loads(files["run/checksums.json"])
    require(
        set(files) == {"run/" + name for name in checksums} | {"run/checksums.json"},
        "Incomplete checksum inventory",
    )
    for name, expected in checksums.items():
        require(hashlib.sha256(files["run/" + name]).hexdigest() == expected, name + " changed")
    saved = json.loads(files["run/analysis.json"])
    manifest = json.loads(files["run/manifest.json"])
    plan = json.loads(files["run/plan.json"])
    require(manifest["status"] == "complete" and len(manifest["blocks"]) == 24, "Incomplete run")
    records = {}
    for block in plan["blocks"]:
        payload = json.loads(files["run/blocks/" + block["id"] + ".json"])
        samples = payload["harness"]["samples"]["context_self_" + block["family"]]
        planned = {row["id"]: row for row in block["rows"]}
        require(len(samples) == len(planned), "Incomplete block")
        for sample in samples:
            row = sample["doc"]
            require(row == planned[row["id"]] and row["id"] not in records, "Changed/duplicate row")
            scores = [response[0] for response in sample["filtered_resps"]]
            require(len(scores) == 4 and all(math.isfinite(s) for s in scores), "Invalid scores")
            prediction = max(range(4), key=scores.__getitem__)
            correct = prediction == row["gold"]
            require(sample["acc"] == correct, "Saved accuracy disagrees with likelihoods")
            records[row["id"]] = {**row, "correct": correct, "prediction": prediction}
    require(len(records) == saved["n_trials"] == saved["expected_trials"] == 768, "Wrong coverage")
    results = []
    for expected in saved["families"]:
        rows = [r for r in records.values() if r["family"] == expected["family"]]
        paired = {
            (r["scenario_id"], r["identity"], r["view"], r["rotation"], r["swapped"]): r
            for r in rows
        }
        pairs = [
            (r, paired[(r["scenario_id"], r["identity"], r["view"], r["rotation"], True)])
            for r in rows
            if not r["swapped"]
        ]
        accuracy = sum(r["correct"] for r in rows) / len(rows)
        both = sum(a["correct"] and b["correct"] for a, b in pairs) / len(pairs)
        require(accuracy == expected["accuracy"], "Family accuracy changed")
        require(both == expected["both_correct_rate"], "Paired accuracy changed")
        views = {}
        for view in ("self", "other"):
            subset = [r for r in rows if r["view"] == view]
            views[view] = sum(r["correct"] for r in subset) / len(subset)
            require(views[view] == expected["checks"]["view:" + view], "View accuracy changed")
        results.append(
            {"family": expected["family"], **views, "combined": accuracy, "both_correct": both}
        )
    return {
        "archive_sha256": SHA256,
        "verified_file_checksums": len(checksums),
        "recomputed_trials": len(records),
        "families": results,
        "note": "Offline reaggregation of saved scores; "
        "no new model evidence or construct validation.",
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
