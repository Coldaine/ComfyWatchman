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

import json
import os
import re
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

from .config import config
from .logging import get_logger
from .utils import get_api_key, validate_url, sanitize_filename
from .state_manager import StateManager

# Import adapters and feature flags
from .adapters import MODELSCOPE_AVAILABLE

# Conditionally import ModelScopeSearch
try:
    from .adapters.modelscope_search import ModelScopeSearch
except ImportError:
    ModelScopeSearch = None


@dataclass
class SearchResult:
    """Result of a model search operation."""
    status: str  # 'FOUND', 'NOT_FOUND', 'INVALID_FILENAME', 'ERROR'
    filename: str
    source: Optional[str] = None  # 'civitai', 'huggingface'
    civitai_id: Optional[int] = None
    version_id: Optional[int] = None
    civitai_name: Optional[str] = None
    version_name: Optional[str] = None
    download_url: Optional[str] = None
    confidence: Optional[str] = None  # 'exact', 'fuzzy'
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
        self.api_key = config.search.civitai_api_key or get_api_key() # Fallback for old method
        self.base_url = "https://civitai.com/api/v1"

    def get_name(self) -> str:
        return "civitai"

    def search(self, model_info: Dict[str, Any]) -> SearchResult:
        """Search Civitai API for a model."""
        filename = model_info['filename']
        model_type = model_info.get('type', '')

        # Clean filename for search
        query = self._prepare_search_query(filename)

        self.logger.info(f"Searching Civitai: {query}")

        try:
            # Build search parameters
            params = {
                'query': query,
                'limit': 10,
                'sort': 'Highest Rated'
            }

            # Add type filtering if applicable
            type_filter = self._get_type_filter(model_type)
            if type_filter:
                params['types'] = type_filter

            response = requests.get(
                f"{self.base_url}/models",
                params=params,
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=30
            )

            if response.status_code != 200:
                return SearchResult(
                    status='ERROR',
                    filename=filename,
                    error_message=f"API error: {response.status_code}"
                )

            results = response.json().get('items', [])
            if not results:
                return SearchResult(
                    status='NOT_FOUND',
                    filename=filename,
                    metadata={'search_attempts': 1, 'reason': 'No results found'}
                )

            # Find best match
            best_match = self._find_best_match(results, filename)

            if best_match:
                return self._create_result_from_match(best_match, filename, 'exact')
            else:
                # Try fuzzy match with first result
                first_result = results[0]
                return self._create_result_from_match(first_result, filename, 'fuzzy')

        except Exception as e:
            self.logger.error(f"Civitai search error: {e}")
            return SearchResult(
                status='ERROR',
                filename=filename,
                error_message=str(e)
            )

    def _prepare_search_query(self, filename: str) -> str:
        """Prepare filename for search query."""
        # Remove extension and clean up
        query = filename.replace('.safetensors', '').replace('.ckpt', '').replace('.pth', '').replace('.pt', '').replace('.bin', '')
        # Replace underscores and dots with spaces
        query = re.sub(r'[_.]', ' ', query)
        return query.strip()

    def _get_type_filter(self, model_type: str) -> Optional[str]:
        """Get Civitai type filter from model type."""
        type_mapping = {
            'checkpoints': 'Checkpoint',
            'loras': 'LORA',
            'vae': 'VAE',
            'controlnet': 'Controlnet',
            'upscale_models': 'Upscaler',
            'clip': 'TextualInversion',  # Approximation
            'unet': 'Checkpoint'  # Approximation
        }
        return type_mapping.get(model_type)

    def _find_best_match(self, results: List[Dict], target_filename: str) -> Optional[Dict]:
        """Find the best matching result."""
        for result in results:
            for version in result.get('modelVersions', []):
                for file_info in version.get('files', []):
                    if file_info.get('name', '').lower() == target_filename.lower():
                        return result
        return None

    def _create_result_from_match(self, result: Dict, filename: str, confidence: str) -> SearchResult:
        """Create SearchResult from Civitai API result."""
        version = result['modelVersions'][0]  # Use first version

        return SearchResult(
            status='FOUND',
            filename=filename,
            source='civitai',
            civitai_id=result['id'],
            version_id=version['id'],
            civitai_name=result['name'],
            version_name=version['name'],
            download_url=f"https://civitai.com/api/download/models/{version['id']}",
            confidence=confidence,
            metadata={'search_attempts': 1}
        )


