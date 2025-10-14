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

# Check for ComfyUI-Copilot backend submodule
def is_copilot_available() -> bool:
    """Check if the forked ComfyUI-Copilot backend is available."""
    import os
    from pathlib import Path
    
    # Check if the submodule directory exists
    copilot_path = Path(__file__).parent.parent.parent / "copilot_backend"
    if not copilot_path.exists():
        return False
    
    # Check if key files exist in the submodule
    modelscope_gateway = copilot_path / "backend" / "utils" / "modelscope_gateway.py"
    if not modelscope_gateway.exists():
        return False
    
    # Check if we can import from the submodule
    try:
        # Try importing a key module to verify it's working
        import sys
        # Add the submodule to sys.path temporarily
        original_path = sys.path.copy()
        sys.path.insert(0, str(copilot_path.parent))
        try:
            from copilot_backend.backend.utils.modelscope_gateway import ModelScopeGateway
            return True
        finally:
            # Restore original sys.path
            sys.path = original_path
    except (ImportError, ModuleNotFoundError, AttributeError):
        return False

COPILOT_AVAILABLE = is_copilot_available()

