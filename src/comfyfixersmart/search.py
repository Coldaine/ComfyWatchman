"""
Model Search Module for ComfyFixerSmart

Provides unified search interface for finding models across multiple sources.
Supports Civitai API search, Qwen-based autonomous search, and HuggingFace search.
Includes caching, validation, and result management.

Classes:
    ModelSearch: Main search coordinator
    CivitaiSearch: Civitai API search backend
    QwenSearch: Qwen-based autonomous search
    HuggingFaceSearch: HuggingFace model search
    SearchResult: Data class for search results

Functions:
    search_civitai: Convenience function for Civitai search
    search_with_qwen: Convenience function for Qwen search
"""

import hashlib
import json
import os
import re
import shlex
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

# Import adapters and feature flags
from .adapters import MODELSCOPE_AVAILABLE
from .config import config
from .logging import get_logger
from .state_manager import StateManager
from .utils import get_api_key, sanitize_filename, validate_and_sanitize_filename

# Conditionally import ModelScopeSearch
try:
    from .adapters.modelscope_search import ModelScopeSearch
except ImportError:
    ModelScopeSearch = None



@dataclass
class SearchResult:
    """Result of a model search operation.

    Note: status may be one of 'FOUND', 'NOT_FOUND', 'INVALID_FILENAME', 'ERROR',
    or 'UNCERTAIN'. 'UNCERTAIN' indicates candidates exist but need human review and
    should not be downloaded automatically.
    """

    status: str
    filename: str
    source: Optional[str] = None  # 'civitai', 'huggingface'
    civitai_id: Optional[int] = None
    version_id: Optional[int] = None
    civitai_name: Optional[str] = None
    version_name: Optional[str] = None
    download_url: Optional[str] = None
    confidence: Optional[str] = None  # 'exact', 'fuzzy'
    type: Optional[str] = None  # Model type for placement (e.g., 'loras', 'vae')
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class SearchBackend(ABC):
    """Abstract base class for search backends."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger(self.__class__.__name__)

    @abstractmethod
    def search(self, model_info: Dict[str, Any]) -> SearchResult:
        """Search for a model."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get backend name."""
        pass


