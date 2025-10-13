"""
Unit tests for the utils module.

Tests utility functions for API key management, model type determination,
file operations, validation, and data handling.
"""

import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from comfyfixersmart.utils import (
    get_api_key, validate_api_key, determine_model_type, validate_model_filename,
    get_file_checksum, validate_url, safe_path_join, ensure_directory,
    find_files_by_pattern, get_file_size, validate_json_file, load_json_file,
    save_json_file, build_local_inventory, extract_models_from_workflow,
    _is_model_filename, format_file_size, sanitize_filename, get_relative_path
)


class TestAPIKeyFunctions:
    """Test API key related functions."""

    @patch.dict(os.environ, {"CIVITAI_API_KEY": "a1b2c3d4e5f678901234567890abcdef"}, clear=True)
    def test_get_api_key_success(self):
        """Test successful API key retrieval."""
        key = get_api_key()
        assert key == "a1b2c3d4e5f678901234567890abcdef"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_api_key_missing(self):
        """Test API key retrieval when environment variable is missing."""
        with pytest.raises(ValueError, match="CIVITAI_API_KEY environment variable not found"):
            get_api_key()

    def test_validate_api_key_valid(self):
        """Test validation of valid API key."""
        valid_key = "a1b2c3d4e5f678901234567890abcdef"
        assert validate_api_key(valid_key) is True

    def test_validate_api_key_invalid_length(self):
        """Test validation of API key with wrong length."""
        invalid_key = "short_key"
        assert validate_api_key(invalid_key) is False

    def test_validate_api_key_invalid_chars(self):
        """Test validation of API key with invalid characters."""
        invalid_key = "a1b2c3d4e5f678901234567890abcdeg"  # contains 'g'
        assert validate_api_key(invalid_key) is False

    def test_validate_api_key_empty(self):
        """Test validation of empty API key."""
        assert validate_api_key("") is False

    def test_validate_api_key_none(self):
        """Test validation of None API key."""
        assert validate_api_key(None) is False


class TestModelTypeFunctions:
    """Test model type determination functions."""

    def test_determine_model_type_known_types(self):
        """Test model type determination for known node types."""
        test_cases = [
            ('CheckpointLoaderSimple', 'checkpoints'),
            ('CheckpointLoader', 'checkpoints'),
            ('LoraLoader', 'loras'),
            ('VAELoader', 'vae'),
            ('CLIPLoader', 'clip'),
            ('ControlNetLoader', 'controlnet'),
            ('UpscaleModelLoader', 'upscale_models'),
            ('CLIPVisionLoader', 'clip_vision'),
            ('UNETLoader', 'unet'),
            ('SAMLoader', 'sams'),
            ('GroundingDinoModelLoader', 'grounding-dino'),
        ]

        for node_type, expected in test_cases:
            assert determine_model_type(node_type) == expected

    def test_determine_model_type_unknown_type(self):
        """Test model type determination for unknown node types."""
        assert determine_model_type('UnknownLoader') == 'checkpoints'  # default

    def test_determine_model_type_custom_mapping(self):
        """Test model type determination with custom mapping."""
        custom_mapping = {
            'CustomLoader': 'custom_models',
            'AnotherLoader': 'another_type'
        }

        assert determine_model_type('CustomLoader', custom_mapping) == 'custom_models'
        assert determine_model_type('AnotherLoader', custom_mapping) == 'another_type'
        assert determine_model_type('UnknownLoader', custom_mapping) == 'checkpoints'  # default

    def test_determine_model_type_empty_custom_mapping(self):
        """Test model type determination with empty custom mapping."""
        assert determine_model_type('CheckpointLoader', {}) == 'checkpoints'  # default


