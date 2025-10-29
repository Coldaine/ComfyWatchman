# AI Agent Development and Usage Guide

This guide provides comprehensive instructions for AI agents, covering both development on the `ComfyWatchman` codebase and autonomous use of its command-line tools.

---

## 1. Critical Project Context

### 1.1. Project Overview & Philosophy
*   **Name:** `ComfyWatchman` (repository name: `ComfyFixerSmart`, package name: `comfywatchman`)
*   **Purpose:** An intelligent Python tool that analyzes ComfyUI workflows, identifies missing models and custom nodes, searches for them on Civitai and HuggingFace, and automates the download process.
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
    *   `HF_TOKEN`: Optional for accessing private models on HuggingFace.

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

    # Lint code
    flake8 src/ tests/

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

## 3. Guide for Using the Tool Autonomously

This section is for AI agents using the compiled `comfywatchman` tool to manage workflows.

### 3.1. Basic Usage
```bash
# Run the full analysis and download pipeline automatically
comfywatchman --auto

# Monitor the progress of a run
comfywatchman --status

# Resume an interrupted run
comfywatchman --resume
```

### 3.2. Monitoring a Run
The tool's status is written to `status.json`. Agents should monitor this file to track progress.

*   **Status Phases:** `idle`, `scanning`, `resolving`, `downloading`, `complete`, `error`.
*   **Example Monitoring Logic:**
    ```python
    import json
    import time

    while True:
        try:
            with open('status.json') as f:
                status = json.load(f)
            
            phase = status.get('phase', 'idle')
            print(f"Current phase: {phase}")

            if phase in ['complete', 'error']:
                break
        except FileNotFoundError:
            print("Waiting for run to start...")
        
        time.sleep(5)
    ```

### 3.3. Understanding the Output
All outputs are placed in the `output/` directory.

*   `missing_models.json`: A list of models that were not found locally.
*   `resolutions.json`: The search results from Civitai/HuggingFace for the missing models.
*   `summary_report.md`: A human-readable summary of the run.

### 3.4. Error Handling and Recovery
*   If `status.json` shows `phase: "error"`, check the `errors` array for details.
*   Consult the log files in the `log/` directory for detailed stack traces.
*   For most transient errors (network issues, timeouts), a run can be recovered by executing `comfywatchman --resume`.
*   If an API key is invalid (`401 Unauthorized`), the agent should notify the user to check their `~/.secrets` file.
