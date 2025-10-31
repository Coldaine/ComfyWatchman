# ComfyWatchman Reboot Instructions

> **Context:** This project has diverged significantly from its original vision. This document provides comprehensive instructions for an AI agent to perform a controlled repository restructure, salvaging valuable components while rebuilding documentation and architecture to align with the vision document.

---

## 🎯 Primary Objective

Transform this repository from a CLI-centric model downloader into a **LangGraph-orchestrated intelligent workflow assistant** that monitors, explains, optimizes, and maintains ComfyUI workflows autonomously while preserving only the utility code that serves this vision.

---

## 📋 Phase 0: Assessment & Salvage (Week 1)

### Step 0.1: Inventory Current Codebase

**Action:** Scan the entire repository and categorize every file into one of these buckets:

1. **🟢 KEEP - Core Utilities (Move to `src/comfywatchman/core/utils/`)**
   - Files that provide reusable, non-orchestration functionality
   - Examples: parsing, validation, API clients, file operations
   
2. **🟡 ADAPT - Needs Refactoring (Document for Phase 1)**
   - Files with good logic but wrong architecture
   - Will become LangGraph tool functions
   
3. **🔴 DELETE - Misaligned with Vision**
   - CLI orchestration that will be replaced by LangGraph
   - Ad-hoc scripts and one-off experiments
   - Redundant or obsolete code
   
4. **📚 ARCHIVE - Historical Reference**
   - Move to `archives/` for reference but remove from active codebase

**Deliverable:** Create `docs/phase0/SALVAGE_INVENTORY.md` with:
```markdown
# Code Salvage Inventory

## 🟢 KEEP - Core Utilities
| File Path | Purpose | New Location | Notes |
|-----------|---------|--------------|-------|
| src/comfyfixersmart/scanner.py | Workflow JSON parsing | src/comfywatchman/tools/scanner.py | Solid, reusable |
| ... | ... | ... | ... |

## 🟡 ADAPT - Refactor to Tools
| File Path | Current Issue | Refactor Plan | Priority |
|-----------|---------------|---------------|----------|
| src/comfyfixersmart/core.py | Monolithic orchestrator | Break into LangGraph nodes | P0 |
| ... | ... | ... | ... |

## 🔴 DELETE - Not Aligned
| File Path | Reason for Deletion |
|-----------|---------------------|
| demo_download_missing_models.sh | One-off demo script |
| ... | ... |

## 📚 ARCHIVE - Historical Reference
| File Path | Archival Reason |
|-----------|-----------------|
| docs/thoughTprocess.md | Outdated thought process |
| ... | ... |
```

### Step 0.2: Slash & Burn Documentation

**Action:** Review ALL markdown files in `docs/` and determine which align with the vision.

**DELETE immediately:**
- Any documentation describing CLI workflows that contradict the vision
- Ad-hoc design notes that don't reference the vision phases
- Implementation details for deprecated features

**KEEP and reorganize:**
- `docs/strategy/vision.md` (THE source of truth)
- `research/RESEARCH_PROMPT.md` (if exists)
- `research/EXISTING_SYSTEMS.md` (if exists)
- Any LangGraph research or agent-related docs

**CREATE new structure:**
```
docs/
├── strategy/
│   └── vision.md                          # IMMUTABLE - The source of truth
├── research/
│   ├── LANGGRAPH_RESEARCH.md              # New: LangGraph best practices
│   ├── RAG_RESEARCH.md                    # New: Local RAG strategies
│   ├── HARDWARE_PROFILING_RESEARCH.md     # New: VRAM detection techniques
│   └── EXISTING_SYSTEMS.md                # Existing analysis
├── phase0/
│   ├── SALVAGE_INVENTORY.md               # From Step 0.1
│   └── ARCHITECTURE_DECISION.md           # LangGraph rationale
├── phase1/
│   ├── INTEGRATION_PLAN.md                # Detailed Phase 1 plan
│   ├── SCHEDULER_DESIGN.md                # 2-hour cycle scheduler
│   └── DASHBOARD_SPEC.md                  # Status dashboard requirements
├── phase2/
│   ├── INTEGRATION_PLAN.md                # Detailed Phase 2 plan
│   ├── KNOWLEDGE_BASE_DESIGN.md           # Document pack structure
│   └── AGENTIC_SEARCH_DESIGN.md           # Qwen agent orchestration
├── phase3/
│   ├── INTEGRATION_PLAN.md                # Detailed Phase 3 plan (future)
│   └── RAG_INTEGRATION_SPEC.md            # Vector store design
└── api/
    └── TOOL_REGISTRY.md                   # Catalog of all LangGraph tools
```

**Deliverable:** Execute the deletion and reorganization, then create `docs/phase0/RESTRUCTURE_COMPLETE.md` documenting what was removed and why.

