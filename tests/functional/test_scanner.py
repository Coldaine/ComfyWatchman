"""
Functional tests for the scanner module.

Tests workflow scanning, parsing, model extraction, and validation
functionality with real file operations and mock data.
"""

import json
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from comfyfixersmart.scanner import (
    WorkflowScanner, WorkflowInfo, ModelReference,
    scan_workflows, extract_models_from_workflow
)


class TestWorkflowInfo:
    """Test WorkflowInfo dataclass."""

    def test_workflow_info_creation(self):
        """Test creating a WorkflowInfo instance."""
        info = WorkflowInfo(
            path="/path/to/workflow.json",
            filename="workflow.json",
            size=1024,
            is_valid=True,
            model_count=5,
            node_count=10,
            errors=[]
        )

        assert info.path == "/path/to/workflow.json"
        assert info.filename == "workflow.json"
        assert info.size == 1024
        assert info.is_valid is True
        assert info.model_count == 5
        assert info.node_count == 10
        assert info.errors == []


class TestModelReference:
    """Test ModelReference dataclass."""

    def test_model_reference_creation(self):
        """Test creating a ModelReference instance."""
        ref = ModelReference(
            filename="model.safetensors",
            type="checkpoints",
            node_type="CheckpointLoaderSimple",
            workflow_path="/path/to/workflow.json",
            node_id="1",
            widget_name="widgets_values[0]"
        )

        assert ref.filename == "model.safetensors"
        assert ref.type == "checkpoints"
        assert ref.node_type == "CheckpointLoaderSimple"
        assert ref.workflow_path == "/path/to/workflow.json"
        assert ref.node_id == "1"
        assert ref.widget_name == "widgets_values[0]"

    def test_model_reference_defaults(self):
        """Test ModelReference default values."""
        ref = ModelReference(
            filename="model.safetensors",
            type="checkpoints",
            node_type="CheckpointLoaderSimple",
            workflow_path="/path/to/workflow.json"
        )

        assert ref.node_id is None
        assert ref.widget_name is None


