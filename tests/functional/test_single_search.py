"""
Functional tests for single model search functionality.

Tests searching for individual models using different backends,
focusing on HuggingFace and other search scenarios.
"""

import os
from unittest.mock import Mock, patch

import pytest

from comfyfixersmart.search import ModelSearch, SearchResult


class TestSingleModelSearch:
    """Test searching for individual models using ModelSearch."""

    @pytest.fixture
    def model_search(self, tmp_path):
        """Create ModelSearch instance for testing."""
        return ModelSearch(cache_dir=str(tmp_path / "cache"))

    def test_search_single_model_civitai_backend(self, model_search):
        """Test searching single model with Civitai backend."""
        model_info = {
            'filename': 'realisticVisionV60B1_v60B1VAE.safetensors',
            'type': 'checkpoints',
            'node_type': 'CheckpointLoaderSimple'
        }

        # Mock Civitai search
        with patch.object(model_search.backends['civitai'], 'search') as mock_civitai:
            mock_civitai.return_value = SearchResult(
                status="FOUND",
                filename="realisticVisionV60B1_v60B1VAE.safetensors",
                source="civitai",
                civitai_id=12345,
                download_url="https://civitai.com/api/download/models/12345",
                confidence="exact"
            )

            result = model_search.search_model(model_info, backends=["civitai"])

            assert result.status == "FOUND"
            assert result.source == "civitai"
            assert result.civitai_id == 12345
            mock_civitai.assert_called_once_with(model_info)

    def test_search_single_model_huggingface_backend(self, model_search):
        """Test searching single model with HuggingFace backend."""
        model_info = {
            'filename': 'rife49.pth',
            'type': 'upscale_models',
            'node_type': 'UpscaleModelLoader'
        }

        # Mock HuggingFace search (currently returns NOT_FOUND)
        with patch.object(model_search.backends['huggingface'], 'search') as mock_hf:
            mock_hf.return_value = SearchResult(
                status="NOT_FOUND",
                filename="rife49.pth",
                metadata={"reason": "HuggingFace search not implemented yet"}
            )

            result = model_search.search_model(model_info, backends=["huggingface"])

            assert result.status == "NOT_FOUND"
            assert "not implemented yet" in result.metadata["reason"]
            mock_hf.assert_called_once_with(model_info)

    def test_search_single_model_qwen_backend(self, model_search):
        """Test searching single model with Qwen backend."""
        model_info = {
            'filename': 'some_model.safetensors',
            'type': 'checkpoints'
        }

        # Mock Qwen search (currently returns NOT_FOUND)
        with patch.object(model_search.backends['qwen'], 'search') as mock_qwen:
            mock_qwen.return_value = SearchResult(
                status="NOT_FOUND",
                filename="some_model.safetensors",
                metadata={"reason": "Qwen integration not implemented yet"}
            )

            result = model_search.search_model(model_info, backends=["qwen"])

            assert result.status == "NOT_FOUND"
            assert "not implemented yet" in result.metadata["reason"]
            mock_qwen.assert_called_once_with(model_info)

    def test_search_single_model_multiple_backends_priority(self, model_search):
        """Test searching with multiple backends - should try in order until success."""
        model_info = {'filename': 'test_model.safetensors', 'type': 'checkpoints'}

        # Mock backends: Civitai fails, Qwen succeeds
        with patch.object(model_search.backends['civitai'], 'search') as mock_civitai, \
             patch.object(model_search.backends['qwen'], 'search') as mock_qwen:

            mock_civitai.return_value = SearchResult(
                status="NOT_FOUND",
                filename="test_model.safetensors"
            )
            mock_qwen.return_value = SearchResult(
                status="FOUND",
                filename="test_model.safetensors",
                source="qwen",
                download_url="https://example.com/qwen_model"
            )

            result = model_search.search_model(model_info, backends=["civitai", "qwen"])

            assert result.status == "FOUND"
            assert result.source == "qwen"
            mock_civitai.assert_called_once()
            mock_qwen.assert_called_once()

    def test_search_single_model_all_backends_fail(self, model_search):
        """Test searching when all backends fail."""
        model_info = {'filename': 'test_model.safetensors', 'type': 'checkpoints'}

        # Mock all backends to fail
        with patch.object(model_search.backends['civitai'], 'search') as mock_civitai, \
             patch.object(model_search.backends['qwen'], 'search') as mock_qwen, \
             patch.object(model_search.backends['huggingface'], 'search') as mock_hf:

            mock_civitai.return_value = SearchResult(status="NOT_FOUND", filename="test_model.safetensors")
            mock_qwen.return_value = SearchResult(status="NOT_FOUND", filename="test_model.safetensors")
            mock_hf.return_value = SearchResult(status="NOT_FOUND", filename="test_model.safetensors")

            result = model_search.search_model(model_info, backends=["civitai", "qwen", "huggingface"])

            assert result.status == "NOT_FOUND"
            assert "backends_tried" in result.metadata
            assert result.metadata["backends_tried"] == ["civitai", "qwen", "huggingface"]

    def test_search_single_model_with_caching(self, model_search, tmp_path):
        """Test that search results are cached and reused."""
        model_info = {'filename': 'cache_test.safetensors', 'type': 'checkpoints'}

        # First search - should call backend
        with patch.object(model_search.backends['civitai'], 'search') as mock_civitai:
            mock_civitai.return_value = SearchResult(
                status="FOUND",
                filename="cache_test.safetensors",
                source="civitai",
                download_url="https://example.com/cached"
            )

            result1 = model_search.search_model(model_info, backends=["civitai"])
            assert result1.status == "FOUND"
            assert mock_civitai.call_count == 1

        # Second search - should use cache
        with patch.object(model_search.backends['civitai'], 'search') as mock_civitai:
            result2 = model_search.search_model(model_info, backends=["civitai"])
            assert result2.status == "FOUND"
            # Backend should not be called again
            assert mock_civitai.call_count == 0

    def test_search_single_model_cache_disabled(self, model_search):
        """Test searching with cache disabled."""
        model_info = {'filename': 'no_cache_test.safetensors', 'type': 'checkpoints'}

        with patch.object(model_search.backends['civitai'], 'search') as mock_civitai:
            mock_civitai.return_value = SearchResult(
                status="FOUND",
                filename="no_cache_test.safetensors",
                source="civitai"
            )

            # First search with cache disabled
            result1 = model_search.search_model(model_info, backends=["civitai"], use_cache=False)
            assert result1.status == "FOUND"
            assert mock_civitai.call_count == 1

            # Second search with cache disabled - should call backend again
            result2 = model_search.search_model(model_info, backends=["civitai"], use_cache=False)
            assert result2.status == "FOUND"
            assert mock_civitai.call_count == 2

    def test_search_single_model_error_handling(self, model_search):
        """Test error handling during search."""
        model_info = {'filename': 'error_test.safetensors', 'type': 'checkpoints'}

        # Mock backend to raise exception
        with patch.object(model_search.backends['civitai'], 'search') as mock_civitai:
            mock_civitai.side_effect = Exception("Network error")

            result = model_search.search_model(model_info, backends=["civitai"])

            assert result.status == "ERROR"
            assert "Network error" in result.error_message

    def test_search_single_model_invalid_backend(self, model_search):
        """Test searching with invalid backend name."""
        model_info = {'filename': 'test.safetensors', 'type': 'checkpoints'}

        result = model_search.search_model(model_info, backends=["invalid_backend", "civitai"])

        # Should skip invalid backend and try valid one
        assert result.status == "NOT_FOUND"  # Since we didn't mock civitai

    def test_search_single_model_default_backends(self, model_search):
        """Test searching with default backends."""
        model_info = {'filename': 'default_test.safetensors', 'type': 'checkpoints'}

        with patch.object(model_search.backends['civitai'], 'search') as mock_civitai:
            mock_civitai.return_value = SearchResult(
                status="FOUND",
                filename="default_test.safetensors",
                source="civitai"
            )

            # Don't specify backends - should use default (civitai)
            result = model_search.search_model(model_info)

            assert result.status == "FOUND"
            mock_civitai.assert_called_once()


