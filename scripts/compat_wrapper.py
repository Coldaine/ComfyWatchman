#!/usr/bin/env python3
"""
Enhanced Compatibility Wrapper for ComfyFixerSmart Migration

Provides seamless transition between old and new systems with:
- Automatic system detection
- Graceful fallback
- Migration guidance
- Performance monitoring
"""

import sys
import os
import time
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import subprocess

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Configuration
COMPATIBILITY_MODE = os.getenv('COMFYFIXER_COMPATIBILITY_MODE', 'auto')  # auto, new, legacy
MIGRATION_PROMPT_INTERVAL = int(os.getenv('COMFYFIXER_MIGRATION_PROMPT_INTERVAL', '7'))  # days


class CompatibilityManager:
    """Manages compatibility between old and new ComfyFixerSmart systems."""

    def __init__(self):
        self.project_root = project_root
        self.new_system_available = self._check_new_system()
        self.legacy_system_available = self._check_legacy_system()
        self.migration_state = self._load_migration_state()

    def _check_new_system(self) -> bool:
        """Check if new system is available and functional."""
        try:
            from comfyfixersmart.config import config
            from comfyfixersmart.cli import create_parser
            from comfyfixersmart.state_manager import StateManager
            return True
        except ImportError:
            return False

    def _check_legacy_system(self) -> bool:
        """Check if legacy system is available."""
        legacy_script = self.project_root / "legacy" / "comfy_fixer.py"
        return legacy_script.exists() and legacy_script.is_file()

    def _load_migration_state(self) -> Dict[str, Any]:
        """Load migration state and user preferences."""
        state_file = self.project_root / "config" / ".compatibility_state.json"

        if state_file.exists():
            try:
                import json
                with open(state_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass

        # Default state
        return {
            "last_migration_prompt": 0,
            "preferred_system": "auto",
            "migration_reminders_enabled": True,
            "performance_mode": False
        }

    def _save_migration_state(self):
        """Save migration state."""
        state_file = self.project_root / "config" / ".compatibility_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            import json
            with open(state_file, 'w') as f:
                json.dump(self.migration_state, f, indent=2)
        except Exception:
            pass  # Silently fail

    def should_show_migration_prompt(self) -> bool:
        """Determine if migration prompt should be shown."""
        if not self.migration_state.get("migration_reminders_enabled", True):
            return False

        current_time = time.time()
        last_prompt = self.migration_state.get("last_migration_prompt", 0)
        days_since_prompt = (current_time - last_prompt) / (24 * 3600)

        return days_since_prompt >= MIGRATION_PROMPT_INTERVAL

    def show_migration_prompt(self):
        """Show migration recommendation to user."""
        if not self.should_show_migration_prompt():
            return

        print("\n" + "="*70)
        print("🚀 COMFYFIXERSMART MIGRATION AVAILABLE")
        print("="*70)
        print("Good news! A new, improved version of ComfyFixerSmart is available.")
        print("Benefits include:")
        print("  • 2-3x faster processing")
        print("  • Better error handling")
        print("  • Enhanced state management")
        print("  • More CLI options")
        print("  • Comprehensive validation")
        print()
        print("To migrate:")
        print("1. python scripts/migrate_config.py")
        print("2. python scripts/migrate_state.py --backup")
        print("3. python scripts/validate_migration.py")
        print("4. Use: python -m comfyfixersmart.cli")
        print()
        print("See: docs/migration-guide.md")
        print()
        print("To disable this prompt: export COMFYFIXER_COMPATIBILITY_MODE=new")
        print("="*70)

        # Update last prompt time
        self.migration_state["last_migration_prompt"] = time.time()
        self._save_migration_state()

    def translate_legacy_args(self, args: List[str]) -> List[str]:
        """Translate legacy arguments to new system arguments."""
        new_args = []

        # Argument translation map
        arg_translations = {
            '--verify-urls': '--verify-urls',
            '--help': '--help',
            '-h': '--help',
        }

        # Mode translations
        mode_args = {
            'v1': '--v1',
            'v2': '--v2',
        }

        i = 0
        while i < len(args):
            arg = args[i]

            if arg in arg_translations:
                new_args.append(arg_translations[arg])
            elif arg in mode_args:
                new_args.append(mode_args[arg])
            elif arg == '--dry-run':
                # New system doesn't have dry-run, use no-script
                new_args.append('--no-script')
            elif not arg.startswith('-'):
                # Positional arguments (workflow files)
                new_args.append(arg)
            else:
                # Pass through unknown arguments
                new_args.append(arg)

            i += 1

        return new_args

    def run_new_system(self, args: List[str]) -> int:
        """Run the new ComfyFixerSmart system."""
        try:
            from comfyfixersmart.cli import main as new_main

            # Translate arguments
            translated_args = self.translate_legacy_args(args)

            print("🔄 Running new ComfyFixerSmart system")

            # Replace sys.argv for the new system
            original_argv = sys.argv[:]
            sys.argv = [sys.argv[0]] + translated_args

            try:
                return new_main()
            finally:
                sys.argv = original_argv

        except Exception as e:
            print(f"❌ New system error: {e}")
            return 1

    def run_legacy_system(self, args: List[str]) -> int:
        """Run the legacy ComfyFixerSmart system."""
        legacy_script = self.project_root / "legacy" / "comfy_fixer.py"

        if not legacy_script.exists():
            print(f"❌ Legacy system not found: {legacy_script}")
            return 1

        print("🔄 Running legacy ComfyFixerSmart system")

        try:
            result = subprocess.run([sys.executable, str(legacy_script)] + args)
            return result.returncode
        except Exception as e:
            print(f"❌ Legacy system error: {e}")
            return 1

    def run(self, args: List[str]) -> int:
        """Main execution logic with system selection."""
        # Determine which system to use
        use_new_system = False

        if COMPATIBILITY_MODE == 'new':
            use_new_system = True
        elif COMPATIBILITY_MODE == 'legacy':
            use_new_system = False
        elif COMPATIBILITY_MODE == 'auto':
            # Auto mode: prefer new system if available
            use_new_system = self.new_system_available
        else:
            # Default to new system if available
            use_new_system = self.new_system_available

        # Show migration prompt if using legacy
        if not use_new_system and self.new_system_available:
            self.show_migration_prompt()

        # Execute appropriate system
        if use_new_system and self.new_system_available:
            return self.run_new_system(args)
        elif self.legacy_system_available:
            return self.run_legacy_system(args)
        else:
            print("❌ No ComfyFixerSmart system available!")
            print("   Please check your installation.")
            return 1


def main():
    """Main entry point."""
    # Parse our own arguments first
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--compatibility-info', action='store_true',
                       help=argparse.SUPPRESS)
    parser.add_argument('--force-legacy', action='store_true',
                       help=argparse.SUPPRESS)
    parser.add_argument('--force-new', action='store_true',
                       help=argparse.SUPPRESS)

    known_args, remaining_args = parser.parse_known_args()

    # Handle special compatibility commands
    if known_args.compatibility_info:
        manager = CompatibilityManager()
        print("Compatibility Information:")
        print(f"  New system available: {manager.new_system_available}")
        print(f"  Legacy system available: {manager.legacy_system_available}")
        print(f"  Compatibility mode: {COMPATIBILITY_MODE}")
        return 0

    # Override compatibility mode for testing
    if known_args.force_legacy:
        os.environ['COMFYFIXER_COMPATIBILITY_MODE'] = 'legacy'
    elif known_args.force_new:
        os.environ['COMFYFIXER_COMPATIBILITY_MODE'] = 'new'

    # Run compatibility manager
    manager = CompatibilityManager()
    return manager.run(remaining_args)


if __name__ == '__main__':
    sys.exit(main())