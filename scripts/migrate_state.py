#!/usr/bin/env python3
"""
State Migration Script for ComfyFixerSmart

Migrates old state data (download_state.json) to new enhanced state format.

Usage:
    python scripts/migrate_state.py [--state-dir PATH] [--backup] [--dry-run]

Options:
    --state-dir PATH    Path to state directory (default: state)
    --backup           Create backup of old state before migration
    --dry-run          Show what would be migrated without writing files
    --force            Overwrite existing new state files
"""

import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import sys

# Add src to path to import new modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from comfywatchman.state_manager import StateManager, DownloadAttempt, DownloadStatus


def load_old_state(state_dir: Path) -> Optional[Dict[str, Any]]:
    """Load old state from download_state.json."""
    old_state_file = state_dir / "download_state.json"

    if not old_state_file.exists():
        print(f"ℹ️  No old state file found at {old_state_file}")
        return None

    try:
        with open(old_state_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load old state file: {e}")
        return None


def convert_old_state_to_new(old_state: Dict[str, Any]) -> Dict[str, Any]:
    """Convert old state format to new format."""
    new_state = {
        "version": "2.0",
        "downloads": {},
        "statistics": {
            "total_attempts": 0,
            "successful_downloads": 0,
            "failed_downloads": 0,
            "total_bytes_downloaded": 0,
            "last_updated": datetime.now().isoformat()
        },
        "migration_info": {
            "migrated_from": "1.0",
            "migration_date": datetime.now().isoformat(),
            "old_format": "simple_json"
        }
    }

    if "downloads" in old_state:
        for filename, download_info in old_state["downloads"].items():
            # Convert old download info to new DownloadAttempt format
            attempt = DownloadAttempt(
                timestamp=download_info.get("timestamp", datetime.now().isoformat()),
                filename=filename,
                status=DownloadStatus.SUCCESS if download_info.get("success", False) else DownloadStatus.FAILED,
                model_type=download_info.get("model_type"),
                node_type=download_info.get("node_type"),
                civitai_id=download_info.get("civitai_id"),
                civitai_name=download_info.get("civitai_name"),
                version_id=download_info.get("version_id"),
                download_url=download_info.get("download_url"),
                completed_at=download_info.get("completed_at"),
                file_path=download_info.get("file_path"),
                file_size=download_info.get("file_size"),
                error=download_info.get("error")
            )

            # Add to downloads dict with filename as key
            new_state["downloads"][filename] = attempt.__dict__

            # Update statistics
            new_state["statistics"]["total_attempts"] += 1
            if attempt.status == DownloadStatus.SUCCESS:
                new_state["statistics"]["successful_downloads"] += 1
                if attempt.file_size:
                    new_state["statistics"]["total_bytes_downloaded"] += attempt.file_size
            elif attempt.status == DownloadStatus.FAILED:
                new_state["statistics"]["failed_downloads"] += 1

    if "history" in old_state:
        # Convert history if it exists (though old format might not have it)
        new_state["history"] = old_state["history"]

    return new_state


def backup_old_state(state_dir: Path) -> Path:
    """Create backup of old state files."""
    backup_dir = state_dir.parent / f"state_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Copy all state files
    for file_path in state_dir.glob("*"):
        if file_path.is_file():
            shutil.copy2(file_path, backup_dir / file_path.name)

    print(f"📦 Old state backed up to {backup_dir}")
    return backup_dir


def validate_migration(old_state: Dict[str, Any], new_state: Dict[str, Any]) -> bool:
    """Validate that migration preserved all important data."""
    old_downloads = old_state.get("downloads", {})
    new_downloads = new_state.get("downloads", {})

    # Check that all old downloads are present in new state
    for filename in old_downloads:
        if filename not in new_downloads:
            print(f"❌ Missing download in new state: {filename}")
            return False

    # Check statistics
    stats = new_state.get("statistics", {})
    if stats["total_attempts"] != len(old_downloads):
        print(f"❌ Statistics mismatch: expected {len(old_downloads)} attempts, got {stats['total_attempts']}")
        return False

    print(f"✅ Migration validation passed: {len(new_downloads)} downloads migrated")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Migrate ComfyFixerSmart state from old to new format"
    )
    parser.add_argument(
        '--state-dir',
        type=Path,
        default=Path('state'),
        help='Path to state directory (default: state)'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Create backup of old state before migration'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without writing files'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing new state files'
    )

    args = parser.parse_args()

    # Ensure state directory exists
    args.state_dir.mkdir(parents=True, exist_ok=True)

    print("🔍 Loading old state...")
    old_state = load_old_state(args.state_dir)

    if not old_state:
        print("ℹ️  No old state to migrate.")
        return

    print(f"📋 Found old state with {len(old_state.get('downloads', {}))} downloads")

    print("\n🏗️  Converting to new format...")
    new_state = convert_old_state_to_new(old_state)

    print(f"📊 Migration summary:")
    stats = new_state.get("statistics", {})
    print(f"   Total attempts: {stats['total_attempts']}")
    print(f"   Successful: {stats['successful_downloads']}")
    print(f"   Failed: {stats['failed_downloads']}")
    print(f"   Total bytes: {stats['total_bytes_downloaded']}")

    # Validate migration
    if not validate_migration(old_state, new_state):
        print("❌ Migration validation failed!")
        sys.exit(1)

    if args.dry_run:
        print("\n🔍 Dry run - no files written.")
        return

    # Create backup if requested
    if args.backup:
        backup_old_state(args.state_dir)

    # Check for existing new state files
    new_state_file = args.state_dir / "download_state_v2.json"
    if new_state_file.exists() and not args.force:
        print(f"\n❌ New state file {new_state_file} already exists. Use --force to overwrite.")
        sys.exit(1)

    # Write new state file
    try:
        with open(new_state_file, 'w') as f:
            json.dump(new_state, f, indent=2)
        print(f"\n✅ State migrated successfully to {new_state_file}")
    except Exception as e:
        print(f"\n❌ Failed to write new state file: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()