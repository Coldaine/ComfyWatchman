# Comfy MCP Donor Evaluation

This note evaluates existing ComfyUI MCP and harness projects as donor systems for ComfyWatchman. The purpose is to move faster by reusing proven surface design and runtime patterns without losing ComfyWatchman's core value: evidence-backed readiness and install planning for a real ComfyUI environment.

## Decision

Do not replace ComfyWatchman with any donor project wholesale.

Use the donors this way:

- `Comfy-Org/ComfyUI-Manager`: primary donor for custom-node and model installation, registry/channel metadata, snapshots, `cm-cli`, security/userdata path behavior, and real-world Comfy dependency management.
- `AIDC-AI/ComfyUI-Copilot`: primary donor for assistant-in-Comfy workflow generation, debugging, rewriting, parameter tuning, model recommendations, and node recommendations.
- `artokun/comfyui-mcp`: primary donor for MCP tool taxonomy, Comfy runtime operations, visualization, workflow conversion, queue/history/log/image handling, registry lookup, and node-pack skill generation.
- `joenorton/comfyui-mcp-server`: primary Python donor for FastMCP shape, streamable HTTP/stdio transport, job lifecycle, asset identity, provenance capture, and curated workflow templates.
- `AIDC-AI/Pixelle-MCP`: donor for turning known-good Comfy API workflows into callable MCP tools, media output normalization, and optional workflow annotation conventions.

Keep these ComfyWatchman-native:

- environment discovery
- workflow dependency extraction
- model and custom-node inventory
- Civitai, Hugging Face, DirectID, and Qwen-backed search
- evidence-backed dry-run install plans
- approval-first downloads and installs
- persistent readiness state
- operator dashboard truth model

## Correction: MCP Was Too Narrow

The first donor pass was too narrow because it searched mainly for MCP-branded Comfy projects. That missed the largest and most operationally important Comfy setup donor: `Comfy-Org/ComfyUI-Manager`.

Current GitHub metadata checked on 2026-05-20:

| Project | Stars | Forks | Last Push | Why It Matters |
| --- | ---: | ---: | --- | --- |
| `Comfy-Org/ComfyUI-Manager` | 14,720 | 2,210 | 2026-05-19 | The dominant install/update/enable/disable manager for custom nodes, model installs, channels, snapshots, userdata migration, and `cm-cli`. |
| `AIDC-AI/ComfyUI-Copilot` | 5,167 | 329 | 2026-04-07 | The large assistant-in-Comfy project for workflow generation, debugging, rewriting, parameter tuning, node/model recommendations, and local environment-aware help. |
| `AIDC-AI/Pixelle-MCP` | 1,017 | 136 | 2025-12-17 | Workflow-as-MCP-tool and multimodal execution platform. |
| `joenorton/comfyui-mcp-server` | 317 | 65 | 2026-02-17 | Pragmatic Python FastMCP execution/control-loop donor. |
| `artokun/comfyui-mcp` | 96 | 20 | 2026-05-18 | Broad MCP runtime harness and Claude Code plugin donor. |

This changes the plan: ComfyWatchman should not only borrow MCP patterns. It should also treat ComfyUI-Manager as the reference implementation for how Comfy users actually install, update, snapshot, and reason about custom nodes and model catalogs.

## Why This Split

The donors have already done much of the MCP and Comfy runtime work. They expose workflows, submit prompts, poll history, fetch images, manage queues, and make AI-assistant surfaces feel natural. ComfyWatchman should not spend months rediscovering those interfaces.

They do not solve the harder local-readiness problem. None of the reviewed donors produces a rigorous plan that says: this workflow needs these exact model files and custom nodes, this local Comfy install has or lacks them, these candidate downloads match with this evidence, and these approved actions will make the workflow runnable.

That is ComfyWatchman's product center.

## Donor Summary

