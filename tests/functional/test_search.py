"""
Functional tests for the search module.

Tests search backends, model search coordination, caching, and API interactions
with comprehensive mocking for external dependencies.
"""

import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import requests

from comfyfixersmart.search import (
    SearchResult, SearchBackend, CivitaiSearch, QwenSearch,
    HuggingFaceSearch, ModelSearch, search_civitai
)


class TestSearchResult:
    """Test SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating a SearchResult instance."""
        result = SearchResult(
            status="FOUND",
            filename="model.safetensors",
            source="civitai",
            civitai_id=12345,
            download_url="https://example.com/download",
            confidence="exact"
        )

        assert result.status == "FOUND"
        assert result.filename == "model.safetensors"
        assert result.source == "civitai"
        assert result.civitai_id == 12345
        assert result.download_url == "https://example.com/download"
        assert result.confidence == "exact"

    def test_search_result_defaults(self):
        """Test SearchResult default values."""
        result = SearchResult(status="NOT_FOUND", filename="model.safetensors")

        assert result.status == "NOT_FOUND"
        assert result.filename == "model.safetensors"
        assert result.source is None
        assert result.civitai_id is None
        assert result.download_url is None
        assert result.confidence is None
        assert result.metadata is None
        assert result.error_message is None


class TestCivitaiSearch:
    """Test CivitaiSearch backend."""

    def test_civitai_search_initialization(self):
        """Test CivitaiSearch initialization."""
        search = CivitaiSearch("test_key")
        assert search.api_key == "test_key"
        assert search.base_url == "https://civitai.com/api/v1"
        assert search.get_name() == "civitai"

    @patch('comfyfixersmart.search.get_api_key')
    def test_civitai_search_default_api_key(self, mock_get_key):
        """Test CivitaiSearch uses default API key when none provided."""
        mock_get_key.return_value = "default_key"
        search = CivitaiSearch()
        assert search.api_key == "default_key"

    def test_prepare_search_query(self):
        """Test search query preparation."""
        search = CivitaiSearch("test_key")

        # Test various filename formats
        assert search._prepare_search_query("model.safetensors") == "model"
        assert search._prepare_search_query("model_v1.0.ckpt") == "model v1 0"
        assert search._prepare_search_query("complex.model.name.pth") == "complex model name"

    def test_get_type_filter(self):
        """Test type filter mapping."""
        search = CivitaiSearch("test_key")

        test_cases = [
            ("checkpoints", "Checkpoint"),
            ("loras", "LORA"),
            ("vae", "VAE"),
            ("controlnet", "Controlnet"),
            ("upscale_models", "Upscaler"),
            ("clip", "TextualInversion"),
            ("unet", "Checkpoint"),
            ("unknown", None)
        ]

        for model_type, expected in test_cases:
            assert search._get_type_filter(model_type) == expected

    @patch('requests.get')
    def test_search_success_exact_match(self, mock_get):
        """Test successful search with exact match."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "id": 12345,
                    "name": "Test Model",
                    "modelVersions": [
                        {
                            "id": 67890,
                            "name": "v1.0",
                            "files": [
                                {
                                    "name": "exact_match.safetensors",
                                    "downloadUrl": "https://civitai.com/api/download/models/67890"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response

        search = CivitaiSearch("test_key")
        result = search.search({"filename": "exact_match.safetensors", "type": "checkpoints"})

        assert result.status == "FOUND"
        assert result.filename == "exact_match.safetensors"
        assert result.source == "civitai"
        assert result.civitai_id == 12345
        assert result.civitai_name == "Test Model"
        assert result.version_id == 67890
        assert result.download_url == "https://civitai.com/api/download/models/67890"
        assert result.confidence == "exact"

    @patch('requests.get')
    def test_search_success_fuzzy_match(self, mock_get):
        """Test successful search with fuzzy match."""
        # Mock API response with no exact match
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "id": 12345,
                    "name": "Test Model",
                    "modelVersions": [
                        {
                            "id": 67890,
                            "name": "v1.0",
                            "files": [
                                {
                                    "name": "different_name.safetensors",
                                    "downloadUrl": "https://civitai.com/api/download/models/67890"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response

        search = CivitaiSearch("test_key")
        result = search.search({"filename": "target_model.safetensors", "type": "checkpoints"})

        assert result.status == "FOUND"
        assert result.filename == "target_model.safetensors"
        assert result.confidence == "fuzzy"

    @patch('requests.get')
    def test_search_not_found(self, mock_get):
        """Test search when no results found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response

        search = CivitaiSearch("test_key")
        result = search.search({"filename": "nonexistent.safetensors"})

        assert result.status == "NOT_FOUND"
        assert result.filename == "nonexistent.safetensors"

    @patch('requests.get')
    def test_search_api_error(self, mock_get):
        """Test search when API returns error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        search = CivitaiSearch("test_key")
        result = search.search({"filename": "model.safetensors"})

        assert result.status == "ERROR"
        assert "API error: 500" in result.error_message

    @patch('requests.get')
    def test_search_request_exception(self, mock_get):
        """Test search when request raises exception."""
        mock_get.side_effect = requests.RequestException("Network error")

        search = CivitaiSearch("test_key")
        result = search.search({"filename": "model.safetensors"})

        assert result.status == "ERROR"
        assert "Network error" in result.error_message

    def test_create_result_from_match(self):
        """Test creating result from API match."""
        search = CivitaiSearch("test_key")

        match = {
            "id": 12345,
            "name": "Test Model",
            "modelVersions": [
                {
                    "id": 67890,
                    "name": "v1.0"
                }
            ]
        }

        result = search._create_result_from_match(match, "model.safetensors", "exact")

        assert result.status == "FOUND"
        assert result.civitai_id == 12345
        assert result.civitai_name == "Test Model"
        assert result.version_id == 67890
        assert result.version_name == "v1.0"
        assert result.download_url == "https://civitai.com/api/download/models/67890"
        assert result.confidence == "exact"


class TestQwenSearch:
    """Test QwenSearch backend."""

    def test_qwen_search_initialization(self):
        """Test QwenSearch initialization."""
        search = QwenSearch()
        assert search.get_name() == "qwen"

    def test_qwen_search_with_temp_dir(self, tmp_path):
        """Test QwenSearch with custom temp directory."""
        temp_dir = tmp_path / "qwen_temp"
        search = QwenSearch(str(temp_dir))
        assert search.temp_dir == temp_dir
        assert temp_dir.exists()

    def test_qwen_search_currently_returns_not_found(self):
        """Test that QwenSearch currently returns NOT_FOUND (placeholder implementation)."""
        search = QwenSearch()
        result = search.search({"filename": "model.safetensors"})

        assert result.status == "NOT_FOUND"
        assert result.filename == "model.safetensors"
        assert "not implemented yet" in result.metadata["reason"]

    def test_build_qwen_prompt(self):
        """Test Qwen prompt building."""
        search = QwenSearch()
        prompt = search._build_qwen_prompt({"filename": "test_model.safetensors"})
        assert "test_model.safetensors" in prompt


class TestHuggingFaceSearch:
    """Test HuggingFaceSearch backend."""

    def test_huggingface_search_initialization(self):
        """Test HuggingFaceSearch initialization."""
        search = HuggingFaceSearch()
        assert search.get_name() == "huggingface"

    def test_huggingface_search_currently_returns_not_found(self):
        """Test that HuggingFaceSearch currently returns NOT_FOUND (placeholder implementation)."""
        search = HuggingFaceSearch()
        result = search.search({"filename": "model.safetensors"})

        assert result.status == "NOT_FOUND"
        assert result.filename == "model.safetensors"
        assert "not implemented yet" in result.metadata["reason"]


class TestModelSearch:
    """Test ModelSearch coordinator."""

    def test_model_search_initialization(self):
        """Test ModelSearch initialization."""
        search = ModelSearch()
        assert "civitai" in search.backends
        assert "qwen" in search.backends
        assert "huggingface" in search.backends
        assert search.cache_dir.exists()

    def test_model_search_with_state_manager(self, tmp_path):
        """Test ModelSearch with state manager."""
        state_manager = Mock()
        search = ModelSearch(state_manager=state_manager)
        assert search.state_manager == state_manager

    def test_model_search_with_custom_cache_dir(self, tmp_path):
        """Test ModelSearch with custom cache directory."""
        cache_dir = tmp_path / "custom_cache"
        search = ModelSearch(cache_dir=str(cache_dir))
        assert search.cache_dir == cache_dir
        assert cache_dir.exists()

    @patch('comfyfixersmart.search.CivitaiSearch.search')
    def test_search_model_found(self, mock_civitai_search):
        """Test successful model search."""
        mock_result = SearchResult(
            status="FOUND",
            filename="model.safetensors",
            source="civitai",
            download_url="https://example.com/download"
        )
        mock_civitai_search.return_value = mock_result

        search = ModelSearch()
        result = search.search_model({"filename": "model.safetensors", "type": "checkpoints"})

        assert result.status == "FOUND"
        assert result.filename == "model.safetensors"
        mock_civitai_search.assert_called_once()

    @patch('comfyfixersmart.search.CivitaiSearch.search')
    def test_search_model_not_found(self, mock_civitai_search):
        """Test model search when not found."""
        mock_civitai_search.return_value = SearchResult(
            status="NOT_FOUND",
            filename="model.safetensors"
        )

        search = ModelSearch()
        result = search.search_model({"filename": "model.safetensors"})

        assert result.status == "NOT_FOUND"

    @patch('comfyfixersmart.search.CivitaiSearch.search')
    def test_search_model_with_multiple_backends(self, mock_civitai_search):
        """Test model search with multiple backends."""
        # First backend fails, second succeeds
        mock_civitai_search.return_value = SearchResult(
            status="NOT_FOUND",
            filename="model.safetensors"
        )

        search = ModelSearch()
        result = search.search_model(
            {"filename": "model.safetensors"},
            backends=["civitai", "qwen"]
        )

        # Should try Civitai first, then Qwen
        assert mock_civitai_search.call_count == 2

    @patch('comfyfixersmart.search.CivitaiSearch.search')
    def test_search_model_uses_cache(self, mock_civitai_search, tmp_path):
        """Test that search uses cached results."""
        # Create a cached result
        cache_dir = tmp_path / "cache"
        search = ModelSearch(cache_dir=str(cache_dir))

        cached_result = SearchResult(
            status="FOUND",
            filename="cached_model.safetensors",
            source="civitai"
        )

        # Manually create cache file
        cache_file = cache_dir / "cached_model.safetensors.json"
        with open(cache_file, 'w') as f:
            json.dump(cached_result.__dict__, f)

        # Search should return cached result without calling backend
        result = search.search_model({"filename": "cached_model.safetensors"})

        assert result.status == "FOUND"
        assert result.filename == "cached_model.safetensors"
        mock_civitai_search.assert_not_called()

    @patch('comfyfixersmart.search.CivitaiSearch.search')
    def test_search_model_caches_results(self, mock_civitai_search, tmp_path):
        """Test that search caches successful results."""
        mock_civitai_search.return_value = SearchResult(
            status="FOUND",
            filename="model.safetensors",
            source="civitai"
        )

        cache_dir = tmp_path / "cache"
        search = ModelSearch(cache_dir=str(cache_dir))

        # Perform search
        result = search.search_model({"filename": "model.safetensors"})

        # Check that result was cached
        cache_file = cache_dir / "model.safetensors.json"
        assert cache_file.exists()

        with open(cache_file, 'r') as f:
            cached_data = json.load(f)

        assert cached_data["status"] == "FOUND"
        assert cached_data["filename"] == "model.safetensors"

    def test_search_multiple_models(self):
        """Test searching multiple models."""
        search = ModelSearch()

        models = [
            {"filename": "model1.safetensors", "type": "checkpoints"},
            {"filename": "model2.safetensors", "type": "loras"}
        ]

        # Mock the search_model method
        with patch.object(search, 'search_model') as mock_search:
            mock_search.side_effect = [
                SearchResult(status="FOUND", filename="model1.safetensors"),
                SearchResult(status="NOT_FOUND", filename="model2.safetensors")
            ]

            results = search.search_multiple_models(models)

            assert len(results) == 2
            assert results[0].status == "FOUND"
            assert results[1].status == "NOT_FOUND"
            assert mock_search.call_count == 2

    def test_clear_cache_all(self, tmp_path):
        """Test clearing all cache."""
        cache_dir = tmp_path / "cache"
        search = ModelSearch(cache_dir=str(cache_dir))

        # Create some cache files
        (cache_dir / "model1.json").write_text("{}")
        (cache_dir / "model2.json").write_text("{}")

        search.clear_cache()

        assert not (cache_dir / "model1.json").exists()
        assert not (cache_dir / "model2.json").exists()

    def test_clear_cache_specific(self, tmp_path):
        """Test clearing specific cache entry."""
        cache_dir = tmp_path / "cache"
        search = ModelSearch(cache_dir=str(cache_dir))

        # Create cache files
        (cache_dir / "model1.json").write_text("{}")
        (cache_dir / "model2.json").write_text("{}")

        search.clear_cache("model1")

        assert not (cache_dir / "model1.json").exists()
        assert (cache_dir / "model2.json").exists()

    def test_get_search_stats(self, tmp_path):
        """Test getting search statistics."""
        cache_dir = tmp_path / "cache"
        search = ModelSearch(cache_dir=str(cache_dir))

        # Create some cache files
        (cache_dir / "model1.json").write_text("{}")
        (cache_dir / "model2.json").write_text("{}")

        stats = search.get_search_stats()

        assert stats["cached_results"] == 2
        assert stats["cache_dir"] == str(cache_dir)
        assert "civitai" in stats["backends_available"]
        assert "qwen" in stats["backends_available"]
        assert "huggingface" in stats["backends_available"]


class TestConvenienceFunctions:
    """Test backward compatibility convenience functions."""

    @patch('comfyfixersmart.search.CivitaiSearch.search')
    def test_search_civitai_function(self, mock_search):
        """Test search_civitai convenience function."""
        mock_search.return_value = SearchResult(
            status="FOUND",
            filename="model.safetensors"
        )

        result = search_civitai({"filename": "model.safetensors"})

        assert result.status == "FOUND"
        mock_search.assert_called_once()


class TestSearchIntegration:
    """Integration tests for search functionality."""

    @patch('requests.get')
    def test_full_search_workflow(self, mock_get):
        """Test complete search workflow with caching and state management."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "id": 12345,
                    "name": "Test Model",
                    "modelVersions": [
                        {
                            "id": 67890,
                            "name": "v1.0",
                            "files": [
                                {
                                    "name": "test_model.safetensors",
                                    "downloadUrl": "https://civitai.com/api/download/models/67890"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response

        # Create search coordinator with state manager
        state_manager = Mock()
        search = ModelSearch(state_manager=state_manager)

        model_info = {
            "filename": "test_model.safetensors",
            "type": "checkpoints",
            "node_type": "CheckpointLoaderSimple"
        }

        # Perform search
        result = search.search_model(model_info)

        # Verify result
        assert result.status == "FOUND"
        assert result.filename == "test_model.safetensors"
        assert result.source == "civitai"
        assert result.civitai_id == 12345

        # Verify state manager was called
        state_manager.mark_download_attempted.assert_called_once()

        # Verify result was cached
        cached_result = search._get_cached_result("test_model.safetensors")
        assert cached_result is not None
        assert cached_result.status == "FOUND"

        # Second search should use cache
        mock_get.reset_mock()
        result2 = search.search_model(model_info)
        assert result2.status == "FOUND"
        # API should not be called again
        mock_get.assert_not_called()

    def test_search_error_handling(self):
        """Test search error handling across backends."""
        search = ModelSearch()

        # Test with invalid backend
        result = search.search_model(
            {"filename": "model.safetensors"},
            backends=["invalid_backend"]
        )

        assert result.status == "NOT_FOUND"
        assert "backends_tried" in result.metadata

    @patch('time.sleep')
    def test_search_multiple_models_delay(self, mock_sleep):
        """Test that searching multiple models includes delays."""
        search = ModelSearch()

        models = [
            {"filename": "model1.safetensors"},
            {"filename": "model2.safetensors"}
        ]

        with patch.object(search, 'search_model') as mock_search:
            mock_search.return_value = SearchResult(status="NOT_FOUND", filename="dummy")

            search.search_multiple_models(models)

            # Should have delay between searches
            mock_sleep.assert_called_with(0.5)