class CivitaiSearch(SearchBackend):
    """Civitai API search backend."""

    def __init__(self, logger=None):
        super().__init__(logger)
        self.api_key = (
            config.search.civitai_api_key or get_api_key()
        )  # Fallback for old method
        self.base_url = "https://civitai.com/api/v1"

    def get_name(self) -> str:
        return "civitai"

    def search(self, model_info: Dict[str, Any]) -> SearchResult:
        """Search Civitai API for a model."""
        raw_filename = model_info["filename"]
        model_type = model_info.get("type", "")

        # Enhanced filename validation with early return for INVALID_FILENAME
        is_valid, sanitized_filename, error_reason = validate_and_sanitize_filename(
            raw_filename
        )
        if not is_valid:
            self.logger.warning(
                f"Invalid filename detected: {raw_filename} - {error_reason}"
            )
            return SearchResult(
                status="INVALID_FILENAME",
                filename=raw_filename,
                type=model_type,
                error_message=error_reason,
                metadata={
                    "validation_reason": error_reason,
                    "original_filename": raw_filename,
                },
            )

        # Normalize to basename independent of OS/path style
        filename = self._normalize_filename(sanitized_filename)

        # NEW: Try DirectIDBackend first
        try:
            from .civitai_tools.direct_id_backend import DirectIDBackend

            direct_backend = DirectIDBackend()

            # Extract name for lookup (remove file extension)
            name = filename.rsplit(".", 1)[0] if "." in filename else filename
            self.logger.info(f"Attempting DirectIDBackend lookup for: {name}")

            result = direct_backend.lookup_by_name(name)

            if result and result.status == "FOUND":
                self.logger.info(
                    f"DirectIDBackend found model: {result.civitai_name} (ID: {result.civitai_id})"
                )
                # Ensure the result has the correct filename and type from the request
                result.filename = filename
                if not result.type or result.type == "unknown":
                    result.type = model_type
                return result
            else:
                self.logger.debug(
                    f"DirectIDBackend lookup returned no results for: {name}"
                )
        except ImportError as e:
            self.logger.warning(
                f"DirectIDBackend not available: {e}, falling back to API search"
            )
        except Exception as e:
            self.logger.warning(
                f"DirectIDBackend lookup failed: {e}, falling back to API search"
            )

        # EXISTING: Fall back to API search
        # Clean filename for search
        query = self._prepare_search_query(filename)

        self.logger.info(f"Searching Civitai API: {query}")

        try:
            # Build search parameters
            params = {"query": query, "limit": 10, "sort": "Highest Rated"}

            # Add type filtering if applicable
            type_filter = self._get_type_filter(model_type)
            if type_filter:
                params["types"] = type_filter

            response = requests.get(
                f"{self.base_url}/models",
                params=params,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30,
            )

            if response.status_code != 200:
                return SearchResult(
                    status="ERROR",
                    filename=filename,
                    error_message=f"API error: {response.status_code}",
                )

            results = response.json().get("items", [])
            if not results:
                self.logger.info(
                    "Simple Civitai search returned zero results, attempting multi-strategy cascade"
                )
                cascade_results = self.search_multi_strategy(model_info)
                if cascade_results:
                    best_result = cascade_results[0]
                    best_result.filename = filename
                    if not best_result.type:
                        best_result.type = model_type
                    if best_result.metadata is None:
                        best_result.metadata = {}
                    best_result.metadata["search_attempts"] = max(
                        2, best_result.metadata.get("search_attempts", 1)
                    )
                    self.logger.info(
                        "Multi-strategy found result after empty simple search: %s (ID: %s)",
                        best_result.civitai_name,
                        best_result.civitai_id,
                    )
                    return best_result

                # Hash fallback: Try to find local file and use its hash for lookup
                hash_result = self._try_hash_fallback(model_info)
                if hash_result:
                    hash_result.filename = filename
                    if not hash_result.type:
                        hash_result.type = model_type
                    if hash_result.metadata is None:
                        hash_result.metadata = {}
                    hash_result.metadata["search_attempts"] = max(
                        3, hash_result.metadata.get("search_attempts", 1)
                    )
                    self.logger.info(
                        "Hash fallback found result after empty simple + multi-strategy search: %s (ID: %s)",
                        hash_result.civitai_name,
                        hash_result.civitai_id,
                    )
                    return hash_result

                return SearchResult(
                    status="NOT_FOUND",
                    filename=filename,
                    type=model_type,
                    metadata={
                        "search_attempts": 3,
                        "reason": "Simple + multi-strategy + hash fallback search returned no results",
                    },
                )

            # Find best match
            best_match = self._find_best_match(results, filename)

            if best_match:
                result_obj, version = best_match
                return self._create_result_from_match(
                    result_obj, version, filename, model_type, "exact"
                )
            else:
                self.logger.info(
                    "Simple Civitai search returned candidates but no exact filename match; "
                    "attempting multi-strategy cascade"
                )
                cascade_results = self.search_multi_strategy(model_info)

                if cascade_results:
                    best_result = cascade_results[0]
                    best_result.filename = filename
                    if not best_result.type:
                        best_result.type = model_type
                    if best_result.metadata is None:
                        best_result.metadata = {}
                    best_result.metadata["search_attempts"] = max(
                        2, best_result.metadata.get("search_attempts", 1)
                    )
                    self.logger.info(
                        "Multi-strategy found result after no exact match: %s (ID: %s)",
                        best_result.civitai_name,
                        best_result.civitai_id,
                    )
                    return best_result

                # Hash fallback: Try to find local file and use its hash for lookup
                hash_result = self._try_hash_fallback(model_info)
                if hash_result:
                    hash_result.filename = filename
                    if not hash_result.type:
                        hash_result.type = model_type
                    if hash_result.metadata is None:
                        hash_result.metadata = {}
                    hash_result.metadata["search_attempts"] = max(
                        3, hash_result.metadata.get("search_attempts", 1)
                    )
                    self.logger.info(
                        "Hash fallback found result after no exact match: %s (ID: %s)",
                        hash_result.civitai_name,
                        hash_result.civitai_id,
                    )
                    return hash_result

                top = results[0]
                meta = {
                    "search_attempts": 3,
                    "reason": "No exact filename match after simple + multi-strategy + hash fallback search",
                    "top_candidate": {
                        "id": top.get("id"),
                        "name": top.get("name"),
                        "type": top.get("type"),
                    },
                }
                return SearchResult(
                    status="NOT_FOUND",
                    filename=filename,
                    type=model_type,
                    metadata=meta,
                )

        except Exception as e:
            self.logger.error(f"Civitai search error: {e}")
            return SearchResult(
                status="ERROR", filename=filename, type=model_type, error_message=str(e)
            )

    def search_by_id(self, model_id: int) -> Optional[SearchResult]:
        """
        Direct lookup bypassing search API.
        Uses /api/v1/models/{id} endpoint.
        Returns SearchResult with 100% confidence on success.
        """
        self.logger.info(f"Searching by direct ID: {model_id}")

        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = requests.get(
                f"{self.base_url}/models/{model_id}", headers=headers, timeout=30
            )

            if response.status_code != 200:
                self.logger.error(f"Direct ID lookup failed: {response.status_code}")
                return None

            model_data = response.json()

            # Get the first version for download (typically the latest)
            versions = model_data.get("modelVersions", [])
            if not versions:
                self.logger.warning(f"No versions found for model ID {model_id}")
                return None

            # Use latest version
            latest_version = versions[0]
            latest_version_id = latest_version["id"]

            # Find primary file or first available file
            primary_file = None
            for file_info in latest_version.get("files", []):
                if file_info.get("primary", False):
                    primary_file = file_info
                    break

            # If no primary file found, just use first file
            if not primary_file and latest_version.get("files"):
                primary_file = latest_version["files"][0]

            if not primary_file:
                self.logger.warning(
                    f"No files found for model ID {model_id} version {latest_version_id}"
                )
                return None

            filename = primary_file.get("name", f"model_{model_id}.safetensors")
            model_name = model_data.get("name", f"Model {model_id}")

            return SearchResult(
                status="FOUND",
                filename=filename,
                source="civitai",
                civitai_id=model_id,
                version_id=latest_version_id,
                civitai_name=model_name,
                version_name=latest_version.get("name", f"Version {latest_version_id}"),
                download_url=f"https://civitai.com/api/download/models/{latest_version_id}",
                confidence="exact",  # 100% confidence for direct ID lookup
                type=self._infer_model_type_from_data(model_data),
                metadata={
                    "search_attempts": 1,
                    "found_by": "direct_id",
                    "nsfw_level": model_data.get(
                        "nsfwLevel", 1
                    ),  # PG=1, PG13=2, R=4, X=8, XXX=16
                },
            )

        except Exception as e:
            self.logger.error(f"Direct ID lookup error for model {model_id}: {e}")
            return None

    def search_multi_strategy(self, model_ref: Dict[str, Any]) -> List[SearchResult]:
        """
        Enhanced cascade through multiple search strategies for 100% NSFW model discovery:
        1. Check known_models.json for direct ID
        2. Try NSFW-specific multi-level search strategies
        3. Try query search with different NSFW parameter combinations
        4. Try advanced tag-based search with NSFW tags
        5. Try creator-based search (if creator known)
        6. Try fallback mechanisms for hidden NSFW content
        Return scored candidates sorted by confidence.
        """
        results = []

        # Strategy 1: Check known_models.json for direct ID using DirectIDBackend
        from .civitai_tools.direct_id_backend import DirectIDBackend

        direct_backend = DirectIDBackend()

        # Try to find by model name first
        filename = model_ref.get("filename", "")
        if filename:
            # Extract model name from filename for lookup
            import re

            name_for_lookup = re.sub(
                r"\.safetensors|\.ckpt|\.pt|\.bin|\.pth|v\d+\.\d+|v\d+",
                "",
                filename,
                flags=re.IGNORECASE,
            )
            name_for_lookup = (
                name_for_lookup.replace("_", " ").replace("-", " ").strip()
            )

            known_result = direct_backend.lookup_by_name(name_for_lookup)
            if known_result:
                results.append(known_result)
                # Sort results by confidence and return early since known result is most confident
                return sorted(
                    results,
                    key=lambda x: self._calculate_confidence_score(x),
                    reverse=True,
                )

        # Strategy 2: Enhanced NSFW-specific multi-level search
        nsfw_results = self._search_nsfw_multi_level(model_ref)
        results.extend(nsfw_results)

        if not results:
            # Strategy 3: Try query search with different NSFW parameter combinations
            nsfw_param_results = self._search_nsfw_parameter_combinations(model_ref)
            results.extend(nsfw_param_results)

        if not results:
            # Strategy 4: Try advanced NSFW tag-based search
            tag_results = self._search_by_nsfw_tags(model_ref)
            results.extend(tag_results)

        if not results and model_ref.get("creator"):
            # Strategy 5: Try creator-based search (if creator known)
            creator_results = self._search_by_creator(model_ref)
            results.extend(creator_results)

        if not results:
            # Strategy 6: Try fallback mechanisms for hidden NSFW content
            fallback_results = self._search_hidden_nsfw_fallbacks(model_ref)
            results.extend(fallback_results)

        # Sort results by confidence or relevance
        return sorted(
            results, key=lambda x: self._calculate_confidence_score(x), reverse=True
        )

    def _search_nsfw_multi_level(self, model_ref: Dict[str, Any]) -> List[SearchResult]:
        """Enhanced NSFW search with multiple strategies for 100% discovery reliability."""
        results = []
        filename = model_ref["filename"]
        query = self._prepare_search_query(filename)

        self.logger.info(f"Starting enhanced NSFW multi-level search for: {query}")

        # Strategy 2.1: Search with explicit NSFW=true and different sort orders
        nsfw_strategies = [
            {"nsfw": "true", "sort": "Highest Rated"},
            {"nsfw": "true", "sort": "Most Downloaded"},
            {"nsfw": "true", "sort": "Newest"},
            {"nsfw": "true", "sort": "Most Liked"},
        ]

        for strategy in nsfw_strategies:
            strategy_results = self._search_with_nsfw_strategy(model_ref, strategy)
            results.extend(strategy_results)
            if (
                results
            ):  # If we found results, continue to next strategy but keep accumulating
                break

        # Strategy 2.2: If no results, try without NSFW filter but with NSFW tags
        if not results:
            no_filter_results = self._search_without_nsfw_filter_with_tags(model_ref)
            results.extend(no_filter_results)

        # Strategy 2.3: Try with different NSFW levels if available
        if not results:
            nsfw_level_results = self._search_by_nsfw_levels(model_ref)
            results.extend(nsfw_level_results)

        return results

    def _search_with_nsfw_strategy(
        self, model_ref: Dict[str, Any], strategy: Dict[str, str]
    ) -> List[SearchResult]:
        """Search using specific NSFW strategy parameters."""
        filename = model_ref["filename"]
        model_type = model_ref.get("type", "")
        query = self._prepare_search_query(filename)

        try:
            params = {
                "query": query,
                "limit": 20,  # Increased limit for better coverage
                "sort": strategy.get("sort", "Highest Rated"),
            }

            if strategy.get("nsfw"):
                params["nsfw"] = strategy["nsfw"]

            type_filter = self._get_type_filter(model_type)
            if type_filter:
                params["types"] = type_filter

            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = requests.get(
                f"{self.base_url}/models", params=params, headers=headers, timeout=30
            )

            if response.status_code != 200:
                return []

            data = response.json()
            results = []

            for item in data.get("items", []):
                # Check if model has NSFW content
                nsfw_level = item.get("nsfwLevel", 1)
                if nsfw_level >= 2:  # PG13 or higher
                    for version in item.get("modelVersions", []):
                        for file_info in version.get("files", []):
                            if self._filename_matches(
                                file_info.get("name", ""), filename
                            ):
                                result = self._create_result_from_match(
                                    item, version, filename, model_type, "fuzzy"
                                )
                                # Add NSFW metadata
                                if result.metadata:
                                    result.metadata["nsfw_level"] = nsfw_level
                                    result.metadata["search_strategy"] = strategy
                                else:
                                    result.metadata = {
                                        "nsfw_level": nsfw_level,
                                        "search_strategy": strategy,
                                    }
                                results.append(result)

            return results

        except Exception as e:
            self.logger.error(f"NSFW strategy search failed: {e}")
            return []

    def _search_without_nsfw_filter_with_tags(
        self, model_ref: Dict[str, Any]
    ) -> List[SearchResult]:
        """Search without NSFW filter but include NSFW-related tags in query."""
        filename = model_ref["filename"]
        model_type = model_ref.get("type", "")
        base_query = self._prepare_search_query(filename)

        # Add NSFW-related keywords to broaden search
        nsfw_keywords = ["nsfw", "adult", "explicit", "nude", "erotic"]
        enhanced_queries = [base_query] + [f"{base_query} {kw}" for kw in nsfw_keywords]

        results = []
        for query in enhanced_queries:
            try:
                params = {"query": query, "limit": 15, "sort": "Highest Rated"}

                type_filter = self._get_type_filter(model_type)
                if type_filter:
                    params["types"] = type_filter

                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                response = requests.get(
                    f"{self.base_url}/models",
                    params=params,
                    headers=headers,
                    timeout=30,
                )

                if response.status_code != 200:
                    continue

                data = response.json()
                for item in data.get("items", []):
                    nsfw_level = item.get("nsfwLevel", 1)
                    if nsfw_level >= 2:  # Only include potentially NSFW content
                        for version in item.get("modelVersions", []):
                            for file_info in version.get("files", []):
                                if self._filename_matches(
                                    file_info.get("name", ""), filename
                                ):
                                    result = self._create_result_from_match(
                                        item, version, filename, model_type, "fuzzy"
                                    )
                                    if result.metadata:
                                        result.metadata["nsfw_level"] = nsfw_level
                                        result.metadata["enhanced_query"] = query
                                    else:
                                        result.metadata = {
                                            "nsfw_level": nsfw_level,
                                            "enhanced_query": query,
                                        }
                                    results.append(result)

            except Exception as e:
                self.logger.error(f"Enhanced query search failed for '{query}': {e}")
                continue

        return results

    def _search_by_nsfw_levels(self, model_ref: Dict[str, Any]) -> List[SearchResult]:
        """Search specifically targeting different NSFW levels."""
        filename = model_ref["filename"]
        model_type = model_ref.get("type", "")
        query = self._prepare_search_query(filename)

        results = []

        # Try different NSFW level combinations
        nsfw_level_strategies = [
            {"nsfwLevel": 2},  # PG13
            {"nsfwLevel": 4},  # R
            {"nsfwLevel": 8},  # X
            {"nsfwLevel": 16},  # XXX
        ]

        for level_strategy in nsfw_level_strategies:
            try:
                params = {
                    "query": query,
                    "limit": 10,
                    "sort": "Highest Rated",
                    **level_strategy,
                }

                type_filter = self._get_type_filter(model_type)
                if type_filter:
                    params["types"] = type_filter

                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                response = requests.get(
                    f"{self.base_url}/models",
                    params=params,
                    headers=headers,
                    timeout=30,
                )

                if response.status_code != 200:
                    continue

                data = response.json()
                for item in data.get("items", []):
                    for version in item.get("modelVersions", []):
                        for file_info in version.get("files", []):
                            if self._filename_matches(
                                file_info.get("name", ""), filename
                            ):
                                result = self._create_result_from_match(
                                    item, version, filename, model_type, "fuzzy"
                                )
                                if result.metadata:
                                    result.metadata["target_nsfw_level"] = (
                                        level_strategy["nsfwLevel"]
                                    )
                                    result.metadata["actual_nsfw_level"] = item.get(
                                        "nsfwLevel", 1
                                    )
                                else:
                                    result.metadata = {
                                        "target_nsfw_level": level_strategy[
                                            "nsfwLevel"
                                        ],
                                        "actual_nsfw_level": item.get("nsfwLevel", 1),
                                    }
                                results.append(result)

            except Exception as e:
                self.logger.error(
                    f"NSFW level search failed for level {level_strategy}: {e}"
                )
                continue

        return results

    def _filename_matches(self, candidate: str, target: str) -> bool:
        """Enhanced filename matching for NSFW models."""
        candidate_lower = candidate.lower()
        target_lower = target.lower()

        # Exact match
        if candidate_lower == target_lower:
            return True

        # Starts with same prefix (more lenient for NSFW models)
        candidate_prefix = candidate_lower.split(".")[0]
        target_prefix = target_lower.split(".")[0]

        if candidate_prefix.startswith(target_prefix) or target_prefix.startswith(
            candidate_prefix
        ):
            return True

        # Fuzzy matching for common NSFW naming patterns
        import re

        # Remove version numbers and common separators
        candidate_clean = re.sub(r"v\d+|\d+\.\d+|_|-|\s+", "", candidate_prefix)
        target_clean = re.sub(r"v\d+|\d+\.\d+|_|-|\s+", "", target_prefix)

        return candidate_clean == target_clean

    def _search_with_nsfw_param(
        self, model_ref: Dict[str, Any], nsfw: bool = True
    ) -> List[SearchResult]:
        """Helper method to search with nsfw parameter."""
        filename = model_ref["filename"]
        model_type = model_ref.get("type", "")
        query = self._prepare_search_query(filename)

        self.logger.info(f"Searching with nsfw={nsfw}: {query}")

        try:
            params = {"query": query, "limit": 10, "sort": "Highest Rated"}

            if nsfw:
                params["nsfw"] = "true"

            type_filter = self._get_type_filter(model_type)
            if type_filter:
                params["types"] = type_filter

            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = requests.get(
                f"{self.base_url}/models", params=params, headers=headers, timeout=30
            )

            if response.status_code != 200:
                return []

            data = response.json()
            results = []

            for item in data.get("items", []):
                for version in item.get("modelVersions", []):
                    for file_info in version.get("files", []):
                        if (
                            file_info.get("name", "")
                            .lower()
                            .startswith(query.lower().split()[0])
                        ):
                            result = self._create_result_from_match(
                                item, version, filename, model_type, "fuzzy"
                            )
                            results.append(result)

            return results

        except Exception as e:
            self.logger.error(f"Search with nsfw={nsfw} failed: {e}")
            return []

    def _search_by_tags(self, model_ref: Dict[str, Any]) -> List[SearchResult]:
        """
        Extract potential tags from filename.
        Search using /api/v1/models?tag={tag}&types={type}&nsfw=true
        """
        filename = model_ref["filename"]
        model_type = model_ref.get("type", "")
        query = self._prepare_search_query(filename)

        # Extract potential tags from the query
        potential_tags = self._extract_tags_from_query(query)
        results = []

        for tag in potential_tags:
            try:
                params = {"tag": tag, "limit": 5, "nsfw": "true"}

                type_filter = self._get_type_filter(model_type)
                if type_filter:
                    params["types"] = type_filter

                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                response = requests.get(
                    f"{self.base_url}/models",
                    params=params,
                    headers=headers,
                    timeout=30,
                )

                if response.status_code != 200:
                    continue

                data = response.json()
                for item in data.get("items", []):
                    for version in item.get("modelVersions", []):
                        for file_info in version.get("files", []):
                            result = self._create_result_from_match(
                                item, version, filename, model_type, "fuzzy"
                            )
                            # Add tag-based source metadata
                            if result.metadata:
                                result.metadata["tag_source"] = tag
                            else:
                                result.metadata = {"tag_source": tag}
                            results.append(result)

            except Exception as e:
                self.logger.error(f"Tag search failed for tag '{tag}': {e}")
                continue

        return results

    def _search_by_creator(self, model_ref: Dict[str, Any]) -> List[SearchResult]:
        """
        Search models by creator username.
        Uses /api/v1/models?username={username}&types={type}&nsfw=true
        """
        filename = model_ref["filename"]
        model_type = model_ref.get("type", "")
        creator = model_ref.get("creator", "")

        if not creator:
            return []

        self.logger.info(f"Searching by creator: {creator}")

        try:
            params = {"username": creator, "limit": 10, "nsfw": "true"}

            type_filter = self._get_type_filter(model_type)
            if type_filter:
                params["types"] = type_filter

            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = requests.get(
                f"{self.base_url}/models", params=params, headers=headers, timeout=30
            )

            if response.status_code != 200:
                return []

            data = response.json()
            results = []

            for item in data.get("items", []):
                for version in item.get("modelVersions", []):
                    result = self._create_result_from_match(
                        item, version, filename, model_type, "fuzzy"
                    )
                    if result.metadata:
                        result.metadata["creator_search"] = creator
                    else:
                        result.metadata = {"creator_search": creator}
                    results.append(result)

            return results

        except Exception as e:
            self.logger.error(f"Creator search failed for '{creator}': {e}")
            return []

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
            if term in query_lower:
                found_tags.append(term)

        # Also add individual words from query as potential tags
        for word in query_lower.split():
            if len(word) > 2 and word not in [
                "and",
                "the",
                "for",
                "with",
                "v1",
                "v2",
                "v3",
                "xl",
            ]:
                if word not in found_tags:
                    found_tags.append(word)

        return found_tags

    def _calculate_confidence_score(self, result: SearchResult) -> int:
        """Calculate confidence score for a search result."""
        if result.confidence == "exact":
            return 100
        elif result.confidence == "fuzzy":
            # Boost score if found by direct ID or creator search
            if result.metadata:
                if result.metadata.get("found_by") == "direct_id":
                    return 90
                elif result.metadata.get("creator_search"):
                    return 70
                elif result.metadata.get("tag_source"):
                    return 60
            return 50
        return 30

    def _infer_model_type_from_data(self, model_data: Dict[str, Any]) -> str:
        """Infer model type from model data."""
        model_type = model_data.get("type", "Unknown")
        type_mapping = {
            "Checkpoint": "checkpoints",
            "LORA": "loras",
            "VAE": "vae",
            "Controlnet": "controlnet",
            "Upscaler": "upscale_models",
            "TextualInversion": "clip",
        }
        return type_mapping.get(model_type, "unknown")

    def _prepare_search_query(self, filename: str) -> str:
        """Prepare filename for search query."""
        # Normalize separators and remove extension
        base = self._normalize_filename(filename)
        # Remove common extensions
        base = re.sub(
            r"\.(safetensors|ckpt|pth|pt|bin|onnx)$", "", base, flags=re.IGNORECASE
        )
        # Replace underscores, backslashes, forward slashes, and dots with spaces
        query = re.sub(r"[\\/_.]+", " ", base)
        return query.strip()

    def _get_type_filter(self, model_type: str) -> Optional[str]:
        """Get Civitai type filter from model type."""
        type_mapping = {
            "checkpoints": "Checkpoint",
            "loras": "LORA",
            "vae": "VAE",
            "controlnet": "Controlnet",
            "upscale_models": "Upscaler",
            "clip": "TextualInversion",  # Approximation
            "embeddings": "TextualInversion",
            "unet": "Checkpoint",  # Approximation
        }
        return type_mapping.get(model_type)

    def _find_best_match(
        self, results: List[Dict], target_filename: str
    ) -> Optional[Tuple[Dict, Dict]]:
        """Find the best matching result with the exact modelVersion that contains the file."""
        target_lower = target_filename.lower()
        for result in results:
            for version in result.get("modelVersions", []):
                for file_info in version.get("files", []):
                    if file_info.get("name", "").lower() == target_lower:
                        return result, version
        return None

    def _create_result_from_match(
        self,
        result: Dict,
        version: Dict,
        filename: str,
        model_type: str,
        confidence: str,
    ) -> SearchResult:
        """Create SearchResult from an exact Civitai API match and its specific version."""
        return SearchResult(
            status="FOUND",
            filename=filename,
            source="civitai",
            civitai_id=result.get("id"),
            version_id=version.get("id"),
            civitai_name=result.get("name"),
            version_name=version.get("name"),
            download_url=f"https://civitai.com/api/download/models/{version.get('id')}",
            confidence=confidence,
            type=model_type,
            metadata={"search_attempts": 1},
        )

    def _normalize_filename(self, name: str) -> str:
        """Normalize a possibly path-like filename using both separators and return the basename."""
        try:
            parts = re.split(r"[\\/]+", name)
            return parts[-1] if parts else name
        except Exception:
            return name

    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """
        Calculate SHA256 hash of a local model file efficiently using streaming.

        Args:
            file_path: Path to the model file

        Returns:
            SHA256 hash as hex string, or None if calculation fails
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files efficiently
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.logger.warning(f"Failed to calculate hash for {file_path}: {e}")
            return None

    def search_by_hash(self, file_path: str, filename: str) -> Optional[SearchResult]:
        """
        Search Civitai using SHA256 hash via /api/v1/model-versions/by-hash/{sha256} endpoint.

        Args:
            file_path: Path to local file for hash calculation
            filename: Original filename for context

        Returns:
            SearchResult if found by hash, None otherwise
        """
        self.logger.info(f"Attempting hash lookup for file: {filename}")

        # Calculate hash of local file
        file_hash = self._calculate_file_hash(file_path)
        if not file_hash:
            self.logger.warning(f"Could not calculate hash for {file_path}")
            return None

        self.logger.info(f"Calculated SHA256 hash: {file_hash[:16]}... for {filename}")

        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # Use the Civitai hash lookup endpoint
            response = requests.get(
                f"{self.base_url}/model-versions/by-hash/{file_hash}",
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()

                # Extract model information from hash lookup result
                model_id = data.get("modelId")
                version_id = data.get("id")
                model_name = data.get("model", {}).get("name", "Unknown Model")
                version_name = data.get("name", f"Version {version_id}")

                # Get the primary file information
                primary_file = data.get("files", [{}])[0] if data.get("files") else {}

                self.logger.info(
                    f"Hash lookup successful: Found {model_name} (ID: {model_id}, Version: {version_id})"
                )

                return SearchResult(
                    status="FOUND",
                    filename=filename,  # Use original filename from search
                    source="civitai",
                    civitai_id=model_id,
                    version_id=version_id,
                    civitai_name=model_name,
                    version_name=version_name,
                    download_url=f"https://civitai.com/api/download/models/{version_id}",
                    confidence="exact",  # Hash match is 100% confidence
                    type=self._infer_model_type_from_data(data.get("model", {})),
                    metadata={
                        "search_attempts": 1,
                        "found_by": "hash_lookup",
                        "hash": file_hash,
                        "hash_lookup_endpoint": f"/api/v1/model-versions/by-hash/{file_hash}",
                    },
                )
            elif response.status_code == 404:
                self.logger.info(f"No model found with hash {file_hash[:16]}...")
                return None
            else:
                self.logger.warning(
                    f"Hash lookup API error: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Hash lookup failed for {file_hash[:16]}...: {e}")
            return None

    def _try_hash_fallback(self, model_info: Dict[str, Any]) -> Optional[SearchResult]:
        """
        Try hash-based fallback when other search methods fail.

        This method checks if we have a local file path and attempts hash lookup
        using the Civitai /api/v1/model-versions/by-hash/{sha256} endpoint.

        Args:
            model_info: Dictionary containing model information

        Returns:
            SearchResult if hash lookup succeeds, None otherwise
        """
        filename = model_info["filename"]

        # Check if we have a local file path to work with
        # The model_info might contain a 'local_path' field, or we might need to
        # construct one based on the ComfyUI directory structure
        local_path = model_info.get("local_path")

        if not local_path:
            # Try to construct local path based on ComfyUI directory
            # This is a common pattern in the codebase
            comfyui_root = model_info.get(
                "comfyui_root", "/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable"
            )
            model_type = model_info.get("type", "checkpoints")

            # Map model types to their directory structure in ComfyUI
            type_to_dir = {
                "checkpoints": "models/checkpoints",
                "loras": "models/loras",
                "vae": "models/vae",
                "controlnet": "models/controlnet",
                "upscale_models": "models/upscale_models",
                "embeddings": "models/embeddings",
                "clip": "models/clip",
            }

            model_dir = type_to_dir.get(model_type, "models/checkpoints")
            local_path = f"{comfyui_root}/{model_dir}/{filename}"

        self.logger.info(f"Attempting hash fallback for local file: {local_path}")

        # Check if file exists
        if not os.path.exists(local_path):
            self.logger.debug(f"Local file not found for hash lookup: {local_path}")
            return None

        # Check file size - skip very small files that are unlikely to be model files
        try:
            file_size = os.path.getsize(local_path)
            if file_size < 1024 * 1024:  # Less than 1MB
                self.logger.debug(
                    f"File too small for hash lookup ({file_size} bytes): {local_path}"
                )
                return None
        except OSError as e:
            self.logger.warning(f"Could not get file size for {local_path}: {e}")
            return None

        # Attempt hash lookup
        return self.search_by_hash(local_path, filename)


class QwenSearch(SearchBackend):
    """Qwen-based agentic search backend with smart pattern recognition."""

    def __init__(
        self,
        temp_dir: Optional[str] = None,
        cache_dir: Optional[str] = None,
        logger=None,
    ):
        super().__init__(logger)
        self.temp_dir = Path(temp_dir or config.temp_dir)
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        self.cache_dir = (
            Path(cache_dir) if cache_dir else Path(config.temp_dir) / "qwen_cache"
        )
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.qwen_binary = config.search.qwen_binary or os.environ.get(
            "QWEN_BINARY", "qwen"
        )

        # Smart pattern recognition for known HF models
        self.hf_model_patterns = self._init_hf_patterns()
        self.enable_pattern_recognition = True

    def get_name(self) -> str:
        return "qwen"

    def _init_hf_patterns(self) -> Dict[str, List[str]]:
        """Initialize known HuggingFace model patterns for smart recognition."""
        return {
            # SAM (Segment Anything Model) variants
            "sam_patterns": [
                r"sam_.*\.pth$",
                r"sam_.*\.pt$",
                r"segment_anything.*\.pth$",
                r"facebook_sam.*\.pth$",
            ],
            # RIFE (Real-time Intermediate Flow Estimation) models
            "rife_patterns": [
                r"rife_.*\.pth$",
                r"rife_.*\.pt$",
                r"rife.*\.pth$",
                r"rife.*\.pt$",
            ],
            # ControlNet and control models
            "controlnet_patterns": [
                r"control_.*\.pth$",
                r"controlnet.*\.pth$",
                r"control_net.*\.pth$",
                r"openpose.*\.pth$",
                r"canny.*\.pth$",
            ],
            # Upscaling models commonly on HF
            "upscaler_patterns": [
                r".*nmkd.*\.pth$",
                r".*esrgan.*\.pth$",
                r".*realesrgan.*\.pth$",
                r".*lanczos.*\.pth$",
                r".*4x.*\.pth$",
            ],
            # CLIP and text encoder models
            "clip_patterns": [
                r"clip.*\.pt$",
                r"clip.*\.pth$",
                r"text_encoder.*\.pth$",
                r"openai.*clip.*\.pth$",
            ],
            # VAE models commonly on HF
            "vae_patterns": [
                r".*kl_f8.*\.pt$",
                r".*kl_f16.*\.pth$",
                r".*vae.*\.pt$",
                r".*variational.*\.pt$",
            ],
            # Common HF model prefixes
            "hf_prefixes": [
                "facebook_",
                "microsoft_",
                "openai_",
                "google_",
                "stability_",
                "runwayml_",
                "cs3244-",
                "lian_",
                "nitrosocke_",
                "gsdf_",
                "taming-transformers-",
            ],
            # Scientific/research model indicators
            "research_patterns": [
                r".*diffusers.*\.pt$",
                r".*transformers.*\.pt$",
                r".*huggingface.*\.pt$",
                r".*checkpoint.*\.safetensors$",
            ],
        }

    def _detect_hf_pattern(self, filename: str) -> Optional[str]:
        """Detect if filename matches known HuggingFace model patterns.

        Returns:
            Pattern name if matched, None otherwise
        """
        filename_lower = filename.lower()

        # Check against regex patterns
        for pattern_type, patterns in self.hf_model_patterns.items():
            if pattern_type.endswith("_patterns"):
                for pattern in patterns:
                    if re.match(pattern, filename_lower, re.IGNORECASE):
                        self.logger.info(
                            f"Pattern match: {filename} matches {pattern_type} pattern: {pattern}"
                        )
                        return pattern_type

        # Check against prefixes
        hf_prefixes = self.hf_model_patterns.get("hf_prefixes", [])
        for prefix in hf_prefixes:
            if filename_lower.startswith(prefix.lower()):
                self.logger.info(
                    f"Prefix match: {filename} starts with HF prefix: {prefix}"
                )
                return "hf_prefix_match"

        return None

    def _extract_repos_from_web_results(
        self, web_results: List[Dict[str, Any]], filename: str
    ) -> List[Dict[str, Any]]:
        """Extract repository information from web search results.

        Args:
            web_results: Results from web search
            filename: Target model filename

        Returns:
            List of repository candidates with metadata
        """
        repos = []
        target_base = filename.rsplit(".", 1)[0].lower()

        for result in web_results:
            url = result.get("url", "")
            title = result.get("title", "")
            content = result.get("content", "")

            # Look for HuggingFace repository URLs
            if "huggingface.co" in url:
                # Extract repo information from URL
                repo_match = re.search(r"huggingface\.co/([^/]+)/([^/?]+)", url)
                if repo_match:
                    username = repo_match.group(1)
                    repo_name = repo_match.group(2)

                    # Calculate relevance score
                    score = self._calculate_web_repo_score(
                        username, repo_name, target_base, title, content
                    )

                    repo_info = {
                        "type": "huggingface",
                        "username": username,
                        "repo_name": repo_name,
                        "full_name": f"{username}/{repo_name}",
                        "url": url,
                        "title": title,
                        "content": content[:500],  # Limit content length
                        "score": score,
                        "search_metadata": result.get("search_metadata", {}),
                    }
                    repos.append(repo_info)

            # Look for GitHub repository URLs
            elif "github.com" in url:
                # Extract repo information from GitHub URL
                repo_match = re.search(r"github\.com/([^/]+)/([^/?]+)", url)
                if repo_match:
                    username = repo_match.group(1)
                    repo_name = repo_match.group(2)

                    score = self._calculate_web_repo_score(
                        username, repo_name, target_base, title, content
                    )

                    repo_info = {
                        "type": "github",
                        "username": username,
                        "repo_name": repo_name,
                        "full_name": f"{username}/{repo_name}",
                        "url": url,
                        "title": title,
                        "content": content[:500],
                        "score": score,
                        "search_metadata": result.get("search_metadata", {}),
                    }
                    repos.append(repo_info)

        # Sort by score and return top candidates
        repos.sort(key=lambda x: x["score"], reverse=True)
        return repos[:10]  # Limit to top 10 candidates

    def _calculate_web_repo_score(
        self, username: str, repo_name: str, target_base: str, title: str, content: str
    ) -> int:
        """Calculate relevance score for a repository based on web search results.

        Args:
            username: Repository owner username
            repo_name: Repository name
            target_base: Target model filename base
            title: Page title from search result
            content: Page content snippet

        Returns:
            Relevance score (0-100)
        """
        score = 0
        target_lower = target_base.lower()
        title_lower = title.lower()
        content_lower = content.lower()

        # Base score for repository format
        score += 20

        # Score based on repo name similarity
        repo_lower = repo_name.lower()
        if repo_lower == target_lower:
            score += 50  # Exact match
        elif target_lower in repo_lower or repo_lower in target_lower:
            score += 35  # Contains match
        else:
            # Check for partial word matches
            target_words = set(target_lower.split("_"))
            repo_words = set(repo_lower.split("_"))
            common_words = target_words.intersection(repo_words)
            if common_words:
                score += 25

        # Score based on title relevance
        if target_lower in title_lower:
            score += 15

        # Score based on content relevance
        if target_lower in content_lower:
            score += 10

        # Bonus for known model-related keywords in content
        model_keywords = ["model", "checkpoint", "safetensors", "diffusion", "ai", "ml"]
        content_words = content_lower.split()
        for keyword in model_keywords:
            if keyword in content_words:
                score += 5

        # Bonus for file extension mentions
        model_extensions = [".safetensors", ".ckpt", ".pt", ".bin", ".pth"]
        for ext in model_extensions:
            if ext in content_lower:
                score += 3

        return min(score, 100)  # Cap at 100

    def _format_web_search_results(
        self, repo_candidates: List[Dict[str, Any]], filename: str
    ) -> Dict[str, Any]:
        """Format web search results for Qwen consumption.

        Args:
            repo_candidates: Repository candidates from web search
            filename: Target model filename

        Returns:
            Formatted results for Qwen
        """
        if not repo_candidates:
            return {
                "status": "NOT_FOUND",
                "metadata": {
                    "web_search_attempts": 0,
                    "reason": "No repositories found via web search",
                    "filename": filename,
                },
            }

        # Format top candidates for Qwen
        formatted_candidates = []
        for repo in repo_candidates[:5]:  # Top 5 candidates
            candidate = {
                "source": repo["type"],
                "repository": repo["full_name"],
                "url": repo["url"],
                "title": repo["title"],
                "match_score": repo["score"] / 100.0,  # Normalize to 0-1
                "confidence": "medium" if repo["score"] > 70 else "low",
                "metadata": {
                    "username": repo["username"],
                    "repo_name": repo["repo_name"],
                    "search_strategy": repo.get("search_metadata", {}),
                },
            }
            formatted_candidates.append(candidate)

        return {
            "status": "UNCERTAIN",
            "candidates": formatted_candidates,
            "reason": f"Found {len(repo_candidates)} repositories via web search, manual verification needed",
            "metadata": {
                "web_search_attempts": len(repo_candidates),
                "filename": filename,
                "top_candidate_score": (
                    repo_candidates[0]["score"] if repo_candidates else 0
                ),
            },
        }

    def _is_likely_hf_model(
        self, filename: str, model_type: str = ""
    ) -> Tuple[bool, str]:
        """Determine if model is likely hosted on HuggingFace.

        Args:
            filename: Model filename
            model_type: Model type from workflow

        Returns:
            Tuple of (is_likely_hf, reason)
        """
        pattern_match = self._detect_hf_pattern(filename)

        if pattern_match:
            return True, f"Pattern match: {pattern_match}"

        # Check model type indicators
        if model_type.lower() in ["checkpoints", "controlnet", "embeddings"]:
            # Many base models and controlnets are on HF
            if any(
                keyword in filename.lower()
                for keyword in [
                    "controlnet",
                    "clip",
                    "text_encoder",
                    "transformer",
                    "unet",
                ]
            ):
                return True, "Model type and filename suggest HF hosting"

        # Check for common HF repository patterns in filename
        hf_repo_patterns = [
            "stabilityai",
            "facebookresearch",
            "microsoft",
            "openai",
            "runwayml",
            "google",
            "huggingface",
            "diffusers",
        ]

        if any(repo in filename.lower() for repo in hf_repo_patterns):
            return True, "Contains HF repository identifiers"

        return False, "No HF patterns detected"

    def _should_skip_civitai(
        self, filename: str, model_type: str = ""
    ) -> Tuple[bool, str]:
        """Determine if Civitai search should be skipped for this model.

        Args:
            filename: Model filename
            model_type: Model type from workflow

        Returns:
            Tuple of (should_skip, reason)
        """
        if not self.enable_pattern_recognition:
            return False, "Pattern recognition disabled"

        is_likely_hf, reason = self._is_likely_hf_model(filename, model_type)

        if is_likely_hf:
            skip_reason = f"Likely HF model - skipping Civitai. Reason: {reason}"
            self.logger.info(
                f"Early termination decision for {filename}: {skip_reason}"
            )
            return True, skip_reason

        return False, "Should search Civitai"

    def search(self, model_info: Dict[str, Any]) -> SearchResult:
        filename = model_info["filename"]
        model_type = model_info.get("type", "")

        # Enhanced filename validation with early return for INVALID_FILENAME
        is_valid, sanitized_filename, error_reason = validate_and_sanitize_filename(
            filename
        )
        if not is_valid:
            self.logger.warning(
                f"Invalid filename detected: {filename} - {error_reason}"
            )
            return SearchResult(
                status="INVALID_FILENAME",
                filename=filename,
                type=model_type,
                error_message=error_reason,
                metadata={
                    "validation_reason": error_reason,
                    "original_filename": filename,
                },
            )

        filename = sanitized_filename

        if not config.search.enable_qwen:
            return SearchResult(
                status="NOT_FOUND",
                filename=filename,
                metadata={"reason": "Qwen backend disabled via configuration"},
            )

        # Smart Pattern Recognition: Check if model is likely on HF
        if self.enable_pattern_recognition:
            should_skip_civitai, skip_reason = self._should_skip_civitai(
                filename, model_type
            )
            if should_skip_civitai:
                self.logger.info(
                    f"Pattern recognition: Skipping Civitai for {filename}. {skip_reason}"
                )

                # Return a result indicating HF-only search should be performed
                return SearchResult(
                    status="NOT_FOUND",
                    filename=filename,
                    type=model_type,
                    metadata={
                        "reason": "Pattern recognition: Likely HF model",
                        "pattern_skip_civitai": True,
                        "skip_reason": skip_reason,
                        "search_strategy": "HF-only",
                        "pattern_recognized": True,
                    },
                )

        cached_result = self._load_cached_result(filename)
        if cached_result:
            # Add pattern recognition info to cached result
            if self.enable_pattern_recognition:
                should_skip_civitai, skip_reason = self._should_skip_civitai(
                    filename, model_type
                )
                if should_skip_civitai:
                    if cached_result.metadata is None:
                        cached_result.metadata = {}
                    cached_result.metadata["pattern_recognized_from_cache"] = True
                    cached_result.metadata["cached_skip_reason"] = skip_reason
            return cached_result

        # Pre-Qwen web search has been removed; rely on Qwen's own tools.
        web_search_results = None

        prompt = self._build_agentic_prompt(model_info, web_search_results)

        command = [self.qwen_binary]

        extra_args = self._collect_extra_args()
        if extra_args:
            command.extend(extra_args)

        self.logger.info("Executing Qwen search via: %s", " ".join(command))

        try:
            completed = subprocess.run(
                command,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                timeout=config.search.qwen_timeout,
                text=True,
                input=prompt,
            )
        except FileNotFoundError:
            self.logger.error("Qwen binary not found: %s", self.qwen_binary)
            return SearchResult(
                status="NOT_FOUND",
                filename=filename,
                metadata={"reason": f"Qwen binary not found: {self.qwen_binary}"},
            )
        except subprocess.TimeoutExpired:
            self.logger.error(
                "Qwen search timed out after %s seconds", config.search.qwen_timeout
            )
            return SearchResult(
                status="ERROR",
                filename=filename,
                error_message=f"Qwen agent timed out after {config.search.qwen_timeout} seconds",
            )

        if completed.returncode != 0:
            self.logger.error(
                "Qwen binary exited with %s: %s",
                completed.returncode,
                completed.stderr.strip(),
            )
            return SearchResult(
                status="NOT_FOUND",
                filename=filename,
                metadata={
                    "reason": "Qwen agent returned non-zero exit code",
                    "stderr": completed.stderr.strip(),
                },
            )

        qwen_payload = self._parse_qwen_stdout(completed.stdout)
        if qwen_payload is None:
            self.logger.warning(
                "Qwen agent produced no consumable output for %s", filename
            )
            return SearchResult(
                status="NOT_FOUND",
                filename=filename,
                metadata={"reason": "Qwen agent produced no output"},
            )

        parsed_result = self._annotate_result(
            self._parse_qwen_result(qwen_payload, filename),
            cached=False,
        )
        self._store_cached_result(filename, qwen_payload)
        return parsed_result

    def _build_agentic_prompt(
        self,
        model_info: Dict[str, Any],
        web_search_results: Optional[Dict[str, Any]] = None,
    ) -> str:
        # Added by Gemini on 2025-10-30
        # This primer was added to give the Qwen agent more detailed instructions on how to use the Hugging Face CLI.
        """Build comprehensive agentic search prompt for Qwen with pattern recognition."""
        filename = model_info.get("filename", "")
        model_type = model_info.get("type", "")
        node_type = model_info.get("node_type", "")

        # Smart pattern recognition for HF models
        pattern_info = ""
        if self.enable_pattern_recognition:
            should_skip_civitai, skip_reason = self._should_skip_civitai(
                filename, model_type
            )
            if should_skip_civitai:
                pattern_info = f"""
