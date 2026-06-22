from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from harvester.doctor import run_doctor
from harvester.observability.logger import configure_logging, get_logger
from harvester.pipeline import Pipeline
from harvester.settings import Settings
from harvester.verify import run_verification


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Disclosure Harvester")
    parser.add_argument("--verbose", action="store_true", help="Emit structured JSON logs to stderr")
    parser.add_argument("--warehouse-path", help="Override the DuckDB warehouse path for this run")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="Check local runtime dependencies")
    subparsers.add_parser("verify", help="Run deterministic end-to-end verification")
    subparsers.add_parser("run-fixtures", help="Run deterministic fixture pipeline")
    subparsers.add_parser("run-live", help="Run live discovery using source-configured static or browser discovery")
    subparsers.add_parser("run-live-static", help="Run live discovery for static sources")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    logger = get_logger("harvester.cli")
    if args.verbose:
        configure_logging()
    if args.command == "doctor":
        print(json.dumps(run_doctor(), indent=2, sort_keys=True))
        return
    if args.command == "verify":
        print(json.dumps(run_verification(), indent=2, sort_keys=True))
        return
    if args.verbose:
        logger.info("pipeline_started", extra={"metadata": {"command": args.command}})
    settings = Settings()
    if args.warehouse_path:
        settings = replace(settings, warehouse_path=Path(args.warehouse_path))
    if args.command == "run-fixtures":
        stats = Pipeline(settings).run_fixtures()
    elif args.command == "run-live":
        stats = Pipeline(settings).run_live()
    elif args.command == "run-live-static":
        stats = Pipeline(settings).run_live_static()
    else:
        raise ValueError(f"unknown command: {args.command}")
    if args.verbose:
        logger.info("pipeline_finished", extra={"metadata": stats.as_dict()})
    print(json.dumps(stats.as_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
