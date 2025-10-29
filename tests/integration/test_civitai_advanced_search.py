"""
Integration tests for Civitai advanced search functionality.

Tests the enhanced Civitai search capabilities including:
- Direct ID lookup for problematic models
- Multi-strategy search fallbacks
- Known models mapping integration
- Batch download operations
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add the src directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from comfyfixersmart.search import CivitaiSearch, SearchResult
from comfyfixersmart.config import config
from comfyfixersmart.civitai_tools.direct_id_backend import DirectIDBackend
from comfyfixersmart.civitai_tools.enhanced_search import EnhancedCivitaiSearch


class TestCivitaiAdvancedSearch:
    """Integration tests for Civitai advanced search functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Use a mock API key for testing to avoid making real API calls
        os.environ["CIVITAI_API_KEY"] = "test_api_key"
        self.civitai_search = CivitaiSearch()
        self.direct_id_backend = DirectIDBackend()

    def test_direct_id_lookup_nsfw_model(self, monkeypatch):
        """Model 1091495 should be found via direct ID."""
        # Mock the API response for model 1091495
        mock_response = {
            "id": 1091495,
            "name": "Better detailed pussy and anus",
            "type": "LORA",
            "modelVersions": [
                {
                    "id": 9857,
                    "name": "v3.0",
                    "files": [
                        {
                            "name": "better_detailed_pussy_anus_v3.safetensors",
                            "id": 12345,
                            "sizeKB": 145000,
                        }
                    ],
                }
            ],
        }

        # Patch the requests.get method to return our mock response
        with patch("requests.get") as mock_get:
            mock_response_obj = Mock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_get.return_value = mock_response_obj

            # Test direct ID lookup
            result = self.civitai_search.search_by_id(1091495)

            assert result is not None
            assert result.status == "FOUND"
            assert result.civitai_id == 1091495
            assert result.civitai_name == "Better detailed pussy and anus"
            assert result.confidence == "exact"

    def test_direct_id_lookup_eyes_hd(self, monkeypatch):
        """Model 670378 should be found via direct ID."""
        # Mock the API response for model 670378
        mock_response = {
            "id": 670378,
            "name": "Eyes High Definition",
            "type": "LORA",
            "modelVersions": [
                {
                    "id": 7890,
                    "name": "V1",
                    "files": [
                        {
                            "name": "eyes_high_definition_v1.safetensors",
                            "id": 67890,
                            "sizeKB": 87000,
                        }
                    ],
                }
            ],
        }

        # Patch the requests.get method to return our mock response
        with patch("requests.get") as mock_get:
            mock_response_obj = Mock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_get.return_value = mock_response_obj

            # Test direct ID lookup
            result = self.civitai_search.search_by_id(670378)

            assert result is not None
            assert result.status == "FOUND"
            assert result.civitai_id == 670378
            assert result.civitai_name == "Eyes High Definition"
            assert result.confidence == "exact"

    def test_query_search_baseline(self, monkeypatch):
        """'Hand Fine Tuning SDXL' should work with standard search."""
        # Mock a successful query response for a standard model
        mock_response = {
            "items": [
                {
                    "id": 123456,
                    "name": "Hand Fine Tuning SDXL",
                    "type": "LORA",
                    "modelVersions": [
                        {
                            "id": 1234,
                            "name": "v1.0",
                            "files": [
                                {
                                    "name": "hand_fine_tuning_sdxl.safetensors",
                                    "id": 5678,
                                    "sizeKB": 120000,
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        with patch("requests.get") as mock_get:
            mock_response_obj = Mock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_get.return_value = mock_response_obj

            # Test standard search
            model_info = {"filename": "hand_fine_tuning_sdxl.safetensors", "type": "loras"}
            result = self.civitai_search.search(model_info)

            assert result.status == "FOUND"
            assert result.civitai_id == 123456

    def test_known_models_integration(self, tmp_path):
        """known_models.json should provide instant lookups."""
        # Create a temporary known models file
        known_models_file = tmp_path / "known_models.json"
        known_models_content = {
            "test model": {
                "model_id": 999999,
                "model_name": "Test Model",
                "version": "v1.0",
                "type": "LORA",
                "url": "https://civitai.com/models/999999",
            }
        }

        import json

        with open(known_models_file, "w") as f:
            json.dump(known_models_content, f)

        # Create DirectIDBackend with the temporary file
        backend = DirectIDBackend(known_models_path=str(known_models_file))

        # Mock the API response for the test model
        mock_response = {
            "id": 999999,
            "name": "Test Model",
            "type": "LORA",
            "modelVersions": [
                {
                    "id": 1111,
                    "name": "v1.0",
                    "files": [{"name": "test_model_v1.safetensors", "id": 2222, "sizeKB": 100000}],
                }
            ],
        }

        with patch("requests.get") as mock_get:
            mock_response_obj = Mock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_get.return_value = mock_response_obj

            # Test lookup by name
            result = backend.lookup_by_name("test model")

            assert result is not None
            assert result.status == "FOUND"
            assert result.civitai_id == 999999
            assert result.civitai_name == "Test Model"

    def test_direct_id_backend_lookup_by_id(self, monkeypatch):
        """DirectIDBackend should find models by ID."""
        # Mock the API response
        mock_response = {
            "id": 888888,
            "name": "Another Test Model",
            "type": "LORA",
            "modelVersions": [
                {
                    "id": 2222,
                    "name": "v2.0",
                    "files": [
                        {
                            "name": "another_test_model_v2.safetensors",
                            "primary": True,
                            "sizeKB": 150000,
                        }
                    ],
                }
            ],
        }

        with patch("requests.get") as mock_get:
            mock_response_obj = Mock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_get.return_value = mock_response_obj

            # Test backend lookup by ID (with default known models file that doesn't exist)
            backend = DirectIDBackend(known_models_path="/nonexistent/file.json")
            result = backend.lookup_by_id(888888)

            assert result is not None
            assert result.status == "FOUND"
            assert result.civitai_id == 888888
            assert result.civitai_name == "Another Test Model"
            assert result.confidence == "exact"  # Direct ID lookups should have exact confidence

    def test_enhanced_search_inheritance(self):
        """EnhancedCivitaiSearch should inherit from CivitaiSearch."""
        enhanced_search = EnhancedCivitaiSearch()

        # Should inherit from CivitaiSearch
        assert isinstance(enhanced_search, CivitaiSearch)

        # Should have the enhanced methods
        assert hasattr(enhanced_search, "_try_browsing_levels")
        assert hasattr(enhanced_search, "search_by_id")
        assert hasattr(enhanced_search, "search_multi_strategy")


# Additional tests for the multi-strategy search methods that were added
class TestMultiStrategySearch:
    """Tests for the multi-strategy search methods."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        os.environ["CIVITAI_API_KEY"] = "test_api_key"
        self.civitai_search = CivitaiSearch()

    def test_search_with_nsfw_param(self, monkeypatch):
        """Test search with nsfw parameter."""
        # Mock the API response
        mock_response = {
            "items": [
                {
                    "id": 111111,
                    "name": "NSFW Test Model",
                    "type": "LORA",
                    "modelVersions": [
                        {
                            "id": 111,
                            "name": "v1.0",
                            "files": [
                                {"name": "nsfw_test_v1.safetensors", "id": 222, "sizeKB": 100000}
                            ],
                        }
                    ],
                }
            ]
        }

        with patch("requests.get") as mock_get:
            mock_response_obj = Mock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_get.return_value = mock_response_obj

            # Test the private method that handles nsfw param
            model_ref = {"filename": "nsfw_test_v1.safetensors", "type": "loras"}
            results = self.civitai_search._search_with_nsfw_param(model_ref, nsfw=True)

            # Should return a list of SearchResult objects
            assert isinstance(results, list)
            if results:  # If results are returned
                assert all(isinstance(r, SearchResult) for r in results)

    def test_extract_tags_from_query(self):
        """Test tag extraction from search queries."""
        query = "better detailed pussy and anus v3.0"
        expected_tags = [
            "pussy",
            "anus",
            "breasts",
            "ass",
            "thighs",
            "realistic",
            "high",
            "definition",
            "hd",
            "detailed",
            "detail",
            "nsfw",
            "explicit",
            "nude",
            "naked",
            "adult",
            "better",
            "detailed",
            "pussy",
            "anus",
            "v3",
            "v3.0",
        ]

        # Use the method we added to CivitaiSearch
        extracted_tags = self.civitai_search._extract_tags_from_query(query)

        # Check that some expected tags are in the result
        assert "pussy" in extracted_tags or "detailed" in extracted_tags
        assert isinstance(extracted_tags, list)

    def test_calculate_confidence_score(self):
        """Test confidence scoring for search results."""
        # Create a mock SearchResult
        result = SearchResult(status="FOUND", filename="test.safetensors", confidence="exact")

        # Test the scoring method we added
        score = self.civitai_search._calculate_confidence_score(result)
        assert score == 100  # Exact matches should score 100

        # Test with fuzzy confidence
        result.confidence = "fuzzy"
        result.metadata = {"found_by": "direct_id"}
        score = self.civitai_search._calculate_confidence_score(result)
        assert score == 90  # Direct ID fuzzy matches should score 90


if __name__ == "__main__":
    pytest.main([__file__])
