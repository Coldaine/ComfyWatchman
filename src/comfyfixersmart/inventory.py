"""
Model Inventory Module for ComfyFixerSmart

Provides comprehensive local model inventory building, validation, and management.
Supports file size checking, state tracking integration, and inventory comparison.

Classes:
    ModelInventory: Main inventory management class
    ModelInfo: Data class for model information

Functions:
    build_local_inventory: Build inventory of local models with validation
    compare_inventories: Compare two inventories and generate diff
    validate_inventory: Validate inventory integrity
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass

from .config import config
from .logging import get_logger
from .state_manager import StateManager
from .utils import get_file_size, validate_model_filename


@dataclass
class ModelInfo:
    """Information about a local model file."""

    filename: str
    path: str
    size: int
    is_valid: bool
    validation_errors: List[str]


class ModelInventory:
    """
    Comprehensive model inventory management for ComfyUI models.

    Handles building inventories with validation, state tracking integration,
    and comparison operations.
    """

    def __init__(
        self,
        models_dir: Optional[str] = None,
        state_manager: Optional[StateManager] = None,
        logger=None,
    ):
        """
        Initialize the model inventory manager.

        Args:
            models_dir: Directory containing models (uses config default if None)
            state_manager: StateManager instance for tracking
            logger: Optional logger instance
        """
        if models_dir:
            self.models_dir = Path(models_dir)
        elif config.models_dir:
            self.models_dir = config.models_dir
        else:
            raise ValueError("models_dir must be provided or configured in config")
        self.state_manager = state_manager
        self.logger = logger or get_logger("ModelInventory")

    def build_inventory(
        self, include_state_tracking: bool = True, min_file_size: int = 1_000_000
    ) -> Dict[str, ModelInfo]:
        """
        Build comprehensive inventory of local models with validation.

        Args:
            include_state_tracking: Whether to include models from state manager
            min_file_size: Minimum file size in bytes to consider valid

        Returns:
            Dictionary mapping filename to ModelInfo
        """
        self.logger.info("Building local model inventory...")

        inventory = {}

        # Scan filesystem
        filesystem_inventory = self._scan_filesystem(min_file_size)
        inventory.update(filesystem_inventory)

        # Include state-tracked models if requested
        if include_state_tracking and self.state_manager:
            state_inventory = self._get_state_tracked_models(min_file_size)
            inventory.update(state_inventory)

        self.logger.info(f"Found {len(inventory)} valid local models")
        return inventory

    def _scan_filesystem(self, min_file_size: int) -> Dict[str, ModelInfo]:
        """Scan filesystem for model files."""
        inventory = {}

        if not self.models_dir.exists():
            self.logger.warning(f"Models directory does not exist: {self.models_dir}")
            return inventory

        model_extensions = config.model_extensions

        for model_file in self.models_dir.rglob("*"):
            if not model_file.is_file():
                continue

            if model_file.suffix.lower() not in model_extensions:
                continue

            filename = model_file.name
            file_path = str(model_file)

            # Get file size
            try:
                file_size = model_file.stat().st_size
            except OSError as e:
                self.logger.warning(f"Cannot get size for {filename}: {e}")
                continue

            # Validate file
            is_valid, errors = self._validate_model_file(file_path, file_size, min_file_size)

            if not is_valid:
                for error in errors:
                    self.logger.warning(f"Skipping {filename}: {error}")
                continue

            inventory[filename] = ModelInfo(
                filename=filename,
                path=file_path,
                size=file_size,
                is_valid=True,
                validation_errors=[],
            )

        return inventory

    def _validate_model_file(
        self, file_path: str, file_size: int, min_file_size: int
    ) -> Tuple[bool, List[str]]:
        """
        Validate a model file.

        Args:
            file_path: Path to the model file
            file_size: Size of the file in bytes
            min_file_size: Minimum acceptable file size

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check file size
        if file_size == 0:
            errors.append("File is empty (0 bytes)")
            return False, errors

        if file_size < min_file_size:
            errors.append(f"File too small ({file_size} bytes, minimum {min_file_size})")
            return False, errors

        # Check filename validity
        filename = os.path.basename(file_path)
        if not validate_model_filename(filename):
            errors.append("Invalid filename format")
            return False, errors

        # Check if file is readable
        try:
            with open(file_path, "rb") as f:
                f.read(1)  # Try to read first byte
        except OSError as e:
            errors.append(f"File not readable: {e}")
            return False, errors

        return True, errors

    def _get_state_tracked_models(self, min_file_size: int) -> Dict[str, ModelInfo]:
        """Get models tracked by the state manager."""
        if not self.state_manager:
            return {}

        inventory = {}
        successful = self.state_manager.get_successful_downloads()

        for filename, info in successful.items():
            file_path = info.get("file_path")
            if not file_path or not os.path.exists(file_path):
                continue

            file_size = get_file_size(file_path)
            if file_size and file_size >= min_file_size:
                inventory[filename] = ModelInfo(
                    filename=filename,
                    path=file_path,
                    size=file_size,
                    is_valid=True,
                    validation_errors=[],
                )
                self.logger.info(f"Added from state: {filename}")

        return inventory

    def get_inventory_summary(self, inventory: Dict[str, ModelInfo]) -> Dict[str, Any]:
        """
        Generate a summary of the inventory.

        Args:
            inventory: Model inventory dictionary

        Returns:
            Dictionary with summary statistics
        """
        total_size = sum(info.size for info in inventory.values())
        valid_count = sum(1 for info in inventory.values() if info.is_valid)

        # Group by file extension
        extensions = {}
        for info in inventory.values():
            ext = Path(info.filename).suffix.lower()
            extensions[ext] = extensions.get(ext, 0) + 1

        return {
            "total_models": len(inventory),
            "valid_models": valid_count,
            "invalid_models": len(inventory) - valid_count,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "extensions": extensions,
            "models_dir": str(self.models_dir),
        }

    def compare_inventories(
        self, old_inventory: Dict[str, ModelInfo], new_inventory: Dict[str, ModelInfo]
    ) -> Dict[str, Any]:
        """
        Compare two inventories and generate a diff.

        Args:
            old_inventory: Previous inventory
            new_inventory: Current inventory

        Returns:
            Dictionary with comparison results
        """
        old_files = set(old_inventory.keys())
        new_files = set(new_inventory.keys())

        added = new_files - old_files
        removed = old_files - new_files
        common = old_files & new_files

        changed = {}
        for filename in common:
            old_info = old_inventory[filename]
            new_info = new_inventory[filename]
            if old_info.size != new_info.size or old_info.path != new_info.path:
                changed[filename] = {
                    "old": {"size": old_info.size, "path": old_info.path},
                    "new": {"size": new_info.size, "path": new_info.path},
                }

        return {
            "added": list(added),
            "removed": list(removed),
            "changed": changed,
            "unchanged": len(common) - len(changed),
            "total_changes": len(added) + len(removed) + len(changed),
        }

    def find_duplicates(self, inventory: Dict[str, ModelInfo]) -> Dict[str, List[str]]:
        """
        Find duplicate models (same filename, different paths).

        Args:
            inventory: Model inventory dictionary

        Returns:
            Dictionary mapping filename to list of paths
        """
        duplicates = {}

        # Group by filename
        filename_to_paths = {}
        for info in inventory.values():
            if info.filename not in filename_to_paths:
                filename_to_paths[info.filename] = []
            filename_to_paths[info.filename].append(info.path)

        # Find duplicates
        for filename, paths in filename_to_paths.items():
            if len(paths) > 1:
                duplicates[filename] = paths

        return duplicates

    def validate_inventory_integrity(self, inventory: Dict[str, ModelInfo]) -> Dict[str, Any]:
        """
        Validate the integrity of an inventory.

        Args:
            inventory: Model inventory dictionary

        Returns:
            Dictionary with validation results
        """
        results = {"valid": True, "errors": [], "warnings": [], "stats": {}}

        # Check for missing files
        missing_files = []
        for filename, info in inventory.items():
            if not os.path.exists(info.path):
                missing_files.append(filename)
                results["errors"].append(f"File not found: {info.path}")

        # Check for duplicates
        duplicates = self.find_duplicates(inventory)
        if duplicates:
            results["warnings"].append(f"Found {len(duplicates)} duplicate filenames")
            results["duplicate_files"] = duplicates

        # Check file sizes
        suspicious_sizes = []
        for info in inventory.values():
            if info.size < 100_000:  # Less than 100KB
                suspicious_sizes.append(f"{info.filename}: {info.size} bytes")

        if suspicious_sizes:
            results["warnings"].extend(suspicious_sizes)

        results["stats"] = {
            "total_models": len(inventory),
            "missing_files": len(missing_files),
            "duplicate_groups": len(duplicates),
            "suspicious_sizes": len(suspicious_sizes),
        }

        results["valid"] = len(results["errors"]) == 0
        return results

    def export_inventory(
        self, inventory: Dict[str, ModelInfo], output_path: str, format: str = "json"
    ) -> bool:
        """
        Export inventory to a file.

        Args:
            inventory: Model inventory dictionary
            output_path: Path to output file
            format: Export format ('json' or 'csv')

        Returns:
            True if export successful
        """
        try:
            if format.lower() == "json":
                data = {
                    "metadata": {
                        "export_time": (
                            str(Path(output_path).stat().st_mtime)
                            if Path(output_path).exists()
                            else None
                        ),
                        "total_models": len(inventory),
                        "models_dir": str(self.models_dir),
                    },
                    "models": {
                        filename: {
                            "path": info.path,
                            "size": info.size,
                            "is_valid": info.is_valid,
                            "validation_errors": info.validation_errors,
                        }
                        for filename, info in inventory.items()
                    },
                }
                import json

                with open(output_path, "w") as f:
                    json.dump(data, f, indent=2)

            elif format.lower() == "csv":
                import csv

                with open(output_path, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["filename", "path", "size", "is_valid"])
                    for filename, info in inventory.items():
                        writer.writerow([filename, info.path, info.size, info.is_valid])
            else:
                self.logger.error(f"Unsupported export format: {format}")
                return False

            self.logger.info(f"Exported inventory to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export inventory: {e}")
            return False


