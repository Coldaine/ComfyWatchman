"""
Unit tests for new search features in ComfyFixerSmart.

Tests TavilyAPI integration, enhanced CivitaiSearch features, QwenSearch pattern recognition,
HuggingFaceSearch web search and verification, and related functionality.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import requests

from comfyfixersmart.search import (
    TavilyAPI,
    CivitaiSearch,
    QwenSearch,
    HuggingFaceSearch,
    SearchResult,
    validate_and_sanitize_filename,
)


class TestTavilyAPI:
    """Test TavilyAPI client functionality."""

    def test_tavily_api_initialization(self):
        """Test TavilyAPI initialization."""
        api = TavilyAPI()
        assert api.base_url == "https://api.tavily.com"
        assert hasattr(api, 'api_key')
        assert hasattr(api, '_session')

    def test_tavily_api_is_available_with_key(self):
        """Test is_available when API key is set."""
        with patch.dict(os.environ, {"TAVILY_API_KEY": "test_key"}):
            api = TavilyAPI()
            assert api.is_available() is True

    def test_tavily_api_is_available_without_key(self):
        """Test is_available when API key is not set."""
        with patch.dict(os.environ, {}, clear=True):
            api = TavilyAPI()
            assert api.is_available() is False

    @patch("requests.Session.post")
    def test_tavily_api_search_success(self, mock_post):
        """Test successful web search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"url": "https://example.com", "title": "Test Result", "content": "Test content"}
            ]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"TAVILY_API_KEY": "test_key"}):
            api = TavilyAPI()
            results = api.search("test query")

            assert results is not None
            assert len(results) == 1
            assert results[0]["url"] == "https://example.com"
            mock_post.assert_called_once()

    @patch("requests.Session.post")
    def test_tavily_api_search_no_api_key(self, mock_post):
        """Test search when API key is not available."""
        api = TavilyAPI()
        results = api.search("test query")

        assert results is None
        mock_post.assert_not_called()

    @patch("requests.Session.post")
    def test_tavily_api_search_authentication_error(self, mock_post):
        """Test search with authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"TAVILY_API_KEY": "invalid_key"}):
            api = TavilyAPI()
            results = api.search("test query")

            assert results is None

    @patch("requests.Session.post")
    def test_tavily_api_search_rate_limit(self, mock_post):
        """Test search with rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limited"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"TAVILY_API_KEY": "test_key"}):
            api = TavilyAPI()
            results = api.search("test query")

            assert results is None

    @patch("requests.Session.post")
    def test_tavily_api_search_timeout(self, mock_post):
        """Test search with timeout."""
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")

        with patch.dict(os.environ, {"TAVILY_API_KEY": "test_key"}):
            api = TavilyAPI()
            results = api.search("test query")

            assert results is None

    @patch("requests.Session.post")
    def test_tavily_api_search_request_exception(self, mock_post):
        """Test search with general request exception."""
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        with patch.dict(os.environ, {"TAVILY_API_KEY": "test_key"}):
            api = TavilyAPI()
            results = api.search("test query")

            assert results is None

    @patch("requests.Session.post")
    def test_tavily_api_search_unexpected_error(self, mock_post):
        """Test search with unexpected error."""
        mock_post.side_effect = Exception("Unexpected error")

        with patch.dict(os.environ, {"TAVILY_API_KEY": "test_key"}):
            api = TavilyAPI()
            results = api.search("test query")

            assert results is None

    def test_tavily_api_search_huggingface_models_no_api_key(self):
        """Test HuggingFace model search without API key."""
        api = TavilyAPI()
        results = api.search_huggingface_models("test_model.safetensors")

        assert results == []

    @patch("requests.Session.post")
    def test_tavily_api_search_huggingface_models_success(self, mock_post):
        """Test successful HuggingFace model search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://huggingface.co/user/repo",
                    "title": "Test Model",
                    "content": "Model description"
                }
            ]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"TAVILY_API_KEY": "test_key"}):
            api = TavilyAPI()
            results = api.search_huggingface_models("test_model.safetensors")

            assert len(results) == 1
            assert results[0]["url"] == "https://huggingface.co/user/repo"
            assert "search_query" in results[0]
            assert "search_strategy" in results[0]

    @patch("requests.Session.post")
    def test_tavily_api_search_huggingface_models_multiple_queries(self, mock_post):
        """Test HuggingFace model search with multiple query strategies."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"TAVILY_API_KEY": "test_key"}):
            api = TavilyAPI()
            results = api.search_huggingface_models("test_model.safetensors")

            # Should try multiple queries
            assert mock_post.call_count == 3  # Three different query strategies

    def test_tavily_api_search_model_repositories_no_api_key(self):
        """Test model repository search without API key."""
        api = TavilyAPI()
        results = api.search_model_repositories("test_model.safetensors")

        assert results == []

    @patch("requests.Session.post")
    def test_tavily_api_search_model_repositories_success(self, mock_post):
        """Test successful model repository search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://github.com/user/repo",
                    "title": "Test Repo",
                    "content": "Repository description"
                }
            ]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"TAVILY_API_KEY": "test_key"}):
            api = TavilyAPI()
            results = api.search_model_repositories("test_model.safetensors")

            assert len(results) == 1
            assert results[0]["url"] == "https://github.com/user/repo"

    def test_tavily_api_determine_search_strategy(self):
        """Test search strategy determination."""
        api = TavilyAPI()

        # Test RIFE pattern
        assert api._determine_search_strategy("rife49.pth") == "rife_specific"

        # Test SAM pattern
        assert api._determine_search_strategy("sam_vit_b.pth") == "sam_specific"

        # Test upscaler pattern
        assert api._determine_search_strategy("4xNMKDSuperscale.pth") == "upscaler_specific"

        # Test ControlNet pattern
        assert api._determine_search_strategy("controlnet_canny.pth") == "controlnet_specific"

        # Test general pattern
        assert api._determine_search_strategy("some_model.pth") == "general_search"


class TestEnhancedCivitaiSearch:
    """Test enhanced CivitaiSearch features."""

    def test_civitai_search_filename_validation_invalid(self):
        """Test filename validation with invalid filename."""
        search = CivitaiSearch("test_key")

        # Test with malformed filename
        result = search.search({"filename": "<script>alert('xss')</script>", "type": "checkpoints"})

        assert result.status == "INVALID_FILENAME"
        assert "malformed" in result.error_message.lower()

    def test_civitai_search_filename_validation_valid(self):
        """Test filename validation with valid filename."""
        search = CivitaiSearch("test_key")

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"items": []}
            mock_get.return_value = mock_response

            result = search.search({"filename": "valid_model.safetensors", "type": "checkpoints"})

            # Should proceed to API search, not return INVALID_FILENAME
            assert result.status != "INVALID_FILENAME"

    @patch("requests.get")
    def test_civitai_search_direct_id_backend_success(self, mock_get):
        """Test DirectIDBackend integration success."""
        search = CivitaiSearch("test_key")

        # Mock DirectIDBackend lookup
        with patch("comfyfixersmart.search.DirectIDBackend") as mock_backend_class:
            mock_backend = Mock()
            mock_backend.lookup_by_name.return_value = SearchResult(
                status="FOUND",
                filename="test_model.safetensors",
                source="civitai",
                civitai_id=12345,
                civitai_name="Test Model"
            )
            mock_backend_class.return_value = mock_backend

            result = search.search({"filename": "test_model.safetensors", "type": "checkpoints"})

            assert result.status == "FOUND"
            assert result.civitai_id == 12345
            mock_backend.lookup_by_name.assert_called_once_with("test_model")

    @patch("requests.get")
    def test_civitai_search_direct_id_backend_not_found(self, mock_get):
        """Test DirectIDBackend integration when not found."""
        search = CivitaiSearch("test_key")

        # Mock DirectIDBackend lookup returning None
        with patch("comfyfixersmart.search.DirectIDBackend") as mock_backend_class:
            mock_backend = Mock()
            mock_backend.lookup_by_name.return_value = None
            mock_backend_class.return_value = mock_backend

            # Mock API response for fallback
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"items": []}
            mock_get.return_value = mock_response

            result = search.search({"filename": "test_model.safetensors", "type": "checkpoints"})

            # Should fall back to API search
            assert result.status == "NOT_FOUND"
            mock_backend.lookup_by_name.assert_called_once()

    @patch("requests.get")
    def test_civitai_search_hash_fallback_success(self, mock_get):
        """Test hash-based fallback success."""
        search = CivitaiSearch("test_key")

        # Mock file existence and hash calculation
        with patch("os.path.exists", return_value=True), \
             patch.object(search, "_calculate_file_hash", return_value="test_hash"), \
             patch.object(search, "search_by_hash") as mock_hash_search:

            mock_hash_search.return_value = SearchResult(
                status="FOUND",
                filename="test_model.safetensors",
                source="civitai",
                civitai_id=12345
            )

            # Mock API responses that return no results
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"items": []}
            mock_get.return_value = mock_response

            result = search.search({
                "filename": "test_model.safetensors",
                "type": "checkpoints",
                "local_path": "/path/to/model.safetensors"
            })

            assert result.status == "FOUND"
            assert result.civitai_id == 12345
            mock_hash_search.assert_called_once()

    @patch("requests.get")
    def test_civitai_search_hash_fallback_file_not_found(self, mock_get):
        """Test hash fallback when local file doesn't exist."""
        search = CivitaiSearch("test_key")

        with patch("os.path.exists", return_value=False):
            # Mock API responses that return no results
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"items": []}
            mock_get.return_value = mock_response

            result = search.search({
                "filename": "test_model.safetensors",
                "type": "checkpoints",
                "local_path": "/nonexistent/model.safetensors"
            })

            assert result.status == "NOT_FOUND"
            # Should not attempt hash search

    def test_civitai_search_calculate_file_hash_success(self, tmp_path):
        """Test SHA256 hash calculation success."""
        search = CivitaiSearch("test_key")

        # Create test file
        test_file = tmp_path / "test_model.safetensors"
        test_content = b"test model data"
        test_file.write_bytes(test_content)

        hash_result = search._calculate_file_hash(str(test_file))

        assert hash_result is not None
        assert len(hash_result) == 64  # SHA256 hex length

    def test_civitai_search_calculate_file_hash_file_not_found(self):
        """Test hash calculation when file doesn't exist."""
        search = CivitaiSearch("test_key")

        hash_result = search._calculate_file_hash("/nonexistent/file.safetensors")

        assert hash_result is None

    @patch("requests.get")
    def test_civitai_search_by_hash_success(self, mock_get):
        """Test hash-based search success."""
        search = CivitaiSearch("test_key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "modelId": 12345,
            "id": 67890,
            "model": {"name": "Test Model", "type": "Checkpoint"},
            "name": "Version 1.0",
            "files": [{"name": "test_model.safetensors"}]
        }
        mock_get.return_value = mock_response

        result = search.search_by_hash("/path/to/model.safetensors", "test_model.safetensors")

        assert result.status == "FOUND"
        assert result.civitai_id == 12345
        assert result.version_id == 67890
        assert result.civitai_name == "Test Model"
        assert result.confidence == "exact"

    @patch("requests.get")
    def test_civitai_search_by_hash_not_found(self, mock_get):
        """Test hash-based search when model not found."""
        search = CivitaiSearch("test_key")

        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = search.search_by_hash("/path/to/model.safetensors", "test_model.safetensors")

        assert result is None

    def test_civitai_search_try_hash_fallback_no_local_path(self):
        """Test hash fallback when no local path provided."""
        search = CivitaiSearch("test_key")

        result = search._try_hash_fallback({"filename": "test_model.safetensors"})

        assert result is None

    def test_civitai_search_try_hash_fallback_file_too_small(self, tmp_path):
        """Test hash fallback with file too small."""
        search = CivitaiSearch("test_key")

        # Create small test file
        small_file = tmp_path / "small.safetensors"
        small_file.write_bytes(b"small")  # Less than 1MB

        with patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=1024):  # Less than 1MB

            result = search._try_hash_fallback({
                "filename": "small.safetensors",
                "local_path": str(small_file)
            })

            assert result is None