### Step 0.3: LangGraph Research

**Action:** Conduct comprehensive research on LangGraph usage patterns for this project's needs.

**Research Topics:**

1. **LangGraph Fundamentals**
   - StateGraph vs. MessageGraph: which for our use case?
   - State management patterns for long-running workflows
   - Persistence backends (SQLite vs. Redis vs. JSON files)
   - Checkpoint/resume patterns for interrupted workflows

2. **Scheduled Agent Patterns**
   - How to implement recurring 2-hour cycles with LangGraph
   - Conditional execution based on system state (VRAM availability, ComfyUI status)
   - Integration with system cron or systemd timers
   - State persistence across restarts

3. **Tool-Calling Patterns**
   - Wrapping existing Python functions as LangGraph tools
   - Tool error handling and retry logic
   - Parallel vs. sequential tool execution
   - Tool result validation

4. **Human-in-the-Loop Patterns**
   - Interrupt mechanisms for approval tokens
   - Presenting choices to users (multiple model candidates)
   - Timeout handling when user doesn't respond
   - Resuming after human approval

5. **Multi-Agent Orchestration**
   - Supervisor pattern for coordinating specialist agents
   - Agent handoff patterns (scanner → explainer → optimizer)
   - Shared state management between agents
   - Error isolation and recovery

6. **Observability & Logging**
   - LangGraph tracing and debug tools (LangSmith alternatives)
   - Local logging for audit trails
   - Performance metrics collection
   - Graph visualization for debugging

**Research Queries to Execute:**

```markdown
# Query 1: LangGraph Scheduled Workflows
Search for examples of LangGraph agents that run on schedules, persist state between runs, and handle system resource checks before execution.

# Query 2: LangGraph Tool Wrapping Best Practices
Find documentation on converting existing Python utilities (file scanners, API clients, download managers) into LangGraph tools with proper error handling.

# Query 3: LangGraph Approval Flows
Research patterns for implementing human approval gates in LangGraph, especially time-boxed approval tokens and resumable workflows.

# Query 4: LangGraph + RAG Integration
Find examples of LangGraph workflows integrated with local vector stores (ChromaDB, FAISS) for document retrieval.

# Query 5: LangGraph State Persistence
Research best practices for persisting LangGraph state to local files (JSON) vs. databases, especially for privacy-sensitive workflows.
```

**Deliverable:** Create `docs/research/LANGGRAPH_RESEARCH.md` with:
- Answers to all research queries
- Code snippets/examples from LangGraph documentation
- Recommendations for our architecture
- Links to relevant LangGraph documentation sections

---

## 📋 Phase 0.4: Salvage Core Utilities

### Step 0.4.1: Identify Salvageable Code

**Criteria for KEEP:**
✅ Pure utility functions (no orchestration logic)
✅ Well-tested, working code
✅ Reusable across multiple agents/tools
✅ Aligned with vision outcomes

**High-Priority Files to Salvage:**

| Current Path | Purpose | New Path | Refactor Needed? |
|--------------|---------|----------|------------------|
| `src/comfyfixersmart/scanner.py` | Workflow JSON parsing | `src/comfywatchman/tools/workflow_scanner.py` | Minor - extract pure functions |
| `src/comfyfixersmart/inventory.py` | Local model enumeration | `src/comfywatchman/tools/model_inventory.py` | Minor - remove CLI coupling |
| `src/comfyfixersmart/search.py` | Multi-backend search | `src/comfywatchman/tools/model_search.py` | Moderate - extract search backends |
| `src/comfyfixersmart/download.py` | Download management | `src/comfywatchman/tools/downloader.py` | Minor - make more functional |
| `src/comfyfixersmart/inspector/` | Model metadata extraction | `src/comfywatchman/tools/inspector/` | Keep as-is |

**Action for Each File:**
1. Copy to new location
2. Remove CLI-specific code (argparse, main functions)
3. Extract pure functions
4. Add type hints if missing
5. Write docstrings explaining purpose and usage as LangGraph tool
6. Update imports

**Deliverable:** Create `docs/phase0/SALVAGE_COMPLETE.md` listing:
- Files successfully migrated
- Functions extracted
- Any breaking changes or deprecations
- Test coverage for salvaged utilities

### Step 0.4.2: Archive Everything Else

**Action:** Move non-salvaged code to `archives/original-codebase/` with timestamp.

```bash
mkdir -p archives/original-codebase-2025-10-31
mv src/comfyfixersmart archives/original-codebase-2025-10-31/
# Keep only salvaged files in new structure
```

---

## 📋 Phase 1: Integration Plan - Workflow Readiness Automation

### Vision Phase 1 Requirements (Direct from vision.md):

