# Civitai Advanced Search Tools

This directory contains tools for advanced Civitai model search and download functionality, specifically designed to handle cases where standard API search fails for NSFW content.

## Background

Standard Civitai API search has limitations when searching for NSFW content with explicit anatomical terms due to filtering mechanisms. This toolset provides multiple strategies to reliably find and download these models.

## Directory Structure

```
civitai_tools/
├── python/          # Python modules for programmatic use
│   ├── __init__.py
│   ├── enhanced_search.py      # Enhanced CivitaiSearch backend
│   ├── direct_id_backend.py    # Direct ID lookup backend
│   └── search_debugger.py      # Diagnostic tool
├── bash/            # Standalone CLI scripts
│   ├── civitai_url_downloader.sh      # Direct ID and URL-based downloader
│   ├── advanced_civitai_search.sh     # Multi-strategy search
│   ├── fuzzy_civitai_finder.sh        # Interactive finder
│   ├── batch_civitai_downloader.sh    # Batch operations
│   └── debug_civitai_search.sh        # Raw API debugging
└── config/          # Configuration files
    └── known_models.json      # Model ID mappings for problematic searches
```

## Key Features

### 1. Direct ID Lookup
Bypasses search API entirely by using known model IDs to fetch model details directly from Civitai's API.

### 2. Multi-Strategy Search
Implements cascading fallbacks:
- Known models mapping
- Query search (with/without NSFW parameter)
- Tag-based search
- Creator-based search

### 3. Advanced Algorithms
- Scoring system for result ranking
- Keyword decomposition
- Tag extraction from search terms
- SHA256 verification for downloads

### 4. Diagnostic Tools
- API query debugging
- Response analysis
- Problem identification
- Suggestion generation

## Usage

### Bash Scripts

```bash
# Direct download by model ID or URL
./civitai_tools/bash/civitai_url_downloader.sh 1091495

# Advanced multi-strategy search
./civitai_tools/bash/advanced_civitai_search.sh "Better detailed pussy and anus"

# Interactive finder for ambiguous searches
./civitai_tools/bash/fuzzy_civitai_finder.sh "Eyes High Definition"

# Batch download multiple models
./civitai_tools/bash/batch_civitai_downloader.sh models_list.txt

# Debug search failures
./civitai_tools/bash/debug_civitai_search.sh "problematic search term"
```

### Python Modules

```python
from comfyfixersmart.civitai_tools.python.direct_id_backend import DirectIDBackend
from comfyfixersmart.civitai_tools.python.enhanced_search import EnhancedCivitaiSearch

# Direct ID lookup
backend = DirectIDBackend()
result = backend.lookup_by_id(1091495)

# Enhanced search with multiple strategies
search = EnhancedCivitaiSearch()
results = search.search_multi_strategy(model_ref)
```

## Configuration

The `known_models.json` file contains mappings for models that fail API search:

```json
{
  "better detailed pussy and anus": {
    "model_id": 1091495,
    "model_name": "Better detailed pussy and anus",
    "type": "LORA",
    "url": "https://civitai.com/models/1091495",
    "notes": "Search API fails due to explicit term filtering"
  }
}
```

## Troubleshooting

For detailed troubleshooting guidance, see [CIVITAI_SEARCH_FIXES.md](../docs/CIVITAI_SEARCH_FIXES.md).

## Integration

These tools integrate with the main ComfyFixerSmart system through:
- Enhanced CivitaiSearch class in `src/comfyfixersmart/search.py`
- Configuration settings in `config.py`
- State management through existing systems
- Logging and error handling infrastructure