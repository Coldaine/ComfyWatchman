# ComfyFixerSmart – Right-Sized Implementation Plan

**Last Updated:** 2025-10-23  
**Owner Directive:** This document captures the prescribed near-term path. Agents must follow it unless the owner issues a newer revision.

---

## Strategic Focus (Phase 1 Minus Dashboard)

To deliver reliable, automated readiness checks, we execute Phase 1 requirements except for the static dashboard. The sequence below is mandatory:

1. **Guardrailed Scheduler**
   - Implement `scheduler.py` that triggers a full readiness cycle every 120 minutes by default.
   - Gate runs on "machine awake" and minimum VRAM (configurable via `config.default.toml` → `[schedule] min_vram_gb`).
   - Provide CLI integrations:
     - `comfywatchman --run-cycle` → single guarded cycle
     - `comfywatchman --scheduler` → background loop (respecting VRAM/awake checks)
   - Persist next-run metadata and last outcomes in the state directory for observability.

2. **Cache Refresh Pipeline**
   - Create `cache_manager.py` that refreshes light-weight caches every scheduler cycle:
     - `state/model_cache.json` → models grouped by type (source: `ModelInventory`).
     - `state/custom_nodes_cache.json` → metadata pulled from `$COMFYUI_ROOT/custom_nodes`.
   - Avoid redundant rewrites by short-circuiting when content is unchanged (checksum/hash).

3. **Workflow Scan & Resolution Hook**
   - Scheduler invokes the existing scanner/inventory path, then the updated multi-backend search (Qwen → Civitai) described in [docs/SEARCH_ARCHITECTURE.md](../SEARCH_ARCHITECTURE.md).
   - Respect UNCERTAIN statuses and include them in cycle summaries for manual review.

4. **Master Status Report**
   - Introduce `reporting/status_report.py` that produces:
     - `output/reports/status/master_status.json`
     - `output/reports/status/master_status.md` (optional human summary)
   - Each entry must capture: workflow path, missing models/nodes, UNCERTAIN count, last resolved timestamp, and intake source (see below).

5. **External Intake Acknowledgment**
   - Detect new/updated workflow files (compare hash or mtime against state).
   - Append acknowledgments to `state/intake_log.jsonl` and surface them in the master status report.
   - Expose `comfywatchman --list-intake` for quick audit of the last N acknowledgments.

6. **State & Telemetry Enhancements**
   - Expand `StateManager` to record per-cycle metrics (duration, success flag, skipped reason).
   - Log structured summaries to `log/structured.log` (phase, workflows scanned, resolved, UNCERTAIN, errors).

> **Explicitly excluded for this iteration:** static dashboard UI/HTML. The scheduler, caches, status report, and search improvements must land first.

---

## Search & Resolution Expectations

The prescribed behavior for model resolution is the architecture in [docs/SEARCH_ARCHITECTURE.md](../SEARCH_ARCHITECTURE.md). Enforcement guidelines:

- Backend order defaults to `config.search.backend_order = ["qwen", "civitai"]`. V2 mode must respect this order.
- Civitai results require case-insensitive **exact** filename matches. No fuzzy `FOUND` responses.
- Qwen must return `UNCERTAIN` with candidates rather than silently downgrading to `NOT_FOUND`.
- `SearchResult.type` propagates to download tasks so files land in the correct ComfyUI subfolder.
- A future `--auto-download` flag may auto-execute trusted matches, but manual review remains the default until download queue automation is approved.

Implementation changes already underway:

- Normalization fixes for Windows-style workflow paths to ensure exact matching.
- `SearchResult` now retains `UNCERTAIN`, enabling scripts/reports to flag doubt cases.
- `search_multiple_models(..., backends=...)` temporarily overrides backend order to honor CLI/config choices.

Agents working on search code must align with these rules before touching new features.

---

## Civitai Image Metadata Safeguard

The incident in `docs/reports/civitai-api-wrong-metadata-incident.md` is now canon. All integrations with the Civitai Images API must:

1. Use a helper such as `validate_civitai_image_response(image_id, payload)` to confirm the returned `id` matches the requested value.
2. Treat mismatched IDs or empty results as hard failures (surface clear `NOT_FOUND` messaging).
3. Log the requested ID, returned ID, and URL at DEBUG level for traceability.
4. Document the behavior in `docs/technical/integrations.md` (see updated entry).

Until that validator exists, new features must not rely on `/api/v1/images` responses.

---

## Deliverables Checklist

Before closing Phase 1 (minus dashboard), ensure the following artifacts exist and CI/agents can rely on them:

- `scheduler.py` with CLI wiring and VRAM guard configuration.
- `cache_manager.py` (or equivalent module) writing model and custom-node caches.
- `reporting/status_report.py` generating JSON/MD outputs listed above.
- Updated `state_manager.py` capturing per-cycle outcomes and intake acknowledgments.
- Configuration defaults documented in `config/default.toml` and `docs/technical/integrations.md`.
- Regression tests or smoke scripts verifying scheduler gating, cache refresh, and status generation on sample workflows.

Document progress in changelog commits and update this plan if requirements change. Any scope modifications still require explicit owner approval per `docs/vision.md`.