class TestQwenSearchPatternRecognition:
    """Test QwenSearch pattern recognition features."""

    def test_qwen_search_pattern_recognition_disabled(self):
        """Test QwenSearch with pattern recognition disabled."""
        search = QwenSearch()
        search.enable_pattern_recognition = False

        result = search.search({"filename": "rife49.pth", "type": "checkpoints"})

        assert result.status == "NOT_FOUND"
        # Should not skip Civitai search when pattern recognition is disabled

    def test_qwen_search_detect_hf_pattern_rife(self):
        """Test HF pattern detection for RIFE models."""
        search = QwenSearch()

        pattern = search._detect_hf_pattern("rife49.pth")
        assert pattern == "rife_patterns"

    def test_qwen_search_detect_hf_pattern_sam(self):
        """Test HF pattern detection for SAM models."""
        search = QwenSearch()

        pattern = search._detect_hf_pattern("sam_vit_b.pth")
        assert pattern == "sam_patterns"

    def test_qwen_search_detect_hf_pattern_controlnet(self):
        """Test HF pattern detection for ControlNet models."""
        search = QwenSearch()

        pattern = search._detect_hf_pattern("controlnet_canny.pth")
        assert pattern == "controlnet_patterns"

    def test_qwen_search_detect_hf_pattern_upscaler(self):
        """Test HF pattern detection for upscaler models."""
        search = QwenSearch()

        pattern = search._detect_hf_pattern("4xNMKDSuperscale.pth")
        assert pattern == "upscaler_patterns"

    def test_qwen_search_detect_hf_pattern_clip(self):
        """Test HF pattern detection for CLIP models."""
        search = QwenSearch()

        pattern = search._detect_hf_pattern("clip_text_encoder.pth")
        assert pattern == "clip_patterns"

    def test_qwen_search_detect_hf_pattern_vae(self):
        """Test HF pattern detection for VAE models."""
        search = QwenSearch()

        pattern = search._detect_hf_pattern("vae_ft_mse_840000.pt")
        assert pattern == "vae_patterns"

    def test_qwen_search_detect_hf_prefix_facebook(self):
        """Test HF prefix detection for Facebook models."""
        search = QwenSearch()

        pattern = search._detect_hf_pattern("facebook_sam_vit_b.pth")
        assert pattern == "hf_prefix_match"

    def test_qwen_search_detect_hf_prefix_microsoft(self):
        """Test HF prefix detection for Microsoft models."""
        search = QwenSearch()

        pattern = search._detect_hf_pattern("microsoft_dinov2_base.pth")
        assert pattern == "hf_prefix_match"

    def test_qwen_search_detect_no_pattern(self):
        """Test pattern detection for non-HF model."""
        search = QwenSearch()

        pattern = search._detect_hf_pattern("some_random_model.safetensors")
        assert pattern is None

    def test_qwen_search_should_skip_civitai_hf_model(self):
        """Test Civitai skip decision for likely HF model."""
        search = QwenSearch()

        should_skip, reason = search._should_skip_civitai("rife49.pth", "checkpoints")

        assert should_skip is True
        assert "Pattern match: rife_patterns" in reason

    def test_qwen_search_should_not_skip_civitai_non_hf_model(self):
        """Test Civitai skip decision for non-HF model."""
        search = QwenSearch()

        should_skip, reason = search._should_skip_civitai("some_model.safetensors", "checkpoints")

        assert should_skip is False
        assert "No HF patterns detected" in reason

    def test_qwen_search_should_not_skip_civitai_disabled_recognition(self):
        """Test Civitai skip decision when pattern recognition is disabled."""
        search = QwenSearch()
        search.enable_pattern_recognition = False

        should_skip, reason = search._should_skip_civitai("rife49.pth", "checkpoints")

        assert should_skip is False
        assert "Pattern recognition disabled" in reason

    def test_qwen_search_is_likely_hf_model_by_type_checkpoint(self):
        """Test HF likelihood detection for checkpoint models."""
        search = QwenSearch()

        is_likely, reason = search._is_likely_hf_model("some_model.safetensors", "checkpoints")

        # Checkpoints are commonly on HF, so should be likely
        assert is_likely is True

    def test_qwen_search_is_likely_hf_model_by_type_lora(self):
        """Test HF likelihood detection for LoRA models."""
        search = QwenSearch()

        is_likely, reason = search._is_likely_hf_model("some_lora.safetensors", "loras")

        # LoRAs are less commonly on HF, so should not be likely
        assert is_likely is False

    def test_qwen_search_is_likely_hf_model_by_filename_patterns(self):
        """Test HF likelihood detection by filename patterns."""
        search = QwenSearch()

        test_cases = [
            ("stabilityai_sd_turbo.safetensors", True, "Contains HF repository identifiers"),
            ("diffusers_model.bin", True, "Contains HF repository identifiers"),
            ("random_model.safetensors", False, "No HF patterns detected"),
        ]

        for filename, expected_likely, expected_reason in test_cases:
            is_likely, reason = search._is_likely_hf_model(filename, "checkpoints")
            assert is_likely == expected_likely
            assert expected_reason in reason


