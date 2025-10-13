"""
Functional tests for Civitai search functionality.

Tests the Civitai search backend with real API calls (when API key is available)
or mocked responses for CI/testing environments.
"""

import os
import json
from unittest.mock import Mock, patch

import pytest

from comfyfixersmart.search import CivitaiSearch, SearchResult


class TestCivitaiSearchIntegration:
    """Integration tests for Civitai search with real/mocked API calls."""

    @pytest.fixture
    def civitai_search(self):
        """Create CivitaiSearch instance for testing."""
        # Use a test API key if available, otherwise mock
        api_key = os.getenv('CIVITAI_API_KEY', 'test_key_for_mocking')
        return CivitaiSearch(api_key)

    @pytest.fixture
    def mock_civitai_response(self):
        """Mock Civitai API response data."""
        return {
            "items": [
                {
                    "id": 12345,
                    "name": "Test Realistic Vision Model",
                    "modelVersions": [
                        {
                            "id": 67890,
                            "name": "v1.0",
                            "files": [
                                {
                                    "name": "realisticVisionV60B1_v60B1VAE.safetensors",
                                    "downloadUrl": "https://civitai.com/api/download/models/67890"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

    def test_civitai_search_real_model(self, civitai_search):
        """Test searching for a known real model (may fail in CI without API key)."""
        model_info = {
            'filename': 'realisticVisionV60B1_v60B1VAE.safetensors',
            'type': 'checkpoints',
            'node_type': 'CheckpointLoaderSimple'
        }

        # Skip if no real API key (for CI environments)
        if not os.getenv('CIVITAI_API_KEY') or civitai_search.api_key == 'test_key_for_mocking':
            pytest.skip("Skipping real API test - no valid API key")

        result = civitai_search.search(model_info)

        # Should either find the model or return NOT_FOUND
        assert isinstance(result, SearchResult)
        assert result.filename == model_info['filename']

        if result.status == 'FOUND':
            assert result.source == 'civitai'
            assert result.civitai_id is not None
            assert result.download_url is not None
            assert 'civitai.com/api/download' in result.download_url

    @patch('requests.get')
    def test_civitai_search_mocked_success(self, mock_get, civitai_search, mock_civitai_response):
        """Test Civitai search with mocked successful response."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_civitai_response
        mock_get.return_value = mock_response

        model_info = {
            'filename': 'realisticVisionV60B1_v60B1VAE.safetensors',
            'type': 'checkpoints'
        }

        result = civitai_search.search(model_info)

        assert result.status == 'FOUND'
        assert result.filename == 'realisticVisionV60B1_v60B1VAE.safetensors'
        assert result.source == 'civitai'
        assert result.civitai_id == 12345
        assert result.civitai_name == 'Test Realistic Vision Model'
        assert result.version_id == 67890
        assert result.version_name == 'v1.0'
        assert result.download_url == 'https://civitai.com/api/download/models/67890'
        assert result.confidence == 'exact'

        # Verify API call was made correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert 'https://civitai.com/api/v1/models' in call_args[0][0]
        assert 'Authorization' in call_args[1]['headers']

    @patch('requests.get')
    def test_civitai_search_mocked_fuzzy_match(self, mock_get, civitai_search):
        """Test Civitai search with fuzzy match (no exact filename match)."""
        # Mock response with different filename
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "id": 11111,
                    "name": "Some Other Model",
                    "modelVersions": [
                        {
                            "id": 22222,
                            "name": "v1.0",
                            "files": [
                                {
                                    "name": "some_other_model.safetensors",
                                    "downloadUrl": "https://civitai.com/api/download/models/22222"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response

        model_info = {
            'filename': 'target_model.safetensors',
            'type': 'checkpoints'
        }

        result = civitai_search.search(model_info)

        assert result.status == 'FOUND'
        assert result.filename == 'target_model.safetensors'
        assert result.confidence == 'fuzzy'
        assert result.civitai_id == 11111

    @patch('requests.get')
    def test_civitai_search_mocked_not_found(self, mock_get, civitai_search):
        """Test Civitai search when no results found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response

        model_info = {'filename': 'nonexistent_model.safetensors', 'type': 'checkpoints'}

        result = civitai_search.search(model_info)

        assert result.status == 'NOT_FOUND'
        assert result.filename == 'nonexistent_model.safetensors'
        assert 'No results found' in result.metadata['reason']

    @patch('requests.get')
    def test_civitai_search_api_error(self, mock_get, civitai_search):
        """Test Civitai search with API error response."""
        mock_response = Mock()
        mock_response.status_code = 429  # Rate limited
        mock_get.return_value = mock_response

        model_info = {'filename': 'test_model.safetensors', 'type': 'checkpoints'}

        result = civitai_search.search(model_info)

        assert result.status == 'ERROR'
        assert 'API error: 429' in result.error_message

    @patch('requests.get')
    def test_civitai_search_network_error(self, mock_get, civitai_search):
        """Test Civitai search with network error."""
        mock_get.side_effect = Exception("Connection timeout")

        model_info = {'filename': 'test_model.safetensors', 'type': 'checkpoints'}

        result = civitai_search.search(model_info)

        assert result.status == 'ERROR'
        assert 'Connection timeout' in result.error_message

    def test_civitai_search_query_preparation(self, civitai_search):
        """Test search query preparation for different filename formats."""
        test_cases = [
            ('model.safetensors', 'model'),
            ('Model_v1.0.ckpt', 'Model v1 0'),
            ('complex-model.name.pth', 'complex-model name'),
            ('model_with_underscores.safetensors', 'model with underscores')
        ]

        for filename, expected_query in test_cases:
            query = civitai_search._prepare_search_query(filename)
            assert query == expected_query

    def test_civitai_search_type_filtering(self, civitai_search):
        """Test type filtering for different model types."""
        test_cases = [
            ('checkpoints', 'Checkpoint'),
            ('loras', 'LORA'),
            ('vae', 'VAE'),
            ('controlnet', 'Controlnet'),
            ('upscale_models', 'Upscaler'),
            ('unknown_type', None)
        ]

        for model_type, expected_filter in test_cases:
            filter_value = civitai_search._get_type_filter(model_type)
            assert filter_value == expected_filter

    def test_civitai_search_find_best_match(self, civitai_search):
        """Test finding best match in search results."""
        results = [
            {
                "id": 1,
                "modelVersions": [
                    {
                        "id": 10,
                        "files": [
                            {"name": "wrong_model.safetensors"},
                            {"name": "target_model.safetensors"}
                        ]
                    }
                ]
            },
            {
                "id": 2,
                "modelVersions": [
                    {
                        "id": 20,
                        "files": [
                            {"name": "another_model.safetensors"}
                        ]
                    }
                ]
            }
        ]

        # Should find exact match
        match = civitai_search._find_best_match(results, "target_model.safetensors")
        assert match["id"] == 1

        # Should return None for no match
        match = civitai_search._find_best_match(results, "nonexistent.safetensors")
        assert match is None


class TestCivitaiSearchConvenienceFunction:
    """Test the search_civitai convenience function."""

    @patch('comfyfixersmart.search.CivitaiSearch.search')
    def test_search_civitai_convenience_function(self, mock_search):
        """Test the search_civitai convenience function."""
        mock_search.return_value = SearchResult(
            status="FOUND",
            filename="test_model.safetensors",
            source="civitai",
            civitai_id=12345
        )

        from comfyfixersmart.search import search_civitai

        model_info = {'filename': 'test_model.safetensors', 'type': 'checkpoints'}
        result = search_civitai(model_info)

        assert result.status == "FOUND"
        assert result.civitai_id == 12345
        mock_search.assert_called_once()


class TestCivitaiSearchRealWorldScenarios:
    """Test Civitai search with real-world scenarios and edge cases."""

    def test_civitai_search_with_special_characters(self):
        """Test searching for models with special characters in names."""
        search = CivitaiSearch("test_key")

        # Test filename with special characters
        filename = "model_v2.0-final_(updated).safetensors"
        query = search._prepare_search_query(filename)

        # Should clean up the filename
        assert "model v2 0 final updated" == query

    def test_civitai_search_empty_results_handling(self):
        """Test handling of empty results from API."""
        search = CivitaiSearch("test_key")

        # Simulate empty results
        results = []
        match = search._find_best_match(results, "any_model.safetensors")
        assert match is None

    def test_civitai_search_malformed_response(self):
        """Test handling of malformed API responses."""
        search = CivitaiSearch("test_key")

        # Test with missing modelVersions
        malformed_result = {"id": 12345, "name": "Test"}
        with pytest.raises(KeyError):
            search._create_result_from_match(malformed_result, "test.safetensors", "exact")

    @patch('requests.get')
    def test_civitai_search_with_different_file_types(self, mock_get):
        """Test searching for different model file types."""
        search = CivitaiSearch("test_key")

        # Mock response for different file types
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "id": 12345,
                    "name": "Multi-format Model",
                    "modelVersions": [
                        {
                            "id": 67890,
                            "name": "v1.0",
                            "files": [
                                {"name": "model.ckpt", "downloadUrl": "url1"},
                                {"name": "model.safetensors", "downloadUrl": "url2"},
                                {"name": "model.pth", "downloadUrl": "url3"}
                            ]
                        }
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response

        # Search for .safetensors version
        result = search.search({"filename": "model.safetensors", "type": "checkpoints"})
        assert result.status == "FOUND"
        assert result.download_url == "https://civitai.com/api/download/models/67890"

    def test_civitai_search_result_structure(self):
        """Test that search results have all expected fields."""
        search = CivitaiSearch("test_key")

        result = SearchResult(
            status="FOUND",
            filename="test.safetensors",
            source="civitai",
            civitai_id=12345,
            version_id=67890,
            civitai_name="Test Model",
            version_name="v1.0",
            download_url="https://example.com/download",
            confidence="exact"
        )

        # Verify all expected fields are present
        assert hasattr(result, 'status')
        assert hasattr(result, 'filename')
        assert hasattr(result, 'source')
        assert hasattr(result, 'civitai_id')
        assert hasattr(result, 'version_id')
        assert hasattr(result, 'civitai_name')
        assert hasattr(result, 'version_name')
        assert hasattr(result, 'download_url')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'metadata')
        assert hasattr(result, 'error_message')