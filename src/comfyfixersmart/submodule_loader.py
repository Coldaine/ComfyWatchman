"""
System path management for ComfyFixerSmart.

This module ensures that bundled submodules (like the forked Copilot backend)
are correctly added to the Python path, making them importable by our application.
"""

import sys
from pathlib import Path

def setup_submodule_paths():
    """
    Adds the necessary submodule directories to the Python system path.
    """
    # Get the root directory of the `comfyfixersmart` package
    package_root = Path(__file__).parent.parent.resolve()

    # Path to the forked copilot backend submodule
    copilot_backend_path = package_root / "copilot_backend"

    if copilot_backend_path.exists() and str(copilot_backend_path) not in sys.path:
        # We need to add the parent of `backend` so that `from backend...` works
        # as it does in the original Copilot structure.
        sys.path.insert(0, str(copilot_backend_path))

    # We also need to add the `src` directory of our own project to resolve
    # sibling modules correctly.
    src_path = package_root.parent
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
