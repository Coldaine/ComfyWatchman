# Inspecting Model Metadata

The `inspect` command provides a deterministic way to summarise ComfyUI model
assets without loading large tensors. It is intended for quick, offline
metadata checks and for scripting model inventories.

## Basic usage

Run the inspector against a single file to print a concise text summary:

```bash
comfywatchman inspect /path/to/model.safetensors
```

Use JSON when you want structured output:

```bash
comfywatchman inspect /path/to/model.ckpt --format json
```

Multiple paths are supported and traversal order is deterministic. Directories
are scanned non-recursively by default. Enable recursion with:

```bash
comfywatchman inspect /path/to/models --recursive
```

## Recognised formats

- `.safetensors` – reads header metadata only via `safetensors.safe_open()`.
- `.ckpt`, `.pt`, `.pth`, `.bin` – **unsafe loading is disabled by default.**
  Pass `--unsafe` to opt-in to `torch.load(..., map_location="cpu")` for a
  shallow summary of top-level keys.
- `.onnx` – reports IR version, opsets, and producer metadata when the `onnx`
  package is installed.
- Diffusers directories (containing `model_index.json`) – summarised at the
  directory level with pipeline class and component stubs.
- Other extensions are treated as `format="other"` with a warning.

## Safety defaults

- Unsafe operations (pickle loading) are **opt-in** via `--unsafe`.
- Hashing is optional (`--hash`) and can be slow on large files.
- Diffusers component listings can be disabled with `--no-components`.
- Outputs are deterministic: traversal and JSON key ordering are stable, and
  no timestamps are included.

## Exit codes

The CLI returns exit code `0` on success and `1` if any inspected file
produces warnings (e.g., unrecognized format, read failures, metadata parsing
errors). This allows scripts to detect potential issues:

```bash
if comfywatchman inspect model.safetensors --format json; then
    echo "Clean inspection"
else
    echo "Inspection completed with warnings"
fi
```

## Example commands

```bash
# Inspect a LoRA safetensors file with metadata keys
comfywatchman inspect path/to/lora.safetensors

# Emit JSON for automation
comfywatchman inspect path/to/model.pth --format json

# Summarise an ONNX model (requires the onnx extra)
comfywatchman inspect path/to/clip.onnx

# Review a Diffusers pipeline
comfywatchman inspect path/to/diffusers_repo --no-components

# IP-Adapter .bin file with opt-in unsafe metadata (requires torch)
comfywatchman inspect path/to/ip-adapter.bin --unsafe
```

## Library usage

The inspector can be used directly from Python:

```python
from comfyfixersmart.inspector import inspect_file, inspect_paths

summary = inspect_file("model.safetensors")
bulk = inspect_paths(["model.safetensors", "models/"], fmt="json", recursive=True)
```

Both functions avoid loading tensors and return deterministic dictionaries that
can be safely logged or serialised.

