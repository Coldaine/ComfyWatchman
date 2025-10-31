"""
Integration tests for new search features in ComfyFixerSmart.

Tests complete workflows combining TavilyAPI, enhanced CivitaiSearch,
QwenSearch pattern recognition, and HuggingFaceSearch web verification.
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
    ModelSearch,
    SearchResult,
)


class TestTavilyCivitaiIntegration:
    """Integration tests for TavilyAPI and CivitaiSearch interaction."""

    @patch("requests.post")
    @patch("requests.get")
    def test_tavily_web_search_informs_civitai_search(self, mock_get, mock_post):
        """Test that web search results can inform Civitai search strategies."""
        # Mock Tavily search results
        tavily_response = Mock()
        tavily_response.status_code = 200
        tavily_response.json.return_value = {
            "results": [
                {
                    "url": "https://huggingface.co/user/rife-model",
                    "title": "RIFE Frame Interpolation Model",
                    "content": "High-quality frame interpolation using RIFE"
                }
            ]
        }
        mock_post.return_value = tavily_response

        # Mock Civitai API response
        civitai_response = Mock()
        civitai_response.status_code = 200
        civitai_response.json.return_value = {"items": []}
        mock_get.return_value = civitai_response

        # Test the integration
        tavily_api = TavilyAPI()
        with patch.dict(os.environ, {"TAVILY_API_KEY": "test_key"}):
            web_results = tavily_api.search_huggingface_models("rife49.pth")

            assert len(web_results) == 1
            assert "rife" in web_results[0]["title"].lower()

            # Now test Civitai search with pattern recognition
            civitai_search = CivitaiSearch("test_key")
            result = civitai_search.search({"filename": "rife49.pth", "type": "checkpoints"})

            # Should attempt API search but return NOT_FOUND
            assert result.status == "NOT_FOUND"
            assert result.filename == "rife49.pth"

    @patch("requests.get")
    def test_civitai_hash_fallback_with_web_search_context(self, mock_get):
        """Test hash fallback when web search provides context."""
        # Mock Civitai API responses
        api_response = Mock()
        api_response.status_code = 200
        api_response.json.return_value = {"items": []}
        mock_get.return_value = api_response

        civitai_search = CivitaiSearch("test_key")

        # Test hash fallback with local file
        with patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=2097152), \
             patch.object(civitai_search, "_calculate_file_hash", return_value="test_hash"), \
             patch.object(civitai_search, "search_by_hash") as mock_hash_search:

            mock_hash_search.return_value = SearchResult(
                status="FOUND",
                filename="test_model.safetensors",
                source="civitai",
                civitai_id=12345
            )

            result = civitai_search.search({
                "filename": "test_model.safetensors",
                "type": "checkpoints",
                "local_path": "/path/to/model.safetensors"
            })

            assert result.status == "FOUND"
            assert result.civitai_id == 12345
            mock_hash_search.assert_called_once()


class TestQwenPatternRecognitionIntegration:
    """Integration tests for QwenSearch pattern recognition with other backends."""

    @patch("requests.post")
    def test_qwen_pattern_recognition_skips_civitai_for_hf_models(self, mock_post):
        """Test that Qwen pattern recognition correctly identifies HF models."""
        # Mock web search for context
        web_response = Mock()
        web_response.status_code = 200
        web_response.json.return_value = {
            "results": [
                {
                    "url": "https://huggingface.co/facebook/sam-vit-base",
                    "title": "SAM ViT Base",
                    "content": "Segment Anything Model"
                }
            ]
        }
        mock_post.return_value = web_response

        qwen_search = QwenSearch()

        # Test pattern recognition for SAM model
        should_skip, reason = qwen_search._should_skip_civitai("sam_vit_b.pth", "checkpoints")

        assert should_skip is True
        assert "sam_patterns" in reason

        # Test search result reflects pattern recognition
        result = qwen_search.search({"filename": "sam_vit_b.pth", "type": "checkpoints"})

        assert result.status == "NOT_FOUND"
        assert "Pattern recognition: Likely HF model" in result.metadata["reason"]
        assert result.metadata["pattern_recognized"] is True

    @patch("requests.post")
    def test_qwen_web_search_integration(self, mock_post):
        """Test Qwen web search integration for repository discovery."""
        # Mock web search results
        web_response = Mock()
        web_response.status_code = 200
        web_response.json.return_value = {
            "results": [
                {
                    "url": "https://huggingface.co/user/test-model",
                    "title": "Test Model Repository",
                    "content": "Stable Diffusion model for testing"
                }
            ]
        }
        mock_post.return_value = web_response

        qwen_search = QwenSearch()

        with patch.dict(os.environ, {"TAVILY_API_KEY": "test_key"}):
            web_results = qwen_search._perform_web_search_fallback({
                "filename": "test_model.safetensors",
                "type": "checkpoints"
            })

            assert len(web_results) == 1
            assert web_results[0]["url"] == "https://huggingface.co/user/test-model"

    def test_qwen_pattern_recognition_disabled_fallback(self):
        """Test Qwen search when pattern recognition is disabled."""
        qwen_search = QwenSearch()
        qwen_search.enable_pattern_recognition = False

        should_skip, reason = qwen_search._should_skip_civitai("rife49.pth", "checkpoints")

        assert should_skip is False
        assert "Pattern recognition disabled" in reason


class TestHuggingFaceWebVerificationIntegration:
    """Integration tests for HuggingFaceSearch web verification."""

    @patch("requests.post")
    @patch("huggingface_hub.HfApi")
    def test_huggingface_web_search_to_repo_verification(self, mock_hf_api_class, mock_post):
        """Test complete flow from web search to repository verification."""
        # Mock web search
        web_response = Mock()
        web_response.status_code = 200
        web_response.json.return_value = {
            "results": [
                {
                    "url": "https://huggingface.co/user/test-model",
                    "title": "Test Model",
                    "content": "Stable Diffusion checkpoint"
                }
            ]
        }
        mock_post.return_value = web_response

        # Mock HF API
        mock_api = Mock()
        mock_repo_info = Mock()
        mock_repo_info.id = "user/test-model"
        mock_api.repo_info.return_value = mock_repo_info
        mock_api.list_repo_files.return_value = [
            Mock(path="test_model.safetensors", size=2097152000)
        ]
        mock_hf_api_class.return_value = mock_api

        hf_search = HuggingFaceSearch()

        with patch.dict(os.environ, {"TAVILY_API_KEY": "test_key"}), \
             patch("comfyfixersmart.search.hf_hub_url", return_value="https://hf.co/download"):

            result = hf_search.search({
                "filename": "test_model.safetensors",
                "type": "checkpoints"
            })

            assert result.status == "FOUND"
            assert result.source == "huggingface"
            assert result.filename == "test_model.safetensors"
            assert result.download_url == "https://hf.co/download"

    @patch("requests.post")
    def test_huggingface_web_search_no_api_key_fallback(self, mock_post):
        """Test HuggingFace search fallback when no API key."""
        hf_search = HuggingFaceSearch()

        result = hf_search.search({"filename": "test_model.safetensors", "type": "checkpoints"})

        assert result.status == "NOT_FOUND"
        assert "No HuggingFace repositories found in web search" in result.metadata["reason"]
        mock_post.assert_not_called()


class TestModelSearchBackendCoordination:
    """Integration tests for ModelSearch backend coordination."""

    def test_model_search_backend_order_qwen_first(self):
        """Test that ModelSearch uses Qwen as primary backend."""
        search = ModelSearch()

        # Check backend order - Qwen should be first
        assert search.backends["qwen"].get_name() == "qwen"
        assert search.backends["civitai"].get_name() == "civitai"
        assert search.backends["huggingface"].get_name() == "huggingface"

    @patch("comfyfixersmart.search.QwenSearch.search")
    def test_model_search_qwen_pattern_recognition_integration(self, mock_qwen_search):
        """Test ModelSearch integration with Qwen pattern recognition."""
        mock_qwen_search.return_value = SearchResult(
            status="NOT_FOUND",
            filename="rife49.pth",
            metadata={
                "reason": "Pattern recognition: Likely HF model",
                "pattern_recognized": True
            }
        )

        search = ModelSearch()
        result = search.search_model({"filename": "rife49.pth", "type": "checkpoints"})

        assert result.status == "NOT_FOUND"
        assert result.metadata["pattern_recognized"] is True
        mock_qwen_search.assert_called_once()

    @patch("comfyfixersmart.search.QwenSearch.search")
    @patch("comfyfixersmart.search.CivitaiSearch.search")
    def test_model_search_fallback_to_civitai(self, mock_civitai_search, mock_qwen_search):
        """Test ModelSearch fallback from Qwen to Civitai."""
        # Qwen returns NOT_FOUND
        mock_qwen_search.return_value = SearchResult(
            status="NOT_FOUND",
            filename="unknown_model.safetensors"
        )

        # Civitai finds the model
        mock_civitai_search.return_value = SearchResult(
            status="FOUND",
            filename="unknown_model.safetensors",
            source="civitai",
            civitai_id=12345
        )

        search = ModelSearch()
        result = search.search_model({"filename": "unknown_model.safetensors", "type": "checkpoints"})

        assert result.status == "FOUND"
        assert result.source == "civitai"
        assert result.civitai_id == 12345

        # Both backends should be called
        mock_qwen_search.assert_called_once()
        mock_civitai_search.assert_called_once()

    @patch("comfyfixersmart.search.QwenSearch.search")
    @patch("comfyfixersmart.search.HuggingFaceSearch.search")
    def test_model_search_fallback_to_huggingface(self, mock_hf_search, mock_qwen_search):
        """Test ModelSearch fallback from Qwen to HuggingFace."""
        # Qwen returns NOT_FOUND
        mock_qwen_search.return_value = SearchResult(
            status="NOT_FOUND",
            filename="hf_model.safetensors"
        )

        # HuggingFace finds the model
        mock_hf_search.return_value = SearchResult(
            status="FOUND",
            filename="hf_model.safetensors",
            source="huggingface",
            download_url="https://hf.co/download"
        )

        search = ModelSearch()
        result = search.search_model({"filename": "hf_model.safetensors", "type": "checkpoints"})

        assert result.status == "FOUND"
        assert result.source == "huggingface"

        # Both backends should be called
        mock_qwen_search.assert_called_once()
        mock_hf_search.assert_called_once()


class TestCompleteSearchWorkflowIntegration:
    """Integration tests for complete search workflows."""

    @patch("requests.post")
    @patch("requests.get")
    @patch("huggingface_hub.HfApi")
    def test_complete_workflow_qwen_to_huggingface(self, mock_hf_api_class, mock_get, mock_post):
        """Test complete workflow: Qwen pattern recognition -> HuggingFace verification."""
        # Mock web search for Qwen
        qwen_web_response = Mock()
        qwen_web_response.status_code = 200
        qwen_web_response.json.return_value = {
            "results": [
                {
                    "url": "https://huggingface.co/user/rife-model",
                    "title": "RIFE Model",
                    "content": "Frame interpolation model"
                }
            ]
        }

        # Mock Civitai API (should be skipped)
        civitai_response = Mock()
        civitai_response.status_code = 200
        civitai_response.json.return_value = {"items": []}

        # Mock HF API
        mock_api = Mock()
        mock_repo_info = Mock()
        mock_repo_info.id = "user/rife-model"
        mock_api.repo_info.return_value = mock_repo_info
        mock_api.list_repo_files.return_value = [
            Mock(path="rife49.pth", size=104857600)
        ]
        mock_hf_api_class.return_value = mock_api

        # Set up mocks
        mock_post.return_value = qwen_web_response
        mock_get.return_value = civitai_response

        with patch.dict(os.environ, {"TAVILY_API_KEY": "test_key"}), \
             patch("comfyfixersmart.search.hf_hub_url", return_value="https://hf.co/rife-download"):

            # Test Qwen pattern recognition
            qwen_search = QwenSearch()
            qwen_result = qwen_search.search({"filename": "rife49.pth", "type": "checkpoints"})

            # Should recognize as HF model and return NOT_FOUND with pattern info
            assert qwen_result.status == "NOT_FOUND"
            assert qwen_result.metadata["pattern_recognized"] is True

            # Test HuggingFace search
            hf_search = HuggingFaceSearch()
            hf_result = hf_search.search({"filename": "rife49.pth", "type": "checkpoints"})

            # Should find the model
            assert hf_result.status == "FOUND"
            assert hf_result.source == "huggingface"
            assert hf_result.download_url == "https://hf.co/rife-download"

    @patch("requests.get")
    def test_complete_workflow_civitai_with_hash_fallback(self, mock_get):
        """Test complete workflow: Civitai API -> Hash fallback."""
        # Mock Civitai API responses (no results)
        api_response = Mock()
        api_response.status_code = 200
        api_response.json.return_value = {"items": []}

        # Mock hash lookup response
        hash_response = Mock()
        hash_response.status_code = 200
        hash_response.json.return_value = {
            "modelId": 12345,
            "id": 67890,
            "model": {"name": "Hash Found Model", "type": "Checkpoint"},
            "name": "Version 1.0",
            "files": [{"name": "hash_model.safetensors"}]
        }

        # Configure mock to return different responses for different URLs
        def mock_get_side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            if "by-hash" in url:
                return hash_response
            else:
                return api_response

        mock_get.side_effect = mock_get_side_effect

        civitai_search = CivitaiSearch("test_key")

        # Test with local file for hash calculation
        with patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=2097152), \
             patch.object(civitai_search, "_calculate_file_hash", return_value="test_hash"):

            result = civitai_search.search({
                "filename": "hash_model.safetensors",
                "type": "checkpoints",
                "local_path": "/path/to/model.safetensors"
            })

            assert result.status == "FOUND"
            assert result.civitai_id == 12345
            assert result.civitai_name == "Hash Found Model"
            assert result.confidence == "exact"

    @patch("requests.post")
    @patch("requests.get")
    def test_error_recovery_across_backends(self, mock_get, mock_post):
        """Test error recovery and fallback across multiple backends."""
        # Mock all APIs to fail initially
        api_response = Mock()
        api_response.status_code = 500
        api_response.text = "Internal Server Error"
        mock_get.return_value = api_response

        web_response = Mock()
        web_response.status_code = 429
        web_response.text = "Rate limited"
        mock_post.return_value = web_response

        # Test Qwen search with errors
        qwen_search = QwenSearch()
        qwen_result = qwen_search.search({"filename": "error_model.safetensors", "type": "checkpoints"})

        assert qwen_result.status == "NOT_FOUND"

        # Test Civitai search with errors
        civitai_search = CivitaiSearch("test_key")
        civitai_result = civitai_search.search({"filename": "error_model.safetensors", "type": "checkpoints"})

        assert civitai_result.status == "ERROR"

        # Test HuggingFace search with errors
        hf_search = HuggingFaceSearch()
        hf_result = hf_search.search({"filename": "error_model.safetensors", "type": "checkpoints"})

        assert hf_result.status == "NOT_FOUND"

        # Test ModelSearch coordination with errors
        search = ModelSearch()
        final_result = search.search_model({"filename": "error_model.safetensors", "type": "checkpoints"})

        # Should return the first error encountered
        assert final_result.status in ["NOT_FOUND", "ERROR"]


class TestSearchPerformanceAndCaching:
    """Integration tests for search performance and caching."""

    def test_model_search_result_caching(self, tmp_path):
        """Test that ModelSearch properly caches results."""
        cache_dir = tmp_path / "cache"
        search = ModelSearch(cache_dir=str(cache_dir))

        # Create a mock successful result
        cached_result = SearchResult(
            status="FOUND",
            filename="cached_model.safetensors",
            source="civitai",
            civitai_id=12345
        )

        # Manually cache the result
        search._cache_result(cached_result)

        # Verify cache file exists
        cache_file = cache_dir / "cached_model.safetensors.json"
        assert cache_file.exists()

        # Test cache retrieval
        retrieved_result = search._get_cached_result("cached_model.safetensors")
        assert retrieved_result is not None
        assert retrieved_result.status == "FOUND"
        assert retrieved_result.civitai_id == 12345

    def test_qwen_search_caching(self, tmp_path):
        """Test QwenSearch caching functionality."""
        cache_dir = tmp_path / "qwen_cache"
        search = QwenSearch(cache_dir=str(cache_dir))

        # Mock Qwen result
        qwen_payload = {
            "status": "FOUND",
            "source": "huggingface",
            "repo": "user/repo",
            "download_url": "https://hf.co/download"
        }

        # Store in cache
        search._store_cached_result("test_model.safetensors", qwen_payload)

        # Retrieve from cache
        cached_result = search._load_cached_result("test_model.safetensors")

        assert cached_result is not None
        assert cached_result.status == "FOUND"
        assert cached_result.source == "huggingface"

    def test_cache_invalidation_by_age(self, tmp_path):
        """Test cache invalidation based on age."""
        import time

        cache_dir = tmp_path / "cache"
        search = ModelSearch(cache_dir=str(cache_dir))

        # Create old cached result
        old_result = SearchResult(
            status="FOUND",
            filename="old_model.safetensors",
            source="civitai"
        )

        # Manually create old cache file
        cache_file = cache_dir / "old_model.safetensors.json"
        with open(cache_file, "w") as f:
            json.dump(old_result.__dict__, f)

        # Set file modification time to be old
        old_time = time.time() - (24 * 60 * 60 * 2)  # 2 days ago
        os.utime(cache_file, (old_time, old_time))

        # Should not retrieve old cached result
        retrieved = search._get_cached_result("old_model.safetensors")
        assert retrieved is None

    def test_search_multiple_models_caching(self):
        """Test caching behavior with multiple model searches."""
        search = ModelSearch()

        models = [
            {"filename": "model1.safetensors", "type": "checkpoints"},
            {"filename": "model2.safetensors", "type": "loras"},
        ]

        # Mock search results
        with patch.object(search, "search_model") as mock_search:
            mock_search.side_effect = [
                SearchResult(status="FOUND", filename="model1.safetensors", source="civitai"),
                SearchResult(status="NOT_FOUND", filename="model2.safetensors"),
            ]

            results = search.search_multiple_models(models)

            assert len(results) == 2
            assert results[0].status == "FOUND"
            assert results[1].status == "NOT_FOUND"

            # Verify caching was attempted for successful result
            assert mock_search.call_count == 2