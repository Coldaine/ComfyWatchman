# ComfyWatchman

Python library of agent-callable tools for analyzing ComfyUI workflows, resolving missing models, and downloading dependencies from Civitai and HuggingFace.

> The internal repository name is `ComfyFixerSmart`; the installable package and CLI entry point are `comfywatchman`.

## What It Does

ComfyWatchman is a library, not a polished end-user CLI. Functions return structured dataclasses/dicts so AI agents (Claude, ChatGPT, custom orchestrators) can drive the workflow:

1. Parse a ComfyUI workflow JSON and list the models it references.
2. Search for missing models across Civitai, HuggingFace, and an optional Qwen agentic search backend.
3. Download resolved models with SHA256 verification.
4. Track local inventory and persistent download state.

There is also a `comfywatchman` CLI entry point (`src/comfywatchman/cli.py`) for ad-hoc use.

## Repository Layout

```
src/comfywatchman/        Python package
  cli.py                  CLI entry point (script: `comfywatchman`)
  core.py                 ComfyFixerCore orchestrator
  scanner.py              Workflow parsing / model extraction
  search.py               Multi-backend search
  download.py             Download manager
  inventory.py            Local model inventory
  scheduler.py            Optional background scheduler
  state_manager.py        Persistent download/search state
  config.py               TOML/env-based configuration
  dashboard.py            Optional dashboard
  civitai_tools/          Civitai search/download adapters
    advanced_search.py
    batch_downloader.py
    direct_downloader.py
    direct_id_backend.py
    enhanced_search.py
    fuzzy_finder.py
  adapters/               Integration adapters
  inspector/              Workflow inspector helpers
  knowledge/              Knowledge base modules
src/copilot_backend/      ComfyUI-Copilot integration backend (scaffold)
scripts/                  Maintenance scripts
docs/
  phase0/ phase1/ phase2/ phase3/   Phased design docs
  research/                          Prior-art surveys
  strategy/vision.md                 Vision doc
tests/                    pytest suite (top-level test_*.py also present)
```

## Requirements

- Python 3.12 or 3.13 (see `pyproject.toml`)
- A ComfyUI installation (path provided via config or `COMFYUI_ROOT`)
- Civitai API key for Civitai search/downloads (free account)
- Optional: HuggingFace token for private models; Qwen CLI for agentic web search

## Install

The repo currently ships as a source install. There is no published PyPI release yet despite the badge having been used historically.

```bash
# Clone
git clone https://github.com/Coldaine/ComfyFixerSmart.git
cd ComfyFixerSmart

# Install with uv (recommended)
uv sync
# or with extras for development
uv sync --extra dev
```

After install the `comfywatchman` console script is available.

## Configuration

Copy `config-example.toml` to `config.toml` (or use environment variables). Common keys:

```bash
export CIVITAI_API_KEY="..."
export COMFYUI_ROOT="/path/to/ComfyUI"
export HF_TOKEN="..."   # optional
```

Relevant TOML sections include `[search]` (backend order across `civitai`, `huggingface`, `qwen`), workflow scan directories, output/log dirs, and cache TTLs. See `config-example.toml` for the full surface.

## Library Usage

```python
from comfywatchman.scanner import WorkflowScanner
from comfywatchman.search import ModelSearch
from comfywatchman.civitai_tools.direct_downloader import CivitaiDirectDownloader

scanner = WorkflowScanner()
models = scanner.extract_models_from_workflow("workflow.json")

search = ModelSearch()
result = search.search_model({"filename": "rife49.pth"})

if result.status == "FOUND" and result.source == "civitai":
    CivitaiDirectDownloader().download_by_id(result.civitai_id, result.version_id)
```

The CLI mirrors the same core flows; run `comfywatchman --help` after install for current commands.

## Search Backends

- **Civitai** — direct ID lookup, advanced/enhanced search, fuzzy matcher, batch downloader.
- **HuggingFace** — used both as a primary backend for repo-hosted assets (e.g. `rife*.pth`, `sam_*.pth`) and as a verification step after Qwen suggestions.
- **Qwen agentic search** (optional) — when configured, uses Qwen's web-search tool to find repos/files when Civitai has no exact match, then verifies file existence before download.
- **DirectID backend** — local lookup table for known-good Civitai IDs.

Filename validation rejects URL parameters and malformed inputs early so failed lookups do not waste API calls.

## Testing

```bash
uv run pytest tests/
# or run a single legacy script
uv run pytest test_civitai_advanced_search.py
```

The repo also has several top-level demo/test scripts (`demonstrate_civitai_advanced_search.py`, `test_filename_validation.py`, etc.) that pre-date the consolidated `tests/` layout.

## Documentation

Active documentation lives under `docs/`:

- `docs/strategy/vision.md` — long-term vision and owner directives
- `docs/phase0/` through `docs/phase3/` — phased design and integration plans (architecture decisions, dashboard, scheduler, agentic search, knowledge base)
- `docs/research/EXISTING_SYSTEMS.md` — prior-art survey (ComfyUI-Copilot, ComfyScript, ComfyGPT, etc.)
- `docs/research/LANGGRAPH_RESEARCH.md` — research notes
- `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `QWEN.md` — AI-agent instructions per tool

Several historical planning files (e.g. `INTEGRATION_PLAN.md`, `HF_PATTERN_RECOGNITION_IMPLEMENTATION.md`, `workflow_analysis_report.md`) remain at the repo root; treat them as point-in-time artifacts, not current state.

## Owner Directive

Principles documented in `docs/strategy/vision.md` are owner-locked and must not be altered without explicit approval.

## License

MIT — see `LICENSE`.
