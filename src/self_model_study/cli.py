"""Entry points intentionally keep data validation and analysis GPU-free."""

import argparse
from pathlib import Path

from .analysis import analyze
from .config import load_config
from .data import dataset_summary
from .io import canonical
from .reporting import export_run
from .runner import expected_jobs, freeze_protocol, rows_for, run, verify_protocol
from .storage import run_lock


def main(argv=None):
    parser = argparse.ArgumentParser(prog="self-study")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser(
        "validate", help="Offline validation or freeze a confirmation protocol"
    )
    validate.add_argument("config", type=Path)
    validate.add_argument("--freeze", type=Path)
    validate.add_argument("--evidence", type=Path)
    execute = commands.add_parser("run", help="Start/resume a bounded, journaled run")
    execute.add_argument("config", type=Path)
    execute.add_argument("--out", required=True, type=Path)
    execute.add_argument(
        "--max-jobs", type=int, help="Per-invocation smoke limit; scientific config unchanged"
    )
    execute.add_argument("--max-seconds", type=int)
    analysis = commands.add_parser(
        "analyze", help="Produce scenario-level estimates from recorded trials"
    )
    analysis.add_argument("run", type=Path)
    analysis.add_argument("--ratings", type=Path, help="Completed combined blind-rating CSV")
    export = commands.add_parser(
        "export", help="Render reports/figures and package an auditable archive"
    )
    export.add_argument("run", type=Path)
    export.add_argument("--out", required=True, type=Path)
    design = commands.add_parser(
        "design", help="Export the CPU-only action-task draft; no model run"
    )
    design.add_argument("--out", required=True, type=Path)
    design.add_argument("--seed", type=int, default=1729)
    design.add_argument("--scenarios", type=int, default=40)
    args = parser.parse_args(argv)
    try:
        if args.command in {"validate", "run"}:
            config = load_config(args.config)
        if args.command == "validate":
            if args.freeze:
                if not args.evidence:
                    parser.error("--freeze requires --evidence")
                result = freeze_protocol(config, args.evidence, args.freeze)
            elif config["phase"] == "confirmatory":
                # Do not materialize held-out prompts merely to preview an unsealed config.
                if config["protocol"] and Path(config["protocol"]).exists():
                    verify_protocol(config)
                result = {
                    "valid": True,
                    "test_data": "sealed until run with frozen protocol",
                    "requires_freeze": True,
                }
            else:
                rows = rows_for(config)
                result = {
                    "valid": True,
                    "dataset": dataset_summary(rows),
                    "planned_jobs": expected_jobs(config, rows),
                    "backend": config["backend"],
                    "max_seconds": config["max_seconds"],
                }
        elif args.command == "run":
            from .config import validate_config

            for field in ("max_jobs", "max_seconds"):
                if getattr(args, field) is not None:
                    config[field] = getattr(args, field)
            validate_config(config)
            result = run(config, args.out)
            print(
                canonical(
                    {k: result[k] for k in ("run_id", "status", "completed_jobs", "expected_jobs")}
                )
            )
            return (
                0
                if result["status"] in {"complete", "paused", "interrupted", "paused_calibration"}
                else 2
            )
        elif args.command == "analyze":
            with run_lock(args.run):
                result = analyze(args.run, args.ratings)
            result = {k: result[k] for k in ("run_id", "status", "complete", "errors", "synthetic")}
        elif args.command == "design":
            from .action_task import export_design

            result = export_design(args.out, args.seed, args.scenarios)
        else:
            result = export_run(args.run, args.out)
        print(canonical(result))
        return 0
    except (ValueError, RuntimeError, OSError, ImportError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
