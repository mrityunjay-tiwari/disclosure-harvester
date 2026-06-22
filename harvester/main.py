from __future__ import annotations

import argparse
import json

from harvester.pipeline import Pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Disclosure Harvester")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("run-fixtures", help="Run deterministic fixture pipeline")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "run-fixtures":
        stats = Pipeline().run_fixtures()
        print(json.dumps(stats.as_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
