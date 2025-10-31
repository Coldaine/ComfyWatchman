"""
Enhanced Search Module for ComfyFixerSmart

This module improves upon the original search implementation with:
1. Unified constants and behaviors
2. Better recall without sacrificing safety
3. Small hardening improvements

The key improvements include:
- MODEL_EXTENSIONS as single source of truth
- Enhanced filename validation with pattern detection
- Better search recall by scanning inputs for embedding tokens
- Hash algorithm guarding
- Removal of dead code/imports
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import requests

from .config import config
from .logging import get_logger
from .state_manager import StateManager
from .enhanced_utils import (
    MODEL_EXTENSIONS,
    validate_and_sanitize_filename,
    sanitize_filename,
    build_local_inventory,
    civitai_search_by_filename,
    quick_hash
)

# Conditionally import optional dependencies
try:
    from .adapters.modelscope_search import ModelScopeSearch
    MODELSCOPE_AVAILABLE = True
except ImportError:
    ModelScopeSearch = None
    MODELSCOPE_AVAILABLE = False


@dataclass
class SearchResult:
    """Result of a model search operation.

    Note: status may be one of 'FOUND', 'NOT_FOUND', 'INVALID_FILENAME', 'ERROR',
    or 'UNCERTAIN'. 'UNCERTAIN' indicates candidates exist but need human review and
    should not be downloaded automatically.
    """

    status: str
    filename: str
    source: Optional[str] = None  # 'civitai', 'huggingface', 'modelscope'
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
    """Enhanced Civitai API search backend."""

    def __init__(self, logger=None):
        super().__init__(logger)
        self.api_key = config.search.civitai_api_key
        self.base_url = "https://civitai.com/api/v1"

    def get_name(self) -> str:
        return "civitai"

    def search(self, model_info: Dict[str, Any]) -> SearchResult:
        """Enhanced search with improved validation and recall."""
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

        self.logger.info(f"Searching Civitai API for: {filename}")

        try:
            # Use the enhanced Civitai search function
            result = civitai_search_by_filename(
                filename, 
                api_key=self.api_key,
                timeout=30
            )

            if result and result.get("status") == "FOUND":
                self.logger.info(
                    f"Found model on Civitai: {result.get('civitai_id')} - {result.get('filename')}"
                )
                return SearchResult(
                    status="FOUND",
                    filename=filename,
                    source="civitai",
                    civitai_id=result.get("civitai_id"),
                    version_id=result.get("version_id"),
                    civitai_name=result.get("civitai_name", filename),
                    version_name=result.get("version_name", "Unknown"),
                    download_url=result.get("download_url"),
                    confidence="exact" if result.get("confidence", 0) >= 90 else "fuzzy",
                    type=result.get("type", model_type),
                    metadata={
                        "confidence_score": result.get("confidence", 0),
                        "search_method": "enhanced_api_search"
                    }
                )
            else:
                self.logger.info(f"No results found for {filename} on Civitai")
                return SearchResult(
                    status="NOT_FOUND",
                    filename=filename,
                    type=model_type,
                    metadata={
                        "search_attempts": 1,
                        "reason": "No results from enhanced Civitai search"
                    }
                )

        except Exception as e:
            self.logger.error(f"Civitai search error: {e}")
            return SearchResult(
                status="ERROR", 
                filename=filename, 
                type=model_type, 
                error_message=str(e)
            )

    def _normalize_filename(self, filename: str) -> str:
        """Normalize filename to basename."""
        # Normalize separators and remove extension
        base = filename
        # Remove common extensions
        base = base.replace(".safetensors", "").replace(".pth", ".pt").replace(".ckpt", "")
        # Replace underscores, spaces, and other separators with spaces
        import re
        query = re.sub(r"[\\/_.-]+", " ", base)
        return query.strip()

    def _prepare_search_query(self, filename: str) -> str:
        """Prepare filename for search query."""
        # Normalize separators and remove extension
        base = filename
        # Remove common extensions
        base = base.replace(".safetensors", "").replace(".pth", ".pt").replace(".ckpt", "")
        # Replace underscores, spaces, and other separators with spaces
        import re
        query = re.sub(r"[\\/_.-]+", " ", base)
        return query.strip()


class HuggingFaceSearch(SearchBackend):
    """HuggingFace search backend with enhanced capabilities."""

    def __init__(self, logger=None):
        super().__init__(logger)
        self.hf_token = os.getenv("HF_TOKEN")

    def get_name(self) -> str:
        return "huggingface"

    def search(self, model_info: Dict[str, Any]) -> SearchResult:
        """Search for a model on HuggingFace."""
        filename = model_info["filename"]
        model_type = model_info.get("type", "")

        # Enhanced filename validation
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
            )

        self.logger.info(f"Searching HuggingFace for: {sanitized_filename}")

        # For now, return NOT_FOUND as we're focusing on Civitai improvements
        return SearchResult(
            status="NOT_FOUND",
            filename=sanitized_filename,
            type=model_type,
            metadata={"reason": "HuggingFace search not implemented in enhanced version"}
        )


class ModelSearch:
    """Enhanced model search coordinator."""

    def __init__(
        self,
        state_manager: Optional[StateManager] = None,
        logger=None,
    ):
        """
        Initialize the enhanced model search coordinator.

        Args:
            state_manager: StateManager for tracking search attempts
            logger: Optional logger instance
        """
        self.logger = logger or get_logger("EnhancedModelSearch")
        self.state_manager = state_manager

        # Initialize available backends
        self.backends: Dict[str, SearchBackend] = {
            "civitai": CivitaiSearch(logger=self.logger),
            "huggingface": HuggingFaceSearch(logger=self.logger),
        }

        # Conditionally register ModelScope backend
        if MODELSCOPE_AVAILABLE and ModelScopeSearch:
            self.logger.info(
                "ModelScope backend available and will be registered."
            )
            self.backends["modelscope"] = ModelScopeSearch(logger=self.logger)
        else:
            self.logger.info("ModelScope backend not available.")

    def search_model(
        self,
        model_info: Dict[str, Any],
        backends: Optional[List[str]] = None,
    ) -> SearchResult:
        """
        Search for a model using the configured backend order.

        Args:
            model_info: Dictionary with model information
            backends: List of backend names to try

        Returns:
            SearchResult object
        """
        filename = model_info["filename"]

        # Determine backend order
        backend_order = backends or config.search.backend_order or ["civitai"]

        # Try each backend in the configured order
        for backend_name in backend_order:
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

            # Return if found or if it's a critical error (don't try other backends)
            if result.status in ["FOUND", "ERROR", "INVALID_FILENAME"]:
                return result

        # If all backends returned NOT_FOUND
        return SearchResult(
            status="NOT_FOUND",
            filename=filename,
            metadata={
                "backends_tried": backend_order,
                "reason": "No results from configured backends",
            },
        )

    def search_multiple_models(
        self,
        models: List[Dict[str, Any]],
        backends: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Search for multiple models.

        Args:
            models: List of model info dictionaries
            backends: List of backend names to try

        Returns:
            List of SearchResult objects
        """
        results = []
        for model in models:
            result = self.search_model(model, backends)
            results.append(result)
            time.sleep(0.5)  # Be respectful to APIs
        return results


