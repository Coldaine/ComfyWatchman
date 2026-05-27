"""
Salvage Utilities for ComfyFixerSmart (Phase 0)

A single, self-contained module with the most reusable building blocks to:
- Scan ComfyUI workflows and extract model references (including embeddings)
- Build a quick local inventory of models under a ComfyUI models/ directory
- Query Civitai (by ID, by hash, and by query) with conservative matching
- Generate a bash download script that writes into proper models subfolders
- Perform lightweight file inspection and hashing (safe by default)

Design:
- No internal project imports; safe to copy anywhere.
- Optional dependency on requests for Civitai helpers.
- Typed function signatures and clear return shapes for later tool wrapping.

Top utilities exported:
- extract_models_from_workflow(path: str) -> list[dict]
- build_local_inventory(models_dir: str | Path, extensions: list[str] | None = None) -> set[str]
- civitai_get_model_by_id(model_id: int, api_key: str | None = None) -> dict
- civitai_get_version_by_hash(sha256: str, api_key: str | None = None) -> dict | None
- civitai_search_by_filename(filename: str, api_key: str | None = None, min_confidence: int = 70) -> dict | None
- generate_download_script(resolutions: list[dict], models_dir: str | Path, out_path: str | Path) -> str
- quick_inspect(path: str | Path, do_hash: bool = False) -> dict

Return shapes are documented in each function.
"""
from __future__ import annotations

import json
import os
import re
import stat
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union

try:
    import requests  # Optional, only needed for Civitai helpers
except Exception:  # pragma: no cover - optional
    requests = None  # type: ignore

Json = Dict[str, Any]
PathLike = Union[str, Path]

# -----------------------------
# Filename and path utilities
# -----------------------------

MODEL_EXTENSIONS = {".safetensors", ".ckpt", ".pt", ".bin", ".pth", ".onnx"}


def validate_and_sanitize_filename(filename: Any) -> tuple[bool, str, Optional[str]]:
    """Validate and sanitize a potentially unsafe model filename.

    Returns (is_valid, sanitized, error_reason). Never raises.
    """
    if not isinstance(filename, str) or not filename:
        return False, "", "Empty or non-string filename"

    if len(filename) > 500:
        return False, "", f"Filename too long ({len(filename)} > 500)"

    # URL-like patterns
    if re.search(r"https?://|ftp://|file://", filename, re.IGNORECASE):
        return False, "", "URL pattern detected"

    # Newlines and control chars
    if any(c in filename for c in ["\n", "\r", "\x00"]):
        return False, "", "Control/newline characters detected"

    # Path traversal and double dots
    if ".." in filename or re.search(r"\.{2,}", filename):
        return False, "", "Suspicious dot traversal"

    # Replace forbidden filesystem characters
    sanitized = filename
    for ch in '<>:"/\\|?*':
        sanitized = sanitized.replace(ch, "_")
    sanitized = sanitized.strip(" .") or "unnamed_file"

    # Basic extension allow-list
    if Path(sanitized).suffix.lower() not in MODEL_EXTENSIONS:
        return False, sanitized, "Unsupported extension"

    return True, sanitized, None


def sanitize_filename(filename: Any) -> str:
    ok, safe, _ = validate_and_sanitize_filename(filename)
    return safe if ok else (safe or "unnamed_file")


# -----------------------------
# Workflow scanning
# -----------------------------

EMBEDDING_TOKEN_PATTERN = re.compile(r"embedding:([A-Za-z0-9_\-\.]+)", re.IGNORECASE)

DEFAULT_NODE_TO_TYPE = {
    "CheckpointLoaderSimple": "checkpoints",
    "CheckpointLoader": "checkpoints",
    "LoraLoader": "loras",
    "LoraLoaderModelOnly": "loras",
    "VAELoader": "vae",
    "CLIPLoader": "clip",
    "DualCLIPLoader": "clip",
    "ControlNetLoader": "controlnet",
    "ControlNetLoaderAdvanced": "controlnet",
    "UpscaleModelLoader": "upscale_models",
    "CLIPVisionLoader": "clip_vision",
    "UNETLoader": "unet",
    "SAMLoader": "sams",
    "TextualInversionLoader": "embeddings",
    "TextualInversionApply": "embeddings",
    "EmbeddingLoader": "embeddings",
    "EmbeddingSelector": "embeddings",
    "TextEmbeddingLoader": "embeddings",
}


