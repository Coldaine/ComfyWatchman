#!/usr/bin/env python3
"""
Rollback Script for ComfyFixerSmart Migration

Rolls back from new system to old system in case of migration issues.

Usage:
    python scripts/rollback.py [--backup-dir PATH] [--dry-run] [--force]

Options:
    --backup-dir PATH    Path to backup directory created during migration
    --dry-run           Show what would be rolled back without making changes
    --force             Skip confirmation prompts
    --restore-config    Also restore old config (environment variables)
"""

import argparse
import shutil
import sys
from pathlib import Path
from typing import Optional, List
import json

# Add src to path to import new modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def find_backup_dirs() -> List[Path]:
    """Find available backup directories."""
    backup_dirs = []
    for item in Path(".").iterdir():
        if item.is_dir() and item.name.startswith("state_backup_"):
            backup_dirs.append(item)

    # Sort by modification time (newest first)
    backup_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return backup_dirs


def confirm_action(message: str, force: bool = False) -> bool:
    """Get user confirmation for destructive actions."""
    if force:
        return True

    response = input(f"{message} (y/N): ").strip().lower()
    return response in ['y', 'yes']


def rollback_state(backup_dir: Path, dry_run: bool = False, force: bool = False) -> bool:
    """Rollback state files from backup."""
    print("🔄 Rolling back state files...")

    state_dir = Path("state")
    backup_state_files = list(backup_dir.glob("*"))

    if not backup_state_files:
        print("❌ No state files found in backup directory")
        return False

    # Remove new state files
    new_state_files = [
        state_dir / "download_state_v2.json",
        state_dir / "state_manager_backup.json"
    ]

    for new_file in new_state_files:
        if new_file.exists():
            if dry_run:
                print(f"   Would remove: {new_file}")
            else:
                try:
                    new_file.unlink()
                    print(f"   Removed: {new_file}")
                except Exception as e:
                    print(f"   Failed to remove {new_file}: {e}")
                    return False

    # Restore old state files
    for backup_file in backup_state_files:
        target_file = state_dir / backup_file.name
        if dry_run:
            print(f"   Would restore: {backup_file} -> {target_file}")
        else:
            try:
                shutil.copy2(backup_file, target_file)
                print(f"   Restored: {backup_file} -> {target_file}")
            except Exception as e:
                print(f"   Failed to restore {backup_file}: {e}")
                return False

    return True


def rollback_config(dry_run: bool = False, force: bool = False) -> bool:
    """Rollback configuration changes."""
    print("🔄 Rolling back configuration...")

    config_file = Path("config/default.toml")

    if config_file.exists():
        if not confirm_action(f"Remove new config file {config_file}?", force):
            print("   Skipped config rollback")
            return True

        if dry_run:
            print(f"   Would remove: {config_file}")
        else:
            try:
                config_file.unlink()
                print(f"   Removed: {config_file}")
            except Exception as e:
                print(f"   Failed to remove {config_file}: {e}")
                return False

    print("ℹ️  Note: Environment variables and old hardcoded config cannot be automatically restored")
    print("   You may need to manually restore any custom environment variables")

    return True


def cleanup_backup_dirs(backup_dirs: List[Path], keep_latest: bool = True, dry_run: bool = False, force: bool = False) -> bool:
    """Clean up old backup directories."""
    if not backup_dirs:
        return True

    dirs_to_remove = backup_dirs[1:] if keep_latest else backup_dirs

    if not dirs_to_remove:
        print("ℹ️  No backup directories to clean up")
        return True

    print(f"🧹 Cleaning up {len(dirs_to_remove)} old backup directories...")

    for backup_dir in dirs_to_remove:
        if dry_run:
            print(f"   Would remove: {backup_dir}")
        else:
            try:
                shutil.rmtree(backup_dir)
                print(f"   Removed: {backup_dir}")
            except Exception as e:
                print(f"   Failed to remove {backup_dir}: {e}")
                return False

    return True


def validate_rollback() -> bool:
    """Validate that rollback was successful."""
    print("🔍 Validating rollback...")

    state_dir = Path("state")
    old_state_file = state_dir / "download_state.json"

    if not old_state_file.exists():
        print("❌ Old state file not restored")
        return False

    try:
        with open(old_state_file, 'r') as f:
            state_data = json.load(f)

        if "downloads" not in state_data:
            print("❌ Invalid old state file format")
            return False

        download_count = len(state_data["downloads"])
        print(f"✅ State file validated: {download_count} downloads")

    except Exception as e:
        print(f"❌ Failed to validate state file: {e}")
        return False

    # Check that new config is gone
    config_file = Path("config/default.toml")
    if config_file.exists():
        print("⚠️  New config file still exists - rollback may be incomplete")
    else:
        print("✅ New config file removed")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Rollback ComfyFixerSmart from new system to old system"
    )
    parser.add_argument(
        '--backup-dir',
        type=Path,
        help='Specific backup directory to use for rollback'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be rolled back without making changes'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompts and force rollback'
    )
    parser.add_argument(
        '--restore-config',
        action='store_true',
        help='Also rollback configuration changes'
    )
    parser.add_argument(
        '--cleanup-backups',
        action='store_true',
        help='Clean up old backup directories after successful rollback'
    )

    args = parser.parse_args()

    print("🔄 ComfyFixerSmart Migration Rollback")
    print("=" * 40)

    # Find backup directories
    available_backups = find_backup_dirs()

    if not available_backups:
        print("❌ No backup directories found. Cannot rollback.")
        print("   Make sure migration was run with --backup flag.")
        sys.exit(1)

    # Select backup directory
    if args.backup_dir:
        if args.backup_dir not in available_backups:
            print(f"❌ Specified backup directory not found: {args.backup_dir}")
            sys.exit(1)
        backup_dir = args.backup_dir
    else:
        backup_dir = available_backups[0]
        print(f"📦 Using latest backup: {backup_dir}")

    print(f"📋 Backup contains: {list(backup_dir.glob('*'))}")

    # Confirm rollback
    if not args.force and not args.dry_run:
        print("\n⚠️  WARNING: This will restore the old ComfyFixerSmart system.")
        print("   Any changes made since migration will be lost.")
        if not confirm_action("Are you sure you want to proceed?", args.force):
            print("Rollback cancelled.")
            return

    success = True

    # Rollback state
    if not rollback_state(backup_dir, args.dry_run, args.force):
        success = False

    # Rollback config if requested
    if args.restore_config:
        if not rollback_config(args.dry_run, args.force):
            success = False

    # Validate rollback
    if not args.dry_run and success:
        if not validate_rollback():
            success = False

    # Cleanup backups
    if args.cleanup_backups and success and not args.dry_run:
        cleanup_backup_dirs(available_backups, keep_latest=True, dry_run=args.dry_run, force=args.force)

    if success:
        print("\n✅ Rollback completed successfully!")
        print("ℹ️  You can now use the old ComfyFixerSmart system.")
        if args.restore_config:
            print("ℹ️  Remember to restore any custom environment variables if needed.")
    else:
        print("\n❌ Rollback failed or incomplete!")
        print("   Check the output above for error details.")
        sys.exit(1)


if __name__ == '__main__':
    main()