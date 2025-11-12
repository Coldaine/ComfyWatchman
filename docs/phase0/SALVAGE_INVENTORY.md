# Code Salvage Inventory

## 🟢 KEEP - Core Utilities (Salvaged)

**Status:** ✅ Salvaged and ready for Phase 1 integration

The essential utilities from the legacy codebase have been extracted and consolidated into a single, self-contained module:

**`docs/phase0/salvage_utilities.py`** - Standalone utility module with:
- **Workflow scanning** - Extract model references (including embeddings) from ComfyUI JSON
- **Local inventory** - Build a set of existing model filenames under ComfyUI models/
- **Minimal Civitai search** - Lookup by ID, by hash, and by filename with exact/fuzzy matching
- **Download script generation** - Bash script generator for proper ComfyUI model subfolders
- **Lightweight inspection** - Quick file metadata and SHA256 hashing (safe by default)

**Design Philosophy:**
- No internal project imports (safe to copy anywhere)
- Minimal dependencies (only `requests` for Civitai helpers)
- Clear function contracts with typed signatures
- Ready for wrapping as LangGraph tools in Phase 1

**Mapping to Top 5 Agent Capabilities:**
1. **Workflow Scanner** → `extract_models_from_workflow()`
2. **Inventory Builder** → `build_local_inventory()`
3. **Search/Resolver** → `civitai_get_model_by_id()`, `civitai_get_version_by_hash()`, `civitai_search_by_filename()`
4. **Download/Verify** → `generate_download_script()`
5. **Inspect/Report** → `quick_inspect()`, `quick_hash()`

See `docs/phase0/README.md` for usage examples and function contracts.

## 🟡 ADAPT - Orchestration Layer

| Component | Status | Phase 1 Plan |
|-----------|--------|--------------|
| **Orchestration** | ❌ Archived | Rebuild with LangGraph StateGraph (see `docs/phase1/INTEGRATION_PLAN.md`) |
| **CLI** | ❌ Archived | New agent-callable API surface, no standalone CLI |
| **State Management** | ❌ Archived | Rebuild with LangGraph checkpointers (SQLite/Postgres) |
| **Scheduler** | ❌ Archived | Rebuild with APScheduler + systemd timers |

## 🔴 ARCHIVED - Historical Reference Only

| Path | Reason |
|------|--------|
| `archives/original-codebase-2025-10-30/src/comfywatchman/*` | CLI-centric architecture incompatible with vision |
| `archives/original-codebase-2025-10-30/civitai_tools/*` | Monolithic design, utilities extracted to `salvage_utilities.py` |
| `archives/original-codebase-2025-10-30/legacy/*` | Obsolete prototypes |
| All old `docs/*` | Outdated documentation, replaced by phase-based structure |

## � Next Steps

1. ✅ **Phase 0 Complete** - Salvage utilities extracted and documented
2. 🔄 **Phase 1 Starting** - Implement LangGraph StateGraph using salvaged utilities as tools
3. ⏳ **Phase 2 Planned** - Add agentic search with Qwen and multi-backend resolution
4. ⏳ **Phase 3 Planned** - Human-in-the-loop approval gates and dashboard
