# ComfyUI Platform Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make ComfyWatchman a verified local ComfyUI custom-node/extension that can safely inspect, validate, and eventually modify ComfyUI workflows across local, Desktop-managed, and optional Cloud-backed contexts.

**Architecture:** Treat ComfyUI as a platform with separate local server, Desktop instance manager, Cloud API, frontend extension, and Manager/Registry surfaces. Land the path in small PRs: prove local API truth first, repair frontend drift, discover Desktop state, clean packaging metadata, restore read-only readiness tools, then add guarded mutation paths.

**Tech Stack:** ComfyUI PromptServer routes, ComfyUI frontend extension APIs, Python 3.10+, aiohttp, React/Vite, Comfy Desktop, ComfyUI-Manager/Registry metadata, GitHub Actions.

---

## Current Understanding

ComfyUI is no longer just a single local Python app. As of June 21, 2026, the relevant product surfaces are:

- Local ComfyUI server routes: `/prompt`, `/object_info`, `/queue`, `/history`, `/interrupt`, `/system_stats`, `/models`, `/extensions`, and `/ws`.
- Comfy Desktop: a multi-install launcher and updater that can manage adopted installs, shared model/output paths, snapshots, and per-instance launch args.
- Comfy Cloud: hosted execution at `https://cloud.comfy.org` with `X-API-Key` authentication and `/api/...` paths. It is compatible with local APIs, but still experimental and gated by tier/credits.
- Frontend extensions: `WEB_DIRECTORY`, `app.registerExtension`, sidebar tabs, commands, selection toolbox commands, keybindings, settings, and the newer context-menu migration surface.
- Custom node packaging: V3 node schema is the forward path for Python node definitions; Registry/Manager metadata matters for install/update/disable/snapshot workflows.

Official source anchors:

- ComfyUI server routes: https://docs.comfy.org/development/comfyui-server/comms_routes
- Comfy Cloud overview: https://docs.comfy.org/development/cloud/overview
- Comfy Desktop overview: https://docs.comfy.org/installation/desktop/overview
- Comfy Desktop usage: https://docs.comfy.org/installation/desktop/usage/overview
- Comfy Desktop repository: https://github.com/Comfy-Org/desktop
- JavaScript extension hooks: https://docs.comfy.org/custom-nodes/js/javascript_hooks
- JavaScript context menu migration: https://docs.comfy.org/custom-nodes/js/context-menu-migration
- Custom node V3 migration: https://docs.comfy.org/custom-nodes/v3_migration
- Manager install and packaging: https://docs.comfy.org/manager/install

## Local Machine Evidence

Comfy Desktop has an adopted local install on this machine:

```powershell
$desktopConfig = "C:\Users\pmacl\AppData\Roaming\Comfy Desktop\installations.json"
```

Observed active local installation record:

```text
name: ComfyUI
installPath: C:\Users\pmacl\ComfyUI-Installs\ComfyUI
adoptedBaseDir: C:\COMFYUI
adoptedPythonPath: C:\COMFYUI\.venv\Scripts\python.exe
launchArgs: --port 8000 --enable-manager
useSharedModels: true
inputDir: C:\COMFYUI\input
outputDir: C:\COMFYUI\output
```

Observed Cloud installation record:

```text
name: Comfy Cloud
remoteUrl: https://cloud.comfy.org/
```

The previous hidden Desktop launch did start validation and reported "Python server is ready", then quit to apply a Comfy Desktop update. The next live smoke should launch the adopted Python install directly or relaunch the updated Desktop app, then poll port `8000`.

## Files And Responsibilities

- `backend/utils/comfy_gateway.py`: Local ComfyUI server client. It currently uses Cloud-style `/api/prompt`, `/api/object_info`, `/api/queue`, and `/api/history` paths in several methods; local routes need a separate client or path mode.
- `ui/src/apis/comfyApiCustom.ts`: Frontend local API calls. It already calls local `/object_info` paths and should remain local-first.
- `entry/comfyui-bridge.js`: Frontend bridge. It still patches `getExtraMenuOptions`; current ComfyUI frontend migration guidance prefers `getNodeMenuItems`.
- `ui/src/main.tsx`: Sidebar registration. It already uses `app.extensionManager.registerSidebarTab`.
- `__init__.py`: Custom node package entrypoint. It exposes `WEB_DIRECTORY = "entry"`, registers backend controllers, and serves `dist/copilot_web` at `/copilot_web/`.
- `pyproject.toml`: Registry/Manager identity. It still names the package `ComfyUI-Copilot` and points at the upstream AIDC repository.
- `docs/comfywatchman-history/HISTORY_HARVEST.md`: Product intent history. It preserves the Copilot shell first, read-only readiness before mutation, and Manager-preferred install direction.
- `archive/comfywatchman-pre-copilot-graft/`: Salvage source for scanner/readiness concepts. Treat as reference material, not active code.

