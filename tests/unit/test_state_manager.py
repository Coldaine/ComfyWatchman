"""
Unit tests for the state_manager module.

Tests state management, download tracking, migration, backup/restore,
and all state operations.
"""

import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

import pytest

from comfyfixersmart.state_manager import (
    StateManager,
    StateData,
    DownloadAttempt,
    DownloadStatus,
    ensure_state_dir,
    load_state,
    save_state,
    mark_download_attempted,
    mark_download_success,
    mark_download_failed,
    get_download_status,
    get_successful_downloads,
    get_failed_downloads,
    was_recently_attempted,
    get_stats,
    clear_failed,
)


class TestDownloadStatus:
    """Test DownloadStatus enum."""

    def test_download_status_values(self):
        """Test that DownloadStatus has expected values."""
        assert DownloadStatus.ATTEMPTED.value == "attempted"
        assert DownloadStatus.SUCCESS.value == "success"
        assert DownloadStatus.FAILED.value == "failed"
        assert DownloadStatus.PENDING.value == "pending"


class TestDownloadAttempt:
    """Test DownloadAttempt dataclass."""

    def test_download_attempt_creation(self):
        """Test creating a DownloadAttempt instance."""
        attempt = DownloadAttempt(
            timestamp="2023-01-01T12:00:00",
            filename="model.safetensors",
            status="success",
            model_type="checkpoints",
            node_type="CheckpointLoaderSimple",
            civitai_id=12345,
            download_url="https://example.com/download",
        )

        assert attempt.timestamp == "2023-01-01T12:00:00"
        assert attempt.filename == "model.safetensors"
        assert attempt.status == "success"
        assert attempt.model_type == "checkpoints"
        assert attempt.node_type == "CheckpointLoaderSimple"
        assert attempt.civitai_id == 12345
        assert attempt.download_url == "https://example.com/download"

    def test_download_attempt_defaults(self):
        """Test DownloadAttempt default values."""
        attempt = DownloadAttempt(
            timestamp="2023-01-01T12:00:00", filename="model.safetensors", status="attempted"
        )

        assert attempt.model_type is None
        assert attempt.node_type is None
        assert attempt.civitai_id is None
        assert attempt.civitai_name is None
        assert attempt.version_id is None
        assert attempt.download_url is None
        assert attempt.completed_at is None
        assert attempt.file_path is None
        assert attempt.file_size is None
        assert attempt.error is None
        assert attempt.failed_at is None
        assert attempt.checksum is None


class TestStateData:
    """Test StateData dataclass."""

    def test_state_data_creation(self):
        """Test creating a StateData instance."""
        state = StateData(
            version="2.0",
            downloads={"model1.safetensors": []},
            history=[],
            metadata={"test": "value"},
        )

        assert state.version == "2.0"
        assert state.downloads == {"model1.safetensors": []}
        assert state.history == []
        assert state.metadata == {"test": "value"}

    def test_state_data_defaults(self):
        """Test StateData default values."""
        state = StateData()

        assert state.version == "2.0"
        assert state.downloads == {}
        assert state.history == []
        assert state.metadata == {}


class TestStateManagerInitialization:
    """Test StateManager initialization and setup."""

    def test_state_manager_init_creates_directories(self, tmp_path):
        """Test that StateManager creates necessary directories."""
        state_dir = tmp_path / "state"

        manager = StateManager(state_dir)

        assert state_dir.exists()
        assert (state_dir / "backups").exists()
        assert manager.state_file == state_dir / "download_state.json"
        assert manager.backup_dir == state_dir / "backups"

    def test_state_manager_init_with_string_path(self, tmp_path):
        """Test StateManager initialization with string path."""
        state_dir_str = str(tmp_path / "state")

        manager = StateManager(state_dir_str)

        assert Path(state_dir_str).exists()

    def test_state_manager_init_with_logger(self, tmp_path):
        """Test StateManager initialization with logger."""
        logger = Mock()
        manager = StateManager(tmp_path / "state", logger=logger)

        assert manager.logger == logger

    def test_state_manager_loads_empty_state_when_no_file(self, tmp_path):
        """Test that StateManager initializes with empty state when no file exists."""
        manager = StateManager(tmp_path / "state")

        assert manager.state.version == "2.0"
        assert manager.state.downloads == {}
        assert manager.state.history == []
        assert manager.state.metadata == {}