class TestHuggingFaceSearchWebVerification:
    """Test HuggingFaceSearch web search and verification features."""

    def test_huggingface_search_initialization(self):
        """Test HuggingFaceSearch initialization."""
        search = HuggingFaceSearch()

        assert search.get_name() == "huggingface"
        assert hasattr(search, 'tavily_api_key')
        assert hasattr(search, 'hf_token')

    @patch("requests.post")
    def test_huggingface_search_web_search_success(self, mock_post):
        """Test web search functionality."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://huggingface.co/user/repo",
                    "title": "Test Model",
                    "content": "Model description"
                }
            ]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"TAVILY_API_KEY": "test_key"}):
            search = HuggingFaceSearch()
            results = search._web_search_huggingface("test_model.safetensors")

            assert len(results) == 1
            assert results[0]["url"] == "https://huggingface.co/user/repo"

    @patch("requests.post")
    def test_huggingface_search_web_search_no_api_key(self, mock_post):
        """Test web search without API key."""
        search = HuggingFaceSearch()
        results = search._web_search_huggingface("test_model.safetensors")

        assert results == []
        mock_post.assert_not_called()

    def test_huggingface_search_extract_repos_from_results(self):
        """Test repository extraction from search results."""
        search = HuggingFaceSearch()

        search_results = [
            {
                "url": "https://huggingface.co/user/repo/tree/main/models",
                "title": "Test Repo",
                "content": "Repository content"
            },
            {
                "url": "https://github.com/user/repo",
                "title": "GitHub Repo",
                "content": "GitHub content"
            },
            {
                "url": "https://example.com/other",
                "title": "Other Site",
                "content": "Other content"
            }
        ]

        repos = search._extract_repos_from_search_results(search_results, "test_model.safetensors")

        assert len(repos) == 2  # Should extract both HF and GitHub repos
        assert repos[0] == "user/repo"  # HF repo
        assert repos[1] == "user/repo"  # GitHub repo

    def test_huggingface_search_calculate_repo_score_exact_match(self):
        """Test repository score calculation with exact match."""
        search = HuggingFaceSearch()

        score = search._calculate_repo_score("user/test_model", "test_model")

        assert score == 100  # Exact match gets highest score

    def test_huggingface_search_calculate_repo_score_contains(self):
        """Test repository score calculation with contains match."""
        search = HuggingFaceSearch()

        score = search._calculate_repo_score("user/test_model_repo", "test_model")

        assert score == 80  # Contains match gets good score

    def test_huggingface_search_calculate_repo_score_partial(self):
        """Test repository score calculation with partial match."""
        search = HuggingFaceSearch()

        score = search._calculate_repo_score("user/my_model", "test_model")

        assert score == 60  # Partial word match

    def test_huggingface_search_calculate_repo_score_no_match(self):
        """Test repository score calculation with no match."""
        search = HuggingFaceSearch()

        score = search._calculate_repo_score("user/unrelated", "test_model")

        assert score == 30  # Base score for valid repo format

    @patch("huggingface_hub.HfApi")
    def test_huggingface_search_verify_repository_success(self, mock_hf_api_class):
        """Test repository verification success."""
        mock_api = Mock()
        mock_repo_info = Mock()
        mock_repo_info.id = "user/repo"
        mock_api.repo_info.return_value = mock_repo_info
        mock_api.list_repo_files.return_value = [
            Mock(path="models/test_model.safetensors", size=1000000)
        ]
        mock_hf_api_class.return_value = mock_api

        with patch("comfyfixersmart.search.hf_hub_url", return_value="https://hf.co/download"):
            search = HuggingFaceSearch()
            result = search._verify_repository_and_find_file("user/repo", "test_model.safetensors")

            assert result is not None
            assert result.status == "FOUND"
            assert result.filename == "test_model.safetensors"
            assert result.source == "huggingface"

    @patch("huggingface_hub.HfApi")
    def test_huggingface_search_verify_repository_not_found(self, mock_hf_api_class):
        """Test repository verification when repo doesn't exist."""
        from huggingface_hub import RepositoryNotFoundError

        mock_api = Mock()
        mock_api.repo_info.side_effect = RepositoryNotFoundError("Repo not found")
        mock_hf_api_class.return_value = mock_api

        search = HuggingFaceSearch()
        result = search._verify_repository_and_find_file("user/nonexistent", "test_model.safetensors")

        assert result is None

    def test_huggingface_search_is_matching_model_file_exact(self):
        """Test model file matching with exact name."""
        search = HuggingFaceSearch()

        is_match = search._is_matching_model_file("test_model.safetensors", "test_model")

        assert is_match is True

    def test_huggingface_search_is_matching_model_file_extension_only(self):
        """Test model file matching with valid extension only."""
        search = HuggingFaceSearch()

        is_match = search._is_matching_model_file("other_model.safetensors", "test_model")

        assert is_match is False  # Different base name

    def test_huggingface_search_is_matching_model_file_contains(self):
        """Test model file matching with contains logic."""
        search = HuggingFaceSearch()

        is_match = search._is_matching_model_file("my_test_model.ckpt", "test_model")

        assert is_match is True  # Contains match

    def test_huggingface_search_is_matching_model_file_invalid_extension(self):
        """Test model file matching with invalid extension."""
        search = HuggingFaceSearch()

        is_match = search._is_matching_model_file("test_model.txt", "test_model")

        assert is_match is False  # Invalid extension

    def test_huggingface_search_select_best_file_exact_match(self):
        """Test best file selection with exact match."""
        search = HuggingFaceSearch()

        files = [
            ("models/test_model.safetensors", 1000000),
            ("models/other_model.ckpt", 2000000),
        ]

        best_file = search._select_best_file(files, "test_model.safetensors")

        assert best_file == ("models/test_model.safetensors", 1000000)

    def test_huggingface_search_select_best_file_largest(self):
        """Test best file selection by size when no exact match."""
        search = HuggingFaceSearch()

        files = [
            ("models/other1.ckpt", 1000000),
            ("models/other2.safetensors", 3000000),  # Largest
            ("models/other3.pt", 2000000),
        ]

        best_file = search._select_best_file(files, "test_model.safetensors")

        assert best_file == ("models/other2.safetensors", 3000000)

    def test_huggingface_search_infer_model_type_checkpoint(self):
        """Test model type inference for checkpoint."""
        search = HuggingFaceSearch()

        model_type = search._infer_model_type_from_filename("checkpoint.safetensors")

        assert model_type == "checkpoints"

    def test_huggingface_search_infer_model_type_lora(self):
        """Test model type inference for LoRA."""
        search = HuggingFaceSearch()

        model_type = search._infer_model_type_from_filename("lora_model.safetensors")

        assert model_type == "loras"

    def test_huggingface_search_infer_model_type_controlnet(self):
        """Test model type inference for ControlNet."""
        search = HuggingFaceSearch()

        model_type = search._infer_model_type_from_filename("controlnet_canny.safetensors")

        assert model_type == "controlnet"

    def test_huggingface_search_infer_model_type_upscaler(self):
        """Test model type inference for upscaler."""
        search = HuggingFaceSearch()

        model_type = search._infer_model_type_from_filename("4x_upscaler.safetensors")

        assert model_type == "upscale_models"

    def test_huggingface_search_infer_model_type_embedding(self):
        """Test model type inference for embedding."""
        search = HuggingFaceSearch()

        model_type = search._infer_model_type_from_filename("textual_embedding.safetensors")

        assert model_type == "embeddings"