## Landing Order

The path forward is clear enough to execute, but only if the next work lands in this order.

### PR 1: Local API Namespace Smoke

**Why first:** Every agentic workflow feature depends on knowing whether ComfyWatchman is talking to local ComfyUI, Desktop-managed local ComfyUI, or Comfy Cloud. Local truth must be proven before validating, editing, or enqueueing workflows.

**Files:**

- Modify: `backend/utils/comfy_gateway.py`
- Test: `tests/test_comfy_gateway_paths.py`
- Optional docs update: `docs/superpowers/plans/2026-06-21-comfyui-platform-control.md`

- [ ] **Step 1: Add failing path tests for local route mode**

Create `tests/test_comfy_gateway_paths.py`:

```python
from backend.utils.comfy_gateway import ComfyGateway


def test_local_route_mode_uses_unprefixed_comfy_routes():
    gateway = ComfyGateway(base_url="http://127.0.0.1:8000", route_mode="local")

    assert gateway.prompt_url == "http://127.0.0.1:8000/prompt"
    assert gateway.object_info_url() == "http://127.0.0.1:8000/object_info"
    assert gateway.object_info_url("CheckpointLoaderSimple") == "http://127.0.0.1:8000/object_info/CheckpointLoaderSimple"
    assert gateway.queue_url == "http://127.0.0.1:8000/queue"
    assert gateway.history_url("abc") == "http://127.0.0.1:8000/history/abc"


def test_cloud_route_mode_uses_api_prefixed_routes():
    gateway = ComfyGateway(base_url="https://cloud.comfy.org", route_mode="cloud")

    assert gateway.prompt_url == "https://cloud.comfy.org/api/prompt"
    assert gateway.object_info_url() == "https://cloud.comfy.org/api/object_info"
    assert gateway.object_info_url("CheckpointLoaderSimple") == "https://cloud.comfy.org/api/object_info/CheckpointLoaderSimple"
    assert gateway.queue_url == "https://cloud.comfy.org/api/queue"
    assert gateway.history_url("abc") == "https://cloud.comfy.org/api/history/abc"
```

- [ ] **Step 2: Run the focused test and confirm it fails**

```powershell
python -m pytest tests/test_comfy_gateway_paths.py -q
```

Expected before implementation: failure because `ComfyGateway.__init__` does not accept `route_mode` and URL helpers do not exist.

- [ ] **Step 3: Add explicit route mode helpers**

Modify `backend/utils/comfy_gateway.py` so `ComfyGateway.__init__` accepts `route_mode: str = "local"`, validates it against `{"local", "cloud"}`, and exposes URL helpers:

```python
def _route(self, path: str) -> str:
    prefix = "/api" if self.route_mode == "cloud" else ""
    return f"{self.base_url}{prefix}{path}"

@property
def prompt_url(self) -> str:
    return self._route("/prompt")

def object_info_url(self, node_class: Optional[str] = None) -> str:
    suffix = f"/{node_class}" if node_class else ""
    return self._route(f"/object_info{suffix}")

@property
def queue_url(self) -> str:
    return self._route("/queue")

def history_url(self, prompt_id: Optional[str] = None) -> str:
    suffix = f"/{prompt_id}" if prompt_id else ""
    return self._route(f"/history{suffix}")
```

Update existing methods to use `self.prompt_url`, `self.object_info_url(...)`, `self.queue_url`, and `self.history_url(...)`.

- [ ] **Step 4: Run focused and import checks**

```powershell
python -m pytest tests/test_comfy_gateway_paths.py -q
python -m compileall -q backend
```

Expected: both pass.

- [ ] **Step 5: Run live local smoke against the adopted Desktop install**

Install the custom node into the actual local base directory if it is not already present:

