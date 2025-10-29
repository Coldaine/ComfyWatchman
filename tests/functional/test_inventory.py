"""
Functional tests for the inventory module.

Tests model inventory building, validation, comparison, and export
functionality with real file system operations.
"""

import json
import csv
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from comfyfixersmart.inventory import ModelInventory, ModelInfo, build_local_inventory


class TestModelInfo:
    """Test ModelInfo dataclass."""

    def test_model_info_creation(self):
        """Test creating a ModelInfo instance."""
        info = ModelInfo(
            filename="model.safetensors",
            path="/models/checkpoints/model.safetensors",
            size=2097152000,  # 2GB
            is_valid=True,
            validation_errors=[],
        )

        assert info.filename == "model.safetensors"
        assert info.path == "/models/checkpoints/model.safetensors"
        assert info.size == 2097152000
        assert info.is_valid is True
        assert info.validation_errors == []

    def test_model_info_with_errors(self):
        """Test ModelInfo with validation errors."""
        info = ModelInfo(
            filename="invalid.safetensors",
            path="/models/invalid.safetensors",
            size=1024,
            is_valid=False,
            validation_errors=["File too small", "Corrupted"],
        )

        assert info.is_valid is False
        assert len(info.validation_errors) == 2
        assert "File too small" in info.validation_errors


