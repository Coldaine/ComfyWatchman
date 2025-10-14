# AGENTS.md

This file provides project context and instructions for AI coding agents working with this repository.

## Project Overview

**ComfyWatchman** (package name: `comfywatchman`, project name: ComfyFixerSmart) is an intelligent Python tool that analyzes ComfyUI workflows, identifies missing models and custom nodes, searches for them on Civitai and HuggingFace, and automates the download process.

**Target Use Case**: Video generation workflows (WAN 2.2, etc.) and general ComfyUI model management

**Development Philosophy**: Solo developer project - favor practical solutions over enterprise patterns, reuse existing code patterns, avoid unnecessary abstractions.

**COMFYUI_ROOT** must point to `/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable`. Every download belongs inside `${COMFYUI_ROOT}/models/<type>/`; the repository itself should never contain `.safetensors`, `.ckpt`, `.pt`, `.pth`, `.bin`, `.onnx`, `.npz`, or other large binaries.

**Configuration guardrails** live in `config/default.toml`, which now pins `comfyui_root` and `workflow_dirs` to the paths above. Temporary overrides can export `COMFYUI_ROOT="/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable"`, but clear them before finishing work so the default remains authoritative.

**Failure-first policy**: abort immediately if `config.models_dir` is missing or cannot be resolved. Generated download scripts must refuse to run without a valid models directory and should never embed raw model binaries.

**Git hygiene**: run `git status` before and after changes. The pre-commit hook blocks files ≥ 90 MB, and `.gitignore` already excludes weights, archives, partial downloads, and generated scripts—leave those defenses intact.

**Escalation protocol**: any scope changes for Phase 1 or Phase 2 (see `docs/vision.md`) require explicit owner approval. Surface uncertainties instead of guessing about download destinations or behavior.

## Critical Paths

### ComfyUI Installation
- **Root**: `/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/`
- **Workflows**: `/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/user/default/workflows/`
- **Models**: `/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/models/`
- **Custom Nodes**: `/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/custom_nodes/`

### API Keys
API keys are in `~/.secrets`, auto-loaded via `~/.bashrc`:
- `CIVITAI_API_KEY` - Required for Civitai downloads
- `HF_TOKEN` - Optional for HuggingFace private models

## Setup and Installation

```bash
# Development installation
pip install -e .

# With dev dependencies
pip install -e .[dev]
```

## Running the Tool

```bash
# Basic usage (analyzes configured workflow directories)
comfywatchman

# Analyze specific workflow
comfywatchman path/to/workflow.json

# Analyze directory
comfywatchman --dir /path/to/workflows

# Search backends
comfywatchman --search civitai,huggingface

# V1 mode (incremental, Qwen search)
comfywatchman --v1

# V2 mode (batch, default)
comfywatchman --v2
```

## Configuration

**Priority order** (highest to lowest):
1. Command-line arguments
2. Environment variables (`COMFYUI_ROOT`, `OUTPUT_DIR`, etc.)
3. Config file (`config/default.toml` or via `--config`)
4. Built-in defaults

**Required**: `comfyui_root` must be configured (no default path)

Create `config/default.toml` from `config-example.toml`:
```toml
comfyui_root = "/path/to/ComfyUI"
workflow_dirs = ["user/default/workflows"]
```

## Architecture

### Module Structure
```
src/comfyfixersmart/
├── cli.py              # CLI entry point
├── core.py             # ComfyFixerCore orchestrator
├── config.py           # TOML + env var configuration
├── scanner.py          # Workflow scanning & model extraction
├── inventory.py        # Local model/node inventory
├── search.py           # Multi-backend search (Civitai, HF, Qwen)
├── download.py         # Download management
├── state_manager.py    # State tracking & caching
├── logging.py          # Structured logging
└── utils.py            # Shared utilities
```

### Key Classes
- **ComfyFixerCore**: Main orchestrator (`run_workflow_analysis()`)
- **WorkflowScanner**: Parse workflows, extract models
- **ModelInventory**: Build local model inventory
- **ModelSearch**: Unified search with multiple backends
- **StateManager**: Track downloads, prevent duplicates
- **Config**: TOML + env var configuration manager

## Development Commands

```bash
# Run tests
pytest

# Coverage report
pytest --cov=comfywatchman --cov-report=html

# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/
```

## Coding Standards

### Python Style
- Use Python 3.7+ compatible syntax
- Follow existing code patterns in the module
- Type hints for function signatures
- Docstrings for public APIs

### Module Organization
- One class per file when classes are substantial
- Related utilities grouped together
- Clear separation of concerns (scanning, searching, downloading)