```powershell
if (-not (Test-Path "C:\COMFYUI\custom_nodes\ComfyWatchman")) {
  New-Item -ItemType Junction -Path "C:\COMFYUI\custom_nodes\ComfyWatchman" -Target "D:\_projects\ComfyUI\ComfyWatchman"
}
```

Install Python requirements into the adopted ComfyUI environment:

```powershell
& "C:\COMFYUI\.venv\Scripts\python.exe" -m pip install -r "D:\_projects\ComfyUI\ComfyWatchman\requirements.txt"
```

Start ComfyUI directly:

```powershell
Push-Location "C:\Users\pmacl\ComfyUI-Installs\ComfyUI\ComfyUI"
& "C:\COMFYUI\.venv\Scripts\python.exe" .\main.py --base-directory C:\COMFYUI --port 8000 --enable-manager
```

In another shell, verify:

```powershell
$base = "http://127.0.0.1:8000"
Invoke-WebRequest "$base/copilot_web/input.js" -UseBasicParsing
Invoke-RestMethod "$base/object_info/CheckpointLoaderSimple"
Invoke-RestMethod "$base/system_stats"
```

Expected: static asset returns HTTP 200, object info returns the `CheckpointLoaderSimple` definition, and `system_stats` returns system/device data.

- [ ] **Step 6: Commit**

```powershell
git add backend/utils/comfy_gateway.py tests/test_comfy_gateway_paths.py
git commit -m "fix: separate local and cloud comfy routes"
```

### PR 2: Frontend Extension Drift

**Why second:** Once the local server is reachable, the UI extension should align with the current frontend API before deeper agentic canvas controls are trusted.

**Files:**

- Modify: `entry/comfyui-bridge.js`
- Test: `ui` build output and live browser console smoke

- [ ] **Step 1: Replace context-menu monkey patch with migrated menu API**

In `entry/comfyui-bridge.js`, replace the `getExtraMenuOptions` wrapper with `getNodeMenuItems` support that preserves existing menu entries and appends the Copilot action:

```javascript
function addNodeMenuItems(nodeType) {
    const originalGetNodeMenuItems = nodeType.prototype.getNodeMenuItems;
    nodeType.prototype.getNodeMenuItems = function (...args) {
        const items = originalGetNodeMenuItems?.apply(this, args) ?? [];
        items.push({
            content: "Explain with Copilot",
            callback: async () => {
                const nodeTypeUniqueId = nodeType?.comfyClass;
                window.dispatchEvent(new CustomEvent(COPILOT_EVENTS.EXPLAIN_NODE, {
                    detail: { nodeType: nodeTypeUniqueId }
                }));
            }
        });
        return items;
    };
}
```

Update `beforeRegisterNodeDef` to call `addNodeMenuItems(nodeType)`.

- [ ] **Step 2: Build the frontend**

```powershell
Push-Location ui
npm ci
npm run build
Pop-Location
```

Expected: build passes. Existing chunk-size warnings are acceptable; syntax errors or missing imports are not.

- [ ] **Step 3: Smoke the live frontend**

With local ComfyUI running on port `8000`, open:

```text
http://127.0.0.1:8000/
```

Verify:

- Copilot sidebar tab appears.
- Selecting a node shows Copilot toolbox commands.
- The node context menu includes "Explain with Copilot".
- Browser console has no `getExtraMenuOptions` deprecation warnings caused by ComfyWatchman.

- [ ] **Step 4: Commit**

```powershell
git add entry/comfyui-bridge.js dist/copilot_web
git commit -m "fix: migrate copilot frontend menu hook"
```

### PR 3: Desktop Environment Discovery

**Why third:** Desktop can manage multiple local installs and Cloud entries. ComfyWatchman must discover the active instance and paths instead of hard-coding a single portable layout.

**Files:**

- Create: `backend/utils/desktop_environment.py`
- Test: `tests/test_desktop_environment.py`
- Modify if needed: `backend/controller/conversation_api.py`

- [ ] **Step 1: Add tests for Desktop config parsing**

Create `tests/test_desktop_environment.py`:

