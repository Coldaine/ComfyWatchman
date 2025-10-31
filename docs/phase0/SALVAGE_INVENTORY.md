# Code Salvage Inventory

## 🟢 KEEP - Core Utilities
| File Path | Purpose | New Location | Notes |
|-----------|---------|--------------|-------|
| N/A | All utilities will be rewritten based on the new LangGraph 1.0 patterns. | N/A | The original codebase has been archived for historical reference. |

## 🟡 ADAPT - Refactor to Tools
| File Path | Current Issue | Refactor Plan | Priority |
|-----------|---------------|---------------|----------|
| N/A | The original CLI-centric architecture is being replaced entirely. | All orchestration will be implemented as a new LangGraph StateGraph. | P0 |

## 🔴 DELETE - Not Aligned
| File Path | Reason for Deletion |
|-----------|---------------------|
| `src/comfyfixersmart/*` | Replaced by new LangGraph architecture. |
| `civitai_tools/*` | Replaced by new LangGraph architecture. |
| `legacy/*` | Obsolete code. |
| All old `docs/*` | Outdated documentation, replaced by new structured documentation. |

## 📚 ARCHIVE - Historical Reference
| File Path | Archival Reason |
|-----------|-----------------|
| `archives/original-codebase-2025-10-30/` | Entire previous codebase, preserved for historical reference. |
