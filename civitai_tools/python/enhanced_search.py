"""
Enhanced Civitai Search Backend

Implements multi-strategy search with direct ID lookup, tag-based search,
and other advanced techniques to overcome Civitai API limitations.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests

from ..search import CivitaiSearch, SearchResult
from ..config import config
from ..logging import get_logger
from ..utils import get_api_key


class EnhancedCivitaiSearch(CivitaiSearch):
    """
    Enhanced Civitai search backend with additional strategies.
    
    This extends the base CivitaiSearch class with additional capabilities
    for handling problematic NSFW searches and direct ID lookups.
    """
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.api_key = config.search.civitai_api_key or get_api_key()
        self.base_url = "https://civitai.com/api/v1"

    def _try_browsing_levels(self, query: str, model_type: str) -> Optional[SearchResult]:
        """
        EXPERIMENTAL: Attempt to use browsingLevel parameter.
        Try levels 4, 8, 16 (R, X, XXX) sequentially.
        If ZodError occurs, fall back to nsfw=true.
        """
        # Browsing levels: PG=1, PG13=2, R=4, X=8, XXX=16
        browsing_levels = [4, 8, 16]  # R, X, XXX - typically NSFW content levels
        
        for level in browsing_levels:
            try:
                params = {
                    'query': query,
                    'browsingLevel': level,
                    'limit': 5,
                    'sort': 'Highest Rated'
                }

                type_filter = self._get_type_filter(model_type)
                if type_filter:
                    params['types'] = type_filter

                headers = {}
                if self.api_key:
                    headers['Authorization'] = f'Bearer {self.api_key}'

                response = requests.get(
                    f"{self.base_url}/models",
                    params=params,
                    headers=headers,
                    timeout=30
                )

                # If we get a 422 or similar error related to browsingLevel, 
                # this suggests the parameter might not work with query search
                if response.status_code == 422 or 'error' in response.text.lower():
                    self.logger.warning(f"Browsing level {level} failed, trying next level")
                    continue

                if response.status_code != 200:
                    continue

                data = response.json()
                if not data.get('items'):
                    continue

                # Process the first result as a potential match
                item = data['items'][0]
                for version in item.get('modelVersions', []):
                    for file_info in version.get('files', []):
                        # Create a result, but mark it as experimental
                        result = self._create_result_from_match(item, version, query, model_type, 'fuzzy')
                        if result.metadata:
                            result.metadata['browsing_level'] = level
                            result.metadata['search_strategy'] = 'browsing_level'
                        else:
                            result.metadata = {
                                'browsing_level': level,
                                'search_strategy': 'browsing_level'
                            }
                        return result

            except Exception as e:
                self.logger.warning(f"Browsing level {level} search failed: {e}")
                continue

        # If browsing levels failed, fall back to nsfw=true
        self.logger.info("Falling back to nsfw=true search after browsing level attempts")
        return None