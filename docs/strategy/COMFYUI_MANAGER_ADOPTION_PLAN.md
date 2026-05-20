# ComfyUI-Manager Adoption Plan

This is the focused follow-up to `COMFY_MCP_DONOR_EVALUATION.md`. The previous donor pass was too MCP-centered. For the actual "make Comfy setup painless" problem, `Comfy-Org/ComfyUI-Manager` is the primary donor.

## Decision

ComfyWatchman should become Manager-aware before it becomes MCP-heavy.

The practical target is:

1. Discover whether ComfyUI-Manager is installed and usable.
2. Read Manager's custom-node, model, snapshot, channel, security, and userdata state.
3. Produce dry-run install plans that prefer Manager-compatible actions.
4. Execute only approved actions through Manager APIs or `cm-cli` when possible.
5. Fall back to ComfyWatchman-native downloads only when Manager cannot represent the operation.

## Why Manager First

Manager is the way Comfy users actually manage Comfy installs. It already owns many hard parts ComfyWatchman was drifting toward reinventing:

- custom-node install, reinstall, uninstall, update, disable, enable, and dependency fix
- model install catalogs and model target path resolution
- channel/local/cache/remote metadata modes
- CNR and Registry-aware node package resolution
- installed-node inventory, invalid-node detection, enabled/disabled state
- snapshots and restore scheduling
- Manager userdata paths and V3.38 security migration
- security-level gates for risky actions
- `cm-cli` for command-line usage without the Comfy web UI
- `extra_model_paths.yaml` and Comfy `folder_paths` integration

ComfyWatchman should not pretend a git clone plus a model download is the correct default. The default should be: if Manager can do it safely and visibly, plan for Manager to do it.

## Observed Manager Surfaces

These were inspected from `D:\_research\comfy-remote-repos\donor-eval\ComfyUI-Manager`.

### API

`openapi.yaml` describes programmatic access for node management, model downloading, snapshots, queue operations, and configuration.

Relevant routes:

| Route | Use |
| --- | --- |
| `/customnode/getmappings` | Node class to node package mapping. Critical for missing-node resolution. |
| `/customnode/installed` | Installed custom node packages. |
| `/customnode/getlist` | Available custom nodes from selected DB mode/channel. |
| `/customnode/alternatives` | Alternative node options. |
| `/customnode/versions/{node_name}` | Available versions for a node package. |
| `/customnode/import_fail_info` | Why a node failed to import. |
| `/externalmodel/getlist` | Manager model catalog with installed-state annotation. |
| `/manager/queue/install` | Queue custom-node install. |
| `/manager/queue/install_model` | Queue model install. |
| `/manager/queue/reinstall` | Queue reinstall. |
| `/manager/queue/uninstall` | Queue uninstall. |
| `/manager/queue/update` and `/manager/queue/update_all` | Queue updates. |
| `/manager/queue/disable` | Disable a custom node without deleting it. |
| `/manager/queue/fix` | Fix dependencies for a custom node. |
| `/manager/queue/status` | Track Manager task queue. |
| `/manager/queue/start` | Start queued Manager work. |
| `/snapshot/get_current` | Current Manager snapshot. |
| `/snapshot/save` | Save current snapshot. |
| `/snapshot/restore` | Schedule snapshot restore. |
| `/snapshot/getlist` | List snapshots. |
| `/manager/db_mode` | Get/set DB mode. |
| `/manager/channel_url_list` | Get/set channel list. |
| `/manager/version` | Manager version. |

### CLI

`cm-cli.py` and `docs/en/cm-cli.md` expose Manager functions without launching ComfyUI:

```text
install|reinstall|uninstall|update|disable|enable|fix node_name ...
update|disable|enable|fix all
show|simple-show installed|enabled|not-installed|disabled|all|snapshot|snapshot-list
save-snapshot
restore-snapshot
cli-only-mode enable|disable
restore-dependencies
clear
```

Important constraints:

- Must run in the same Python environment as ComfyUI.
- `COMFYUI_PATH` can point to the ComfyUI install.
- `--channel` and `--mode` choose metadata source.
- `--user-directory` can select Manager userdata.
- `--restore-to` can target a custom node path during snapshot restore.

### Manager State Paths

V3.38 moved Manager config/data to protected userdata paths:

- Current config path: `<ComfyUI user directory>/__manager/config.ini`
- Current snapshots path: `<ComfyUI user directory>/__manager/snapshots/`
- Startup scripts: `<ComfyUI user directory>/__manager/startup-scripts/`
- Channels: `<ComfyUI user directory>/__manager/channels.list`
- Cache: `<ComfyUI user directory>/__manager/cache/`
- Legacy backup: `<ComfyUI user directory>/__manager/.legacy-manager-backup/`

ComfyWatchman environment discovery must inspect this state. It should not rely only on `ComfyUI/custom_nodes`.

### Security Model

Manager has security levels:

- `strong`: ComfyUI update only; most installs blocked.
- `normal`: registered custom nodes and models.
- `normal-`: above plus Git URL or pip on localhost.
- `weak`: broad operations, intended only for isolated development.

