# ComfyWatchman

**Agent-Callable Tools for ComfyUI Workflow Analysis & Model Resolution**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

ComfyWatchman provides Python APIs designed for AI agents to analyze ComfyUI workflows, identify missing models, search Civitai and Qwen-mediated HuggingFace evidence, and automatically download dependencies.

**Built for AI Agents** - Not primarily an end-user CLI. Functions return structured data (dataclasses, dicts) so AI agents can make decisions about what to scan, search, or download.

**Complements [ComfyUI-Copilot](https://github.com/AIDC-AI/ComfyUI-Copilot)** - Copilot handles workflow generation and interactive debugging; ComfyWatchman provides dependency resolution and multi-backend search as callable tools.

## Current State

Package `comfywatchman` v3.0.0 (Python 3.12+). Core workflow is implemented end-to-end:

- Workflow scanning and model extraction - implemented (`scanner.py`)
- Local model inventory - implemented (`inventory.py`)
- Multi-backend search orchestration - implemented (`search.py`, `civitai_tools/`)
- Automatic download with SHA256 verification - implemented (`download.py`)
- Background scheduler with GPU VRAM guard - implemented (`scheduler.py`)
- Static HTML dashboard generation - implemented (`dashboard.py`)
- React/Vite dashboard prototype - implemented (`frontend/comfywatchman-dashboard/`)
- Model file inspector (`comfywatchman inspect`) - implemented (`inspector/`)
- Adapters for ComfyUI-Copilot integration - implemented (`adapters/`)

## Installation

```bash
git clone https://github.com/Coldaine/ComfyWatchman.git
cd ComfyWatchman

# Install in editable mode
pip install -e .

# With development dependencies
pip install -e ".[dev]"
```

## Configuration

Set environment variables or use a `config.toml` (see `config-example.toml`):

```bash
export CIVITAI_API_KEY="your-api-key"          # Required for Civitai search
export COMFYUI_ROOT="/path/to/comfyui"          # ComfyUI installation root
export HF_TOKEN="your-huggingface-token"        # Optional, for private HF models
```

## CLI Usage

```bash
# Analyze all workflows in configured directories (default: v2 batch mode)
comfywatchman

# Analyze a specific workflow file
comfywatchman workflow.json

# Analyze workflows in a specific directory
comfywatchman --dir /path/to/workflows

# Use specific search backends (default is qwen,civitai)
comfywatchman --search qwen,civitai

# Inspect a model file's metadata (no tensor loading)
comfywatchman inspect model.safetensors
comfywatchman inspect /path/to/models --recursive --format json

# Run as continuous background scheduler (checks every 120 min by default)
comfywatchman --scheduler --scheduler-interval 60
```

## Agent Usage (Python API)

```python
from comfywatchman.scanner import WorkflowScanner
from comfywatchman.search import ModelSearch
from comfywatchman.inventory import ModelInventory
from comfywatchman.civitai_tools.direct_downloader import CivitaiDirectDownloader

# 1. Scan a workflow for model dependencies
scanner = WorkflowScanner()
models = scanner.extract_models_from_workflow("workflow.json")
# Returns: List[ModelReference] with filename, type, node_type, workflow

# 2. Build local inventory
inventory = ModelInventory()
local_models = inventory.build_inventory()

# 3. Search for a missing model
search = ModelSearch()
result = search.search_model({"filename": "model.safetensors", "type": "checkpoint"})
# Returns: SearchResult(status="FOUND"|"NOT_FOUND"|"UNCERTAIN", civitai_id, download_url, confidence)

# 4. Download if found
if result.status == "FOUND" and result.source == "civitai":
    downloader = CivitaiDirectDownloader()
    download_result = downloader.download_by_id(result.civitai_id, result.version_id)
    # Returns: DownloadResult(status=SUCCESS|FAILED|HASH_MISMATCH, file_path, actual_hash)
```

### Full Orchestrated Run

```python
from comfywatchman.core import ComfyFixerCore

core = ComfyFixerCore()
run = core.run_workflow_analysis()
# Scans workflows, finds missing models, searches, and auto-downloads
# Returns: WorkflowRun(status, workflows_scanned, models_found, models_missing, models_resolved)
```

## Architecture

```text
src/comfywatchman/
|-- cli.py                   # CLI entry point (comfywatchman command)
|-- core.py                  # ComfyFixerCore orchestrator
|-- scanner.py               # Workflow JSON parsing, model extraction
|-- inventory.py             # Local model inventory builder
|-- search.py                # Multi-backend search coordination
|-- download.py              # Automatic download with hash verification
|-- scheduler.py             # Background scheduler with VRAM guard
|-- state_manager.py         # State tracking and download caching
|-- dashboard.py             # Static HTML dashboard generation
|-- config.py                # TOML + env-based configuration
|-- inspector/               # Model file metadata inspection
|-- civitai_tools/           # Civitai-specific search and download tools
`-- adapters/                # Integration adapters (ComfyUI-Copilot, etc.)
```

## Search Backends

| Backend | Description |
|---------|-------------|
| `qwen` | Default first-pass agentic routing, pattern recognition, and web/HuggingFace evidence gathering |
| `civitai` | Default fallback direct Civitai API search with DirectID support |
| `huggingface` | Verification-oriented backend; direct discovery is currently handled through Qwen |

Pattern recognition routes by filename:
- `rife*.pth`, `sam_*.pth` -> likely HuggingFace-hosted
- `*.safetensors` -> Civitai primary
- `*.pt` -> context-aware routing

## Requirements

- Python 3.12+
- Civitai API key (free account) - required for Civitai search
- ComfyUI installation

Optional:
- HuggingFace token - for private HF models
- Qwen CLI - for agentic web search fallback

## License

MIT License - see [LICENSE](LICENSE).