class QwenSearch(SearchBackend):
    """Qwen-based autonomous search backend."""

    def __init__(self, temp_dir: Optional[str] = None, logger=None):
        super().__init__(logger)
        self.temp_dir = Path(temp_dir or config.temp_dir)
        self.temp_dir.mkdir(exist_ok=True)

    def get_name(self) -> str:
        return "qwen"

    def search(self, model_info: Dict[str, Any]) -> SearchResult:
        """Use Qwen agent to search for a model."""
        filename = model_info['filename']

        # Create unique result file
        safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        result_file = self.temp_dir / f"qwen_result_{safe_name}.json"

        # Build Qwen prompt
        prompt = self._build_qwen_prompt(model_info)

        try:
            # Run Qwen (this is a placeholder - actual implementation would call Qwen)
            # For now, return a mock result
            self.logger.info(f"Qwen search for: {filename}")

            # Mock Qwen execution - in real implementation, this would run:
            # subprocess.run(['qwen', '-p', prompt, '--yolo'], ...)

            # For demonstration, return NOT_FOUND
            return SearchResult(
                status='NOT_FOUND',
                filename=filename,
                metadata={
                    'civitai_searches': 0,
                    'huggingface_searches': 0,
                    'reason': 'Qwen integration not implemented yet'
                }
            )

        except Exception as e:
            self.logger.error(f"Qwen search error: {e}")
            return SearchResult(
                status='ERROR',
                filename=filename,
                error_message=str(e)
            )

    def _build_qwen_prompt(self, model_info: Dict[str, Any]) -> str:
        """Build the Qwen search prompt."""
        # This would be the full prompt from QWEN_SEARCH_IMPLEMENTATION_PLAN.md
        return f"Search for model: {model_info['filename']}"


class HuggingFaceSearch(SearchBackend):
    """HuggingFace model search backend."""

    def __init__(self, logger=None):
        super().__init__(logger)

    def get_name(self) -> str:
        return "huggingface"

    def search(self, model_info: Dict[str, Any]) -> SearchResult:
        """Search HuggingFace for a model."""
        filename = model_info['filename']

        # For now, return NOT_FOUND as HuggingFace search is complex
        # Real implementation would use web search or API
        self.logger.info(f"HuggingFace search for: {filename}")

        return SearchResult(
            status='NOT_FOUND',
            filename=filename,
            metadata={'reason': 'HuggingFace search not implemented yet'}
        )


