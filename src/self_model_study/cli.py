"""Entry points intentionally keep data validation and analysis GPU-free."""

import argparse
from pathlib import Path

from .analysis import analyze
from .config import load_config
from .data import dataset_summary
from .io import canonical, read_json
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
    validate.add_argument(
        "--tokenizer-check",
        action="store_true",
        help="Qwen only: audit pinned tokenizer on CPU, no model weights",
    )
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
            engine = read_json(args.config).get("engine")
        elif args.command in {"analyze", "export"}:
            engine = read_json(args.run / "manifest.json").get("engine")
        else:
            engine = None
        if engine == "qwen-role-patch":
            return role_patch_command(args)
        if engine == "qwen-role-control":
            return role_control_command(args)
        if engine == "qwen-pilot":
            return pilot_command(args)
        if args.command == "validate" and args.tokenizer_check:
            raise ValueError("--tokenizer-check is available only for the Qwen pilot")
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


def pilot_command(args):
    from . import pilot
    from .pilot_analysis import analyze as pilot_analyze
    from .pilot_reporting import export as pilot_export

    if args.command in {"validate", "run"}:
        spec = pilot.load_spec(args.config)
    if args.command == "validate":
        if args.freeze or args.evidence:
            raise ValueError("The Qwen development pilot cannot freeze/unlock confirmation")
        result = pilot.tokenizer_audit(spec) if args.tokenizer_check else pilot.preview(spec)
    elif args.command == "run":
        if args.max_seconds is not None:
            spec["max_seconds"] = args.max_seconds
        result = pilot.run(spec, args.out, max_jobs=args.max_jobs)
        result = {k: result[k] for k in ("run_id", "status", "expected_jobs", "synthetic")}
    elif args.command == "analyze":
        with run_lock(args.run):
            result = pilot_analyze(args.run, args.ratings)
        result = {
            k: result[k] for k in ("run_id", "status", "completed_jobs", "action_gate_passed")
        }
    else:
        result = pilot_export(args.run, args.out)
    print(canonical(result))
    return 2 if result.get("status") in {"failed", "complete_with_errors"} else 0


def role_control_command(args):
    from . import role_control
    from .role_control_analysis import analyze as control_analyze
    from .role_control_reporting import export as control_export

    if args.command in {"validate", "run"}:
        spec = role_control.validate_spec(read_json(args.config))
    if args.command == "validate":
        if args.evidence:
            raise ValueError("Role control cannot unlock the historical confirmation protocol")
        if args.freeze:
            result = role_control.prepare(spec, args.freeze, args.tokenizer_check)
        else:
            result = (
                role_control.tokenizer_audit(spec)
                if args.tokenizer_check
                else role_control.preview(spec)
            )
    elif args.command == "run":
        if args.max_seconds is not None:
            spec["max_seconds"] = args.max_seconds
        result = role_control.run(spec, args.out, max_jobs=args.max_jobs)
        result = {k: result[k] for k in ("run_id", "status", "expected_jobs", "synthetic")}
    elif args.command == "analyze":
        if args.ratings:
            raise ValueError("Role control has no generation or human-rating arm")
        with run_lock(args.run):
            result = control_analyze(args.run)
        result = {k: result[k] for k in ("run_id", "status", "completed_jobs", "decision")}
    else:
        result = control_export(args.run, args.out)
    print(canonical(result))
    return 2 if result.get("status") in {"failed", "complete_with_errors"} else 0


def role_patch_command(args):
    from . import role_patch
    from .role_patch_analysis import analyze as control_analyze
    from .role_patch_reporting import export as control_export

    if args.command in {"validate", "run"}:
        spec = role_patch.validate_spec(read_json(args.config))
    if args.command == "validate":
        if args.evidence:
            raise ValueError("Role patch cannot unlock the historical confirmation protocol")
        if args.freeze:
            result = role_patch.prepare(spec, args.freeze, args.tokenizer_check)
        else:
            result = (
                role_patch.tokenizer_audit(spec)
                if args.tokenizer_check
                else role_patch.preview(spec)
            )
    elif args.command == "run":
        if args.max_seconds is not None:
            spec["max_seconds"] = args.max_seconds
        result = role_patch.run(spec, args.out, max_jobs=args.max_jobs)
        result = {k: result[k] for k in ("run_id", "status", "expected_jobs", "synthetic")}
    elif args.command == "analyze":
        if args.ratings:
            raise ValueError("Role patch has no generation or human-rating arm")
        with run_lock(args.run):
            result = control_analyze(args.run)
        result = {k: result[k] for k in ("run_id", "status", "completed_jobs", "decision")}
    else:
        result = control_export(args.run, args.out)
    print(canonical(result))
    return 2 if result.get("status") in {"failed", "complete_with_errors"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
