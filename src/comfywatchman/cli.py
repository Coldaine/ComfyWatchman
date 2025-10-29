"""
CLI entry for ComfyWatchman.

Delegates to the legacy implementation during the rename transition.
"""

from typing import Optional


def main(argv: Optional[list[str]] = None) -> int:
    try:
        from comfyfixersmart.cli import main as legacy_main  # type: ignore
    except Exception as e:
        # Fallback informative error to help diagnose missing legacy code
        print("ComfyWatchman: legacy module not found (comfyfixersmart).", flush=True)
        print(f"Error: {e}", flush=True)
        return 1

    return legacy_main() if argv is None else legacy_main()  # pass-through


if __name__ == "__main__":
    raise SystemExit(main())
