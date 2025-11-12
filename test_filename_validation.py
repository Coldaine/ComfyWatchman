#!/usr/bin/env python3
"""
Test suite for enhanced filename validation with pattern detection.

Tests the enhanced validate_and_sanitize_filename function and its integration
into the search workflow, including early return logic for INVALID_FILENAME status.
"""

import pytest
import sys
from pathlib import Path

# Add the source directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from comfywatchman.utils import validate_and_sanitize_filename, sanitize_filename
from comfywatchman.search import (
    SearchResult,
    CivitaiSearch,
    QwenSearch,
    HuggingFaceSearch,
)


class TestFilenameValidation:
    """Test cases for enhanced filename validation."""

    def test_valid_filenames(self):
        """Test that valid filenames pass validation."""
        valid_filenames = [
            "model.safetensors",
            "checkpoint_v1.0.safetensors",
            "lora-trained-model_v2.pt",
            "VAE_kl-f8-anime-v2_1.ckpt",
            "controlnet_canny.safetensors",
            "simple_name.pth",
            "model-with-dashes.bin",
            "model_with_underscores.pt",
            "textual_inversion_v1.safetensors",
        ]

        for filename in valid_filenames:
            is_valid, sanitized, error_reason = validate_and_sanitize_filename(filename)
            assert is_valid, f"Valid filename {filename} should pass validation"
            assert sanitized, "Sanitized filename should not be empty"
            assert (
                error_reason is None
            ), f"Valid filename {filename} should not have error reason"

    def test_url_patterns(self):
        """Test detection of URL patterns in filenames."""
        url_filenames = [
            "http://evil.com/model.safetensors",
            "https://malicious.com/file.pt",
            "ftp://bad.com/data.ckpt",
            "file://local/path/model.bin",
            "modelhttp://evil.com.safetensors",
        ]

        for filename in url_filenames:
            is_valid, sanitized, error_reason = validate_and_sanitize_filename(filename)
            assert not is_valid, f"URL pattern in {filename} should be detected"
            assert (
                "URL pattern detected" in error_reason
            ), f"Should detect URL pattern in {filename}"

    def test_newline_characters(self):
        """Test detection of newline characters in filenames."""
        newline_filenames = [
            "model\nname.safetensors",
            "model\rname.pt",
            "model\r\nname.ckpt",
            "model\nwith\nnewlines.bin",
        ]

        for filename in newline_filenames:
            is_valid, sanitized, error_reason = validate_and_sanitize_filename(filename)
            assert not is_valid, f"Newline in {filename} should be detected"
            assert (
                "Newline characters detected" in error_reason
            ), f"Should detect newlines in {filename}"

    def test_path_traversal_patterns(self):
        """Test detection of path traversal attempts."""
        traversal_filenames = [
            "../etc/passwd.safetensors",
            "../../bin/bash.pt",
            ".\\windows\\system32\\file.ckpt",
            "safe_name../../../etc/passwd.bin",
            "./sensitive/file.safetensors",
        ]

        for filename in traversal_filenames:
            is_valid, sanitized, error_reason = validate_and_sanitize_filename(filename)
            assert not is_valid, f"Path traversal in {filename} should be detected"
            assert (
                "Path traversal pattern detected" in error_reason
            ), f"Should detect path traversal in {filename}"

    def test_control_characters(self):
        """Test detection of control characters (excluding tabs, LF, CR)."""
        control_filenames = [
            "model\x00name.safetensors",  # Null byte
            "model\x01control.bin",  # SOH (Start of Heading)
            "model\x7fdelete.pt",  # DEL (Delete)
            "model\x02bel.bin",  # BEL (Bell)
        ]

        for filename in control_filenames:
            is_valid, sanitized, error_reason = validate_and_sanitize_filename(filename)
            assert (
                not is_valid
            ), f"Control characters in {repr(filename)} should be detected"
            assert (
                "Control characters detected" in error_reason
            ), f"Should detect control chars in {repr(filename)}"

    def test_excessive_special_characters(self):
        """Test detection of excessive special characters."""
        # More than 50% special characters
        excessive_special = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~\xf1\xf2.safetensors"

        is_valid, sanitized, error_reason = validate_and_sanitize_filename(
            excessive_special
        )
        assert not is_valid, "Excessive special characters should be detected"
        assert (
            "Excessive special characters" in error_reason
        ), "Should detect excessive special chars"

    def test_command_injection_patterns(self):
        """Test detection of command injection patterns."""
        injection_filenames = [
            "model$(whoami).safetensors",
            "file`id`.pt",
            "name;rm -rf /.ckpt",
            "model|evil.bin",
            "file&malicious.pt",
            "name!bang.safetensors",
        ]

        for filename in injection_filenames:
            is_valid, sanitized, error_reason = validate_and_sanitize_filename(filename)
            assert (
                not is_valid
            ), f"Command injection pattern in {filename} should be detected"
            assert (
                "Potential command injection pattern detected" in error_reason
            ), f"Should detect injection in {filename}"

    def test_excessive_length(self):
        """Test detection of excessively long filenames."""
        # Create a filename longer than 500 characters
        long_name = "a" * 600 + ".safetensors"

        is_valid, sanitized, error_reason = validate_and_sanitize_filename(long_name)
        assert not is_valid, "Excessively long filename should be detected"
        assert "Filename too long" in error_reason, "Should detect excessive length"

    def test_double_extensions(self):
        """Test detection of suspicious double extensions."""
        double_ext_filenames = [
            "model..safetensors",
            "file.backdoor.safetensors",
            "model.v1.0.backdoor.pt",
        ]

        for filename in double_ext_filenames:
            is_valid, sanitized, error_reason = validate_and_sanitize_filename(filename)
            assert not is_valid, f"Double extension in {filename} should be detected"
            assert (
                "Suspicious file extension pattern detected" in error_reason
            ), f"Should detect double ext in {filename}"

    def test_empty_and_invalid_inputs(self):
        """Test handling of empty and invalid inputs."""
        invalid_inputs = [
            "",  # Empty string
            None,  # None value
            123,  # Integer (not string)
            [],  # List
        ]

        for invalid_input in invalid_inputs:
            if invalid_input is None:
                # None should cause an error
                with pytest.raises(TypeError):
                    validate_and_sanitize_filename(invalid_input)
            else:
                is_valid, sanitized, error_reason = validate_and_sanitize_filename(
                    invalid_input
                )
                assert (
                    not is_valid
                ), f"Invalid input {repr(invalid_input)} should fail validation"
                assert (
                    "Empty or non-string filename" in error_reason
                ), f"Should detect invalid input {repr(invalid_input)}"

    def test_legacy_sanitize_filename_compatibility(self):
        """Test that legacy sanitize_filename function still works."""
        test_cases = [
            ("normal_model.safetensors", "normal_model.safetensors"),
            ("model/with*invalid>chars.pt", "model_with_invalid_chars.pt"),
            ("  spaced name  .ckpt", "spaced name .ckpt"),
        ]

        for input_filename, expected in test_cases:
            result = sanitize_filename(input_filename)
            assert (
                result == expected
            ), f"Legacy sanitize_filename should work for {input_filename}"


