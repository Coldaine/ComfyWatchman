# Inspecting Model Metadata

The `inspect` command provides a safe, deterministic way to summarize ComfyUI model assets without loading large tensors into memory. It is intended for quick, offline metadata checks and for scripting model inventories.

## Basic Usage

You can run the inspector against a single file or an entire directory.

### Inspecting a Single File
To print a concise text summary of a single model:
```bash
comfywatchman inspect /path/to/model.safetensors
```

For scriptable output, use the JSON format:
```bash
comfywatchman inspect /path/to/model.ckpt --format json
```

### Inspecting a Directory
Directories are scanned non-recursively by default. Use the `--recursive` flag to scan all subdirectories:
```bash
comfywatchman inspect /path/to/models --recursive
```

## Command-Line Interface (CLI)

The inspector is available through two commands, which share the same flags:
*   `comfywatchman inspect <path>`
*   `comfy-inspect <path>` (standalone entry point)

### Key Flags
*   `--format text|json`: Sets the output format (default: `text`).
*   `--recursive`: Scans directories recursively.
*   `--hash`: Computes the SHA256 hash of each file (can be slow).
*   `--unsafe`: **(Use with caution)** Opt-in to shallowly load pickle-based formats (`.ckpt`, `.pt`, `.pth`) to read top-level keys.
*   `--summary` / `--no-summary`: Toggles the concise summary view in text mode.
*   `--no-components`: Disables listing components for Diffusers directories.

## Supported Formats & Safety Defaults

The inspector is **safe by default** and will not execute any code from model files.

*   **`.safetensors`**: Reads header metadata only. Tensors are not loaded.
*   **`.ckpt`, `.pt`, `.pth`, `.bin`**: These pickle-based formats are **not opened by default** due to security risks. Basic file info is provided. You must pass the `--unsafe` flag to inspect their internal structure.
*   **`.onnx`**: Reports model metadata (IR version, opsets) if the optional `onnx` package is installed.
*   **Diffusers Directories**: Summarized at the directory level.

## Library Usage (Python API)

You can use the inspector's functions directly in your Python code.

```python
from comfyfixersmart.inspector import inspect_file, inspect_paths

# Inspect a single file
summary = inspect_file("model.safetensors", do_hash=True)

# Inspect multiple paths and get JSON-like output
bulk_results = inspect_paths(
    ["model.safetensors", "models/"], 
    fmt="json", 
    recursive=True
)
```
Both functions return deterministic dictionaries containing stable keys, making them safe to log or serialize.

### Result Data Structure
Each result is a dictionary with the following keys:
*   `filename`, `path`, `size_bytes`, `format`
*   `type_hint` (e.g., `checkpoint`, `lora`, `vae`)
*   `family` (optional, e.g., "sdxl", "flux")
*   `metadata` (a subset of format-specific metadata)
*   `warnings` (a list of any issues encountered)
*   `sha256` (string or null, only present when `--hash` is used)

## Exit Codes for Scripting

The CLI is designed for automation and returns specific exit codes:
*   **`0`**: The inspection was successful with no warnings.
*   **`1`**: The inspection completed but one or more files produced warnings (e.g., unrecognized format, read failure).

You can use this in scripts to detect potential issues:
```bash
if comfywatchman inspect model.safetensors; then
    echo "Clean inspection."
else
    echo "Inspection completed with warnings."
fi
```