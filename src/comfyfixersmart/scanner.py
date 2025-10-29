"""
Workflow Scanner Module for ComfyFixerSmart

Provides comprehensive workflow scanning, parsing, and model extraction capabilities.
Supports multiple workflow directory scanning, workflow validation, and integration
with the ScanTool functionality.

Classes:
    WorkflowScanner: Main scanner class for discovering and parsing workflows

Functions:
    scan_workflows: Scan workflow directories for JSON files
    extract_models_from_workflow: Parse workflow and extract model references
    validate_workflow: Validate workflow structure and content
"""

import asyncio
import glob
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import for integration
from .adapters.copilot_validator import CopilotValidator
from .config import config
from .logging import get_logger
from .utils import _is_model_filename, determine_model_type, validate_json_file


@dataclass
class WorkflowInfo:
    """Information about a scanned workflow."""

    path: str
    filename: str
    size: int
    is_valid: bool
    model_count: int
    node_count: int
    errors: List[str]
    copilot_validation_report: Optional[Dict[str, Any]] = None


@dataclass
class ModelReference:
    """A model reference extracted from a workflow."""

    filename: str
    type: str
    node_type: str
    workflow_path: str
    node_id: Optional[str] = None
    widget_name: Optional[str] = None


class WorkflowScanner:
    """
    Comprehensive workflow scanner for ComfyUI workflows.

    Handles scanning multiple directories, parsing workflow JSON files,
    extracting model references, and validating workflow structure.
    """

    def __init__(self, logger=None):
        """
        Initialize the workflow scanner.

        Args:
            logger: Optional logger instance. If None, uses default logger.
        """
        self.logger = logger or get_logger("WorkflowScanner")
        self.validator = CopilotValidator(logger=self.logger)

    def scan_workflows(
        self, specific_paths: Optional[List[str]] = None, workflow_dirs: Optional[List[str]] = None
    ) -> List[str]:
        """
        Scan workflow directories for JSON files.

        Args:
            specific_paths: List of specific workflow file paths to scan
            workflow_dirs: List of directories to scan (uses config default if None)

        Returns:
            List of valid workflow file paths
        """
        self.logger.info("=== Scanning Workflows ===")

        if specific_paths:
            return self._scan_specific_paths(specific_paths)

        # Scan directories
        workflow_dirs = workflow_dirs or config.workflow_dirs
        all_workflows = []

        for directory in workflow_dirs:
            if not os.path.exists(directory):
                self.logger.warning(f"Skipping non-existent directory: {directory}")
                continue

            self.logger.info(f"Scanning: {directory}")
            found = glob.glob(f"{directory}/**/*.json", recursive=True)
            all_workflows.extend(found)
            self.logger.info(f"Found {len(found)} workflows")

        self.logger.info(f"Total workflows found: {len(all_workflows)}")
        return all_workflows

    def _scan_specific_paths(self, paths: List[str]) -> List[str]:
        """Scan specific workflow file paths."""
        workflows = []
        for path in paths:
            if os.path.exists(path) and path.endswith(".json"):
                workflows.append(path)
                self.logger.info(f"Added: {path}")
            else:
                self.logger.warning(f"Not found or not JSON: {path}")
        self.logger.info(f"Total workflows to scan: {len(workflows)}")
        return workflows

    async def scan_workflows_detailed(
        self, specific_paths: Optional[List[str]] = None, workflow_dirs: Optional[List[str]] = None
    ) -> List[WorkflowInfo]:
        """
        Scan workflows and return detailed information about each workflow, running analysis in parallel.

        Args:
            specific_paths: List of specific workflow file paths to scan
            workflow_dirs: List of directories to scan

        Returns:
            List of WorkflowInfo objects with detailed workflow metadata
        """
        workflow_paths = self.scan_workflows(specific_paths, workflow_dirs)

        tasks = [self._analyze_workflow(path) for path in workflow_paths]
        detailed_info = await asyncio.gather(*tasks)

        return detailed_info

    async def _analyze_workflow(self, workflow_path: str) -> WorkflowInfo:
        """Analyze a single workflow file and return detailed information."""
        path_obj = Path(workflow_path)
        errors = []

        try:
            size = path_obj.stat().st_size
        except OSError as e:
            errors.append(f"Cannot read file size: {e}")
            size = 0

        is_valid = validate_json_file(workflow_path)
        if not is_valid:
            errors.append("Invalid JSON format")

        model_count = 0
        node_count = 0
        validation_report = None

        if is_valid:
            try:
                # This part is synchronous and CPU-bound, so it's fine to run it directly.
                models, nodes = self.extract_models_from_workflow(
                    workflow_path, return_node_count=True
                )
                model_count = len(models)
                node_count = nodes
            except Exception as e:
                errors.append(f"Error extracting models: {e}")
                is_valid = False

        # Conditionally run the Copilot validation if enabled and available
        if is_valid and config.copilot.enabled and config.copilot.validation:
            if self.validator.is_available():
                # This is an async network call, so we await it.
                validation_report = await self.validator.validate(workflow_path)
                if validation_report is None and config.copilot.require_comfyui:
                    errors.append("Copilot validation failed, and it is required by config.")
            elif config.copilot.require_comfyui:
                errors.append(
                    "Copilot validation is required by config, but the backend is not available."
                )

        return WorkflowInfo(
            path=workflow_path,
            filename=path_obj.name,
            size=size,
            is_valid=is_valid and not errors,  # Mark as invalid if validation fails and is required
            model_count=model_count,
            node_count=node_count,
            errors=errors,
            copilot_validation_report=validation_report,
        )

    def extract_models_from_workflow(self, workflow_path: str, return_node_count: bool = False):
        """
        Parse workflow and extract model references.

        Args:
            workflow_path: Path to the workflow JSON file
            return_node_count: If True, return tuple of (models, node_count)

        Returns:
            List of ModelReference objects, or tuple if return_node_count=True
        """
        try:
            with open(workflow_path, encoding="utf-8") as f:
                data = json.load(f)

            models = []
            nodes = data.get("nodes", [])

            for node in nodes:
                node_type = node.get("type", "")
                node_id = node.get("id", "")

                # Check widgets_values for model filenames
                for i, value in enumerate(node.get("widgets_values", [])):
                    if isinstance(value, str) and _is_model_filename(value):
                        # Normalize filename from either POSIX or Windows-style paths
                        # os.path.basename does not treat backslashes as separators on POSIX
                        # so split on both separators to robustly obtain the basename
                        try:
                            parts = re.split(r"[\\/]+", value)
                            filename = parts[-1] if parts else value
                        except Exception:
                            filename = os.path.basename(value)
                        model_type = determine_model_type(node_type)

                        model_ref = ModelReference(
                            filename=filename,
                            type=model_type,
                            node_type=node_type,
                            workflow_path=workflow_path,
                            node_id=node_id,
                            widget_name=f"widgets_values[{i}]",
                        )
                        models.append(model_ref)

            if return_node_count:
                return models, len(nodes)
            return models

        except (json.JSONDecodeError, OSError) as e:
            self.logger.error(f"Error parsing workflow {workflow_path}: {e}")
            if return_node_count:
                return [], 0
            return []

    def validate_workflow(self, workflow_path: str) -> Dict[str, Any]:
        """
        Validate workflow structure and content.

        Args:
            workflow_path: Path to the workflow JSON file

        Returns:
            Dictionary with validation results
        """
        result = {
            "path": workflow_path,
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "stats": {},
        }

        try:
            with open(workflow_path, encoding="utf-8") as f:
                data = json.load(f)

            # Basic structure validation
            if not isinstance(data, dict):
                result["errors"].append("Workflow must be a JSON object")
                return result

            nodes = data.get("nodes", [])
            if not isinstance(nodes, list):
                result["errors"].append("'nodes' must be a list")
                return result

            # Node validation
            node_ids = set()
            for node in nodes:
                if not isinstance(node, dict):
                    result["errors"].append("Each node must be a JSON object")
                    continue

                node_id = node.get("id")
                if node_id is None:
                    result["warnings"].append("Node missing 'id' field")
                elif node_id in node_ids:
                    result["errors"].append(f"Duplicate node ID: {node_id}")
                else:
                    node_ids.add(node_id)

                if "type" not in node:
                    result["errors"].append(f"Node {node_id} missing 'type' field")

            # Model reference validation
            models = self.extract_models_from_workflow(workflow_path)
            invalid_models = []

            for model in models:
                if not model.filename:
                    invalid_models.append("Empty filename")
                elif len(model.filename) > 255:
                    invalid_models.append(f"Filename too long: {model.filename[:50]}...")

            if invalid_models:
                result["warnings"].extend(invalid_models)

            result["is_valid"] = len(result["errors"]) == 0
            result["stats"] = {
                "node_count": len(nodes),
                "model_count": len(models),
                "unique_model_types": len(set(m.type for m in models)),
                "unique_node_types": len(
                    set(n.get("type", "") for n in nodes if isinstance(n, dict))
                ),
            }

        except (json.JSONDecodeError, OSError) as e:
            result["errors"].append(f"Parse error: {e}")

        return result

    def get_workflow_summary(self, workflow_paths: List[str]) -> Dict[str, Any]:
        """
        Generate a summary of multiple workflows.

        Args:
            workflow_paths: List of workflow file paths

        Returns:
            Dictionary with summary statistics
        """
        summary = {
            "total_workflows": len(workflow_paths),
            "valid_workflows": 0,
            "invalid_workflows": 0,
            "total_models": 0,
            "unique_models": set(),
            "model_types": {},
            "node_types": {},
            "errors": [],
        }

        for path in workflow_paths:
            try:
                models = self.extract_models_from_workflow(path)
                summary["total_models"] += len(models)

                for model in models:
                    summary["unique_models"].add(model.filename)
                    summary["model_types"][model.type] = (
                        summary["model_types"].get(model.type, 0) + 1
                    )
                    summary["node_types"][model.node_type] = (
                        summary["node_types"].get(model.node_type, 0) + 1
                    )

                summary["valid_workflows"] += 1

            except Exception as e:
                summary["invalid_workflows"] += 1
                summary["errors"].append(f"{path}: {e}")

        summary["unique_models"] = len(summary["unique_models"])
        return summary


# Convenience functions for backward compatibility
def scan_workflows(specific_paths=None, workflow_dirs=None, logger=None):
    """
    Convenience function to scan workflows.

    Args:
        specific_paths: List of specific workflow paths
        workflow_dirs: List of directories to scan
        logger: Optional logger instance

    Returns:
        List of workflow file paths
    """
    scanner = WorkflowScanner(logger)
    return scanner.scan_workflows(specific_paths, workflow_dirs)


def extract_models_from_workflow(workflow_path, logger=None):
    """
    Convenience function to extract models from a workflow.

    Args:
        workflow_path: Path to workflow file
        logger: Optional logger instance

    Returns:
        List of model dictionaries (for backward compatibility)
    """
    scanner = WorkflowScanner(logger)
    models = scanner.extract_models_from_workflow(workflow_path)

    # Convert to dictionary format for backward compatibility
    return [
        {
            "filename": m.filename,
            "type": m.type,
            "node_type": m.node_type,
            "workflow": os.path.basename(m.workflow_path),
        }
        for m in models
    ]