- **Scheduler:** LLM-powered workflow checks run when manually triggered AND automatically every 2 hours, provided the machine is awake and sufficient VRAM is free, and ComfyUI is open.
- **Master Status Report:** Each cycle regenerates a comprehensive status entry for every workflow under `workflows/`, marking it runnable only when all nodes are present and each referenced model exists in the proper ComfyUI directory.
- **Static Dashboard:** Produce a locally stored (non-hosted) dashboard summarizing workflow readiness and dependency gaps.
- **Caches:** Refresh lightweight caches of installed custom nodes and available models (grouped by type) on the same cadence to feed reports.

### Step 1.1: Write Phase 1 Integration Plan

**Action:** Create `docs/phase1/INTEGRATION_PLAN.md` with the following structure:

```markdown
# Phase 1 Integration Plan: Workflow Readiness Automation

## Overview
Transform salvaged utilities into a LangGraph-orchestrated system that monitors workflow readiness every 2 hours and produces human-readable status reports.

## Architecture Decision: LangGraph StateGraph

**Why StateGraph over MessageGraph:**
- Need persistent state across 2-hour cycles (workflow statuses, model inventory)
- Complex conditional logic (VRAM checks, ComfyUI status checks)
- Multiple specialized nodes (scanner, inventory, report generator)
- Human-readable state for debugging

**State Schema:**
```python
from typing import TypedDict, List, Dict

class WorkflowHealthState(TypedDict):
    # Inputs
    workflows_dir: str
    comfyui_root: str
    
    # Scan Results
    workflows: List[Dict]  # List of workflow metadata
    models_inventory: Dict[str, List[str]]  # model_type -> [paths]
    custom_nodes: List[str]
    
    # Analysis Results
    workflow_statuses: Dict[str, Dict]  # workflow_name -> status
    missing_dependencies: Dict[str, List]  # workflow_name -> [deps]
    
    # System State
    vram_available: bool
    comfyui_running: bool
    last_check_time: str
    
    # Outputs
    report_path: str
    dashboard_path: str
```

## Component Breakdown

### 1.1: System Health Checker
**Purpose:** Verify system is ready for analysis
**Tools Used:** `psutil`, custom VRAM detector
**Outputs:** `vram_available: bool`, `comfyui_running: bool`
**Conditional:** If false, skip cycle and schedule retry

### 1.2: Workflow Scanner
**Purpose:** Discover and parse all workflows in `workflows/`
**Tools Used:** `workflow_scanner.py` (salvaged)
**Outputs:** `workflows: List[Dict]` with model/node dependencies

### 1.3: Model Inventory Builder
**Purpose:** Scan ComfyUI directories for installed models
**Tools Used:** `model_inventory.py` (salvaged)
**Outputs:** `models_inventory: Dict[str, List[str]]`

### 1.4: Custom Node Inventory
**Purpose:** List installed custom nodes
**Tools Used:** New utility to scan ComfyUI `custom_nodes/`
**Outputs:** `custom_nodes: List[str]`

### 1.5: Dependency Resolver (No LLM Yet)
**Purpose:** Match workflow requirements against inventory
**Logic:** Simple string matching (exact filename match)
**Outputs:** `workflow_statuses`, `missing_dependencies`

### 1.6: Report Generator
**Purpose:** Create Markdown and JSON reports
**Tools Used:** Jinja2 templates
**Outputs:** 
- `output/reports/workflows/index.md` (human-readable)
- `output/reports/workflows/index.json` (machine-readable)
- Per-workflow reports

### 1.7: Dashboard Generator
**Purpose:** Create static HTML dashboard
**Tools Used:** HTML template + embedded JSON
**Outputs:** `output/dashboard/index.html`

## LangGraph Workflow

```python
from langgraph.graph import StateGraph

# Define the graph
workflow = StateGraph(WorkflowHealthState)

# Add nodes
workflow.add_node("check_system", check_system_health)
workflow.add_node("scan_workflows", scan_workflows)
workflow.add_node("build_model_inventory", build_model_inventory)
workflow.add_node("scan_custom_nodes", scan_custom_nodes)
workflow.add_node("resolve_dependencies", resolve_dependencies)
workflow.add_node("generate_reports", generate_reports)
workflow.add_node("generate_dashboard", generate_dashboard)

# Define edges
workflow.set_entry_point("check_system")

# Conditional: only proceed if system ready
workflow.add_conditional_edges(
    "check_system",
    lambda state: "scan" if state["vram_available"] and state["comfyui_running"] else "skip",
    {
        "scan": "scan_workflows",
        "skip": END
    }
)