| Donor | Best Use | Do Not Use For |
| --- | --- | --- |
| `Comfy-Org/ComfyUI-Manager` | Custom-node install/update/remove/disable/enable flows, Manager channel/cache/local DB behavior, model installer UI concepts, snapshot and restore semantics, `extra_model_paths.yaml` handling, `cm-cli`, security migration/userdata paths. | LLM workflow reasoning, evidence-backed model candidate scoring, ComfyWatchman's approval ledger, or direct unreviewed mutation. |
| `AIDC-AI/ComfyUI-Copilot` | Assistant UX inside Comfy, workflow generation/debug/rewrite/parameter tuning, node/model recommendations, selected-node context, local environment-aware agent patterns. | Stable backend dependency truth, because its hosted API service has been suspended and its own README points users to bring their own API key/base URL for agent features. |
| `artokun/comfyui-mcp` | Broad MCP runtime harness, Comfy API client patterns, workflow visualization/conversion, queue/history/log/image/upload tools, Registry search, generated node-pack skills, plugin packaging. | Resolver core, approval model, install planning, tests, security posture, or direct process-control exposure without guardrails. |
| `joenorton/comfyui-mcp-server` | Python FastMCP implementation, streamable HTTP/stdio transport, prompt polling, asset registry, provenance snapshots, curated parameterized workflow templates. | Deep dependency scanning, model inventory beyond checkpoints, model downloads, custom-node install, readiness dashboard. |
| `AIDC-AI/Pixelle-MCP` | Workflow-as-MCP-tool conversion, local/cloud executor abstraction, media output classification, optional parameter DSL for known workflows. | Comfy environment discovery, dependency resolution, model search/download, local-first readiness planning. |

## Feature Adoption Matrix

