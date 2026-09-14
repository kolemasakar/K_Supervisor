from __future__ import annotations

import argparse
import json

from . import __version__
from .config import load_config
from .extensions import discover_extensions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="k-supervisor")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("version", help="print package version")

    config = sub.add_parser("validate-config", help="validate a JSON or TOML configuration file")
    config.add_argument("path")

    extensions = sub.add_parser("extensions", help="list installed K_Supervisor extensions")
    extensions.add_argument("--kind", choices=("agent", "capability", "project_template", "adapter"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "version":
        print(__version__)
        return 0
    if args.command == "validate-config":
        config = load_config(args.path)
        print(json.dumps(config.model_dump(mode="json"), sort_keys=True))
        return 0
    if args.command == "extensions":
        items = discover_extensions(args.kind)
        print(json.dumps([item.__dict__ for item in items], sort_keys=True))
        return 0
    raise RuntimeError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
