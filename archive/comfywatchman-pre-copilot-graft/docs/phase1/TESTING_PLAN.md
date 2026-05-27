# Phase 1 Testing Plan

## Overview
This document outlines the testing strategy for the Phase 1 implementation of the Workflow Readiness Automation system.

## 1. Unit Tests

**Framework:** `pytest`

**Objective:** To test each component (LangGraph node function) in isolation.

| Component | Test Scenarios | Mock Data / Fixtures |
|---|---|---|
| **System Health Checker** | - VRAM is sufficient and ComfyUI is running<br>- VRAM is insufficient<br>- ComfyUI is not running<br>- Handles errors from `psutil` or VRAM detection | - Mock `psutil` to simulate running/not running processes<br>- Mock VRAM detection library to return different values |
| **Workflow Scanner** | - Scans a directory with valid workflow JSON files<br>- Handles empty directories<br>- Handles files that are not valid JSON<br>- Correctly extracts model and custom node dependencies | - A `tests/fixtures/workflows` directory with sample workflow files (valid, invalid, empty) |
| **Model Inventory Builder** | - Scans a directory with a standard ComfyUI model structure<br>- Correctly categorizes models (checkpoints, loras, etc.)<br>- Handles empty model directories | - A `tests/fixtures/comfyui_root` directory with a mock model structure |
| **Custom Node Inventory** | - Scans a directory with custom nodes<br>- Handles nested custom node directories | - A `tests/fixtures/comfyui_root/custom_nodes` directory with mock custom nodes |
| **Dependency Resolver** | - All dependencies are present<br>- Some models are missing<br>- Some custom nodes are missing<br>- Both models and custom nodes are missing | - `workflow_statuses` and `missing_dependencies` state from previous nodes |
| **Report Generator** | - Generates Markdown and JSON reports correctly<br>- Handles cases with no missing dependencies<br>- Uses Jinja2 templates correctly | - Sample `workflow_statuses` and `missing_dependencies` data |
| **Dashboard Generator** | - Generates a valid HTML file<br>- Correctly embeds the JSON data | - Sample `index.json` data |

## 2. Integration Tests

**Framework:** `pytest` with LangGraph's testing utilities.

**Objective:** To test the full LangGraph workflow from start to finish.

**Scenarios:**

1.  **"Happy Path" Scenario:**
    *   **Setup:** Mock system health check to return `True`. Provide a set of mock workflows and a mock ComfyUI root directory where all dependencies are present.
    *   **Expected Outcome:** The graph runs to completion, all workflows are marked as "Runnable", and the generated reports and dashboard reflect this.

2.  **"Missing Dependencies" Scenario:**
    *   **Setup:** Mock system health check to return `True`. Provide mock workflows with some dependencies that are *not* present in the mock ComfyUI root.
    *   **Expected Outcome:** The graph runs to completion, the correct workflows are marked as "Missing Dependencies", and the reports and dashboard correctly list the missing items.

3.  **"System Not Ready" Scenario:**
    *   **Setup:** Mock system health check to return `False` (e.g., `vram_available: False`).
    *   **Expected Outcome:** The graph enters at `check_system` and then immediately exits through the conditional edge to `END`. No other nodes are executed.

## 3. System Tests

**Objective:** To test the system in a real-world environment.

**Setup:**

*   A dedicated, isolated ComfyUI installation.
*   A collection of real-world workflows, some with known missing dependencies.
*   The `comfywatchman` tool installed in a virtual environment.

**Test Cases:**

1.  **Manual Trigger:** Run the health check manually from the CLI (`comfywatchman --run-check`).
2.  **Scheduler Trigger (Manual):** Manually trigger the systemd service (`systemctl --user start comfywatchman.service`) and verify the outcome.
3.  **End-to-End Verification:**
    *   Check the generated reports in `output/reports/workflows/`.
    *   Open the `output/dashboard/index.html` file in a browser and verify its contents and interactivity.
    *   Check the state files in `state/` to ensure they are being created and updated correctly.

## 4. Performance Tests

**Objective:** To measure the performance of the system with a large number of workflows.

**Setup:**

*   A directory with 50+ workflow files.
*   A ComfyUI installation with a large number of models.

**Metrics to Measure:**

*   **Total execution time:** The time it takes for the entire LangGraph workflow to complete.
*   **Time per node:** Use logging to measure the time spent in each node of the graph.
*   **Memory usage:** Monitor the memory usage of the Python process during execution.

**Goal:** Ensure that the system can complete a full scan in a reasonable amount of time (e.g., under 5 minutes for 50 workflows) without consuming excessive resources.
