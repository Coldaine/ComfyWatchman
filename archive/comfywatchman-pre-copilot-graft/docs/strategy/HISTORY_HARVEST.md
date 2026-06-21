# ComfyWatchman History Harvest

Date: 2026-05-27

## Purpose

This document preserves the useful product intent, repo archaeology, and
subagent findings before the Copilot root graft. It is intentionally concise:
the goal is to carry the hard-won context forward after the current
ComfyWatchman tree is archived and the Copilot-derived shell becomes the active
root.

## Bottom Line

The current repo history is worth preserving for product intent and dependency
readiness knowledge, not because the current ComfyWatchman app shell should stay
primary.

The forward product shape is:

- Copilot-derived shell for the ComfyUI-native assistant UI, canvas context,
  workflow generation, debugging, rewriting, saving, and execution loop.
- PR #130 / `vehoelite` Agent Mode work as the local-provider and autonomous
  tool-loop starting point.
- ComfyWatchman as the readiness/dependency engine grafted back in through
  local tools: scan, inventory, search, readiness report, and install planning.
- ComfyUI-Manager as the preferred operational substrate for installs,
  snapshots, and safety where available.

## Worth Saving

| Area | Why it matters | Where it showed up | Forward destination |
| --- | --- | --- | --- |
| Prompt-to-workflow intent | The recurring desired loop is: ask for a workflow, inspect current canvas/state, generate or modify it, then save/validate/execute. | PR #16, `docs/strategy/COPILOT_LOCAL_FIRST_EVALUATION_PLAN.md`, `docs/strategy/COPILOT_INVESTIGATION_SPIKE_FINDINGS.md` | Copilot shell |
| Dependency readiness engine | This is the strongest ComfyWatchman-native value: scan workflows, inventory local models, detect missing dependencies, and report readiness before execution. | `src/comfywatchman/scanner.py`, `src/comfywatchman/inventory.py`, PR #12, strategy docs | Copilot tools |
| Multi-backend model search | The project repeatedly pushed beyond one API call: Civitai, HuggingFace, Qwen, direct-ID lookup, fuzzy matching, diagnostics, and confidence/uncertainty handling. | PR #5, PR #7, `src/comfywatchman/search.py`, `docs/phase2/AGENTIC_SEARCH_DESIGN.md` | Copilot readiness/search tool |
| Embeddings edge case | Real user pain: valid tiny embeddings were filtered by the global `min_model_size`, causing false missing-model warnings. | Issue #4 | First-class readiness bug to preserve |
| Safe metadata inspector | Inspecting model metadata without loading huge tensors is useful for classification and readiness. | PR #3, inspector package | Optional readiness tool |
| Download safety | The repo should not store model weights; downloads must target ComfyUI model paths and fail fast when roots are unknown. | PR #1 | Install planning and safety policy |
| Approval-first mutation | Multiple docs converge on read first, dry-run plan second, explicit approval before downloads/installs/execution. | Manager plan, Copilot plan, phase docs | Product invariant |
| Manager-aware operations | Use Manager for snapshots, installs, and safer mutations rather than reinventing everything. | `docs/strategy/COMFYUI_MANAGER_ADOPTION_PLAN.md` | Operational backend |
| Dashboard concepts | The mock dashboard is not the product shell, but concepts such as readiness review, search workbench, queue ops, graph studio, and dependency views are useful. | PR #13, `frontend/comfywatchman-dashboard` | Design reference |
| Workflow schemas/templates | Deferred owner workflow schemas may become future Copilot templates or examples. | PR #8, `docs/phase2/WORKFLOW_SCHEMAS.md` | Archive/reference unless promoted |

## Not Worth Preserving as Current Direction

| Area | Decision | Reason |
| --- | --- | --- |
| Current ComfyWatchman app shell | Archive | Copilot already owns the ComfyUI-native chat/canvas/runtime surface. |
| Mock dashboard implementation | Reference only | It is mock-backed and should not compete with the Copilot shell. |
| PR #2 inspector attempt | Superseded | PR #3 provided the better architecture and preserved useful project assets. |
| PR #7 branch state | Mine ideas only | It diverged heavily, conflicted with main, and was closed stale. |
| PR #14 README audit | Superseded | PR #15 replaced it with a deeper code-first README audit. |
| Phase 0-3 docs as active plans | Archive/provenance | They explain evolution, but newer strategy docs supersede their product direction. |
| Script-first downloader direction | Archive/provenance | Future integration should be tool/API-first behind Copilot. |
| LangGraph/native-agent shell plans | Defer/archive | Useful history, but likely obsolete if Copilot PR #130 becomes the shell. |

## PR and Issue Timeline Signals

- PR #1: established repo hygiene and model-download safety boundaries.
- PR #3: established the safe model metadata inspector direction.
- Issue #4: captured the embeddings-size false-negative problem.
- PR #5: added the core multi-backend Civitai/search/downloader architecture.
- PR #7: contains useful search/download/scheduler ideas, but is not a clean
  merge source.
- PR #8: explicitly deferred owner workflow schemas so they are not forgotten.
- PR #10 / issue #9: moved the project toward `uv`, Python 3.12+, and dependency
  cleanup.
- PR #12: created the first meaningful scanner/config test baseline.
- PR #13: restored the mock dashboard and added strategy docs that elevated the
  Copilot-local-first path.
- PR #15: made README truth line up with current code.
- PR #16: records the Copilot investigation spike and recommends Copilot as the
  product shell with ComfyWatchman as dependency/readiness tooling.

## Carry-Forward Requirements

- Preserve local-first operation as a product principle, not a nice-to-have.
- Treat hosted services as optional/provider-specific, not the foundation.
- Keep validation/readiness read-only until the user approves mutation.
- Distinguish true dry-run validation from ComfyUI `/api/prompt` execution.
- Keep model paths environment-derived; do not assume a fixed ComfyUI layout.
- Prefer Manager for install/snapshot/security operations when available.
- Keep provenance for donor code and pre-graft ComfyWatchman history.

## First Salvage Candidates After the Graft

1. `scan_workflow_dependencies`: extract from the workflow scanner.
2. `inventory_local_models`: extract from the model inventory.
3. `readiness_report`: combine scan + inventory into a current-workflow report.
4. `search_missing_model`: expose Civitai/Qwen/direct-ID search with confidence.
5. `plan_install`: produce an approval-first install plan; do not download yet.
6. `inspect_model_metadata`: optional classifier/metadata helper.

## Archive Policy

After the Copilot root graft, the old ComfyWatchman tree should be archived under
`archive/comfywatchman-pre-copilot-graft/`. That archive is not the product
surface. It is a mine for salvage and provenance. Pull useful pieces forward in
small PRs, then delete or compress archive material once it has been drained.