class TestFilenameValidation:
    """Test filename validation functions."""

    def test_validate_model_filename_valid(self):
        """Test validation of valid model filenames."""
        valid_filenames = [
            'model.safetensors',
            'checkpoint.ckpt',
            'network.pt',
            'weights.bin',
            'model.pth',
            'MODEL.SAFETENSORS',  # uppercase
            'path/to/model.safetensors'
        ]

        for filename in valid_filenames:
            assert validate_model_filename(filename) is True

    def test_validate_model_filename_invalid_extension(self):
        """Test validation of filenames with invalid extensions."""
        invalid_filenames = [
            'model.txt',
            'model.jpg',
            'model.zip',
            'model'
        ]

        for filename in invalid_filenames:
            assert validate_model_filename(filename) is False

    def test_validate_model_filename_too_short(self):
        """Test validation of filenames that are too short."""
        assert validate_model_filename('a.pt') is False

    def test_validate_model_filename_too_long(self):
        """Test validation of filenames that are too long."""
        long_name = 'a' * 256 + '.safetensors'
        assert validate_model_filename(long_name) is False

    def test_validate_model_filename_suspicious_chars(self):
        """Test validation of filenames with suspicious characters."""
        suspicious_names = [
            'model<.safetensors',
            'model>.safetensors',
            'model:.safetensors',
            'model".safetensors',
            'model|.safetensors',
            'model?.safetensors',
            'model*.safetensors'
        ]

        for filename in suspicious_names:
            assert validate_model_filename(filename) is False

    def test_validate_model_filename_empty(self):
        """Test validation of empty filename."""
        assert validate_model_filename('') is False

    def test_validate_model_filename_none(self):
        """Test validation of None filename."""
        assert validate_model_filename(None) is False

    def test_is_model_filename_valid(self):
        """Test _is_model_filename function with valid filenames."""
        valid_filenames = [
            'model.safetensors',
            'model.ckpt',
            'model.pt',
            'model.bin',
            'model.pth'
        ]

        for filename in valid_filenames:
            assert _is_model_filename(filename) is True

    def test_is_model_filename_invalid(self):
        """Test _is_model_filename function with invalid filenames."""
        invalid_filenames = [
            'model.txt',
            'model',
            '',
            None
        ]

        for filename in invalid_filenames:
            assert _is_model_filename(filename) is False


