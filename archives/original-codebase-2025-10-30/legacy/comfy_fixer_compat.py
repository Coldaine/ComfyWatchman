#!/usr/bin/env python3
"""
Compatibility Wrapper for ComfyFixerSmart

Maintains backward compatibility with the old CLI interface while
transparently using the new refactored system.

This wrapper:
- Accepts old command-line arguments
- Translates them to new system calls
- Provides deprecation warnings
- Falls back gracefully if new system unavailable
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional

# Add src to path for new system
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Fallback imports
try:
    from comfyfixersmart.cli import main as new_main
    from comfyfixersmart.config import config
    NEW_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  New system not available: {e}")
    print("   Falling back to legacy system...")
    NEW_SYSTEM_AVAILABLE = False

# Legacy system path
LEGACY_SCRIPT = Path(__file__).parent / "comfy_fixer.py"


def translate_args(old_args: List[str]) -> List[str]:
    """Translate old CLI arguments to new system arguments."""
    new_args = ["comfyfixersmart.cli"]  # Module name for python -m

    i = 0
    while i < len(old_args):
        arg = old_args[i]

        if arg in ['-h', '--help']:
            new_args.append('--help')
        elif arg == '--verify-urls':
            new_args.extend(['--verify-urls'])
        elif arg == '--dry-run':
            # New system doesn't have dry-run, but we can simulate
            new_args.extend(['--no-script'])  # Close equivalent
        elif not arg.startswith('-'):
            # Positional argument (workflow file)
            new_args.append(arg)
        else:
            # Unknown argument, pass through
            new_args.append(arg)

        i += 1

    return new_args


def run_legacy_system(args: List[str]) -> int:
    """Run the legacy system as fallback."""
    if not LEGACY_SCRIPT.exists():
        print(f"❌ Legacy script not found: {LEGACY_SCRIPT}")
        return 1

    print("🔄 Running legacy system...")
    try:
        result = subprocess.run([sys.executable, str(LEGACY_SCRIPT)] + args)
        return result.returncode
    except Exception as e:
        print(f"❌ Failed to run legacy system: {e}")
        return 1


def show_migration_prompt():
    """Show migration prompt to user."""
    print("\n" + "="*60)
    print("📢 MIGRATION RECOMMENDATION")
    print("="*60)
    print("You're using the compatibility wrapper for ComfyFixerSmart.")
    print("Consider migrating to the new system for better performance:")
    print()
    print("1. Run migration: python scripts/migrate_config.py")
    print("2. Run migration: python scripts/migrate_state.py --backup")
    print("3. Validate: python scripts/validate_migration.py")
    print("4. Use new CLI: python -m comfyfixersmart.cli")
    print()
    print("See docs/migration-guide.md for detailed instructions.")
    print("="*60)


def main():
    """Main compatibility wrapper function."""
    # Parse arguments to determine if we should show migration info
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--no-migration-prompt', action='store_true',
                       help=argparse.SUPPRESS)
    parser.add_argument('--show-migration-info', action='store_true',
                       help=argparse.SUPPRESS)

    # Parse known args, leave the rest for the actual command
    known_args, remaining_args = parser.parse_known_args()

    if known_args.show_migration_info:
        show_migration_prompt()
        return 0

    # Check if new system is available
    if NEW_SYSTEM_AVAILABLE:
        try:
            # Translate arguments
            new_args = translate_args(remaining_args)

            print("🔄 Using new ComfyFixerSmart system (compatibility mode)")

            # Show migration prompt unless suppressed
            if not known_args.no_migration_prompt:
                print("💡 Tip: Consider migrating permanently for best performance")
                print("   Run with --no-migration-prompt to hide this message")

            # Run new system
            sys.argv = [sys.argv[0]] + new_args[1:]  # Replace script name
            return new_main()

        except Exception as e:
            print(f"❌ New system failed: {e}")
            print("🔄 Falling back to legacy system...")
            return run_legacy_system(remaining_args)
    else:
        print("🔄 New system not available, using legacy system")
        return run_legacy_system(remaining_args)


if __name__ == '__main__':
    sys.exit(main())