class TestFilenameValidation:
    """Test enhanced filename validation functionality."""

    def test_validate_and_sanitize_filename_valid(self):
        """Test validation and sanitization of valid filename."""
        is_valid, sanitized, error = validate_and_sanitize_filename("valid_model.safetensors")

        assert is_valid is True
        assert sanitized == "valid_model.safetensors"
        assert error is None

    def test_validate_and_sanitize_filename_malformed_script(self):
        """Test validation of malformed filename with script tags."""
        is_valid, sanitized, error = validate_and_sanitize_filename("<script>alert('xss')</script>")

        assert is_valid is False
        assert sanitized == ""
        assert "malformed" in error.lower()

    def test_validate_and_sanitize_filename_path_traversal(self):
        """Test validation of filename with path traversal."""
        is_valid, sanitized, error = validate_and_sanitize_filename("../../../etc/passwd")

        assert is_valid is False
        assert sanitized == ""
        assert "path traversal" in error.lower()

    def test_validate_and_sanitize_filename_null_bytes(self):
        """Test validation of filename with null bytes."""
        is_valid, sanitized, error = validate_and_sanitize_filename("model\x00.safetensors")

        assert is_valid is False
        assert sanitized == ""
        assert "null bytes" in error.lower()

    def test_validate_and_sanitize_filename_too_long(self):
        """Test validation of filename that is too long."""
        long_name = "a" * 300 + ".safetensors"
        is_valid, sanitized, error = validate_and_sanitize_filename(long_name)

        assert is_valid is False
        assert sanitized == ""
        assert "too long" in error.lower()

    def test_validate_and_sanitize_filename_invalid_chars(self):
        """Test validation of filename with invalid characters."""
        is_valid, sanitized, error = validate_and_sanitize_filename("model<>:|?*.safetensors")

        assert is_valid is False
        assert sanitized == ""
        assert "invalid characters" in error.lower()

    def test_validate_and_sanitize_filename_empty(self):
        """Test validation of empty filename."""
        is_valid, sanitized, error = validate_and_sanitize_filename("")

        assert is_valid is False
        assert sanitized == ""
        assert "empty" in error.lower()

    def test_validate_and_sanitize_filename_whitespace_only(self):
        """Test validation of whitespace-only filename."""
        is_valid, sanitized, error = validate_and_sanitize_filename("   \t\n   ")

        assert is_valid is False
        assert sanitized == ""
        assert "empty" in error.lower()

    def test_validate_and_sanitize_filename_suspicious_patterns(self):
        """Test validation of filename with suspicious patterns."""
        suspicious_names = [
            "model.exe",
            "model.bat",
            "model.cmd",
            "model.sh",
            "model.dll",
            "model.so",
        ]

        for name in suspicious_names:
            is_valid, sanitized, error = validate_and_sanitize_filename(name)
            assert is_valid is False
            assert "suspicious" in error.lower()

    def test_validate_and_sanitize_filename_normalization(self):
        """Test filename normalization during sanitization."""
        # Test with various separators and case
        is_valid, sanitized, error = validate_and_sanitize_filename("My.Model.Name.SAFETENSORS")

        assert is_valid is True
        assert sanitized == "My.Model.Name.SAFETENSORS"  # Should preserve case and dots