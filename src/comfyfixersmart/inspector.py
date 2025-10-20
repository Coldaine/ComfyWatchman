"""
Model Metadata Inspector (DP-016)

Safe, metadata-only inspection for ComfyUI model files.

Design goals:
- Never execute untrusted code. Do not unpickle or torch.load .pth/.ckpt
- Prefer safetensors header metadata via safetensors.safe_open
- Optionally compute SHA256 for integrity bookkeeping (opt-in flag)
- Provide lightweight heuristics to infer model type from filename/path

Note: This module is intentionally dependency-light. It only uses
"safetensors" if available; ONNX metadata is optional and best-effort.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


try:  # Optional dependency
    from safetensors import safe_open  # type: ignore
    _HAVE_SAFETENSORS = True
except Exception:  # pragma: no cover - environment may not have it
    safe_open = None  # type: ignore
    _HAVE_SAFETENSORS = False


def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _infer_type_from_name(name: str) -> str:
    n = name.lower()
    # coarse heuristics aligned with project taxonomy
    if any(k in n for k in ["lora", "locon", "lycoris"]):
        return "lora"
    if "controlnet" in n:
        return "controlnet"
    if "vae" in n and "approx" in n:
        return "vae_approx"
    if "vae" in n:
        return "vae"
    if any(k in n for k in ["remacri", "4x", "upscale", "esrgan", "real-esrgan", "superscale"]):
        return "upscale"
    if any(k in n for k in ["clip-vision", "clip_vision"]):
        return "clip_vision"
    if "clip" in n:
        return "clip"
    if any(k in n for k in ["sam", "segment-anything"]):
        return "sam"
    if any(k in n for k in ["unet", "diffusion_model", "sdxl", "sd14", "sd15", "sd2"]):
        return "checkpoint"
    if any(k in n for k in ["t5", "text_encoder", "text-encoder"]):
        return "t5"
    if "ip_adapter" in n or "ip-adapter" in n:
        return "ip_adapter"
    if any(k in n for k in ["yolo", "ultralytics"]):
        return "yolo"
    return "unknown"


@dataclass
class InspectionResult:
    path: str
    size: int
    ext: str
    type_hint: str
    safe_to_load: bool
    format: str
    tensors: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    sha256: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def inspect_file(path: Path, compute_hash: bool = False) -> InspectionResult:
    """Inspect a single model file safely.

    - .safetensors: reads only headers/metadata with safetensors.safe_open
    - .ckpt/.pt/.pth/.bin: do NOT load; mark unsafe_to_load
    - .onnx: best-effort metadata (size + suffix); no external deps
    """
    p = Path(path)
    try:
        size = p.stat().st_size
    except FileNotFoundError:
        return InspectionResult(
            path=str(p), size=0, ext=p.suffix.lower(), type_hint="unknown",
            safe_to_load=False, format="missing", error="File not found"
        )

    ext = p.suffix.lower()
    lower_name = p.name.lower()
    type_hint = _infer_type_from_name(lower_name)

    # Default
    result = InspectionResult(
        path=str(p), size=size, ext=ext, type_hint=type_hint,
        safe_to_load=False, format="unknown", tensors=None, metadata=None
    )

    if ext == ".safetensors":
        if not _HAVE_SAFETENSORS:
            result.error = "safetensors not installed"
            result.format = "safetensors"
            # Still safe: we didn't try to load tensors
            result.safe_to_load = True
            return result
        # Metadata only; do not materialize tensors
        try:
            with safe_open(str(p), framework="pt", device="cpu") as f:  # type: ignore
                keys = list(f.keys())
                # try reading metadata from header if present
                try:
                    meta = f.metadata() or {}
                except Exception:
                    meta = {}
            result.tensors = keys
            result.metadata = meta
            result.format = "safetensors"
            result.safe_to_load = True
        except Exception as e:  # corrupt or unreadable
            result.error = f"safetensors read error: {e}"
            result.format = "safetensors"
            result.safe_to_load = False

    elif ext in {".ckpt", ".pt", ".pth", ".bin"}:
        # Unsafe container for arbitrary pickles or opaque binaries.
        result.format = "pytorch"
        result.safe_to_load = False
        # Do not attempt to import torch or load anything.

    elif ext == ".onnx":
        # Best-effort: we won't import onnx as a dependency to keep it light.
        result.format = "onnx"
        # ONNX is generally safe to parse, but without onnx dep, we don't parse graph.
        result.safe_to_load = True  # Reading bytes/size is safe; execution is not attempted.

    else:
        # Unknown formats; be conservative
        result.format = ext.lstrip(".") or "unknown"
        result.safe_to_load = False

    if compute_hash and result.error is None and size > 0:
        try:
            result.sha256 = _sha256(p)
        except Exception as e:
            result.error = f"hash error: {e}"

    return result


def inspect_paths(paths: List[Path], compute_hash: bool = False) -> List[InspectionResult]:
    results: List[InspectionResult] = []
    for path in paths:
        p = Path(path)
        if p.is_dir():
            for candidate in p.rglob("*"):
                if candidate.is_file():
                    results.append(inspect_file(candidate, compute_hash=compute_hash))
        else:
            results.append(inspect_file(p, compute_hash=compute_hash))
    return results


def results_to_json(results: List[InspectionResult]) -> str:
    return json.dumps([r.to_dict() for r in results], indent=2)
