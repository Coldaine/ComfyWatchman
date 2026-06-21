# Copilot Local-First Evaluation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decide whether the correct product path is to fork/localize ComfyUI-Copilot as the primary Comfy assistant surface, with ComfyWatchman contributing dependency readiness and safe install planning.

**Architecture:** Treat Copilot as the candidate product shell because it already lives inside ComfyUI and already has chat, workflow generation, debugging, rewriting, parameter tuning, node/model recommendation, canvas integration, and agent-mode surfaces. Treat ComfyWatchman as the candidate local readiness engine, not necessarily the top-level app. Treat ComfyUI-Manager as the operational installer/snapshot/security substrate.

**Tech Stack:** ComfyUI custom node/plugin, React/Vite Copilot UI, Copilot Python backend, `openai-agents`, local/OpenAI-compatible providers such as LM Studio, ComfyUI-Manager APIs/`cm-cli`, ComfyWatchman scanner/search/download/state modules.

---

## Decision Status

This is an evaluation plan, not a settled decision.

The prior Manager-first and ComfyWatchman-native strategy is no longer allowed to stand as the only path. The Copilot-local-first path must be evaluated as a first-class candidate and may become the primary direction if it runs locally and proves easier to productize.

## Working Hypothesis

The likely correct path is:

1. Fork a ComfyUI-Copilot codebase as the product base.
2. Remove hosted-service assumptions from the default path.
3. Make local/open-provider agent mode the normal operating mode.
4. Add ComfyWatchman capabilities as local tools inside Copilot.
5. Use ComfyUI-Manager for install/update/snapshot/security operations where possible.

This would preserve the mature Comfy assistant surface instead of rebuilding it in a separate dashboard.

## Why This Path Exists

Copilot already has the surfaces ComfyWatchman would otherwise spend months recreating:

- in-Comfy assistant UI
- current-canvas context
- workflow generation
- workflow debugging
- workflow rewriting
- parameter tuning
- model recommendations
- node recommendations
- selected-node inspection
- workflow import/apply behavior
- Comfy runtime execution hooks

The problem is not that Copilot lacks a product surface. The problem is that upstream Copilot drifted around hosted services and now needs a local-first path.

## Candidate Bases

| Candidate | Role | Evaluation Question |
| --- | --- | --- |
| `AIDC-AI/ComfyUI-Copilot` | Upstream product base | What still works locally after the hosted service suspension notice? |
| `vehoelite/ComfyUI-Copilot` / PR `AIDC-AI/ComfyUI-Copilot#130` | Local-agent candidate | Does Agent Mode, multi-provider routing, LM Studio support, and local tool use actually run? |
| `Comfy-Org/ComfyUI-Manager` | Operational substrate | Can Copilot call Manager or `cm-cli` for safe installs, snapshots, and node/model management? |
| `ComfyWatchman` | Readiness engine | Which scanner, inventory, search, and download components are worth exposing as Copilot tools? |

## Evidence Already Found

Upstream Copilot:

- Repo: `AIDC-AI/ComfyUI-Copilot`
- Stars checked on 2026-05-20: about 5,167
- Last push checked on 2026-05-20: 2026-04-07
- README says hosted API service has been suspended and users should configure their own API key/base URL for agent capabilities.

Local-agent fork / PR:

- PR: `AIDC-AI/ComfyUI-Copilot#130`
- Head repo: `vehoelite/ComfyUI-Copilot`
- Claims Agent Mode, multi-provider support, LM Studio fixes, local model routing, tool budgets, loop prevention, voice I/O, and QLoRA training assets.
- Inspected files include:
  - `backend/service/agent_mode.py`
  - `backend/service/agent_mode_tools.py`
  - `backend/agent_factory.py`
  - `HOW_TO_USE_LMSTUDIO.md`
  - `training/generate_dataset.py`
  - `training/train.py`
  - `training/tool_schemas.py`

Important observed local-agent tools:

- `plan_tasks`
- `get_current_workflow_for_agent`
- `save_workflow`
- `validate_workflow`
- `execute_workflow`
- `check_execution_result`
- `search_nodes`
- `get_node_details`
- `list_available_models`

These are the right kind of hooks for local Comfy workflow creation and iteration.

## Evaluation Questions

1. Can the Copilot fork install as a ComfyUI custom node on this machine?
2. Can the fork start without the suspended hosted service?
3. Can LM Studio or another OpenAI-compatible local provider drive chat and agent mode?
4. Can Agent Mode read the current workflow, search installed nodes, inspect node details, list local models, save a workflow, validate it, and execute it?
5. Which features still call AIDC-hosted endpoints by default?
6. Which hosted calls can be disabled, replaced, or routed to local/provider-configured services?
7. Can Manager be used from Copilot for missing custom nodes, missing models, snapshots, and install queues?
8. Which ComfyWatchman functions should become Copilot tools first?
9. Is the v3 fork cleaner to adopt than upstream plus manual patches?
10. Is there a better active fork than `vehoelite/ComfyUI-Copilot`?

