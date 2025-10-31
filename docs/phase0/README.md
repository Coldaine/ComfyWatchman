Salvage Utilities (Phase 0)

This folder contains a single, self-contained Python module (`salvage_utilities.py`) with the most reusable building blocks from ComfyFixerSmart to support a lean reboot and orchestration rewrite.

What’s included
- Workflow scanning: Extract model references (including embeddings) from ComfyUI workflow JSONs.
- Local inventory: Build a quick inventory of existing models under a ComfyUI models/ directory.
- Minimal Civitai search: Lookup by model ID, by SHA256 hash, and by query with conservative exact-file matching.
- Download script generation: Produce a bash script that downloads to the proper ComfyUI models subfolders.
- Lightweight inspector: Quick file metadata and SHA256 hashing (safe by default).

Design goals
- Single file, no internal project imports, safe to copy-paste into other contexts.
- Minimal external deps (only `requests` if you use Civitai helpers).
- Clear function docstrings and typed signatures to enable later LangGraph tool wrapping.

Usage
- Drop the file anywhere or import it directly:
  - python -c "import salvage_utilities as su; print(su.__doc__.splitlines()[0])"
- See function docstrings for contracts and return shapes.

Notes
- Set CIVITAI_API_KEY in your environment for authenticated Civitai calls.
- Prefer explicit models_dir arguments rather than relying on environment.
- The script generator produces a bash-compatible script; run with bash even if your login shell is fish.