def determine_model_type(node_type: str, mapping: Optional[Dict[str, str]] = None) -> str:
    mapping = mapping or DEFAULT_NODE_TO_TYPE
    return mapping.get(node_type, "checkpoints")


def _is_model_filename(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return Path(value).suffix.lower() in MODEL_EXTENSIONS


def _sanitize_embedding_name(name: str) -> str:
    return name.strip().replace(" ", "_")


def _extract_embedding_tokens(value: Any) -> List[str]:
    tokens: List[str] = []
    if isinstance(value, str):
        tokens.extend(EMBEDDING_TOKEN_PATTERN.findall(value))
    elif isinstance(value, list):
        for item in value:
            tokens.extend(_extract_embedding_tokens(item))
    elif isinstance(value, dict):
        for item in value.values():
            tokens.extend(_extract_embedding_tokens(item))
    return tokens


def extract_models_from_workflow(workflow_path: PathLike) -> List[Dict[str, str]]:
    """Parse a ComfyUI workflow JSON and return model references.

    Returns a list of dicts with keys: filename, type, node_type, workflow_path.
    Embedding references like "embedding:xyz" are normalized to xyz.pt under type=embeddings.
    """
    path = Path(workflow_path)
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)

    models: List[Dict[str, str]] = []
    nodes = data.get("nodes", []) if isinstance(data, dict) else []
    seen_embeddings: Set[str] = set()

    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_type = node.get("type", "")

        # widgets_values scanning
        for val in node.get("widgets_values", []):
            if isinstance(val, str) and _is_model_filename(val):
                parts = re.split(r"[\\/]+", val)
                filename = parts[-1] if parts else val
                models.append(
                    {
                        "filename": filename,
                        "type": determine_model_type(node_type),
                        "node_type": node_type,
                        "workflow_path": str(path),
                    }
                )
            for emb in _extract_embedding_tokens(val):
                key = emb.lower()
                if key in seen_embeddings:
                    continue
                seen_embeddings.add(key)
                models.append(
                    {
                        "filename": f"{_sanitize_embedding_name(emb)}.pt",
                        "type": "embeddings",
                        "node_type": node_type,
                        "workflow_path": str(path),
                    }
                )

        # inputs scanning (embedding tokens only)
        inputs = node.get("inputs", {})
        if isinstance(inputs, dict):
            for v in inputs.values():
                for emb in _extract_embedding_tokens(v):
                    key = emb.lower()
                    if key in seen_embeddings:
                        continue
                    seen_embeddings.add(key)
                    models.append(
                        {
                            "filename": f"{_sanitize_embedding_name(emb)}.pt",
                            "type": "embeddings",
                            "node_type": node_type,
                            "workflow_path": str(path),
                        }
                    )

    return models


# -----------------------------
# Local inventory
# -----------------------------


def build_local_inventory(models_dir: PathLike, extensions: Optional[List[str]] = None) -> Set[str]:
    """Return a set of filenames found under models_dir matching the allowed extensions.

    This is case-sensitive on Linux and excludes directories. Returns only basenames.
    """
    exts = set(extensions) if extensions else {".safetensors", ".ckpt", ".pt", ".bin", ".pth"}
    base = Path(models_dir)
    if not base.exists():
        return set()
    found: Set[str] = set()
    for ext in exts:
        for p in base.rglob(f"*{ext}"):
            if p.is_file():
                found.add(p.name)
    return found


# -----------------------------
# Minimal Civitai helpers (optional requests)
# -----------------------------

CIVITAI_API_BASE = "https://civitai.com/api/v1"


def _require_requests():  # pragma: no cover - small guard
    if requests is None:
        raise RuntimeError("The 'requests' package is required for Civitai helpers")


def _auth_headers(api_key: Optional[str]) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _validate_civitai_images_response(data: Json, requested_id: Optional[int]) -> tuple[bool, str | None]:
    # /images?ids=... => { items: [ { id, ... } ] }
    items = data.get("items", []) if isinstance(data, dict) else []
    if not items:
        return False, "Image not found (empty items)"
    if requested_id is not None and items[0].get("id") != requested_id:
        return False, f"API returned wrong image (requested {requested_id}, got {items[0].get('id')})"
    return True, None