| Feature | Donor Evidence | ComfyWatchman Target | Action |
| --- | --- | --- | --- |
| Custom-node install/update/remove | `ComfyUI-Manager` is the dominant custom-node manager and supports install, remove, disable, enable, updates, channel DB modes, conflict surfacing, and Manager-recognized install paths. | Missing custom-node plans should produce Manager-compatible install/update actions where possible, not hand-rolled git clone commands first. | Adopt as primary operational donor. |
| Model install catalogs | `ComfyUI-Manager` has an install models surface and channel/local/remote DB behavior. | Model candidates should include Manager/Registry/catalog evidence alongside Civitai/HF evidence when available. | Adopt metadata paths, keep ComfyWatchman scoring. |
| Snapshots and rollback | `ComfyUI-Manager` has snapshot save/restore semantics and startup restore scripts. | Before mutation, ComfyWatchman should understand whether a Manager snapshot exists and offer snapshot-before-install behavior. | Adopt concept for safety model. |
| `cm-cli` | `ComfyUI-Manager` ships command-line tooling for power users. | Prefer calling or matching Manager-supported commands for node management when present, instead of inventing a parallel installer. | Investigate and wrap where safe. |
| Manager security/userdata paths | `ComfyUI-Manager` V3.38 moved Manager data into protected user paths and documents current path rules. | Environment discovery must inspect current Manager/userdata paths rather than assuming old `custom_nodes` local state is complete. | Adopt path rules. |
| Assistant-in-Comfy workflow help | `ComfyUI-Copilot` is the large donor for workflow generation, debugging, rewriting, parameter tuning, and selected-node recommendations. | ComfyWatchman should expose backend truth that such assistant surfaces can consume: missing deps, candidate fixes, executable plans, and verification results. | Mine UX/agent patterns, do not depend on suspended hosted service. |
| MCP server surface | `artokun` registers a large tool taxonomy; `joenorton` and `Pixelle` both use FastMCP-style callable tools. | Add a ComfyWatchman MCP facade with explicit tools for scan, readiness, plan, search, approve, download, queue, and execution. | Adopt pattern, implement native tools. |
| Transport | `joenorton` supports streamable HTTP at `/mcp` and stdio; `Pixelle` mounts MCP inside a web app. | Support stdio and HTTP so desktop clients, coding agents, and local services can use the same harness. | Adopt from Python donor. |
| Comfy API client | `artokun` covers queue, history, logs, prompt enqueue, image view/upload, VRAM, embeddings, and object info via `@stable-canvas/comfyui-client` plus REST; `joenorton` covers prompt/history/queue/view; `Pixelle` covers prompt/history/ws/upload/view. | Build `ComfyClient` with read-only truth routes first: `/system_stats`, `/object_info`, `/models` where available, `/queue`, `/history`, `/view`, `/upload/image`; add `/prompt` and `/ws` after plans exist. | Port concepts, not code wholesale. |
| Environment discovery | `artokun` probes common Desktop, manual, and home-directory paths plus ports 8188/8000. | Detect Desktop, portable, manual clone, `comfy-cli`, active server URL, model roots, `extra_model_paths.yaml`, custom nodes, workflows, OS path conventions. | Use donor path list as seed, expand substantially. |
| Workflow reader | `artokun` has UI-to-API conversion and workflow analysis; `Pixelle` converts API workflows into MCP tools; current ComfyWatchman scanner extracts model-like fields. | Normalize API prompt JSON, workflow JSON, legacy UI JSON, and PNG-embedded metadata into one dependency model. | Combine: keep ComfyWatchman scanner, add donor conversion ideas. |
| Workflow visualization | `artokun` has Mermaid and hierarchical visualization. | Render dependency and execution graphs for review, missing-node diagnosis, and dashboard drilldowns. | Adopt strongly. |
| Workflow composition | `artokun` has templates and graph patch operations; `Pixelle` does not synthesize workflows but wraps existing ones. | Later capability: curated templates and controlled graph edits after readiness planning is stable. | Defer, then port selectively. |
| Workflow-as-tool | `Pixelle` dynamically registers workflow files as MCP tools using title markers; `joenorton` exposes `PARAM_*` workflow templates. | Allow curated, known-good workflows to become callable tools with validated parameters and recorded provenance. | Adopt with validation, avoid unchecked dynamic `exec` style generation. |
| Dependency resolution | Donors have shallow or no model dependency resolution. `joenorton` only checks checkpoint names; `artokun` scans local folders and downloads direct URLs; `Pixelle` has no resolver. | Determine required model files, node classes, expected model folder, local status, ambiguity, and evidence. | Keep ComfyWatchman-native. |
| Model search | `artokun` searches Hugging Face and has Civitai-adjacent hash/generation metadata pieces. ComfyWatchman already has Civitai, Hugging Face, DirectID, ModelScope, and Qwen-oriented search pieces. | Search should produce candidates with source, filename, size/hash, confidence, rationale, target folder, and risk flags. | Use donor UX ideas only; keep native resolver. |
| Download/install | `artokun` downloads direct URLs to model subfolders. `joenorton` has no dependency install. `Pixelle` has no model install. | Downloads happen only after a dry-run install plan exists and a candidate is approved. Custom-node install is a separate approved operation. | Substitute with ComfyWatchman plan and state. |
| Queue/history/jobs | `artokun` and `joenorton` both have useful prompt IDs, queue state, polling, cancellation, and history snapshots. | Track execution and verification runs against readiness plans, with prompt IDs, outputs, history, and errors persisted. | Adopt strongly. |
| Asset identity | `joenorton` models assets as filename/subfolder/type and captures provenance; `Pixelle` normalizes media outputs. | Persist local output identity and provenance without relying on fragile URLs or public re-upload. | Adopt shape, keep local-first storage. |
| Image upload/output fetch | All donors have useful examples for `/upload/image` and `/view`. | Support img2img/inpaint/control inputs and reviewable outputs after planning. | Adopt. |
| Custom-node registry | `artokun` searches ComfyUI Registry and generates node-pack skills. | Use registry details as evidence for missing custom-node plans and reusable knowledge packs. | Adopt selectively. |
| Node-pack skill generation | `artokun` scans Registry/GitHub and live `/object_info` to emit `SKILL.md`. | Generate local knowledge packs for custom node packs only after verifying installed nodes and examples. | Adopt as a later knowledge-pack lane. |
| Process control | `artokun` can stop/start/restart ComfyUI. | Dangerous unless user explicitly enables local process management. | Defer behind explicit guardrails. |
| VRAM/memory tools | `artokun` has `/free`, system stats, and VRAM hooks. | Use for readiness warnings and scheduler/execution safety checks. | Adopt read-only first, mutation later. |
| Generation tracking | `artokun` logs sampler/model/LoRA settings to SQLite and suggests settings. | Useful later for optimization and "known good settings" history. | Defer until readiness core exists. |
| Publish/demo assets | `joenorton` can publish generated assets into web project directories. | Not central to ComfyWatchman. Could help demo-site assets later. | Ignore for core harness. |
| Cloud execution | `Pixelle` supports RunningHub cloud mode. | Local Comfy readiness is primary. Cloud can be optional adapter later. | Defer. |
| Tests | `artokun` builds but currently has no real test files; `Pixelle` has no tracked tests; `joenorton` has useful unit tests but local run needs dependencies. | Add fixture-based fake-Comfy tests before any ported behavior lands. | Do not inherit donor test gaps. |

