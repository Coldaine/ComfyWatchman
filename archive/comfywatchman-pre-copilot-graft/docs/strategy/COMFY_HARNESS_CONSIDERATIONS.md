# Comfy Harness Considerations

This note is about the actual ComfyUI operating harness. It was written from a ComfyWatchman-native perspective and must now be read alongside `COPILOT_LOCAL_FIRST_EVALUATION_PLAN.md`. The open question is whether the harness should live in ComfyWatchman as the product shell or inside a localized ComfyUI-Copilot fork.

## Why the harness comes first

ComfyWatchman is only useful if it can produce trustworthy readiness and install plans for a concrete ComfyUI environment. UI screens can make that state easier to inspect, but they cannot create the truth. The source of truth has to come from ComfyUI itself, local model paths, workflow files, resolver evidence, and explicit operator approvals.

The current repo still contains useful scanner, inventory, search, download, and state pieces. It also contains stale assumptions: hardcoded Comfy roots, legacy widget parsing, script-first downloads, and folder guesses that ignore current Comfy model path behavior. The next major work should evaluate whether those pieces become local tools inside Copilot rather than continuing a standalone ComfyWatchman UI.

The donor evaluation in `COMFY_MCP_DONOR_EVALUATION.md` is the companion decision record for this plan. It identifies which existing ComfyUI MCP projects should be mined for runtime and MCP patterns, and which parts must remain ComfyWatchman-native.

## Product question

The core question is:

Can a local Comfy assistant inspect a real ComfyUI environment, decide whether selected workflows can run, and produce a dry-run plan for everything missing?

Everything else should support that question. The assistant surface may be a localized Copilot fork.

## Components

### 1. Environment discovery

Find the ComfyUI environment before parsing or downloading anything.

Required answers:

- Is ComfyUI installed as Desktop, portable, manual clone, or `comfy-cli` managed install?
- Is a ComfyUI server running?
- What server URL should the harness talk to?
- Where are workflow files?
- What model roots and extra paths are active?
- Which custom nodes are installed?
- Which operating-system path conventions apply on this machine?

Repo state:

- `config.toml` and some docs still assume a fixed local root.
- `ModelInventory` can scan files, but it needs a modern environment-discovery layer before it is authoritative.

### 2. Comfy API client

Add a thin client for live ComfyUI server truth. This should be independent from search, download, and UI code.

Minimum routes:

- `/object_info` for node classes and input definitions.
- `/models` and `/models/{folder}` for model folders and known model files.
- `/queue`, `/history`, `/prompt`, and `/ws` for execution and queue state.
- `/system_stats` for runtime visibility.

Current Comfy docs:

- https://docs.comfy.org/development/comfyui-server/comms_routes
- https://docs.comfy.org/specs/workflow_json
- https://docs.comfy.org/development/core-concepts/models
- https://docs.comfy.org/comfy-cli/reference

### 3. Workflow reader

Do not treat every workflow as the same JSON shape.

Supported inputs should be explicit:

- Workflow JSON v1.
- API prompt JSON.
- Legacy UI workflow JSON.
- PNG-embedded workflow metadata if available.

Output should be a normalized internal representation:

- workflow identity
- source path
- node instances
- node classes
- declared inputs
- model-like fields
- unresolved fields that need Comfy `/object_info`

Repo state:

- `src/comfywatchman/scanner.py` is valuable, but its current extraction path is too dependent on legacy UI JSON and `widgets_values`.
- It should become one parser among several, or be split into a `workflow_reader` package.

### 4. Dependency resolver

The resolver decides what a workflow needs. It should not guess from filenames alone.

Inputs:

- normalized workflow data
- Comfy `/object_info`
- local model inventory
- known Comfy model folders
- optional registry/custom-node metadata

Outputs:

- required node classes
- required model references
- model folder/type expectation
- local match, missing, ambiguous, or unknown status
- confidence and reason

Important distinction:

- Missing custom node is not the same problem as missing model.
- Missing model with known folder is not the same problem as ambiguous model alias.
- A local file in the wrong folder is not the same problem as absent file.

### 5. Model locator

Inventory needs to reflect the actual Comfy install.

It should understand:

- default `ComfyUI/models/*` folders
- `extra_model_paths.yaml`
- Comfy Desktop path conventions
- portable install path conventions
- duplicate model files
- candidate files in wrong folders
- optional hashes and sizes

Current repo pieces:

- `src/comfywatchman/inventory.py` has useful scanning and summary behavior.
- It should be driven by environment discovery, not hardcoded root assumptions.

### 6. Candidate search

Candidate search should produce evidence, not decisions.

Sources:

- local inventory
- Civitai
- Hugging Face
- optional ModelScope
- optional ComfyUI-Manager or registry metadata for custom nodes

Output:

- candidate URL/source
- filename
- size/hash if known
- confidence
- reason
- risk flags
- target folder recommendation

Repo state:

- `src/comfywatchman/search.py` and `src/comfywatchman/civitai_tools/*` are useful salvage.
- Adapters that cannot actually search or download must report unavailable, not success-like fallback state.

### 7. Install plan

This is the central durable product artifact.

An install plan should be dry-run first and explicit:

- affected workflow IDs and paths
- missing model or node
- selected candidate
- download URL or install command
- target path
- expected size/hash if available
- confidence and rationale
- warnings
- approval status

No mutation should happen before this plan exists and is approved.

### 8. Execution layer

Execution is separate from planning.

Responsibilities:

- download approved models
- install approved custom nodes
- resume or retry failed downloads
- report progress
- write state
- never silently choose a target path

Current repo pieces:

