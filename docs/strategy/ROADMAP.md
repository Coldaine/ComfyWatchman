# ComfyFixerSmart Project Roadmap

**Document Version**: 3.0
**Status**: Active Development
**Date**: 2025-10-29
**Last Updated**: 2025-10-29

---

## 0. Current Implementation Status

### **🚀 ACTIVE: Phase 1A - Civitai Advanced Search (Weeks 1-2)**
**Status**: Planning → Implementation (Commit 2 starting)
**Branch**: `feature/civitai-advanced-search`
**Doc**: [`docs/implementation/implementation1029.md`](../implementation/implementation1029.md)

**Critical Context:**
Research identified that Civitai API's `nsfw=true` parameter doesn't map to all browsing levels (R=4, X=8, XXX=16), and query searches filter explicit anatomical terms. This blocks 67% of NSFW model searches. Phase 1A fixes this foundational issue before all other work.

**Why This Is Priority #1:**
- **Blocks Everything Else:** Can't download what you can't find
- **High Impact:** Improves search success from 33% → 100% for NSFW models
- **Infrastructure Foundation:** Qwen refinement (Phase 1B) depends on this working
- **Real User Pain:** Fixing actual broken searches from user's 12-model request

**Key Deliverables:**
- ✅ Commit 1: Implementation plan (DONE)
- 🔄 Commit 2-11: Direct ID downloader, multi-strategy search, `known_models.json`, enhanced Python backend, debug tools

---

### **⏳ NEXT: Phase 1B - Qwen Integration & Refinement (Weeks 3-4)**
**Status**: Planned (starts after 1A)
**Doc**: This roadmap (Section 3.2) + [`docs/planning/QWEN_PROMPT.md`](../planning/QWEN_PROMPT.md)

**Critical Integration:**
Qwen will USE the Phase 1A infrastructure:
```python
# Orchestration strategy (src/comfyfixersmart/core.py)
1. Check known_models.json (Phase 1A) → instant success
2. Try multi-strategy Civitai search (Phase 1A) → 90%+ success without LLM
3. If still fails → Qwen fallback (Phase 1B) using improved backends
4. Qwen can call search_by_id() if it discovers model IDs
```

This reduces Qwen's workload by 90%, allowing it to focus on truly hard cases.

---

### **✅ COMPLETED: LMStudio Integration (ComfyUI-Copilot Backend)**
**Status**: Implementation complete
**Doc**: [`src/copilot_backend/LMSTUDIO_IMPLEMENTATION.md`](../../src/copilot_backend/LMSTUDIO_IMPLEMENTATION.md)

Enables local LLM support in Copilot backend (alternative to OpenAI API).

---

### **📋 UPCOMING: MCP Server Implementation (Weeks 9-14)**
**Status**: Planning complete, waiting for Phase 1-2 completion
**Doc**: [`docs/mcp/implementationPlan.md`](../mcp/implementationPlan.md)

3-phase rollout to integrate ComfyWatchman with Claude Desktop via Model Context Protocol. Requires stable search infrastructure from Phase 1.

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

The project will be executed in four main phases, ensuring that each phase builds upon a stable and valuable foundation. **The order is critical**: search infrastructure must work before AI refinement, and both must work before integration layers.

### Phase 1: Search Infrastructure (Weeks 1-4) - FOUNDATION
**Focus:** Fix critical search API limitations and build multi-strategy infrastructure.

#### **Phase 1A: Civitai Advanced Search** ⭐ *[CURRENT PRIORITY]*
*   **Timeline:** Weeks 1-2
*   **Doc:** [`docs/implementation/implementation1029.md`](../implementation/implementation1029.md)
*   **Why First:** Fixes blocking API bugs; prerequisite for all downstream improvements
*   **Deliverables:**
    - Direct ID downloader bypassing search API
    - Multi-strategy search (query → tag → creator → direct ID cascade)
    - `known_models.json` mapping for problematic models
    - Enhanced `CivitaiSearch` Python class with `search_by_id()`, `search_multi_strategy()`
    - Debug tools for API diagnostics

#### **Phase 1B: Qwen Integration & Refinement**
*   **Timeline:** Weeks 3-4
*   **Why After 1A:** Integrates with improved Civitai backends; reduces LLM workload by 90%
*   **Deliverables:**
    - Refined prompt engineering leveraging Phase 1A capabilities
    - Integration: Qwen uses `known_models.json`, `search_multi_strategy()`, `search_by_id()`
    - Robust error handling + retry logic
    - Search result caching
    - Target: >80% accuracy (up from <70%)

---

### Phase 2: Core Completeness (Weeks 5-8) - STABILITY
**Focus:** Add missing core features now that search is reliable.

*   **Initiative 1: Embedding Support (DP-017)** *(Week 5)*
    - Add detection, search, and download for textual inversion embeddings
    - Uses the now-improved search backends

*   **Initiative 2: Incremental Workflow** *(Weeks 6-7)*
    - Rework batch download to one-model-at-a-time with real-time feedback
    - Per-model scripts and verification