class TestSearchBackendIntegration:
    """Test integration of filename validation in search backends."""

    def test_civitai_search_invalid_filename(self):
        """Test CivitaiSearch returns INVALID_FILENAME for problematic filenames."""
        backend = CivitaiSearch()

        # Test with malicious filename
        model_info = {
            "filename": "http://evil.com/malicious.safetensors",
            "type": "checkpoints",
        }

        result = backend.search(model_info)
        assert (
            result.status == "INVALID_FILENAME"
        ), "Should return INVALID_FILENAME status"
        assert result.error_message is not None, "Should have error message"
        assert (
            "URL pattern detected" in result.error_message
        ), "Should include validation reason"

    def test_qwen_search_invalid_filename(self):
        """Test QwenSearch returns INVALID_FILENAME for problematic filenames."""
        backend = QwenSearch()

        # Test with newline in filename
        model_info = {"filename": "model\nwith\nnewlines.pt", "type": "loras"}

        result = backend.search(model_info)
        assert (
            result.status == "INVALID_FILENAME"
        ), "Should return INVALID_FILENAME status"
        assert result.error_message is not None, "Should have error message"
        assert (
            "Newline characters detected" in result.error_message
        ), "Should include validation reason"

    def test_huggingface_search_invalid_filename(self):
        """Test HuggingFaceSearch returns INVALID_FILENAME for problematic filenames."""
        backend = HuggingFaceSearch()

        # Test with path traversal
        model_info = {
            "filename": "../../../etc/passwd.safetensors",
            "type": "checkpoints",
        }

        result = backend.search(model_info)
        assert (
            result.status == "INVALID_FILENAME"
        ), "Should return INVALID_FILENAME status"
        assert result.error_message is not None, "Should have error message"
        assert (
            "Path traversal pattern detected" in result.error_message
        ), "Should include validation reason"

    def test_valid_filename_processing(self):
        """Test that valid filenames are processed normally by all backends."""
        valid_filenames = [
            ("normal_model.safetensors", "checkpoints"),
            ("lora_v1.pt", "loras"),
            ("vae_kl_f8.ckpt", "vae"),
        ]

        backends = [
            ("CivitaiSearch", CivitaiSearch()),
            ("QwenSearch", QwenSearch()),
            ("HuggingFaceSearch", HuggingFaceSearch()),
        ]

        for backend_name, backend in backends:
            for filename, model_type in valid_filenames:
                model_info = {"filename": filename, "type": model_type}

                # Should NOT return INVALID_FILENAME for valid filenames
                # (might return NOT_FOUND or other status, but not INVALID_FILENAME)
                result = backend.search(model_info)
                assert (
                    result.status != "INVALID_FILENAME"
                ), f"{backend_name} should not reject valid filename {filename}"


