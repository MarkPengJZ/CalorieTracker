from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_import


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Catalog ingestion pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import", help="Import nutrition data")
    import_parser.add_argument(
        "--source",
        action="append",
        required=True,
        help="Path to source JSON file",
    )
    import_parser.add_argument(
        "--output",
        required=True,
        help="Path to output catalog JSON file",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "import":
        source_paths = [Path(path) for path in args.source]
        output_path = Path(args.output)
        count, location = run_import(source_paths, output_path)
        print(f"Imported {count} items into {location}")


if __name__ == "__main__":
    main()
