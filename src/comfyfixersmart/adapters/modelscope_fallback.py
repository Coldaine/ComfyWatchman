"""
Fallback ModelScope implementation for when copilot_backend is not available.

This module provides a minimal implementation of the ModelScope gateway interface
that can be used when the actual ComfyUI-Copilot backend is not available.
"""

import logging
from typing import Any, Dict, Optional


class ModelScopeGatewayFallback:
    """
    Fallback implementation of ModelScopeGateway for when copilot_backend is not available.

    This provides the same interface as the real ModelScopeGateway but returns
    appropriate error messages or empty results.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Using fallback ModelScope gateway (copilot_backend not available)")

    def suggest(self, name: str, page_size: int = 10, page: int = 1) -> Dict[str, Any]:
        """
        Fallback suggest method that returns empty results.

        Args:
            name: Model name to search for
            page_size: Number of results per page
            page: Page number

        Returns:
            Empty result dictionary
        """
        self.logger.warning(f"ModelScope search not available (fallback mode): {name}")
        return {"data": None}

    def search_models(self, keyword: str, page_size: int = 10, page: int = 1) -> Dict[str, Any]:
        """
        Fallback search method that returns empty results.

        Args:
            keyword: Search keyword
            page_size: Number of results per page
            page: Page number

        Returns:
            Empty result dictionary
        """
        self.logger.warning(f"ModelScope search not available (fallback mode): {keyword}")
        return {"data": None}

    def download_with_sdk(
        self, model_id: str, model_type: str, dest_dir: Optional[str] = None
    ) -> str:
        """
        Fallback download method that raises an error.

        Args:
            model_id: Model ID to download
            model_type: Type of model
            dest_dir: Destination directory

        Returns:
            None (raises RuntimeError)

        Raises:
            RuntimeError: Always raised since download is not available in fallback mode
        """
        error_msg = f"ModelScope download not available (fallback mode): {model_id}"
        self.logger.error(error_msg)
        raise RuntimeError(error_msg)

    def get_model_size(self, path: str, name: str, rversion: str = "master") -> int:
        """
        Fallback method that returns 0 for model size.

        Args:
            path: Model path
            name: Model name
            rversion: Model version

        Returns:
            0 (since model is not available)
        """
        self.logger.warning(f"ModelScope size query not available (fallback mode): {path}/{name}")
        return 0
