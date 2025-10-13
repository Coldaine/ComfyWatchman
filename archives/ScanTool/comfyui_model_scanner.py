#!/usr/bin/env python3
"""
ComfyUI Model Scanner

A utility for scanning and indexing ComfyUI model files with metadata extraction.
"""
import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Union
import argparse

# Optional: pip install safetensors pyyaml
from safetensors import safe_open
import yaml


def setup_logging(verbosity: int = 0) -> logging.Logger:
    """
    Set up logging based on verbosity level
    :param verbosity: 0=WARNING, 1=INFO, 2+=DEBUG
    """
    log_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    level = log_levels[min(verbosity, len(log_levels) - 1)]
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    return logging.getLogger(__name__)

def discover_roots(comfy_root: Optional[Union[str, Path]] = None, logger: Optional[logging.Logger] = None) -> List[Path]:
    """
    Discover model root directories based on ComfyUI structure
    :param comfy_root: Path to ComfyUI root directory
    :param logger: Logger instance for logging messages
    :return: List of model root directories
    """
    if logger is None:
        logger = logging.getLogger(__name__)
        
    roots = []

    # If no root specified, use script's parent directory
    if comfy_root is None:
        comfy_root = Path(__file__).resolve().parent
        logger.debug(f"No ComfyUI root specified, using script's parent directory: {comfy_root}")
    else:
        comfy_root = Path(comfy_root).resolve()
        logger.info(f"Using specified ComfyUI root directory: {comfy_root}")

    models_root = comfy_root / "models"

    # Add models directory if it exists
    if models_root.exists():
        roots.append(models_root)
        logger.debug(f"Found models directory: {models_root}")

    # If the specified directory itself contains models, scan it directly
    if comfy_root.exists() and comfy_root != models_root:
        roots.append(comfy_root)
        logger.debug(f"Adding ComfyUI root as model directory: {comfy_root}")

    # Add extra model roots if present (both actual and example file)
    extra_paths = []
    for candidate in ["extra_model_paths.yaml", "extra_model_paths.yaml.example"]:
        cfg = comfy_root / candidate
        if cfg.exists():
            extra_paths.append(cfg)
            logger.debug(f"Found extra model paths config: {cfg}")

    # Proper YAML parsing
    for y in extra_paths:
        try:
            config = yaml.safe_load(y.read_text(encoding="utf-8", errors="ignore"))
            if config and isinstance(config, dict):
                for key, value in config.items():
                    if isinstance(value, dict) and "models" in value:
                        models_path = Path(value["models"])
                        if models_path.exists():
                            roots.append(models_path)
                            logger.info(f"Added extra models path from {y}: {models_path}")
                        else:
                            logger.warning(f"Configured models path does not exist: {models_path}")
        except Exception as e:
            logger.error(f"Error parsing {y}: {e}", exc_info=True)

    # Deduplicate while preserving order
    uniq = []
    seen = set()
    for r in roots:
        rp = r.resolve()
        if rp not in seen:
            uniq.append(rp)
            seen.add(rp)
    logger.info(f"Discovered {len(uniq)} unique model root directories")
    return uniq

def sha256_fast(path: Union[str, Path], chunk: int = 1024 * 1024, logger: Optional[logging.Logger] = None) -> str:
    """
    Calculate SHA256 hash of a file
    :param path: Path to the file
    :param chunk: Chunk size for reading the file
    :param logger: Logger instance for logging messages
    :return: SHA256 hash as hex string
    """
    if logger is None:
        logger = logging.getLogger(__name__)
        
    logger.debug(f"Computing SHA256 hash for: {path}")
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                b = f.read(chunk)
                if not b:
                    break
                h.update(b)
        logger.debug(f"SHA256 computed for: {path}")
        return h.hexdigest()
    except Exception as e:
        logger.error(f"Error computing SHA256 for {path}: {e}", exc_info=True)
        raise

