"""Standalone CLI entry point for the inspector."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Iterable, Optional

from .inspector import inspect_paths
from .logging import configure_logging


def _add_bool_toggle(
    parser: argparse.ArgumentParser,
    *,
    name: str,
    help_enable: str,
    help_disable: str,
    default: bool,
) -> None:
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        f"--{name}",
        dest=name,
        action="store_true",
        help=help_enable,
    )
    group.add_argument(
        f"--no-{name}",
        dest=name,
        action="store_false",
        help=help_disable,
    )
    parser.set_defaults(**{name: default})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="comfy-inspect",
        description="Inspect ComfyUI model metadata without loading tensors.",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Paths to files or directories to inspect",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively inspect directories",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    _add_bool_toggle(
        parser,
        name="summary",
        help_enable="Show condensed text output (default)",
        help_disable="Show expanded metadata section in text output",
        default=True,
    )
    parser.add_argument(
        "--hash",
        action="store_true",
        help="Compute SHA256 hashes (may be slow on large files)",
    )
    parser.add_argument(
        "--unsafe",
        action="store_true",
        help="Allow unsafe torch.load for pickle checkpoints (opt-in)",
    )
    _add_bool_toggle(
        parser,
        name="components",
        help_enable="Include per-component listings for Diffusers directories (default)",
        help_disable="Exclude per-component listings for Diffusers directories",
        default=True,
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress non-error output",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    configure_logging(args.log_level, args.quiet)

    include_components = getattr(args, "components", True)

    results = inspect_paths(
        args.paths,
        recursive=args.recursive,
        fmt=args.format,
        summary=args.summary,
        do_hash=args.hash,
        unsafe=args.unsafe,
        include_components=include_components,
    )

    if args.format == "json":
        json_results = results
    else:
        json_results = inspect_paths(
            args.paths,
            recursive=args.recursive,
            fmt="json",
            summary=args.summary,
            do_hash=args.hash,
            unsafe=args.unsafe,
            include_components=include_components,
        )

    items = json_results if isinstance(json_results, list) else [json_results]
    exit_code = (
        1
        if any(
            (
                item.get("warnings")
                for item in items
                if isinstance(item, dict) and item.get("warnings")
            )
        )
        else 0
    )

    if args.format == "json":
        payload: object
        if isinstance(json_results, list) and len(json_results) == 1:
            payload = json_results[0]
        else:
            payload = json_results
        print(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    else:
        print(results)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
