# Builder Prompt: Implement a Model Metadata Inspector Tool (CLI + Library)
<!-- markdownlint-disable MD032 -->

You are a research/implementation agent. Your task is to IMPLEMENT a Python tool (library + CLI) inside this repository that inspects model files and emits concise, safety-conscious summaries. Do not inspect any files yourself; instead, produce code, tests, and docs that enable users to run the tool locally.

## Objective

Create a first-class "Model Metadata Inspector" integrated into the `comfywatchman` package that:
- Safely extracts lightweight metadata from model files without executing untrusted code
- Works on single files and directories (optional recursion)
- Outputs either concise text summaries or structured JSON

## Non-negotiable Guardrails (align with AGENTS.md)

- No model binaries committed; never embed weights into the repo.
- Failure-first: if required directories or config are missing, exit with a clear error.
- Safety: Never import/execute code from model files. Do NOT use `torch.load` by default for pickle-based formats.
- Configuration guardrails live in `config/default.toml`; do not change pinned paths unless owner-approved.
- Keep code small and practical; reuse existing patterns from `src/comfyfixersmart`.

## Scope of Work

1) Library module
   - File: `src/comfyfixersmart/inspector.py`
   - Expose a typed API:
     - `inspect_paths(paths: list[str], *, recursive: bool = False, fmt: Literal["text","json"] = "text", summary: bool = True, do_hash: bool = False, unsafe: bool = False) -> str | list[dict]`
     - `inspect_file(path: str, *, do_hash: bool = False, unsafe: bool = False) -> dict`
   - Support extensions: `.safetensors`, `.ckpt`, `.pt`, `.pth`, `.onnx`; treat others as `format="other"` with warnings.
   - Do not load tensors. For `.safetensors`, read header via `safetensors.safe_open(...).metadata()` only.
   - For `.pth/.pt/.ckpt`, default is safe mode: no unpickle. If `unsafe=True`, allow `torch.load(..., map_location='cpu', weights_only=True)` and summarise top-level keys (count + first few names).
   - For `.onnx`, if `onnx` is available, read metadata (ir_version, opset, producer). If not installed, return a warning.
   - Derive `type_hint` using metadata + filename heuristics (see Heuristics below).

2) CLI integration
   - Add a subcommand `inspect` to the existing CLI (`src/comfyfixersmart/cli.py`).
   - CLI signature:
     - `comfywatchman inspect <path> [--recursive] [--format text|json] [--summary/--no-summary] [--hash] [--unsafe]`
   - Print text to stdout in `text` mode; emit JSON to stdout in `json` mode.
   - Exit code: 0 on success; non-zero on fatal errors. Partial per-file errors must appear under `warnings`.

3) Packaging
   - Update `pyproject.toml` with an optional extra `inspector` including:
     - `safetensors>=0.4.2` (or current stable)
     - `onnx>=1.14.0` (optional; tool should degrade gracefully if missing)
     - `torch` is NOT required for safe mode. If used in tests for `unsafe` path, mark test as skipped when torch missing.
   - Do not add heavy runtime deps by default; keep them optional.

4) Tests and fixtures
   - Add unit tests under `tests/unit/test_inspector.py` covering:
     - Safetensors metadata extraction (create a tiny file at runtime using `safetensors` APIs; do NOT commit binaries).
     - PTH safe mode returns warning and basic info; `unsafe` path is skipped unless torch is available.
     - ONNX summarization when `onnx` is installed; otherwise a clear warning is emitted.
     - Directory recursion and mixed extensions; resilience to unreadable/corrupt files.
   - Add minimal integration test for CLI: run `comfywatchman inspect` against a temp directory and assert JSON structure.

5) Documentation
   - Create `docs/usage/inspect.md` with quickstart, examples, and safety notes.
   - Update `CHANGELOG.md` (Unreleased) with the new `inspect` command.

## Safety Rules (enforced in code)

- Never import or execute code from model files.
- `.safetensors`: metadata/header only.
- `.pth/.pt/.ckpt`: default = no unpickle. `unsafe=True` must be opt-in and clearly marked in help text.
- `.onnx`: read graph/model metadata only; never execute ops.
- Hashing is optional (`--hash`) and may be slow; print progress only if necessary.

## Data Contract (per-file result)

