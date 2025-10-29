"""
Shared pytest fixtures and configuration for ComfyFixerSmart tests.

This module provides common test fixtures, utilities, and setup/teardown
functions used across all test modules.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import Mock, patch

import pytest

# Import the package modules
from comfyfixersmart.config import Config
from comfyfixersmart.logging import get_logger, setup_logging
from comfyfixersmart.state_manager import StateManager


@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for the entire test session."""
    temp_path = Path(tempfile.mkdtemp(prefix="comfyfixer_test_"))
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create a temporary config directory for tests."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def temp_log_dir(tmp_path: Path) -> Path:
    """Create a temporary log directory for tests."""
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    return log_dir


@pytest.fixture
def temp_state_dir(tmp_path: Path) -> Path:
    """Create a temporary state directory for tests."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    return state_dir


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory for tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_config(
    temp_config_dir: Path, temp_log_dir: Path, temp_state_dir: Path, temp_output_dir: Path
) -> Config:
    """Create a sample configuration for testing."""
    return Config(
        comfyui_root=Path("/tmp/comfyui"),
        workflow_dirs=[Path("/tmp/workflows")],
        output_dir=temp_output_dir,
        log_dir=temp_log_dir,
        state_dir=temp_state_dir,
        search_log_file="test_search.log",
        download_counter_file="test_counter.txt",
        temp_dir=Path("/tmp") / "test_qwen_results",
        civitai_api_base="https://civitai.com/api/v1",
        civitai_download_base="https://civitai.com/api/download/models",
        civitai_api_timeout=10,
        model_extensions=[".safetensors", ".ckpt", ".pt"],
        state_file="test_state.json",
    )


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return Mock()


@pytest.fixture
def state_manager(temp_state_dir: Path, sample_config: Config):
    """Create a StateManager instance for testing."""
    return StateManager(state_dir=temp_state_dir, config=sample_config)


@pytest.fixture
def sample_workflow_data() -> Dict[str, Any]:
    """Sample workflow JSON data for testing."""
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "realisticVisionV60B1_v60B1VAE.safetensors"},
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "a beautiful landscape", "clip": ["1", 1]},
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": "vae-ft-mse-840000-ema-pruned.safetensors"},
        },
        "4": {
            "class_type": "LoraLoader",
            "inputs": {
                "lora_name": "epiNoiseoffset_v2.safetensors",
                "strength_model": 1.0,
                "strength_clip": 1.0,
            },
        },
    }


@pytest.fixture
def sample_workflow_file(tmp_path: Path, sample_workflow_data: Dict[str, Any]) -> Path:
    """Create a sample workflow file for testing."""
    workflow_file = tmp_path / "sample_workflow.json"
    with open(workflow_file, "w") as f:
        json.dump(sample_workflow_data, f, indent=2)
    return workflow_file


@pytest.fixture
def mock_api_response() -> Dict[str, Any]:
    """Mock API response data for testing."""
    return {
        "id": 12345,
        "name": "Test Model",
        "type": "Checkpoint",
        "modelVersions": [
            {
                "id": 67890,
                "name": "v1.0",
                "files": [
                    {
                        "name": "test_model.safetensors",
                        "downloadUrl": "https://civitai.com/api/download/models/67890",
                        "sizeKB": 2048000,
                    }
                ],
            }
        ],
    }


@pytest.fixture
def mock_huggingface_response() -> Dict[str, Any]:
    """Mock HuggingFace API response data."""
    return {
        "repo": "test/repo",
        "file_path": "models/test_model.safetensors",
        "download_url": "https://huggingface.co/test/repo/resolve/main/models/test_model.safetensors",
        "size": 2097152000,
    }


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for consistent testing."""
    env_vars = {
        "CIVITAI_API_KEY": "test_api_key_32_chars_long_12345",
        "COMFYUI_ROOT": "/tmp/comfyui",
        "PYTHONPATH": "/home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart/src",
    }
    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture
def mock_requests_get():
    """Mock requests.get for API testing."""
    with patch("requests.get") as mock_get:
        yield mock_get


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for command execution testing."""
    with patch("subprocess.run") as mock_run:
        yield mock_run


class TestHelpers:
    """Helper utilities for tests."""

    @staticmethod
    def create_mock_model_file(directory: Path, filename: str, size: int = 1024) -> Path:
        """Create a mock model file with specified size."""
        file_path = directory / filename
        with open(file_path, "wb") as f:
            f.write(b"0" * size)
        return file_path

    @staticmethod
    def create_mock_workflow(directory: Path, name: str, models: list) -> Path:
        """Create a mock workflow file with model references."""
        workflow_data = {}
        node_id = 1

        for model in models:
            workflow_data[str(node_id)] = {
                "class_type": model.get("node_type", "CheckpointLoaderSimple"),
                "inputs": {model.get("input_key", "ckpt_name"): model["filename"]},
            }
            node_id += 1

        workflow_file = directory / f"{name}.json"
        with open(workflow_file, "w") as f:
            json.dump(workflow_data, f, indent=2)

        return workflow_file


# Make TestHelpers available as a fixture
@pytest.fixture
def test_helpers():
    """Provide test helper utilities."""
    return TestHelpers()
