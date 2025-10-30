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

from abc import ABC, abstractmethod
from contextlib import contextmanager
import threading
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple, Union
from collections import deque
from pathlib import Path
from datetime import datetime, timedelta
import shutil
import json
import os

from .config import config
from .logging import get_logger


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
    cycle_history: List[Dict[str, Any]] = field(default_factory=list)


class StateManager(ABC):
    """Abstract base class for state managers."""

    @abstractmethod
    def mark_download_attempted(self, filename: str, model_info: Dict[str, Any], civitai_info: Optional[Dict[str, Any]] = None):
        pass

    @abstractmethod
    def mark_download_success(self, filename: str, file_path: Union[str, Path], file_size: int, checksum: Optional[str] = None):
        pass

    @abstractmethod
    def mark_download_failed(self, filename: str, error_message: str):
        pass

    @abstractmethod
    def get_download_status(self, filename: str) -> Optional[str]:
        pass

    @abstractmethod
    def get_successful_downloads(self) -> Dict[str, DownloadAttempt]:
        pass

    @abstractmethod
    def get_failed_downloads(self) -> List[str]:
        pass

    @abstractmethod
    def was_recently_attempted(self, filename: str, hours: int = 24) -> bool:
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        pass


class JsonStateManager(StateManager):
    """Enhanced state manager using a JSON file backend."""

    def __init__(self, state_dir: Union[str, Path], logger=None):
        """
        Initialize state manager.
        ...
        """
        self.state_dir = Path(state_dir)
        self.state_file = self.state_dir / "download_state.json"
        self.backup_dir = self.state_dir / "backups"
        self.lock = threading.RLock()
        self.logger = logger

        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.state = self._load_state()

    def _load_state(self) -> StateData:
        """Load state from file with error handling and migration."""
        if not self.state_file.exists():
            self._log("Creating new state file")
            return StateData()

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            version = data.get('version', '1.0')
            if version != '2.0':
                self._log(f"Migrating state from version {version} to 2.0")
                data = self._migrate_state(data, version)
            return self._dict_to_state_data(data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self._log(f"Error loading state file: {e}. Creating backup and initializing new state.")
            self._create_backup("corrupted")
            return StateData()

    def _migrate_state(self, data: Dict[str, Any], from_version: str) -> Dict[str, Any]:
        """Migrate state data from older versions."""
        if from_version == '1.0':
            return {
                'version': '2.0',
                'downloads': data.get('downloads', {}),
                'history': data.get('history', []),
                'metadata': {
                    'migrated_from': from_version,
                    'migration_date': datetime.now().isoformat(),
                    'original_keys': list(data.keys())
                }
            }
        return data

    def _dict_to_state_data(self, data: Dict[str, Any]) -> StateData:
        """Convert dictionary to StateData object."""
        history = [DownloadAttempt(**item) for item in data.get('history', []) if isinstance(item, dict)]
        downloads = {
            filename: [DownloadAttempt(**attempt) for attempt in attempts if isinstance(attempt, dict)]
            for filename, attempts in data.get('downloads', {}).items()
        }
        return StateData(
            version=data.get('version', '2.0'),
            downloads=downloads,
            history=history,
            metadata=data.get('metadata', {}),
            cycle_history=data.get('cycle_history', [])
        )

    def _save_state(self):
        """Save state to file with backup."""
        with self.lock:
            if self.state_file.exists():
                self._create_backup("auto")
            try:
                data = asdict(self.state)
                with open(self.state_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self._log("State saved successfully")
            except Exception as e:
                self._log(f"Error saving state: {e}")
                raise

    # ------------------------------------------------------------------
    # General-purpose artifact helpers
    # ------------------------------------------------------------------

    def _artifact_path(self, filename: str) -> Path:
        """Return the fully qualified path for a state artifact."""

        path = self.state_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def save_json_artifact(self, filename: str, data: Any) -> Path:
        """Persist JSON data inside the state directory."""

        artifact_path = self._artifact_path(filename)
        serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
        with self.lock:
            artifact_path.write_text(serialized, encoding='utf-8')
        return artifact_path

    def load_json_artifact(self, filename: str, default: Any = None) -> Any:
        """Load JSON data from the state directory."""

        artifact_path = self._artifact_path(filename)
        if not artifact_path.exists():
            return default
        try:
            return json.loads(artifact_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            self._log(f"JSON artifact {filename} is corrupted; returning default")
            return default

    def _append_jsonl(self, filename: str, record: Dict[str, Any]) -> Path:
        """Append a JSON line record to an artifact file."""

        artifact_path = self._artifact_path(filename)
        line = json.dumps(record, ensure_ascii=False)
        with self.lock:
            with artifact_path.open('a', encoding='utf-8') as handle:
                handle.write(line + "\n")
        return artifact_path

    def _read_jsonl(self, filename: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Read the most recent JSONL records from an artifact file."""

        artifact_path = self._artifact_path(filename)
        if not artifact_path.exists():
            return []

        records: deque = deque(maxlen=limit)
        with artifact_path.open('r', encoding='utf-8') as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    self._log(f"Skipping malformed JSONL line in {filename}")
        return list(records)

    # ------------------------------------------------------------------
    # Intake logging
    # ------------------------------------------------------------------

    def append_intake_event(self, event_type: str, path: str, metadata: Optional[Dict[str, Any]] = None) -> Path:
        """Record a workflow intake event (new/updated)."""

        metadata = metadata or {}
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "path": str(path),
        }
        record.update(metadata)
        return self._append_jsonl('intake_log.jsonl', record)

    def list_intake_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent intake events."""

        return self._read_jsonl('intake_log.jsonl', limit=limit)

    def process_workflow_intake(self, workflow_paths: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Update workflow snapshot metadata and return new/updated paths."""

        snapshot: Dict[str, Dict[str, Any]] = {}
        new_items: List[Dict[str, Any]] = []
        updated_items: List[Dict[str, Any]] = []
        previous_snapshot: Dict[str, Dict[str, Any]] = self.state.metadata.get('workflow_snapshot', {})

        for path_str in workflow_paths:
            path_obj = Path(path_str)
            try:
                stats = path_obj.stat()
            except OSError:
                continue

            entry = {
                'path': str(path_obj),
                'mtime': stats.st_mtime,
                'size': stats.st_size,
            }
            snapshot[str(path_obj)] = entry
            previous = previous_snapshot.get(str(path_obj))
            if previous is None:
                new_items.append(entry)
            elif previous.get('mtime') != entry['mtime'] or previous.get('size') != entry['size']:
                updated_items.append(entry)

        removed_paths = [path for path in previous_snapshot.keys() if path not in snapshot]

        if new_items or updated_items or removed_paths:
            self.state.metadata['workflow_snapshot'] = snapshot
            self._save_state()

            for item in new_items:
                self.append_intake_event('new_workflow', item['path'], {'size': item['size']})
            for item in updated_items:
                self.append_intake_event('updated_workflow', item['path'], {'size': item['size']})
            for path in removed_paths:
                self.append_intake_event('removed_workflow', path, {})

        return {
            'new': new_items,
            'updated': updated_items,
            'removed': removed_paths,
        }

    # ------------------------------------------------------------------
    # Cycle tracking
    # ------------------------------------------------------------------

    def record_cycle_result(self, result: Dict[str, Any], max_history: int = 50) -> None:
        """Persist scheduler cycle metadata for observability."""

        with self.lock:
            self.state.cycle_history.append(result)
            if len(self.state.cycle_history) > max_history:
                self.state.cycle_history = self.state.cycle_history[-max_history:]
            self.state.metadata['last_cycle'] = result
            self._save_state()

    def get_recent_cycles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return the most recent cycle summaries."""

        return self.state.cycle_history[-limit:]

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
            print(f"[JsonStateManager] {message}")

    @contextmanager
    def transaction(self):
        """Context manager for atomic state operations."""
        original_state = self._dict_to_state_data(asdict(self.state))
        try:
            yield
            self._save_state()
        except Exception as e:
            self.state = original_state
            self._log(f"Transaction failed, state restored: {e}")
            raise

    def mark_download_attempted(self, filename: str, model_info: Dict[str, Any], civitai_info: Optional[Dict[str, Any]] = None):
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
            
            self.state.history.append(attempt)
            if filename not in self.state.downloads:
                self.state.downloads[filename] = []
            self.state.downloads[filename].append(attempt)
            self._log(f"Marked download attempted: {filename}")

    def mark_download_success(self, filename: str, file_path: Union[str, Path], file_size: int, checksum: Optional[str] = None):
        """Mark that a download succeeded."""
        with self.transaction():
            file_path = str(file_path)
            if filename in self.state.downloads and self.state.downloads[filename]:
                latest = self.state.downloads[filename][-1]
                latest.status = DownloadStatus.SUCCESS.value
                latest.completed_at = datetime.now().isoformat()
                latest.file_path = file_path
                latest.file_size = file_size
                latest.checksum = checksum
                for entry in reversed(self.state.history):
                    if entry.filename == filename and entry.status == DownloadStatus.ATTEMPTED.value:
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
            if filename in self.state.downloads and self.state.downloads[filename]:
                latest = self.state.downloads[filename][-1]
                latest.status = DownloadStatus.FAILED.value
                latest.failed_at = datetime.now().isoformat()
                latest.error = error_message
                for entry in reversed(self.state.history):
                    if entry.filename == filename and entry.status == DownloadStatus.ATTEMPTED.value:
                        entry.status = DownloadStatus.FAILED.value
                        entry.failed_at = datetime.now().isoformat()
                        entry.error = error_message
                        break
            self._log(f"Marked download failed: {filename} - {error_message}")

    def get_download_status(self, filename: str) -> Optional[str]:
        """Get the status of a model download."""
        if filename not in self.state.downloads or not self.state.downloads[filename]:
            return None
        return self.state.downloads[filename][-1].status

    def get_successful_downloads(self) -> Dict[str, DownloadAttempt]:
        """Get dict of all successfully downloaded models."""
        return {
            filename: attempts[-1]
            for filename, attempts in self.state.downloads.items()
            if attempts and attempts[-1].status == DownloadStatus.SUCCESS.value
        }

    def get_failed_downloads(self) -> List[str]:
        """Get list of models that failed to download."""
        return [
            filename
            for filename, attempts in self.state.downloads.items()
            if attempts and attempts[-1].status == DownloadStatus.FAILED.value
        ]

    def was_recently_attempted(self, filename: str, hours: int = 24) -> bool:
        """Check if a download was attempted recently."""
        if filename not in self.state.downloads or not self.state.downloads[filename]:
            return False
        latest = self.state.downloads[filename][-1]
        try:
            timestamp = datetime.fromisoformat(latest.timestamp)
            return (datetime.now() - timestamp).total_seconds() / 3600 < hours
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
        for attempts in self.state.downloads.values():
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


class StateManagerFactory:
    """Factory for creating a state manager based on configuration."""
    _instance: Optional[StateManager] = None
    _lock = threading.Lock()

    @classmethod
    def get_manager(cls, logger=None) -> StateManager:
        """Get the singleton instance of the configured state manager."""
        with cls._lock:
            if cls._instance is None:
                logger = logger or get_logger("StateManagerFactory")
                if config.state.backend == "sql":
                    from .adapters.sql_state import SqlStateManager
                    logger.info("Using SQL state backend.")
                    cls._instance = SqlStateManager(db_path=config.state.sql_url, logger=logger)
                else:
                    logger.info("Using JSON state backend.")
                    cls._instance = JsonStateManager(state_dir=config.state.json_path, logger=logger)
            return cls._instance