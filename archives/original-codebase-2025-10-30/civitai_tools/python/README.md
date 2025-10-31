# Civitai Tools - Python Implementation

Complete Python ports of bash tools for Civitai model search and download. Designed for MCP integration and AI agent usage.

## Quick Start

```python
from civitai_tools.python import AdvancedCivitaiSearch, CivitaiDirectDownloader

# Search for models
searcher = AdvancedCivitaiSearch()
results = searcher.search("Better detailed pussy and anus", model_type="LORA")

# Download by ID
downloader = CivitaiDirectDownloader()
result = downloader.download_by_id(1091495)
```

## Modules

### 1. Advanced Search (`advanced_search.py`)
Multi-strategy search with cascading fallbacks and relevance scoring.

**Port of:** `bash/advanced_civitai_search.sh`

### 2. Direct Downloader (`direct_downloader.py`)
Direct model ID downloader with SHA256 hash verification.

**Port of:** `bash/civitai_url_downloader.sh`

### 3. Search Diagnostics (`search_diagnostics.py`)
Diagnostic tool for troubleshooting search failures.

**Port of:** `bash/debug_civitai_search.sh`

### 4. Batch Downloader (`batch_downloader.py`)
Batch model downloader with retry logic.

**Port of:** `bash/batch_civitai_downloader.sh`

### 5. Fuzzy Finder (`fuzzy_finder.py`)
Interactive tool to search and select models.

**Port of:** `bash/fuzzy_civitai_finder.sh`

## CLI Usage

Each module can be run standalone:

```bash
# Advanced search
python -m civitai_tools.python.advanced_search "Better detailed pussy" --type LORA

# Direct download
python -m civitai_tools.python.direct_downloader 1091495 --output-dir ./models

# Search diagnostics
python -m civitai_tools.python.search_diagnostics "problematic search" --export report.json

# Batch download
python -m civitai_tools.python.batch_downloader models.json --max-retries 3

# Fuzzy finder
python -m civitai_tools.python.fuzzy_finder "search term" --type LORA
```

## MCP Integration

These modules are designed for easy MCP server integration:

```python
from mcp.server import Server
from civitai_tools.python import AdvancedCivitaiSearch, CivitaiDirectDownloader

server = Server("civitai-tools")

@server.tool()
async def search_civitai(query: str) -> dict:
    searcher = AdvancedCivitaiSearch()
    return searcher.search(query, "LORA")

@server.tool()
async def download_model(model_id: int) -> dict:
    downloader = CivitaiDirectDownloader()
    result = downloader.download_by_id(model_id)
    return result.to_dict()
```

## Environment Variables

- `CIVITAI_API_KEY` - Civitai API key (loaded from `~/.secrets`)

## See Also

- Full documentation: [FULL_README.md](./FULL_README.md)
- Bash originals: `../bash/`
- Known models database: `../config/known_models.json`