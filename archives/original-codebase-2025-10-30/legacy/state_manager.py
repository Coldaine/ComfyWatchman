#!/usr/bin/env python3
"""
State Manager for ComfyFixerSmart
Tracks download attempts, successes, and failures to prevent re-downloading

Maintains a JSON database of:
- Models attempted to download
- Download success/failure status
- File locations and sizes
- Timestamps
"""

import json
import os
from datetime import datetime
from pathlib import Path

STATE_FILE = "state/download_state.json"

def ensure_state_dir():
    """Ensure state directory exists"""
    os.makedirs("state", exist_ok=True)


def load_state():
    """Load download state from JSON file"""
    ensure_state_dir()

    if not os.path.exists(STATE_FILE):
        return {
            "downloads": {},  # filename -> download info
            "history": []     # chronological list of attempts
        }

    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        # If corrupted, return empty state
        return {"downloads": {}, "history": []}


def save_state(state):
    """Save download state to JSON file"""
    ensure_state_dir()

    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def mark_download_attempted(filename, model_info, civitai_info=None):
    """
    Mark that a download was attempted

    Args:
        filename: Model filename
        model_info: Dict with type, node_type
        civitai_info: Optional dict with civitai_id, version_id, download_url
    """
    state = load_state()

    attempt = {
        "timestamp": datetime.now().isoformat(),
        "filename": filename,
        "status": "attempted",
        "model_type": model_info.get('type'),
        "node_type": model_info.get('node_type')
    }

    if civitai_info:
        attempt.update({
            "civitai_id": civitai_info.get('civitai_id'),
            "civitai_name": civitai_info.get('civitai_name'),
            "version_id": civitai_info.get('version_id'),
            "download_url": civitai_info.get('download_url')
        })

    # Add to history
    state['history'].append(attempt)

    # Update downloads dict
    if filename not in state['downloads']:
        state['downloads'][filename] = []
    state['downloads'][filename].append(attempt)

    save_state(state)


def mark_download_success(filename, file_path, file_size):
    """
    Mark that a download succeeded

    Args:
        filename: Model filename
        file_path: Absolute path where file was saved
        file_size: Size of downloaded file in bytes
    """
    state = load_state()

    # Update most recent attempt for this filename
    if filename in state['downloads'] and state['downloads'][filename]:
        state['downloads'][filename][-1].update({
            "status": "success",
            "completed_at": datetime.now().isoformat(),
            "file_path": str(file_path),
            "file_size": file_size
        })

        # Also update history
        for entry in reversed(state['history']):
            if entry['filename'] == filename and entry['status'] == 'attempted':
                entry.update({
                    "status": "success",
                    "completed_at": datetime.now().isoformat(),
                    "file_path": str(file_path),
                    "file_size": file_size
                })
                break

    save_state(state)


def mark_download_failed(filename, error_message):
    """
    Mark that a download failed

    Args:
        filename: Model filename
        error_message: Error description
    """
    state = load_state()

    # Update most recent attempt for this filename
    if filename in state['downloads'] and state['downloads'][filename]:
        state['downloads'][filename][-1].update({
            "status": "failed",
            "failed_at": datetime.now().isoformat(),
            "error": error_message
        })

        # Also update history
        for entry in reversed(state['history']):
            if entry['filename'] == filename and entry['status'] == 'attempted':
                entry.update({
                    "status": "failed",
                    "failed_at": datetime.now().isoformat(),
                    "error": error_message
                })
                break

    save_state(state)


def get_download_status(filename):
    """
    Get the status of a model download

    Returns:
        None if never attempted
        'success' if successfully downloaded
        'failed' if failed
        'attempted' if attempted but not completed
    """
    state = load_state()

    if filename not in state['downloads']:
        return None

    attempts = state['downloads'][filename]
    if not attempts:
        return None

    # Return status of most recent attempt
    return attempts[-1].get('status')


def get_successful_downloads():
    """
    Get dict of all successfully downloaded models

    Returns:
        Dict mapping filename -> download info
    """
    state = load_state()
    successful = {}

    for filename, attempts in state['downloads'].items():
        if attempts:
            latest = attempts[-1]
            if latest.get('status') == 'success':
                successful[filename] = latest

    return successful


def get_failed_downloads():
    """
    Get list of models that failed to download

    Returns:
        List of filenames
    """
    state = load_state()
    failed = []

    for filename, attempts in state['downloads'].items():
        if attempts:
            latest = attempts[-1]
            if latest.get('status') == 'failed':
                failed.append(filename)

    return failed


def was_recently_attempted(filename, hours=24):
    """
    Check if a download was attempted recently

    Args:
        filename: Model filename
        hours: How many hours to consider "recent"

    Returns:
        True if attempted within the time window
    """
    state = load_state()

    if filename not in state['downloads']:
        return False

    attempts = state['downloads'][filename]
    if not attempts:
        return False

    latest = attempts[-1]
    timestamp_str = latest.get('timestamp')
    if not timestamp_str:
        return False

    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600
        return age_hours < hours
    except Exception:
        return False


def get_stats():
    """
    Get statistics about downloads

    Returns:
        Dict with success/failed/attempted counts
    """
    state = load_state()

    stats = {
        "total_unique_models": len(state['downloads']),
        "total_attempts": len(state['history']),
        "successful": 0,
        "failed": 0,
        "pending": 0
    }

    for filename, attempts in state['downloads'].items():
        if attempts:
            status = attempts[-1].get('status')
            if status == 'success':
                stats['successful'] += 1
            elif status == 'failed':
                stats['failed'] += 1
            elif status == 'attempted':
                stats['pending'] += 1

    return stats


def clear_failed():
    """
    Clear all failed download records so they can be retried
    """
    state = load_state()

    for filename in list(state['downloads'].keys()):
        attempts = state['downloads'][filename]
        if attempts and attempts[-1].get('status') == 'failed':
            del state['downloads'][filename]

    # Also clean history
    state['history'] = [
        entry for entry in state['history']
        if entry.get('status') != 'failed'
    ]

    save_state(state)


if __name__ == "__main__":
    # CLI interface for inspecting state
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "stats":
            stats = get_stats()
            print("Download Statistics:")
            print(f"  Unique models tracked: {stats['total_unique_models']}")
            print(f"  Total attempts: {stats['total_attempts']}")
            print(f"  Successful: {stats['successful']}")
            print(f"  Failed: {stats['failed']}")
            print(f"  Pending: {stats['pending']}")

        elif command == "successful":
            successful = get_successful_downloads()
            print(f"Successfully downloaded models: {len(successful)}")
            for filename, info in successful.items():
                print(f"  {filename}")
                print(f"    Path: {info.get('file_path')}")
                print(f"    Size: {info.get('file_size')} bytes")

        elif command == "failed":
            failed = get_failed_downloads()
            print(f"Failed downloads: {len(failed)}")
            for filename in failed:
                print(f"  {filename}")

        elif command == "clear-failed":
            clear_failed()
            print("Cleared all failed download records")

        else:
            print("Unknown command. Available: stats, successful, failed, clear-failed")
    else:
        print("Usage: python state_manager.py [command]")
        print("Commands: stats, successful, failed, clear-failed")
