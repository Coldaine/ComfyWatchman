"""
End-to-end tests for ComfyFixerSmart.

Tests complete workflows from workflow scanning to download script generation
with realistic data and minimal mocking.
"""

import json
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from comfyfixersmart.core import ComfyFixerCore


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""

    def test_complete_workflow_with_missing_models(self, tmp_path):
        """Test complete workflow: scan -> find missing -> search -> generate downloads."""
        # Create test directory structure
        workflows_dir = tmp_path / "workflows"
        workflows_dir.mkdir()

        models_dir = tmp_path / "models"
        models_dir.mkdir()

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create test workflow with multiple missing models
        workflow1 = workflows_dir / "workflow1.json"
        workflow_data1 = {
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["missing_checkpoint.safetensors"]
                },
                {
                    "id": "2",
                    "type": "VAELoader",
                    "widgets_values": ["missing_vae.safetensors"]
                }
            ]
        }
        workflow1.write_text(json.dumps(workflow_data1))

        workflow2 = workflows_dir / "workflow2.json"
        workflow_data2 = {
            "nodes": [
                {
                    "id": "1",
                    "type": "LoraLoader",
                    "widgets_values": ["existing_lora.safetensors", 1.0]
                },
                {
                    "id": "2",
                    "type": "ControlNetLoader",
                    "widgets_values": ["missing_controlnet.pth"]
                }
            ]
        }
        workflow2.write_text(json.dumps(workflow_data2))

        # Create one existing model
        existing_lora = models_dir / "existing_lora.safetensors"
        existing_lora.write_bytes(b"x" * 2_000_000)  # 2MB

        # Initialize core
        core = ComfyFixerCore()

        # Mock search results for missing models
        search_results = {
            "missing_checkpoint.safetensors": {
                "status": "FOUND",
                "filename": "missing_checkpoint.safetensors",
                "download_url": "https://civitai.com/api/download/models/12345",
                "type": "checkpoints",
                "civitai_id": 12345,
                "confidence": "exact"
            },
            "missing_vae.safetensors": {
                "status": "FOUND",
                "filename": "missing_vae.safetensors",
                "download_url": "https://civitai.com/api/download/models/67890",
                "type": "vae",
                "civitai_id": 67890,
                "confidence": "exact"
            },
            "missing_controlnet.pth": {
                "status": "FOUND",
                "filename": "missing_controlnet.pth",
                "download_url": "https://civitai.com/api/download/models/11111",
                "type": "controlnet",
                "civitai_id": 11111,
                "confidence": "fuzzy"
            }
        }

        def mock_search_model(model_info, **kwargs):
            return search_results.get(model_info["filename"],
                                    {"status": "NOT_FOUND", "filename": model_info["filename"]})

        core.search.search_model = mock_search_model

        # Run complete workflow
        result = core.run(
            workflow_dirs=[str(workflows_dir)],
            models_dir=str(models_dir),
            output_dir=str(output_dir),
            generate_scripts=True
        )

        # Verify results
        assert result["workflows_scanned"] == 2
        assert result["models_found"] == 4  # 2 in workflow1 + 2 in workflow2
        assert result["models_missing"] == 3  # 3 missing models
        assert result["models_resolved"] == 3  # All 3 found via search
        assert result["downloads_generated"] == 3  # 3 download tasks

        # Verify download script was generated
        script_files = list(output_dir.glob("download_*.sh"))
        assert len(script_files) == 1

        script_content = script_files[0].read_text()
        assert "missing_checkpoint.safetensors" in script_content
        assert "missing_vae.safetensors" in script_content
        assert "missing_controlnet.pth" in script_content
        assert "FUZZY MATCH - VERIFY" in script_content  # For controlnet

    def test_workflow_with_all_models_present(self, tmp_path):
        """Test workflow where all models are already present locally."""
        # Create test directory structure
        workflows_dir = tmp_path / "workflows"
        workflows_dir.mkdir()

        models_dir = tmp_path / "models"
        models_dir.mkdir()

        checkpoints_dir = models_dir / "checkpoints"
        checkpoints_dir.mkdir()

        loras_dir = models_dir / "loras"
        loras_dir.mkdir()

        # Create workflow
        workflow = workflows_dir / "complete_workflow.json"
        workflow_data = {
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["existing_checkpoint.safetensors"]
                },
                {
                    "id": "2",
                    "type": "LoraLoader",
                    "widgets_values": ["existing_lora.safetensors", 1.0]
                }
            ]
        }
        workflow.write_text(json.dumps(workflow_data))

        # Create existing models
        checkpoint_file = checkpoints_dir / "existing_checkpoint.safetensors"
        checkpoint_file.write_bytes(b"x" * 2_000_000)

        lora_file = loras_dir / "existing_lora.safetensors"
        lora_file.write_bytes(b"x" * 1_500_000)

        # Initialize core
        core = ComfyFixerCore()

        # Run workflow
        result = core.run(
            workflow_dirs=[str(workflows_dir)],
            models_dir=str(models_dir),
            scan_only=True  # Only scan, don't search or download
        )

        # Verify results
        assert result["workflows_scanned"] == 1
        assert result["models_found"] == 2
        assert result["models_missing"] == 0  # No missing models
        assert result["models_resolved"] == 2  # Both resolved locally

        # Search should not have been called
        core.search.search_model.assert_not_called()

    def test_workflow_with_mixed_model_states(self, tmp_path):
        """Test workflow with mix of existing, missing, and invalid models."""
        # Create test directory structure
        workflows_dir = tmp_path / "workflows"
        workflows_dir.mkdir()

        models_dir = tmp_path / "models"
        models_dir.mkdir()

        checkpoints_dir = models_dir / "checkpoints"
        checkpoints_dir.mkdir()

        # Create workflow
        workflow = workflows_dir / "mixed_workflow.json"
        workflow_data = {
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["existing_checkpoint.safetensors"]
                },
                {
                    "id": "2",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["missing_checkpoint.safetensors"]
                },
                {
                    "id": "3",
                    "type": "VAELoader",
                    "widgets_values": ["small_vae.safetensors"]  # Will be too small
                }
            ]
        }
        workflow.write_text(json.dumps(workflow_data))

        # Create existing valid model
        valid_checkpoint = checkpoints_dir / "existing_checkpoint.safetensors"
        valid_checkpoint.write_bytes(b"x" * 2_000_000)

        # Create invalid model (too small)
        small_vae = models_dir / "small_vae.safetensors"
        small_vae.write_bytes(b"x" * 500_000)  # Too small

        # Initialize core
        core = ComfyFixerCore()

        # Mock search for missing model
        def mock_search_model(model_info, **kwargs):
            if model_info["filename"] == "missing_checkpoint.safetensors":
                return {
                    "status": "FOUND",
                    "filename": "missing_checkpoint.safetensors",
                    "download_url": "https://example.com/missing",
                    "type": "checkpoints"
                }
            return {"status": "NOT_FOUND", "filename": model_info["filename"]}

        core.search.search_model = mock_search_model

        # Run workflow
        result = core.run(
            workflow_dirs=[str(workflows_dir)],
            models_dir=str(models_dir),
            generate_scripts=True
        )

        # Verify results
        assert result["models_found"] == 3
        assert result["models_missing"] == 2  # missing_checkpoint + small_vae (invalid)
        assert result["models_resolved"] == 1  # existing_checkpoint only
        assert result["downloads_generated"] == 1  # Only missing_checkpoint found via search

    def test_multiple_workflow_directories(self, tmp_path):
        """Test scanning multiple workflow directories."""
        # Create multiple workflow directories
        workflows1_dir = tmp_path / "workflows1"
        workflows1_dir.mkdir()

        workflows2_dir = tmp_path / "workflows2"
        workflows2_dir.mkdir()

        models_dir = tmp_path / "models"
        models_dir.mkdir()

        # Create workflows in different directories
        workflow1 = workflows1_dir / "workflow1.json"
        workflow1_data = {
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["model1.safetensors"]
                }
            ]
        }
        workflow1.write_text(json.dumps(workflow1_data))

        workflow2 = workflows2_dir / "workflow2.json"
        workflow2_data = {
            "nodes": [
                {
                    "id": "1",
                    "type": "VAELoader",
                    "widgets_values": ["model2.safetensors"]
                }
            ]
        }
        workflow2.write_text(json.dumps(workflow2_data))

        # Initialize core
        core = ComfyFixerCore()

        # Mock search - both models found
        def mock_search_model(model_info, **kwargs):
            return {
                "status": "FOUND",
                "filename": model_info["filename"],
                "download_url": f"https://example.com/{model_info['filename']}",
                "type": "checkpoints" if "model1" in model_info["filename"] else "vae"
            }

        core.search.search_model = mock_search_model

        # Run with multiple directories
        result = core.run(
            workflow_dirs=[str(workflows1_dir), str(workflows2_dir)],
            models_dir=str(models_dir),
            generate_scripts=True
        )

        # Verify results
        assert result["workflows_scanned"] == 2
        assert result["models_found"] == 2
        assert result["models_resolved"] == 2
        assert result["downloads_generated"] == 2

    def test_workflow_validation_and_error_handling(self, tmp_path):
        """Test workflow validation and error handling in end-to-end flow."""
        # Create test directory structure
        workflows_dir = tmp_path / "workflows"
        workflows_dir.mkdir()

        models_dir = tmp_path / "models"
        models_dir.mkdir()

        # Create valid workflow
        valid_workflow = workflows_dir / "valid.json"
        valid_workflow.write_text(json.dumps({
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["valid_model.safetensors"]
                }
            ]
        }))

        # Create invalid workflow (malformed JSON)
        invalid_workflow = workflows_dir / "invalid.json"
        invalid_workflow.write_text('{"nodes": [{"type": "CheckpointLoaderSimple", "widgets_values": ["model.safetensors"]')

        # Create empty workflow
        empty_workflow = workflows_dir / "empty.json"
        empty_workflow.write_text(json.dumps({"nodes": []}))

        # Initialize core
        core = ComfyFixerCore()

        # Mock search
        core.search.search_model.return_value = {
            "status": "FOUND",
            "filename": "valid_model.safetensors",
            "download_url": "https://example.com/valid",
            "type": "checkpoints"
        }

        # Run workflow processing
        result = core.run(
            workflow_dirs=[str(workflows_dir)],
            models_dir=str(models_dir),
            generate_scripts=True
        )

        # Should handle errors gracefully
        assert result["workflows_scanned"] >= 1  # At least the valid one
        assert "models_found" in result

        # Valid workflow should be processed
        if result["models_found"] > 0:
            assert result["models_resolved"] >= 1

    def test_large_workflow_processing(self, tmp_path):
        """Test processing of a large workflow with many models."""
        # Create test directory structure
        workflows_dir = tmp_path / "workflows"
        workflows_dir.mkdir()

        models_dir = tmp_path / "models"
        models_dir.mkdir()

        # Create large workflow with many models
        workflow = workflows_dir / "large_workflow.json"

        nodes = []
        model_count = 20

        for i in range(model_count):
            node_type = ["CheckpointLoaderSimple", "VAELoader", "LoraLoader"][i % 3]
            model_name = f"model_{i}.safetensors"
            nodes.append({
                "id": str(i + 1),
                "type": node_type,
                "widgets_values": [model_name] if node_type != "LoraLoader" else [model_name, 1.0]
            })

        workflow_data = {"nodes": nodes}
        workflow.write_text(json.dumps(workflow_data))

        # Initialize core
        core = ComfyFixerCore()

        # Mock search - all models found
        def mock_search_model(model_info, **kwargs):
            return {
                "status": "FOUND",
                "filename": model_info["filename"],
                "download_url": f"https://example.com/{model_info['filename']}",
                "type": "checkpoints"  # Simplified
            }

        core.search.search_model = mock_search_model

        # Run workflow
        result = core.run(
            workflow_dirs=[str(workflows_dir)],
            models_dir=str(models_dir),
            generate_scripts=True
        )

        # Verify results
        assert result["workflows_scanned"] == 1
        assert result["models_found"] == model_count
        assert result["models_resolved"] == model_count
        assert result["downloads_generated"] == model_count

    def test_output_file_generation(self, tmp_path):
        """Test that all expected output files are generated."""
        # Create test directory structure
        workflows_dir = tmp_path / "workflows"
        workflows_dir.mkdir()

        models_dir = tmp_path / "models"
        models_dir.mkdir()

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create workflow
        workflow = workflows_dir / "test.json"
        workflow.write_text(json.dumps({
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["test_model.safetensors"]
                }
            ]
        }))

        # Initialize core
        core = ComfyFixerCore()

        # Mock search
        core.search.search_model.return_value = {
            "status": "FOUND",
            "filename": "test_model.safetensors",
            "download_url": "https://example.com/test",
            "type": "checkpoints"
        }

        # Run workflow
        result = core.run(
            workflow_dirs=[str(workflows_dir)],
            models_dir=str(models_dir),
            output_dir=str(output_dir),
            generate_scripts=True
        )

        # Check that output files were created
        run_id = result.get("run_id", "")

        # Download script
        script_files = list(output_dir.glob("download_*.sh"))
        assert len(script_files) == 1

        # Missing models file
        missing_files = list(output_dir.glob("missing_models*.json"))
        assert len(missing_files) >= 1

        # Resolutions file
        resolution_files = list(output_dir.glob("resolutions*.json"))
        assert len(resolution_files) >= 1

        # Verify script is executable
        script_path = script_files[0]
        assert os.access(script_path, os.X_OK)

        # Verify script content
        content = script_path.read_text()
        assert "test_model.safetensors" in content
        assert "https://example.com/test" in content


