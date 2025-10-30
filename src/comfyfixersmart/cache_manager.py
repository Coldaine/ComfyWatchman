"""Cache refresh utilities for scheduler cycles."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

from .config import config
from .inventory import ModelInventory, ModelInfo
from .logging import get_logger
from .state_manager import JsonStateManager, StateManager


class CacheManager:
    """Refresh lightweight caches for models and custom nodes."""

    def __init__(self, state_manager: Optional[StateManager] = None, logger=None) -> None:
        self.logger = logger or get_logger("CacheManager")
        self.state_manager = state_manager or JsonStateManager(config.state_dir, logger=self.logger)
        self.inventory = ModelInventory(state_manager=self.state_manager, logger=self.logger)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh_all(self) -> Dict[str, Optional[Path]]:
        """Refresh every cache and return the resulting artifact paths."""

        return {
            'model_cache': self.refresh_model_cache(),
            'custom_nodes_cache': self.refresh_custom_nodes_cache(),
        }

    def refresh_model_cache(self) -> Optional[Path]:
        """Persist the current local model inventory grouped by type."""

        if not config.models_dir or not config.models_dir.exists():
            self.logger.warning("Models directory is not configured; skipping model cache refresh")
            return None

        inventory = self.inventory.build_inventory(include_state_tracking=True)
        summary = self._summarize_models(inventory)

        existing = self.state_manager.load_json_artifact('model_cache.json', default=None)
        if existing and self._cache_payload_equal(existing, summary):
            self.logger.debug("Model cache unchanged; skipping write")
            return self.state_manager._artifact_path('model_cache.json')

        path = self.state_manager.save_json_artifact('model_cache.json', summary)
        self.logger.info(f"Model cache refreshed with {summary['total_models']} entries")
        return path

    def refresh_custom_nodes_cache(self) -> Optional[Path]:
        """Persist metadata about installed custom nodes."""

        if not config.comfyui_root:
            self.logger.warning("COMFYUI_ROOT is not configured; skipping custom node cache refresh")
            return None

        nodes_dir = config.comfyui_root / 'custom_nodes'
        if not nodes_dir.exists():
            self.logger.warning(f"Custom nodes directory missing: {nodes_dir}")
            return None

        packages = []
        for entry in sorted(nodes_dir.iterdir(), key=lambda item: item.name.lower()):
            if not entry.is_dir() or entry.name.startswith('.'):
                continue
            try:
                stats = entry.stat()
            except OSError:
                continue

            packages.append({
                'name': entry.name,
                'path': str(entry),
                'last_modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                'size_bytes': stats.st_size,
            })

        summary = {
            'generated_at': datetime.now().isoformat(),
            'total_packages': len(packages),
            'packages': packages,
        }

        existing = self.state_manager.load_json_artifact('custom_nodes_cache.json', default=None)
        if existing and self._cache_payload_equal(existing, summary):
            self.logger.debug("Custom node cache unchanged; skipping write")
            return self.state_manager._artifact_path('custom_nodes_cache.json')

        path = self.state_manager.save_json_artifact('custom_nodes_cache.json', summary)
        self.logger.info(f"Custom node cache refreshed with {summary['total_packages']} packages")
        return path

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _summarize_models(self, inventory: Dict[str, ModelInfo]) -> Dict[str, Any]:
        grouped: Dict[str, Dict[str, Any]] = {}

        for model in inventory.values():
            model_type = self._derive_model_type(Path(model.path))
            bucket = grouped.setdefault(model_type, {'count': 0, 'models': []})
            bucket['models'].append({
                'filename': model.filename,
                'path': model.path,
                'size_bytes': model.size,
            })
            bucket['count'] += 1

        for bucket in grouped.values():
            bucket['models'].sort(key=lambda entry: entry['filename'].lower())

        return {
            'generated_at': datetime.now().isoformat(),
            'total_models': len(inventory),
            'types': grouped,
        }

    def _derive_model_type(self, path: Path) -> str:
        try:
            relative = path.relative_to(config.models_dir)
            return relative.parts[0] if relative.parts else 'unknown'
        except Exception:
            return 'external'

    @staticmethod
    def _cache_payload_equal(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
        comparable_left = dict(left)
        comparable_right = dict(right)
        comparable_left.pop('generated_at', None)
        comparable_right.pop('generated_at', None)
        return comparable_left == comparable_right
