# ComfyWatchman History Harvest

Date: 2026-05-27

## Purpose

This is the carry-forward history note for the Copilot root graft. The full
pre-graft ComfyWatchman tree is archived at
`archive/comfywatchman-pre-copilot-graft/`; this document records what should be
mined from it and what should remain historical.

## Product Direction

- Copilot owns the active ComfyUI-native shell: assistant UI, canvas context,
  workflow generation, debugging, rewriting, saving, and execution loop.
- PR #130 / `vehoelite` Agent Mode is the starting point for local-provider and
  autonomous tool-loop behavior.
- ComfyWatchman becomes the readiness/dependency engine behind Copilot.
- ComfyUI-Manager should be preferred for installs, snapshots, and safety
  operations when available.

## Save First

| Candidate | Archived location | Intended Copilot tool |
| --- | --- | --- |
| Workflow dependency scanner | `archive/comfywatchman-pre-copilot-graft/src/comfywatchman/scanner.py` | `scan_workflow_dependencies` |
| Local model inventory | `archive/comfywatchman-pre-copilot-graft/src/comfywatchman/inventory.py` | `inventory_local_models` |
| Readiness report logic | `archive/comfywatchman-pre-copilot-graft/src/comfywatchman/core.py` and dashboard concepts | `readiness_report` |
| Multi-backend model search | `archive/comfywatchman-pre-copilot-graft/src/comfywatchman/search.py` | `search_missing_model` |
| Install/download planning | `archive/comfywatchman-pre-copilot-graft/src/comfywatchman/download.py` | `plan_install`, approval-first only |
| Safe metadata inspector | `archive/comfywatchman-pre-copilot-graft/src/comfywatchman/inspector/` | Optional `inspect_model_metadata` helper |

## Keep as Reference Only

- Old ComfyWatchman CLI/core shell. It is not the new product shell.
- Mock dashboard implementation. Keep its readiness/search/queue/graph concepts,
  not the standalone dashboard app.
- Scheduler, state manager, and direct download mutation flows until Copilot has
  explicit approval, rollback, and persistence contracts.
- Old Copilot adapter attempts that imported Copilot into ComfyWatchman; the new
  direction is Copilot shell first, ComfyWatchman tools second.
- Phase 0-3 planning docs as provenance, not current execution plans.

## Durable Product Lessons

- Local-first is a requirement, not an optimization.
- Readiness checks must be read-only until the user approves mutation.
- `validate_workflow` must not secretly enqueue `/api/prompt` execution.
- Model paths must be discovered from the real ComfyUI environment, including
  Manager userdata and `extra_model_paths.yaml`, not hard-coded.
- The embeddings-size bug from issue #4 is a real domain edge case: tiny
  embeddings must not be filtered out by checkpoint-sized thresholds.
- Search should remain multi-backend and confidence-aware, not a single API
  lookup.