workflow.add_edge("scan_workflows", "build_model_inventory")
workflow.add_edge("build_model_inventory", "scan_custom_nodes")
workflow.add_edge("scan_custom_nodes", "resolve_dependencies")
workflow.add_edge("resolve_dependencies", "generate_reports")
workflow.add_edge("generate_reports", "generate_dashboard")
workflow.add_edge("generate_dashboard", END)
```

## Scheduler Implementation

**Option 1: Systemd Timer (Recommended)**
```ini
# /etc/systemd/user/comfywatchman.timer
[Unit]
Description=ComfyWatchman Workflow Health Check

[Timer]
OnBootSec=5min
OnUnitActiveSec=2h
Persistent=true

[Install]
WantedBy=timers.target
```

**Option 2: Python APScheduler**
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(run_health_check, 'interval', hours=2)
scheduler.start()
```

## Persistence Strategy

**State Storage:** JSON files in `state/`
- `state/current_health.json` - Latest workflow health state
- `state/history/YYYY-MM-DD-HH-MM.json` - Historical snapshots

**Cache Storage:** JSON files in `cache/`
- `cache/models_inventory.json` - Last model scan (2h TTL)
- `cache/custom_nodes.json` - Last node scan (2h TTL)

## Testing Strategy

1. **Unit Tests:** Test each node function independently
2. **Integration Test:** Full graph execution with mock workflows
3. **System Test:** Real ComfyUI installation test
4. **Performance Test:** Measure scan time for 50+ workflows

## Implementation Milestones

| Milestone | Deliverable | Time Estimate |
|-----------|-------------|---------------|
| M1.1 | System health checker working | 2 days |
| M1.2 | Workflow scanner as LangGraph tool | 3 days |
| M1.3 | Model inventory as LangGraph tool | 2 days |
| M1.4 | Custom node scanner | 1 day |
| M1.5 | Basic dependency resolver | 2 days |
| M1.6 | Report generator with templates | 3 days |
| M1.7 | Dashboard generator | 2 days |
| M1.8 | LangGraph orchestration | 3 days |
| M1.9 | Scheduler integration | 2 days |
| M1.10 | End-to-end testing | 3 days |
| **TOTAL** | **Phase 1 Complete** | **~3 weeks** |

## Success Criteria

- [ ] Workflow health check runs automatically every 2 hours
- [ ] System health check prevents runs when VRAM insufficient
- [ ] All workflows in `workflows/` are scanned and analyzed
- [ ] Reports generated in Markdown and JSON formats
- [ ] Dashboard viewable in browser showing all workflow statuses
- [ ] State persists across system restarts
- [ ] No missed cycles (≥95% reliability over 1 week)

## Research Questions

1. Best method for detecting VRAM availability on Linux?
2. How to detect if ComfyUI is running (process check vs. port check)?
3. LangGraph checkpoint strategy for 2-hour intervals?
4. Report template design - what info is most useful?
```

**Deliverable:** Complete `docs/phase1/INTEGRATION_PLAN.md` with all sections filled in.

### Step 1.2: Write Phase 1 Research Prompts

**Action:** Create `docs/phase1/RESEARCH_PROMPTS.md`

```markdown
# Phase 1 Research Prompts

## R1.1: VRAM Detection on Linux
**Query:** "How to detect available GPU VRAM on Linux using Python? Need to check if at least 2GB is free before running ComfyUI workflow analysis. Prefer solutions that work with NVIDIA GPUs using nvidia-smi or pynvml."

**Expected Outputs:**
- Code snippets for VRAM detection
- Threshold recommendations
- Error handling strategies

---

## R1.2: Process Detection for ComfyUI
**Query:** "Best method to detect if ComfyUI is running on localhost? Should I check for process name, or check if port 8188 is listening? Need reliable detection for scheduling workflow analysis only when ComfyUI is active."

**Expected Outputs:**
- Comparison of process check vs. port check
- Python code examples (psutil or socket)
- Reliability considerations

---

## R1.3: LangGraph Persistence for Scheduled Jobs
**Query:** "LangGraph best practices for persisting state between scheduled runs every 2 hours. Need to save workflow health check results and resume if interrupted. Should I use SQLite checkpointing or JSON file persistence for privacy-first local storage?"

**Expected Outputs:**
- LangGraph persistence backends comparison
- Code examples for JSON-based persistence
- Performance considerations for 50+ workflows

---

## R1.4: ComfyUI Workflow JSON Structure
**Query:** "ComfyUI workflow JSON schema and structure. Need to understand how to parse workflow files to extract model references, custom node dependencies, and parameter settings. Looking for official documentation or robust parsing examples."

**Expected Outputs:**
- Workflow JSON schema overview
- Common node types and their parameters
- Model reference patterns (checkpoints, LoRAs, embeddings)

---

## R1.5: Static Dashboard Generation
**Query:** "Generate a static HTML dashboard from JSON data without hosting a web server. Need a single-file HTML with embedded CSS/JS that reads workflow status JSON and displays it as an interactive dashboard. No build tools or npm dependencies."