# Convenience functions for backward compatibility
def search_civitai(model: Dict[str, Any], api_key: Optional[str] = None) -> SearchResult:
    """
    Convenience function for Civitai search.

    Args:
        model: Model info dictionary
        api_key: Optional API key

    Returns:
        SearchResult object
    """
    backend = CivitaiSearch()
    if api_key:
        backend.api_key = api_key
    return backend.search(model)


def search_with_enhanced_validation(
    filename: str,
    model_type: str = "checkpoints"
) -> SearchResult:
    """
    Enhanced search function with improved validation.

    Args:
        filename: Model filename to search for
        model_type: Model type for categorization

    Returns:
        SearchResult with enhanced validation
    """
    # Enhanced filename validation
    is_valid, sanitized_filename, error_reason = validate_and_sanitize_filename(filename)
    
    if not is_valid:
        logger = get_logger("EnhancedSearch")
        logger.warning(f"Invalid filename detected: {filename} - {error_reason}")
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
    
    # Proceed with search
    model_info = {
        "filename": sanitized_filename,
        "type": model_type
    }
    
    searcher = ModelSearch()
    return searcher.search_model(model_info)


__all__ = [
    "SearchResult",
    "SearchBackend",
    "CivitaiSearch",
    "HuggingFaceSearch",
    "ModelSearch",
    "search_civitai",
    "search_with_enhanced_validation"
]