class TestModelInventory:
    """Test ModelInventory class functionality."""

    def test_inventory_initialization_with_models_dir(self, tmp_path):
        """Test ModelInventory initialization with models directory."""
        models_dir = tmp_path / "models"
        inventory = ModelInventory(models_dir=str(models_dir))

        assert inventory.models_dir == models_dir
        assert inventory.state_manager is None
        assert inventory.logger is not None

    @patch("comfyfixersmart.inventory.config")
    def test_inventory_initialization_from_config(self, mock_config, tmp_path):
        """Test ModelInventory initialization using config."""
        mock_config.models_dir = tmp_path / "config_models"
        inventory = ModelInventory()

        assert inventory.models_dir == tmp_path / "config_models"

    @patch("comfyfixersmart.inventory.config")
    def test_inventory_initialization_no_models_dir(self, mock_config):
        """Test ModelInventory initialization failure when no models dir."""
        mock_config.models_dir = None

        with pytest.raises(ValueError, match="models_dir must be provided"):
            ModelInventory()

    def test_build_inventory_filesystem_only(self, tmp_path):
        """Test building inventory from filesystem only."""
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        # Create model files
        checkpoints_dir = models_dir / "checkpoints"
        checkpoints_dir.mkdir()

        model1 = checkpoints_dir / "model1.safetensors"
        model1.write_bytes(b"x" * 2_000_000)  # 2MB

        loras_dir = models_dir / "loras"
        loras_dir.mkdir()

        model2 = loras_dir / "lora1.safetensors"
        model2.write_bytes(b"x" * 1_500_000)  # 1.5MB

        # Create non-model file
        readme = models_dir / "README.txt"
        readme.write_text("readme")

        inventory = ModelInventory(models_dir=str(models_dir))
        result = inventory.build_inventory(include_state_tracking=False)

        assert len(result) == 2
        assert "model1.safetensors" in result
        assert "lora1.safetensors" in result

        model1_info = result["model1.safetensors"]
        assert model1_info.size == 2_000_000
        assert model1_info.is_valid is True
        assert model1_info.path == str(model1)

    def test_build_inventory_with_state_tracking(self, tmp_path):
        """Test building inventory with state tracking."""
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        # Create a model file
        model_file = models_dir / "state_model.safetensors"
        model_file.write_bytes(b"x" * 2_000_000)

        # Mock state manager
        state_manager = Mock()
        state_manager.get_successful_downloads.return_value = {
            "state_model.safetensors": {"file_path": str(model_file), "file_size": 2_000_000}
        }

        inventory = ModelInventory(models_dir=str(models_dir), state_manager=state_manager)
        result = inventory.build_inventory(include_state_tracking=True)

        assert "state_model.safetensors" in result
        state_manager.get_successful_downloads.assert_called_once()

    def test_build_inventory_nonexistent_directory(self, tmp_path):
        """Test building inventory for nonexistent directory."""
        nonexistent_dir = tmp_path / "nonexistent"
        inventory = ModelInventory(models_dir=str(nonexistent_dir))

        result = inventory.build_inventory(include_state_tracking=False)

        assert result == {}

    def test_validate_model_file_valid(self, tmp_path):
        """Test validating a valid model file."""
        model_file = tmp_path / "valid.safetensors"
        model_file.write_bytes(b"x" * 2_000_000)  # 2MB

        inventory = ModelInventory(models_dir=str(tmp_path))
        is_valid, errors = inventory._validate_model_file(str(model_file), 2_000_000, 1_000_000)

        assert is_valid is True
        assert errors == []

    def test_validate_model_file_too_small(self, tmp_path):
        """Test validating a file that's too small."""
        small_file = tmp_path / "small.safetensors"
        small_file.write_bytes(b"x" * 500_000)  # 500KB

        inventory = ModelInventory(models_dir=str(tmp_path))
        is_valid, errors = inventory._validate_model_file(str(small_file), 500_000, 1_000_000)

        assert is_valid is False
        assert any("too small" in error.lower() for error in errors)

    def test_validate_model_file_empty(self, tmp_path):
        """Test validating an empty file."""
        empty_file = tmp_path / "empty.safetensors"
        empty_file.write_bytes(b"")

        inventory = ModelInventory(models_dir=str(tmp_path))
        is_valid, errors = inventory._validate_model_file(str(empty_file), 0, 1_000_000)

        assert is_valid is False
        assert any("empty" in error.lower() for error in errors)

    def test_validate_model_file_invalid_filename(self, tmp_path):
        """Test validating a file with invalid filename."""
        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_bytes(b"x" * 2_000_000)

        inventory = ModelInventory(models_dir=str(tmp_path))
        is_valid, errors = inventory._validate_model_file(str(invalid_file), 2_000_000, 1_000_000)

        assert is_valid is False
        assert any("filename" in error.lower() for error in errors)

    def test_validate_model_file_not_readable(self, tmp_path):
        """Test validating a non-readable file."""
        unreadable_file = tmp_path / "unreadable.safetensors"
        unreadable_file.write_bytes(b"x" * 2_000_000)

        # Make file unreadable (this might not work on all systems)
        try:
            os.chmod(unreadable_file, 0o000)
            inventory = ModelInventory(models_dir=str(tmp_path))
            is_valid, errors = inventory._validate_model_file(
                str(unreadable_file), 2_000_000, 1_000_000
            )

            # Restore permissions for cleanup
            os.chmod(unreadable_file, 0o644)

            assert is_valid is False
            assert any("readable" in error.lower() for error in errors)
        except OSError:
            # If we can't change permissions, skip this test
            pytest.skip("Cannot test file permissions on this system")

    def test_get_inventory_summary(self, tmp_path):
        """Test generating inventory summary."""
        models_dir = tmp_path / "models"

        # Create mock inventory
        inventory = {
            "model1.safetensors": ModelInfo(
                filename="model1.safetensors",
                path=str(models_dir / "model1.safetensors"),
                size=2_000_000,
                is_valid=True,
                validation_errors=[],
            ),
            "model2.ckpt": ModelInfo(
                filename="model2.ckpt",
                path=str(models_dir / "model2.ckpt"),
                size=1_500_000,
                is_valid=True,
                validation_errors=[],
            ),
            "invalid.safetensors": ModelInfo(
                filename="invalid.safetensors",
                path=str(models_dir / "invalid.safetensors"),
                size=500_000,
                is_valid=False,
                validation_errors=["Too small"],
            ),
        }

        inventory_manager = ModelInventory(models_dir=str(models_dir))
        summary = inventory_manager.get_inventory_summary(inventory)

        assert summary["total_models"] == 3
        assert summary["valid_models"] == 2
        assert summary["invalid_models"] == 1
        assert summary["total_size_bytes"] == 4_000_000
        assert summary["total_size_mb"] == 4_000_000 / (1024 * 1024)
        assert summary["extensions"][".safetensors"] == 2
        assert summary["extensions"][".ckpt"] == 1
        assert summary["models_dir"] == str(models_dir)

    def test_compare_inventories(self, tmp_path):
        """Test comparing two inventories."""
        models_dir = tmp_path / "models"

        # Old inventory
        old_inventory = {
            "existing1.safetensors": ModelInfo(
                filename="existing1.safetensors",
                path=str(models_dir / "existing1.safetensors"),
                size=2_000_000,
                is_valid=True,
                validation_errors=[],
            ),
            "changed.safetensors": ModelInfo(
                filename="changed.safetensors",
                path=str(models_dir / "changed.safetensors"),
                size=1_000_000,  # Old size
                is_valid=True,
                validation_errors=[],
            ),
            "removed.safetensors": ModelInfo(
                filename="removed.safetensors",
                path=str(models_dir / "removed.safetensors"),
                size=1_500_000,
                is_valid=True,
                validation_errors=[],
            ),
        }

        # New inventory
        new_inventory = {
            "existing1.safetensors": ModelInfo(
                filename="existing1.safetensors",
                path=str(models_dir / "existing1.safetensors"),
                size=2_000_000,
                is_valid=True,
                validation_errors=[],
            ),
            "changed.safetensors": ModelInfo(
                filename="changed.safetensors",
                path=str(models_dir / "changed.safetensors"),
                size=2_000_000,  # New size
                is_valid=True,
                validation_errors=[],
            ),
            "added.safetensors": ModelInfo(
                filename="added.safetensors",
                path=str(models_dir / "added.safetensors"),
                size=3_000_000,
                is_valid=True,
                validation_errors=[],
            ),
        }

        inventory_manager = ModelInventory(models_dir=str(models_dir))
        comparison = inventory_manager.compare_inventories(old_inventory, new_inventory)

        assert comparison["added"] == ["added.safetensors"]
        assert comparison["removed"] == ["removed.safetensors"]
        assert "changed.safetensors" in comparison["changed"]
        assert comparison["unchanged"] == 1  # existing1
        assert comparison["total_changes"] == 3

    def test_find_duplicates(self, tmp_path):
        """Test finding duplicate models."""
        models_dir = tmp_path / "models"

        inventory = {
            "model1.safetensors": ModelInfo(
                filename="model1.safetensors",
                path=str(models_dir / "checkpoints" / "model1.safetensors"),
                size=2_000_000,
                is_valid=True,
                validation_errors=[],
            ),
            "model1_duplicate.safetensors": ModelInfo(
                filename="model1.safetensors",  # Same filename
                path=str(models_dir / "loras" / "model1.safetensors"),
                size=2_000_000,
                is_valid=True,
                validation_errors=[],
            ),
            "unique.safetensors": ModelInfo(
                filename="unique.safetensors",
                path=str(models_dir / "checkpoints" / "unique.safetensors"),
                size=1_500_000,
                is_valid=True,
                validation_errors=[],
            ),
        }

        inventory_manager = ModelInventory(models_dir=str(models_dir))
        duplicates = inventory_manager.find_duplicates(inventory)

        assert len(duplicates) == 1
        assert "model1.safetensors" in duplicates
        assert len(duplicates["model1.safetensors"]) == 2

    def test_validate_inventory_integrity_valid(self, tmp_path):
        """Test validating inventory integrity with valid inventory."""
        models_dir = tmp_path / "models"

        # Create actual files
        model_file = models_dir / "checkpoints" / "model.safetensors"
        model_file.parent.mkdir(parents=True)
        model_file.write_bytes(b"x" * 2_000_000)

        inventory = {
            "model.safetensors": ModelInfo(
                filename="model.safetensors",
                path=str(model_file),
                size=2_000_000,
                is_valid=True,
                validation_errors=[],
            )
        }

        inventory_manager = ModelInventory(models_dir=str(models_dir))
        result = inventory_manager.validate_inventory_integrity(inventory)

        assert result["valid"] is True
        assert result["errors"] == []
        assert result["stats"]["total_models"] == 1
        assert result["stats"]["missing_files"] == 0

    def test_validate_inventory_integrity_missing_file(self, tmp_path):
        """Test validating inventory integrity with missing file."""
        models_dir = tmp_path / "models"

        inventory = {
            "missing.safetensors": ModelInfo(
                filename="missing.safetensors",
                path=str(models_dir / "missing.safetensors"),
                size=2_000_000,
                is_valid=True,
                validation_errors=[],
            )
        }

        inventory_manager = ModelInventory(models_dir=str(models_dir))
        result = inventory_manager.validate_inventory_integrity(inventory)

        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert "not found" in result["errors"][0].lower()
        assert result["stats"]["missing_files"] == 1

    def test_validate_inventory_integrity_with_duplicates(self, tmp_path):
        """Test validating inventory integrity with duplicates."""
        models_dir = tmp_path / "models"

        inventory = {
            "model1.safetensors": ModelInfo(
                filename="model1.safetensors",
                path=str(models_dir / "path1" / "model1.safetensors"),
                size=2_000_000,
                is_valid=True,
                validation_errors=[],
            ),
            "model1_duplicate.safetensors": ModelInfo(
                filename="model1.safetensors",
                path=str(models_dir / "path2" / "model1.safetensors"),
                size=2_000_000,
                is_valid=True,
                validation_errors=[],
            ),
        }

        inventory_manager = ModelInventory(models_dir=str(models_dir))
        result = inventory_manager.validate_inventory_integrity(inventory)

        assert result["valid"] is True  # Duplicates are warnings, not errors
        assert len(result["warnings"]) > 0
        assert "duplicate" in result["warnings"][0].lower()
        assert result["stats"]["duplicate_groups"] == 1

    def test_export_inventory_json(self, tmp_path):
        """Test exporting inventory to JSON."""
        models_dir = tmp_path / "models"
        output_file = tmp_path / "inventory.json"

        inventory = {
            "model1.safetensors": ModelInfo(
                filename="model1.safetensors",
                path=str(models_dir / "model1.safetensors"),
                size=2_000_000,
                is_valid=True,
                validation_errors=[],
            )
        }

        inventory_manager = ModelInventory(models_dir=str(models_dir))
        result = inventory_manager.export_inventory(inventory, str(output_file), format="json")

        assert result is True
        assert output_file.exists()

        # Verify content
        with open(output_file, "r") as f:
            data = json.load(f)

        assert "metadata" in data
        assert "models" in data
        assert data["metadata"]["total_models"] == 1
        assert "model1.safetensors" in data["models"]

    def test_export_inventory_csv(self, tmp_path):
        """Test exporting inventory to CSV."""
        models_dir = tmp_path / "models"
        output_file = tmp_path / "inventory.csv"

        inventory = {
            "model1.safetensors": ModelInfo(
                filename="model1.safetensors",
                path=str(models_dir / "model1.safetensors"),
                size=2_000_000,
                is_valid=True,
                validation_errors=[],
            )
        }

        inventory_manager = ModelInventory(models_dir=str(models_dir))
        result = inventory_manager.export_inventory(inventory, str(output_file), format="csv")

        assert result is True
        assert output_file.exists()

        # Verify content
        with open(output_file, "r") as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert len(rows) == 2  # Header + 1 data row
        assert rows[0] == ["filename", "path", "size", "is_valid"]
        assert rows[1][0] == "model1.safetensors"

    def test_export_inventory_invalid_format(self, tmp_path):
        """Test exporting inventory with invalid format."""
        models_dir = tmp_path / "models"
        output_file = tmp_path / "inventory.txt"

        inventory = {
            "model1.safetensors": ModelInfo(
                filename="model1.safetensors",
                path=str(models_dir / "model1.safetensors"),
                size=2_000_000,
                is_valid=True,
                validation_errors=[],
            )
        }

        inventory_manager = ModelInventory(models_dir=str(models_dir))
        result = inventory_manager.export_inventory(inventory, str(output_file), format="invalid")

        assert result is False


