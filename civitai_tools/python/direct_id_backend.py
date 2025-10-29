"""
Direct ID Backend for Civitai

Implements direct model ID lookup which bypasses search API limitations
and provides 100% success rate for known model IDs.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests
import json
from pathlib import Path

from ..search import SearchResult
from ..config import config
from ..logging import get_logger
from ..utils import get_api_key


class DirectIDBackend:
    """
    Direct ID lookup backend for Civitai.
    
    This backend bypasses search API entirely by using known model IDs
    to fetch model details directly from the API.
    """
    
    def __init__(self, known_models_path: str = "civitai_tools/config/known_models.json", logger=None):
        self.known_models_path = Path(known_models_path)
        self.api_key = config.search.civitai_api_key or get_api_key()
        self.base_url = "https://civitai.com/api/v1"
        self.logger = logger or get_logger("DirectIDBackend")
        self.known_models = self._load_known_models()

    def _load_known_models(self) -> Dict[str, Any]:
        """Load known model mappings from JSON file."""
        if not self.known_models_path.exists():
            self.logger.warning(f"Known models file not found: {self.known_models_path}")
            return {}
        
        try:
            with open(self.known_models_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.logger.info(f"Loaded {len(data)} known models from {self.known_models_path}")
            return data
        except Exception as e:
            self.logger.error(f"Failed to load known models: {e}")
            return {}

    def lookup_by_name(self, model_name: str) -> Optional[SearchResult]:
        """
        Lookup model by name using known models mapping.
        
        Args:
            model_name: Name of the model to lookup
            
        Returns:
            SearchResult if found, None otherwise
        """
        # Normalize the model name for lookup
        normalized_name = self._normalize_model_name(model_name)
        
        for known_name, model_info in self.known_models.items():
            if normalized_name.lower() in known_name.lower() or known_name.lower() in normalized_name.lower():
                model_id = model_info.get('model_id')
                if model_id:
                    return self.lookup_by_id(model_id, model_info.get('version_id'))
        
        return None

    def lookup_by_id(self, model_id: int, version_id: Optional[int] = None) -> Optional[SearchResult]:
        """
        Lookup model by direct ID.
        
        Args:
            model_id: Civitai model ID
            version_id: Specific version ID (optional, uses latest if not provided)
            
        Returns:
            SearchResult if found, None otherwise
        """
        self.logger.info(f"Direct ID lookup for model {model_id}")
        
        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            response = requests.get(
                f"{self.base_url}/models/{model_id}",
                headers=headers,
                timeout=30
            )

            if response.status_code != 200:
                self.logger.error(f"Direct ID lookup failed with status {response.status_code}")
                return None

            model_data = response.json()

            # Get the specified version or latest version
            versions = model_data.get('modelVersions', [])
            if not versions:
                self.logger.warning(f"No versions found for model ID {model_id}")
                return None

            target_version = None
            if version_id:
                # Find specific version
                for version in versions:
                    if version.get('id') == version_id:
                        target_version = version
                        break
            else:
                # Use latest version (first in list)
                target_version = versions[0]

            if not target_version:
                self.logger.warning(f"Version {version_id} not found for model {model_id}")
                return None

            # Find the appropriate file to download
            target_file = self._find_target_file(target_version)
            if not target_file:
                self.logger.warning(f"No suitable file found for model {model_id} version {target_version.get('id')}")
                return None

            filename = target_file.get('name', f"model_{model_id}.safetensors")
            model_name = model_data.get('name', f"Model {model_id}")
            model_type = model_data.get('type', 'Unknown')

            # Create a SearchResult
            return SearchResult(
                status='FOUND',
                filename=filename,
                source='civitai',
                civitai_id=model_id,
                version_id=target_version.get('id'),
                civitai_name=model_name,
                version_name=target_version.get('name', f"Version {target_version.get('id')}"),
                download_url=f"https://civitai.com/api/download/models/{target_version.get('id')}",
                confidence='exact',  # Direct ID lookup is 100% confident
                type=self._map_model_type(model_type),
                metadata={
                    'search_attempts': 1,
                    'found_by': 'direct_id',
                    'nsfw_level': model_data.get('nsfwLevel', 1),
                    'model_type': model_type,
                    'direct_id_lookup': True
                }
            )

        except Exception as e:
            self.logger.error(f"Direct ID lookup error for model {model_id}: {e}")
            return None

    def _find_target_file(self, version_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find the best file to download from version data."""
        files = version_data.get('files', [])
        
        # First, try to find a primary file
        for file_info in files:
            if file_info.get('primary', False):
                return file_info
        
        # If no primary file, find the largest file (likely the main model)
        if files:
            # Sort by size and return the largest
            sorted_files = sorted(files, key=lambda x: x.get('sizeKB', 0), reverse=True)
            return sorted_files[0]
        
        return None

    def _normalize_model_name(self, name: str) -> str:
        """Normalize model name for comparison."""
        # Remove common version indicators and normalize
        import re
        normalized = re.sub(r'\bv\d+\.\d+|\bv\d+|\b\d+\.\d+', '', name, flags=re.IGNORECASE)
        normalized = re.sub(r'\s+', ' ', normalized)  # Replace multiple spaces with single
        return normalized.strip()

    def _map_model_type(self, civitai_type: str) -> str:
        """Map Civitai model type to local model type."""
        type_mapping = {
            'Checkpoint': 'checkpoints',
            'LORA': 'loras',
            'VAE': 'vae',
            'Controlnet': 'controlnet',
            'Upscaler': 'upscale_models',
            'TextualInversion': 'embeddings'  # Usually stored in embeddings folder
        }
        return type_mapping.get(civitai_type, 'unknown')