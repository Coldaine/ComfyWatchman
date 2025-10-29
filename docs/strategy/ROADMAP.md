# ComfyFixerSmart Project Roadmap

**Document Version**: 2.0
**Status**: Final
**Date**: 2025-10-29

---

## 1. Executive Summary & Current State

ComfyFixerSmart is an intelligent Python tool that analyzes ComfyUI workflows, identifies missing models, and automates the download process. The project is approximately 70% complete with its foundational phase, possessing a stable core architecture, functional analysis modules, and a multi-backend search system.

However, a review has identified several critical gaps that impact user experience and block future enhancements:
*   **Missing Embedding Support:** The tool does not handle textual inversion embeddings, a common cause of workflow failures.
*   **Unreliable Search:** The AI-driven search (Qwen) has an accuracy below 70%.
*   **Lack of Automation:** The workflow is not yet fully automated with a scheduler or a seamless incremental download process.

This document outlines a prioritized roadmap to address these gaps, stabilize the foundation, and pave the way for future intelligence layers.

---

## 2. Strategic Roadmap & Phased Rollout

The project will be executed in three main phases, ensuring that each phase builds upon a stable and valuable foundation.

### Phase 1: Foundation Completion
**Focus:** Stabilize core functionality and address immediate user pain points.
*   **Initiative 1: Embedding Support:** Add detection, search, and download for textual inversion embeddings.
*   **Initiative 2: Qwen Search Refinement:** Improve prompt engineering and error handling to increase search accuracy to >80%.
*   **Initiative 3: Core Automation:** Implement the scheduler, status dashboard, and cache refresh system.
*   **Initiative 4: Incremental Workflow:** Rework the download process to be one-model-at-a-time for better feedback and reliability.

### Phase 2: Integration Layer
**Focus:** Extend capabilities through controlled, optional integrations with external tools like ComfyUI-Copilot.
*   **Initiative 5: Adapter Framework:** Build a plugin architecture to cleanly integrate external tools.
*   **Initiative 6: Copilot Integration:** Add adapters for Copilot's validation and ModelScope search.
*   **Initiative 7: Automated Download Service:** Evolve the downloader into a true "fire-and-forget" background service with a persistent job queue.

### Phase 3: Intelligence Layer
**Focus:** Implement advanced AI-powered features for workflow optimization and generation.
*   **Initiative 8: Knowledge-Guided Resolution:** Build a curated knowledge base to guide the AI.
*   **Initiative 9: LLM + RAG Vision:** Begin research and prototyping for advanced features like Retrieval-Augmented Generation for workflow creation.

---

## 3. Detailed Implementation Plan

This plan details the execution of Phase 1, which is the immediate priority.

### 3.1. Priority 1: Embedding Support (DP-017)
*   **Goal:** Add full support for detecting and downloading missing textual inversion embeddings.
*   **Implementation Steps:**
    1.  **Detection:** Update `scanner.py` to recognize `embedding:name` syntax in workflow JSON.
    2.  **Configuration:** Add `embeddings` to the model type mapping in `config.py`.
    3.  **Search:** Extend the `CivitaiSearch` class in `search.py` to filter by the `TextualInversion` type.
    4.  **Download:** Update `download.py` to place embedding files (`.pt`, `.safetensors`) in the correct `models/embeddings/` directory.
    5.  **Testing & Documentation:** Add unit tests and update the user guide.
*   **Acceptance Criteria:** The tool correctly identifies, finds, and downloads missing embeddings, allowing previously failing workflows to load.

### 3.2. Priority 2: Qwen Search Refinement
*   **Goal:** Increase search accuracy and reliability to over 80%.
*   **Implementation Steps:**
    1.  **Prompt Engineering:** Refine the prompt templates in `docs/planning/QWEN_PROMPT.md` to be more precise.
    2.  **Error Handling:** Implement robust error handling and retry mechanisms for the LLM API calls in `search.py`.
    3.  **Fallback Logic:** Create a fallback to direct, non-AI Civitai search if the Qwen agent fails.
    4.  **Performance:** Implement search result caching to reduce redundant API calls and add structured logging for easier debugging.
*   **Acceptance Criteria:** A/B testing shows a significant improvement in search accuracy, and the system gracefully handles LLM failures.

### 3.3. Priority 3: Core Automation (Scheduler & Reporting)
*   **Goal:** Implement the foundational components for automated, scheduled workflow analysis.
*   **Implementation Steps:**
    1.  **Scheduler:** Create `scheduler.py` to run analysis on a configurable interval, with guards for resource usage (e.g., minimum VRAM).
    2.  **Status Reporting:** Implement a master status report generator that creates JSON and Markdown summaries in the `output/` directory.
    3.  **Cache Management:** Implement an intelligent cache refresh system that updates the local model inventory on each run.
*   **Acceptance Criteria:** The scheduler runs reliably, and the status reports accurately reflect the health of the workflow library.

### 3.4. Priority 4: Incremental Workflow
*   **Goal:** Rework the batch-oriented download process into a more responsive, one-model-at-a-time workflow.
*   **Implementation Steps:**
    1.  **Sequential Processing:** Modify `core.py` to process one missing model at a time (search -> download -> verify).
    2.  **Real-time Feedback:** Add progress tracking and live updates to the CLI and status files.
    3.  **Individual Scripts:** Enhance `download.py` to generate per-model download scripts for easier debugging.
    4.  **Verification:** Add an automated verification step that checks file integrity after every few downloads.
*   **Acceptance Criteria:** The user sees real-time progress, downloads start immediately, and the system is more resilient to individual model failures.

---

## 4. Leveraging the Existing Dashboard

The project includes a pre-existing React-based dashboard in `src/copilot_backend/`, which provides a significant head start on UI development (estimated 40% time savings).

*   **Integration Strategy:** Instead of building a new UI from scratch, we will extend the existing dashboard.
*   **Extension Points:**
    *   Add new pages and components for `ComfyFixerSmart`-specific features (e.g., scheduler status, download queue).
    *   Extend the existing API to serve data from our backend.
    *   Utilize the existing styling and component library for a consistent look and feel.

This approach allows for rapid prototyping and provides a rich user interface for the features developed in this roadmap.
