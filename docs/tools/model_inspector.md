# Model Metadata Inspector (DP-016)

Safe, metadata-only inspection tool for ComfyUI model files.

- Safetensors: reads headers/metadata via safetensors.safe_open (no tensor materialization)
- PyTorch pickles (.pth/.ckpt/.pt/.bin): never unpickle; flagged unsafe
- ONNX: best-effort format detection (no dependency required)
- Optional SHA256 for integrity bookkeeping

## CLI

- Inspect files or directories:
  - comfywatchman-inspect path/to/file.safetensors
  - comfywatchman-inspect /path/to/models --hash --json

Exit code is non-zero if any item is unsafe or has errors.

## Library

Python API:

- from comfyfixersmart.inspector import inspect_file, inspect_paths
- returns InspectionResult objects with fields: path, size, ext, type_hint, safe_to_load, format, tensors, metadata, sha256, error

## Safety Notes

- Never call torch.load on external files.
- For .safetensors we read headers only. In rare corrupt files, we report an error.
- Hashing large files can be slow; use --hash selectively.
