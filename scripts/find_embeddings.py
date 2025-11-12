#!/usr/bin/env python3
"""Detect embedding references within ComfyUI workflow files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from comfyfixersmart.scanner import WorkflowScanner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="List embedding references in workflows.")
    parser.add_argument("workflows", nargs="+", help="Path(s) to workflow JSON files")
    return parser


def summarize_embeddings(workflow_path: Path) -> List[str]:
    scanner = WorkflowScanner()
    models = scanner.extract_models_from_workflow(str(workflow_path))
    return [m.filename for m in models if m.type == "embeddings"]


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    exit_code = 0
    for workflow in args.workflows:
        path = Path(workflow)
        if not path.exists():
            print(f"⚠️  Workflow not found: {workflow}", file=sys.stderr)
            exit_code = 2
            continue

        embeddings = summarize_embeddings(path)
        print(f"{path.name}:")
        if embeddings:
            for name in embeddings:
                print(f"  - {name}")
        else:
            print("  (no embeddings detected)")

    return exit_code


if __name__ == "__main__":  # pragma: no cover - CLI entry
    sys.exit(main())
