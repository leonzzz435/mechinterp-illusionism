"""Single-writer, transactional trial journal. Failures remain part of the record."""

import fcntl
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .io import canonical


@contextmanager
def run_lock(directory):
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    with (path / ".lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Another process is using this run") from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


class Journal:
    def __init__(self, directory):
        self.db = sqlite3.connect(Path(directory) / "trials.sqlite")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS trials "
            "(id TEXT PRIMARY KEY, status TEXT NOT NULL, payload TEXT NOT NULL)"
        )
        self.db.commit()

    def contains(self, trial_id):
        return (
            self.db.execute("SELECT 1 FROM trials WHERE id=?", (trial_id,)).fetchone() is not None
        )

    def put(self, trial_id, status, payload):
        with self.db:
            self.db.execute(
                "INSERT INTO trials VALUES (?, ?, ?)", (trial_id, status, canonical(payload))
            )

    def rows(self):
        return [json.loads(p) for (p,) in self.db.execute("SELECT payload FROM trials ORDER BY id")]

    def close(self):
        self.db.close()


def read_records(directory):
    path = Path(directory) / "trials.sqlite"
    if not path.exists():
        return []
    with sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True) as db:
        return [json.loads(p) for (p,) in db.execute("SELECT payload FROM trials ORDER BY id")]