class TestSearchScenarios:
    """Test various search scenarios and edge cases."""

    def test_search_different_model_types(self):
        """Test searching for different types of models."""
        search = ModelSearch()

        test_cases = [
            ("checkpoint.safetensors", "checkpoints", "CheckpointLoaderSimple"),
            ("lora.safetensors", "loras", "LoraLoader"),
            ("vae.safetensors", "vae", "VAELoader"),
            ("controlnet.pth", "controlnet", "ControlNetLoader"),
            ("upscaler.pth", "upscale_models", "UpscaleModelLoader"),
        ]

        for filename, model_type, node_type in test_cases:
            model_info = {
                'filename': filename,
                'type': model_type,
                'node_type': node_type
            }

            # Mock successful search
            with patch.object(search.backends['civitai'], 'search') as mock_civitai:
                mock_civitai.return_value = SearchResult(
                    status="FOUND",
                    filename=filename,
                    source="civitai",
                    download_url=f"https://example.com/{filename}"
                )

                result = search.search_model(model_info, backends=["civitai"])

                assert result.status == "FOUND"
                assert result.filename == filename

    def test_search_with_state_manager_tracking(self):
        """Test search with state manager tracking."""
        state_manager = Mock()
        search = ModelSearch(state_manager=state_manager)

        model_info = {'filename': 'tracked_model.safetensors', 'type': 'checkpoints'}

        with patch.object(search.backends['civitai'], 'search') as mock_civitai:
            mock_civitai.return_value = SearchResult(
                status="FOUND",
                filename="tracked_model.safetensors",
                source="civitai",
                civitai_id=12345
            )

            result = search.search_model(model_info, backends=["civitai"])

            # State manager should be notified
            state_manager.mark_download_attempted.assert_called_once()
            call_args = state_manager.mark_download_attempted.call_args
            assert call_args[0][0] == "tracked_model.safetensors"  # filename
            assert call_args[0][1] == model_info  # model_info

    def test_search_result_metadata(self):
        """Test that search results include proper metadata."""
        search = ModelSearch()

        model_info = {'filename': 'metadata_test.safetensors', 'type': 'checkpoints'}

        with patch.object(search.backends['civitai'], 'search') as mock_civitai:
            mock_civitai.return_value = SearchResult(
                status="FOUND",
                filename="metadata_test.safetensors",
                source="civitai",
                confidence="exact",
                metadata={"search_attempts": 1, "api_calls": 2}
            )

            result = search.search_model(model_info, backends=["civitai"])

            assert result.metadata["search_attempts"] == 1
            assert result.metadata["api_calls"] == 2
            assert result.confidence == "exact"

    def test_search_filename_normalization(self):
        """Test that search handles various filename formats."""
        search = ModelSearch()

        # Test different filename variations
        filenames = [
            "model.safetensors",
            "Model.Safetensors",
            "MODEL.SAFETENSORS",
            "model_v1.0.safetensors",
            "model-final-version.safetensors"
        ]

        for filename in filenames:
            model_info = {'filename': filename, 'type': 'checkpoints'}

            with patch.object(search.backends['civitai'], 'search') as mock_civitai:
                mock_civitai.return_value = SearchResult(
                    status="FOUND",
                    filename=filename,
                    source="civitai"
                )

                result = search.search_model(model_info, backends=["civitai"])
                assert result.status == "FOUND"
                assert result.filename == filename


