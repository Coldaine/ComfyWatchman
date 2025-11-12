#!/usr/bin/env python3
"""
Add or update a known model entry in civitai_tools/config/known_models.json.

This helper validates the model against the live Civitai API, then persists
the enriched metadata so DirectIDBackend can resolve it instantly.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from comfyfixersmart.civitai_tools.direct_id_backend import DirectIDBackend


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:  # pragma: no cover - CLI guard
        raise argparse.ArgumentTypeError(f"Expected integer, got '{value}'") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Value must be positive")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Add a known model entry for instant DirectID lookups."
    )
    parser.add_argument("name", help="Human-readable model name (used for lookup key).")
    parser.add_argument("civitai_id", type=positive_int, help="Civitai model ID.")
    parser.add_argument(
        "--version-id",
        type=positive_int,
        dest="version_id",
        help="Specific version ID (optional). Defaults to latest version.",
    )
    parser.add_argument(
        "--type",
        dest="model_type",
        help="Optional model type hint (e.g., LORA, Checkpoint, VAE).",
    )
    parser.add_argument(
        "--nsfw-level",
        type=positive_int,
        dest="nsfw_level",
        help="Override NSFW level (defaults to API value).",
    )
    parser.add_argument("--notes", help="Optional notes to store with the entry.")
    parser.add_argument(
        "--auto",
        action="store_true",
        dest="auto_added",
        help="Mark the entry as auto-added (useful for automated pipelines).",
    )
    parser.add_argument(
        "--known-models-path",
        dest="known_models_path",
        help="Override path to known_models.json (defaults to civitai_tools/config/known_models.json).",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    backend = DirectIDBackend(
        known_models_path=args.known_models_path
        if args.known_models_path
        else "civitai_tools/config/known_models.json"
    )

    entry = backend.add_known_model(
        name=args.name,
        civitai_id=args.civitai_id,
        version_id=args.version_id,
        model_type=args.model_type,
        nsfw_level=args.nsfw_level,
        notes=args.notes,
        auto_added=args.auto_added,
    )

    print("✅ Known model entry stored successfully:")
    for key, value in entry.items():
        print(f"  {key}: {value}")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    sys.exit(main())
