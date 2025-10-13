# Set up paths for submodules before any other imports
try:
    from . import submodule_loader
    submodule_loader.setup_submodule_paths()
except ImportError:
    # This might happen during initial setup or if the file is moved.
    # We can add more robust error handling if needed.
    print("Warning: submodule_loader.py not found. Submodule imports may fail.")


"""
ComfyFixerSmart - Incremental ComfyUI Model Downloader

A comprehensive tool for analyzing ComfyUI workflows and downloading missing models
from Civitai and other sources.
"""

__version__ = "2.0.0"
__author__ = "ComfyFixerSmart Team"
__description__ = "Incremental ComfyUI model downloader with enhanced state management"
__url__ = "https://github.com/your-repo/comfyfixersmart"
__license__ = "MIT"

# Migration information
MIGRATION_TARGET_VERSION = "2.0.0"
LEGACY_VERSION_SUPPORT = "1.x"
COMPATIBILITY_LAYER_ACTIVE = True

def get_version_info():
    """Get detailed version information."""
    return {
        "version": __version__,
        "migration_target": MIGRATION_TARGET_VERSION,
        "legacy_support": LEGACY_VERSION_SUPPORT,
        "compatibility_layer": COMPATIBILITY_LAYER_ACTIVE,
        "description": __description__,
        "author": __author__,
    }