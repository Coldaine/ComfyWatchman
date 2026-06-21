"""Lightweight logging helpers for the inspector CLI."""

from __future__ import annotations

import logging


def configure_logging(level: str = "INFO", quiet: bool = False) -> None:
    """Configure a basic logger for console output."""
    if quiet:
        level = "ERROR"

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(levelname)s %(name)s: %(message)s",
    )