SMART PATTERN RECOGNITION RESULTS:
- Pattern Recognition: ACTIVE - Model detected as likely HuggingFace-hosted
- Early Termination Decision: SKIP Civitai search
- Reason: {skip_reason}
- Recommended Strategy: Go directly to HuggingFace search (Phase 2 only)
- Expected Success Rate: HIGH for HuggingFace-hosted models

IMPORTANT: Based on pattern recognition, do NOT search Civitai (Phase 1). 
Proceed directly to Phase 2: HUGGINGFACE SEARCH ONLY.
"""
            else:
                pattern_info = f"""
SMART PATTERN RECOGNITION RESULTS:
- Pattern Recognition: ACTIVE - No HF patterns detected
- Early Termination Decision: SEARCH Civitai (normal workflow)
- Reason: {skip_reason}
- Recommended Strategy: Full Civitai + HuggingFace search (Phase 1 + Phase 2)
"""
        else:
            pattern_info = f"""
SMART PATTERN RECOGNITION: DISABLED
- Proceeding with standard search workflow
- Will search both Civitai and HuggingFace
"""

        # Add web search context if available
        web_search_context = ""
        if web_search_results:
            if web_search_results.get(
                "status"
            ) == "UNCERTAIN" and web_search_results.get("candidates"):
                candidates = web_search_results["candidates"]
                web_search_context = f"""