**Expected Outputs:**
- Template HTML with embedded JavaScript
- JSON data binding examples
- Responsive design patterns for status displays

---

## R1.6: Systemd User Timer Setup
**Query:** "How to set up systemd user timer (not system-level) to run a Python script every 2 hours. Timer should start on boot, persist across user sessions, and log output. Include instructions for enabling/disabling timer."

**Expected Outputs:**
- Complete .timer and .service file examples
- Installation commands
- Logging configuration

---

## R1.7: LangGraph Conditional Execution
**Query:** "LangGraph conditional edges pattern for skipping workflow execution based on runtime checks. Need to check system state (VRAM, process running) and either proceed with analysis or skip and schedule next run."

**Expected Outputs:**
- Conditional edge syntax examples
- State-based routing patterns
- Best practices for early termination
```

**Deliverable:** Complete `docs/phase1/RESEARCH_PROMPTS.md`

### Step 1.3: Additional Phase 1 Specs

**Action:** Create these additional specification documents:

1. **`docs/phase1/SCHEDULER_DESIGN.md`**
   - Systemd timer configuration
   - APScheduler alternative
   - Failure recovery strategy
   - Logging and monitoring

2. **`docs/phase1/DASHBOARD_SPEC.md`**
   - Dashboard layout mockup (ASCII or description)
   - Data visualization requirements
   - Interactivity requirements (filters, search)
   - Refresh strategy

3. **`docs/phase1/TESTING_PLAN.md`**
   - Unit test strategy for each node
   - Integration test scenarios
   - Mock data fixtures
   - Performance benchmarks

---

## 📋 Phase 2: Integration Plan - Knowledge-Guided Resolution

### Vision Phase 2 Requirements:

- **Curated Knowledge Base:** Plain-document knowledge pack for LLM reasoning
- **Scheduled Discovery:** Attempt to resolve missing models/nodes
- **Agentic Search Workflow:** Use Qwen to manipulate search tools
- **Doubt Handling:** Return UNCERTAIN status with candidate list
- **Owner Workflow Schemas:** Auto-Inpaint, Image-Cycling, Dynamic Prompt Generator

### Step 2.1: Write Phase 2 Integration Plan

**Action:** Create `docs/phase2/INTEGRATION_PLAN.md`

```markdown
# Phase 2 Integration Plan: Knowledge-Guided Resolution

## Overview
Extend Phase 1 system with LLM-powered model search, knowledge base integration, and intelligent dependency resolution that can explain WHY models are chosen and WHEN it's uncertain.

## New Components

### 2.1: Knowledge Base Builder
**Purpose:** Maintain plain-text document pack for LLM grounding
**Structure:**
```
knowledge/
├── nodes/
│   ├── samplers.md
│   ├── loaders.md
│   └── ...
├── models/
│   ├── checkpoints-sdxl.md
│   ├── loras-concepts.md
│   └── ...
├── workflows/
│   ├── inpainting-patterns.md
│   ├── upscaling-patterns.md
│   └── ...
└── schemas/
    ├── auto-inpaint-frontend.md
    ├── image-cycling-frontend.md
    └── dynamic-prompt-generator.md
```

**Refresh Strategy:** Update docs on demand or weekly from curated sources

### 2.2: Qwen Agent Search Orchestrator
**Purpose:** Use Qwen LLM to coordinate multi-backend search with reasoning
**Architecture:**
```python
class QwenSearchAgent:
    def search(self, model_name: str, context: Dict) -> SearchResult:
        # 1. Extract keywords from model name
        keywords = self.extract_keywords(model_name, context)
        
        # 2. Decide search strategy
        strategy = self.plan_search_strategy(keywords)
        
        # 3. Execute searches (Civitai, HuggingFace, etc.)
        results = self.execute_searches(strategy)
        
        # 4. Validate and rank results
        validated = self.validate_results(results, model_name)
        
        # 5. Return with confidence score
        return self.rank_and_return(validated)
```

**Key Features:**
- Reasoning logged at each step
- Confidence scoring (0-100%)
- UNCERTAIN status when confidence < 70%
- Tool usage tracked for audit

### 2.3: LLM Workflow Explainer
**Purpose:** Generate human-readable explanations of workflow intent
**Inputs:**
- Workflow JSON
- Knowledge base context (retrieved docs)
- Model inventory

**Outputs:**
- Purpose statement
- Expected outputs
- Hardware requirements estimate
- Quality/speed trade-offs

**Example Output:**
```markdown
## Workflow: turbo-upscale-x4.json

**Purpose:** Fast 4x image upscaling using SDXL Turbo for speed

**Process:**
1. Loads SDXL Turbo checkpoint (low-quality, fast)
2. Applies ControlNet Tile for structure preservation
3. Upscales in 2x2 tile batches
4. Minimal denoising steps (4-8)

**Hardware Requirements:**
- VRAM: ~6GB
- Speed: ~30 sec for 1024x1024 -> 4096x4096

**Trade-offs:**
- ✅ Very fast
- ⚠️ Lower quality than full SDXL
- ⚠️ May have tile seams on complex images
```

