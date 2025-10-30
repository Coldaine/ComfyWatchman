# AI Agent Development and Usage Guide

This guide provides comprehensive instructions for AI agents using ComfyWatchman as **callable Python tools** for ComfyUI workflow management.

---

## 1. Critical Project Context

### 1.1. Project Overview & Philosophy
*   **Name:** `ComfyWatchman` (repository name: `ComfyFixerSmart`, package name: `comfywatchman`)
*   **Purpose:** A **library of Python tools designed for AI agents** to analyze ComfyUI workflows, identify missing models, search across multiple sources, and automatically download dependencies.
*   **Agent-First Design:** Functions return structured data (dataclasses, dicts) for agent decision-making. Not a monolithic CLI for end users.
*   **Development Philosophy:** This is a solo developer project. Favor practical solutions, reuse existing code patterns, and avoid unnecessary enterprise-level abstractions.

### 1.2. Relationship to ComfyUI-Copilot
This project is designed to **complement and integrate with** [ComfyUI-Copilot](https://github.com/AIDC-AI/ComfyUI-Copilot), not compete with it.

*   **ComfyWatchman's Strengths:** Superior dependency resolution, multi-backend search (Civitai, HuggingFace, Qwen), offline-first operation, and a robust CLI for automation.
*   **Copilot's Strengths:** Workflow generation from text, interactive debugging, and deep UI integration.
*   **Integration Strategy:** `ComfyWatchman` provides its powerful dependency management as a standalone tool that can also be integrated into Copilot's workflow via an adapter layer.

### 1.3. Core File Paths & Environment
*   **ComfyUI Root:** The tool operates on a ComfyUI installation located at `/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/`. All model downloads are placed within this directory structure.
*   **API Keys:** The tool requires API keys which are stored in `~/.secrets` and loaded into the environment.
    *   `CIVITAI_API_KEY`: Required for Civitai API search.
    *   `TAVILY_API_KEY`: Required for the Qwen agent's web search fallback.
    *   `HF_TOKEN`: required for accessing private models on HuggingFace.

---

## 2. Guide for Developing on the Codebase

This section is for AI agents contributing to the `ComfyWatchman` source code.

### 2.1. Architecture Overview
The codebase follows a clean, modular architecture with a clear separation of concerns.

*   `src/comfyfixersmart/`:
    *   `cli.py`: Main CLI entry point (`comfywatchman` command).
    *   `core.py`: The `ComfyFixerCore` orchestrator class.
    *   `scanner.py`: Handles workflow parsing and model extraction.
    *   `inventory.py`: Builds the local model inventory.
    *   `search.py`: Manages multi-backend model search (Qwen, Civitai, etc.).
    *   `download.py`: Manages model downloads and script generation.
    *   `state_manager.py`: Handles state tracking and caching.
    *   `inspector/`: The model metadata inspection subsystem.
    *   `adapters/`: The integration layer for external tools like ComfyUI-Copilot.

### 2.2. Development Workflow & Commands
1.  **Installation:**
    ```bash
    # Install in editable mode with all development dependencies
    pip install -e .[dev,full]
    ```
2.  **Code Quality:**
    ```bash
    # Format code
    black src/ tests/

    # Type checking
    mypy src/
    ```
3.  **Testing:**
    ```bash
    # Run all tests
    pytest

    # Run with coverage report
    pytest --cov=comfywatchman --cov-report=html
    ```

### 2.3. Common Development Tasks

*   **Adding a New Search Backend:**
    1.  Create a new class in `search.py` that inherits from `SearchBackend`.
    2.  Implement the `search()` and `get_name()` methods.
    3.  Register the new backend in the `ModelSearch` class.

*   **Adding a New Adapter:**
    1.  Create a new file in `adapters/` inheriting from `BaseAdapter`.
    2.  Implement the required methods (`get_name`, `is_available`, etc.).
    3.  Add an optional dependency group to `pyproject.toml` if needed.

---

## 3. Guide for AI Agents: Calling ComfyWatchman Tools

This section shows how AI agents invoke ComfyWatchman's Python APIs programmatically.

### 3.1. Core Tools Available

**Workflow Scanning:**
```python
from comfyfixersmart.scanner import WorkflowScanner

scanner = WorkflowScanner()
models = scanner.extract_models_from_workflow("/path/to/workflow.json")
# Returns: List[Dict] with filename, type, node_id, etc.
```

**Model Search:**
```python
from comfyfixersmart.search import ModelSearch, SearchResult

search = ModelSearch()
result = search.search_model({"filename": "model.safetensors", "type": "checkpoint"})
# Returns: SearchResult(status="FOUND", civitai_id=123, download_url="...", confidence="exact")
```

**Model Downloads:**
```python
from comfyfixersmart.civitai_tools.direct_downloader import CivitaiDirectDownloader

downloader = CivitaiDirectDownloader(download_dir="/path/to/ComfyUI/models/checkpoints")
result = downloader.download_by_id(
    model_id=123456,
    version_id=789012
)
# Returns: DownloadResult(status=DownloadStatus.SUCCESS, file_path="...", file_size=..., actual_hash="...")
```

**Local Inventory:**
```python
from comfyfixersmart.inventory import ModelInventory

inventory = ModelInventory(models_dir="/path/to/ComfyUI/models")
local_models = inventory.build_inventory()
# Returns: Dict[str, List[str]] - {"checkpoints": [...], "loras": [...]}
```

### 3.2. Decision-Making Pattern for Agents

Agents should use these tools in a workflow:

```python
# 1. Scan workflow to find dependencies
models_needed = scanner.extract_models_from_workflow("workflow.json")

# 2. Check what's already available
local_models = inventory.build_inventory()

# 3. Find what's missing
missing = [m for m in models_needed if m['filename'] not in local_models.get(m['type'], [])]

# 4. Search for each missing model
for model_info in missing:
    search_result = search.search_model(model_info)

    # 5. Agent decides whether to download based on confidence
    if search_result.status == "FOUND" and search_result.confidence == "exact":
        download_result = downloader.download_by_id(
            search_result.civitai_id,
            search_result.version_id
        )

        if download_result.status == DownloadStatus.SUCCESS:
            print(f"✓ Downloaded {model_info['filename']}")
        else:
            print(f"✗ Failed: {download_result.error_message}")
```

### 3.3. Understanding Return Types

All tools return structured data for agent decision-making:

*   **SearchResult:** `status` (FOUND/NOT_FOUND/UNCERTAIN), `civitai_id`, `download_url`, `confidence` (exact/fuzzy)
*   **DownloadResult:** `status` (SUCCESS/FAILED/HASH_MISMATCH), `file_path`, `file_size`, `expected_hash`, `actual_hash`
*   **Model Lists:** List[Dict] with `filename`, `type`, `node_id`, `workflow`

### 3.4. Error Handling for Agents

Agents should handle errors gracefully:

```python
try:
    result = search.search_model(model_info)

    if result.status == "NOT_FOUND":
        # Agent decides: notify user, try alternative search, etc.
        pass
    elif result.status == "UNCERTAIN":
        # Agent reviews candidates and asks user for clarification
        candidates = result.metadata.get("candidates", [])
        pass

except ImportError as e:
    # Missing dependency - notify user to install optional packages
    pass
except Exception as e:
    # Unexpected error - log and continue with other models
    pass
```
