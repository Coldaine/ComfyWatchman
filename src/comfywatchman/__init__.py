"""ComfyWatchman package.

Temporary shim package pointing to the existing implementation while
the codebase transitions from ComfyFixerSmart to ComfyWatchman.
"""

try:
    # Re-export version if present in legacy package
    from comfyfixersmart import __version__  # type: ignore
except Exception:
    __version__ = "0.0.0"