class TestWorkflowScanner:
    """Test WorkflowScanner class functionality."""

    def test_scanner_initialization(self):
        """Test WorkflowScanner initialization."""
        scanner = WorkflowScanner()
        assert scanner.logger is not None

    def test_scanner_initialization_with_logger(self):
        """Test WorkflowScanner initialization with custom logger."""
        logger = Mock()
        scanner = WorkflowScanner(logger=logger)
        assert scanner.logger == logger

    def test_scan_workflows_specific_paths(self, tmp_path):
        """Test scanning specific workflow paths."""
        # Create test workflow files
        workflow1 = tmp_path / "workflow1.json"
        workflow2 = tmp_path / "workflow2.json"
        non_json = tmp_path / "not_workflow.txt"

        workflow1.write_text('{"nodes": []}')
        workflow2.write_text('{"nodes": []}')
        non_json.write_text("not json")

        scanner = WorkflowScanner()

        paths = [
            str(workflow1),
            str(workflow2),
            str(non_json),  # Should be filtered out
            "/nonexistent.json"  # Should be filtered out
        ]

        result = scanner.scan_workflows(specific_paths=paths)

        assert len(result) == 2
        assert str(workflow1) in result
        assert str(workflow2) in result

    def test_scan_workflows_directories(self, tmp_path):
        """Test scanning workflow directories."""
        # Create directory structure
        workflows_dir = tmp_path / "workflows"
        workflows_dir.mkdir()

        subdir = workflows_dir / "subdir"
        subdir.mkdir()

        # Create workflow files
        (workflows_dir / "workflow1.json").write_text('{"nodes": []}')
        (workflows_dir / "workflow2.json").write_text('{"nodes": []}')
        (subdir / "workflow3.json").write_text('{"nodes": []}')
        (workflows_dir / "not_workflow.txt").write_text("text")  # Should be ignored

        scanner = WorkflowScanner()

        result = scanner.scan_workflows(workflow_dirs=[str(workflows_dir)])

        assert len(result) == 3
        assert any("workflow1.json" in path for path in result)
        assert any("workflow2.json" in path for path in result)
        assert any("workflow3.json" in path for path in result)

    def test_scan_workflows_nonexistent_directory(self, tmp_path):
        """Test scanning nonexistent directory."""
        scanner = WorkflowScanner()
        result = scanner.scan_workflows(workflow_dirs=["/nonexistent"])

        assert result == []

    def test_scan_workflows_detailed(self, tmp_path):
        """Test detailed workflow scanning."""
        workflow_file = tmp_path / "workflow.json"
        workflow_data = {
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["model.safetensors"]
                }
            ]
        }
        workflow_file.write_text(json.dumps(workflow_data))

        scanner = WorkflowScanner()
        result = scanner.scan_workflows_detailed(specific_paths=[str(workflow_file)])

        assert len(result) == 1
        info = result[0]
        assert info.path == str(workflow_file)
        assert info.filename == "workflow.json"
        assert info.is_valid is True
        assert info.model_count == 1
        assert info.node_count == 1
        assert info.errors == []

    def test_analyze_workflow_valid(self, tmp_path):
        """Test analyzing a valid workflow."""
        workflow_file = tmp_path / "workflow.json"
        workflow_data = {
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["model.safetensors"]
                },
                {
                    "id": "2",
                    "type": "CLIPTextEncode",
                    "widgets_values": ["some text"]
                }
            ]
        }
        workflow_file.write_text(json.dumps(workflow_data))

        scanner = WorkflowScanner()
        info = scanner._analyze_workflow(str(workflow_file))

        assert info.path == str(workflow_file)
        assert info.filename == "workflow.json"
        assert info.is_valid is True
        assert info.model_count == 1
        assert info.node_count == 2
        assert info.errors == []

    def test_analyze_workflow_invalid_json(self, tmp_path):
        """Test analyzing workflow with invalid JSON."""
        workflow_file = tmp_path / "invalid.json"
        workflow_file.write_text('{"invalid": json}')

        scanner = WorkflowScanner()
        info = scanner._analyze_workflow(str(workflow_file))

        assert info.is_valid is False
        assert "Invalid JSON format" in info.errors

    def test_extract_models_from_workflow(self, tmp_path):
        """Test extracting models from workflow."""
        workflow_file = tmp_path / "workflow.json"
        workflow_data = {
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["model.safetensors"]
                },
                {
                    "id": "2",
                    "type": "LoraLoader",
                    "widgets_values": ["lora1.safetensors", 1.0]
                },
                {
                    "id": "3",
                    "type": "VAELoader",
                    "widgets_values": ["vae.safetensors"]
                },
                {
                    "id": "4",
                    "type": "CLIPTextEncode",
                    "widgets_values": ["some text"]  # Not a model
                }
            ]
        }
        workflow_file.write_text(json.dumps(workflow_data))

        scanner = WorkflowScanner()
        models = scanner.extract_models_from_workflow(str(workflow_file))

        assert len(models) == 3

        # Check first model
        model1 = models[0]
        assert model1.filename == "model.safetensors"
        assert model1.type == "checkpoints"
        assert model1.node_type == "CheckpointLoaderSimple"
        assert model1.workflow_path == str(workflow_file)
        assert model1.node_id == "1"
        assert model1.widget_name == "widgets_values[0]"

        # Check second model
        model2 = models[1]
        assert model2.filename == "lora1.safetensors"
        assert model2.type == "loras"
        assert model2.node_type == "LoraLoader"

        # Check third model
        model3 = models[2]
        assert model3.filename == "vae.safetensors"
        assert model3.type == "vae"
        assert model3.node_type == "VAELoader"

    def test_extract_models_from_workflow_with_node_count(self, tmp_path):
        """Test extracting models with node count."""
        workflow_file = tmp_path / "workflow.json"
        workflow_data = {
            "nodes": [
                {"id": "1", "type": "CheckpointLoaderSimple", "widgets_values": ["model.safetensors"]},
                {"id": "2", "type": "CLIPTextEncode", "widgets_values": ["text"]}
            ]
        }
        workflow_file.write_text(json.dumps(workflow_data))

        scanner = WorkflowScanner()
        result = scanner.extract_models_from_workflow(str(workflow_file), return_node_count=True)

        models, node_count = result
        assert len(models) == 1
        assert node_count == 2

    def test_extract_models_from_workflow_invalid_file(self, tmp_path):
        """Test extracting models from invalid workflow file."""
        scanner = WorkflowScanner()
        models = scanner.extract_models_from_workflow("/nonexistent.json")

        assert models == []

    def test_validate_workflow_valid(self, tmp_path):
        """Test validating a valid workflow."""
        workflow_file = tmp_path / "workflow.json"
        workflow_data = {
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["model.safetensors"]
                },
                {
                    "id": "2",
                    "type": "CLIPTextEncode",
                    "widgets_values": ["some text"]
                }
            ]
        }
        workflow_file.write_text(json.dumps(workflow_data))

        scanner = WorkflowScanner()
        result = scanner.validate_workflow(str(workflow_file))

        assert result["is_valid"] is True
        assert result["errors"] == []
        assert result["warnings"] == []
        assert result["stats"]["node_count"] == 2
        assert result["stats"]["model_count"] == 1

    def test_validate_workflow_invalid_structure(self, tmp_path):
        """Test validating workflow with invalid structure."""
        workflow_file = tmp_path / "invalid.json"
        workflow_file.write_text('"not an object"')

        scanner = WorkflowScanner()
        result = scanner.validate_workflow(str(workflow_file))

        assert result["is_valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_workflow_missing_node_type(self, tmp_path):
        """Test validating workflow with missing node type."""
        workflow_file = tmp_path / "workflow.json"
        workflow_data = {
            "nodes": [
                {"id": "1"},  # Missing type
                {"id": "2", "type": "ValidType"}
            ]
        }
        workflow_file.write_text(json.dumps(workflow_data))

        scanner = WorkflowScanner()
        result = scanner.validate_workflow(str(workflow_file))

        assert result["is_valid"] is False
        assert any("missing 'type' field" in error for error in result["errors"])

    def test_validate_workflow_duplicate_node_ids(self, tmp_path):
        """Test validating workflow with duplicate node IDs."""
        workflow_file = tmp_path / "workflow.json"
        workflow_data = {
            "nodes": [
                {"id": "1", "type": "Type1"},
                {"id": "1", "type": "Type2"}  # Duplicate ID
            ]
        }
        workflow_file.write_text(json.dumps(workflow_data))

        scanner = WorkflowScanner()
        result = scanner.validate_workflow(str(workflow_file))

        assert result["is_valid"] is False
        assert any("Duplicate node ID" in error for error in result["errors"])

    def test_get_workflow_summary(self, tmp_path):
        """Test getting workflow summary."""
        # Create test workflows
        workflow1 = tmp_path / "workflow1.json"
        workflow1_data = {
            "nodes": [
                {"id": "1", "type": "CheckpointLoaderSimple", "widgets_values": ["model1.safetensors"]},
                {"id": "2", "type": "LoraLoader", "widgets_values": ["lora1.safetensors", 1.0]}
            ]
        }
        workflow1.write_text(json.dumps(workflow1_data))

        workflow2 = tmp_path / "workflow2.json"
        workflow2_data = {
            "nodes": [
                {"id": "1", "type": "VAELoader", "widgets_values": ["vae1.safetensors"]}
            ]
        }
        workflow2.write_text(json.dumps(workflow2_data))

        scanner = WorkflowScanner()
        summary = scanner.get_workflow_summary([str(workflow1), str(workflow2)])

        assert summary["total_workflows"] == 2
        assert summary["valid_workflows"] == 2
        assert summary["invalid_workflows"] == 0
        assert summary["total_models"] == 3
        assert summary["unique_models"] == 3
        assert summary["model_types"]["checkpoints"] == 1
        assert summary["model_types"]["loras"] == 1
        assert summary["model_types"]["vae"] == 1
        assert summary["node_types"]["CheckpointLoaderSimple"] == 1
        assert summary["node_types"]["LoraLoader"] == 1
        assert summary["node_types"]["VAELoader"] == 1


class TestConvenienceFunctions:
    """Test backward compatibility convenience functions."""

    def test_scan_workflows_function(self, tmp_path):
        """Test scan_workflows convenience function."""
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": []}')

        result = scan_workflows(specific_paths=[str(workflow_file)])

        assert len(result) == 1
        assert str(workflow_file) in result

    def test_extract_models_from_workflow_function(self, tmp_path):
        """Test extract_models_from_workflow convenience function."""
        workflow_file = tmp_path / "workflow.json"
        workflow_data = {
            "nodes": [
                {"id": "1", "type": "CheckpointLoaderSimple", "widgets_values": ["model.safetensors"]}
            ]
        }
        workflow_file.write_text(json.dumps(workflow_data))

        models = extract_models_from_workflow(str(workflow_file))

        assert len(models) == 1
        assert models[0]["filename"] == "model.safetensors"
        assert models[0]["type"] == "checkpoints"
        assert models[0]["node_type"] == "CheckpointLoaderSimple"
        assert models[0]["workflow"] == "workflow.json"


class TestScannerIntegration:
    """Integration tests for scanner functionality."""

    def test_full_workflow_processing(self, tmp_path):
        """Test complete workflow processing pipeline."""
        # Create a complex workflow
        workflow_file = tmp_path / "complex_workflow.json"
        workflow_data = {
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["realisticVisionV60B1_v60B1VAE.safetensors"]
                },
                {
                    "id": "2",
                    "type": "CLIPTextEncode",
                    "widgets_values": ["a beautiful landscape"]
                },
                {
                    "id": "3",
                    "type": "VAELoader",
                    "widgets_values": ["vae-ft-mse-840000-ema-pruned.safetensors"]
                },
                {
                    "id": "4",
                    "type": "LoraLoader",
                    "widgets_values": ["epiNoiseoffset_v2.safetensors", 1.0, 1.0]
                },
                {
                    "id": "5",
                    "type": "ControlNetLoader",
                    "widgets_values": ["control_v11p_sd15_canny.pth"]
                },
                {
                    "id": "6",
                    "type": "UpscaleModelLoader",
                    "widgets_values": ["4x-UltraSharp.pth"]
                }
            ]
        }
        workflow_file.write_text(json.dumps(workflow_data))

        scanner = WorkflowScanner()

        # Test scanning
        workflows = scanner.scan_workflows(specific_paths=[str(workflow_file)])
        assert len(workflows) == 1

        # Test detailed scanning
        details = scanner.scan_workflows_detailed(specific_paths=[str(workflow_file)])
        assert len(details) == 1
        assert details[0].model_count == 5  # 5 model references
        assert details[0].node_count == 6   # 6 total nodes

        # Test model extraction
        models = scanner.extract_models_from_workflow(str(workflow_file))
        assert len(models) == 5

        expected_models = [
            ("realisticVisionV60B1_v60B1VAE.safetensors", "checkpoints"),
            ("vae-ft-mse-840000-ema-pruned.safetensors", "vae"),
            ("epiNoiseoffset_v2.safetensors", "loras"),
            ("control_v11p_sd15_canny.pth", "controlnet"),
            ("4x-UltraSharp.pth", "upscale_models")
        ]

        for i, (expected_filename, expected_type) in enumerate(expected_models):
            assert models[i].filename == expected_filename
            assert models[i].type == expected_type

        # Test validation
        validation = scanner.validate_workflow(str(workflow_file))
        assert validation["is_valid"] is True
        assert validation["stats"]["node_count"] == 6
        assert validation["stats"]["model_count"] == 5

        # Test summary
        summary = scanner.get_workflow_summary([str(workflow_file)])
        assert summary["total_workflows"] == 1
        assert summary["valid_workflows"] == 1
        assert summary["total_models"] == 5
        assert summary["unique_models"] == 5