class TestStateManagerLoading:
    """Test state loading and migration."""

    def test_load_state_from_valid_file(self, tmp_path):
        """Test loading state from a valid JSON file."""
        state_dir = tmp_path / "state"
        state_file = state_dir / "download_state.json"

        state_data = {
            "version": "2.0",
            "downloads": {
                "model1.safetensors": [
                    {
                        "timestamp": "2023-01-01T12:00:00",
                        "filename": "model1.safetensors",
                        "status": "success",
                    }
                ]
            },
            "history": [
                {
                    "timestamp": "2023-01-01T12:00:00",
                    "filename": "model1.safetensors",
                    "status": "success",
                }
            ],
            "metadata": {"test": "value"},
        }

        state_dir.mkdir()
        with open(state_file, "w") as f:
            json.dump(state_data, f)

        manager = StateManager(state_dir)

        assert manager.state.version == "2.0"
        assert len(manager.state.downloads) == 1
        assert len(manager.state.history) == 1
        assert manager.state.metadata == {"test": "value"}

    def test_load_state_migrates_from_v1(self, tmp_path):
        """Test migrating state from version 1.0 to 2.0."""
        state_dir = tmp_path / "state"
        state_file = state_dir / "download_state.json"

        v1_data = {
            "downloads": {
                "model1.safetensors": [
                    {
                        "timestamp": "2023-01-01T12:00:00",
                        "filename": "model1.safetensors",
                        "status": "success",
                    }
                ]
            },
            "history": [
                {
                    "timestamp": "2023-01-01T12:00:00",
                    "filename": "model1.safetensors",
                    "status": "success",
                }
            ],
        }

        state_dir.mkdir()
        with open(state_file, "w") as f:
            json.dump(v1_data, f)

        manager = StateManager(state_dir)

        assert manager.state.version == "2.0"
        assert "migrated_from" in manager.state.metadata
        assert manager.state.metadata["migrated_from"] == "1.0"

    def test_load_state_handles_corrupted_file(self, tmp_path):
        """Test handling of corrupted state file."""
        state_dir = tmp_path / "state"
        state_file = state_dir / "download_state.json"

        state_dir.mkdir()
        with open(state_file, "w") as f:
            f.write("invalid json content")

        manager = StateManager(state_dir)

        # Should create backup and initialize empty state
        assert manager.state.version == "2.0"
        assert manager.state.downloads == {}

        # Check that backup was created
        backups = list(manager.backup_dir.glob("*.json"))
        assert len(backups) == 1
        assert "corrupted" in backups[0].name


