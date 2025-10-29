"""
Integration tests for the core module.

Tests the main ComfyFixerSmart workflow orchestration,
integrating scanner, search, inventory, and download components.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from comfyfixersmart.core import ComfyFixerCore, WorkflowRun, run_comfy_fixer


class TestWorkflowRun:
    """Test WorkflowRun dataclass."""

    def test_workflow_run_creation(self):
        """Test creating a WorkflowRun instance."""
        from datetime import datetime

        start_time = datetime.now()

        run = WorkflowRun(
            run_id="test_run_123",
            start_time=start_time,
            status="running",
            workflows_scanned=5,
            models_found=10,
            models_missing=3,
            models_resolved=7,
            downloads_generated=7,
        )

        assert run.run_id == "test_run_123"
        assert run.start_time == start_time
        assert run.status == "running"
        assert run.workflows_scanned == 5
        assert run.models_found == 10
        assert run.models_missing == 3
        assert run.models_resolved == 7
        assert run.downloads_generated == 7
        assert run.end_time is None
        assert run.output_dir is None

    def test_workflow_run_defaults(self):
        """Test WorkflowRun default values."""
        from datetime import datetime

        run = WorkflowRun(run_id="test", start_time=datetime.now())

        assert run.status == "running"
        assert run.workflows_scanned == 0
        assert run.models_found == 0
        assert run.models_missing == 0
        assert run.models_resolved == 0
        assert run.downloads_generated == 0
        assert run.end_time is None
        assert run.output_dir is None


class TestComfyFixerCore:
    """Test ComfyFixerCore class functionality."""

    def test_core_initialization(self):
        """Test ComfyFixerCore initialization."""
        core = ComfyFixerCore()
        assert core.logger is not None
        assert hasattr(core, "scanner")
        assert hasattr(core, "search")
        assert hasattr(core, "inventory")
        assert hasattr(core, "downloader")

    @patch("comfyfixersmart.core.WorkflowScanner")
    @patch("comfyfixersmart.core.ModelSearch")
    @patch("comfyfixersmart.core.ModelInventory")
    @patch("comfyfixersmart.core.DownloadManager")
    def test_core_initialization_with_mocks(
        self, mock_download, mock_inventory, mock_search, mock_scanner
    ):
        """Test ComfyFixerCore initialization with mocked dependencies."""
        core = ComfyFixerCore()

        # Verify that dependencies are initialized
        mock_scanner.assert_called_once()
        mock_search.assert_called_once()
        mock_inventory.assert_called_once()
        mock_download.assert_called_once()

    def test_run_workflow_scan_only(self, tmp_path):
        """Test running workflow scan only."""
        # Create test workflow
        workflow_dir = tmp_path / "workflows"
        workflow_dir.mkdir()

        workflow_file = workflow_dir / "test_workflow.json"
        workflow_data = {
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["model.safetensors"],
                }
            ]
        }
        workflow_file.write_text(json.dumps(workflow_data))

        core = ComfyFixerCore()

        # Mock the scanner to return our test workflow
        core.scanner.scan_workflows.return_value = [str(workflow_file)]

        # Mock other components
        core.search.search_model.return_value = {
            "status": "FOUND",
            "filename": "model.safetensors",
            "download_url": "https://example.com/model",
        }
        core.inventory.build_inventory.return_value = {}
        core.downloader.create_download_tasks.return_value = []

        result = core.run(scan_only=True, workflow_dirs=[str(workflow_dir)])

        assert result is not None
        assert "workflows_scanned" in result
        assert result["workflows_scanned"] >= 1

        # Verify scanner was called
        core.scanner.scan_workflows.assert_called()

    def test_run_full_workflow(self, tmp_path):
        """Test running full ComfyFixerSmart workflow."""
        # Create test workflow
        workflow_dir = tmp_path / "workflows"
        workflow_dir.mkdir()

        workflow_file = workflow_dir / "test_workflow.json"
        workflow_data = {
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["missing_model.safetensors"],
                }
            ]
        }
        workflow_file.write_text(json.dumps(workflow_data))

        core = ComfyFixerCore()

        # Mock components
        core.scanner.scan_workflows.return_value = [str(workflow_file)]
        core.scanner.extract_models_from_workflow.return_value = [
            Mock(filename="missing_model.safetensors", type="checkpoints")
        ]

        # Mock search - model not found locally
        core.search.search_model.return_value = {
            "status": "FOUND",
            "filename": "missing_model.safetensors",
            "download_url": "https://example.com/model",
            "type": "checkpoints",
        }

        # Mock inventory - model not in local inventory
        core.inventory.build_inventory.return_value = {}

        # Mock download task creation
        mock_task = Mock()
        mock_task.filename = "missing_model.safetensors"
        core.downloader.create_download_tasks.return_value = [mock_task]

        result = core.run(workflow_dirs=[str(workflow_dir)], generate_scripts=True)

        assert result is not None
        assert result["workflows_scanned"] >= 1
        assert result["models_found"] >= 1

        # Verify all components were called
        core.scanner.scan_workflows.assert_called()
        core.inventory.build_inventory.assert_called()
        core.search.search_model.assert_called()
        core.downloader.create_download_tasks.assert_called()

    def test_run_with_existing_models(self, tmp_path):
        """Test running workflow when models already exist locally."""
        # Create test workflow
        workflow_file = tmp_path / "workflow.json"
        workflow_data = {
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["existing_model.safetensors"],
                }
            ]
        }
        workflow_file.write_text(json.dumps(workflow_data))

        # Create the model file locally
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        model_file = models_dir / "existing_model.safetensors"
        model_file.write_bytes(b"x" * 2_000_000)  # 2MB file

        core = ComfyFixerCore()

        # Mock components
        core.scanner.scan_workflows.return_value = [str(workflow_file)]
        core.scanner.extract_models_from_workflow.return_value = [
            Mock(filename="existing_model.safetensors", type="checkpoints")
        ]

        # Mock inventory to return the existing model
        core.inventory.build_inventory.return_value = {
            "existing_model.safetensors": Mock(
                filename="existing_model.safetensors",
                path=str(model_file),
                size=2_000_000,
                is_valid=True,
            )
        }

        result = core.run(workflow_dirs=[str(tmp_path)], scan_only=True)

        assert result is not None
        assert result["models_found"] >= 1
        # Should not try to search or download since model exists
        core.search.search_model.assert_not_called()

    def test_run_error_handling(self, tmp_path):
        """Test error handling during workflow execution."""
        core = ComfyFixerCore()

        # Mock scanner to raise exception
        core.scanner.scan_workflows.side_effect = Exception("Scan failed")

        result = core.run(workflow_dirs=["/nonexistent"])

        assert result is not None
        # Should handle the error gracefully
        assert "error" in result or result.get("workflows_scanned") == 0

    def test_generate_run_report(self, tmp_path):
        """Test generating run report."""
        core = ComfyFixerCore()

        # Create a mock run result
        run_result = {
            "run_id": "test_run_123",
            "workflows_scanned": 5,
            "models_found": 10,
            "models_missing": 3,
            "models_resolved": 7,
            "downloads_generated": 7,
            "start_time": "2023-01-01T12:00:00",
            "end_time": "2023-01-01T12:05:00",
        }

        report_path = core._generate_run_report(run_result, str(tmp_path))

        assert report_path is not None
        assert Path(report_path).exists()

        # Verify report content
        with open(report_path, "r") as f:
            content = f.read()

        assert "test_run_123" in content
        assert "5" in content  # workflows_scanned
        assert "10" in content  # models_found
        assert "7" in content  # models_resolved


class TestCoreIntegrationWorkflow:
    """Integration tests for complete ComfyFixerSmart workflows."""

    def test_end_to_end_workflow_simulation(self, tmp_path):
        """Test simulated end-to-end workflow."""
        # Create test directory structure
        workflows_dir = tmp_path / "workflows"
        workflows_dir.mkdir()

        models_dir = tmp_path / "models"
        models_dir.mkdir()

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create test workflow with missing model
        workflow_file = workflows_dir / "test_workflow.json"
        workflow_data = {
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["missing_model.safetensors"],
                },
                {
                    "id": "2",
                    "type": "LoraLoader",
                    "widgets_values": ["existing_lora.safetensors", 1.0],
                },
            ]
        }
        workflow_file.write_text(json.dumps(workflow_data))

        # Create existing model
        existing_lora = models_dir / "existing_lora.safetensors"
        existing_lora.write_bytes(b"x" * 2_000_000)

        core = ComfyFixerCore()

        # Mock search to return result for missing model
        def mock_search_model(model_info, **kwargs):
            if model_info["filename"] == "missing_model.safetensors":
                return {
                    "status": "FOUND",
                    "filename": "missing_model.safetensors",
                    "download_url": "https://example.com/missing_model",
                    "type": "checkpoints",
                    "civitai_id": 12345,
                }
            return {"status": "NOT_FOUND", "filename": model_info["filename"]}

        core.search.search_model = mock_search_model

        # Run the workflow
        result = core.run(
            workflow_dirs=[str(workflows_dir)],
            models_dir=str(models_dir),
            output_dir=str(output_dir),
            generate_scripts=True,
        )

        assert result is not None
        assert result["workflows_scanned"] >= 1
        assert result["models_found"] >= 2  # Both models found in workflow
        assert result["models_missing"] >= 1  # One model missing
        assert result["models_resolved"] >= 1  # One model resolved via search

    def test_workflow_with_multiple_missing_models(self, tmp_path):
        """Test workflow processing with multiple missing models."""
        # Create test workflow
        workflow_file = tmp_path / "workflow.json"
        workflow_data = {
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["checkpoint1.safetensors"],
                },
                {"id": "2", "type": "VAELoader", "widgets_values": ["vae1.safetensors"]},
                {"id": "3", "type": "LoraLoader", "widgets_values": ["lora1.safetensors", 1.0]},
            ]
        }
        workflow_file.write_text(json.dumps(workflow_data))

        core = ComfyFixerCore()

        # Mock empty local inventory
        core.inventory.build_inventory.return_value = {}

        # Mock search results - all found
        search_results = {
            "checkpoint1.safetensors": {
                "status": "FOUND",
                "filename": "checkpoint1.safetensors",
                "download_url": "https://example.com/checkpoint1",
                "type": "checkpoints",
            },
            "vae1.safetensors": {
                "status": "FOUND",
                "filename": "vae1.safetensors",
                "download_url": "https://example.com/vae1",
                "type": "vae",
            },
            "lora1.safetensors": {"status": "NOT_FOUND", "filename": "lora1.safetensors"},
        }

        def mock_search_model(model_info, **kwargs):
            return search_results.get(
                model_info["filename"], {"status": "NOT_FOUND", "filename": model_info["filename"]}
            )

        core.search.search_model = mock_search_model

        # Mock download task creation
        core.downloader.create_download_tasks.return_value = [
            Mock(filename="checkpoint1.safetensors"),
            Mock(filename="vae1.safetensors"),
        ]

        result = core.run(workflow_dirs=[str(tmp_path)], generate_scripts=True)

        assert result["models_found"] == 3
        assert result["models_missing"] == 3  # All missing from local
        assert result["models_resolved"] == 2  # Two found via search
        assert result["downloads_generated"] == 2  # Two download tasks created

    def test_workflow_with_no_missing_models(self, tmp_path):
        """Test workflow processing when all models exist locally."""
        # Create test workflow
        workflow_file = tmp_path / "workflow.json"
        workflow_data = {
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["existing_checkpoint.safetensors"],
                }
            ]
        }
        workflow_file.write_text(json.dumps(workflow_data))

        # Create the model locally
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        model_file = models_dir / "existing_checkpoint.safetensors"
        model_file.write_bytes(b"x" * 2_000_000)

        core = ComfyFixerCore()

        # Mock inventory to return the existing model
        core.inventory.build_inventory.return_value = {
            "existing_checkpoint.safetensors": Mock(
                filename="existing_checkpoint.safetensors",
                path=str(model_file),
                size=2_000_000,
                is_valid=True,
            )
        }

        result = core.run(workflow_dirs=[str(tmp_path)], scan_only=True)

        assert result["models_found"] == 1
        assert result["models_missing"] == 0
        assert result["models_resolved"] == 1

        # Search should not be called since model exists
        core.search.search_model.assert_not_called()


class TestConvenienceFunctions:
    """Test convenience functions for running ComfyFixerSmart."""

    @patch("comfyfixersmart.core.ComfyFixerCore")
    def test_run_comfy_fixer_function(self, mock_core_class):
        """Test run_comfy_fixer convenience function."""
        mock_core = Mock()
        mock_core.run.return_value = {"success": True}
        mock_core_class.return_value = mock_core

        result = run_comfy_fixer(workflow_dirs=["/workflows"], scan_only=True)

        assert result == {"success": True}
        mock_core.run.assert_called_once_with(
            workflow_dirs=["/workflows"],
            scan_only=True,
            models_dir=None,
            output_dir=None,
            search_backends=None,
            generate_scripts=False,
        )