### 2.4: Uncertainty Handler (NEW)
**Purpose:** Present multiple candidates to user when uncertain
**Triggers:** Confidence < 70% OR multiple good matches
**Outputs:**
```json
{
  "status": "UNCERTAIN",
  "model_name": "realistic_vision_v5.safetensors",
  "candidates": [
    {
      "name": "Realistic Vision V5.1",
      "source": "civitai",
      "confidence": 0.85,
      "reason": "Exact filename match",
      "url": "https://civitai.com/models/12345"
    },
    {
      "name": "Realistic Vision V5.0",
      "source": "civitai",
      "confidence": 0.75,
      "reason": "Similar filename, older version",
      "url": "https://civitai.com/models/12340"
    }
  ],
  "recommendation": "First candidate is likely correct (exact filename match)",
  "action": "Please review and approve download"
}
```

## Updated LangGraph Workflow

**New Nodes Added to Phase 1 Graph:**
- `load_knowledge_base` - Loads relevant docs into context
- `explain_workflows` - LLM generates workflow explanations
- `agentic_search` - Qwen agent searches for missing models
- `handle_uncertainty` - Prompts user when confidence low
- `download_approved` - Downloads only approved models

**Human-in-the-Loop Integration:**
```python
workflow.add_node("handle_uncertainty", present_candidates_to_user)
workflow.add_conditional_edges(
    "handle_uncertainty",
    lambda state: "approved" if state["user_approved"] else "skip",
    {
        "approved": "download_approved",
        "skip": END
    }
)
```

## Implementation Milestones

| Milestone | Deliverable | Time Estimate |
|-----------|-------------|---------------|
| M2.1 | Knowledge base structure | 3 days |
| M2.2 | Document pack initial content | 5 days |
| M2.3 | Qwen agent search integration | 5 days |
| M2.4 | LLM workflow explainer | 4 days |
| M2.5 | Uncertainty handler UI | 3 days |
| M2.6 | Approval token system | 3 days |
| M2.7 | Download queue with approval gates | 3 days |
| M2.8 | End-to-end testing | 4 days |
| **TOTAL** | **Phase 2 Complete** | **~4-5 weeks** |

## Success Criteria

- [ ] Knowledge base contains 50+ curated documents
- [ ] LLM explanations rated ≥4/5 for clarity by owner
- [ ] Agentic search resolves 90%+ of missing models
- [ ] Uncertainty handler triggers for ambiguous cases
- [ ] No downloads occur without explicit approval
- [ ] Search reasoning logged for audit

## Open Questions

1. Which Qwen model version? (Qwen2.5 recommended)
2. Local vs. API-based LLM inference?
3. Knowledge base update cadence?
4. How to source initial knowledge base content?
```

**Deliverable:** Complete `docs/phase2/INTEGRATION_PLAN.md`

### Step 2.2: Write Phase 2 Research Prompts

**Action:** Create `docs/phase2/RESEARCH_PROMPTS.md`

```markdown
# Phase 2 Research Prompts

## R2.1: Qwen Agent Framework
**Query:** "How to implement an agentic search workflow using Qwen LLM with LangGraph? Need the LLM to decide search strategies, call multiple search tools (Civitai API, HuggingFace), validate results, and return confidence scores. Looking for tool-calling patterns with Qwen."

---

## R2.2: Local Knowledge Base for LLM Grounding
**Query:** "Best practices for creating a local plain-text knowledge base to ground LLM responses. Need to maintain markdown documents about ComfyUI nodes, models, and workflows. How to structure for easy retrieval without a vector database?"

---

## R2.3: LLM Confidence Scoring
**Query:** "How to extract confidence scores from LLM outputs when searching/matching? Need the model to return a 0-100% confidence along with its reasoning. Prefer techniques that work with open-source models like Qwen."

---

## R2.4: Human-in-the-Loop with LangGraph
**Query:** "LangGraph patterns for human approval gates. Need to pause workflow execution, present options to user, wait for approval (with timeout), then resume. Looking for interrupt/resume patterns."

---

## R2.5: Workflow Intent Analysis
**Query:** "Using LLMs to analyze ComfyUI workflow JSON and extract intent/purpose. What context should be provided to the LLM? How to structure prompts for consistent, accurate explanations?"

---

## R2.6: Multi-Source Search Ranking
**Query:** "Algorithm for ranking search results from multiple sources (Civitai, HuggingFace, ModelScope) when looking for AI models. How to normalize confidence scores across different APIs and filename matching strategies?"

