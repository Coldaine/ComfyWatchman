"""
CLI for Model Metadata Inspector (DP-016)

Usage examples:
  comfywatchman-inspect file.safetensors
  comfywatchman-inspect models/ --hash --json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from .inspector import inspect_paths, results_to_json


def _print_table(results):
    # minimal fixed-width table for TTY
    headers = ["path", "ext", "format", "type", "size", "safe", "error"]
    rows = []
    for r in results:
        rows.append([
            r.path,
            r.ext,
            r.format,
            r.type_hint,
            str(r.size),
            "yes" if r.safe_to_load else "no",
            (r.error or "-")[:120],
        ])

    col_widths = [max(len(h), *(len(row[i]) for row in rows)) for i, h in enumerate(headers)]

    def fmt_row(cols):
        return "  ".join(c.ljust(col_widths[i]) for i, c in enumerate(cols))

    print(fmt_row(headers))
    print("  ".join("-" * w for w in col_widths))
    for row in rows:
        print(fmt_row(row))


def create_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="comfywatchman-inspect",
        description="Inspect model files safely (.safetensors metadata-only).",
    )
    p.add_argument("paths", nargs="+", help="Files or directories to inspect")
    p.add_argument("--hash", dest="compute_hash", action="store_true", help="Compute SHA256")
    p.add_argument("--json", dest="as_json", action="store_true", help="Output JSON")
    return p


def main(argv: List[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    paths = [Path(s) for s in args.paths]
    results = inspect_paths(paths, compute_hash=args.compute_hash)

    if args.as_json:
        print(results_to_json(results))
    else:
        _print_table(results)

    # Exit non-zero if any file had an error or was unsafe (.pth/.ckpt etc.)
    any_error = any(r.error for r in results)
    any_unsafe = any((not r.safe_to_load) for r in results)
    return 1 if (any_error or any_unsafe) else 0


if __name__ == "__main__":
    raise SystemExit(main())