class TestFileOperations:
    """Test file operation functions."""

    def test_get_file_checksum_valid_file(self, tmp_path):
        """Test checksum calculation for valid file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        checksum = get_file_checksum(test_file)
        assert checksum is not None
        assert len(checksum) == 64  # SHA256 hex length

    def test_get_file_checksum_nonexistent_file(self):
        """Test checksum calculation for nonexistent file."""
        checksum = get_file_checksum("/nonexistent/file.txt")
        assert checksum is None

    def test_get_file_checksum_directory(self, tmp_path):
        """Test checksum calculation for directory."""
        checksum = get_file_checksum(tmp_path)
        assert checksum is None

    def test_get_file_checksum_invalid_algorithm(self, tmp_path):
        """Test checksum calculation with invalid algorithm."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        checksum = get_file_checksum(test_file, "invalid_algorithm")
        assert checksum is None

    def test_get_file_size_valid_file(self, tmp_path):
        """Test file size retrieval for valid file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"  # 13 bytes
        test_file.write_bytes(test_content)

        size = get_file_size(test_file)
        assert size == 13

    def test_get_file_size_nonexistent_file(self):
        """Test file size retrieval for nonexistent file."""
        size = get_file_size("/nonexistent/file.txt")
        assert size is None

    def test_get_file_size_directory(self, tmp_path):
        """Test file size retrieval for directory."""
        size = get_file_size(tmp_path)
        assert size is None


class TestURLValidation:
    """Test URL validation functions."""

    def test_validate_url_valid(self):
        """Test validation of valid URLs."""
        valid_urls = [
            'https://example.com',
            'http://example.com/path',
            'https://example.com:8080/path?query=value',
            'ftp://example.com/file.txt'
        ]

        for url in valid_urls:
            assert validate_url(url) is True

    def test_validate_url_invalid(self):
        """Test validation of invalid URLs."""
        invalid_urls = [
            'not-a-url',
            'example.com',
            '://example.com',
            '',
            None
        ]

        for url in invalid_urls:
            assert validate_url(url) is False


class TestPathOperations:
    """Test path-related functions."""

    def test_safe_path_join_normal_paths(self, tmp_path):
        """Test safe path joining with normal paths."""
        base = tmp_path / "base"
        result = safe_path_join(base, "subdir", "file.txt")
        expected = base / "subdir" / "file.txt"
        assert result == expected

    def test_safe_path_join_directory_traversal(self, tmp_path):
        """Test safe path joining with directory traversal attempt."""
        base = tmp_path / "base"

        with pytest.raises(ValueError, match="Unsafe path component"):
            safe_path_join(base, "..", "file.txt")

    def test_safe_path_join_absolute_path(self, tmp_path):
        """Test safe path joining with absolute path component."""
        base = tmp_path / "base"

        with pytest.raises(ValueError, match="Unsafe path component"):
            safe_path_join(base, "/absolute", "file.txt")

    def test_safe_path_join_traversal_after_resolve(self, tmp_path):
        """Test safe path joining that results in path traversal after resolution."""
        base = tmp_path / "base"
        base.mkdir()

        # Create a scenario where traversal happens after joining
        # This is harder to test directly, but the function should handle it
        result = safe_path_join(base, "safe", "path")
        assert str(result).startswith(str(base.resolve()))

    def test_ensure_directory_create_new(self, tmp_path):
        """Test directory creation when directory doesn't exist."""
        new_dir = tmp_path / "new_dir"
        result = ensure_directory(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()
        assert result == new_dir

    def test_ensure_directory_already_exists(self, tmp_path):
        """Test directory creation when directory already exists."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        result = ensure_directory(existing_dir)
        assert result == existing_dir

    def test_ensure_directory_with_parents(self, tmp_path):
        """Test directory creation with parent directories."""
        nested_dir = tmp_path / "parent" / "child" / "grandchild"
        result = ensure_directory(nested_dir)

        assert nested_dir.exists()
        assert nested_dir.is_dir()
        assert result == nested_dir

    def test_find_files_by_pattern_recursive(self, tmp_path):
        """Test file finding with recursive pattern matching."""
        # Create test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file2.txt").write_text("content2")
        (tmp_path / "subdir" / "file3.json").write_text("content3")

        # Find all .txt files recursively
        txt_files = find_files_by_pattern(tmp_path, "*.txt", recursive=True)
        txt_names = {f.name for f in txt_files}

        assert txt_names == {"file1.txt", "file2.txt"}

    def test_find_files_by_pattern_non_recursive(self, tmp_path):
        """Test file finding with non-recursive pattern matching."""
        # Create test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file2.txt").write_text("content2")

        # Find .txt files in root only
        txt_files = find_files_by_pattern(tmp_path, "*.txt", recursive=False)
        txt_names = {f.name for f in txt_files}

        assert txt_names == {"file1.txt"}

    def test_find_files_by_pattern_nonexistent_directory(self):
        """Test file finding in nonexistent directory."""
        result = find_files_by_pattern("/nonexistent", "*.txt")
        assert result == []


class TestJSONOperations:
    """Test JSON file operations."""

    def test_validate_json_file_valid(self, tmp_path):
        """Test JSON file validation with valid JSON."""
        json_file = tmp_path / "valid.json"
        json_file.write_text('{"key": "value", "number": 42}')

        assert validate_json_file(json_file) is True

    def test_validate_json_file_invalid(self, tmp_path):
        """Test JSON file validation with invalid JSON."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text('{"key": "value", invalid}')

        assert validate_json_file(json_file) is False

    def test_validate_json_file_nonexistent(self):
        """Test JSON file validation with nonexistent file."""
        assert validate_json_file("/nonexistent.json") is False

    def test_load_json_file_valid(self, tmp_path):
        """Test JSON file loading with valid file."""
        json_file = tmp_path / "test.json"
        test_data = {"key": "value", "list": [1, 2, 3]}
        json_file.write_text(json.dumps(test_data))

        result = load_json_file(json_file)
        assert result == test_data

    def test_load_json_file_invalid(self, tmp_path):
        """Test JSON file loading with invalid JSON."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text('invalid json')

        result = load_json_file(json_file, default="fallback")
        assert result == "fallback"

    def test_load_json_file_nonexistent(self):
        """Test JSON file loading with nonexistent file."""
        result = load_json_file("/nonexistent.json", default="fallback")
        assert result == "fallback"

    def test_save_json_file_success(self, tmp_path):
        """Test successful JSON file saving."""
        json_file = tmp_path / "output.json"
        test_data = {"key": "value", "nested": {"inner": 123}}

        result = save_json_file(json_file, test_data)
        assert result is True
        assert json_file.exists()

        # Verify content
        loaded = json.loads(json_file.read_text())
        assert loaded == test_data

    def test_save_json_file_invalid_data(self, tmp_path):
        """Test JSON file saving with invalid data."""
        json_file = tmp_path / "output.json"

        # Try to save a set (not JSON serializable)
        result = save_json_file(json_file, {1, 2, 3})
        assert result is False

    def test_save_json_file_permission_error(self):
        """Test JSON file saving with permission error."""
        # Try to save to a directory that doesn't allow writing
        result = save_json_file("/root/forbidden.json", {"data": "test"})
        assert result is False


class TestInventoryOperations:
    """Test inventory building functions."""

    def test_build_local_inventory_with_models(self, tmp_path):
        """Test local inventory building with model files."""
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        # Create subdirectories and model files
        checkpoints_dir = models_dir / "checkpoints"
        checkpoints_dir.mkdir()
        (checkpoints_dir / "model1.safetensors").write_text("fake model")
        (checkpoints_dir / "model2.ckpt").write_text("fake model")

        loras_dir = models_dir / "loras"
        loras_dir.mkdir()
        (loras_dir / "lora1.safetensors").write_text("fake lora")

        # Create non-model file
        (models_dir / "readme.txt").write_text("readme")

        inventory = build_local_inventory(models_dir)
        expected = {"model1.safetensors", "model2.ckpt", "lora1.safetensors"}

        assert inventory == expected

    def test_build_local_inventory_empty_directory(self, tmp_path):
        """Test local inventory building with empty directory."""
        models_dir = tmp_path / "empty_models"
        models_dir.mkdir()

        inventory = build_local_inventory(models_dir)
        assert inventory == set()

    def test_build_local_inventory_nonexistent_directory(self):
        """Test local inventory building with nonexistent directory."""
        inventory = build_local_inventory("/nonexistent")
        assert inventory == set()

    def test_build_local_inventory_custom_extensions(self, tmp_path):
        """Test local inventory building with custom extensions."""
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        (models_dir / "model1.custom").write_text("fake model")
        (models_dir / "model2.txt").write_text("not a model")

        inventory = build_local_inventory(models_dir, extensions=[".custom"])
        assert inventory == {"model1.custom"}


class TestWorkflowExtraction:
    """Test workflow model extraction functions."""

    def test_extract_models_from_workflow_valid(self, tmp_path):
        """Test model extraction from valid workflow."""
        workflow_file = tmp_path / "workflow.json"

        workflow_data = {
            "nodes": [
                {
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["model.safetensors"]
                },
                {
                    "type": "LoraLoader",
                    "widgets_values": ["lora1.safetensors", 1.0]
                },
                {
                    "type": "VAELoader",
                    "widgets_values": ["vae.safetensors"]
                }
            ]
        }

        workflow_file.write_text(json.dumps(workflow_data))

        models = extract_models_from_workflow(workflow_file)

        expected = [
            {
                'filename': 'model.safetensors',
                'type': 'checkpoints',
                'node_type': 'CheckpointLoaderSimple',
                'workflow_path': str(workflow_file)
            },
            {
                'filename': 'lora1.safetensors',
                'type': 'loras',
                'node_type': 'LoraLoader',
                'workflow_path': str(workflow_file)
            },
            {
                'filename': 'vae.safetensors',
                'type': 'vae',
                'node_type': 'VAELoader',
                'workflow_path': str(workflow_file)
            }
        ]

        assert models == expected

    def test_extract_models_from_workflow_invalid_json(self, tmp_path):
        """Test model extraction from invalid JSON workflow."""
        workflow_file = tmp_path / "invalid.json"
        workflow_file.write_text('invalid json')

        with pytest.raises(ValueError, match="Failed to parse workflow"):
            extract_models_from_workflow(workflow_file)

    def test_extract_models_from_workflow_nonexistent_file(self):
        """Test model extraction from nonexistent workflow file."""
        with pytest.raises(ValueError, match="Failed to parse workflow"):
            extract_models_from_workflow("/nonexistent.json")

    def test_extract_models_from_workflow_no_models(self, tmp_path):
        """Test model extraction from workflow with no models."""
        workflow_file = tmp_path / "no_models.json"

        workflow_data = {
            "nodes": [
                {
                    "type": "CLIPTextEncode",
                    "widgets_values": ["some text"]
                }
            ]
        }

        workflow_file.write_text(json.dumps(workflow_data))

        models = extract_models_from_workflow(workflow_file)
        assert models == []


class TestFormattingFunctions:
    """Test data formatting functions."""

    def test_format_file_size_bytes(self):
        """Test file size formatting for bytes."""
        assert format_file_size(0) == "0 B"
        assert format_file_size(512) == "512 B"
        assert format_file_size(1023) == "1023 B"

    def test_format_file_size_kilobytes(self):
        """Test file size formatting for kilobytes."""
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(1048576 - 1) == "1024.0 KB"

    def test_format_file_size_megabytes(self):
        """Test file size formatting for megabytes."""
        assert format_file_size(1048576) == "1.0 MB"
        assert format_file_size(1073741824 - 1) == "1024.0 MB"

    def test_format_file_size_gigabytes(self):
        """Test file size formatting for gigabytes."""
        assert format_file_size(1073741824) == "1.0 GB"

    def test_sanitize_filename_normal(self):
        """Test filename sanitization with normal filename."""
        assert sanitize_filename("normal_file.txt") == "normal_file.txt"

    def test_sanitize_filename_invalid_chars(self):
        """Test filename sanitization with invalid characters."""
        assert sanitize_filename('file<>:|?*.txt') == 'file_______ .txt'

    def test_sanitize_filename_leading_trailing_spaces(self):
        """Test filename sanitization with leading/trailing spaces and dots."""
        assert sanitize_filename('  .file.txt.  ') == 'file.txt'

    def test_sanitize_filename_empty_after_sanitization(self):
        """Test filename sanitization that results in empty string."""
        assert sanitize_filename('<>:"|?*') == "unnamed_file"

    def test_get_relative_path_valid(self, tmp_path):
        """Test relative path calculation for valid paths."""
        base = tmp_path / "base"
        file_path = base / "subdir" / "file.txt"

        relative = get_relative_path(file_path, base)
        assert relative == "subdir/file.txt"

    def test_get_relative_path_not_relative(self, tmp_path):
        """Test relative path calculation for non-relative paths."""
        base = tmp_path / "base"
        external_path = tmp_path / "external" / "file.txt"

        relative = get_relative_path(external_path, base)
        assert relative is None

    def test_get_relative_path_same_path(self, tmp_path):
        """Test relative path calculation for same path."""
        path = tmp_path / "file.txt"
        relative = get_relative_path(path, tmp_path)
        assert relative == "file.txt"