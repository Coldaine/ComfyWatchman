"""
Functional tests for the download module.

Tests download task creation, script generation, execution, and verification
with comprehensive mocking for external dependencies.
"""

import os
import stat
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open

import pytest

from comfyfixersmart.download import (
    DownloadTask,
    DownloadScriptGenerator,
    DownloadManager,
    generate_download_script,
    verify_download,
)


class TestDownloadTask:
    """Test DownloadTask dataclass."""

    def test_download_task_creation(self):
        """Test creating a DownloadTask instance."""
        task = DownloadTask(
            filename="model.safetensors",
            download_url="https://example.com/download",
            target_path="/path/to/model.safetensors",
            model_type="checkpoints",
            civitai_id=12345,
            confidence="exact",
            retry_count=1,
            max_retries=3,
        )

        assert task.filename == "model.safetensors"
        assert task.download_url == "https://example.com/download"
        assert task.target_path == "/path/to/model.safetensors"
        assert task.model_type == "checkpoints"
        assert task.civitai_id == 12345
        assert task.confidence == "exact"
        assert task.retry_count == 1
        assert task.max_retries == 3
        assert task.status == "pending"

    def test_download_task_defaults(self):
        """Test DownloadTask default values."""
        task = DownloadTask(
            filename="model.safetensors",
            download_url="https://example.com/download",
            target_path="/path/to/model.safetensors",
            model_type="checkpoints",
        )

        assert task.civitai_id is None
        assert task.version_id is None
        assert task.confidence == "exact"
        assert task.retry_count == 0
        assert task.max_retries == 3
        assert task.status == "pending"


class TestDownloadScriptGenerator:
    """Test DownloadScriptGenerator class."""

    def test_script_generator_initialization(self):
        """Test DownloadScriptGenerator initialization."""
        generator = DownloadScriptGenerator()
        assert generator.state_manager is None
        assert generator.logger is not None

    def test_script_generator_with_state_manager(self):
        """Test DownloadScriptGenerator with state manager."""
        state_manager = Mock()
        generator = DownloadScriptGenerator(state_manager=state_manager)
        assert generator.state_manager == state_manager

    def test_generate_script_basic(self, tmp_path):
        """Test basic script generation."""
        generator = DownloadScriptGenerator()
        tasks = [
            DownloadTask(
                filename="model1.safetensors",
                download_url="https://example.com/model1",
                target_path="/models/checkpoints/model1.safetensors",
                model_type="checkpoints",
                confidence="exact",
            )
        ]

        script_path = tmp_path / "download.sh"
        result_path = generator.generate_script(tasks, str(script_path))

        assert result_path == str(script_path)
        assert script_path.exists()

        # Check script content
        content = script_path.read_text()
        assert "#!/bin/bash" in content
        assert "model1.safetensors" in content
        assert "https://example.com/model1" in content
        assert "EXACT MATCH" in content

        # Check executable permissions
        assert script_path.stat().st_mode & stat.S_IEXEC

    def test_generate_script_fuzzy_match(self, tmp_path):
        """Test script generation with fuzzy match."""
        generator = DownloadScriptGenerator()
        tasks = [
            DownloadTask(
                filename="model.safetensors",
                download_url="https://example.com/model",
                target_path="/models/checkpoints/model.safetensors",
                model_type="checkpoints",
                confidence="fuzzy",
            )
        ]

        script_path = tmp_path / "download.sh"
        generator.generate_script(tasks, str(script_path))

        content = script_path.read_text()
        assert "FUZZY MATCH - VERIFY" in content

    def test_generate_script_multiple_tasks(self, tmp_path):
        """Test script generation with multiple tasks."""
        generator = DownloadScriptGenerator()
        tasks = [
            DownloadTask(
                filename="model1.safetensors",
                download_url="https://example.com/model1",
                target_path="/models/checkpoints/model1.safetensors",
                model_type="checkpoints",
            ),
            DownloadTask(
                filename="lora1.safetensors",
                download_url="https://example.com/lora1",
                target_path="/models/loras/lora1.safetensors",
                model_type="loras",
            ),
        ]

        script_path = tmp_path / "download.sh"
        generator.generate_script(tasks, str(script_path))

        content = script_path.read_text()
        assert "model1.safetensors" in content
        assert "lora1.safetensors" in content
        assert "checkpoints" in content
        assert "loras" in content

    def test_build_script_header(self):
        """Test script header building."""
        generator = DownloadScriptGenerator()
        header = generator._build_script_header("test_run_123")

        assert header[0] == "#!/bin/bash"
        assert "test_run_123" in header[1]
        assert "source ~/.secrets" in "\n".join(header)

    def test_build_script_functions(self):
        """Test script functions building."""
        generator = DownloadScriptGenerator()
        functions = generator._build_script_functions()

        functions_text = "\n".join(functions)
        assert "verify_download()" in functions_text
        assert "update_state()" in functions_text
        assert "wget" in functions_text

    def test_build_download_commands(self):
        """Test download commands building."""
        generator = DownloadScriptGenerator()
        tasks = [
            DownloadTask(
                filename="model.safetensors",
                download_url="https://example.com/model",
                target_path="/models/checkpoints/model.safetensors",
                model_type="checkpoints",
                max_retries=5,
            )
        ]

        commands = generator._build_download_commands(tasks)
        commands_text = "\n".join(commands)

        assert "mkdir -p" in commands_text
        assert "wget" in commands_text
        assert "tries=5" in commands_text
        assert "verify_download" in commands_text
        assert "update_state" in commands_text

    def test_build_script_footer(self):
        """Test script footer building."""
        generator = DownloadScriptGenerator()
        footer = generator._build_script_footer()

        footer_text = "\n".join(footer)
        assert "Download complete!" in footer_text
        assert "python3 -c" in footer_text


