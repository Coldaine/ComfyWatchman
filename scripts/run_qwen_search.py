#!/usr/bin/env python3
"""
Run a single Qwen search using the configured backend.

Example:
    ./scripts/run_qwen_search.py "better_detailed_model.safetensors" --type loras
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from comfyfixersmart.search import QwenSearch


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute a Qwen search for a given filename.")
    parser.add_argument("filename", help="Model filename to search for.")
    parser.add_argument(
        "--type",
        dest="model_type",
        default="",
        help="Optional model type hint (e.g., loras, checkpoints).",
    )
    parser.add_argument(
        "--node-type",
        dest="node_type",
        default="",
        help="Optional ComfyUI node type associated with this model.",
    )
    parser.add_argument(
        "--temp-dir",
        dest="temp_dir",
        help="Override temporary directory for Qwen artifacts.",
    )
    parser.add_argument(
        "--cache-dir",
        dest="cache_dir",
        help="Override cache directory for Qwen results.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    backend = QwenSearch(temp_dir=args.temp_dir, cache_dir=args.cache_dir)
    result = backend.search(
        {
            "filename": args.filename,
            "type": args.model_type,
            "node_type": args.node_type,
        }
    )

    print(json.dumps(result.__dict__, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    sys.exit(main())