class TestStateManagerOperations:
    """Test StateManager download tracking operations."""

    def test_mark_download_attempted(self, tmp_path):
        """Test marking a download as attempted."""
        manager = StateManager(tmp_path / "state")

        model_info = {"type": "checkpoints", "node_type": "CheckpointLoaderSimple"}
        civitai_info = {
            "civitai_id": 12345,
            "civitai_name": "Test Model",
            "version_id": 67890,
            "download_url": "https://example.com/download",
        }

        manager.mark_download_attempted("model.safetensors", model_info, civitai_info)

        assert "model.safetensors" in manager.state.downloads
        assert len(manager.state.downloads["model.safetensors"]) == 1

        attempt = manager.state.downloads["model.safetensors"][0]
        assert attempt.status == "attempted"
        assert attempt.filename == "model.safetensors"
        assert attempt.model_type == "checkpoints"
        assert attempt.node_type == "CheckpointLoaderSimple"
        assert attempt.civitai_id == 12345
        assert attempt.download_url == "https://example.com/download"

        # Check history
        assert len(manager.state.history) == 1
        assert manager.state.history[0] == attempt

    def test_mark_download_success(self, tmp_path):
        """Test marking a download as successful."""
        manager = StateManager(tmp_path / "state")

        # First mark as attempted
        manager.mark_download_attempted("model.safetensors", {"type": "checkpoints"})

        # Then mark as success
        manager.mark_download_success(
            "model.safetensors", "/path/to/model.safetensors", 1048576, "checksum123"
        )

        attempt = manager.state.downloads["model.safetensors"][0]
        assert attempt.status == "success"
        assert attempt.completed_at is not None
        assert attempt.file_path == "/path/to/model.safetensors"
        assert attempt.file_size == 1048576
        assert attempt.checksum == "checksum123"

    def test_mark_download_failed(self, tmp_path):
        """Test marking a download as failed."""
        manager = StateManager(tmp_path / "state")

        # First mark as attempted
        manager.mark_download_attempted("model.safetensors", {"type": "checkpoints"})

        # Then mark as failed
        manager.mark_download_failed("model.safetensors", "Network error")

        attempt = manager.state.downloads["model.safetensors"][0]
        assert attempt.status == "failed"
        assert attempt.failed_at is not None
        assert attempt.error == "Network error"

    def test_get_download_status(self, tmp_path):
        """Test getting download status."""
        manager = StateManager(tmp_path / "state")

        # No status for unknown file
        assert manager.get_download_status("unknown.safetensors") is None

        # Mark as attempted
        manager.mark_download_attempted("model.safetensors", {"type": "checkpoints"})
        assert manager.get_download_status("model.safetensors") == "attempted"

        # Mark as success
        manager.mark_download_success("model.safetensors", "/path/to/file", 1024)
        assert manager.get_download_status("model.safetensors") == "success"

    def test_get_successful_downloads(self, tmp_path):
        """Test getting successful downloads."""
        manager = StateManager(tmp_path / "state")

        # Add some downloads
        manager.mark_download_attempted("model1.safetensors", {"type": "checkpoints"})
        manager.mark_download_success("model1.safetensors", "/path/1", 1024)

        manager.mark_download_attempted("model2.safetensors", {"type": "loras"})
        manager.mark_download_failed("model2.safetensors", "Error")

        successful = manager.get_successful_downloads()

        assert len(successful) == 1
        assert "model1.safetensors" in successful
        assert successful["model1.safetensors"].file_path == "/path/1"

    def test_get_failed_downloads(self, tmp_path):
        """Test getting failed downloads."""
        manager = StateManager(tmp_path / "state")

        # Add some downloads
        manager.mark_download_attempted("model1.safetensors", {"type": "checkpoints"})
        manager.mark_download_success("model1.safetensors", "/path/1", 1024)

        manager.mark_download_attempted("model2.safetensors", {"type": "loras"})
        manager.mark_download_failed("model2.safetensors", "Error")

        failed = manager.get_failed_downloads()

        assert len(failed) == 1
        assert "model2.safetensors" in failed

    def test_was_recently_attempted(self, tmp_path):
        """Test checking if download was recently attempted."""
        manager = StateManager(tmp_path / "state")

        # Unknown file
        assert not manager.was_recently_attempted("unknown.safetensors")

        # Recent attempt
        manager.mark_download_attempted("model.safetensors", {"type": "checkpoints"})
        assert manager.was_recently_attempted("model.safetensors", hours=1)

        # Old attempt (simulate by modifying timestamp)
        manager.state.downloads["model.safetensors"][0].timestamp = (
            datetime.now() - timedelta(hours=25)
        ).isoformat()
        assert not manager.was_recently_attempted("model.safetensors", hours=24)


class TestStateManagerStats:
    """Test StateManager statistics functionality."""

    def test_get_stats(self, tmp_path):
        """Test getting comprehensive statistics."""
        manager = StateManager(tmp_path / "state")

        # Add various downloads
        manager.mark_download_attempted("model1.safetensors", {"type": "checkpoints"})
        manager.mark_download_success("model1.safetensors", "/path/1", 1024)

        manager.mark_download_attempted("model2.safetensors", {"type": "loras"})
        manager.mark_download_failed("model2.safetensors", "Error")

        manager.mark_download_attempted("model3.safetensors", {"type": "vae"})
        # Leave as attempted

        stats = manager.get_stats()

        assert stats["version"] == "2.0"
        assert stats["total_unique_models"] == 3
        assert stats["total_attempts"] == 3
        assert stats["successful"] == 1
        assert stats["failed"] == 1
        assert stats["attempted"] == 1
        assert stats["pending"] == 0
        assert stats["total_downloaded_size"] == 1024
        assert "last_updated" in stats


