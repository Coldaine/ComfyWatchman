# Phase 1 Integration Plan: Workflow Readiness Automation

## Overview
This document outlines the plan to transform salvaged utilities into a LangGraph-orchestrated system that monitors workflow readiness every 2 hours and produces human-readable status reports.

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
    workflows: List[Dict] # List of workflow metadata
    models_inventory: Dict[str, List[str]] # model_type -> [paths]
    custom_nodes: List[str]
    # Analysis Results
    workflow_statuses: Dict[str, Dict] # workflow_name -> status
    missing_dependencies: Dict[str, List] # workflow_name -> [deps]
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
**Tools Used:** `workflow_scanner.py` (to be created)
**Outputs:** `workflows: List[Dict]` with model/node dependencies

### 1.3: Model Inventory Builder
**Purpose:** Scan ComfyUI directories for installed models
**Tools Used:** `model_inventory.py` (to be created)
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
from langgraph.graph import StateGraph, END

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