class TestEndToEndErrorRecovery:
    """Test error recovery in end-to-end scenarios."""

    def test_partial_failure_recovery(self, tmp_path):
        """Test recovery when some operations fail but others succeed."""
        # Create test directory structure
        workflows_dir = tmp_path / "workflows"
        workflows_dir.mkdir()

        models_dir = tmp_path / "models"
        models_dir.mkdir()

        # Create workflow
        workflow = workflows_dir / "test.json"
        workflow.write_text(json.dumps({
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["good_model.safetensors"]
                },
                {
                    "id": "2",
                    "type": "VAELoader",
                    "widgets_values": ["bad_model.safetensors"]
                }
            ]
        }))

        # Initialize core
        core = ComfyFixerCore()

        # Mock search - one succeeds, one fails
        def mock_search_model(model_info, **kwargs):
            if "good_model" in model_info["filename"]:
                return {
                    "status": "FOUND",
                    "filename": model_info["filename"],
                    "download_url": "https://example.com/good",
                    "type": "checkpoints"
                }
            else:
                return {
                    "status": "ERROR",
                    "filename": model_info["filename"],
                    "error_message": "Search failed"
                }

        core.search.search_model = mock_search_model

        # Run workflow
        result = core.run(
            workflow_dirs=[str(workflows_dir)],
            models_dir=str(models_dir),
            generate_scripts=True
        )

        # Should still generate results even with partial failure
        assert result["models_found"] == 2
        assert result["models_resolved"] == 1  # Only good_model resolved
        assert result["downloads_generated"] == 1  # Only one download task

    def test_network_failure_recovery(self, tmp_path):
        """Test recovery from network/API failures."""
        # Create test directory structure
        workflows_dir = tmp_path / "workflows"
        workflows_dir.mkdir()

        models_dir = tmp_path / "models"
        models_dir.mkdir()

        # Create workflow
        workflow = workflows_dir / "test.json"
        workflow.write_text(json.dumps({
            "nodes": [
                {
                    "id": "1",
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["network_model.safetensors"]
                }
            ]
        }))

        # Initialize core
        core = ComfyFixerCore()

        # Mock search that fails with network error
        core.search.search_model.side_effect = Exception("Network timeout")

        # Run workflow - should handle the error gracefully
        result = core.run(
            workflow_dirs=[str(workflows_dir)],
            models_dir=str(models_dir),
            generate_scripts=False  # Don't generate scripts on error
        )

        # Should still return results, but with errors noted
        assert "models_found" in result
        assert result["models_found"] == 1
        assert result["models_resolved"] == 0  # Search failed