class TestStateManagerValidation:
    """Test StateManager validation functionality."""

    def test_validate_state_no_issues(self, tmp_path):
        """Test validation with no issues."""
        manager = StateManager(tmp_path / "state")

        issues = manager.validate_state()
        assert issues == []

    def test_validate_state_missing_file(self, tmp_path):
        """Test validation detects missing files."""
        manager = StateManager(tmp_path / "state")

        # Add successful download with non-existent file
        manager.mark_download_attempted("model.safetensors", {"type": "checkpoints"})
        manager.mark_download_success(
            "model.safetensors", "/nonexistent/path/model.safetensors", 1024
        )

        issues = manager.validate_state()
        assert len(issues) == 1
        assert "Missing file" in issues[0]

    def test_validate_state_invalid_status(self, tmp_path):
        """Test validation detects invalid status."""
        manager = StateManager(tmp_path / "state")

        # Manually add invalid status
        manager.state.downloads["model.safetensors"] = [
            DownloadAttempt("2023-01-01T12:00:00", "model.safetensors", "invalid_status")
        ]

        issues = manager.validate_state()
        assert len(issues) == 1
        assert "Invalid status" in issues[0]


class TestStateManagerCleanup:
    """Test StateManager cleanup functionality."""

    def test_cleanup_state_old_failed(self, tmp_path):
        """Test cleanup of old failed downloads."""
        manager = StateManager(tmp_path / "state")

        # Add old failed download
        old_time = (datetime.now() - timedelta(days=40)).isoformat()
        manager.state.downloads["old_failed.safetensors"] = [
            DownloadAttempt(old_time, "old_failed.safetensors", "failed", failed_at=old_time)
        ]

        # Add recent failed download
        recent_time = datetime.now().isoformat()
        manager.state.downloads["recent_failed.safetensors"] = [
            DownloadAttempt(
                recent_time, "recent_failed.safetensors", "failed", failed_at=recent_time
            )
        ]

        stats = manager.cleanup_state(remove_failed_older_than_days=30)

        assert stats["removed_failed"] == 1
        assert "old_failed.safetensors" not in manager.state.downloads
        assert "recent_failed.safetensors" in manager.state.downloads

    def test_cleanup_state_duplicates(self, tmp_path):
        """Test cleanup of duplicate successful downloads."""
        manager = StateManager(tmp_path / "state")

        # Add multiple successful attempts
        attempts = [
            DownloadAttempt(
                "2023-01-01T10:00:00",
                "model.safetensors",
                "success",
                completed_at="2023-01-01T10:00:00",
                file_path="/path/1",
            ),
            DownloadAttempt(
                "2023-01-01T11:00:00",
                "model.safetensors",
                "success",
                completed_at="2023-01-01T11:00:00",
                file_path="/path/2",
            ),
            DownloadAttempt(
                "2023-01-01T12:00:00",
                "model.safetensors",
                "success",
                completed_at="2023-01-01T12:00:00",
                file_path="/path/3",
            ),
        ]
        manager.state.downloads["model.safetensors"] = attempts

        stats = manager.cleanup_state(remove_successful_duplicates=True)

        assert stats["removed_duplicates"] == 2
        assert len(manager.state.downloads["model.safetensors"]) == 1
        # Should keep the latest (by completed_at)
        assert manager.state.downloads["model.safetensors"][0].file_path == "/path/3"