class TestConvenienceFunctions:
    """Test backward compatibility convenience functions."""

    def test_build_local_inventory_function(self, tmp_path):
        """Test build_local_inventory convenience function."""
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        # Create model files
        model1 = models_dir / "model1.safetensors"
        model1.write_bytes(b"x" * 2_000_000)

        model2 = models_dir / "model2.ckpt"
        model2.write_bytes(b"x" * 1_500_000)

        # Create non-model file
        readme = models_dir / "README.txt"
        readme.write_text("readme")

        inventory = build_local_inventory(str(models_dir))

        assert len(inventory) == 2
        assert "model1.safetensors" in inventory
        assert "model2.ckpt" in inventory


class TestInventoryIntegration:
    """Integration tests for inventory functionality."""

    def test_full_inventory_workflow(self, tmp_path):
        """Test complete inventory building and management workflow."""
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        # Create directory structure
        checkpoints_dir = models_dir / "checkpoints"
        checkpoints_dir.mkdir()

        loras_dir = models_dir / "loras"
        loras_dir.mkdir()

        # Create model files
        model1 = checkpoints_dir / "checkpoint1.safetensors"
        model1.write_bytes(b"x" * 2_000_000)

        model2 = loras_dir / "lora1.safetensors"
        model2.write_bytes(b"x" * 1_500_000)

        model3 = checkpoints_dir / "checkpoint2.ckpt"
        model3.write_bytes(b"x" * 3_000_000)

        # Create invalid files
        small_model = checkpoints_dir / "small.safetensors"
        small_model.write_bytes(b"x" * 500_000)  # Too small

        non_model = models_dir / "readme.txt"
        non_model.write_text("readme")

        # Build inventory
        inventory_manager = ModelInventory(models_dir=str(models_dir))
        inventory = inventory_manager.build_inventory(include_state_tracking=False)

        # Verify inventory
        assert len(inventory) == 3  # Only valid model files
        assert "checkpoint1.safetensors" in inventory
        assert "lora1.safetensors" in inventory
        assert "checkpoint2.ckpt" in inventory

        # Get summary
        summary = inventory_manager.get_inventory_summary(inventory)
        assert summary["total_models"] == 3
        assert summary["valid_models"] == 3
        assert summary["total_size_bytes"] == 6_500_000

        # Export to JSON
        export_file = tmp_path / "exported_inventory.json"
        success = inventory_manager.export_inventory(inventory, str(export_file), format="json")
        assert success is True
        assert export_file.exists()

        # Validate integrity
        validation = inventory_manager.validate_inventory_integrity(inventory)
        assert validation["valid"] is True
        assert validation["stats"]["total_models"] == 3

        # Test comparison with modified inventory
        # Simulate adding a new model
        new_model = checkpoints_dir / "new_model.safetensors"
        new_model.write_bytes(b"x" * 1_000_000)

        new_inventory = inventory_manager.build_inventory(include_state_tracking=False)
        comparison = inventory_manager.compare_inventories(inventory, new_inventory)

        assert len(comparison["added"]) == 1
        assert "new_model.safetensors" in comparison["added"]
        assert comparison["total_changes"] == 1

    def test_inventory_with_state_manager_integration(self, tmp_path):
        """Test inventory building with state manager integration."""
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        # Create filesystem model
        fs_model = models_dir / "filesystem_model.safetensors"
        fs_model.write_bytes(b"x" * 2_000_000)

        # Mock state manager with additional model
        state_manager = Mock()
        state_manager.get_successful_downloads.return_value = {
            "state_model.safetensors": {
                "file_path": str(models_dir / "state_model.safetensors"),
                "file_size": 1_500_000,
            }
        }

        # Create the state model file
        state_model = models_dir / "state_model.safetensors"
        state_model.write_bytes(b"x" * 1_500_000)

        inventory_manager = ModelInventory(models_dir=str(models_dir), state_manager=state_manager)

        inventory = inventory_manager.build_inventory(include_state_tracking=True)

        assert len(inventory) == 2
        assert "filesystem_model.safetensors" in inventory
        assert "state_model.safetensors" in inventory

        # Verify state manager was called
        state_manager.get_successful_downloads.assert_called_once()