---

## R2.7: Approval Token Security
**Query:** "Secure implementation of time-limited, single-use approval tokens for authorizing agent actions. Need local-only implementation (no auth server) with cryptographic verification and expiration."
```

**Deliverable:** Complete `docs/phase2/RESEARCH_PROMPTS.md`

### Step 2.3: Additional Phase 2 Specs

**Action:** Create these documents:

1. **`docs/phase2/KNOWLEDGE_BASE_DESIGN.md`**
   - Document structure and taxonomy
   - Content sourcing strategy
   - Update and versioning process
   - Retrieval patterns (keyword, semantic)

2. **`docs/phase2/AGENTIC_SEARCH_DESIGN.md`**
   - Qwen prompt templates
   - Search strategy decision tree
   - Validation rules
   - Logging and tracing

3. **`docs/phase2/WORKFLOW_SCHEMAS.md`**
   - Auto-Inpaint Frontend specification
   - Image-Cycling Frontend specification
   - Dynamic Prompt Generator specification
   - Usage guardrails

---

## 📋 Phase 3: Integration Plan - Extended LLM + RAG Vision

### Step 3.1: Write Phase 3 Integration Plan

**Action:** Create `docs/phase3/INTEGRATION_PLAN.md`

```markdown
# Phase 3 Integration Plan: Extended LLM + RAG Vision

> **STATUS:** DEFERRED - Do not implement until Phases 1 & 2 complete and owner approves

## Overview
Optional integration of vector embeddings, semantic search, and advanced RAG workflows for workflow comparison, optimization recommendations, and automated variant generation.

## Architecture Decisions (Pending)

### Vector Store Selection
**Options:**
- ChromaDB (lightweight, local, persistent)
- FAISS (fast, in-memory, requires save/load)
- Qdrant (full-featured, can run locally)

**Evaluation Criteria:**
- Local-only operation (no cloud)
- Privacy guarantees
- Performance for 100-1000 workflows
- Integration with LangGraph

### Embedding Model Selection
**Options:**
- `all-MiniLM-L6-v2` (lightweight, fast)
- `bge-small-en-v1.5` (better quality)
- `gte-large` (highest quality, slower)

**Requirements:**
- Local inference only
- <500MB model size
- <100ms per embedding

## New Capabilities (Deferred)

### 3.1: Semantic Workflow Search
**Query:** "Find workflows similar to turbo-upscale-x4.json"
**Process:**
1. Embed target workflow (structure + purpose)
2. Search vector store
3. Return top-K similar workflows with explanations

### 3.2: Automated Optimization Suggestions
**Query:** "Optimize workflow for 8GB VRAM"
**Process:**
1. Retrieve similar workflows from vector store
2. Analyze parameter differences
3. Suggest modifications with trade-off analysis

### 3.3: Regression Detection
**Compare:** workflow-v1.json vs. workflow-v2.json
**Outputs:**
- Parameter diffs
- VRAM usage change estimate
- Quality impact prediction

## Research Required (Phase 3 Kickoff)

- [ ] Benchmark vector stores for local performance
- [ ] Evaluate embedding models for workflow similarity
- [ ] Test RAG retrieval quality with 50+ workflows
- [ ] Measure privacy guarantees (no data egress)

## Success Criteria (To Be Defined)

- TBD after Phase 1 & 2 complete
- Owner approval required before implementation

```

**Deliverable:** Create `docs/phase3/INTEGRATION_PLAN.md` (stub for now)

### Step 3.2: Write Phase 3 Research Prompts

**Action:** Create `docs/phase3/RESEARCH_PROMPTS.md`

```markdown
# Phase 3 Research Prompts (DEFERRED)

> These research prompts should NOT be executed until Phase 1 & 2 are complete and owner approves Phase 3.

## R3.1: Local Vector Store Comparison
**Query:** "Compare ChromaDB, FAISS, and Qdrant for local-only vector storage. Need privacy-preserving, no-cloud option for storing embeddings of 100-1000 ComfyUI workflows. Evaluation criteria: performance, persistence, LangGraph integration."

## R3.2: Workflow Embedding Strategies
**Query:** "How to embed ComfyUI workflow JSON for semantic similarity search? Should I embed the raw JSON, extract structured features, or generate text summaries first? Need embeddings that capture both structure and intent."

## R3.3: RAG + LangGraph Integration Patterns
**Query:** "LangGraph examples of retrieval-augmented generation (RAG) with local vector stores. Need to retrieve relevant documents from ChromaDB/FAISS during LLM reasoning steps without external API calls."

## R3.4: Regression Detection Metrics
**Query:** "Metrics for detecting quality regressions in AI image generation workflows. Need automated, objective measures that don't require running the workflows. Consider parameter changes, model swaps, resolution changes."

