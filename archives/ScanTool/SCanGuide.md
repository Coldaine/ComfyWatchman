

# Script Review: ComfyUI Model Scanner

I've reviewed your Python script for scanning ComfyUI model folders and extracting metadata from .safetensors files. Overall, it's a well-structured script that follows good security practices, but there are several areas that could be improved.

## Strengths

1. **Security-conscious approach**: Using `safe_open` to extract metadata without loading tensors is excellent.
2. **Avoiding pickle risks**: Correctly avoids loading .ckpt/.pt files which could execute malicious code.
3. **Modular design**: Functions are well-separated and focused on specific tasks.
4. **Comprehensive path handling**: Attempts to include both default and extra model paths.

## Issues and Improvements

### 1. YAML Parsing
The current approach to parsing `extra_model_paths.yaml` is too simplistic:

```python
# Current approach
if line.startswith(("/", "C:", "D:", "E:")) and ("models" in line.lower()):
```

This is platform-specific and won't correctly parse YAML structure. Instead, use a proper YAML parser:

```python
import yaml

def discover_roots():
    roots = []
    if MODELS_ROOT.exists():
        roots.append(MODELS_ROOT)
    
    # Proper YAML parsing
    for y in EXTRA_PATHS:
        try:
            config = yaml.safe_load(y.read_text(encoding="utf-8", errors="ignore"))
            if config and isinstance(config, dict):
                for key, value in config.items():
                    if isinstance(value, dict) and "models" in value:
                        models_path = Path(value["models"])
                        if models_path.exists():
                            roots.append(models_path)
        except Exception as e:
            print(f"Error parsing {y}: {e}", file=sys.stderr)
    
    # Deduplicate while preserving order
    uniq = []
    seen = set()
    for r in roots:
        rp = r.resolve()
        if rp not in seen:
            uniq.append(rp)
            seen.add(rp)
    return uniq
```

### 2. Optional Hashing
Calculating SHA256 for every file can be slow. Make it optional:

```python
def scan(compute_hashes=False):
    # ... existing code ...
    if ext in exts_st:
        rec["metadata"] = read_safetensors_metadata(p)
        if compute_hashes:
            rec["sha256"] = sha256_fast(p)
```

### 3. Better Type Detection
Improve the model type detection logic:

```python
def detect_model_type(metadata, path):
    # Check path first as it's often more reliable
    path_lower = str(path).lower()
    if "lora" in path_lower:
        return "lora"
    elif "controlnet" in path_lower:
        return "controlnet"
    elif "vae" in path_lower:
        return "vae"
    
    # Fall back to metadata
    if not metadata:
        return "unknown"
    
    keys_lower = " ".join(f"{k} {v}" for k, v in metadata.items()).lower()
    if "lora" in keys_lower:
        return "lora"
    elif "controlnet" in keys_lower:
        return "controlnet"
    elif "vae" in keys_lower:
        return "vae"
    
    # Check for specific tensor keys that indicate model type
    try:
        with safe_open(str(path), framework="pt", device="cpu") as f:
            keys = list(f.keys())
            if "lora_down" in str(keys):
                return "lora"
            elif "input_blocks" in str(keys) and "middle_blocks" in str(keys):
                return "controlnet"
            elif "first_stage_model" in str(keys):
                return "vae"
    except Exception:
        pass
    
    return "checkpoint_or_other"
```

### 4. Command Line Arguments
Add command line options for better usability:

```python
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scan ComfyUI model folders")
    parser.add_argument("--hashes", action="store_true", help="Compute SHA256 hashes")
    parser.add_argument("--output", help="Output file (default: stdout)")
    args = parser.parse_args()
    
    out = scan(compute_hashes=args.hashes)
    if args.output:
        with open(args.output, "w") as f:
            json.dump(out, f, indent=2)
    else:
        print(json.dumps(out, indent=2))
```

### 5. Error Handling
Improve error handling to be more specific:

```python
def read_safetensors_metadata(path):
    meta = {}
    try:
        with safe_open(str(path), framework="pt", device="cpu") as f:
            meta = dict(f.metadata() or {})
    except Exception as e:
        meta = {"error": str(e), "error_type": type(e).__name__}
    return meta
```

## Revised Script

Here's a revised version of your script incorporating these improvements:

