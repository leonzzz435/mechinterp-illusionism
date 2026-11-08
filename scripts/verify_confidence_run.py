"""CPU reproduction using hash-verified archived confidence source and cached tokenizer.

Rechecks all actual inputs, candidate boundaries, calibration and the complete analysis.
Checks journal/JSONL identity and regenerates figures without pretrained model inference.
"""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from review_qwen_evidence import archive_files, require


def verify(archive, checksum):
    files, actual, count = archive_files(archive, checksum)
    require(
        json.loads(files["run/manifest.json"])["protocol"] == "qwen-confidence-pilot-v2",
        "This verifier targets v2; v1 retains its documented strict probability-audit failure",
    )
    with TemporaryDirectory(prefix="confidence-verification-") as tmp:
        for name, content in files.items():
            destination = Path(tmp) / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        directory = Path(tmp) / "run"
        subprocess.run(
            [
                sys.executable,
                "-c",
                """
import json, math, sys
from pathlib import Path
from self_model_study.confidence import read_run, load_tokenizer, check_tokens
from self_model_study.confidence_analysis import summarize
from self_model_study.confidence_reporting import plots
from self_model_study.io import source_hash
directory = Path(sys.argv[1])
manifest, plan, records = read_run(directory)
assert source_hash() == manifest['provenance']['source_hash'], 'Archived source mismatch'
tokenizer = load_tokenizer(manifest['config'])
for r in records:
    check_tokens(r['result'], r['result']['input_prompt'], r['job']['row']['choices'],
                 tokenizer, manifest['config']['model']['max_length'])
report = summarize(manifest, plan, records, directory)
saved = json.loads((directory / 'analysis.json').read_text())
differences = []
def compare(a, b, path='analysis'):
    if isinstance(a, float) and isinstance(b, (int, float)):
        assert math.isclose(a, b, rel_tol=0, abs_tol=1e-10), path
        if a != b:
            differences.append(abs(a-b))
    elif isinstance(a, dict):
        assert a.keys() == b.keys(), path
        for k in a:
            compare(a[k], b[k], path+'/'+k)
    elif isinstance(a, list):
        assert len(a) == len(b), path
        for i, (x,y) in enumerate(zip(a,b)):
            compare(x,y,path+'/'+str(i))
    else:
        assert a == b, path
compare(report, saved)
plots(report, directory.parent / 'regenerated')
(directory.parent / 'verification.json').write_text(json.dumps({
    'analysis_exact': not differences,
    'analysis_maximum_float_difference': max(differences, default=0),
    'tokenizer_inputs_rechecked': len(records),
    'candidate_boundaries_rechecked': sum(len(r['result']['candidates']) for r in records),
}))
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
            rows = con.execute("SELECT id,status,payload FROM trials ORDER BY id").fetchall()
        require(
            [(r["id"], r["status"], r) for r in records]
            == [(rid, status, json.loads(payload)) for rid, status, payload in rows],
            "Journal differs from JSONL",
        )
        figures = list((Path(tmp) / "regenerated").iterdir())
        require(
            {"run/figures/" + p.name for p in figures}
            == {name for name in files if name.startswith("run/figures/")},
            "Figure inventory differs",
        )
        identical = sum(p.read_bytes() == files["run/figures/" + p.name] for p in figures)
        return {
            "archive_sha256": actual,
            "verified_payloads": count,
            **json.loads((Path(tmp) / "verification.json").read_text()),
            "journal_matches_jsonl": True,
            "figures_regenerated": len(figures),
            "figures_byte_identical": identical,
            "no_additional_model_inference": True,
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive")
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.archive, args.sha256), indent=2, sort_keys=True))