## R3.5: Privacy-Preserving Embeddings
**Query:** "How to ensure vector embeddings don't leak sensitive information? Best practices for local-only embedding storage, preventing data exfiltration, and auditing vector store access."
```

**Deliverable:** Create `docs/phase3/RESEARCH_PROMPTS.md`

---

## 📋 Final Deliverables Checklist

Upon completion of ALL steps above, the repository should have:

### Documentation Structure
```
docs/
├── strategy/
│   └── vision.md (unchanged)
├── research/
│   ├── LANGGRAPH_RESEARCH.md (✓ from Phase 0)
│   ├── RAG_RESEARCH.md (Phase 3)
│   └── EXISTING_SYSTEMS.md (if exists)
├── phase0/
│   ├── SALVAGE_INVENTORY.md (✓)
│   ├── RESTRUCTURE_COMPLETE.md (✓)
│   └── ARCHITECTURE_DECISION.md (✓)
├── phase1/
│   ├── INTEGRATION_PLAN.md (✓)
│   ├── RESEARCH_PROMPTS.md (✓)
│   ├── SCHEDULER_DESIGN.md (✓)
│   ├── DASHBOARD_SPEC.md (✓)
│   └── TESTING_PLAN.md (✓)
├── phase2/
│   ├── INTEGRATION_PLAN.md (✓)
│   ├── RESEARCH_PROMPTS.md (✓)
│   ├── KNOWLEDGE_BASE_DESIGN.md (✓)
│   ├── AGENTIC_SEARCH_DESIGN.md (✓)
│   └── WORKFLOW_SCHEMAS.md (✓)
├── phase3/
│   ├── INTEGRATION_PLAN.md (stub) (✓)
│   └── RESEARCH_PROMPTS.md (✓)
└── api/
    └── TOOL_REGISTRY.md (for LangGraph tools)
```

### Code Structure
```
src/comfywatchman/
├── core/
│   └── utils/           # Salvaged utilities
│       ├── scanner.py
│       ├── inventory.py
│       ├── search.py
│       ├── download.py
│       └── inspector/
├── agents/              # NEW: LangGraph agents (Phase 1+)
│   ├── workflow_health.py
│   ├── model_resolver.py
│   └── optimizer.py (Phase 2+)
├── tools/               # NEW: LangGraph tool wrappers
│   ├── workflow_scanner.py
│   ├── model_inventory.py
│   ├── model_search.py
│   └── downloader.py
├── knowledge/           # NEW: Knowledge base (Phase 2)
│   ├── nodes/
│   ├── models/
│   └── workflows/
├── state/               # NEW: State persistence
│   ├── manager.py
│   └── schemas.py
└── cli.py               # Simplified CLI (just invoke agents)
```

### Archives
```
archives/
└── original-codebase-2025-10-31/
    └── [everything not salvaged]
```

---

## 🎯 Execution Instructions for AI Agent

### Priority Order:
1. **Phase 0 (Week 1):** Assessment, salvage, documentation slash & burn
2. **Phase 1 Research (Week 1-2):** Execute all Phase 1 research prompts
3. **Phase 1 Specs (Week 2):** Write detailed Phase 1 integration plan
4. **Phase 2 Research (Week 2-3):** Execute all Phase 2 research prompts
5. **Phase 2 Specs (Week 3):** Write detailed Phase 2 integration plan
6. **Phase 3 Stubs (Week 3):** Create Phase 3 stub documents
7. **Review Checkpoint:** Present complete documentation to owner

### Key Principles:
- ✅ **DO:** Keep scanner, inventory, search, download, inspector utilities
- ✅ **DO:** Rewrite orchestration as LangGraph StateGraph
- ✅ **DO:** Focus on Phase 1 & 2; defer Phase 3
- ✅ **DO:** Create comprehensive, actionable documentation
- ❌ **DON'T:** Preserve CLI-centric architecture
- ❌ **DON'T:** Keep ad-hoc scripts or demos
- ❌ **DON'T:** Start coding before documentation complete
- ❌ **DON'T:** Skip research prompts - they inform design

### Success Criteria:
- [ ] All old documentation removed or archived
- [ ] New documentation structure matches template above
- [ ] All research prompts written and ready to execute
- [ ] Integration plans are detailed and actionable
- [ ] Code salvage complete with new file structure
- [ ] Owner can read docs and understand full plan

---

## 📞 Owner Review Checkpoints

After completing each phase of documentation:

1. **Phase 0 Complete:** Review salvage inventory - anything to preserve?
2. **Phase 1 Plan Complete:** Does scheduler design match expectations?
3. **Phase 2 Plan Complete:** Is knowledge base structure appropriate?
4. **Pre-Implementation:** Final approval before coding begins

---

**END OF INSTRUCTIONS**