def civitai_get_model_by_id(model_id: int, api_key: Optional[str] = None, timeout: int = 30) -> Json:
    """Fetch a Civitai model by ID with basic validation.

    Returns JSON model object. Raises ValueError on HTTP/validation errors.
    """
    _require_requests()
    url = f"{CIVITAI_API_BASE}/models/{model_id}"
    resp = requests.get(url, headers=_auth_headers(api_key), timeout=timeout)
    if resp.status_code != 200:
        raise ValueError(f"Civitai HTTP {resp.status_code} for model {model_id}")
    data = resp.json()
    if data.get("id") != model_id:
        raise ValueError(f"API returned wrong model (requested {model_id}, got {data.get('id')})")
    return data


def civitai_get_version_by_hash(sha256: str, api_key: Optional[str] = None, timeout: int = 30) -> Optional[Json]:
    """Lookup a model version by its file SHA256 via /model-versions/by-hash/{hash}.

    Returns the version JSON or None if not found.
    """
    _require_requests()
    url = f"{CIVITAI_API_BASE}/model-versions/by-hash/{sha256}"
    resp = requests.get(url, headers=_auth_headers(api_key), timeout=timeout)
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise ValueError(f"Civitai HTTP {resp.status_code} for hash {sha256}")
    return resp.json()


def civitai_search_by_filename(
    filename: str,
    api_key: Optional[str] = None,
    min_confidence: int = 70,
    timeout: int = 30,
) -> Optional[Json]:
    """Best-effort search for a filename on Civitai via /models?query=.

    Strategy:
    - Query by filename stem; scan versions/files for an exact filename match (case-sensitive).
    - If exact file not found, return the first model whose version contains a file whose name
      shares the same stem and a known extension, with a lower confidence.

    Returns a dict:
      { status: "FOUND"|"NOT_FOUND", filename, civitai_id?, version_id?, download_url?, confidence: int }
    or None on fatal errors (e.g., HTTP).
    """
    _require_requests()

    ok, safe_name, err = validate_and_sanitize_filename(filename)
    if not ok:
        return {"status": "NOT_FOUND", "filename": filename, "reason": err}

    stem = Path(safe_name).stem
    url = f"{CIVITAI_API_BASE}/models"
    resp = requests.get(url, params={"query": stem}, headers=_auth_headers(api_key), timeout=timeout)
    if resp.status_code != 200:
        return None

    payload = resp.json()
    items: List[Json] = payload if isinstance(payload, list) else payload.get("items", [])
    if not isinstance(items, list):
        items = []

    # Exact filename match pass
    for model in items:
        mid = model.get("id")
        for ver in model.get("modelVersions", []) or []:
            vid = ver.get("id")
            for f in ver.get("files", []) or []:
                if f.get("name") == safe_name:
                    # Prefer the primary download URL when present
                    dl = f.get("downloadUrl") or f.get("downloadUrlLegacy") or f.get("downloadUrlV2")
                    return {
                        "status": "FOUND",
                        "filename": filename,
                        "civitai_id": mid,
                        "version_id": vid,
                        "download_url": dl,
                        "confidence": 100,
                        "type": _infer_type_from_filename(safe_name),
                    }

    # Fuzzy stem match as fallback
    for model in items:
        mid = model.get("id")
        for ver in model.get("modelVersions", []) or []:
            vid = ver.get("id")
            for f in ver.get("files", []) or []:
                cand = f.get("name") or ""
                if Path(cand).stem == stem and Path(cand).suffix.lower() in MODEL_EXTENSIONS:
                    dl = f.get("downloadUrl") or f.get("downloadUrlLegacy") or f.get("downloadUrlV2")
                    return {
                        "status": "FOUND",
                        "filename": filename,
                        "civitai_id": mid,
                        "version_id": vid,
                        "download_url": dl,
                        "confidence": max(min_confidence, 70),
                        "type": _infer_type_from_filename(cand),
                    }

    return {"status": "NOT_FOUND", "filename": filename}


def _infer_type_from_filename(name: str) -> str:
    low = name.lower()
    if low.endswith(".safetensors") or low.endswith(".ckpt") or low.endswith(".pt") or low.endswith(".pth"):
        if "vae" in low:
            return "vae"
        if "lora" in low or "lycoris" in low or "locon" in low:
            return "loras"
        return "checkpoints"
    if low.endswith(".onnx"):
        if "clip" in low:
            return "clip"
        return "checkpoints"
    return "checkpoints"