```python
import json

from backend.utils.desktop_environment import parse_desktop_installations


def test_parse_adopted_local_installation():
    payload = json.dumps([
        {
            "id": "inst-local",
            "name": "ComfyUI",
            "sourceId": "standalone",
            "installPath": r"C:\Users\pmacl\ComfyUI-Installs\ComfyUI",
            "adoptedBaseDir": r"C:\COMFYUI",
            "adoptedPythonPath": r"C:\COMFYUI\.venv\Scripts\python.exe",
            "launchArgs": "--port 8000 --enable-manager",
            "inputDir": r"C:\COMFYUI\input",
            "outputDir": r"C:\COMFYUI\output",
            "useSharedModels": True,
            "status": "installed",
        }
    ])

    installs = parse_desktop_installations(payload)

    assert len(installs) == 1
    assert installs[0].kind == "local"
    assert installs[0].base_dir == r"C:\COMFYUI"
    assert installs[0].python_path == r"C:\COMFYUI\.venv\Scripts\python.exe"
    assert installs[0].port == 8000


def test_parse_cloud_installation():
    payload = json.dumps([
        {
            "id": "inst-cloud",
            "name": "Comfy Cloud",
            "sourceId": "cloud",
            "remoteUrl": "https://cloud.comfy.org/",
            "status": "installed",
        }
    ])

    installs = parse_desktop_installations(payload)

    assert installs[0].kind == "cloud"
    assert installs[0].remote_url == "https://cloud.comfy.org/"
```

- [ ] **Step 2: Implement parser**

Create `backend/utils/desktop_environment.py` with a small dataclass-based parser. It should not import Electron/Desktop internals; it only parses JSON if a caller provides it.

```python
from dataclasses import dataclass
import json
import re
from typing import Optional


@dataclass(frozen=True)
class ComfyDesktopInstall:
    id: str
    name: str
    kind: str
    base_dir: Optional[str] = None
    install_path: Optional[str] = None
    python_path: Optional[str] = None
    port: Optional[int] = None
    input_dir: Optional[str] = None
    output_dir: Optional[str] = None
    remote_url: Optional[str] = None


def _port_from_launch_args(launch_args: str | None) -> Optional[int]:
    if not launch_args:
        return None
    match = re.search(r"--port\s+(\d+)", launch_args)
    return int(match.group(1)) if match else None


def parse_desktop_installations(raw_json: str) -> list[ComfyDesktopInstall]:
    records = json.loads(raw_json)
    installs: list[ComfyDesktopInstall] = []
    for record in records:
        source_id = record.get("sourceId")
        if source_id == "cloud":
            installs.append(ComfyDesktopInstall(
                id=record["id"],
                name=record.get("name", "Comfy Cloud"),
                kind="cloud",
                remote_url=record.get("remoteUrl"),
            ))
            continue

        installs.append(ComfyDesktopInstall(
            id=record["id"],
            name=record.get("name", "ComfyUI"),
            kind="local",
            base_dir=record.get("adoptedBaseDir"),
            install_path=record.get("installPath"),
            python_path=record.get("adoptedPythonPath"),
            port=_port_from_launch_args(record.get("launchArgs")),
            input_dir=record.get("inputDir"),
            output_dir=record.get("outputDir"),
        ))
    return installs
```

- [ ] **Step 3: Run parser tests**

```powershell
python -m pytest tests/test_desktop_environment.py -q
python -m compileall -q backend
```

Expected: both pass.

- [ ] **Step 4: Add read-only endpoint if UI needs it**

If the UI needs environment display, add a read-only route such as `/api/comfy-environment` in `backend/controller/conversation_api.py` that returns:

```json
{
  "kind": "local",
  "base_dir": "C:\\COMFYUI",
  "port": 8000,
  "input_dir": "C:\\COMFYUI\\input",
  "output_dir": "C:\\COMFYUI\\output",
  "cloud_available": true
}
```

Do not expose API keys, tokens, absolute provider credentials, or Desktop updater internals.

- [ ] **Step 5: Commit**

```powershell
git add backend/utils/desktop_environment.py tests/test_desktop_environment.py
git commit -m "feat: discover comfy desktop environments"
```

### PR 4: Registry And Manager Metadata

**Why fourth:** Before restoring install/readiness behavior, decide what this package is called and how Manager should identify it.

**Files:**

- Modify: `pyproject.toml`
- Create or modify: `node_list.json` if Registry publishing requires node metadata for this extension package
- Modify: `.github/workflows/publish.yml`
- Test: metadata lint and GitHub Actions dry inspection

- [ ] **Step 1: Choose identity**