def read_safetensors_metadata(path: Union[str, Path], logger: Optional[logging.Logger] = None) -> Dict:
    """
    Read metadata from a safetensors file
    :param path: Path to the safetensors file
    :param logger: Logger instance for logging messages
    :return: Dictionary containing metadata
    """
    if logger is None:
        logger = logging.getLogger(__name__)
        
    logger.debug(f"Reading safetensors metadata from: {path}")
    meta = {}
    try:
        with safe_open(str(path), framework="pt", device="cpu") as f:
            meta = dict(f.metadata() or {})
        logger.debug(f"Successfully read metadata from: {path}")
    except Exception as e:
        logger.error(f"Error reading safetensors metadata from {path}: {e}", exc_info=True)
        meta = {"error": str(e), "error_type": type(e).__name__, "error_path": str(path)}
    return meta

def detect_model_type(metadata: Dict, path: Union[str, Path], logger: Optional[logging.Logger] = None) -> str:
    """
    Detect model type based on path, metadata, and tensor keys
    :param metadata: Metadata dictionary from the model file
    :param path: Path to the model file
    :param logger: Logger instance for logging messages
    :return: String indicating the model type
    """
    if logger is None:
        logger = logging.getLogger(__name__)
        
    logger.debug(f"Detecting model type for: {path}")
    
    # Get file size for heuristics
    try:
        file_size = Path(path).stat().st_size
        logger.debug(f"File size for {path}: {file_size} bytes")
    except Exception as e:
        logger.warning(f"Could not get file size for {path}: {e}")
        file_size = 0

    # Large files (>2GB) are typically checkpoints, not LoRAs or VAEs
    if file_size > 2 * 1024 * 1024 * 1024:  # 2GB threshold
        path_lower = str(path).lower()
        if "checkpoint" in path_lower or "ckpt" in path_lower:
            logger.debug(f"Detected checkpoint (large file + name) for: {path}")
            return "checkpoint"
        # Even if path says lora/vae, size indicates checkpoint
        logger.debug(f"Detected checkpoint (large file) for: {path}")
        return "checkpoint"

    # Check path first as it's often more reliable
    path_lower = str(path).lower()
    if "lora" in path_lower and file_size < 1024 * 1024 * 1024:  # <1GB
        logger.debug(f"Detected LoRA based on path and size: {path}")
        return "lora"
    elif "controlnet" in path_lower:
        logger.debug(f"Detected ControlNet based on path: {path}")
        return "controlnet"
    elif "vae" in path_lower and file_size < 1024 * 1024 * 1024:  # <1GB
        logger.debug(f"Detected VAE based on path and size: {path}")
        return "vae"
    elif "checkpoint" in path_lower:
        logger.debug(f"Detected checkpoint based on path: {path}")
        return "checkpoint"

    # Fall back to metadata
    if not metadata:
        logger.debug(f"No metadata available, defaulting for: {path}")
        return "unknown"

    keys_lower = " ".join(f"{k} {v}" for k, v in metadata.items()).lower()
    if "lora" in keys_lower and file_size < 1024 * 1024 * 1024:
        logger.debug(f"Detected LoRA based on metadata: {path}")
        return "lora"
    elif "controlnet" in keys_lower:
        logger.debug(f"Detected ControlNet based on metadata: {path}")
        return "controlnet"
    elif "vae" in keys_lower and file_size < 512 * 1024 * 1024:  # VAEs typically <512MB
        logger.debug(f"Detected VAE based on metadata: {path}")
        return "vae"

    # Check for specific tensor keys that indicate model type
    try:
        with safe_open(str(path), framework="pt", device="cpu") as f:
            keys = list(f.keys())
            keys_str = str(keys)
            if "lora_down" in keys_str or "lora.down" in keys_str:
                logger.debug(f"Detected LoRA based on tensor keys: {path}")
                return "lora"
            elif "input_blocks" in keys_str and "middle_blocks" in keys_str:
                logger.debug(f"Detected ControlNet based on tensor keys: {path}")
                return "controlnet"
            elif "first_stage_model" in keys_str:
                logger.debug(f"Detected VAE based on tensor keys: {path}")
                return "vae"
            # Check for common checkpoint keys
            elif any(k in keys_str for k in ["model.diffusion_model", "cond_stage_model", "unet"]):
                logger.debug(f"Detected checkpoint based on tensor keys: {path}")
                return "checkpoint"
    except Exception as e:
        logger.warning(f"Error checking tensor keys for {path}: {e}", exc_info=True)

    # If still unknown and large file, assume checkpoint
    if file_size > 1024 * 1024 * 1024:  # >1GB
        logger.debug(f"Defaulting to checkpoint based on size for: {path}")
        return "checkpoint"

    logger.debug(f"Could not determine model type, defaulting to unknown for: {path}")
    return "unknown"