=== WEB SEARCH RESULTS (Pre-search Context) ===
The following repositories were found via web search with varying confidence levels:

"""
                for i, candidate in enumerate(candidates[:5], 1):
                    web_search_context += f"""{i}. {candidate['repository']} ({candidate['source']})
   URL: {candidate['url']}
   Match Score: {candidate['match_score']:.2f}
   Confidence: {candidate['confidence']}
   Title: {candidate.get('title', 'N/A')}
   
"""
                web_search_context += f"""
IMPORTANT: These candidates were found via web search and should be verified. 
You can use these as starting points for your search, but still perform your own verification.
"""
            elif web_search_results.get("status") == "FOUND":
                web_search_context = f"""

=== WEB SEARCH RESULT (High Confidence) ===
A high-confidence match was found via web search but requires Qwen verification:
Repository: {web_search_results.get('metadata', {}).get('repository', 'Unknown')}
Score: {web_search_results.get('metadata', {}).get('web_search_score', 0)}
You should prioritize verifying this result.
"""

        return f"""You are an autonomous AI model discovery agent. Your task is to find the correct download source for a ComfyUI model file using intelligent search strategies.{pattern_info}

INPUT DATA:
- Filename: {filename}
- Model Type: {model_type}
- Node Type: {node_type}

ENVIRONMENT:
- CIVITAI_API_KEY is available in environment (from ~/.secrets)
- You have access to: bash, web_search, web_fetch tools

