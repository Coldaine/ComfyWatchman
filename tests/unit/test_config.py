"""
Unit tests for the config module.

Tests configuration loading, validation, environment variable handling,
and TOML configuration support.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from comfyfixersmart.config import Config


class TestConfig:
    """Test cases for the Config class."""

    def test_config_defaults(self):
        """Test that Config initializes with correct defaults."""
        config = Config()

        # Test path defaults
        assert config.output_dir == Path("output")
        assert config.log_dir == Path("log")
        assert config.state_dir == Path("state")
        assert config.temp_dir == Path("/tmp") / "qwen_search_results"

        # Test API defaults
        assert config.civitai_api_base == "https://civitai.com/api/v1"
        assert config.civitai_download_base == "https://civitai.com/api/download/models"
        assert config.civitai_api_timeout == 30

        # Test model settings
        assert ".safetensors" in config.model_extensions
        assert ".ckpt" in config.model_extensions
        assert ".pt" in config.model_extensions
        assert ".bin" in config.model_extensions
        assert ".pth" in config.model_extensions

        # Test model type mapping
        assert config.model_type_mapping['CheckpointLoaderSimple'] == 'checkpoints'
        assert config.model_type_mapping['LoraLoader'] == 'loras'
        assert config.model_type_mapping['VAELoader'] == 'vae'
        assert config.model_type_mapping['ControlNetLoader'] == 'controlnet'

        # Test state management
        assert config.state_file == "download_state.json"

        # Test validation thresholds
        assert config.min_model_size == 1_000_000
        assert config.recent_attempt_hours == 1

    def test_config_initialization_with_params(self):
        """Test Config initialization with custom parameters."""
        custom_config = Config(
            comfyui_root=Path("/custom/comfyui"),
            output_dir=Path("/custom/output"),
            civitai_api_timeout=60,
            min_model_size=2_000_000
        )

        assert custom_config.comfyui_root == Path("/custom/comfyui")
        assert custom_config.output_dir == Path("/custom/output")
        assert custom_config.civitai_api_timeout == 60
        assert custom_config.min_model_size == 2_000_000

    def test_config_validation_success(self, tmp_path):
        """Test successful config validation."""
        config = Config(comfyui_root=tmp_path / "comfyui")
        (tmp_path / "comfyui").mkdir()

        # Should not raise
        config.validate(require_comfyui_path=True)

    def test_config_validation_missing_comfyui_root(self):
        """Test validation failure when ComfyUI root is required but missing."""
        config = Config(comfyui_root=None)

        with pytest.raises(ValueError, match="comfyui_root must be configured"):
            config.validate(require_comfyui_path=True)

    def test_config_validation_comfyui_root_not_exists(self, tmp_path):
        """Test validation failure when ComfyUI root doesn't exist."""
        config = Config(comfyui_root=tmp_path / "nonexistent")

        with pytest.raises(ValueError, match="ComfyUI root does not exist"):
            config.validate(require_comfyui_path=True)

    def test_config_validation_invalid_timeout(self):
        """Test validation failure for invalid API timeout."""
        config = Config(civitai_api_timeout=3)

        with pytest.raises(ValueError, match="civitai_api_timeout must be at least 5 seconds"):
            config.validate(require_comfyui_path=False)

    def test_config_validation_invalid_min_size(self):
        """Test validation failure for invalid minimum model size."""
        config = Config(min_model_size=-1)

        with pytest.raises(ValueError, match="min_model_size must be non-negative"):
            config.validate(require_comfyui_path=False)

    @patch.dict(os.environ, {"COMFYUI_ROOT": "/env/comfyui"}, clear=True)
    def test_env_override_comfyui_root(self):
        """Test environment variable override for ComfyUI root."""
        config = Config()
        assert config.comfyui_root == Path("/env/comfyui")

    @patch.dict(os.environ, {"OUTPUT_DIR": "/env/output"}, clear=True)
    def test_env_override_output_dir(self):
        """Test environment variable override for output directory."""
        config = Config()
        assert config.output_dir == Path("/env/output")

    @patch.dict(os.environ, {"LOG_DIR": "/env/log"}, clear=True)
    def test_env_override_log_dir(self):
        """Test environment variable override for log directory."""
        config = Config()
        assert config.log_dir == Path("/env/log")

    @patch.dict(os.environ, {"STATE_DIR": "/env/state"}, clear=True)
    def test_env_override_state_dir(self):
        """Test environment variable override for state directory."""
        config = Config()
        assert config.state_dir == Path("/env/state")

    @patch.dict(os.environ, {"TEMP_DIR": "/env/temp"}, clear=True)
    def test_env_override_temp_dir(self):
        """Test environment variable override for temp directory."""
        config = Config()
        assert config.temp_dir == Path("/env/temp")

    @patch.dict(os.environ, {"CIVITAI_API_TIMEOUT": "45"}, clear=True)
    def test_env_override_api_timeout(self):
        """Test environment variable override for API timeout."""
        config = Config()
        assert config.civitai_api_timeout == 45

    @patch.dict(os.environ, {"MIN_MODEL_SIZE": "2000000"}, clear=True)
    def test_env_override_min_model_size(self):
        """Test environment variable override for minimum model size."""
        config = Config()
        assert config.min_model_size == 2000000

    @patch.dict(os.environ, {"RECENT_ATTEMPT_HOURS": "2"}, clear=True)
    def test_env_override_recent_attempt_hours(self):
        """Test environment variable override for recent attempt hours."""
        config = Config()
        assert config.recent_attempt_hours == 2

    @patch.dict(os.environ, {"ENABLE_CLAUDE_VERIFICATION": "true"}, clear=True)
    def test_env_override_claude_verification_true(self):
        """Test environment variable override for Claude verification (true)."""
        config = Config()
        assert config.enable_claude_verification is True

    @patch.dict(os.environ, {"ENABLE_CLAUDE_VERIFICATION": "false"}, clear=True)
    def test_env_override_claude_verification_false(self):
        """Test environment variable override for Claude verification (false)."""
        config = Config()
        assert config.enable_claude_verification is False

    @patch.dict(os.environ, {"INVALID_ENV_VAR": "value"}, clear=True)
    def test_env_override_invalid_key(self):
        """Test that invalid environment variables are ignored."""
        config = Config()
        # Should not have any attribute for invalid env var
        assert not hasattr(config, 'invalid_env_var')

    @patch.dict(os.environ, {"CIVITAI_API_TIMEOUT": "invalid"}, clear=True)
    def test_env_override_invalid_value(self, capsys):
        """Test handling of invalid environment variable values."""
        config = Config()
        # Should keep default value
        assert config.civitai_api_timeout == 30

        # Should print warning
        captured = capsys.readouterr()
        assert "Warning: Invalid value for CIVITAI_API_TIMEOUT" in captured.err

    def test_toml_loading_success(self, tmp_path):
        """Test successful TOML configuration loading."""
        # Create a temporary config directory and file
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "default.toml"

        toml_content = """
[paths]
comfyui_root = "/toml/comfyui"
output_dir = "/toml/output"

[api]
civitai_api_timeout = 60

[validation]
min_model_size = 3000000
"""

        config_file.write_text(toml_content)

        # Change to the temp directory so config loading works
        with patch('pathlib.Path.cwd', return_value=tmp_path):
            config = Config()

        assert config.comfyui_root == Path("/toml/comfyui")
        assert config.output_dir == Path("/toml/output")
        assert config.civitai_api_timeout == 60
        assert config.min_model_size == 3000000

    def test_toml_loading_file_not_exists(self):
        """Test TOML loading when config file doesn't exist."""
        # Should not raise, just use defaults
        config = Config()
        assert config.civitai_api_timeout == 30  # default value

    def test_toml_loading_invalid_format(self, tmp_path, capsys):
        """Test TOML loading with invalid format."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "default.toml"

        # Write invalid TOML
        config_file.write_text("invalid toml content [")

        with patch('pathlib.Path.cwd', return_value=tmp_path):
            config = Config()

        # Should print warning but continue with defaults
        captured = capsys.readouterr()
        assert "Warning: Failed to load TOML config" in captured.err
        assert config.civitai_api_timeout == 30  # default value

    def test_ensure_dirs_creation(self, tmp_path):
        """Test that directories are created during initialization."""
        output_dir = tmp_path / "output"
        log_dir = tmp_path / "log"
        state_dir = tmp_path / "state"
        temp_dir = tmp_path / "temp"

        config = Config(
            output_dir=output_dir,
            log_dir=log_dir,
            state_dir=state_dir,
            temp_dir=temp_dir
        )

        assert output_dir.exists()
        assert log_dir.exists()
        assert state_dir.exists()
        assert temp_dir.exists()

    def test_models_dir_property(self, tmp_path):
        """Test models_dir property."""
        config = Config(comfyui_root=tmp_path / "comfyui")
        expected = tmp_path / "comfyui" / "models"
        assert config.models_dir == expected

    def test_models_dir_property_none(self):
        """Test models_dir property when comfyui_root is None."""
        config = Config(comfyui_root=None)
        assert config.models_dir is None

    def test_state_file_path_property(self, tmp_path):
        """Test state_file_path property."""
        config = Config(state_dir=tmp_path / "state")
        expected = tmp_path / "state" / "download_state.json"
        assert config.state_file_path == expected

    def test_get_log_file_no_run_id(self):
        """Test get_log_file without run ID."""
        config = Config(log_dir=Path("/logs"))
        log_file = config.get_log_file()

        # Should contain current timestamp format
        assert log_file.startswith("/logs/run_")
        assert log_file.endswith(".log")

    def test_get_log_file_with_run_id(self):
        """Test get_log_file with run ID."""
        config = Config(log_dir=Path("/logs"))
        log_file = config.get_log_file("test_run_123")

        assert log_file == "/logs/run_test_run_123.log"

    def test_get_search_log_file(self):
        """Test get_search_log_file method."""
        config = Config(log_dir=Path("/logs"))
        search_log = config.get_search_log_file()

        assert search_log == "/logs/qwen_search_history.log"

    def test_get_download_counter_file(self):
        """Test get_download_counter_file method."""
        config = Config(output_dir=Path("/output"))
        counter_file = config.get_download_counter_file()

        assert counter_file == "/output/download_counter.txt"

    def test_get_missing_models_file_no_run_id(self):
        """Test get_missing_models_file without run ID."""
        config = Config(output_dir=Path("/output"))
        missing_file = config.get_missing_models_file()

        assert missing_file == "/output/missing_models.json"

    def test_get_missing_models_file_with_run_id(self):
        """Test get_missing_models_file with run ID."""
        config = Config(output_dir=Path("/output"))
        missing_file = config.get_missing_models_file("test_run_123")

        assert missing_file == "/output/missing_models_test_run_123.json"

    def test_get_resolutions_file_no_run_id(self):
        """Test get_resolutions_file without run ID."""
        config = Config(output_dir=Path("/output"))
        resolutions_file = config.get_resolutions_file()

        assert resolutions_file == "/output/resolutions.json"

    def test_get_resolutions_file_with_run_id(self):
        """Test get_resolutions_file with run ID."""
        config = Config(output_dir=Path("/output"))
        resolutions_file = config.get_resolutions_file("test_run_123")

        assert resolutions_file == "/output/resolutions_test_run_123.json"

    def test_update_from_dict_basic(self):
        """Test _update_from_dict with basic values."""
        config = Config()
        data = {
            "civitai_api_timeout": 45,
            "min_model_size": 2000000,
            "enable_claude_verification": True
        }

        config._update_from_dict(data)

        assert config.civitai_api_timeout == 45
        assert config.min_model_size == 2000000
        assert config.enable_claude_verification is True

    def test_update_from_dict_paths(self, tmp_path):
        """Test _update_from_dict with path values."""
        config = Config()
        data = {
            "comfyui_root": str(tmp_path / "comfyui"),
            "output_dir": str(tmp_path / "output"),
            "workflow_dirs": [str(tmp_path / "workflows")]
        }

        config._update_from_dict(data)

        assert config.comfyui_root == tmp_path / "comfyui"
        assert config.output_dir == tmp_path / "output"
        assert config.workflow_dirs == [tmp_path / "workflows"]

    def test_update_from_dict_lists_and_dicts(self):
        """Test _update_from_dict with lists and dicts."""
        config = Config()
        data = {
            "model_extensions": [".safetensors", ".custom"],
            "model_type_mapping": {"CustomLoader": "custom"}
        }

        config._update_from_dict(data)

        assert ".custom" in config.model_extensions
        assert config.model_type_mapping["CustomLoader"] == "custom"

    def test_update_from_dict_invalid_key(self):
        """Test _update_from_dict with invalid key (should be ignored)."""
        config = Config()
        original_timeout = config.civitai_api_timeout

        data = {"invalid_key": "value"}
        config._update_from_dict(data)

        # Should not change anything
        assert config.civitai_api_timeout == original_timeout
        assert not hasattr(config, 'invalid_key')