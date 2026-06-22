from __future__ import annotations

import argparse
import json

from harvester.observability.logger import configure_logging, get_logger
from harvester.pipeline import Pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Disclosure Harvester")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("run-fixtures", help="Run deterministic fixture pipeline")
    subparsers.add_parser("run-live", help="Run live discovery using source-configured static or browser discovery")
    subparsers.add_parser("run-live-static", help="Run live discovery for static sources")
    return parser


def main() -> None:
    configure_logging()
    logger = get_logger("harvester.cli")
    args = build_parser().parse_args()
    logger.info("pipeline_started", extra={"metadata": {"command": args.command}})
    if args.command == "run-fixtures":
        stats = Pipeline().run_fixtures()
    elif args.command == "run-live":
        stats = Pipeline().run_live()
    elif args.command == "run-live-static":
        stats = Pipeline().run_live_static()
    else:
        raise ValueError(f"unknown command: {args.command}")
    logger.info("pipeline_finished", extra={"metadata": stats.as_dict()})
    print(json.dumps(stats.as_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