# Convenience functions for backward compatibility
def build_local_inventory(
    models_dir=None,
    state_manager=None,
    logger=None,
    include_state_tracking=True,
    min_file_size=1_000_000,
):
    """
    Convenience function to build local model inventory.

    Args:
        models_dir: Directory containing models
        state_manager: StateManager instance
        logger: Optional logger instance
        include_state_tracking: Whether to include state-tracked models
        min_file_size: Minimum file size to consider valid

    Returns:
        Dictionary mapping filename to ModelInfo (for detailed access)
        or set of filenames (for backward compatibility)
    """
    inventory_manager = ModelInventory(models_dir, state_manager, logger)
    inventory = inventory_manager.build_inventory(include_state_tracking, min_file_size)

    # Return set of filenames for backward compatibility
    return set(inventory.keys())


def compare_inventories(old_inventory, new_inventory, logger=None):
    """
    Convenience function to compare two inventories.

    Args:
        old_inventory: Previous inventory (set or dict)
        new_inventory: Current inventory (set or dict)
        logger: Optional logger instance

    Returns:
        Dictionary with comparison results
    """
    # Convert sets to dict format if needed
    if isinstance(old_inventory, set):
        old_dict = {filename: ModelInfo(filename, "", 0, True, []) for filename in old_inventory}
    else:
        old_dict = old_inventory

    if isinstance(new_inventory, set):
        new_dict = {filename: ModelInfo(filename, "", 0, True, []) for filename in new_inventory}
    else:
        new_dict = new_inventory

    inventory_manager = ModelInventory(logger=logger)
    return inventory_manager.compare_inventories(old_dict, new_dict)