YOUR MISSION:
Find where to download this EXACT file, or confirm it doesn't exist on Civitai/HuggingFace.{web_search_context}

SEARCH STRATEGY (Execute in order):

=== PHASE 1: CIVITAI API SEARCH (Max 5 attempts) ===

1. Extract search keywords from filename:
   - Remove extensions: .pth, .pt, .safetensors, .ckpt, .bin
   - Split on delimiters: _, -, .
   - Identify: version numbers, model types, keywords

   Examples:
   "rife49.pth" → ["rife", "49", "frame interpolation"]
   "4xNMKDSuperscale.pt" → ["nmkd", "superscale", "4x", "upscale"]

2. Try Civitai API with these queries (stop when found):
   a) Exact name without extension
   b) Main keyword only
   c) Alternative terms based on model type
   d) Broader category search

3. API endpoint: https://civitai.com/api/v1/models
   Parameters: ?query=<term>&limit=10&sort=Highest+Rated
   Headers: Authorization: Bearer $CIVITAI_API_KEY

4. For EACH result:
   - Fetch full details: https://civitai.com/api/v1/models/{{id}}
   - Check ALL modelVersions[].files[].name for EXACT match to "{filename}"
   - Log: "Checked model {{id}} '{{name}}': {{files found}}"

5. CRITICAL: Match must be EXACT filename (case-sensitive)