class TestDownloadManager:
    """Test DownloadManager class."""

    def test_download_manager_initialization(self, tmp_path):
        """Test DownloadManager initialization."""
        manager = DownloadManager()
        assert manager.output_dir.exists()
        assert isinstance(manager.script_generator, DownloadScriptGenerator)

    def test_download_manager_with_custom_output_dir(self, tmp_path):
        """Test DownloadManager with custom output directory."""
        custom_dir = tmp_path / "custom_output"
        manager = DownloadManager(output_dir=str(custom_dir))
        assert manager.output_dir == custom_dir
        assert custom_dir.exists()

    def test_create_download_tasks(self):
        """Test creating download tasks from search results."""
        manager = DownloadManager()
        search_results = [
            {
                "status": "FOUND",
                "filename": "model1.safetensors",
                "download_url": "https://example.com/model1",
                "type": "checkpoints",
                "civitai_id": 12345,
                "version_id": 67890,
                "confidence": "exact",
            },
            {"status": "NOT_FOUND", "filename": "model2.safetensors"},
            {
                "status": "FOUND",
                "filename": "model3.safetensors",
                "download_url": "https://example.com/model3",
                "type": "loras",
            },
        ]

        tasks = manager.create_download_tasks(search_results)

        assert len(tasks) == 2

        task1 = tasks[0]
        assert task1.filename == "model1.safetensors"
        assert task1.download_url == "https://example.com/model1"
        assert task1.model_type == "checkpoints"
        assert task1.civitai_id == 12345
        assert task1.version_id == 67890
        assert task1.confidence == "exact"

        task2 = tasks[1]
        assert task2.filename == "model3.safetensors"
        assert task2.model_type == "loras"

    def test_get_target_path(self):
        """Test getting target file path."""
        manager = DownloadManager()
        result = {"filename": "model.safetensors", "type": "checkpoints"}

        target_path = manager._get_target_path(result)
        expected = str(manager.output_dir / "checkpoints" / "model.safetensors")
        assert target_path == expected

    def test_generate_download_script(self, tmp_path):
        """Test download script generation."""
        manager = DownloadManager(output_dir=str(tmp_path / "output"))
        search_results = [
            {
                "status": "FOUND",
                "filename": "model.safetensors",
                "download_url": "https://example.com/model",
                "type": "checkpoints",
            }
        ]

        script_path = manager.generate_download_script(search_results, "test_run")

        assert script_path.endswith("download_test_run.sh")
        assert Path(script_path).exists()

    def test_generate_download_script_no_tasks(self):
        """Test download script generation with no valid tasks."""
        manager = DownloadManager()
        search_results = [{"status": "NOT_FOUND", "filename": "model.safetensors"}]

        script_path = manager.generate_download_script(search_results)
        assert script_path == ""

    @patch("subprocess.run")
    def test_execute_download_script_success(self, mock_run, tmp_path):
        """Test successful download script execution."""
        mock_run.return_value = Mock(returncode=0, stdout="success", stderr="")

        manager = DownloadManager()
        script_path = str(tmp_path / "test.sh")

        result = manager.execute_download_script(script_path)

        assert result is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_execute_download_script_failure(self, mock_run, tmp_path):
        """Test failed download script execution."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="error")

        manager = DownloadManager()
        script_path = str(tmp_path / "test.sh")

        result = manager.execute_download_script(script_path)

        assert result is False

    @patch("subprocess.run")
    def test_execute_download_script_timeout(self, mock_run, tmp_path):
        """Test download script execution timeout."""
        from subprocess import TimeoutExpired

        mock_run.side_effect = TimeoutExpired("timeout", 3600)

        manager = DownloadManager()
        script_path = str(tmp_path / "test.sh")

        result = manager.execute_download_script(script_path, timeout=10)

        assert result is False

    def test_verify_downloads(self, tmp_path):
        """Test download verification."""
        manager = DownloadManager()

        # Create a mock downloaded file
        test_file = tmp_path / "model.safetensors"
        test_file.write_bytes(b"x" * 2_000_000)  # 2MB file

        tasks = [
            DownloadTask(
                filename="model.safetensors",
                download_url="https://example.com/model",
                target_path=str(test_file),
                model_type="checkpoints",
            )
        ]

        results = manager.verify_downloads(tasks)

        assert results["total"] == 1
        assert results["successful"] == 1
        assert results["failed"] == 0
        assert results["missing"] == 0

        assert len(results["details"]) == 1
        assert results["details"][0]["status"] == "success"
        assert results["details"][0]["size"] == 2_000_000

    def test_verify_downloads_missing_file(self, tmp_path):
        """Test download verification with missing file."""
        manager = DownloadManager()

        tasks = [
            DownloadTask(
                filename="missing.safetensors",
                download_url="https://example.com/model",
                target_path=str(tmp_path / "missing.safetensors"),
                model_type="checkpoints",
            )
        ]

        results = manager.verify_downloads(tasks)

        assert results["missing"] == 1
        assert results["details"][0]["status"] == "missing"

    def test_verify_downloads_small_file(self, tmp_path):
        """Test download verification with too small file."""
        manager = DownloadManager()

        # Create a small file
        small_file = tmp_path / "small.safetensors"
        small_file.write_bytes(b"x" * 500_000)  # 500KB file

        tasks = [
            DownloadTask(
                filename="small.safetensors",
                download_url="https://example.com/model",
                target_path=str(small_file),
                model_type="checkpoints",
            )
        ]

        results = manager.verify_downloads(tasks)

        assert results["failed"] == 1
        assert results["details"][0]["status"] == "failed"
        assert "too small" in results["details"][0]["error"]

    def test_retry_failed_downloads(self, tmp_path):
        """Test creating retry tasks for failed downloads."""
        manager = DownloadManager()

        # Create a failed download (small file)
        failed_file = tmp_path / "failed.safetensors"
        failed_file.write_bytes(b"x" * 500_000)

        # Create a successful download
        success_file = tmp_path / "success.safetensors"
        success_file.write_bytes(b"x" * 2_000_000)

        tasks = [
            DownloadTask(
                filename="failed.safetensors",
                download_url="https://example.com/failed",
                target_path=str(failed_file),
                model_type="checkpoints",
                retry_count=0,
            ),
            DownloadTask(
                filename="success.safetensors",
                download_url="https://example.com/success",
                target_path=str(success_file),
                model_type="checkpoints",
                retry_count=0,
            ),
            DownloadTask(
                filename="max_retries.safetensors",
                download_url="https://example.com/max",
                target_path=str(tmp_path / "max.safetensors"),
                model_type="checkpoints",
                retry_count=3,  # Already at max
            ),
        ]

        retry_tasks = manager.retry_failed_downloads(tasks, max_retries=3)

        assert len(retry_tasks) == 1
        assert retry_tasks[0].filename == "failed.safetensors"
        assert retry_tasks[0].retry_count == 1

    def test_get_download_stats_with_state_manager(self):
        """Test getting download stats with state manager."""
        state_manager = Mock()
        state_manager.get_stats.return_value = {"total": 10, "successful": 8}

        manager = DownloadManager(state_manager=state_manager)
        stats = manager.get_download_stats()

        assert stats == {"total": 10, "successful": 8}
        state_manager.get_stats.assert_called_once()

    def test_get_download_stats_no_state_manager(self):
        """Test getting download stats without state manager."""
        manager = DownloadManager(state_manager=None)
        stats = manager.get_download_stats()

        assert stats == {"error": "No state manager configured"}


class TestConvenienceFunctions:
    """Test backward compatibility convenience functions."""

    @patch("comfyfixersmart.download.DownloadManager.generate_download_script")
    def test_generate_download_script_function(self, mock_generate):
        """Test generate_download_script convenience function."""
        mock_generate.return_value = "/path/to/script.sh"

        resolutions = [{"status": "FOUND", "filename": "model.safetensors"}]
        result = generate_download_script(resolutions, output_dir="/tmp", run_id="test")

        assert result == "/path/to/script.sh"
        mock_generate.assert_called_once()

    def test_verify_download_function_success(self, tmp_path):
        """Test verify_download convenience function with success."""
        # Create a valid file
        test_file = tmp_path / "model.safetensors"
        test_file.write_bytes(b"x" * 2_000_000)

        result = verify_download(str(test_file), "model.safetensors")

        assert result is True

    def test_verify_download_function_failure(self, tmp_path):
        """Test verify_download convenience function with failure."""
        # Create a small file
        test_file = tmp_path / "small.safetensors"
        test_file.write_bytes(b"x" * 500_000)

        result = verify_download(str(test_file), "small.safetensors")

        assert result is False

    def test_verify_download_function_missing_file(self):
        """Test verify_download convenience function with missing file."""
        result = verify_download("/nonexistent/file.safetensors", "missing.safetensors")
        assert result is False


class TestDownloadIntegration:
    """Integration tests for download functionality."""

    def test_full_download_workflow(self, tmp_path):
        """Test complete download workflow from search results to script execution."""
        # Create search results
        search_results = [
            {
                "status": "FOUND",
                "filename": "model1.safetensors",
                "download_url": "https://example.com/model1",
                "type": "checkpoints",
                "civitai_id": 12345,
                "confidence": "exact",
            },
            {
                "status": "FOUND",
                "filename": "lora1.safetensors",
                "download_url": "https://example.com/lora1",
                "type": "loras",
                "confidence": "fuzzy",
            },
        ]

        # Create download manager
        output_dir = tmp_path / "downloads"
        manager = DownloadManager(output_dir=str(output_dir))

        # Generate script
        script_path = manager.generate_download_script(search_results, "integration_test")
        assert Path(script_path).exists()

        # Verify script content
        script_content = Path(script_path).read_text()
        assert "model1.safetensors" in script_content
        assert "lora1.safetensors" in script_content
        assert "EXACT MATCH" in script_content
        assert "FUZZY MATCH - VERIFY" in script_content

        # Create tasks and verify
        tasks = manager.create_download_tasks(search_results)
        assert len(tasks) == 2

        # Test verification on non-existent files
        verification = manager.verify_downloads(tasks)
        assert verification["total"] == 2
        assert verification["missing"] == 2

        # Test retry logic
        retry_tasks = manager.retry_failed_downloads(tasks)
        assert len(retry_tasks) == 2
        assert all(task.retry_count == 1 for task in retry_tasks)

    def test_script_generation_with_special_characters(self, tmp_path):
        """Test script generation handles special characters in filenames."""
        manager = DownloadManager()
        tasks = [
            DownloadTask(
                filename="model-with_special.chars.safetensors",
                download_url="https://example.com/model",
                target_path="/models/checkpoints/model-with_special.chars.safetensors",
                model_type="checkpoints",
            )
        ]

        script_path = tmp_path / "special.sh"
        manager.script_generator.generate_script(tasks, str(script_path))

        content = script_path.read_text()
        # Should handle special characters properly in bash script
        assert "model-with_special.chars.safetensors" in content

    @patch("subprocess.run")
    def test_script_execution_error_handling(self, mock_run, tmp_path):
        """Test script execution error handling."""
        # Mock subprocess to raise exception
        mock_run.side_effect = Exception("Execution failed")

        manager = DownloadManager()
        script_path = str(tmp_path / "failing.sh")

        result = manager.execute_download_script(script_path)

        assert result is False