## Recommended Backend Shape

ComfyWatchman should become a two-layer system:

1. Core readiness engine:
   - discovers Comfy environments
   - reads workflows
   - queries live Comfy truth
   - inventories local model and node state
   - resolves dependencies
   - produces dry-run install/readiness plans
   - persists approvals, attempts, failures, and evidence

2. MCP/runtime facade:
   - exposes the core as callable tools
   - submits approved workflows
   - tracks prompt IDs and outputs
   - fetches images and history
   - optionally wraps curated workflows as tools

The MCP facade should use donor ergonomics. The core should remain ComfyWatchman-specific.

## Implementation Sequence

1. Stabilize current ComfyWatchman imports, config loading, and planning-only startup.
2. Fix the existing orchestration bug where `_analyze_models()` returns node types but `run_workflow_analysis()` does not capture them.
3. Add fixture tests for scanner, inventory, missing model detection, missing custom-node detection, and no-network dry runs.
4. Evaluate `ComfyUI-Manager` internals first: channel DB, model DB, install APIs, `cm-cli`, snapshot files, userdata path migration, and `extra_model_paths.yaml` behavior.
5. Add `ComfyClient` read-only probes using donor route coverage as the checklist.
6. Add environment discovery with Desktop, portable, manual clone, `comfy-cli`, Manager userdata paths, `extra_model_paths.yaml`, and active server detection.
7. Split workflow reading by format and normalize into a dependency schema.
8. Produce a dry-run readiness/install plan before any downloads or installs.
9. Add Manager-aware custom-node and model install actions behind approval.
10. Add an MCP facade with explicit ComfyWatchman tools.
11. Add queue/history/output execution tools behind approved plans.
12. Add optional curated workflow-as-tool support using `PARAM_*` or Pixelle-style annotations.
13. Add visualization and registry-backed node-pack knowledge generation.

## Immediate Substitutions

Replace the stale "ComfyUI-Copilot complements this" framing with a donor-aware framing:

- Copilot is no longer the central assumption.
- MCP is the operating surface.
- Existing MCP donors provide mature assistant interaction patterns.
- ComfyWatchman's differentiation is readiness, dependency truth, and safe install execution.

Replace script-first downloads with plan-first installs:

- Current download code can remain as an execution backend.
- It should not be the product artifact.
- The product artifact is the install plan with evidence and approval state.

Replace hardcoded root assumptions with discovered environment state:

- Model roots come from the actual Comfy install and `extra_model_paths.yaml`.
- Workflow roots are explicit scan inputs.
- Custom nodes are separate from model files.
- Manager userdata and snapshot paths are first-class local state, not incidental files.

## Open Follow-Up

Review Manager and Copilot before implementing model-detection or install work:

- `Comfy-Org/ComfyUI-Manager`: `openapi.yaml`, `glob/manager_server.py`, `glob/manager_core.py`, `glob/manager_downloader.py`, `glob/node_package.py`, `cm-cli.py`, `docs/en/cm-cli.md`, and V3.38 userdata migration docs.
- `AIDC-AI/ComfyUI-Copilot`: backend agent/debug/rewrite services, model/node recommendation UI flows, and the service suspension notice.

Review active donor PRs before implementing model-detection work:

- `joenorton/comfyui-mcp-server` PR #15: multi-backend pool.
- `joenorton/comfyui-mcp-server` PR #17: enhanced model detection.

Those PRs may contain useful model-detection ideas, but they should still be measured against ComfyWatchman's stricter readiness-plan requirements.