### Configuration Management
- All configurable values go through `config.py`
- Support both TOML files and environment variables
- Command-line args override everything

### State and Caching
- Use `StateManager` for download tracking
- Cache search results to minimize API calls
- Persist state to `state_dir/download_state.json`

## Important Patterns

### Model Type Mapping
ComfyUI node types map to model directories via `config.model_type_mapping`:
```python
{
    'CheckpointLoaderSimple': 'checkpoints',
    'LoraLoader': 'loras',
    'VAELoader': 'vae',
    'ControlNetLoader': 'controlnet',
    'UpscaleModelLoader': 'upscale_models',
    # ... see config.py for complete mapping
}
```

### Workflow JSON Structure
ComfyUI workflows have this structure:
```json
{
  "nodes": [
    {
      "id": "1",
      "type": "CheckpointLoaderSimple",
      "widgets_values": ["model_name.safetensors", ...]
    }
  ]
}
```

Model references are in `widgets_values` arrays. Scanner looks for strings ending in: `.safetensors`, `.ckpt`, `.pt`, `.bin`, `.pth`

### Search Results
- Return `SearchResult` objects with download URLs
- Support multiple backends: Civitai (primary), HuggingFace, Qwen
- Cache results in `temp_dir/search_cache/`

### Logging
- Console: INFO level, user-friendly
- File: DEBUG level, in `log/run_YYYYMMDD_HHMMSS.log`
- Use `from comfyfixersmart.logging import get_logger`

## Test Strategy

### Test Structure
- `tests/unit/` - Individual module tests
- `tests/integration/` - Module interaction tests
- `tests/functional/` - End-to-end tests
- `tests/fixtures/` - Shared fixtures
- `tests/test_data/` - Sample workflow files

### Testing Patterns
- Mock external APIs (Civitai, HuggingFace)
- Use sample workflow JSON files
- Test state persistence and recovery
- Verify file operations without actual downloads

## Common Tasks

### Adding New Search Backend
1. Create class inheriting from `SearchBackend` in `search.py`
2. Implement `search()` returning `SearchResult`
3. Implement `get_name()` returning identifier
4. Register in `ModelSearch.__init__()` backends dict

### Adding Model Type Support
1. Update `model_type_mapping` in `config.py`
2. Add type filter in `CivitaiSearch._get_type_filter()`
3. Update documentation

### Extending CLI
1. Add argument in `cli.create_parser()`
2. Update `cli.update_config_from_args()` if needed
3. Pass through to `core.run_workflow_analysis()`

## Output Files

**Results** (in `output_dir`, default `./output/`):
- `missing_models_RUNID.json` - Models not found locally
- `resolutions_RUNID.json` - Search results with URLs
- `download_missing_RUNID.sh` - Generated download script
- `found_models_cache.json` - Cached inventory

**Logs** (in `log_dir`, default `./log/`):
- `run_RUNID.log` - Main execution log
- `structured.log` - Structured output
- `qwen_search_history.log` - Qwen operations

**State** (in `state_dir`, default `./state/`):
- `download_state.json` - Download tracking

## Key Files

- `pyproject.toml` - Package metadata, dependencies, build config
- `REQUIREMENTS.md` - Original requirements (historical)
- `INSTALL.md` - User installation guide
- `config-example.toml` - Configuration template
- `CLAUDE.md` - Claude Code specific instructions
- `legacy/` - Previous implementations (reference)
- `archives/` - Historical tools (ScanTool, etc.)
- `docs/planning/RIGHT_SIZED_PLAN.md` - Core architecture
- `docs/planning/AGENT_GUIDE.md` - AI agent usage guide
- `docs/research/` - Related systems research

## Strategic Context

This project is at a strategic crossroads regarding integration with ComfyUI-Copilot and similar tools:
- `docs/CROSSROADS.md` - Strategic decision framework
- `docs/research/EXISTING_SYSTEMS.md` - Analysis of related tools
- `docs/vision.md` - Long-term vision with LLM integration

**Owner Directive**: Phase 1 and Phase 2 requirements in Vision and Architecture docs require explicit owner consent to modify.

## Package Information

- **Package name**: `comfywatchman` (PyPI)
- **Project name**: ComfyFixerSmart (repository)
- **Entry point**: `comfywatchman` command
- **Version**: 2.0.0 (development, not yet on PyPI)
- **License**: MIT

## Development Notes

- Solo developer project - no enterprise overhead
- Reuse existing patterns from codebase
- Practical solutions over complex abstractions
- Video generation workflows are primary but tool is general-purpose
- Legacy code in `legacy/` and `archives/` for reference only
