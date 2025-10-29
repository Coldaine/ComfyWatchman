"""
Civitai Search Debugger

Diagnostic tool that shows exact API queries, raw responses,
scoring breakdowns, and suggests alternative approaches.
"""

from typing import Any, Dict, List, Optional

import requests

from ..config import config
from ..logging import get_logger
from ..utils import get_api_key


class SearchDebugger:
    """
    Diagnostic tool for Civitai search operations.

    Provides detailed insights into search failures and suggests alternatives.
    """

    def __init__(self, logger=None):
        self.api_key = config.search.civitai_api_key or get_api_key()
        self.base_url = "https://civitai.com/api/v1"
        self.logger = logger or get_logger("SearchDebugger")

    def debug_search(
        self, query: str, model_type: str = "LORA", nsfw: bool = True
    ) -> Dict[str, Any]:
        """
        Debug a search query showing all relevant information.

        Args:
            query: Search query to debug
            model_type: Model type to filter (LORA, Checkpoint, etc.)
            nsfw: Whether to include NSFW results

        Returns:
            Dictionary with detailed debugging information
        """
        debug_info = {
            "query": query,
            "model_type": model_type,
            "nsfw": nsfw,
            "strategies_tried": [],
            "results": {},
            "diagnosis": [],
            "suggestions": [],
        }

        # Strategy 1: Query search with nsfw=true
        debug_info["strategies_tried"].append("query_nsfw")
        nsfw_results = self._debug_query_search(query, model_type, nsfw=True)
        debug_info["results"]["query_nsfw"] = nsfw_results

        # Strategy 2: Query search without nsfw parameter
        debug_info["strategies_tried"].append("query_without_nsfw")
        no_nsfw_results = self._debug_query_search(query, model_type, nsfw=False)
        debug_info["results"]["query_without_nsfw"] = no_nsfw_results

        # Strategy 3: Tag-based search
        debug_info["strategies_tried"].append("tag_search")
        tag_results = self._debug_tag_search(query, model_type)
        debug_info["results"]["tag_search"] = tag_results

        # Analyze results and provide diagnosis
        diagnosis = self._analyze_results(debug_info)
        debug_info["diagnosis"] = diagnosis
        debug_info["suggestions"] = self._generate_suggestions(debug_info)

        return debug_info

    def _debug_query_search(self, query: str, model_type: str, nsfw: bool) -> Dict[str, Any]:
        """Debug a query search operation."""
        params = {"query": query, "limit": 10, "sort": "Highest Rated"}

        if nsfw:
            params["nsfw"] = "true"

        type_filter = self._map_model_type(model_type)
        if type_filter:
            params["types"] = type_filter

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        api_url = f"{self.base_url}/models"
        response = requests.get(api_url, params=params, headers=headers, timeout=30)

        raw_response = response.text
        http_code = response.status_code

        try:
            response_json = response.json()
        except Exception:
            response_json = {"error": "Invalid JSON response", "raw": raw_response}

        return {
            "api_url": f"{api_url}?{self._format_params(params)}",
            "http_code": http_code,
            "response": response_json,
            "items_returned": (
                len(response_json.get("items", [])) if isinstance(response_json, dict) else 0
            ),
        }

    def _debug_tag_search(self, query: str, model_type: str) -> Dict[str, Any]:
        """Debug a tag-based search operation."""
        # Extract tags from query
        potential_tags = self._extract_tags_from_query(query)
        tag_results = []

        for tag in potential_tags:
            params = {"tag": tag, "limit": 5, "nsfw": "true"}

            type_filter = self._map_model_type(model_type)
            if type_filter:
                params["types"] = type_filter

            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            api_url = f"{self.base_url}/models"
            response = requests.get(api_url, params=params, headers=headers, timeout=30)

            raw_response = response.text
            http_code = response.status_code

            try:
                response_json = response.json()
            except Exception:
                response_json = {"error": "Invalid JSON response", "raw": raw_response}

            tag_results.append(
                {
                    "tag": tag,
                    "api_url": f"{api_url}?{self._format_params(params)}",
                    "http_code": http_code,
                    "response": response_json,
                    "items_returned": (
                        len(response_json.get("items", []))
                        if isinstance(response_json, dict)
                        else 0
                    ),
                }
            )

        return tag_results

    def _analyze_results(self, debug_info: Dict[str, Any]) -> List[str]:
        """Analyze search results and identify issues."""
        diagnosis = []

        query_nsfw_result = debug_info["results"].get("query_nsfw", {})
        query_without_nsfw_result = debug_info["results"].get("query_without_nsfw", {})

        # Check if query search failed due to term filtering
        if (
            query_nsfw_result.get("items_returned", 0) == 0
            and query_without_nsfw_result.get("items_returned", 0) == 0
        ):
            diagnosis.append("Query search failed - likely explicit term filtering")

        # Check for different results with/without NSFW flag
        nsfw_items = query_nsfw_result.get("items_returned", 0)
        without_nsfw_items = query_without_nsfw_result.get("items_returned", 0)

        if nsfw_items > 0 and without_nsfw_items == 0:
            diagnosis.append("NSFW flag required for these results")
        elif without_nsfw_items > 0 and nsfw_items == 0:
            diagnosis.append("NSFW flag may be blocking results")

        return diagnosis

    def _generate_suggestions(self, debug_info: Dict[str, Any]) -> List[str]:
        """Generate suggestions based on search results."""
        suggestions = []

        # If no results from query search, suggest direct ID if known
        if all(
            debug_info["results"][key].get("items_returned", 0) == 0
            for key in ["query_nsfw", "query_without_nsfw"]
        ):
            suggestions.append("Try direct ID lookup if model URL known")
            suggestions.append("Try tag search: anatomy, detail, nsfw")

        # If tag search shows some results, suggest refining tags
        tag_results = debug_info["results"].get("tag_search", [])
        if tag_results:
            valid_tag_results = [
                tag_result for tag_result in tag_results if tag_result.get("items_returned", 0) > 0
            ]
            if valid_tag_results:
                suggestions.append("Tag search successful - try combining successful tags")

        # General suggestions
        suggestions.append("Check for alternative names or creators")

        return suggestions

    def _extract_tags_from_query(self, query: str) -> List[str]:
        """Extract potential tags from search query."""
        # Simple extraction - could be enhanced with NLP
        # Common tags for NSFW model search
        anatomical_terms = [
            "anatomy",
            "anatomical",
            "detail",
            "details",
            "eyes",
            "pussy",
            "anus",
            "breasts",
            "ass",
            "thighs",
        ]
        style_terms = ["realistic", "high", "definition", "hd", "detailed", "detail"]
        content_terms = ["nsfw", "explicit", "nude", "naked", "adult"]

        all_terms = anatomical_terms + style_terms + content_terms
        found_tags = []

        query_lower = query.lower()
        for term in all_terms:
            if term in query_lower and term not in found_tags:
                found_tags.append(term)

        # Also add individual words from query as potential tags
        for word in query_lower.split():
            if len(word) > 2 and word not in ["and", "the", "for", "with", "v1", "v2", "v3", "xl"]:
                if word not in found_tags:
                    found_tags.append(word)

        return found_tags

    def _format_params(self, params: Dict[str, Any]) -> str:
        """Format parameters for URL display."""
        return "&".join([f"{k}={v}" for k, v in params.items()])

    def _map_model_type(self, model_type: str) -> Optional[str]:
        """Map model type string to Civitai API format."""
        type_mapping = {
            "checkpoints": "Checkpoint",
            "loras": "LORA",
            "vae": "VAE",
            "controlnet": "Controlnet",
            "upscale_models": "Upscaler",
            "embeddings": "TextualInversion",
            "clip": "TextualInversion",
        }
        return type_mapping.get(model_type.lower())

    def print_debug_report(self, debug_info: Dict[str, Any]):
        """Print a formatted debug report to console."""
        print(f"{'=' * 50}")
        print("CIVITAI SEARCH DEBUGGER")
        print(f"{'=' * 50}")
        print(f'Search Term: "{debug_info["query"]}"')
        print(f"Model Type: {debug_info['model_type']}")
        print(f"NSFW Search: {debug_info['nsfw']}")
        print()

        # Show each strategy result
        for strategy, result in debug_info["results"].items():
            print(f"[{strategy.upper().replace('_', ' ')}]")
            if strategy == "tag_search":
                # Handle tag search results (list of results)
                for tag_result in result:
                    print(f"  Tag: {tag_result.get('tag', 'N/A')}")
                    print(f"  API URL: {tag_result.get('api_url', 'N/A')}")
                    print(f"  HTTP Code: {tag_result.get('http_code', 'N/A')}")
                    print(f"  Items Returned: {tag_result.get('items_returned', 'N/A')}")
                    print()
            else:
                print(f"API URL: {result.get('api_url', 'N/A')}")
                print(f"HTTP Code: {result.get('http_code', 'N/A')}")
                print(f"Items Returned: {result.get('items_returned', 'N/A')}")
                print()

        # Show diagnosis
        if debug_info["diagnosis"]:
            print("[DIAGNOSIS]")
            for diag in debug_info["diagnosis"]:
                print(f"  - {diag}")
            print()

        # Show suggestions
        print("[SUGGESTIONS]")
        for suggestion in debug_info["suggestions"]:
            print(f"  - {suggestion}")

        print(f"{'=' * 50}")
