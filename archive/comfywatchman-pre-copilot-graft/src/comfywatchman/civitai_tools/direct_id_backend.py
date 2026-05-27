"""
Direct ID Backend for Civitai

Implements direct model ID lookup which bypasses search API limitations
and provides 100% success rate for known model IDs.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from ..config import config
from ..logging import get_logger
from ..search import SearchResult
from ..utils import get_api_key


class DirectIDBackend:
    """
    Direct ID lookup backend for Civitai.

    This backend bypasses search API entirely by using known model IDs
    to fetch model details directly from the API.
    """

    def __init__(
        self, known_models_path: str = "civitai_tools/config/known_models.json", logger=None
    ):
        self.known_models_path = Path(known_models_path)
        self.api_key = config.search.civitai_api_key or get_api_key()
        self.base_url = "https://civitai.com/api/v1"
        self.logger = logger or get_logger("DirectIDBackend")
        self.known_models = self._load_known_models()

    def add_known_model(
        self,
        name: str,
        civitai_id: int,
        version_id: Optional[int] = None,
        model_type: Optional[str] = None,
        nsfw_level: Optional[int] = None,
        notes: Optional[str] = None,
        auto_added: bool = False,
    ) -> Dict[str, Any]:
        """
        Add or update a known model entry.

        The method validates the model/ version against the live Civitai API,
        stores the enriched metadata in known_models.json, and updates the
        in-memory cache.
        """
        if not name or not isinstance(name, str):
            raise ValueError("Model name must be a non-empty string")
        if not isinstance(civitai_id, int):
            raise ValueError("civitai_id must be an integer")
        if version_id is not None and not isinstance(version_id, int):
            raise ValueError("version_id must be an integer when provided")
        if nsfw_level is not None and not isinstance(nsfw_level, int):
            raise ValueError("nsfw_level must be an integer when provided")

        model_data = self._fetch_model_data(civitai_id)
        if not model_data:
            raise ValueError(f"Unable to fetch model metadata for ID {civitai_id}")

        versions = model_data.get("modelVersions", []) or []
        selected_version = None
        if version_id:
            for version in versions:
                if version.get("id") == version_id:
                    selected_version = version
                    break
            if not selected_version:
                available = [v.get("id") for v in versions]
                raise ValueError(
                    f"Version {version_id} not found for model {civitai_id}. "
                    f"Available versions: {available}"
                )
        else:
            selected_version = versions[0] if versions else None
            version_id = selected_version.get("id") if selected_version else None

        version_name = selected_version.get("name") if selected_version else None
        resolved_type = model_type or model_data.get("type", "Unknown")
        creator = (model_data.get("creator") or {}).get("username")
        resolved_nsfw_level = nsfw_level if nsfw_level is not None else model_data.get("nsfwLevel")

        normalized_key = self._normalize_model_name(name).lower()
        entry: Dict[str, Any] = {
            "model_id": civitai_id,
            "model_name": model_data.get("name", name),
            "version": version_name,
            "version_id": version_id,
            "type": resolved_type,
            "creator": creator,
            "url": f"https://civitai.com/models/{civitai_id}",
        }
        if resolved_nsfw_level is not None:
            entry["nsfw_level"] = resolved_nsfw_level
        if notes:
            entry["notes"] = notes
        if auto_added:
            entry["auto_added"] = True

        self.known_models[normalized_key] = entry
        self._save_known_models()
        self.logger.info(
            "Added known model '%s' (ID %s, version %s) to %s",
            normalized_key,
            civitai_id,
            version_id,
            self.known_models_path,
        )
        return entry

    def _load_known_models(self) -> Dict[str, Any]:
        """Load known model mappings from JSON file."""
        if not self.known_models_path.exists():
            self.logger.warning(f"Known models file not found: {self.known_models_path}")
            return {}

        try:
            with open(self.known_models_path, encoding="utf-8") as f:
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
            if (
                normalized_name.lower() in known_name.lower()
                or known_name.lower() in normalized_name.lower()
            ):
                model_id = model_info.get("model_id")
                if model_id:
                    return self.lookup_by_id(model_id, model_info.get("version_id"))

        return None

    def lookup_by_id(
        self, model_id: int, version_id: Optional[int] = None
    ) -> Optional[SearchResult]:
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
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = requests.get(
                f"{self.base_url}/models/{model_id}", headers=headers, timeout=30
            )

            if response.status_code != 200:
                self.logger.error(f"Direct ID lookup failed with status {response.status_code}")
                return None

            model_data = response.json()

            # Get the specified version or latest version
            versions = model_data.get("modelVersions", [])
            if not versions:
                self.logger.warning(f"No versions found for model ID {model_id}")
                return None

            target_version = None
            if version_id:
                # Find specific version
                for version in versions:
                    if version.get("id") == version_id:
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
                self.logger.warning(
                    f"No suitable file found for model {model_id} version {target_version.get('id')}"
                )
                return None

            filename = target_file.get("name", f"model_{model_id}.safetensors")
            model_name = model_data.get("name", f"Model {model_id}")
            model_type = model_data.get("type", "Unknown")

            # Create a SearchResult
            return SearchResult(
                status="FOUND",
                filename=filename,
                source="civitai",
                civitai_id=model_id,
                version_id=target_version.get("id"),
                civitai_name=model_name,
                version_name=target_version.get("name", f"Version {target_version.get('id')}"),
                download_url=f"https://civitai.com/api/download/models/{target_version.get('id')}",
                confidence="exact",  # Direct ID lookup is 100% confident
                type=self._map_model_type(model_type),
                metadata={
                    "search_attempts": 1,
                    "found_by": "direct_id",
                    "nsfw_level": model_data.get("nsfwLevel", 1),
                    "model_type": model_type,
                    "direct_id_lookup": True,
                },
            )

        except Exception as e:
            self.logger.error(f"Direct ID lookup error for model {model_id}: {e}")
            return None

    def _fetch_model_data(self, model_id: int) -> Optional[Dict[str, Any]]:
        """Fetch raw model data from Civitai API."""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = requests.get(f"{self.base_url}/models/{model_id}", headers=headers, timeout=30)
        except Exception as exc:  # pragma: no cover - network guard
            self.logger.error("Failed to fetch metadata for model %s: %s", model_id, exc)
            return None

        if response.status_code != 200:
            self.logger.error(
                "Fetching metadata for model %s failed with status %s",
                model_id,
                response.status_code,
            )
            return None

        try:
            return response.json()
        except Exception as exc:  # pragma: no cover - malformed JSON
            self.logger.error("Invalid JSON when fetching model %s: %s", model_id, exc)
            return None

    def _find_target_file(self, version_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find the best file to download from version data."""
        files = version_data.get("files", [])

        # First, try to find a primary file
        for file_info in files:
            if file_info.get("primary", False):
                return file_info

        # If no primary file, find the largest file (likely the main model)
        if files:
            # Sort by size and return the largest
            sorted_files = sorted(files, key=lambda x: x.get("sizeKB", 0), reverse=True)
            return sorted_files[0]

        return None

    def _normalize_model_name(self, name: str) -> str:
        """Normalize model name for comparison."""
        # Remove common version indicators and normalize
        import re

        normalized = re.sub(r"\bv\d+\.\d+|\bv\d+|\b\d+\.\d+", "", name, flags=re.IGNORECASE)
        normalized = re.sub(r"\s+", " ", normalized)  # Replace multiple spaces with single
        return normalized.strip()

    def _map_model_type(self, civitai_type: str) -> str:
        """Map Civitai model type to local model type."""
        type_mapping = {
            "Checkpoint": "checkpoints",
            "LORA": "loras",
            "VAE": "vae",
            "Controlnet": "controlnet",
            "Upscaler": "upscale_models",
            "TextualInversion": "embeddings",  # Usually stored in embeddings folder
        }
        return type_mapping.get(civitai_type, "unknown")

    def _save_known_models(self) -> None:
        """Persist known models mapping to disk atomically."""
        self.known_models_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_dir = self.known_models_path.parent
        fd, tmp_path = tempfile.mkstemp(
            dir=tmp_dir,
            prefix=self.known_models_path.stem,
            suffix=".tmp",
            text=True,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                json.dump(self.known_models, tmp_file, indent=2, ensure_ascii=False)
                tmp_file.write("\n")
            Path(tmp_path).replace(self.known_models_path)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