class TestSearchPerformance:
    """Test search performance and optimization."""

    def test_search_multiple_models_batching(self):
        """Test searching multiple models efficiently."""
        search = ModelSearch()

        models = [
            {'filename': f'model_{i}.safetensors', 'type': 'checkpoints'}
            for i in range(5)
        ]

        # Mock successful searches for all models
        with patch.object(search, 'search_model') as mock_search:
            mock_search.side_effect = [
                SearchResult(status="FOUND", filename=f'model_{i}.safetensors', source="civitai")
                for i in range(5)
            ]

            results = search.search_multiple_models(models, backends=["civitai"])

            assert len(results) == 5
            assert all(r.status == "FOUND" for r in results)
            assert mock_search.call_count == 5

    def test_search_cache_management(self, tmp_path):
        """Test cache management functionality."""
        cache_dir = tmp_path / "test_cache"
        search = ModelSearch(cache_dir=str(cache_dir))

        # Create some cache files
        cache_file1 = cache_dir / "model1.safetensors.json"
        cache_file1.write_text('{"status": "FOUND", "filename": "model1.safetensors"}')

        cache_file2 = cache_dir / "model2.safetensors.json"
        cache_file2.write_text('{"status": "FOUND", "filename": "model2.safetensors"}')

        # Clear specific cache
        search.clear_cache("model1.safetensors")
        assert not cache_file1.exists()
        assert cache_file2.exists()

        # Clear all cache
        search.clear_cache()
        assert not cache_file2.exists()

    def test_search_statistics(self, tmp_path):
        """Test search statistics reporting."""
        cache_dir = tmp_path / "stats_cache"
        search = ModelSearch(cache_dir=str(cache_dir))

        # Create some cache files
        for i in range(3):
            cache_file = cache_dir / f"cached_model_{i}.json"
            cache_file.write_text('{"status": "FOUND"}')

        stats = search.get_search_stats()

        assert stats["cached_results"] == 3
        assert stats["cache_dir"] == str(cache_dir)
        assert len(stats["backends_available"]) == 3
        assert "civitai" in stats["backends_available"]