class TestRealWorldExamples:
    """Test with real-world examples of problematic filenames."""

    def test_malicious_workflow_filenames(self):
        """Test filenames that might appear in malicious workflows."""
        malicious_examples = [
            # XSS attempt
            "<script>alert('xss')</script>.safetensors",
            # SQL injection attempt
            "'; DROP TABLE models; --.pt",
            # Command injection
            "model$(cat /etc/passwd).safetensors",
            # Unicode attacks
            "model\u202e\u202d\u202c.safetensors",  # Right-to-left override
            # Null byte attack
            "model\x00.safetensors",
        ]

        for filename in malicious_examples:
            is_valid, sanitized, error_reason = validate_and_sanitize_filename(filename)
            assert (
                not is_valid
            ), f"Malicious pattern in {repr(filename)} should be detected"
            assert (
                error_reason is not None
            ), f"Should provide error reason for {repr(filename)}"

    def test_accidental_malformed_filenames(self):
        """Test accidentally malformed filenames from data corruption or export issues."""
        malformed_examples = [
            # Copy-paste errors with URLs
            "https://civitai.com/api/download/models/12345.safetensors",
            # Line-wrapped content
            "model_name\nhttps://example.com/download.pt",
            # JSON export issues
            '{"filename": "escaped"quote.safetensors"}',
            # Path corruption
            "/home/user/models/model_name.safetensors",
            # Double extensions from downloads
            "model.safetensors.download",
        ]

        for filename in malformed_examples:
            is_valid, sanitized, error_reason = validate_and_sanitize_filename(filename)
            # Some might be valid after sanitization, others should be invalid
            if not is_valid:
                assert (
                    error_reason is not None
                ), f"Should provide error reason for malformed {filename}"
            else:
                # If valid after sanitization, sanitized should be different from original
                assert (
                    sanitized != filename
                ), f"Valid filename {filename} should be sanitized"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
