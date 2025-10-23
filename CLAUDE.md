# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ComfyWatchman** (formerly ComfyFixerSmart) is an intelligent tool that analyzes ComfyUI workflows, identifies missing models and custom nodes, searches for them on Civitai and HuggingFace, and automates the download process.

The project is a **Python package** designed for both CLI usage and programmatic integration.

### Relationship to ComfyUI-Copilot

**CRITICAL CONTEXT:** This project is designed to **complement and integrate with** [ComfyUI-Copilot](https://github.com/AIDC-AI/ComfyUI-Copilot), not compete with it.

**Strategic Integration:**
- **ComfyWatchman Focus:** Dependency resolution, model discovery, multi-backend search, offline-first operations
- **Copilot Focus:** Workflow generation, LLM orchestration, interactive debugging, UI integration
- **Upstream Remote:** `upstream` points to AIDC-AI/ComfyUI-Copilot for integration reference
- **Integration Approach:** ComfyWatchman provides advanced dependency management that can be used standalone OR integrated into Copilot's workflow

**Why This Matters:**
- PRs and issues from `upstream` (ComfyUI-Copilot) are for their project, not ours
- We provide complementary capabilities: better search (Civitai+HF vs ModelScope), better state management, CLI tools
- Our adapters (`adapters/copilot_validator.py`, `adapters/sql_state.py`) enable integration pathways
- See `docs/CROSSROADS.md` for the complete strategic analysis and decision framework

**Key Differentiators:**
1. **Multi-backend search** - CivitAI + HuggingFace + Qwen agent vs Copilot's ModelScope only
2. **Offline-first** - Works without constant LLM calls; deterministic and resumable
3. **CLI interface** - Automation-friendly command-line tools vs Copilot's web UI only
4. **Production-grade state management** - Sophisticated caching, retry logic, download verification

## Critical Path Information

### ComfyUI Installation Paths

**CRITICAL:** The actual ComfyUI installation is at:
- **Root:** `/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/`
- **Workflows:** `/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/user/default/workflows/`
- **Models:** `/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/models/`
- **Custom Nodes:** `/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/custom_nodes/`
- **Virtual Environment:** `/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/venv/`
- **Launch Script:** `/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/start_comfyui.sh`

**Symlink:** A symlink `./workflows/` points to the ComfyUI workflows directory for convenience.

### API Keys

API keys are stored in `~/.secrets` and auto-loaded via `~/.bashrc`. Use environment variables:
- `CIVITAI_API_KEY` - Required for Civitai API search
- `TAVILY_API_KEY` - Required for web search fallback (Qwen agent)
- `HF_TOKEN` or `HUGGINGFACE_TOKEN` - Optional for HuggingFace private models

## Architecture

### Modular Design

The codebase follows a clean modular architecture with separation of concerns:

```
src/comfyfixersmart/
├── cli.py                   # Main CLI entry point (comfywatchman command)
├── core.py                  # Main orchestrator (ComfyFixerCore class)
├── config.py                # Configuration management (TOML + env vars)
├── scanner.py               # Workflow scanning and model extraction
├── inventory.py             # Local model/node inventory building
├── search.py                # Multi-backend model search (Civitai, HF, Qwen)
├── download.py              # Download management and script generation
├── state_manager.py         # State tracking and caching
├── logging.py               # Structured logging utilities
├── utils.py                 # Shared utility functions
├── inspector/               # Model metadata inspection subsystem
│   ├── cli.py              # Inspector CLI entry point (comfy-inspect command)
│   ├── inspector.py        # Safe model metadata extraction
│   └── logging.py          # Inspector-specific logging
└── adapters/                # Optional integrations with external systems
    ├── base.py             # Base adapter abstract classes
    ├── copilot_validator.py # ComfyUI-Copilot validation adapter
    ├── sql_state.py        # SQL-based state backend (optional)
    ├── modelscope_search.py # ModelScope search backend
    └── modelscope_fallback.py # ModelScope download fallback
```

### Key Classes

**ComfyFixerCore** (`core.py`): Main orchestrator that coordinates the workflow
- `run_workflow_analysis()` - Primary entry point for analysis
- Returns `WorkflowRun` dataclass with complete run statistics

**WorkflowScanner** (`scanner.py`): Scans and parses ComfyUI workflow JSON files
- `scan_workflows()` - Find workflow files in directories
- `extract_models_from_workflow()` - Parse workflows and extract model references
- Returns `ModelReference` objects with filename, type, node_type, workflow_path

**ModelInventory** (`inventory.py`): Builds inventory of local ComfyUI models
- `build_inventory()` - Scan ComfyUI models directory recursively
- Returns dict mapping filenames to paths and metadata

**ModelSearch** (`search.py`): Unified search interface with multiple backends
- `search_model()` - Search single model across backends
- `search_multiple_models()` - Batch search with caching
- **Primary Backend**: `QwenSearch` - Agentic search orchestrating Civitai API + web search + HuggingFace discovery
- **Fallback Backend**: `CivitaiSearch` - Direct Civitai API (no agent reasoning)
- **Experimental**: `ModelScopeSearch` - Alternative model hub (optional)
- Returns `SearchResult` objects with download URLs and confidence levels
- See **[docs/SEARCH_ARCHITECTURE.md](docs/SEARCH_ARCHITECTURE.md)** for complete architecture details

**StateManager** (`state_manager.py`): Tracks download attempts and success/failure
- Persists state to `state_dir/download_state.json`
- Prevents duplicate downloads and supports retry logic

**Config** (`config.py`): Configuration via TOML files and environment variables
- Loads from `config/default.toml` if exists
- Environment variables override TOML values
- Global instance: `from comfyfixersmart.config import config`

**ModelInspector** (`inspector/inspector.py`): Safe metadata extraction from model files
- `inspect_file()` - Extract metadata from single file without loading tensors
- `inspect_paths()` - Batch inspection of files/directories
- Supports safetensors, ONNX, and (opt-in) pickle formats
- Returns lightweight metadata: file size, format, hash (optional), tensor info

**Adapters** (`adapters/`): Optional integrations following adapter pattern
- `BaseAdapter` - Abstract base for all adapters
- `CopilotValidatorAdapter` - Workflow validation via ComfyUI-Copilot
- `SqlStateAdapter` - Alternative SQL-based state persistence
- `ModelScopeSearch` - ModelScope hub search backend
- All adapters are optional dependencies, check `is_available()` before use

## Development Workflow

### Installation

```bash
# Development installation (editable mode)
pip install -e .

# With development dependencies
pip install -e .[dev]

# With optional dependencies
pip install -e .[inspector]    # Add safetensors/ONNX support
pip install -e .[copilot]      # Add Copilot validation adapter
pip install -e .[modelscope]   # Add ModelScope search backend
pip install -e .[full]         # Install all optional features
```

### Running the Tool

```bash
# Main workflow analysis tool
comfywatchman                              # Analyze all workflows
comfywatchman path/to/workflow.json        # Analyze specific workflow
comfywatchman --dir /path/to/workflows     # Analyze directory
comfywatchman --search civitai,huggingface # Use specific backends
comfywatchman --v1                         # V1 mode (incremental + Qwen)
comfywatchman --v2                         # V2 mode (batch, default)

# Model metadata inspector (separate tool)
comfy-inspect model.safetensors            # Inspect single model
comfy-inspect models/ --recursive          # Inspect directory recursively
comfy-inspect model.ckpt --unsafe          # Allow pickle loading (caution!)
comfy-inspect models/ --format json        # Output as JSON
comfy-inspect models/ --hash               # Include SHA256 hashes
```

### Configuration

Configuration priority (highest to lowest):
1. Command-line arguments (`--comfyui-root`, `--output-dir`, etc.)
2. Environment variables (`COMFYUI_ROOT`, `OUTPUT_DIR`, etc.)
3. Config file (`config/default.toml` or specified via `--config`)
4. Built-in defaults

**Important:** `comfyui_root` must be configured before running. No default path is provided.

Configuration file location: `config/default.toml` (already exists in repo, edit as needed)

Example configuration (based on `config-example.toml`):
```toml
comfyui_root = "/path/to/ComfyUI"
workflow_dirs = ["user/default/workflows"]
civitai_api_key = "${CIVITAI_API_KEY}"  # Uses env var
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=comfywatchman --cov-report=html

# Run specific test file
pytest tests/unit/test_config.py

# Run with verbose output and debug logging
pytest -v --log-cli-level=DEBUG
```

Test structure:
- `tests/unit/` - Unit tests for individual modules
- `tests/integration/` - Integration tests for module interactions
- `tests/functional/` - End-to-end functional tests
- `tests/fixtures/` - Shared test fixtures
- `tests/test_data/` - Sample data for testing

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Important Design Patterns

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

When adding support for new node types, update this mapping.

### State Persistence

Downloads are tracked in `state_dir/download_state.json` to prevent:
- Duplicate downloads
- Re-attempting recent failures (configurable via `recent_attempt_hours`)

State structure:
```json
{
  "downloads": {
    "model_filename.safetensors": {
      "status": "success|failed|pending",
      "timestamp": "2025-10-12T14:30:00",
      "url": "https://...",
      "attempts": 1
    }
  }
}
```

### Search Result Caching

Search results are optionally cached in `temp_dir/search_cache/` to reduce API calls.
- Cache key: sanitized filename
- Cache format: JSON serialized `SearchResult` objects

### Logging Strategy

Two log outputs:
1. **Console:** INFO level, user-friendly messages
2. **File:** DEBUG level, structured logs in `log/run_YYYYMMDD_HHMMSS.log`

Use the logging utilities:
```python
from comfyfixersmart.logging import get_logger
logger = get_logger("ModuleName")
logger.info("User message")
logger.debug("Detailed debug info")
```

## Common Tasks

### Adding a New Search Backend

1. Create backend class inheriting from `SearchBackend` in `search.py`
2. Implement `search()` method returning `SearchResult`
3. Implement `get_name()` returning backend identifier
4. Register in `ModelSearch.__init__()` backends dict

### Adding Support for New Model Types

1. Update `model_type_mapping` in `config.py`
2. Add type filter mapping in `CivitaiSearch._get_type_filter()`
3. Update documentation

### Extending CLI Options

1. Add argument in `cli.create_parser()`
2. Update `cli.update_config_from_args()` if it affects config
3. Pass through to `core.run_workflow_analysis()` or compatibility functions

### Creating a New Adapter

1. Create new file in `adapters/` inheriting from `BaseAdapter`
2. Implement required methods: `get_name()`, `is_available()`, `initialize()`, `shutdown()`
3. Add optional dependency group to `pyproject.toml` if needed
4. Register adapter in appropriate module (e.g., `search.py` for search backends)
5. Add integration tests in `tests/integration/`

### Working with the Inspector

The inspector provides safe metadata extraction from model files:

```python
from comfyfixersmart.inspector import inspect_file, inspect_paths

# Single file inspection
result = inspect_file("model.safetensors", do_hash=True)
print(result["file_size"], result["format"], result["sha256"])

# Batch inspection
results = inspect_paths(["models/"], recursive=True, include_components=False)
for path, metadata in results.items():
    print(f"{path}: {metadata['format']}")
```

**Safety notes:**
- Inspector never loads full tensors into memory
- Pickle formats (`.ckpt`, `.pt`, `.pth`) require `--unsafe` flag
- Always verify file sources before using `--unsafe`

## Key Files and Their Purposes

- **pyproject.toml**: Package metadata, dependencies, build configuration, tool settings
- **REQUIREMENTS.md**: Original requirements document (historical reference)
- **INSTALL.md**: Installation and setup guide for users
- **config-example.toml**: Template configuration file
- **legacy/**: Previous implementation versions kept for reference
- **archives/**: Historical tools and research (ScanTool, etc.)
- **docs/**: Comprehensive documentation including planning, reports, research
- **docs/CROSSROADS.md**: **[CRITICAL]** Strategic decision framework for Copilot integration
- **docs/SEARCH_ARCHITECTURE.md**: Complete agentic search architecture (Qwen + Tavily + multi-source)
- **docs/planning/RIGHT_SIZED_PLAN.md**: Core architectural design document
- **docs/planning/AGENT_GUIDE.md**: Guide for AI agents using this tool
- **docs/planning/QWEN_SEARCH_IMPLEMENTATION_PLAN.md**: Original search implementation plan
- **docs/research/**: Research on related systems (ComfyUI-Copilot, etc.)
- **docs/research/ComfyUI-Copilot-Research-Report.md**: Deep analysis of Copilot architecture and integration opportunities
- **docs/research/EXISTING_SYSTEMS.md**: Comprehensive survey of 15+ competing/complementary tools

## Git Repository Structure

**Remotes:**
- **origin**: `https://github.com/Coldaine/ComfyWatchman.git` - Our main repository
- **upstream**: `https://github.com/AIDC-AI/ComfyUI-Copilot.git` - Integration reference (different codebase)

**Important:** When checking PRs or issues:
- Use `gh pr list --repo Coldaine/ComfyWatchman` for OUR project
- PRs from `upstream` are for ComfyUI-Copilot (Node.js/React web UI), not our Python CLI tool
- The two projects have completely different codebases but complementary missions

## Compatibility Modes

### V1 Mode (`--v1`)
- Original incremental processing approach
- Uses Qwen search as optional backend
- Incremental state tracking with immediate processing

### V2 Mode (`--v2`, default)
- Batch processing approach
- Direct Civitai API integration
- Generates download scripts for review before execution

Both modes use the same underlying modules but with different orchestration patterns via `run_v1_compatibility_mode()` and `run_v2_compatibility_mode()` in `core.py`.

## Output Files

All outputs go to `output_dir` (default: `./output/`):
- `missing_models_RUNID.json` - Models not found locally
- `resolutions_RUNID.json` - Search results with download URLs
- `download_missing_RUNID.sh` - Generated download script (if enabled)
- `found_models_cache.json` - Cached local inventory

Logs go to `log_dir` (default: `./log/`):
- `run_RUNID.log` - Main execution log
- `structured.log` - Structured logging output
- `qwen_search_history.log` - Qwen search operation history

State files in `state_dir` (default: `./state/`):
- `download_state.json` - Download tracking and history

## Strategic Direction

**Current Position: Integration & Complement Strategy**

ComfyWatchman is designed to **enhance ComfyUI-Copilot** by providing superior dependency management while maintaining standalone value as a CLI tool.

### The Hybrid Architecture Strategy

**ComfyWatchman Provides:**
- Multi-backend search (Civitai + HuggingFace + Qwen agent)
- Production-grade state management with retry logic
- Offline-first operation for reliability
- CLI automation for CI/CD pipelines
- Advanced model metadata inspection

**ComfyUI-Copilot Provides:**
- Workflow generation from text
- Interactive debugging with streaming UI
- Multi-agent orchestration (Link, Parameter, Structural agents)
- Deep ComfyUI integration
- Browser-based user experience

### Integration Pathways

1. **Adapter Layer** (`adapters/copilot_validator.py`) - Validates Copilot-generated workflows
2. **Optional Backend** (`adapters/sql_state.py`) - Alternative state persistence compatible with Copilot's checkpoint system
3. **Standalone Mode** - CLI tools work independently of Copilot
4. **API Integration** - Python APIs can be called from Copilot's backend

### Key Documents

- **`docs/CROSSROADS.md`** - Complete strategic analysis and decision framework
- **`docs/research/ComfyUI-Copilot-Research-Report.md`** - Deep dive into Copilot architecture
- **`docs/research/EXISTING_SYSTEMS.md`** - Landscape analysis of 15+ related tools
- **`docs/vision.md`** - Long-term vision including LLM integration
- **`docs/architecture.md`** - Proposed architecture for Phase 2 integration

**Owner Directive:** Phase 1 and Phase 2 requirements in Vision and Architecture docs are mandatory and require explicit owner consent to modify.

## Working with Workflow JSON Files

ComfyUI workflow files are JSON with this structure:
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

Model references are in `widgets_values` arrays. The scanner looks for strings ending in model extensions (`.safetensors`, `.ckpt`, `.pt`, `.bin`, `.pth`).

## Package Distribution

Package name: `comfywatchman` (PyPI name differs from project name ComfyFixerSmart for branding)

Entry points:
- `comfywatchman` - Main workflow analysis CLI
- `comfy-inspect` - Model metadata inspector CLI

Current status: Development version 2.0.0, not yet published to PyPI

## Additional Context

- This is a **solo developer project**, not enterprise-level
- Focus on **practical solutions** over complex abstractions
- **Reuse existing patterns** from the codebase rather than introducing new ones
- Video generation workflows (WAN 2.2, etc.) are primary use case but tool is general-purpose
