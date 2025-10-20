"""Model metadata inspector for ComfyWatchman.

This module provides deterministic utilities for inspecting model files
and Diffusers directories without loading large tensors. It is designed
to be safe by default and expose only lightweight metadata so that users
can triage assets locally.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Literal, Optional, Tuple

SUPPORTED_EXTENSIONS = {
    ".safetensors": "safetensors",
    ".ckpt": "ckpt",
    ".pt": "pt",
    ".pth": "pth",
    ".onnx": "onnx",
    ".bin": "bin",
}

PICKLE_FORMATS = {"ckpt", "pt", "pth", "bin"}


@dataclass
class InspectionContext:
    """Context shared across inspection calls."""

    do_hash: bool = False
    unsafe: bool = False
    include_components: bool = True


def inspect_file(
    path: str,
    *,
    do_hash: bool = False,
    unsafe: bool = False,
    include_components: bool = True,
) -> Dict[str, object]:
    """Inspect a single file or Diffusers directory.

    Parameters
    ----------
    path:
        Path to the file or directory to inspect.
    do_hash:
        When ``True`` compute a SHA256 hash of files. Hashing is skipped
        for directories.
    unsafe:
        Opt-in flag that allows reading pickle based checkpoints via
        ``torch.load``. Disabled by default to avoid code execution.
    include_components:
        Controls whether Diffusers directories include per-file component
        summaries.
    """

    target = Path(path)
    ctx = InspectionContext(do_hash=do_hash, unsafe=unsafe, include_components=include_components)

    if not target.exists():
        return _missing_path_report(target)

    if target.is_dir():
        if _looks_like_diffusers_dir(target):
            return _inspect_diffusers_dir(target, ctx)
        return _inspect_generic_directory(target)

    return _inspect_model_file(target, ctx)


def inspect_paths(
    paths: List[str],
    *,
    recursive: bool = False,
    fmt: Literal["text", "json"] = "text",
    summary: bool = True,
    do_hash: bool = False,
    unsafe: bool = False,
    include_components: bool = True,
) -> str | List[Dict[str, object]]:
    """Inspect a collection of paths and render the result.

    Parameters mirror :func:`inspect_file` with additional formatting
    controls for CLI use. Results are deterministic: traversal is sorted
    and processing happens on a single thread.
    """

    ctx = InspectionContext(do_hash=do_hash, unsafe=unsafe, include_components=include_components)
    collected: List[Dict[str, object]] = []

    for root in sorted(paths, key=lambda p: str(Path(p))):
        root_path = Path(root)
        if not root_path.exists():
            collected.append(_missing_path_report(root_path))
            continue

        if root_path.is_dir() and not _looks_like_diffusers_dir(root_path):
            collected.extend(
                _inspect_directory_entries(root_path, ctx, recursive=recursive)
            )
        else:
            collected.append(_inspect_entry(root_path, ctx))

    if fmt == "json":
        return collected

    return _render_text(collected, summary=summary)


def _inspect_entry(path: Path, ctx: InspectionContext) -> Dict[str, object]:
    if path.is_dir():
        if _looks_like_diffusers_dir(path):
            return _inspect_diffusers_dir(path, ctx)
        return _inspect_generic_directory(path)
    return _inspect_model_file(path, ctx)


def _inspect_directory_entries(
    directory: Path,
    ctx: InspectionContext,
    *,
    recursive: bool,
) -> List[Dict[str, object]]:
    entries: List[Dict[str, object]] = []

    if recursive:
        for root, dirnames, filenames in os.walk(directory):
            dirnames.sort()
            filenames.sort()

            root_path = Path(root)
            if root_path != directory and _looks_like_diffusers_dir(root_path):
                entries.append(_inspect_diffusers_dir(root_path, ctx))
                # Skip descending into Diffusers directories further.
                dirnames[:] = []
                continue

            for filename in filenames:
                entries.append(_inspect_model_file(root_path / filename, ctx))
    else:
        for entry in sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name)):
            if entry.is_file() or _looks_like_diffusers_dir(entry):
                entries.append(_inspect_entry(entry, ctx))

    return entries


def _inspect_model_file(path: Path, ctx: InspectionContext) -> Dict[str, object]:
    size_bytes = path.stat().st_size
    extension = path.suffix.lower()
    file_format = SUPPORTED_EXTENSIONS.get(extension, "other")
    warnings: List[str] = []
    metadata: Dict[str, object] = {}

    if file_format == "safetensors":
        metadata, meta_warnings = _extract_safetensors_metadata(path)
        warnings.extend(meta_warnings)
    elif file_format == "onnx":
        meta, meta_warnings = _extract_onnx_metadata(path)
        metadata.update(meta)
        warnings.extend(meta_warnings)
    elif file_format in PICKLE_FORMATS:
        meta, meta_warnings = _extract_pickle_metadata(path, ctx.unsafe)
        metadata.update(meta)
        warnings.extend(meta_warnings)

    sha_val = _hash_file(path) if ctx.do_hash else None

    type_hint, family = _guess_type_hint(path, file_format, metadata, size_bytes)
    source_hints = _guess_source_hints(path)

    return {
        "filename": path.name,
        "path": str(path.resolve()),
        "size_bytes": size_bytes,
        "format": file_format,
        "type_hint": type_hint,
        "metadata": metadata,
        "sha256": sha_val,
        "source_hints": source_hints or None,
        "warnings": warnings,
        "family": family,
    }


def _inspect_diffusers_dir(path: Path, ctx: InspectionContext) -> Dict[str, object]:
    warnings: List[str] = []
    metadata: Dict[str, object] = {}
    pipeline_class: Optional[str] = None
    model_index_path = path / "model_index.json"

    if model_index_path.exists():
        try:
            model_data = json.loads(model_index_path.read_text(encoding="utf-8"))
            pipeline_class = (
                model_data.get("_class_name")
                or model_data.get("model_type")
                or model_data.get("pipeline_class")
            )
            metadata["pipeline_class"] = pipeline_class
            if "_diffusers_version" in model_data:
                metadata["diffusers_version"] = str(model_data["_diffusers_version"])
        except Exception as exc:  # pragma: no cover - safety guard
            warnings.append(f"Failed to parse model_index.json: {exc}")
    else:
        warnings.append("Missing model_index.json")

    components = _list_diffusers_components(path)
    metadata["components"] = [comp[0] for comp in components]
    if ctx.include_components:
        metadata["files"] = [
            {"name": comp[0], "size_bytes": comp[1], "extension": comp[2]}
            for comp in components
        ]

    total_size = sum(comp[1] for comp in components)
    type_hint, family = _guess_type_hint(path, "diffusers", metadata, total_size)

    return {
        "filename": path.name,
        "path": str(path.resolve()),
        "size_bytes": total_size,
        "format": "diffusers",
        "type_hint": type_hint,
        "metadata": metadata,
        "sha256": None,
        "source_hints": _guess_source_hints(path) or None,
        "warnings": warnings,
        "family": family,
    }


def _inspect_generic_directory(path: Path) -> Dict[str, object]:
    warnings = [
        "Directory inspected without recursion; pass --recursive to traverse contents",
    ]
    return {
        "filename": path.name,
        "path": str(path.resolve()),
        "size_bytes": 0,
        "format": "directory",
        "type_hint": "unknown",
        "metadata": {},
        "sha256": None,
        "source_hints": _guess_source_hints(path) or None,
        "warnings": warnings,
        "family": None,
    }


def _missing_path_report(path: Path) -> Dict[str, object]:
    return {
        "filename": path.name,
        "path": str(path),
        "size_bytes": 0,
        "format": "other",
        "type_hint": "unknown",
        "metadata": {},
        "sha256": None,
        "source_hints": None,
        "warnings": ["Path not found"],
        "family": None,
    }


def _extract_safetensors_metadata(path: Path) -> Tuple[Dict[str, object], List[str]]:
    from importlib import import_module

    warnings: List[str] = []
    try:
        safetensors = import_module("safetensors")
        safe_open = getattr(safetensors, "safe_open")
    except Exception as exc:  # pragma: no cover - import failure guarded via tests
        warnings.append(f"safetensors import failed: {exc}")
        return {}, warnings

    try:
        with safe_open(path, framework="numpy") as handle:  # type: ignore[call-arg]
            header = handle.metadata() or {}
    except Exception as exc:
        warnings.append(f"Failed to read safetensors metadata: {exc}")
        return {}, warnings

    metadata = {
        key: str(header[key]) for key in sorted(header.keys())[:20]
    }
    return metadata, warnings


def _extract_onnx_metadata(path: Path) -> Tuple[Dict[str, object], List[str]]:
    import importlib

    warnings: List[str] = []
    try:
        onnx = importlib.import_module("onnx")
    except ImportError:
        warnings.append("onnx not installed; metadata unavailable")
        return {}, warnings

    try:
        model = onnx.load(path, load_external_data=False)
    except Exception as exc:
        warnings.append(f"Failed to read ONNX file: {exc}")
        return {}, warnings

    metadata: Dict[str, object] = {}
    metadata["ir_version"] = getattr(model, "ir_version", None)
    if hasattr(model, "opset_import") and model.opset_import:
        metadata["opset"] = [
            {"domain": imp.domain or "", "version": imp.version}
            for imp in model.opset_import
        ]
    if hasattr(model, "producer_name") and model.producer_name:
        metadata["producer"] = str(model.producer_name)
    if hasattr(model, "producer_version") and model.producer_version:
        metadata["producer_version"] = str(model.producer_version)

    return metadata, warnings


def _extract_pickle_metadata(path: Path, unsafe: bool) -> Tuple[Dict[str, object], List[str]]:
    import importlib

    metadata: Dict[str, object] = {}
    warnings: List[str] = []

    if not unsafe:
        metadata["unsafe"] = "disabled"
        warnings.append("Unsafe loading disabled; showing file metadata only")
        return metadata, warnings

    try:
        torch = importlib.import_module("torch")
    except ImportError:
        warnings.append("torch not installed; cannot perform unsafe load")
        return metadata, warnings

    try:
        try:
            loaded = torch.load(path, map_location="cpu", weights_only=True)
        except TypeError:
            loaded = torch.load(path, map_location="cpu")
    except Exception as exc:  # pragma: no cover - runtime safety guard
        warnings.append(f"torch.load failed: {exc}")
        return metadata, warnings

    metadata["unsafe_top_level"] = _summarize_top_level(loaded)
    return metadata, warnings


def _summarize_top_level(obj: object) -> Dict[str, object]:
    summary: Dict[str, object] = {"type": type(obj).__name__}
    if isinstance(obj, dict):
        keys = list(obj.keys())
        summary["key_count"] = len(keys)
        summary["sample_keys"] = [str(key) for key in keys[:5]]
    elif hasattr(obj, "state_dict"):
        try:
            state = obj.state_dict()
            if isinstance(state, dict):
                keys = list(state.keys())
                summary["state_keys"] = [str(key) for key in keys[:5]]
                summary["state_key_count"] = len(keys)
        except Exception:  # pragma: no cover - defensive guard
            pass
    return summary


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _guess_type_hint(
    path: Path,
    file_format: str,
    metadata: Dict[str, object],
    size_bytes: int,
) -> Tuple[str, Optional[str]]:
    lowered_parts = [part.lower() for part in path.parts]
    filename = path.name.lower()
    family: Optional[str] = None

    dir_type_map = {
        "checkpoints": "checkpoint",
        "models": "checkpoint",
        "loras": "lora",
        "lycoris": "lycoris",
        "locon": "locon",
        "embeddings": "embedding",
        "hypernetworks": "hypernetwork",
        "controlnet": "controlnet",
        "clip": "clip",
        "clip_vision": "clip_vision",
        "vae": "vae",
        "vae_approx": "vae_approx",
        "upscale_models": "upscale",
        "sam": "sam",
        "t2i_adapter": "t2i_adapter",
        "ipadapter": "ip_adapter",
        "motion_lora": "motion",
        "animatediff_models": "motion",
        "segmentation": "segmentation",
        "yolo": "yolo",
        "flux": "flux",
    }

    for part in lowered_parts:
        if part in dir_type_map:
            hint = dir_type_map[part]
            if hint == "flux":
                family = "flux"
                hint = "checkpoint"
            return hint, family

    text_blob = " ".join(str(value).lower() for value in metadata.values())
    meta_keywords = [
        ("flux", "flux"),
        ("lora", "lora"),
        ("lycoris", "lycoris"),
        ("locon", "locon"),
        ("controlnet", "controlnet"),
        ("vae", "vae"),
        ("ipadapter", "ip_adapter"),
        ("embedding", "embedding"),
        ("clip vision", "clip_vision"),
        ("t2i", "t2i_adapter"),
        ("sam", "sam"),
        ("hypernetwork", "hypernetwork"),
        ("upscale", "upscale"),
    ]

    for keyword, hint in meta_keywords:
        if keyword in text_blob:
            if hint == "flux":
                family = "flux"
                return "checkpoint", family
            if hint == "vae":
                return "vae", family
            return hint, family

    filename_map = [
        (r"^ti_", "embedding"),
        (r"embedding", "embedding"),
        (r"lycoris", "lycoris"),
        (r"locon", "locon"),
        (r"ip.?adapter", "ip_adapter"),
        (r"t2i[_-]?adapter", "t2i_adapter"),
        (r"hypernetwork", "hypernetwork"),
        (r"controlnet", "controlnet"),
        (r"clip_vision", "clip_vision"),
        (r"^sam_", "sam"),
        (r"realesrgan|esrgan", "upscale"),
        (r"gfpgan|codeformer", "face_restore"),
        (r"yolo", "yolo"),
        (r"flux", "checkpoint"),
        (r"t5", "t5"),
        (r"animatediff|motion", "motion"),
        (r"vae", "vae"),
    ]

    for pattern, hint in filename_map:
        if re.search(pattern, filename):
            if pattern == r"flux":
                family = "flux"
            if hint == "checkpoint" and family == "flux":
                return hint, family
            return hint, family

    if file_format in {"safetensors", "ckpt", "pt", "pth"}:
        if size_bytes >= 2 * 1024 * 1024 * 1024:
            return "checkpoint", family
        if size_bytes <= 200 * 1024 * 1024:
            return "lora", family
        if size_bytes <= 600 * 1024 * 1024 and "vae" in filename:
            return "vae", family

    if file_format == "onnx":
        return "clip" if "clip" in filename else "unknown", family

    return "unknown", family


def _guess_source_hints(path: Path) -> List[str]:
    hints: List[str] = []
    path_str = str(path).lower()
    if "civitai" in path_str:
        hints.append("civitai")
    if "huggingface" in path_str or "hf_" in path.name.lower():
        hints.append("huggingface")
    if "github" in path_str:
        hints.append("github")
    return hints


def _looks_like_diffusers_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    return (path / "model_index.json").exists()


def _list_diffusers_components(path: Path) -> List[Tuple[str, int, str]]:
    components: List[Tuple[str, int, str]] = []
    for root, _, files in os.walk(path):
        rel_root = Path(root)
        files.sort()
        for file_name in files:
            file_path = rel_root / file_name
            extension = file_path.suffix.lower()
            if extension not in SUPPORTED_EXTENSIONS and extension not in {".json"}:
                continue
            relative = file_path.relative_to(path)
            size = file_path.stat().st_size
            components.append((str(relative), size, extension.lstrip(".")))
    components.sort(key=lambda item: item[0])
    return components


def _render_text(entries: Iterable[Dict[str, object]], *, summary: bool) -> str:
    lines: List[str] = []
    for entry in entries:
        first_line = (
            f"{entry['filename']} | format={entry['format']} | type={entry['type_hint']} | "
            f"size={entry['size_bytes']}"
        )
        lines.append(first_line)

        if not summary:
            metadata = entry.get("metadata") or {}
            if metadata:
                items = list(metadata.items())
                formatted_items = []
                for key, value in items[:5]:
                    formatted_items.append(f"{key}={value}")
                lines.append("  metadata: " + "; ".join(formatted_items))

            if entry.get("sha256"):
                lines.append(f"  sha256: {entry['sha256']}")

        warnings = entry.get("warnings") or []
        if warnings:
            lines.append("  warnings: " + " | ".join(str(w) for w in warnings))

    return "\n".join(lines)


__all__ = [
    "inspect_file",
    "inspect_paths",
]
