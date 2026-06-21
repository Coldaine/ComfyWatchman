"""Legacy entry point delegating to the inspector package CLI."""

from __future__ import annotations

from typing import Iterable, Optional

from .inspector.cli import main as inspector_main


def main(argv: Optional[Iterable[str]] = None) -> int:
    return inspector_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