*   **Initiative 3: Core Automation** *(Week 8)*
    - Scheduler with configurable intervals
    - Status dashboard (JSON/Markdown reports)
    - Intelligent cache refresh system

---

### Phase 3: Integration Layer (Weeks 9-14) - EXPANSION
**Focus:** Extend capabilities through MCP server and external tool integration.

*   **Initiative 4: MCP Server - Phase 1 (Foundation)** *(Weeks 9-10)*
    - Wrap existing tools as Claude Desktop endpoints
    - Analysis, search, and inspection tools
    - Doc: [`docs/mcp/implementationPlan.md`](../mcp/implementationPlan.md)

*   **Initiative 5: MCP Server - Phase 2 (Workflow Generation)** *(Weeks 11-12)*
    - Node database, connection validator
    - 5+ workflow templates, workflow builder

*   **Initiative 6: MCP Server - Phase 3 (Advanced Features)** *(Weeks 13-14)*
    - Model compatibility matrix
    - Workflow repair tool, optimization strategies
    - Natural language → workflow generation

*   **Initiative 7: Copilot Integration** *(Post-MCP)*
    - Adapter framework for external tools
    - Copilot validation and ModelScope adapters
    - Automated download service (background job queue)

---

### Phase 4: Intelligence Layer (Week 15+) - FUTURE
**Focus:** Implement advanced AI-powered features for workflow optimization.

*   **Initiative 8: Knowledge-Guided Resolution**
    - Build curated knowledge base (seed: `known_models.json` from Phase 1A)
    - Hardware-aware recommendations

*   **Initiative 9: LLM + RAG Vision**
    - Retrieval-Augmented Generation for workflow creation
    - Advanced optimization strategies

---

## 3. Detailed Implementation Plan

This plan details the execution of Phase 1 and Phase 2, which are the immediate priorities.

### 3.0. Phase 1A: Civitai Advanced Search (CURRENT - Weeks 1-2)

**Comprehensive Plan:** See [`docs/implementation/implementation1029.md`](../implementation/implementation1029.md) for full 11-commit implementation plan.

*   **Goal:** Fix Civitai API search limitations that block 67% of NSFW model searches.

*   **Root Causes Identified:**
    1.  `nsfw=true` parameter doesn't map to all browsing levels (R=4, X=8, XXX=16)
    2.  Query parameter filters explicit anatomical terms even with API key
    3.  Web UI finds models that API search cannot

*   **Solution Architecture:**
    ```
    ┌─────────────────────────────────────┐
    │ Model Search Request                │
    └─────────────┬───────────────────────┘
                  ↓
    ┌─────────────────────────────────────┐
    │ 1. Check known_models.json          │ ← Phase 1A: Direct ID database
    │    (instant success for known cases)│
    └─────────────┬───────────────────────┘
                  ↓ (if not found)
    ┌─────────────────────────────────────┐
    │ 2. Multi-strategy Civitai search    │ ← Phase 1A: New infrastructure
    │    - Query search (nsfw variants)   │
    │    - Tag-based search               │
    │    - Creator-based search           │
    │    - Direct ID lookup (if ID known) │
    └─────────────┬───────────────────────┘
                  ↓ (if confidence < 50%)
    ┌─────────────────────────────────────┐
    │ 3. Qwen agent fallback              │ ← Phase 1B: Uses new backends
    │    - Can call search_by_id()        │
    │    - Can use debug tools            │
    └─────────────────────────────────────┘
    ```

*   **Key Implementation Files:**
    - `civitai_tools/bash/civitai_url_downloader.sh` - Direct ID downloader (Commit 3)
    - `civitai_tools/config/known_models.json` - Model ID mappings (Commit 5)
    - `src/comfyfixersmart/search.py` - Enhanced `CivitaiSearch` class (Commit 4)
    - `civitai_tools/bash/debug_civitai_search.sh` - Diagnostic tool (Commit 6)

*   **Acceptance Criteria:**
    - Can download Model 1091495 ("Better detailed pussy and anus v3.0") via direct ID
    - Can download Model 670378 ("Eyes High Definition V1") via direct ID
    - All 12 models from original request: 100% success rate (up from 33%)
    - Multi-strategy search resolves 90%+ queries without LLM calls

---

### 3.1. Phase 1B: Qwen Integration & Refinement (Weeks 3-4)

*   **Goal:** Increase Qwen search accuracy to >80% by integrating with Phase 1A infrastructure.

*   **Critical Integration Strategy:**
    Qwen becomes a **smart fallback** rather than a primary search mechanism:

    ```python
    # src/comfyfixersmart/core.py orchestration
    def resolve_model(self, model_ref):
        # Phase 1A: Check known_models.json first
        if self._check_known_models(model_ref):
            return "instant_success"  # ~10% of queries

        # Phase 1A: Try multi-strategy Civitai
        results = self.civitai.search_multi_strategy(model_ref)
        if results and results[0].confidence >= 50:
            return results[0]  # ~80% of remaining queries

        # Phase 1B: Qwen fallback with enhanced capabilities
        return self.qwen.search_with_infrastructure(
            model_ref,
            capabilities={
                "known_models": self.known_models,
                "search_by_id": self.civitai.search_by_id,
                "multi_strategy": self.civitai.search_multi_strategy,
                "debug_tools": self.civitai.debug_search
            }
        )  # ~10% of queries (truly hard cases)
    ```

