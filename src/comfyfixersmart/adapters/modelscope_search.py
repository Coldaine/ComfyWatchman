"""
ModelScope Search Adapter for ComfyFixerSmart

Provides a search backend that integrates with the ModelScope utilities
forked from the ComfyUI-Copilot repository. Implements both the CopilotAdapter
interface for Copilot integration and the SearchBackend interface for
model search functionality.
"""

from ..logging import get_logger
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import sys
sys.path.append('/home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart/src')
from adapters.base import CopilotAdapter

if TYPE_CHECKING:
    from ..search import SearchBackend, SearchResult

from ..search import SearchBackend, SearchResult
# Feature detection from our new __init__.py
from . import MODELSCOPE_AVAILABLE

# Conditionally import from the forked submodule
if MODELSCOPE_AVAILABLE:
    try:
        # This path assumes the submodule is at src/copilot_backend
        # We may need to adjust sys.path if imports fail
        from ..copilot_backend.backend.utils.modelscope_gateway import ModelScopeGateway
    except (ImportError, ModuleNotFoundError):
        # Handle cases where the submodule is present but has issues
        ModelScopeGateway = None
else:
    ModelScopeGateway = None


class ModelScopeAdapter(CopilotAdapter):
    """
    Adapter for ModelScope search functionality from ComfyUI-Copilot.

    This adapter wraps the ModelScope gateway functionality and provides
    a clean interface for searching models on the ModelScope platform.
    """

    def __init__(self, name: str = "modelscope", description: str = "ModelScope model search and download"):
        super().__init__(name, description)
        self._gateway = None

    def is_available(self) -> bool:
        """Check if ModelScope dependencies are available."""
        return MODELSCOPE_AVAILABLE and ModelScopeGateway is not None

    def initialize(self) -> bool:
        """Initialize the ModelScope gateway."""
        if not self.is_available():
            self.logger.warning("ModelScope dependencies not available")
            return False

        try:
            self._gateway = ModelScopeGateway()
            self._initialized = True
            self.logger.info("ModelScopeAdapter initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize ModelScopeAdapter: {e}")
            return False

    def get_capabilities(self) -> List[str]:
        """Return the capabilities provided by this adapter."""
        if not self.is_available():
            return []

        return [
            "model_search",
            "model_download",
            "modelscope_integration"
        ]

    def execute(self, operation: str, **kwargs) -> Any:
        """
        Execute a ModelScope operation.

        Args:
            operation: The operation to perform ('search', 'download', etc.)
            **kwargs: Operation-specific parameters

        Returns:
            Operation result

        Raises:
            NotImplementedError: If operation is not supported
            RuntimeError: If adapter is not initialized or operation fails
        """
        if not self._initialized:
            raise RuntimeError("ModelScopeAdapter is not initialized")

        if operation == "search":
            return self._search_models(**kwargs)
        elif operation == "download":
            return self._download_model(**kwargs)
        else:
            raise NotImplementedError(f"Operation '{operation}' not supported by ModelScopeAdapter")

    def _search_models(self, query: str, model_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for models on ModelScope.

        Args:
            query: Search query (model name or filename)
            model_type: Optional model type filter
            limit: Maximum number of results to return

        Returns:
            List of model dictionaries from ModelScope
        """
        if not self._gateway:
            raise RuntimeError("ModelScope gateway not initialized")

        try:
            # Use the suggest method for fuzzy search
            result = self._gateway.suggest(
                name=query,
                page_size=min(limit, 30),  # ModelScope max is 30
                page=1
            )

            if result.get("data"):
                # Return raw ModelScope results
                return result["data"][:limit]
            else:
                self.logger.warning(f"No results found for query: {query}")
                return []

        except Exception as e:
            self.logger.error(f"ModelScope search failed for query '{query}': {e}")
            raise RuntimeError(f"ModelScope search failed: {e}") from e

    def _download_model(self, model_id: str, model_type: str, dest_dir: Optional[str] = None) -> str:
        """
        Download a model from ModelScope.

        Args:
            model_id: ModelScope model ID (path/name format)
            model_type: ComfyUI model type
            dest_dir: Optional destination directory

        Returns:
            Path to downloaded model
        """
        if not self._gateway:
            raise RuntimeError("ModelScope gateway not initialized")

        try:
            return self._gateway.download_with_sdk(
                model_id=model_id,
                model_type=model_type,
                dest_dir=dest_dir
            )
        except Exception as e:
            self.logger.error(f"ModelScope download failed for model '{model_id}': {e}")
            raise RuntimeError(f"ModelScope download failed: {e}") from e


class ModelScopeSearch(SearchBackend):



















    """
    Search backend that uses the ModelScopeAdapter for finding models.

    This backend integrates with ComfyUI-Copilot's ModelScope functionality
    through the adapter pattern, providing graceful degradation when
    dependencies are not available.
    """

    def __init__(self, logger=None):
        super().__init__(logger)
        self.adapter = ModelScopeAdapter()
        self.enabled = self.adapter.initialize()

        if not self.enabled:
            self.logger.warning("ModelScopeSearch backend disabled due to initialization failure")

    def get_name(self) -> str:
        return "modelscope"

    def search(self, model_info: Dict[str, Any]) -> "SearchResult":
        """
        Search for a model using ModelScope.

        Args:
            model_info: Dictionary containing model details ('filename', 'type', etc.)

        Returns:
            SearchResult object with found model information or error status
        """
        if not self.enabled:
            return SearchResult(
                status='ERROR',
                filename=model_info['filename'],
                source=self.get_name(),
                error_message="ModelScope backend is not available or failed to initialize."
            )

        filename = model_info['filename']
        model_type = model_info.get('type', 'checkpoints')

        self.logger.info(f"Searching ModelScope for: {filename}")

        try:
            # Search using the adapter
            results = self.adapter.execute(
                "search",
                query=filename,
                model_type=model_type,
                limit=5  # Get top 5 results
            )

            if not results:
                return SearchResult(
                    status='NOT_FOUND',
                    filename=filename,
                    source=self.get_name(),
                    metadata={'reason': f'No ModelScope results for {filename}'}
                )

            # Take the best result (first one)
            best_match = results[0]

            # Convert ModelScope result to SearchResult format
            return SearchResult(
                status='FOUND',
                filename=filename,
                source=self.get_name(),
                download_url=self._construct_download_url(best_match),
                confidence=self._calculate_confidence(filename, best_match),
                metadata={
                    'modelscope_id': f"{best_match.get('Path', '')}/{best_match.get('Name', '')}",
                    'modelscope_name': best_match.get('Name', ''),
                    'modelscope_path': best_match.get('Path', ''),
                    'chinese_name': best_match.get('ChineseName', ''),
                    'downloads': best_match.get('Downloads', 0),
                    'libraries': best_match.get('Libraries', []),
                    'last_updated': best_match.get('LastUpdatedTime', '')
                }
            )

        except Exception as e:
            self.logger.error(f"ModelScope search failed for '{filename}': {e}")
            return SearchResult(
                status='ERROR',
                filename=filename,
                source=self.get_name(),
                error_message=str(e)
            )

    def _construct_download_url(self, model_data: Dict[str, Any]) -> str:
        """
        Construct a download URL from ModelScope model data.

        Args:
            model_data: Model data from ModelScope API

        Returns:
            Download URL string
        """
        path = model_data.get('Path', '')
        name = model_data.get('Name', '')

        if path and name:
            # ModelScope download URL format
            return f"https://modelscope.cn/api/v1/models/{path}/{name}/repo?Revision=master"
        else:
            return ""

    def _calculate_confidence(self, query_filename: str, model_data: Dict[str, Any]) -> str:
        """
        Calculate confidence level for a search result.

        Args:
            query_filename: Original filename searched for
            model_data: Model data from search result

        Returns:
            Confidence level string ('exact', 'high', 'medium', 'low')
        """
        model_name = model_data.get('Name', '').lower()
        query_name = query_filename.lower().replace('.safetensors', '').replace('.ckpt', '').replace('.pth', '')

        # Exact match
        if model_name == query_name:
            return 'exact'

        # Contains the query
        if query_name in model_name or model_name in query_name:
            return 'high'

        # Similar words
        query_words = set(query_name.split())
        model_words = set(model_name.split())

        if query_words & model_words:
            return 'medium'

        return 'low'