=== PHASE 2: WEB SEARCH + HUGGINGFACE (If Civitai fails) ===

### **Hugging Face Primer for an AI Agent**

You have access to the `hf` command-line tool to interact with the Hugging Face Hub. Here is your guide on how to use it to find and download models.

**Your primary workflow for Hugging Face will be:**
1.  Use `web_search` to find the correct repository ID (`repo_id`).
2.  Use the `hf` tool to list the files in that repository to find the exact filename.
3.  Use the `hf` tool to download the specific file you need.

---

#### **Step 1: Find the Repository ID (`repo_id`)**

The `hf` tool does not have a search command. You must first use `web_search` to find the `repo_id`, which is in the format `author/repository_name`.

**Example Web Search Queries:**
*   To find the SDXL base model: `"sd_xl_base_1.0.safetensors" site:huggingface.co`
*   To find a RIFE model: `"rife frame interpolation" model huggingface`

Your goal is to find the official repository, for example: `stabilityai/stable-diffusion-xl-base-1.0`.

---

#### **Step 2: List Files in the Repository**

Once you have the `repo_id`, you must verify that the file you need exists in the repository and get its exact path. Use the `hf download` command with the `--dry-run` flag for this.

**Command:**
```bash
hf download --dry-run <repo_id>
```

**Example:** To list all files in the `stabilityai/stable-diffusion-xl-base-1.0` repository:
```bash
hf download --dry-run stabilityai/stable-diffusion-xl-base-1.0
```
The output will be a list of all files in that repository. Look through this list to find the exact filename you need, for example, `sd_xl_base_1.0.safetensors`.

---

#### **Step 3: Download the Specific File**

After you have the `repo_id` and the exact `path/to/file/in/repo`, you can download it.

**Command:**
```bash
hf download <repo_id> <path/to/file/in/repo> --local-dir <your/local/directory>
```

**Example:** To download the `sd_xl_base_1.0.safetensors` file to the `/tmp/models` directory:
```bash
hf download stabilityai/stable-diffusion-xl-base-1.0 sd_xl_base_1.0.safetensors --local-dir /tmp/models
```

This command will download the specified file into the directory you provide. Always use the `--local-dir` flag to control where the file is saved.

---

1. Use your web_search tool with smart patterns:
   - If "rife*.pth" → "rife frame interpolation huggingface"
   - If "sam_*.pth" → "facebook sam segment anything huggingface"
   - If "*NMKD*" → "nmkd upscaler huggingface github"
   - Otherwise → "{filename} site:huggingface.co OR site:github.com"

2. Extract repos from results:
   - Look for: huggingface.co/<user>/<repo>/blob/main/<path>
   - Look for: github.com/<user>/<repo>/releases

3. Verify file exists:
   - HuggingFace: Use `hf` CLI or web_fetch to check repo files
   - GitHub: Check releases or repo files

4. If found, construct download URL:
   - HF: https://huggingface.co/<user>/<repo>/resolve/main/<path>
   - GitHub: Use release asset URL or raw.githubusercontent.com

=== PHASE 3: OUTPUT RESULT ===

SUCCESS - Found on Civitai:
{{{{
  "status": "FOUND",
  "source": "civitai",
  "civitai_id": <model_id>,
  "version_id": <version_id>,
  "civitai_name": "<model_name>",
  "version_name": "<version_name>",
  "download_url": "https://civitai.com/api/download/models/<version_id>",
  "confidence": "exact",
  "metadata": {{{{
    "search_attempts": <count>,
    "reasoning": "brief explanation"
  }}}}
}}}}

SUCCESS - Found on HuggingFace:
{{{{
  "status": "FOUND",
  "source": "huggingface",
  "repo": "<user>/<repo>",
  "file_path": "<path>",
  "download_url": "<url>",
  "confidence": "high",
  "metadata": {{{{
    "search_attempts": <count>,
    "reasoning": "brief explanation"
  }}}}
}}}}

UNCERTAIN - Need Human Review:
{{{{
  "status": "UNCERTAIN",
  "candidates": [
    {{{{"source": "...", "name": "...", "url": "...", "match_score": 0.7}}}}
  ],
  "reason": "Multiple candidates found, need manual verification",
  "metadata": {{{{
    "search_attempts": <count>
  }}}}
}}}}

NOT FOUND:
{{{{
  "status": "NOT_FOUND",
  "metadata": {{{{
    "civitai_searches": <count>,
    "web_searches": <count>,
    "reason": "detailed explanation of where you looked"
  }}}}
}}}}

INVALID:
{{{{
  "status": "INVALID_FILENAME",
  "reason": "Filename contains invalid characters or is malformed",
  "metadata": {{{{
    "reason": "explanation"
  }}}}
}}}}

CRITICAL RULES:
1. Filename validation must be EXACT match
2. Try multiple strategies before giving up
3. Return EXACTLY ONE JSON object as your final output with no additional commentary
4. If uncertain, return UNCERTAIN status with candidates
5. Maximum 15 minutes timeout

