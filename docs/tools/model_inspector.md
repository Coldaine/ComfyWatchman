# Model Metadata Inspector

Safe-by-default tooling for summarising ComfyUI model assets.

- `.safetensors`: header metadata only via `safetensors.safe_open`.
- `.ckpt` / `.pt` / `.pth` / `.bin`: pickle containers stay unopened unless `--unsafe`.
- `.onnx`: reads basic metadata when the optional `onnx` dependency is present.
- Diffusers directories: summarised at directory level with optional component listings.
- Optional SHA256 hashing (`--hash`) for integrity checks.

## CLI

- `comfywatchman inspect path/to/file.safetensors`
- `comfywatchman inspect /path/to/models --recursive --format json`
- `comfy-inspect path/to/repo --no-components`

Both commands share the same flags and exit with non-zero status when any entry reports warnings.

## Library

```python
from comfyfixersmart.inspector import inspect_file, inspect_paths

single = inspect_file("model.safetensors")
bulk = inspect_paths(["model.safetensors", "models/"], fmt="json", recursive=True)
```

Each result is a dict with stable keys:

- `filename`, `path`, `size_bytes`, `format`
- `type_hint`, `family` (optional), `source_hints` (optional)
- `metadata` (format specific), `warnings`
- `sha256` (only when hashing enabled)

## Safety Notes

- Unsafe pickle loading is opt-in only (`--unsafe`).
- Safetensors and ONNX reads avoid tensor materialisation.
- Hashing large files can be slow; enable only when required.
