"""
ModelScope Search Adapter for ComfyFixerSmart

Provides integration with ModelScope for searching models.
This adapter leverages the ModelScope gateway from ComfyUI-Copilot when available.
"""

import json
import logging
from typing import Dict, List, Optional, Any

from ..search import SearchBackend, SearchResult
from ..logging import get_logger


class ModelScopeSearch(SearchBackend):
    """
    ModelScope search backend for finding models on ModelScope platform.
    
    This adapter integrates with ModelScope through the ComfyUI-Copilot
    ModelScope gateway when available, providing access to ModelScope's
    extensive model repository.
    """

    def __init__(self, logger=None):
        super().__init__(logger)
        self.gateway = None
        self._initialize_gateway()

    def get_name(self) -> str:
        return "modelscope"

    def _initialize_gateway(self) -> bool:
        """Initialize the ModelScope gateway if available."""
        try:
            # Import the ModelScope gateway from ComfyUI-Copilot
            from ..adapters.copilot_backend.backend.utils.modelscope_gateway import ModelScopeGateway
            self.gateway = ModelScopeGateway()
            self.logger.info("ModelScope gateway initialized successfully")
            return True
        except ImportError as e:
            self.logger.warning(f"Failed to initialize ModelScope gateway: {e}")
            return False

    def search(self, model_info: Dict[str, Any]) -> SearchResult:
        """
        Search ModelScope for a model.
        
        Args:
            model_info: Dictionary containing model information including filename
            
        Returns:
            SearchResult with model information if found
        """
        filename = model_info['filename']
        model_type = model_info.get('type', '')
        
        self.logger.info(f"Searching ModelScope for: {filename}")
        
        if not self.gateway:
            return SearchResult(
                status='ERROR',
                filename=filename,
                error_message="ModelScope gateway not available"
            )
        
        try:
            # Prepare search query from filename
            query = self._prepare_search_query(filename)
            
            # Search ModelScope
            results = self.gateway.search_models(
                query=query,
                model_type=self._map_model_type(model_type),
                limit=10
            )
            
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
            self.logger.error(f"ModelScope search error: {e}")
            return SearchResult(
                status='ERROR',
                filename=filename,
                error_message=str(e)
            )
    
    def _prepare_search_query(self, filename: str) -> str:
        """
        Prepare filename for search query by cleaning and formatting.
        
        Args:
            filename: Original model filename
            
        Returns:
            Cleaned search query string
        """
        import re
        
        # Remove extension and clean up
        query = filename.replace('.safetensors', '').replace('.ckpt', '').replace('.pth', '').replace('.pt', '').replace('.bin', '')
        # Replace underscores and dots with spaces
        query = re.sub(r'[_.]', ' ', query)
        return query.strip()
    
    def _map_model_type(self, model_type: str) -> str:
        """
        Map ComfyUI model types to ModelScope model types.
        
        Args:
            model_type: ComfyUI model type
            
        Returns:
            ModelScope model type
        """
        type_mapping = {
            'checkpoints': 'Stable-diffusion',
            'loras': 'LoRA',
            'vae': 'VAE',
            'controlnet': 'ControlNet',
            'upscale_models': 'Super-resolution',
            'clip': 'Text-to-Image',
            'unet': 'Stable-diffusion'
        }
        return type_mapping.get(model_type, 'General')
    
    def _find_best_match(self, results: List[Dict], target_filename: str) -> Optional[Dict]:
        """
        Find the best matching result from ModelScope search results.
        
        Args:
            results: List of ModelScope search results
            target_filename: Target filename to match
            
        Returns:
            Best matching result or None
        """
        target_base = target_filename.lower().replace('.safetensors', '').replace('.ckpt', '').replace('.pth', '').replace('.pt', '').replace('.bin', '')
        
        for result in results:
            model_name = result.get('name', '').lower()
            # Simple matching - can be enhanced with more sophisticated matching
            if target_base in model_name or model_name in target_base:
                return result
                
        return None
    
    def _create_result_from_match(self, result: Dict, filename: str, confidence: str) -> SearchResult:
        """
        Create a SearchResult from a ModelScope match.
        
        Args:
            result: ModelScope search result
            filename: Original filename
            confidence: Match confidence level
            
        Returns:
            SearchResult object
        """
        return SearchResult(
            status='FOUND',
            filename=filename,
            source='modelscope',
            civitai_name=result.get('name', ''),
            version_name=result.get('version', ''),
            download_url=result.get('download_url', ''),
            confidence=confidence,
            metadata={
                'model_id': result.get('id', ''),
                'search_attempts': 1,
                'modelscope_info': result
            }
        )# Kilo Experiment - ModelScope Search Adapter