class ModelSearch:
    """
    Unified model search coordinator.

    Manages multiple search backends and provides caching, validation,
    and result management.
    """

    def __init__(self, state_manager: Optional[StateManager] = None,
                 cache_dir: Optional[str] = None, logger=None):
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
        self.backends: Dict[str, SearchBackend] = {
            'civitai': CivitaiSearch(logger=self.logger),
            'huggingface': HuggingFaceSearch(logger=self.logger)
            # 'qwen' is deprecated/placeholder, so we leave it out for now
        }

        # Conditionally register ModelScope backend
        if MODELSCOPE_AVAILABLE and ModelScopeSearch and config.copilot.enable_modelscope:
            self.logger.info("ModelScope backend enabled and available, adding to search backends.")
            self.backends['modelscope'] = ModelScopeSearch(logger=self.logger)
        elif MODELSCOPE_AVAILABLE and ModelScopeSearch and not config.copilot.enable_modelscope:
            self.logger.info("ModelScope backend available but disabled in configuration.")
        elif MODELSCOPE_AVAILABLE and not ModelScopeSearch:
            self.logger.warning("ModelScope package available but ModelScopeSearch import failed.")
        else:
            self.logger.info("ModelScope backend not available.")

        # Validate and set backend order
        self._validate_backend_order()

        # Setup caching
        self.cache_dir = Path(cache_dir or config.temp_dir) / "search_cache"
        self.cache_dir.mkdir(exist_ok=True)

    def search_model(self, model_info: Dict[str, Any],
                     use_cache: bool = True) -> SearchResult:
        """
        Search for a model using the configured backend order.

        Args:
            model_info: Dictionary with model information
            use_cache: Whether to use cached results

        Returns:
            SearchResult object
        """
        filename = model_info['filename']

        # Check cache first
        if use_cache and config.search.enable_cache:
            cached_result = self._get_cached_result(filename)
            if cached_result:
                self.logger.info(f"Using cached result for {filename}")
                return cached_result

        # Use the backend order from the global config
        backends_to_try = config.search.backend_order

        # Try each backend in the configured order
        for backend_name in backends_to_try:
            if backend_name not in self.backends:
                self.logger.warning(f"Configured backend '{backend_name}' is not available or unknown.")
                continue

            backend = self.backends[backend_name]
            self.logger.info(f"Trying '{backend_name}' search for '{filename}'")

            result = backend.search(model_info)

            # Cache successful results
            if result.status == 'FOUND' and use_cache and config.search.enable_cache:
                self._cache_result(result)

            # Mark attempt in state manager
            if self.state_manager:
                self.state_manager.mark_download_attempted(
                    filename, model_info, result.__dict__ if result.status == 'FOUND' else None
                )

            # Return if found or if it's a critical error (don't try other backends)
            if result.status in ['FOUND', 'ERROR', 'INVALID_FILENAME']:
                return result

        # If all backends returned NOT_FOUND
        return SearchResult(
            status='NOT_FOUND',
            filename=filename,
            metadata={
                'backends_tried': backends_to_try,
                'reason': f'No results from configured backends'
            }
        )

    def search_multiple_models(self, models: List[Dict[str, Any]],
                             use_cache: bool = True) -> List[SearchResult]:
        """
        Search for multiple models.

        Args:
            models: List of model info dictionaries
            backends: List of backend names to try
            use_cache: Whether to use cached results

        Returns:
            List of SearchResult objects
        """
        results = []
        for model in models:
            result = self.search_model(model, use_cache)
            results.append(result)

            # Small delay to be respectful to APIs
            time.sleep(0.5)

        return results

    def _get_cached_result(self, filename: str) -> Optional[SearchResult]:
        """Get cached search result."""
        cache_file = self.cache_dir / f"{sanitize_filename(filename)}.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            return SearchResult(**data)
        except Exception:
            return None

    def _cache_result(self, result: SearchResult) -> None:
        """Cache a search result."""
        cache_file = self.cache_dir / f"{sanitize_filename(result.filename)}.json"
        try:
            with open(cache_file, 'w') as f:
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
            'cached_results': len(cache_files),
            'cache_dir': str(self.cache_dir),
            'backends_available': list(self.backends.keys())
        }

    def _validate_backend_order(self):
        """Validate the configured backend order against available backends."""
        configured_order = config.search.backend_order
        available_backends = set(self.backends.keys())

        # Filter out invalid backends
        valid_order = [backend for backend in configured_order if backend in available_backends]

        # Log warnings for invalid backends
        invalid_backends = [backend for backend in configured_order if backend not in available_backends]
        if invalid_backends:
            self.logger.warning(f"Configured backends not available: {invalid_backends}. "
                              f"Available backends: {list(available_backends)}")

        # If no valid backends remain, fall back to default order
        if not valid_order:
            valid_order = list(available_backends)
            self.logger.warning("No valid backends in configured order, falling back to all available backends")

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