def scan(compute_hashes: bool = False, comfy_root: Optional[Union[str, Path]] = None, logger: Optional[logging.Logger] = None) -> List[Dict]:
    """
    Scan model directories and collect information about model files
    :param compute_hashes: Whether to compute SHA256 hashes for files
    :param comfy_root: Path to ComfyUI root directory
    :param logger: Logger instance for logging messages
    :return: List of model file records
    """
    if logger is None:
        logger = logging.getLogger(__name__)
        
    logger.info("Starting model scan")
    results = []
    roots = discover_roots(comfy_root=comfy_root, logger=logger)
    exts_st = {".safetensors"}
    # Only index ckpt/pt for name+size; skip loading due to pickle risk
    exts_ckpt = {".ckpt", ".pt"}

    total_files = 0
    processed_files = 0

    for root in roots:
        logger.info(f"Scanning directory: {root}")
        for dirpath, _, files in os.walk(root):
            total_files += len(files)
            for fn in files:
                p = Path(dirpath) / fn
                ext = p.suffix.lower()
                rec = {
                    "path": str(p),
                    "size_bytes": p.stat().st_size if p.exists() else None,
                    "sha256": None,
                    "type_hint": None,
                    "metadata": None,
                }
                try:
                    if ext in exts_st:
                        logger.debug(f"Processing safetensors file: {p}")
                        rec["metadata"] = read_safetensors_metadata(p, logger)
                        if compute_hashes:
                            rec["sha256"] = sha256_fast(p, logger=logger)
                        rec["type_hint"] = detect_model_type(rec["metadata"], p, logger)
                        processed_files += 1
                    elif ext in exts_ckpt:
                        # Do not torch.load; record basic info only
                        logger.debug(f"Processing checkpoint file: {p}")
                        rec["type_hint"] = "ckpt_or_pt_unsafe"
                        processed_files += 1
                    else:
                        logger.debug(f"Skipping file with unsupported extension: {p}")
                        continue
                except Exception as e:
                    logger.error(f"Error processing file {p}: {e}", exc_info=True)
                    rec["metadata"] = {"error": str(e), "error_type": type(e).__name__, "error_path": str(p)}
                results.append(rec)
    
    logger.info(f"Scan completed. Processed {processed_files} out of {total_files} total files")
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scan ComfyUI model folders")
    parser.add_argument("--hashes", action="store_true", help="Compute SHA256 hashes")
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--dir", help="Directory to scan (default: script's parent directory)")
    parser.add_argument("-v", "--verbose", action="count", default=0, 
                        help="Increase verbosity (use -v, -vv, or -vvv for more detail)")
    args = parser.parse_args()

    try:
        # Setup logging
        logger = setup_logging(args.verbose)
        
        logger.info("Starting ComfyUI model scanner")
        logger.debug(f"Arguments: compute_hashes={args.hashes}, output={args.output}, dir={args.dir}, verbose={args.verbose}")
        
        out = scan(compute_hashes=args.hashes, comfy_root=args.dir, logger=logger)
        
        if args.output:
            logger.info(f"Writing output to: {args.output}")
            with open(args.output, "w") as f:
                json.dump(out, f, indent=2)
            logger.info("Output written successfully")
        else:
            print(json.dumps(out, indent=2))
        
        logger.info("ComfyUI model scanner completed")
    except KeyboardInterrupt:
        logger.info("Scan interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during scanning: {e}", exc_info=True)
        sys.exit(1)