- `src/comfywatchman/download.py` and `src/comfywatchman/state_manager.py` are useful, but the script-generation and automatic-download framing should be demoted behind approved install plans.

### 9. Readiness state

State should make the tool useful across sessions.

Persist:

- scanned environments
- scanned workflows
- normalized dependency results
- candidate search runs
- user approvals/rejections
- completed downloads
- failures and retries

This state should feed the UI, CLI, and future automation equally.

### 10. Operator surfaces

UI comes after harness truth.

The six restored UI variants are useful as aesthetic and interaction references:

- Operator Console: main readiness surface.
- Search Workbench: missing-model candidate review.
- Queue Ops: execution and download progress.
- Graph Studio: dependency drilldown.
- Readiness Review: install-plan approval.
- Pipeline Board: optional staged workflow board.

They should not drive backend shape. They should render backend truth.

## Minimal useful implementation order

1. Stabilize the existing non-network core path so it can run without search, download, or live Comfy mutation.
2. Fix configuration loading and root/path handling so `--config`, `COMFYUI_ROOT`, `models_dir`, workflow dirs, and custom-node dirs agree.
3. Fix the current orchestration break where `_analyze_models()` returns node types but `run_workflow_analysis()` does not capture them.
4. Define the readiness report schema: workflows, required models, installed models, missing models, unknown model type, missing custom nodes, recommended target paths, confidence, and blocking errors.
5. Add fixture-based tests under `tests/` with a fake Comfy root, fake workflows, fake model files, and no network/API-key assumptions.
6. Add `ComfyClient` with read-only server probes.
7. Split workflow reading by format and normalize outputs.
8. Resolve dependencies using normalized workflow data plus `/object_info`.
9. Produce a dry-run readiness/install plan.
10. Wire CLI output to the plan before wiring frontend screens.
11. Add execution only after the plan format is stable and reviewed.

## Current blockers found in code

These are the first concrete repair targets before calling this a real harness:

- `src/comfywatchman/core.py`: `run_workflow_analysis()` expects two values from `_analyze_models()`, but `_analyze_models()` returns three, including `all_node_types`. The later missing-node pass then references a value that was not captured.
- `src/comfywatchman/inventory.py`: `ComfyFixerCore()` initialization can fail before a planning-only path because `models_dir`/`COMFYUI_ROOT` is required too early.
- `src/comfywatchman/config.py` and `src/comfywatchman/cli.py`: CLI accepts `--config`, but the config object does not expose the expected `load_from_file()` path.
- `src/comfywatchman/inventory.py`: custom-node inventory references config/state attributes that do not currently exist as called.
- `src/comfywatchman/adapters/copilot_validator.py`: Copilot validation references stale config names and calls a validation method that is not defined as used.
- `src/comfywatchman/download.py` and `src/comfywatchman/state_manager.py`: downloader state updates do not match the JSON state manager API.
- `pyproject.toml`: pytest points at `tests/`, while current tests are at repo root; existing tests include network/API-key assumptions.

Observed verification from the harness audit:

- `uv run python -c "import comfywatchman; from comfywatchman.core import ComfyFixerCore; print('import-ok')"` passed.
- `uv run python -c "from comfywatchman.core import ComfyFixerCore; ComfyFixerCore()"` failed because model path configuration was not available.
- `uv run --extra dev python -m pytest -q` produced 10 failures out of 21 tests.

## What not to do next

- Do not add more UI variants as if aesthetics are the blocker.
- Do not wire downloads before dry-run install plans exist.
- Do not use Copilot as the central Comfy primitive.
- Do not assume `ComfyUI/models/<type>` is the only model destination.
- Do not treat API prompt JSON, Workflow JSON, and legacy UI JSON as the same format.
- Do not present fallback adapters as working integrations when their dependency is missing.

## Kilo and agent delegation

Kilo is installed locally and callable from this repo.

Verified commands:

```powershell
kilo --version
kilocode --version
kilo --help
kilo run --help
kilo config check
kilo auth list
kilo debug paths
kilo debug agent orchestrator
```

Local result:

- `kilo` and `kilocode` are on PATH under `C:\Users\pmacl\AppData\Roaming\npm`.
- Current local version is `7.3.1`.
- `kilo config check` reports no config warnings.
- `kilo auth list` shows configured providers; do not print credential values.
- Kilo paths resolve under `C:\Users\pmacl\.config\kilo`, `C:\Users\pmacl\.local\share\kilo`, and `C:\Users\pmacl\.cache\kilo`.
- This repo has `.kilocode/mcp.json` and `.kilocodemodes`; `.kilocodemodes` currently has no custom modes.
- The local `orchestrator` agent is present and is explicitly configured to delegate work to explore/general agents in waves.

Useful Kilo commands for this work:

```powershell
# Start interactive Kilo in this repo.
kilo .

# Run a bounded harness investigation task.
kilo run --agent orchestrator --dir D:\_research\comfy-remote-repos\ComfyWatchman "Map the Comfy harness modernization work. Do not edit files."

# Run a non-interactive task only after permissions and scope are constrained.
kilo run --agent orchestrator --auto --dir D:\_research\comfy-remote-repos\ComfyWatchman "Inspect workflow parsing gaps and write a report."

# Inspect agent configuration before relying on it.
kilo debug agent orchestrator
```

Codex subagent delegation is also available in this session and should be used for independent passes. Good split points:

- one explorer for Comfy API/current docs
- one explorer for repo scanner/inventory/download state
- one explorer for Kilo/local agent config
- one worker for a bounded implementation slice with a disjoint write set

The important rule is to delegate independent research or disjoint implementation. Do not delegate the immediate blocking step if the main thread needs that answer before continuing.
