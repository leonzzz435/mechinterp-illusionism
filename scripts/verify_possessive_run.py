"""Reproduce the pinned wording-control analysis and figures on CPU, without inference.

Requires eval extras and the pinned tokenizer already in the local HF cache. The
checksum-verified archived source is used, so later package changes cannot change history.
"""

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from review_possessive_evidence import ARCHIVE, SHA256
from review_qwen_evidence import archive_files, require


def verify():
    files, _, count = archive_files(ARCHIVE, SHA256)
    with TemporaryDirectory(prefix="possessive-verification-") as tmp:
        for name, data in files.items():
            dest = Path(tmp) / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        directory = Path(tmp) / "run"
        subprocess.run(
            [
                sys.executable,
                "-c",
                """
import json, sys
from pathlib import Path
from self_model_study.possessive import read_run
from self_model_study.possessive_analysis import summarize
from self_model_study.possessive_reporting import plots
from self_model_study.io import source_hash
directory = Path(sys.argv[1])
# read_run also checks all actual rendered inputs and candidate token boundaries.
manifest, plan, records = read_run(directory)
assert source_hash() == manifest['provenance']['source_hash'], 'Archived source mismatch'
report = summarize(manifest, plan, records)
assert report == json.loads((directory / 'analysis.json').read_text()), 'Analysis mismatch'
plots(report, directory.parent / 'regenerated')
""",
                str(directory),
            ],
            cwd=tmp,
            env={
                **os.environ,
                "PYTHONPATH": str(directory / "source"),
                "HF_HUB_OFFLINE": "1",
                "TRANSFORMERS_OFFLINE": "1",
                "OMP_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1",
                "OPENBLAS_NUM_THREADS": "1",
            },
            check=True,
        )
        records = [json.loads(line) for line in files["run/records.jsonl"].splitlines()]
        with sqlite3.connect(f"file:{directory}/trials.sqlite?mode=ro", uri=True) as con:
            journal = con.execute("SELECT id,status,payload FROM trials ORDER BY id").fetchall()
        require(
            [(r["id"], r["status"], r) for r in sorted(records, key=lambda r: r["id"])]
            == [(rid, status, json.loads(payload)) for rid, status, payload in journal],
            "SQLite differs from JSONL",
        )
        figures = list((Path(tmp) / "regenerated").iterdir())
        require(len(figures) == 12, "Unexpected figure inventory")
        for figure in figures:
            require(
                figure.read_bytes() == files["run/figures/" + figure.name],
                "Figure differs from archived rendering: " + figure.name,
            )
        manifest = json.loads(files["run/manifest.json"])
        return {
            "archive_sha256": SHA256,
            "verified_payloads": count,
            "local_frozen_analysis_exactly_matches_cloud": True,
            "journal_matches_jsonl": True,
            "tokenizer_inputs_rechecked": len(records),
            "candidate_boundaries_rechecked": 4 * len(records),
            "matched_your_the_pairs": 2048,
            "figures_byte_identical": len(figures),
            "source_hash": manifest["provenance"]["source_hash"],
            "no_additional_model_inference": True,
        }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