Use `ComfyWatchman` if this repository owns the product direction. Use `ComfyUI-Copilot` only if the repo is intentionally a rebranded donor fork.

Recommended active identity:

```toml
[project]
name = "ComfyWatchman"
description = "Local ComfyUI assistant and readiness copilot."
version = "3.0.0"
license = {file = "LICENSE"}

[project.urls]
Repository = "https://github.com/Coldaine/ComfyWatchman"

[tool.comfy]
PublisherId = "coldaine"
DisplayName = "ComfyWatchman"
Icon = ""
```

- [ ] **Step 2: Verify publish workflow owner guard**

Inspect:

```powershell
Get-Content .github\workflows\publish.yml
```

Expected owner guard: publishing only runs for the intended repository owner and not donor forks.

- [ ] **Step 3: Validate metadata**

```powershell
python -m pip install build
python -m build --wheel
```

Expected: wheel metadata builds and contains the chosen project name and repository URL.

- [ ] **Step 4: Commit**

```powershell
git add pyproject.toml .github/workflows/publish.yml node_list.json
git commit -m "chore: align manager metadata with comfywatchman"
```

### PR 5: Read-Only Readiness Tools

**Why fifth:** The user's desired agentic workflow builder needs node, model, and dependency awareness before it is allowed to mutate workflows or install anything.

**Files:**

- Create: `backend/service/readiness_inventory.py`
- Create: `tests/test_readiness_inventory.py`
- Modify: `backend/controller/conversation_api.py`
- Reference only: `archive/comfywatchman-pre-copilot-graft/`

- [ ] **Step 1: Add tests for tiny embedding validity**

Create `tests/test_readiness_inventory.py`:

```python
from backend.service.readiness_inventory import classify_model_file


def test_tiny_embedding_files_are_valid_assets():
    result = classify_model_file(
        folder="embeddings",
        filename="style.pt",
        size_bytes=524_288,
    )

    assert result.is_valid is True
    assert result.reason == "embedding assets may be small"


def test_checkpoint_files_need_large_model_size():
    result = classify_model_file(
        folder="checkpoints",
        filename="tiny.safetensors",
        size_bytes=524_288,
    )

    assert result.is_valid is False
    assert result.reason == "checkpoint is below minimum size"
```

- [ ] **Step 2: Implement read-only classifier**

Create `backend/service/readiness_inventory.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelFileClassification:
    folder: str
    filename: str
    size_bytes: int
    is_valid: bool
    reason: str


MIN_LARGE_MODEL_BYTES = 10 * 1024 * 1024
SMALL_ASSET_REASONS = {
    "embeddings": "embedding assets may be small",
    "loras": "lora assets may be small",
    "controlnet_aux": "controlnet_aux assets may be small",
    "vae_approx": "vae_approx assets may be small",
}


def classify_model_file(folder: str, filename: str, size_bytes: int) -> ModelFileClassification:
    normalized_folder = folder.lower()
    if normalized_folder in SMALL_ASSET_REASONS:
        return ModelFileClassification(folder, filename, size_bytes, True, SMALL_ASSET_REASONS[normalized_folder])
    if size_bytes < MIN_LARGE_MODEL_BYTES:
        return ModelFileClassification(folder, filename, size_bytes, False, f"{normalized_folder.rstrip('s')} is below minimum size")
    return ModelFileClassification(folder, filename, size_bytes, True, "large model size is plausible")
```

- [ ] **Step 3: Add read-only inventory endpoint**

Add a route named `/api/readiness/inventory` that reads installed ComfyUI models and node classes without downloading, installing, moving, or deleting files.

Expected response shape:

```json
{
  "nodes": {
    "count": 350,
    "source": "/object_info"
  },
  "models": {
    "embeddings": [
      {
        "filename": "style.pt",
        "is_valid": true,
        "reason": "embedding assets may be small"
      }
    ]
  },
  "mutations_allowed": false
}
```

- [ ] **Step 4: Run tests**

```powershell
python -m pytest tests/test_readiness_inventory.py -q
python -m compileall -q backend
```

Expected: both pass.

- [ ] **Step 5: Commit**

```powershell
git add backend/service/readiness_inventory.py tests/test_readiness_inventory.py backend/controller/conversation_api.py
git commit -m "feat: add read-only readiness inventory"
```

### PR 6: Agentic Workflow Control Proof

