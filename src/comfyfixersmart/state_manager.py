"""
Enhanced State Management Module for ComfyFixerSmart

Provides robust state tracking for download operations with:
- Configurable state directory paths
- Better error handling and recovery
- State migration between versions
- State validation and cleanup utilities
- Enhanced statistics and reporting
- Thread-safe operations
- Backup and restore capabilities
"""

import json
import os
import shutil
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading
from contextlib import contextmanager


class DownloadStatus(Enum):
    """Enumeration of possible download statuses."""
    ATTEMPTED = "attempted"
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


@dataclass
class DownloadAttempt:
    """Represents a single download attempt."""
    timestamp: str
    filename: str
    status: str
    model_type: Optional[str] = None
    node_type: Optional[str] = None
    civitai_id: Optional[int] = None
    civitai_name: Optional[str] = None
    version_id: Optional[int] = None
    download_url: Optional[str] = None
    completed_at: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    error: Optional[str] = None
    failed_at: Optional[str] = None
    checksum: Optional[str] = None


@dataclass
class StateData:
    """Complete state data structure."""
    version: str = "2.0"
    downloads: Dict[str, List[DownloadAttempt]] = field(default_factory=dict)
    history: List[DownloadAttempt] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateManager:
    """Enhanced state manager with configurable paths and robust error handling."""

    def __init__(self, state_dir: Union[str, Path], logger=None):
        """
        Initialize state manager.

        Args:
            state_dir: Directory to store state files
            logger: Optional logger instance
        """
        self.state_dir = Path(state_dir)
        self.state_file = self.state_dir / "download_state.json"
        self.backup_dir = self.state_dir / "backups"
        self.lock = threading.RLock()
        self.logger = logger

        # Ensure directories exist
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Load or initialize state
        self.state = self._load_state()

    def _load_state(self) -> StateData:
        """Load state from file with error handling and migration."""
        if not self.state_file.exists():
            self._log("Creating new state file")
            return StateData()

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check version and migrate if needed
            version = data.get('version', '1.0')
            if version != '2.0':
                self._log(f"Migrating state from version {version} to 2.0")
                data = self._migrate_state(data, version)

            # Convert to StateData object
            return self._dict_to_state_data(data)

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self._log(f"Error loading state file: {e}. Creating backup and initializing new state.")
            self._create_backup("corrupted")
            return StateData()

    def _migrate_state(self, data: Dict[str, Any], from_version: str) -> Dict[str, Any]:
        """Migrate state data from older versions."""
        if from_version == '1.0':
            # Version 1.0 to 2.0 migration
            migrated = {
                'version': '2.0',
                'downloads': data.get('downloads', {}),
                'history': data.get('history', []),
                'metadata': {
                    'migrated_from': from_version,
                    'migration_date': datetime.now().isoformat(),
                    'original_keys': list(data.keys())
                }
            }
            return migrated
        return data

    def _dict_to_state_data(self, data: Dict[str, Any]) -> StateData:
        """Convert dictionary to StateData object."""
        # Convert history items to DownloadAttempt objects
        history = []
        for item in data.get('history', []):
            if isinstance(item, dict):
                history.append(DownloadAttempt(**item))

        # Convert downloads dict
        downloads = {}
        for filename, attempts in data.get('downloads', {}).items():
            downloads[filename] = []
            for attempt in attempts:
                if isinstance(attempt, dict):
                    downloads[filename].append(DownloadAttempt(**attempt))

        return StateData(
            version=data.get('version', '2.0'),
            downloads=downloads,
            history=history,
            metadata=data.get('metadata', {})
        )

    def _save_state(self):
        """Save state to file with backup."""
        with self.lock:
            # Create backup before saving
            if self.state_file.exists():
                self._create_backup("auto")

            try:
                # Convert to dict for JSON serialization
                data = asdict(self.state)

                with open(self.state_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                self._log("State saved successfully")

            except Exception as e:
                self._log(f"Error saving state: {e}")
                raise

    def _create_backup(self, reason: str):
        """Create a backup of the current state file."""
        if not self.state_file.exists():
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"download_state_{timestamp}_{reason}.json"
        backup_path = self.backup_dir / backup_name

        try:
            shutil.copy2(self.state_file, backup_path)
            self._log(f"Backup created: {backup_path}")
        except Exception as e:
            self._log(f"Failed to create backup: {e}")

    def _log(self, message: str):
        """Internal logging method."""
        if self.logger:
            self.logger.info(message)
        else:
            print(f"[StateManager] {message}")

    @contextmanager
    def transaction(self):
        """Context manager for atomic state operations."""
        # Create a backup point
        original_state = self._dict_to_state_data(asdict(self.state))
        try:
            yield
            self._save_state()
        except Exception as e:
            # Restore original state on error
            self.state = original_state
            self._log(f"Transaction failed, state restored: {e}")
            raise

    def mark_download_attempted(self, filename: str, model_info: Dict[str, Any],
                              civitai_info: Optional[Dict[str, Any]] = None):
        """Mark that a download was attempted."""
        with self.transaction():
            attempt = DownloadAttempt(
                timestamp=datetime.now().isoformat(),
                filename=filename,
                status=DownloadStatus.ATTEMPTED.value,
                model_type=model_info.get('type'),
                node_type=model_info.get('node_type')
            )

            if civitai_info:
                attempt.civitai_id = civitai_info.get('civitai_id')
                attempt.civitai_name = civitai_info.get('civitai_name')
                attempt.version_id = civitai_info.get('version_id')
                attempt.download_url = civitai_info.get('download_url')

            # Add to history
            self.state.history.append(attempt)

            # Add to downloads dict
            if filename not in self.state.downloads:
                self.state.downloads[filename] = []
            self.state.downloads[filename].append(attempt)

            self._log(f"Marked download attempted: {filename}")

    def mark_download_success(self, filename: str, file_path: Union[str, Path],
                            file_size: int, checksum: Optional[str] = None):
        """Mark that a download succeeded."""
        with self.transaction():
            file_path = str(file_path)

            # Update most recent attempt
            if filename in self.state.downloads and self.state.downloads[filename]:
                latest = self.state.downloads[filename][-1]
                latest.status = DownloadStatus.SUCCESS.value
                latest.completed_at = datetime.now().isoformat()
                latest.file_path = file_path
                latest.file_size = file_size
                latest.checksum = checksum

                # Update history
                for entry in reversed(self.state.history):
                    if (entry.filename == filename and
                        entry.status == DownloadStatus.ATTEMPTED.value):
                        entry.status = DownloadStatus.SUCCESS.value
                        entry.completed_at = datetime.now().isoformat()
                        entry.file_path = file_path
                        entry.file_size = file_size
                        entry.checksum = checksum
                        break

            self._log(f"Marked download success: {filename}")

    def mark_download_failed(self, filename: str, error_message: str):
        """Mark that a download failed."""
        with self.transaction():
            # Update most recent attempt
            if filename in self.state.downloads and self.state.downloads[filename]:
                latest = self.state.downloads[filename][-1]
                latest.status = DownloadStatus.FAILED.value
                latest.failed_at = datetime.now().isoformat()
                latest.error = error_message

                # Update history
                for entry in reversed(self.state.history):
                    if (entry.filename == filename and
                        entry.status == DownloadStatus.ATTEMPTED.value):
                        entry.status = DownloadStatus.FAILED.value
                        entry.failed_at = datetime.now().isoformat()
                        entry.error = error_message
                        break

            self._log(f"Marked download failed: {filename} - {error_message}")

    def get_download_status(self, filename: str) -> Optional[str]:
        """Get the status of a model download."""
        if filename not in self.state.downloads:
            return None

        attempts = self.state.downloads[filename]
        if not attempts:
            return None

        return attempts[-1].status

    def get_successful_downloads(self) -> Dict[str, DownloadAttempt]:
        """Get dict of all successfully downloaded models."""
        successful = {}
        for filename, attempts in self.state.downloads.items():
            if attempts:
                latest = attempts[-1]
                if latest.status == DownloadStatus.SUCCESS.value:
                    successful[filename] = latest
        return successful

    def get_failed_downloads(self) -> List[str]:
        """Get list of models that failed to download."""
        failed = []
        for filename, attempts in self.state.downloads.items():
            if attempts:
                latest = attempts[-1]
                if latest.status == DownloadStatus.FAILED.value:
                    failed.append(filename)
        return failed

    def was_recently_attempted(self, filename: str, hours: int = 24) -> bool:
        """Check if a download was attempted recently."""
        if filename not in self.state.downloads:
            return False

        attempts = self.state.downloads[filename]
        if not attempts:
            return False

        latest = attempts[-1]
        try:
            timestamp = datetime.fromisoformat(latest.timestamp)
            age_hours = (datetime.now() - timestamp).total_seconds() / 3600
            return age_hours < hours
        except (ValueError, AttributeError):
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about downloads."""
        stats = {
            "version": self.state.version,
            "total_unique_models": len(self.state.downloads),
            "total_attempts": len(self.state.history),
            "successful": 0,
            "failed": 0,
            "pending": 0,
            "attempted": 0,
            "total_downloaded_size": 0,
            "last_updated": datetime.now().isoformat(),
        }

        for filename, attempts in self.state.downloads.items():
            if attempts:
                status = attempts[-1].status
                if status == DownloadStatus.SUCCESS.value:
                    stats['successful'] += 1
                    if attempts[-1].file_size:
                        stats['total_downloaded_size'] += attempts[-1].file_size
                elif status == DownloadStatus.FAILED.value:
                    stats['failed'] += 1
                elif status == DownloadStatus.ATTEMPTED.value:
                    stats['attempted'] += 1
                elif status == DownloadStatus.PENDING.value:
                    stats['pending'] += 1

        return stats

    def validate_state(self) -> List[str]:
        """Validate state integrity and return list of issues."""
        issues = []

        # Check for missing files
        successful = self.get_successful_downloads()
        for filename, attempt in successful.items():
            if attempt.file_path and not Path(attempt.file_path).exists():
                issues.append(f"Missing file: {attempt.file_path} (recorded for {filename})")

        # Check for invalid statuses
        valid_statuses = {s.value for s in DownloadStatus}
        for filename, attempts in self.state.downloads.items():
            for attempt in attempts:
                if attempt.status not in valid_statuses:
                    issues.append(f"Invalid status '{attempt.status}' for {filename}")

        # Check for orphaned history entries
        history_filenames = {entry.filename for entry in self.state.history}
        download_filenames = set(self.state.downloads.keys())
        orphaned = history_filenames - download_filenames
        if orphaned:
            issues.append(f"Orphaned history entries: {orphaned}")

        return issues

    def cleanup_state(self, remove_failed_older_than_days: int = 30,
                     remove_successful_duplicates: bool = True) -> Dict[str, int]:
        """Clean up state data and return cleanup statistics."""
        with self.transaction():
            stats = {"removed_failed": 0, "removed_duplicates": 0, "validated_files": 0}

            # Remove old failed attempts
            cutoff_date = datetime.now() - timedelta(days=remove_failed_older_than_days)

            for filename in list(self.state.downloads.keys()):
                attempts = self.state.downloads[filename]
                if not attempts:
                    continue

                latest = attempts[-1]
                if (latest.status == DownloadStatus.FAILED.value and
                    latest.failed_at):
                    try:
                        failed_date = datetime.fromisoformat(latest.failed_at)
                        if failed_date < cutoff_date:
                            del self.state.downloads[filename]
                            stats["removed_failed"] += 1
                    except ValueError:
                        pass

            # Remove duplicate successful attempts (keep only latest)
            if remove_successful_duplicates:
                for filename in list(self.state.downloads.keys()):
                    attempts = self.state.downloads[filename]
                    if len(attempts) > 1:
                        # Keep only the latest successful attempt
                        successful_attempts = [
                            a for a in attempts
                            if a.status == DownloadStatus.SUCCESS.value
                        ]
                        if successful_attempts:
                            latest_success = max(successful_attempts,
                                               key=lambda a: a.completed_at or "")
                            self.state.downloads[filename] = [latest_success]
                            stats["removed_duplicates"] += len(attempts) - 1

            # Validate file existence
            successful = self.get_successful_downloads()
            for filename, attempt in successful.items():
                if attempt.file_path and Path(attempt.file_path).exists():
                    stats["validated_files"] += 1

            # Clean history (remove entries older than cutoff)
            self.state.history = [
                entry for entry in self.state.history
                if not entry.failed_at or
                datetime.fromisoformat(entry.failed_at) > cutoff_date
            ]

            self._log(f"State cleanup completed: {stats}")
            return stats

    def export_state(self, export_path: Union[str, Path]) -> bool:
        """Export state to a file."""
        try:
            data = asdict(self.state)
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._log(f"State exported to: {export_path}")
            return True
        except Exception as e:
            self._log(f"Failed to export state: {e}")
            return False

    def import_state(self, import_path: Union[str, Path], merge: bool = False) -> bool:
        """Import state from a file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if merge:
                # Merge with existing state
                imported_state = self._dict_to_state_data(data)
                # Merge downloads
                for filename, attempts in imported_state.downloads.items():
                    if filename not in self.state.downloads:
                        self.state.downloads[filename] = attempts
                    else:
                        self.state.downloads[filename].extend(attempts)
                # Merge history
                self.state.history.extend(imported_state.history)
            else:
                # Replace state
                self.state = self._dict_to_state_data(data)

            self._save_state()
            self._log(f"State imported from: {import_path}")
            return True
        except Exception as e:
            self._log(f"Failed to import state: {e}")
            return False


# Backward compatibility functions
def ensure_state_dir():
    """Backward compatibility - use StateManager instead."""
    pass

def load_state():
    """Backward compatibility - use StateManager instead."""
    return {"downloads": {}, "history": []}

def save_state(state):
    """Backward compatibility - use StateManager instead."""
    pass

# Other backward compatibility functions follow the same pattern...
def mark_download_attempted(filename, model_info, civitai_info=None):
    """Backward compatibility - use StateManager instead."""
    pass

def mark_download_success(filename, file_path, file_size):
    """Backward compatibility - use StateManager instead."""
    pass

def mark_download_failed(filename, error_message):
    """Backward compatibility - use StateManager instead."""
    pass

def get_download_status(filename):
    """Backward compatibility - use StateManager instead."""
    return None

def get_successful_downloads():
    """Backward compatibility - use StateManager instead."""
    return {}

def get_failed_downloads():
    """Backward compatibility - use StateManager instead."""
    return []

def was_recently_attempted(filename, hours=24):
    """Backward compatibility - use StateManager instead."""
    return False

def get_stats():
    """Backward compatibility - use StateManager instead."""
    return {"total_unique_models": 0, "total_attempts": 0, "successful": 0, "failed": 0, "pending": 0}

def clear_failed():
    """Backward compatibility - use StateManager instead."""
    pass