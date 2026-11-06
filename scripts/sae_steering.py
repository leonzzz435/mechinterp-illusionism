#!/usr/bin/env python3
"""Compatibility entry point for the archived pilot; shared auditable runner."""

import sys
from pathlib import Path

from self_model_study.cli import main

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    raise SystemExit(
        main(
            [
                "run",
                str(root / "configs/reference.json"),
                "--out",
                str(root / "runs/reference"),
                *sys.argv[1:],
            ]
        )
    )
