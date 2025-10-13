"""
Adapters Module for ComfyFixerSmart

Provides optional integration with ComfyUI-Copilot features through adapter pattern.
All Copilot features are optional with graceful degradation when dependencies are missing.
"""

import logging
from typing import Optional

from comfyfixersmart.logging import get_logger

# Feature detection for ComfyUI-Copilot
COPILOT_AVAILABLE = False

try:
    import comfyui_copilot  # type: ignore
    COPILOT_AVAILABLE = True
except ImportError:
    # ComfyUI-Copilot not available, log warning but continue
    logger = get_logger()
    logger.warning(
        "ComfyUI-Copilot not available. Copilot features will be disabled. "
        "Install ComfyUI-Copilot to enable advanced workflow generation and optimization features."
    )

# Feature detection for ModelScope (via ComfyUI-Copilot submodule)
MODELSCOPE_AVAILABLE = False

try:
    # Try to import from the copilot_backend submodule
    from .copilot_backend.backend.utils.modelscope_gateway import ModelScopeGateway
    MODELSCOPE_AVAILABLE = True
except ImportError:
    # ModelScope dependencies not available
    logger = get_logger()
    logger.info(
        "ModelScope integration not available. ModelScope search backend will be disabled. "
        "This is normal if ComfyUI-Copilot submodule is not properly initialized."
    )

# Export base adapter classes
from .base import BaseAdapter

__all__ = [
    "COPILOT_AVAILABLE",
    "MODELSCOPE_AVAILABLE",
    "BaseAdapter",
]