Manager also has specific blocks for risky installs, non-registered pip packages, remote use, and old ComfyUI versions without the System User Protection API. ComfyWatchman should surface these blocks as plan constraints instead of trying to work around them.

### Model Targeting

Manager's model install route is not just "download to models":

- `download_model_base` from `extra_model_paths.yaml` can redirect model downloads.
- `folder_paths.folder_names_and_paths` is used for known model folders.
- Manager maps model types such as checkpoints, lora, vae, text_encoders, controlnet, clip_vision, embeddings, diffusion_models, and upscale_models.
- `save_path` can target custom-node-owned model paths.
- filenames are guarded against path traversal.
- Hugging Face repo downloads and direct URL downloads use different paths.
- `COMFYUI_MANAGER_ARIA2_SERVER`, `HF_ENDPOINT`, and `model_download_by_agent` influence download behavior.

ComfyWatchman should treat Manager's path resolution as a reference implementation when building install plans.

## What ComfyWatchman Should Build

### 1. Manager Discovery

Add discovery that answers:

- Is Manager installed under any configured `custom_nodes` path?
- Is Manager active in the running ComfyUI server?
- What Manager version is active?
- Is the OpenAPI route set available?
- Is `cm-cli.py` available on disk?
- What Python executable/environment should be used for `cm-cli`?
- What is the Comfy user directory?
- Where is `__manager`?
- What is the configured security level?
- What DB mode and channel are active?
- Are there legacy backup or migration warnings?

### 2. Manager Client

Add a read-first Manager client:

- `get_version()`
- `get_security_state()`
- `get_installed_nodes()`
- `get_node_mappings()`
- `get_available_nodes(mode, channel)`
- `get_external_models(mode)`
- `get_queue_status()`
- `get_current_snapshot()`
- `list_snapshots()`

Mutation calls should exist only behind an approved plan:

- `save_snapshot()`
- `queue_install_node()`
- `queue_fix_node()`
- `queue_install_model()`
- `queue_start()`

### 3. Manager-Aware Readiness Plan

Readiness plan entries should choose an execution strategy:

| Need | Preferred Strategy |
| --- | --- |
| Missing custom node with Manager mapping | Manager queue install by node package ID. |
| Missing custom node with multiple alternatives | Plan alternatives, require operator selection. |
| Broken installed custom node | Manager queue fix or reinstall. |
| Disabled custom node | Manager queue enable. |
| Missing model in Manager model catalog | Manager queue install model. |
| Missing model not in Manager catalog | ComfyWatchman candidate search with explicit target folder and approval. |
| Risky Git URL or pip install | Surface Manager security block; require explicit security decision. |
| Before mutation | Save or reference Manager snapshot. |

### 4. Native Fallbacks

ComfyWatchman-native downloads and installs still matter, but only as fallbacks:

- exact Civitai model version download
- Hugging Face file download not represented by Manager
- DirectID known-model lookup
- Qwen/web-assisted candidate search
- local wrong-folder detection and move/copy plan
- custom-node instructions that Manager cannot install

Fallback actions must include why Manager was not used.

## Implementation Order

1. Add fixtures representing Manager API responses and Manager userdata layout.
2. Add environment discovery for Manager install path, active route availability, `__manager`, snapshots, and `cm-cli`.
3. Add a read-only `ManagerClient`.
4. Add Manager state to the readiness report schema.
5. Map missing node classes to Manager node packages using `/customnode/getmappings`.
6. Map Manager model catalog entries to missing model references using `/externalmodel/getlist`.
7. Emit dry-run plan entries with `execution_backend = manager_api`, `manager_cli`, or `comfywatchman_native`.
8. Add snapshot-before-mutation behavior to the plan.
9. Add approved Manager API execution.
10. Add `cm-cli` execution fallback for cases where ComfyUI is not running but Manager exists on disk.

## Non-Goals

- Do not vendor ComfyUI-Manager.
- Do not bypass Manager security levels.
- Do not silently change Manager DB mode, channel, or security level.
- Do not execute Manager queue operations without a dry-run plan and approval.
- Do not replace Civitai/Hugging Face resolver logic with Manager metadata alone.

## Immediate Code Targets

Likely new modules:

- `src/comfywatchman/environment.py`
- `src/comfywatchman/comfy_client.py`
- `src/comfywatchman/manager_client.py`
- `src/comfywatchman/readiness.py`
- `src/comfywatchman/install_plan.py`

Likely tests:

- `tests/test_manager_discovery.py`
- `tests/test_manager_client.py`
- `tests/test_manager_readiness_plan.py`
- `tests/test_manager_fallbacks.py`

## Open Questions

- Is Manager installed on the user's active ComfyUI instance, and where?
- Does the active ComfyUI expose Manager routes, or should ComfyWatchman use `cm-cli` first?
- Which DB mode should ComfyWatchman read by default: Manager's active config, cache, remote, or local?
- Should ComfyWatchman ever request changing Manager security level, or only explain the blocker?
- Should ComfyWatchman save snapshots automatically as part of approved mutations, or require a separate approval?

