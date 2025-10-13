"""
Adapters for integrating external tools and libraries into ComfyFixerSmart.

This module provides a layer for feature detection, allowing the application
to gracefully degrade if optional dependencies are not installed.
"""

import importlib.util

def is_package_available(package_name: str) -> bool:
    """Check if a package is installed without importing it."""
    return importlib.util.find_spec(package_name) is not None

# --- Feature Flags ---

# Check for ModelScope (for optional search backend)
MODELSCOPE_AVAILABLE = is_package_available("modelscope")

# Conditionally import ModelScopeSearch when available
if MODELSCOPE_AVAILABLE:
    try:
        from .modelscope_search import ModelScopeSearch
    except ImportError:
        ModelScopeSearch = None
        MODELSCOPE_AVAILABLE = False
else:
    ModelScopeSearch = None

# Check for SQLAlchemy (for optional SQL state backend)
SQLALCHEMY_AVAILABLE = is_package_available("sqlalchemy")

# Placeholder for ComfyUI-Copilot backend check.
# This will be more robust once it's a submodule.
def is_copilot_available() -> bool:
    """Check if the forked ComfyUI-Copilot backend is available."""
    # For now, we can check if a key file exists. This will be improved
    # when using git submodules.
    # A simple check could be for the main agent file.
    copilot_agent_path = "src/copilot_backend/service/debug_agent.py"
    # This path will need to be adjusted based on the submodule location.
    # For now, let's assume a placeholder logic.
    return is_package_available("agents") # A key dependency of the copilot backend

COPILOT_AVAILABLE = is_copilot_available()

