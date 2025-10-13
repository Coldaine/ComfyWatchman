"""
ModelScope Search Adapter for ComfyFixerSmart

Provides a search backend that integrates with the ModelScope utilities
forked from the ComfyUI-Copilot repository.
"""

from ..search import SearchBackend, SearchResult
from ..logging import get_logger
from typing import Dict, Any

# Feature detection from our new __init__.py
from . import MODELSCOPE_AVAILABLE

# Conditionally import from the forked submodule
if MODELSCOPE_AVAILABLE:
    try:
        # This path assumes the submodule is at src/copilot_backend
        # We may need to adjust sys.path if imports fail
        from ..copilot_backend.backend.utils import modelscope_gateway
    except (ImportError, ModuleNotFoundError):
        # Handle cases where the submodule is present but has issues
        modelscope_gateway = None
else:
    modelscope_gateway = None


class ModelScopeSearch(SearchBackend):
    """
    A search backend to find models using the ModelScope platform.

    This adapter calls the search logic present in the forked
    ComfyUI-Copilot codebase.
    """

    def __init__(self, logger=None):
        super().__init__(logger)
        if not MODELSCOPE_AVAILABLE or modelscope_gateway is None:
            self.logger.warning(
                "ModelScope dependencies not found. The ModelScopeSearch backend will be disabled."
            )
            self.enabled = False
        else:
            self.enabled = True
            self.logger.info("ModelScopeSearch backend initialized.")

    def get_name(self) -> str:
        return "modelscope"

    def search(self, model_info: Dict[str, Any]) -> SearchResult:
        """
        Search for a model on ModelScope.

        Args:
            model_info: A dictionary containing model details, like 'filename'.

        Returns:
            A SearchResult object.
        """
        if not self.enabled:
            return SearchResult(
                status='ERROR',
                filename=model_info['filename'],
                source=self.get_name(),
                error_message="ModelScope backend is not available or failed to initialize."
            )

        filename = model_info['filename']
        self.logger.info(f"Searching ModelScope for: {filename}")

        try:
            # NOTE: The forked 'modelscope_gateway.py' does not have a direct
            # filename search function. It has 'search_models' which takes a query.
            # We will adapt to use that. The original `parameter_tools.py` in Copilot
            # provides a better example of how it's used.
            # For now, we will implement a placeholder that simulates the call.

            # Placeholder logic:
            # In a real implementation, we would call a function like:
            # results = modelscope_gateway.search_models(query=filename, type_filter=model_info.get('type'))
            # and then parse 'results' to find the best match.

            self.logger.warning("ModelScope search is not yet implemented.")
            return SearchResult(
                status='ERROR',
                filename=filename,
                source=self.get_name(),
                error_message="ModelScope search is not yet implemented."
            )

        except Exception as e:
            self.logger.error(f"An unexpected error occurred during ModelScope search: {e}")
            return SearchResult(
                status='ERROR',
                filename=filename,
                source=self.get_name(),
                error_message=str(e)
            )