BEGIN AGENTIC SEARCH NOW. Think step by step and log your progress."""

    def _build_qwen_prompt(self, model_info: Dict[str, Any]) -> str:
        """Simplified prompt builder used by tests."""
        filename = model_info.get("filename", "")
        return f"Qwen Search Prompt for {filename}"

    def _parse_qwen_result(
        self, qwen_result: Dict[str, Any], filename: str
    ) -> SearchResult:
        """Parse Qwen's search results into SearchResult object."""
        status = qwen_result.get("status", "ERROR")

        if status == "FOUND":
            source = qwen_result.get("source", "unknown")

            if source == "civitai":
                return SearchResult(
                    status="FOUND",
                    filename=filename,
                    source="civitai",
                    civitai_id=qwen_result.get("civitai_id"),
                    version_id=qwen_result.get("version_id"),
                    civitai_name=qwen_result.get("civitai_name"),
                    version_name=qwen_result.get("version_name"),
                    download_url=qwen_result.get("download_url"),
                    confidence=qwen_result.get("confidence", "exact"),
                    metadata=qwen_result.get("metadata", {}),
                )

            elif source == "huggingface":
                return SearchResult(
                    status="FOUND",
                    filename=filename,
                    source="huggingface",
                    download_url=qwen_result.get("download_url"),
                    confidence=qwen_result.get("confidence", "high"),
                    metadata={
                        "repo": qwen_result.get("repo"),
                        "file_path": qwen_result.get("file_path"),
                        **qwen_result.get("metadata", {}),
                    },
                )

        elif status == "UNCERTAIN":
            return SearchResult(
                status="UNCERTAIN",
                filename=filename,
                metadata={
                    "reason": qwen_result.get("reason", "Uncertain matches"),
                    "candidates": qwen_result.get("candidates", []),
                    "requires_review": True,
                },
            )

        elif status == "INVALID_FILENAME":
            return SearchResult(
                status="INVALID_FILENAME",
                filename=filename,
                error_message=qwen_result.get("reason", "Invalid filename"),
            )

        # NOT_FOUND or ERROR
        return SearchResult(
            status=status,
            filename=filename,
            metadata=qwen_result.get("metadata", {}),
            error_message=qwen_result.get("error_message"),
        )

    def _collect_extra_args(self) -> List[str]:
        """Collect additional CLI arguments from config and environment."""
        args: List[str] = []
        if config.search.qwen_extra_args:
            args.extend(config.search.qwen_extra_args)
        extra_from_env = os.environ.get("QWEN_EXTRA_ARGS")
        if extra_from_env:
            try:
                args.extend(shlex.split(extra_from_env))
            except ValueError as exc:
                self.logger.warning("Failed to parse QWEN_EXTRA_ARGS: %s", exc)
        return args

    def _cache_file_path(self, filename: str) -> Path:
        return self.cache_dir / f"{sanitize_filename(filename)}-qwen.json"

    def _load_cached_result(self, filename: str) -> Optional[SearchResult]:
        """Load cached Qwen result if within TTL."""
        cache_file = self._cache_file_path(filename)
        if not cache_file.exists():
            return None

        ttl = max(config.search.qwen_cache_ttl, 0)
        age = time.time() - cache_file.stat().st_mtime
        if ttl and age > ttl:
            try:
                cache_file.unlink()
            except OSError:
                pass
            return None

        try:
            with open(cache_file, encoding="utf-8") as fh:
                payload = json.load(fh)
        except Exception as exc:
            self.logger.warning("Failed to read Qwen cache for %s: %s", filename, exc)
            try:
                cache_file.unlink()
            except OSError:
                pass
            return None

        qwen_result = payload.get("result") if isinstance(payload, dict) else None
        if not isinstance(qwen_result, dict):
            return None

        parsed = self._parse_qwen_result(qwen_result, filename)
        return self._annotate_result(parsed, cached=True)

    def _store_cached_result(self, filename: str, payload: Dict[str, Any]) -> None:
        """Persist raw Qwen payload for future reuse."""
        cache_file = self._cache_file_path(filename)
        envelope = {"cached_at": time.time(), "result": payload}
        try:
            with open(cache_file, "w", encoding="utf-8") as fh:
                json.dump(envelope, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
        except Exception as exc:
            self.logger.warning("Unable to store Qwen cache for %s: %s", filename, exc)

    def _annotate_result(self, result: SearchResult, cached: bool) -> SearchResult:
        """Ensure metadata flags that Qwen handled the lookup."""
        metadata = result.metadata or {}
        metadata.setdefault("found_by", "qwen")
        if cached:
            metadata["cached"] = True
        elif "cached" in metadata:
            metadata.pop("cached", None)
        result.metadata = metadata
        return result

    def _parse_qwen_stdout(self, stdout: str) -> Optional[Dict[str, Any]]:
        """Parse the Qwen CLI stdout as JSON."""
        output = stdout.strip()
        if not output:
            return None

        try:
            return json.loads(output)
        except json.JSONDecodeError:
            self.logger.debug("Qwen stdout is not valid JSON; length=%s", len(output))
            return None


class HuggingFaceSearch(SearchBackend):
    """HuggingFace search backend with web search and file verification."""

    def __init__(self, logger=None):
        super().__init__(logger)
        self.hf_token = os.getenv("HF_TOKEN")

    def get_name(self) -> str:
        return "huggingface"

    def search(self, model_info: Dict[str, Any]) -> SearchResult:
        """
        Search for a model on HuggingFace using web search and file verification.

        Args:
            model_info: Dictionary containing model information (filename, type, etc.)

        Returns:
            SearchResult with model information if found, or NOT_FOUND/ERROR status
        """
        filename = model_info["filename"]
        model_type = model_info.get("type", "")

        # Enhanced filename validation with early return for INVALID_FILENAME
        is_valid, sanitized_filename, error_reason = validate_and_sanitize_filename(
            filename
        )
        if not is_valid:
            self.logger.warning(
                f"Invalid filename detected: {filename} - {error_reason}"
            )
            return SearchResult(
                status="INVALID_FILENAME",
                filename=filename,
                type=model_type,
                error_message=error_reason,
                metadata={
                    "validation_reason": error_reason,
                    "original_filename": filename,
                },
            )

        filename = sanitized_filename

        self.logger.info(f"Searching HuggingFace for model: {filename}")

        # Direct discovery via web search has been removed from this backend.
        # Discovery is handled by the Qwen agent; this backend focuses on verification when given a repo.
        return SearchResult(
            status="NOT_FOUND",
            filename=filename,
            type=model_type,
            metadata={
                "reason": "Direct HuggingFace discovery is disabled; rely on Qwen for repository discovery",
                "search_attempts": 0,
            },
        )

    def _extract_repos_from_search_results(
        self, search_results: List[Dict[str, Any]], target_filename: str
    ) -> List[str]:
        """
        Extract HuggingFace repository names from search results.

        Args:
            search_results: Results from a generic web search tool
            target_filename: Target model filename

        Returns:
            List of repository names in format "username/repo-name"
        """
        repos = []
        target_base = target_filename.rsplit(".", 1)[0].lower()

        for result in search_results:
            url = result.get("url", "")

            # Look for HuggingFace repository URLs
            if "huggingface.co" in url:
                # Extract repo name from URL
                # Expected format: https://huggingface.co/username/repo-name/tree/main/path/to/file
                # or: https://huggingface.co/username/repo-name
                match = re.search(r"huggingface\.co/([^/]+)/([^/?]+)", url)
                if match:
                    repo_name = f"{match.group(1)}/{match.group(2)}"

                    # Remove any trailing path components
                    repo_name = (
                        repo_name.split("/")[0]
                        + "/"
                        + repo_name.split("/")[1].split("?")[0].split("#")[0]
                    )

                    if repo_name not in repos:
                        repos.append(repo_name)
                        self.logger.debug(f"Extracted repository: {repo_name}")

        # Prioritize repositories with names matching to target filename
        repos.sort(
            key=lambda x: self._calculate_repo_score(x, target_base), reverse=True
        )
        return repos[:5]  # Limit to top 5 candidates

    def _calculate_repo_score(self, repo_name: str, target_filename: str) -> int:
        """
        Calculate a relevance score for a repository based on name similarity.

        Args:
            repo_name: Repository name in format "username/repo-name"
            target_filename: Target model filename (without extension)

        Returns:
            Relevance score (higher is better)
        """
        repo_parts = repo_name.lower().split("/")
        if len(repo_parts) < 2:
            return 0

        repo_short_name = repo_parts[1]
        target_lower = target_filename.lower()

        # Exact match gets highest score
        if repo_short_name == target_lower:
            return 100

        # Contains match gets good score
        if target_lower in repo_short_name or repo_short_name in target_lower:
            return 80

        # Partial match gets lower score
        for word in target_lower.split("_"):
            if word in repo_short_name:
                return 60

        return 30

    def _verify_repository_and_find_file(
        self, repo_name: str, target_filename: str
    ) -> Optional[SearchResult]:
        """
        Verify a HuggingFace repository and find the target model file.

        Args:
            repo_name: Repository name in format "username/repo-name"
            target_filename: Target model filename

        Returns:
            SearchResult if file is found, None otherwise
        """
        try:
            # Import huggingface_hub here to avoid import errors if not available
            try:
                from huggingface_hub import HfApi, RepositoryNotFoundError, hf_hub_url
            except ImportError:
                self.logger.error("huggingface_hub library not available")
                return None

            # Initialize HF API with token if available
            hf_api = HfApi(token=self.hf_token)

            # Get repository info
            try:
                repo_info = hf_api.repo_info(repo_name)
            except RepositoryNotFoundError:
                self.logger.debug(f"Repository not found: {repo_name}")
                return None
            except Exception as e:
                self.logger.warning(
                    f"Failed to get repository info for {repo_name}: {e}"
                )
                return None

            # List all files in the repository
            try:
                repo_files = hf_api.list_repo_files(repo_name, repo_type="model")
            except Exception as e:
                self.logger.warning(f"Failed to list files for {repo_name}: {e}")
                return None

            # Find matching files
            target_base = target_filename.rsplit(".", 1)[0].lower()
            matching_files = []

            for file_info in repo_files:
                file_path = (
                    file_info.path if hasattr(file_info, "path") else str(file_info)
                )
                file_name = os.path.basename(file_path)

                # Check if file name matches our target (with common model extensions)
                if self._is_matching_model_file(file_name, target_base):
                    file_size = getattr(file_info, "size", 0)
                    matching_files.append((file_path, file_size))

            if not matching_files:
                return None

            # Select the best match (prefer exact name match, then largest file)
            best_file = self._select_best_file(matching_files, target_filename)
            if not best_file:
                return None

            file_path, file_size = best_file

            # Construct download URL
            download_url = hf_hub_url(
                repo_name=repo_name, filename=file_path, repo_type="model"
            )

            # Determine confidence based on filename match
            confidence = (
                "exact"
                if os.path.basename(file_path).lower() == target_filename.lower()
                else "fuzzy"
            )

            return SearchResult(
                status="FOUND",
                filename=target_filename,
                source="huggingface",
                download_url=download_url,
                confidence=confidence,
                type=self._infer_model_type_from_filename(target_filename),
                metadata={
                    "repo": repo_name,
                    "file_path": file_path,
                    "file_size": file_size,
                    "search_attempts": 1,
                },
            )

        except Exception as e:
            self.logger.error(f"Error verifying repository {repo_name}: {e}")
            return None

    def _is_matching_model_file(self, file_name: str, target_base: str) -> bool:
        """
        Check if a file matches our target model file.

        Args:
            file_name: File name from repository
            target_base: Target filename base (without extension)

        Returns:
            True if file matches target
        """
        file_lower = file_name.lower()
        target_lower = target_base.lower()

        # Remove extension for comparison
        file_base = file_lower.rsplit(".", 1)[0] if "." in file_lower else file_lower

        # Exact match
        if file_base == target_lower:
            return True

        # Check for common model extensions
        valid_extensions = [".safetensors", ".ckpt", ".pt", ".bin", ".pth", ".onnx"]
        if any(file_lower.endswith(ext) for ext in valid_extensions):
            # Check if target is contained in filename or vice versa
            if target_lower in file_base or file_base in target_lower:
                return True

        return False

    def _select_best_file(
        self, matching_files: List[Tuple[str, int]], target_filename: str
    ) -> Optional[Tuple[str, int]]:
        """
        Select the best matching file from a list of candidates.

        Args:
            matching_files: List of (file_path, file_size) tuples
            target_filename: Target filename

        Returns:
            Best file tuple or None
        """
        if not matching_files:
            return None

        target_base = target_filename.lower()

        # First, try to find exact name match
        for file_path, file_size in matching_files:
            file_name = os.path.basename(file_path).lower()
            if (
                file_name == target_base
                or file_name == target_base + ".safetensors"
                or file_name == target_base + ".ckpt"
            ):
                return (file_path, file_size)

        # If no exact match, prefer larger files (likely to be main model)
        return max(matching_files, key=lambda x: x[1])

    def _infer_model_type_from_filename(self, filename: str) -> str:
        """
        Infer model type from filename.

        Args:
            filename: Model filename

        Returns:
            Model type string
        """
        filename_lower = filename.lower()

        # Check for specific patterns in filename
        if "lora" in filename_lower or "loras" in filename_lower:
            return "loras"
        elif "vae" in filename_lower:
            return "vae"
        elif "controlnet" in filename_lower or "control" in filename_lower:
            return "controlnet"
        elif (
            "upscale" in filename_lower
            or "esrgan" in filename_lower
            or "realesrgan" in filename_lower
        ):
            return "upscale_models"
        elif "embed" in filename_lower:
            return "embeddings"
        else:
            return "checkpoints"


class ModelSearch:
    """
    Unified model search coordinator.

    Manages multiple search backends and provides caching, validation,
    and result management.
    """

    def __init__(
        self,
        state_manager: Optional[StateManager] = None,
        cache_dir: Optional[str] = None,
        logger=None,
    ):
        """
        Initialize the model search coordinator.

        Args:
            state_manager: StateManager for tracking search attempts
            cache_dir: Directory for caching search results
            logger: Optional logger instance
        """
        self.logger = logger or get_logger("ModelSearch")
        self.state_manager = state_manager

        # Initialize available backends dynamically
        # Qwen is the PRIMARY agentic search backend that handles all sources
        self.backends: Dict[str, SearchBackend] = {
            "qwen": QwenSearch(logger=self.logger),  # PRIMARY - agentic search
            "civitai": CivitaiSearch(logger=self.logger),  # FALLBACK - direct API
            "huggingface": HuggingFaceSearch(logger=self.logger),  # Placeholder backend
        }

        # Conditionally register ModelScope backend
        if (
            MODELSCOPE_AVAILABLE
            and ModelScopeSearch
            and config.copilot.enable_modelscope
        ):
            self.logger.info(
                "ModelScope backend enabled and available, adding to search backends."
            )
            self.backends["modelscope"] = ModelScopeSearch(logger=self.logger)
        elif (
            MODELSCOPE_AVAILABLE
            and ModelScopeSearch
            and not config.copilot.enable_modelscope
        ):
            self.logger.info(
                "ModelScope backend available but disabled in configuration."
            )
        elif MODELSCOPE_AVAILABLE and not ModelScopeSearch:
            self.logger.warning(
                "ModelScope package available but ModelScopeSearch import failed."
            )
        else:
            self.logger.info("ModelScope backend not available.")

        # Validate and set backend order
        self._validate_backend_order()

        # Setup caching
        self.cache_dir = Path(cache_dir or config.temp_dir) / "search_cache"
        self.cache_dir.mkdir(exist_ok=True)

    def search_model(
        self,
        model_info: Dict[str, Any],
        use_cache: bool = True,
        backends: Optional[List[str]] = None,
    ) -> SearchResult:
        """
        Search for a model using the configured backend order.

        Args:
            model_info: Dictionary with model information
            use_cache: Whether to use cached results

        Returns:
            SearchResult object
        """
        filename = model_info["filename"]

        # Check cache first
        if use_cache and config.search.enable_cache:
            cached_result = self._get_cached_result(filename)
            if cached_result:
                self.logger.info(f"Using cached result for {filename}")
                return cached_result

        # Determine backend order (override if explicit list provided)
        backends_to_try = backends if backends else config.search.backend_order

        # Try each backend in the configured order
        for backend_name in backends_to_try:
            if backend_name not in self.backends:
                self.logger.warning(
                    f"Configured backend '{backend_name}' is not available or unknown."
                )
                continue

            backend = self.backends[backend_name]
            self.logger.info(f"Trying '{backend_name}' search for '{filename}'")

            result = backend.search(model_info)

            # Attach model type for downstream placement if backend didn't set it
            if getattr(result, "type", None) is None:
                try:
                    result.type = model_info.get("type")
                except Exception:
                    pass

            # Cache successful results
            if result.status == "FOUND" and use_cache and config.search.enable_cache:
                self._cache_result(result)

            # Mark attempt in state manager
            if self.state_manager:
                self.state_manager.mark_download_attempted(
                    filename,
                    model_info,
                    result.__dict__ if result.status == "FOUND" else None,
                )

            # Return if found or if it's a critical error (don't try other backends)
            if result.status in ["FOUND", "ERROR", "INVALID_FILENAME"]:
                return result

        # If all backends returned NOT_FOUND
        return SearchResult(
            status="NOT_FOUND",
            filename=filename,
            metadata={
                "backends_tried": backends_to_try,
                "reason": "No results from configured backends",
            },
        )

    def search_multiple_models(
        self,
        models: List[Dict[str, Any]],
        backends: Optional[List[str]] = None,
        use_cache: bool = True,
    ) -> List[SearchResult]:
        """
        Search for multiple models.

        Args:
            models: List of model info dictionaries
            backends: List of backend names to try
            use_cache: Whether to use cached results

        Returns:
            List of SearchResult objects
        """
        original_order = list(config.search.backend_order)
        try:
            if backends:
                config.search.backend_order = backends

            results = []
            for model in models:
                result = self.search_model(model, use_cache)
                results.append(result)
                time.sleep(0.5)
            return results
        finally:
            # Restore original order to avoid side-effects
            config.search.backend_order = original_order

    def _get_cached_result(self, filename: str) -> Optional[SearchResult]:
        """Get cached search result."""
        cache_file = self.cache_dir / f"{sanitize_filename(filename)}.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file) as f:
                data = json.load(f)
            return SearchResult(**data)
        except Exception:
            return None

    def _cache_result(self, result: SearchResult) -> None:
        """Cache a search result."""
        cache_file = self.cache_dir / f"{sanitize_filename(result.filename)}.json"
        try:
            with open(cache_file, "w") as f:
                json.dump(result.__dict__, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to cache result: {e}")

    def clear_cache(self, filename: Optional[str] = None) -> None:
        """
        Clear search cache.

        Args:
            filename: Specific filename to clear, or None for all
        """
        if filename:
            cache_file = self.cache_dir / f"{sanitize_filename(filename)}.json"
            if cache_file.exists():
                cache_file.unlink()
        else:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()

    def get_search_stats(self) -> Dict[str, Any]:
        """Get search statistics."""
        cache_files = list(self.cache_dir.glob("*.json"))
        return {
            "cached_results": len(cache_files),
            "cache_dir": str(self.cache_dir),
            "backends_available": list(self.backends.keys()),
        }

    def _validate_backend_order(self):
        """Validate the configured backend order against available backends."""
        configured_order = config.search.backend_order
        available_backends = set(self.backends.keys())

        # Filter out invalid backends
        valid_order = [
            backend for backend in configured_order if backend in available_backends
        ]

        # Log warnings for invalid backends
        invalid_backends = [
            backend for backend in configured_order if backend not in available_backends
        ]
        if invalid_backends:
            self.logger.warning(
                f"Configured backends not available: {invalid_backends}. "
                f"Available backends: {list(available_backends)}"
            )

        # If no valid backends remain, fall back to default order
        if not valid_order:
            valid_order = list(available_backends)
            self.logger.warning(
                "No valid backends in configured order, falling back to all available backends"
            )

        # Update the config with the validated order
        config.search.backend_order = valid_order

        self.logger.info(f"Using backend order: {valid_order}")


# Convenience functions for backward compatibility
def search_civitai(model, api_key=None, logger=None):
    """
    Convenience function for Civitai search (backward compatibility).

    Args:
        model: Model info dictionary
        api_key: Optional API key
        logger: Optional logger

    Returns:
        SearchResult object
    """
    backend = CivitaiSearch(logger)
    return backend.search(model)


def search_with_qwen(model, temp_dir=None, logger=None):
    """
    Convenience function for Qwen search (backward compatibility).

    Args:
        model: Model info dictionary
        temp_dir: Temporary directory for results
        logger: Optional logger

    Returns:
        SearchResult object
    """
    backend = QwenSearch(temp_dir, logger)
    return backend.search(model)