```python
#!/usr/bin/env python3
import os, sys, json, hashlib
from pathlib import Path
import argparse

# Optional: pip install safetensors pyyaml
from safetensors import safe_open
import yaml

COMFY_ROOT = Path(__file__).resolve().parent
MODELS_ROOT = COMFY_ROOT / "models"

# Add extra model roots if present (both actual and example file)
EXTRA_PATHS = []
for candidate in ["extra_model_paths.yaml", "extra_model_paths.yaml.example"]:
    cfg = COMFY_ROOT / candidate
    if cfg.exists():
        EXTRA_PATHS.append(cfg)

def discover_roots():
    roots = []
    if MODELS_ROOT.exists():
        roots.append(MODELS_ROOT)
    
    # Proper YAML parsing
    for y in EXTRA_PATHS:
        try:
            config = yaml.safe_load(y.read_text(encoding="utf-8", errors="ignore"))
            if config and isinstance(config, dict):
                for key, value in config.items():
                    if isinstance(value, dict) and "models" in value:
                        models_path = Path(value["models"])
                        if models_path.exists():
                            roots.append(models_path)
        except Exception as e:
            print(f"Error parsing {y}: {e}", file=sys.stderr)
    
    # Deduplicate while preserving order
    uniq = []
    seen = set()
    for r in roots:
        rp = r.resolve()
        if rp not in seen:
            uniq.append(rp)
            seen.add(rp)
    return uniq

def sha256_fast(path, chunk=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def read_safetensors_metadata(path):
    meta = {}
    try:
        with safe_open(str(path), framework="pt", device="cpu") as f:
            meta = dict(f.metadata() or {})
    except Exception as e:
        meta = {"error": str(e), "error_type": type(e).__name__}
    return meta

def detect_model_type(metadata, path):
    # Check path first as it's often more reliable
    path_lower = str(path).lower()
    if "lora" in path_lower:
        return "lora"
    elif "controlnet" in path_lower:
        return "controlnet"
    elif "vae" in path_lower:
        return "vae"
    
    # Fall back to metadata
    if not metadata:
        return "unknown"
    
    keys_lower = " ".join(f"{k} {v}" for k, v in metadata.items()).lower()
    if "lora" in keys_lower:
        return "lora"
    elif "controlnet" in keys_lower:
        return "controlnet"
    elif "vae" in keys_lower:
        return "vae"
    
    # Check for specific tensor keys that indicate model type
    try:
        with safe_open(str(path), framework="pt", device="cpu") as f:
            keys = list(f.keys())
            if "lora_down" in str(keys):
                return "lora"
            elif "input_blocks" in str(keys) and "middle_blocks" in str(keys):
                return "controlnet"
            elif "first_stage_model" in str(keys):
                return "vae"
    except Exception:
        pass
    
    return "checkpoint_or_other"

def scan(compute_hashes=False):
    results = []
    roots = discover_roots()
    exts_st = {".safetensors"}
    # Only index ckpt/pt for name+size; skip loading due to pickle risk
    exts_ckpt = {".ckpt", ".pt"}

    for root in roots:
        for dirpath, _, files in os.walk(root):
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
                        rec["metadata"] = read_safetensors_metadata(p)
                        if compute_hashes:
                            rec["sha256"] = sha256_fast(p)
                        rec["type_hint"] = detect_model_type(rec["metadata"], p)
                    elif ext in exts_ckpt:
                        # Do not torch.load; record basic info only
                        rec["type_hint"] = "ckpt_or_pt_unsafe"
                    else:
                        continue
                except Exception as e:
                    rec["metadata"] = {"error": str(e), "error_type": type(e).__name__}
                results.append(rec)
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scan ComfyUI model folders")
    parser.add_argument("--hashes", action="store_true", help="Compute SHA256 hashes")
    parser.add_argument("--output", help="Output file (default: stdout)")
    args = parser.parse_args()
    
    out = scan(compute_hashes=args.hashes)
    if args.output:
        with open(args.output, "w") as f:
            json.dump(out, f, indent=2)
    else:
        print(json.dumps(out, indent=2))
```

## Additional Recommendations

1. **Progress Indicator**: For large model collections, consider adding a progress indicator.
2. **Caching**: Implement a simple cache to avoid re-scanning unchanged files.
3. **Filtering**: Add options to filter by model type or other criteria.
4. **Database Output**: Consider adding an option to output to a SQLite database for easier querying.

The script is functional and secure, but these improvements would make it more robust, user-friendly, and efficient.