## Evaluation Tasks

### Task 1: Get a Clean Local Copy

**Files:**
- External clone: `D:\_projects\ComfyUI-Copilot-local-first`
- Read: `README.md`, `requirements.txt`, `pyproject.toml`, `backend/service/agent_mode.py`, `backend/service/agent_mode_tools.py`, `backend/agent_factory.py`, `ui/package.json`

- [ ] Clone or fetch the candidate fork without polluting ComfyWatchman history.
- [ ] Confirm the exact commit hash.
- [ ] Record whether the clone is upstream, fork, or PR head.
- [ ] Record whether the repo contains built `dist/` assets or needs a UI build.

### Task 2: Static Hosted-Service Audit

**Files:**
- Read under candidate repo: `backend/`, `ui/src/`, `README.md`, `LMSTUDIO_SETUP.md`, `HOW_TO_USE_LMSTUDIO.md`
- Output note: `docs/strategy/COPILOT_LOCAL_FIRST_EVALUATION_RESULTS.md`

- [ ] Search for hosted endpoints, API defaults, and service suspension paths.
- [ ] Classify each external call as required, optional, replaceable, or dead.
- [ ] Identify the minimum config needed to run with LM Studio or another local OpenAI-compatible provider.
- [ ] Identify any hard-coded AIDC/ModelScope/Bing/MCP services that block local operation.

### Task 3: Install/Run Smoke Test

**Files:**
- Candidate repo in ComfyUI `custom_nodes` or linked equivalent.
- Output note: `docs/strategy/COPILOT_LOCAL_FIRST_EVALUATION_RESULTS.md`

- [ ] Install Python dependencies in the ComfyUI Python environment.
- [ ] Start ComfyUI with the Copilot custom node installed.
- [ ] Confirm the Copilot UI button/panel appears.
- [ ] Confirm the backend imports without the wrong `agents` package.
- [ ] Confirm local provider settings can be saved.
- [ ] Confirm a simple chat request reaches the configured provider.

### Task 4: Agent Mode Capability Test

**Files:**
- Candidate repo: `backend/service/agent_mode.py`, `backend/service/agent_mode_tools.py`
- Output note: `docs/strategy/COPILOT_LOCAL_FIRST_EVALUATION_RESULTS.md`

- [ ] Run `search_nodes` against live `/object_info`.
- [ ] Run `get_node_details` for a common built-in node.
- [ ] Run `list_available_models` for checkpoints and LoRAs.
- [ ] Ask Agent Mode to create a small complete workflow.
- [ ] Save the workflow to the canvas.
- [ ] Validate the workflow.
- [ ] Execute only if validation is clean and the user approves.

### Task 5: ComfyWatchman Tool Fit

**Files:**
- Read: `src/comfywatchman/scanner.py`, `src/comfywatchman/inventory.py`, `src/comfywatchman/search.py`, `src/comfywatchman/download.py`, `src/comfywatchman/state_manager.py`
- Output note: `docs/strategy/COPILOT_LOCAL_FIRST_EVALUATION_RESULTS.md`

- [ ] Identify the first three ComfyWatchman functions that should become Copilot local tools.
- [ ] Prefer read-only tools first: scan workflow dependencies, inventory local models, produce missing dependency report.
- [ ] Do not expose download or install mutation until dry-run plans and approvals exist.
- [ ] Decide whether ComfyWatchman should be imported as a Python package, copied as a backend module, or split into a separate local service.

### Task 6: Manager Integration Fit

**Files:**
- Read: `docs/strategy/COMFYUI_MANAGER_ADOPTION_PLAN.md`
- Candidate repo: Copilot backend service/tool files
- Output note: `docs/strategy/COPILOT_LOCAL_FIRST_EVALUATION_RESULTS.md`

- [ ] Determine whether Copilot can call Manager routes directly from inside ComfyUI.
- [ ] Determine whether `cm-cli` is useful when ComfyUI is not running.
- [ ] Define a safe Manager tool subset for Copilot: read installed nodes, read model catalog, save snapshot, queue install only after approval.
- [ ] Record which Manager operations must remain blocked unless explicitly approved.

## Product Decision After Evaluation

After the tasks above, choose one path:

1. **Copilot-local-first becomes primary:** fork/localize Copilot, add ComfyWatchman readiness tools, use Manager for installs.
2. **Hybrid:** keep Copilot as UI/plugin and keep ComfyWatchman as a separate local service exposed through Copilot tools.
3. **ComfyWatchman-native remains primary:** only if Copilot local-agent mode fails materially or cannot be made safe without excessive rewrite.

The decision must be based on running evidence, not docs preference.

## Do Not Do Yet

- Do not keep building the standalone ComfyWatchman dashboard as if it is the product center.
- Do not assume Manager-first means assistant-first.
- Do not rewrite Copilot from scratch.
- Do not expose direct downloads or custom-node installs before approval-state exists.
- Do not treat hosted service suspension as a reason to discard Copilot; it is the reason to localize it.