# -----------------------------
# Download script generation
# -----------------------------

SCRIPT_HEADER = """#!/bin/bash
# Auto-generated download script (ComfyFixerSmart salvage)
set -euo pipefail

: "${COMFY_MODELS_DIR:?Set COMFY_MODELS_DIR to your ComfyUI/models path}"

verify() {
  local f="$1"
  if [ ! -f "$f" ]; then
    echo "  ✗ missing: $f"; return 1
  fi
  local sz
  sz=$(stat -c%s "$f" 2>/dev/null || stat -f%z "$f" 2>/dev/null)
  if [ "${sz:-0}" -lt 1000000 ]; then
    echo "  ⚠ too small ($sz)"; rm -f "$f"; return 1
  fi
  echo "  ✓ $f ($sz bytes)"; return 0
}
"""


def generate_download_script(resolutions: List[Json], models_dir: PathLike, out_path: PathLike) -> str:
    """Generate a bash script to download resolved models.

    Input `resolutions` items should be dicts like those returned from civitai_search_by_filename:
      { status, filename, download_url?, type?, civitai_id?, version_id?, confidence? }

    The script uses COMFY_MODELS_DIR environment variable at runtime but we also bake the provided
    models_dir into mkdir paths for convenience.

    Returns the path (str) to the generated script.
    """
    lines: List[str] = [SCRIPT_HEADER]

    base = Path(models_dir)
    for r in resolutions:
        if r.get("status") != "FOUND" or not r.get("download_url"):
            continue
        filename = sanitize_filename(r.get("filename", "model.safetensors"))
        mtype = r.get("type") or _infer_type_from_filename(filename)
        target_dir = base / mtype
        target = f"$COMFY_MODELS_DIR/{mtype}/{filename}"

        lines += [
            "echo '----------------------------------------'",
            f"echo 'Downloading: {filename} -> {mtype}'",
            f"mkdir -p '{target_dir}'",
            "wget -c --content-disposition \\",
            "  --timeout=60 --tries=3 \\",
            f"  -O '{target}' \\",
            f"  '{r['download_url']}'",
            f"verify '{target}' || true",
        ]

    out = Path(out_path)
    out.write_text("\n".join(lines), encoding="utf-8")
    out.chmod(out.stat().st_mode | stat.S_IEXEC)
    return str(out)


# -----------------------------
# Lightweight inspector
# -----------------------------

SUPPORTED_EXT = {".safetensors", ".ckpt", ".pt", ".pth", ".onnx", ".bin"}


def quick_hash(path: PathLike, algo: str = "sha256", chunk_mb: int = 1) -> Optional[str]:
    p = Path(path)
    if not p.exists() or not p.is_file():
        return None
    h = getattr(hashlib, algo)()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_mb * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def quick_inspect(path: PathLike, do_hash: bool = False) -> Dict[str, Any]:
    """Return basic file metadata without loading tensors.

    Returns dict: { filename, path, size_bytes, format, sha256?, warnings: list[str] }
    """
    p = Path(path)
    if not p.exists():
        return {
            "filename": p.name,
            "path": str(p),
            "size_bytes": 0,
            "format": "other",
            "sha256": None,
            "warnings": ["Path not found"],
        }

    size = p.stat().st_size
    ext = p.suffix.lower()
    fmt = ext.lstrip(".") if ext in SUPPORTED_EXT else "other"
    sha = quick_hash(p) if do_hash else None

    warnings: List[str] = []
    if fmt == "other":
        warnings.append("Unrecognized extension; limited metadata only")

    return {
        "filename": p.name,
        "path": str(p.resolve()),
        "size_bytes": size,
        "format": fmt,
        "sha256": sha,
        "warnings": warnings,
    }


__all__ = [
    # workflow
    "extract_models_from_workflow",
    "determine_model_type",
    # inventory
    "build_local_inventory",
    # civitai
    "civitai_get_model_by_id",
    "civitai_get_version_by_hash",
    "civitai_search_by_filename",
    # downloads
    "generate_download_script",
    # inspection
    "quick_inspect",
    "quick_hash",
    # utils
    "sanitize_filename",
    "validate_and_sanitize_filename",
]
