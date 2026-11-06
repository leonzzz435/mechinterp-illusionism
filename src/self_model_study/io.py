"""Canonical serialization, atomic artifacts and reproducibility metadata."""

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as stream:
        stream.write(canonical(value) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    tmp.replace(path)


def read_json(path):
    return json.loads(Path(path).read_text())


def source_hash():
    root = Path(__file__).parent
    return digest(
        {p.name: file_hash(p) for p in sorted(root.iterdir()) if p.suffix in {".py", ".json"}}
    )


def provenance():
    def git(*args):
        result = subprocess.run(["git", *args], capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None

    packages = sorted((d.metadata["Name"], d.version) for d in importlib.metadata.distributions())
    return {
        "git_commit": git("rev-parse", "HEAD"),
        "git_status": git("status", "--porcelain"),
        "source_hash": source_hash(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": dict(packages),
    }