**Why sixth:** Only after local API, frontend drift, environment discovery, metadata, and read-only readiness are stable should the tool connect nodes and fill fields.

**Files:**

- Modify: `backend/service/agent_mode_tools.py`
- Modify: `backend/service/agent_mode.py`
- Test: `tests/test_agent_mode_workflow_tools.py`

- [ ] **Step 1: Add tests for workflow graph editing without execution**

Create `tests/test_agent_mode_workflow_tools.py`:

```python
from backend.service.agent_mode_tools import WorkflowDraft


def test_workflow_draft_connects_node_outputs_to_inputs():
    draft = WorkflowDraft()

    checkpoint = draft.add_node("CheckpointLoaderSimple", {"ckpt_name": "model.safetensors"})
    sampler = draft.add_node("KSampler", {"steps": 20, "cfg": 7.0})
    draft.connect(checkpoint, "MODEL", sampler, "model")

    api = draft.to_api_prompt()

    assert api[str(sampler)]["inputs"]["model"] == [str(checkpoint), 0]


def test_workflow_draft_refuses_unknown_required_fields():
    draft = WorkflowDraft()

    try:
        draft.add_node("EmptyLatentImage", {"width": 512})
    except ValueError as exc:
        assert "missing required input" in str(exc)
    else:
        raise AssertionError("expected missing required input error")
```

- [ ] **Step 2: Implement draft-only graph operations**

Implement a `WorkflowDraft` that builds a Comfy API prompt JSON object from `/object_info`-validated node schemas. It must not call `/prompt`.

Required operations:

- `add_node(class_type, inputs) -> node_id`
- `set_input(node_id, input_name, value) -> None`
- `connect(source_id, source_output_name, target_id, target_input_name) -> None`
- `to_api_prompt() -> dict`
- `validate_required_inputs() -> list[str]`

- [ ] **Step 3: Add explicit execution gate**

In `backend/service/agent_mode.py`, keep draft mutation separate from queue execution. A draft can be saved and restored, but `/prompt` must require an explicit user confirmation flag such as:

```json
{
  "session_id": "abc",
  "confirmed_execution": true
}
```

If `confirmed_execution` is false or absent, return the draft and validation report without enqueueing.

- [ ] **Step 4: Run tests**

```powershell
python -m pytest tests/test_agent_mode_workflow_tools.py -q
python -m compileall -q backend
```

Expected: both pass.

- [ ] **Step 5: Live proof**

With ComfyUI running on port `8000`, ask Agent Mode to build a tiny draft:

```text
Create a 64x64 latent image workflow draft. Do not execute it.
```

Expected:

- The workflow draft is visible in ComfyWatchman state.
- No prompt appears in `/queue`.
- The draft can be restored through `/api/restore-workflow-checkpoint`.

- [ ] **Step 6: Commit**

```powershell
git add backend/service/agent_mode_tools.py backend/service/agent_mode.py tests/test_agent_mode_workflow_tools.py
git commit -m "feat: draft comfy workflows without execution"
```

## Explicit Non-Goals Until The Above Lands

- Do not treat Comfy Cloud success as proof that the local extension works.
- Do not install missing models or custom nodes directly from Agent Mode.
- Do not use `/prompt` as a dry-run validator.
- Do not hand-roll LiteGraph link objects in frontend code; use ComfyUI/LiteGraph APIs when frontend graph edits become necessary.
- Do not depend on a single Desktop path such as `C:\Users\pmacl\AppData\Local\Programs\ComfyUI\resources\ComfyUI`.

## Readiness Definition

The repository is ready to push into full agentic workflow stitching when all of these are true:

- Local ComfyUI smoke passes on the adopted Desktop install at port `8000`.
- ComfyWatchman static UI loads from `/copilot_web/input.js`.
- `/object_info`, `/system_stats`, `/queue`, and `/history` are called with local paths in local mode.
- Cloud calls are isolated behind a Cloud route mode and use explicit API-key handling.
- The frontend bridge uses current ComfyUI extension APIs.
- The package identity and Manager metadata match the repository owner and product name.
- Read-only readiness inventory reports nodes, models, and small valid assets without mutation.
- Agent Mode can build, connect, fill, save, and restore a workflow draft without enqueueing execution.
- Execution requires explicit confirmation and leaves an auditable checkpoint.