Fields to populate in the result dict:
- `filename`, `path`, `size_bytes`
- `format`: safetensors | pth | pt | ckpt | onnx | other
- `type_hint`: checkpoint | lora | lycoris | locon | embedding | vae | vae_approx | controlnet | t2i_adapter | ip_adapter | hypernetwork | upscale | sam | clip | clip_vision | unet | t5 | motion | face_restore | segmentation | yolo | flux | unknown
- `metadata`: concise subset; for safetensors include up to 20 `__metadata__` keys (not tensors)
- `sha256`: string | null (only when `--hash`)
- `source_hints`: optional
- `warnings`: list[str]
- `family`: optional string capturing architecture family (e.g., "sd1.5", "sdxl", "flux")

## Heuristics for `type_hint`

- Prefer directory hints first when path includes a known ComfyUI models dir name; fall back to filename and metadata. If `config.model_type_mapping` exists, reuse it to inform mapping.
- safetensors metadata contains: keys with "lora" → lora; "lycoris" → lycoris; "controlnet" → controlnet; `modelspec.architecture` containing "vae" → vae; `modelspec.architecture` containing "flux" → flux (also set `family="flux"`).
- filename and directory families:
   - embeddings dir or names like `ti_*`, `embedding*`, files ending `.pt`/`.bin` under `embeddings/` → embedding
   - `lycoris*`, `locon*`, files under `lycoris/` → lycoris or locon
   - `ipadapter*`, `ip-adapter*`, files under `ipadapter/` → ip_adapter
   - `t2iadapter*`, `t2i_adapter*`, files under `t2i_adapter/` → t2i_adapter
   - `hypernetwork*`, files under `hypernetworks/` → hypernetwork
   - `sam_*.pth`, files under `sam/` → sam
   - `RealESRGAN_*`, `ESRGAN*`, files under `upscale_models/` → upscale
   - `gfpgan*`, `codeformer*` → face_restore
   - `yolo*`, `ultralytics*` → yolo (segmentation/detection)
   - `clip_vision*` or under `clip_vision/` → clip_vision
   - `t5*` (text encoder) → t5
   - `animatediff*`, `mm_*`, `motion*` → motion
   - `vae_approx*` or under `vae_approx/` → vae_approx
   - `flux*` checkpoint/unet names → flux (also set `family="flux"`)
   - default: large `.safetensors`/`.ckpt`/`.pt` under `checkpoints/` → checkpoint
- coarse size ranges: LoRA often < 200MB; checkpoints often > 2GB; VAEs < 600MB (heuristic only). Use size only as a secondary signal.

## Output Modes

- `text`: ≤10 lines per file: filename, format, size, type_hint, 3–8 salient metadata items, warnings (if any)
- `json`: JSON array of objects with the fields defined above. Errors recorded in `warnings` must not crash the whole run.

## Deliverables (files to add/modify)

- Add: `src/comfyfixersmart/inspector.py` (library)
- Modify: `src/comfyfixersmart/cli.py` (add `inspect` subcommand)
- Modify: `pyproject.toml` (optional extra `inspector`)
- Add: `tests/unit/test_inspector.py` (unit + CLI smoke tests)
- Add: `docs/usage/inspect.md` (usage and safety)
- Modify: `CHANGELOG.md` (Unreleased section)

## Acceptance Criteria

- Library API and CLI behave as specified.
- Safe by default: never unpickle by default; clear `--unsafe` gating and help text.
- Works on single file and directory (with `--recursive`).
- Text output concise; JSON output validates with expected keys.
- Tests PASS locally without requiring internet or large binaries; generate tiny fixtures at runtime.
- Lint/typecheck PASS (reuse repo settings). No new large files added to repo.

## Developer Notes

- Use absolute paths in any background operations (if any); avoid relying on shell cwd.
- For shell examples in docs, prefer POSIX-compatible commands; note that fish shell users should avoid heredocs.
- Use existing logging pattern from `src/comfyfixersmart/logging.py` for structured logs if needed.

## Example CLI (for docs)

```text
comfywatchman inspect /path/to/models --format json > report.json
comfywatchman inspect /path/to/file.safetensors --summary --hash
comfywatchman inspect /path/to/checkpoint.ckpt --unsafe --format text
```

Focus on practicality and minimal footprint. Implement end-to-end in this repo with tests and docs.