class TestStateManagerImportExport:
    """Test StateManager import/export functionality."""

    def test_export_state(self, tmp_path):
        """Test exporting state to file."""
        manager = StateManager(tmp_path / "state")
        export_path = tmp_path / "exported_state.json"

        # Add some data
        manager.mark_download_attempted("model.safetensors", {"type": "checkpoints"})
        manager.mark_download_success("model.safetensors", "/path/to/model", 1024)

        result = manager.export_state(export_path)

        assert result is True
        assert export_path.exists()

        # Verify content
        with open(export_path, "r") as f:
            data = json.load(f)

        assert data["version"] == "2.0"
        assert "model.safetensors" in data["downloads"]

    def test_import_state_replace(self, tmp_path):
        """Test importing state with replace mode."""
        manager = StateManager(tmp_path / "state")

        # Create import data
        import_data = {
            "version": "2.0",
            "downloads": {
                "imported_model.safetensors": [
                    {
                        "timestamp": "2023-01-01T12:00:00",
                        "filename": "imported_model.safetensors",
                        "status": "success",
                    }
                ]
            },
            "history": [
                {
                    "timestamp": "2023-01-01T12:00:00",
                    "filename": "imported_model.safetensors",
                    "status": "success",
                }
            ],
            "metadata": {"imported": True},
        }

        import_file = tmp_path / "import.json"
        with open(import_file, "w") as f:
            json.dump(import_data, f)

        result = manager.import_state(import_file, merge=False)

        assert result is True
        assert "imported_model.safetensors" in manager.state.downloads
        assert manager.state.metadata == {"imported": True}

    def test_import_state_merge(self, tmp_path):
        """Test importing state with merge mode."""
        manager = StateManager(tmp_path / "state")

        # Add existing data
        manager.mark_download_attempted("existing.safetensors", {"type": "checkpoints"})

        # Create import data
        import_data = {
            "version": "2.0",
            "downloads": {
                "imported_model.safetensors": [
                    {
                        "timestamp": "2023-01-01T12:00:00",
                        "filename": "imported_model.safetensors",
                        "status": "success",
                    }
                ]
            },
            "history": [
                {
                    "timestamp": "2023-01-01T12:00:00",
                    "filename": "imported_model.safetensors",
                    "status": "success",
                }
            ],
            "metadata": {"imported": True},
        }

        import_file = tmp_path / "import.json"
        with open(import_file, "w") as f:
            json.dump(import_data, f)

        result = manager.import_state(import_file, merge=True)

        assert result is True
        assert "existing.safetensors" in manager.state.downloads
        assert "imported_model.safetensors" in manager.state.downloads


class TestStateManagerTransaction:
    """Test StateManager transaction functionality."""

    def test_transaction_success(self, tmp_path):
        """Test successful transaction."""
        manager = StateManager(tmp_path / "state")

        with manager.transaction():
            manager.mark_download_attempted("model.safetensors", {"type": "checkpoints"})
            manager.mark_download_success("model.safetensors", "/path/to/model", 1024)

        # Should be saved
        assert manager.get_download_status("model.safetensors") == "success"

    def test_transaction_rollback_on_error(self, tmp_path):
        """Test transaction rollback on error."""
        manager = StateManager(tmp_path / "state")

        # Add initial data
        manager.mark_download_attempted("existing.safetensors", {"type": "checkpoints"})

        try:
            with manager.transaction():
                manager.mark_download_attempted("new_model.safetensors", {"type": "loras"})
                raise ValueError("Test error")
        except ValueError:
            pass  # Expected

        # Should have rolled back - new model should not exist
        assert "new_model.safetensors" not in manager.state.downloads
        # But existing data should still be there
        assert "existing.safetensors" in manager.state.downloads


class TestBackwardCompatibility:
    """Test backward compatibility functions."""

    def test_backward_compatibility_functions_exist(self):
        """Test that backward compatibility functions exist and don't crash."""
        # These functions should exist but do nothing or return defaults
        ensure_state_dir()
        state = load_state()
        assert state == {"downloads": {}, "history": []}

        save_state({"test": "data"})
        mark_download_attempted("test", {})
        mark_download_success("test", "/path", 1024)
        mark_download_failed("test", "error")

        assert get_download_status("test") is None
        assert get_successful_downloads() == {}
        assert get_failed_downloads() == []
        assert was_recently_attempted("test") is False

        stats = get_stats()
        assert stats["total_unique_models"] == 0

        clear_failed()
