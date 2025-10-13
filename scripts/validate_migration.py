#!/usr/bin/env python3
"""
Migration Validation Script for ComfyFixerSmart

Validates that migration from old to new system was successful.

Usage:
    python scripts/validate_migration.py [--config-path PATH] [--state-dir PATH] [--comfyui-root PATH]

Options:
    --config-path PATH    Path to config file (default: config/default.toml)
    --state-dir PATH      Path to state directory (default: state)
    --comfyui-root PATH   Path to ComfyUI installation
    --verbose            Show detailed validation output
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import tomllib
import json

# Add src to path to import new modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from comfyfixersmart.config import Config
from comfyfixersmart.state_manager import StateManager


class MigrationValidator:
    """Validates migration from old to new ComfyFixerSmart system."""

    def __init__(self, config_path: Path, state_dir: Path, comfyui_root: Optional[Path] = None, verbose: bool = False):
        self.config_path = config_path
        self.state_dir = state_dir
        self.comfyui_root = comfyui_root
        self.verbose = verbose
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def log(self, message: str, level: str = "info"):
        """Log a message if verbose mode is enabled."""
        if self.verbose or level in ["error", "warning"]:
            print(f"[{level.upper()}] {message}")

    def validate_config_exists(self) -> bool:
        """Check if config file exists."""
        if not self.config_path.exists():
            self.errors.append(f"Config file not found: {self.config_path}")
            return False

        self.log(f"✅ Config file exists: {self.config_path}")
        return True

    def validate_config_format(self) -> bool:
        """Validate config file format and required fields."""
        try:
            with open(self.config_path, 'rb') as f:
                config_data = tomllib.load(f)
        except Exception as e:
            self.errors.append(f"Failed to parse config file: {e}")
            return False

        # Check required fields
        required_fields = ['output_dir', 'log_dir', 'state_dir']
        for field in required_fields:
            if field not in config_data:
                self.errors.append(f"Missing required config field: {field}")
                return False

        # Check ComfyUI root if specified
        if self.comfyui_root:
            config_comfyui_root = config_data.get('comfyui_root')
            if config_comfyui_root and Path(config_comfyui_root) != self.comfyui_root:
                self.warnings.append(f"Config ComfyUI root ({config_comfyui_root}) differs from specified ({self.comfyui_root})")

        self.log("✅ Config file format is valid")
        return True

    def validate_directories(self) -> bool:
        """Validate that required directories exist and are accessible."""
        try:
            with open(self.config_path, 'rb') as f:
                config_data = tomllib.load(f)
        except Exception:
            return False  # Already validated in validate_config_format

        dirs_to_check = [
            ('output_dir', config_data.get('output_dir', 'output')),
            ('log_dir', config_data.get('log_dir', 'log')),
            ('state_dir', config_data.get('state_dir', 'state')),
        ]

        all_valid = True
        for dir_name, dir_path in dirs_to_check:
            path = Path(dir_path)
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    self.log(f"📁 Created directory: {path}")
                except Exception as e:
                    self.errors.append(f"Cannot create {dir_name}: {path} - {e}")
                    all_valid = False
            elif not path.is_dir():
                self.errors.append(f"{dir_name} is not a directory: {path}")
                all_valid = False
            else:
                self.log(f"✅ Directory exists: {path}")

        return all_valid

    def validate_state_files(self) -> bool:
        """Validate state files exist and are properly formatted."""
        state_file_v2 = self.state_dir / "download_state_v2.json"

        if not state_file_v2.exists():
            self.warnings.append(f"New state file not found: {state_file_v2}")
            # Check for old state file
            old_state_file = self.state_dir / "download_state.json"
            if old_state_file.exists():
                self.warnings.append("Old state file still exists - migration may not have run")
            return True  # Not an error, just a warning

        # Validate new state file format
        try:
            with open(state_file_v2, 'r') as f:
                state_data = json.load(f)

            required_fields = ['version', 'downloads', 'statistics', 'migration_info']
            for field in required_fields:
                if field not in state_data:
                    self.errors.append(f"Missing required state field: {field}")
                    return False

            if state_data.get('version') != '2.0':
                self.warnings.append(f"Unexpected state version: {state_data.get('version')}")

            self.log(f"✅ State file valid with {len(state_data.get('downloads', {}))} downloads")

        except Exception as e:
            self.errors.append(f"Failed to parse state file: {e}")
            return False

        return True

    def validate_comfyui_integration(self) -> bool:
        """Validate ComfyUI integration if root is specified."""
        if not self.comfyui_root:
            self.log("ℹ️  ComfyUI root not specified, skipping integration validation")
            return True

        if not self.comfyui_root.exists():
            self.errors.append(f"ComfyUI root does not exist: {self.comfyui_root}")
            return False

        # Check for models directory
        models_dir = self.comfyui_root / "models"
        if not models_dir.exists():
            self.warnings.append(f"Models directory not found: {models_dir}")
        else:
            self.log(f"✅ ComfyUI models directory found: {models_dir}")

        # Check for workflows directory
        workflows_dir = self.comfyui_root / "user" / "default" / "workflows"
        if not workflows_dir.exists():
            self.warnings.append(f"Workflows directory not found: {workflows_dir}")
        else:
            self.log(f"✅ ComfyUI workflows directory found: {workflows_dir}")

        return True

    def validate_new_system_import(self) -> bool:
        """Validate that new system modules can be imported."""
        try:
            from comfyfixersmart.config import Config
            from comfyfixersmart.state_manager import StateManager
            from comfyfixersmart.cli import create_parser

            # Try to create config and state manager
            config = Config()
            state_manager = StateManager(config.state_dir)

            self.log("✅ New system modules import successfully")
            return True

        except ImportError as e:
            self.errors.append(f"Failed to import new system modules: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Failed to initialize new system: {e}")
            return False

    def run_validation(self) -> bool:
        """Run all validation checks."""
        self.log("🚀 Starting migration validation...")

        checks = [
            ("Config file exists", self.validate_config_exists),
            ("Config format", self.validate_config_format),
            ("Directories", self.validate_directories),
            ("State files", self.validate_state_files),
            ("ComfyUI integration", self.validate_comfyui_integration),
            ("New system import", self.validate_new_system_import),
        ]

        all_passed = True
        for check_name, check_func in checks:
            self.log(f"🔍 Running check: {check_name}")
            try:
                if not check_func():
                    all_passed = False
            except Exception as e:
                self.errors.append(f"Check '{check_name}' failed with exception: {e}")
                all_passed = False

        return all_passed

    def print_report(self):
        """Print validation report."""
        print("\n" + "="*50)
        print("MIGRATION VALIDATION REPORT")
        print("="*50)

        if not self.errors and not self.warnings:
            print("✅ ALL CHECKS PASSED - Migration appears successful!")
            return

        if self.errors:
            print(f"❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")

        if self.warnings:
            print(f"⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")

        if self.errors:
            print("\n🔧 RECOMMENDED ACTIONS:")
            print("   • Review and fix the errors listed above")
            print("   • Re-run migration scripts if needed")
            print("   • Check file permissions and paths")
        else:
            print("\n✅ Migration validation completed with warnings only.")


def main():
    parser = argparse.ArgumentParser(
        description="Validate ComfyFixerSmart migration from old to new system"
    )
    parser.add_argument(
        '--config-path',
        type=Path,
        default=Path('config/default.toml'),
        help='Path to config file (default: config/default.toml)'
    )
    parser.add_argument(
        '--state-dir',
        type=Path,
        default=Path('state'),
        help='Path to state directory (default: state)'
    )
    parser.add_argument(
        '--comfyui-root',
        type=Path,
        help='Path to ComfyUI installation for integration validation'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed validation output'
    )

    args = parser.parse_args()

    validator = MigrationValidator(
        config_path=args.config_path,
        state_dir=args.state_dir,
        comfyui_root=args.comfyui_root,
        verbose=args.verbose
    )

    success = validator.run_validation()
    validator.print_report()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()