*   **Implementation Steps:**
    1.  **Prompt Engineering:** Refine prompts in `docs/planning/QWEN_PROMPT.md` to:
        - Inform Qwen about `known_models.json` existence
        - Teach Qwen when to use `search_by_id()` (if it finds a Civitai URL)
        - Provide examples of multi-strategy search usage

    2.  **Backend Integration:** Update `src/comfyfixersmart/search.py` `QwenSearch` class:
        - Add `known_models` parameter to constructor
        - Add `civitai_backend` parameter for direct method calls
        - Implement smart routing: check known models before LLM call

    3.  **Error Handling:** Robust retry logic for LLM API calls:
        - 3 attempts with exponential backoff
        - Fallback to direct Civitai search on LLM failure
        - Structured error logging for debugging

    4.  **Performance Optimization:**
        - Cache Qwen search results (30-day TTL)
        - Skip LLM call if model in `known_models.json`
        - Batch similar queries when possible

    5.  **Testing & Validation:**
        - A/B testing with Phase 1A disabled to measure Qwen improvement
        - Integration testing with full cascade (known → multi-strategy → Qwen)
        - Accuracy benchmarking on 100+ model dataset

*   **Acceptance Criteria:**
    - Overall search accuracy: >95% (Phase 1A + 1B combined)
    - Qwen-only accuracy: >80% (up from <70%)
    - Qwen call reduction: 90% (only invoked for truly hard cases)
    - Graceful degradation: System works even if Qwen LLM unavailable

---

### 3.2. Phase 2: Embedding Support (DP-017) - Week 5

*   **Goal:** Add full support for detecting and downloading missing textual inversion embeddings.

*   **Why After Phase 1:** Embeddings are just another model type that requires reliable search. Phase 1's improved search infrastructure makes this straightforward.

*   **Implementation Steps:**
    1.  **Detection:** Update `scanner.py` to recognize `embedding:name` syntax in workflow JSON.
    2.  **Configuration:** Add `embeddings` to the model type mapping in `config.py`.
    3.  **Search:** Extend the `CivitaiSearch` class in `search.py` to filter by the `TextualInversion` type.
        - Uses the multi-strategy search from Phase 1A
        - Supports direct ID lookup for known embeddings
    4.  **Download:** Update `download.py` to place embedding files (`.pt`, `.safetensors`) in the correct `models/embeddings/` directory.
    5.  **Testing & Documentation:** Add unit tests and update the user guide.

*   **Acceptance Criteria:**
    - The tool correctly identifies, finds, and downloads missing embeddings
    - Previously failing workflows with embeddings now load successfully
    - Embedding search uses Phase 1A multi-strategy infrastructure

---

### 3.3. Phase 2: Incremental Workflow - Weeks 6-7

*   **Goal:** Rework the batch-oriented download process into a more responsive, one-model-at-a-time workflow.

*   **Implementation Steps:**
    1.  **Sequential Processing:** Modify `core.py` to process one missing model at a time (search → download → verify).
    2.  **Real-time Feedback:** Add progress tracking and live updates to the CLI and status files.
    3.  **Individual Scripts:** Enhance `download.py` to generate per-model download scripts for easier debugging.
    4.  **Verification:** Add an automated verification step that checks file integrity after every few downloads.

*   **Acceptance Criteria:**
    - The user sees real-time progress
    - Downloads start immediately (no waiting for full batch)
    - System is more resilient to individual model failures
    - Can pause/resume mid-download

---

### 3.4. Phase 2: Core Automation - Week 8

*   **Goal:** Implement the foundational components for automated, scheduled workflow analysis.

*   **Implementation Steps:**
    1.  **Scheduler:** Create `scheduler.py` to run analysis on a configurable interval, with guards for resource usage (e.g., minimum VRAM).
    2.  **Status Reporting:** Implement a master status report generator that creates JSON and Markdown summaries in the `output/` directory.
    3.  **Cache Management:** Implement an intelligent cache refresh system that updates the local model inventory on each run.

*   **Acceptance Criteria:**
    - The scheduler runs reliably
    - Status reports accurately reflect the health of the workflow library
    - Cache refresh doesn't cause performance issues

---

## 4. Leveraging the Existing Dashboard

The project includes a pre-existing React-based dashboard in `src/copilot_backend/`, which provides a significant head start on UI development (estimated 40% time savings).

*   **Integration Strategy:** Instead of building a new UI from scratch, we will extend the existing dashboard.
*   **Extension Points:**
    *   Add new pages and components for `ComfyFixerSmart`-specific features (e.g., scheduler status, download queue).
    *   Extend the existing API to serve data from our backend.
    *   Utilize the existing styling and component library for a consistent look and feel.

This approach allows for rapid prototyping and provides a rich user interface for the features developed in this roadmap.
