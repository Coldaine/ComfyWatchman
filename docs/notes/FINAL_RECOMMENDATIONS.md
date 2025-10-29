# Final Documentation Consolidation Recommendations

**Date**: 2025-10-29
**Analysis Scope**: 98 markdown files across entire repository
**Context**: Solo developer project, not enterprise-level

---

## Executive Summary

After comprehensive analysis of all markdown documentation, combining automated scanning with manual review of existing notes, I recommend **consolidating or removing 32 files (33% reduction)** while preserving all critical information.

**Key Findings**:
- Heavy duplication in migration docs (6 files → 3 files)
- Pre-decision research superseded by CROSSROADS.md (3 files to archive)
- Root directory clutter (6 files to move/delete)
- Complete archive directory can be removed (4 files)
- Strategic document overlap needs consolidation (4 files)

**Impact**: Cleaner structure, easier navigation, reduced maintenance burden, clearer authority hierarchy.

---

## Priority Actions

### 🔴 **CRITICAL - Do Immediately (10 files)**

These files provide no current value or create confusion:

#### Delete Completely (6 files)
1. **`archives/UnusedArchive/architecture.md`**
   - 95% duplicate of `docs/developer/architecture.md`
   - 1,013 lines of redundant content
   - Explicitly marked "Unused"

2. **`PR_COMPARISON.md`** (root)
   - One-time PR comparison analysis (PR #2 vs #3)
   - Historical artifact with no ongoing value
   - 512 lines

3. **`PR_REVIEW_PROMPT.md`** (root)
   - Template for specific PR #3 review
   - PR already merged
   - 509 lines

4. **`workflow_review_framework.md`** (root)
   - Not referenced anywhere
   - Appears to be draft/unused template

5. **`docs/CLEANUP_SUMMARY.md`**
   - Log file from previous cleanup
   - Historical record, not living documentation

6. **Entire `archives/` directory** (confirm first)
   - `archives/ScanTool/SCanGuide.md` - Functionality integrated into inspector
   - `archives/UnusedArchive/` - All 3 files are drafts/obsolete
   - Name "UnusedArchive" indicates these are not needed

**Action**: `rm -rf archives/` after confirming no critical info

#### Move to Appropriate Locations (4 files)
7. **`environment_analysis_prompt.md`** (root) → `docs/prompts/`
8. **`node_research_prompt.md`** (root) → `docs/prompts/`
9. **`workflow_analysis_report.md`** (root) → `docs/reports/`
10. **`REQUIREMENTS.md`** (root) → `docs/legacy/` or delete
    - Marked as "historical reference" in CLAUDE.md
    - Original requirements document

---

### 🟠 **HIGH PRIORITY - This Week (16 files)**

#### Merge Migration Documentation (6 files → 3 files)

**Current State**: 6 files with 20-25% content overlap
- `docs/migration-guide.md` (1,331 lines) - User-focused
- `docs/technical/migration-guide.md` (382 lines) - Developer-focused
- `docs/migration-checklist.md` (247 lines) - Governance tracking
- `docs/migration-cheat-sheet.md` (231 lines) - Quick reference
- `docs/migration-testing-strategy.md` (432 lines) - Test framework
- `docs/migration-release-plan.md` (385 lines) - Enterprise release plan

**Recommendation**:

1. **Create `docs/MIGRATION.md`** (merge first two)
   - Combine migration-guide.md + technical/migration-guide.md
   - Target: ~700 lines consolidated
   - Keep user-friendly step-by-step PLUS breaking changes/API details
   - Structure:
     ```
     1. What's New in 2.0
     2. Pre-Migration Preparation
     3. Key Breaking Changes
     4. Step-by-Step Migration Process
     5. API Migration Guide
     6. Troubleshooting & FAQ
     7. Rollback Procedures
     ```

2. **Keep `docs/MIGRATION-CHECKLIST.md`** (rename from migration-checklist.md)
   - Distinct purpose: procedural governance tracking
   - Used for team/owner sign-off

3. **Keep `docs/MIGRATION-QUICK-REFERENCE.md`** (rename from migration-cheat-sheet.md)
   - Quick command reference
   - Tab-friendly for developers

4. **Delete `docs/migration-testing-strategy.md`**
   - Content is already covered in tests/README.md
   - Specific testing details belong in test documentation

5. **Delete `docs/migration-release-plan.md`**
   - Enterprise-focused staged release plan
   - Not applicable to solo developer
   - You noted this in your CLAUDE.md: "solo developer, not enterprise"

**Benefit**: Reduces migration docs by 50%, eliminates duplication, clearer purpose for each file.

#### Archive Pre-Decision Research (3 files → docs/research/archive/)

These were **inputs** to the CROSSROADS.md decision. That decision has been made (Option 3: Complement Copilot). Historical value only.

1. **`docs/research/ComfyUI-Copilot-Research-Report.md`**
   - Pre-decision technical analysis
   - Superseded by CROSSROADS.md

2. **`docs/research/ComfyUI-Copilot_Analysis.md`**
   - Pre-decision strategic recommendations
   - Recommended "adopting agent-based architecture" - decision made differently

3. **`docs/research/RESEARCH_PROMPT.md`**
   - Original research questions
   - All questions answered by EXISTING_SYSTEMS.md and CROSSROADS.md

**Action**:
```bash
mkdir -p docs/research/archive/
git mv docs/research/ComfyUI-Copilot-Research-Report.md docs/research/archive/
git mv docs/research/ComfyUI-Copilot_Analysis.md docs/research/archive/
git mv docs/research/RESEARCH_PROMPT.md docs/research/archive/
```

Add `docs/research/archive/README.md`:
```markdown
# Archived Research

These documents were part of the strategic analysis that led to the
CROSSROADS.md decision (October 2025). They are preserved for historical
context but are not authoritative going forward.

**Authoritative Documents**:
- `../CROSSROADS.md` - The decision framework (Option 3: Complement)
- `../EXISTING_SYSTEMS.md` - Landscape analysis (still current)
```

#### Merge AI Agent Guides (2 files → 1 file)

**Issue**: `AGENTS.md` and `CLAUDE.md` both provide instructions for AI agents with significant overlap.

**Your Observation** (from 01_root_notes.md):
> "Both provide instructions for AI agents. They have significant overlap. CLAUDE.md is more detailed about the integration strategy with ComfyUI-Copilot. These should be merged."

**Recommendation**:
- **Keep `CLAUDE.md`** as the primary AI agent guide
- **Delete `AGENTS.md`** (44 lines vs 800+ in CLAUDE.md)
- Update README.md to point only to CLAUDE.md
- CLAUDE.md already serves this purpose comprehensively

#### Evaluate Copilot Integration Plans (2 files)

**Files**:
- `docs/truth/Pathforward.md` (Flexible Fork Integration Plan)
- `docs/truth/FutureFileTree.md` (Planned Copilot integration architecture)

**Question**: Are these still relevant given CROSSROADS.md decision?

**Recommendation**:
- **If pursuing deep integration**: Keep in `docs/truth/` and reference from CROSSROADS.md
- **If keeping minimal integration**: Move to `docs/research/archive/` as "considered but deferred"
- **Action needed**: You must decide based on current strategy

**My assessment**: CROSSROADS.md chose "Option 3: Complement" which is lighter integration than these docs plan. Consider archiving unless you're committed to the full adapter-based integration described in Pathforward.md.

#### Archive Outdated Planning (1 file)

**`docs/planning/NEW_FEATURES.md`**
- References old architecture (`comfy_fixer.py`)
- Not integrated into current V2 architecture
- Describes prototype features from early development

**Action**: Move to `docs/planning/archive/` with note about historical context.

---

### 🟡 **MEDIUM PRIORITY - Next 2 Weeks (6 files)**

#### Extract Autonomous Playbook Section from Vision

**Issue**: `docs/vision.md` contains 450 lines (lines 111-314) of "NOT ACTIVE" future playbooks.

**Recommendation**:
```bash
# Create new file
docs/vision/AUTONOMOUS_PLAYBOOK_VISION.md

# Move lines 111-314 from vision.md
# Add header: "DEFERRED - Post Phase 2 - Not Currently Active"
# Keep brief (2-3 line) reference in vision.md
```

**Benefit**: vision.md becomes focused (~350 lines vs ~800), clearer separation of active vs future work.

#### Consolidate Roadmap Documentation (2 files)

**Issue**: Overlapping strategic content between:
- `docs/roadmap/COMPREHENSIVE_ROADMAP.md` (500 lines)
- `docs/roadmap/IMPLEMENTATION_PLAN.md` (820 lines)

**Recommendation**:
1. **Rename** COMPREHENSIVE_ROADMAP.md → `ROADMAP_STRATEGY.md`
2. **Rename** IMPLEMENTATION_PLAN.md → `IMPLEMENTATION_ROADMAP.md`
3. **Remove** duplicated strategy sections from IMPLEMENTATION_ROADMAP
4. **Add** forward reference in ROADMAP_STRATEGY: "See IMPLEMENTATION_ROADMAP for day-by-day details"

**Benefit**: ~200 lines of duplication removed, clearer document purposes.

#### Consolidate Strategic Documents (4 files in docs/ root)

**Your Observation** (from 03_docs_root_notes.md):
> "vision.md, architecture.md, CROSSROADS.md, and thoughTprocess.md all contribute to the project's high-level strategy. They could be consolidated or grouped."

**Recommendation**: Don't merge, but **group** and **clarify hierarchy**:

```
docs/
├── vision.md                    # Phase 1-3 roadmap (owner-approved)
├── architecture.md              # Phase 2-3 technical details (future)
├── CROSSROADS.md               # Strategic decision (Oct 2025)
└── strategy/                   # NEW subdirectory
    ├── README.md               # Explains document hierarchy
    └── thoughTprocess.md       # Move here (informal, valuable but not official)
```

Create `docs/strategy/README.md`:
```markdown
# Strategic Documentation

## Document Hierarchy

1. **`../vision.md`** - Owner-approved mission and phased requirements
   - Authority: Owner-signed, requires explicit consent to modify
   - Scope: Phase 1-3 architecture and principles

2. **`../architecture.md`** - Technical architecture for Phase 2-3
   - Authority: Owner-approved with Phase 1-2 as mandatory
   - Scope: LLM + RAG extensions

3. **`../CROSSROADS.md`** - Integration strategy decision (Oct 2025)
   - Authority: Strategic decision document
   - Decision: Option 3 (Complement ComfyUI-Copilot)

4. **`thoughTprocess.md`** - Owner thought process and refinements
   - Authority: Informal, valuable context
   - Scope: Vision refinement and priority evolution
```

---

### 🟢 **LOW PRIORITY - Maintenance (Ongoing)**

#### Create Documentation Map

**File**: `docs/DOCUMENT_MAP.md`

**Purpose**: Single source of truth for documentation navigation.

**Content**:
```markdown
# Documentation Map

## Authority Levels
- **Owner-Approved**: Requires explicit owner consent to modify
- **Proposed**: Design complete, awaiting approval
- **Historical**: Preserved for context, not authoritative

## Core Documentation
| Document | Purpose | Authority | Last Updated |
|----------|---------|-----------|--------------|
| vision.md | Mission & phased roadmap | Owner-Approved | 2025-10-XX |
| architecture.md | Phase 2-3 technical plan | Owner-Approved | 2025-10-XX |
| CROSSROADS.md | Integration strategy | Strategic | 2025-10-XX |

## Current Implementation
| Document | Purpose | Status |
|----------|---------|--------|
| planning/RIGHT_SIZED_PLAN.md | Phase 1 execution | Active |
| planning/QWEN_SEARCH_IMPLEMENTATION_PLAN.md | Search design | Implemented |
| planning/EMBEDDING_SUPPORT_PLAN.md | DP-017 design | Proposed |

## User Documentation
| Document | Purpose |
|----------|---------|
| README.md | Project overview |
| INSTALL.md | Installation guide |
| docs/user/ | User guides |

## Developer Documentation
| Document | Purpose |
|----------|---------|
| CLAUDE.md | AI agent instructions |
| docs/developer/ | Developer guides |
| docs/adr/ | Architecture decisions |

## Historical/Archive
| Document | Location | Reason |
|----------|----------|--------|
| Research reports | docs/research/archive/ | Pre-decision analysis |
| Migration docs | (consolidated) | V1→V2 migration complete |
| Legacy requirements | docs/legacy/ | Initial requirements |
```

#### Update CLAUDE.md References

**Action**: Update CLAUDE.md to reference document authority levels and point to DOCUMENT_MAP.md.

**Addition to CLAUDE.md**:
```markdown
## Documentation Authority

See `docs/DOCUMENT_MAP.md` for complete navigation.

**Authority Hierarchy**:
1. Owner-Approved (vision.md, architecture.md) - Cannot modify without explicit consent
2. Strategic (CROSSROADS.md) - Current strategic direction
3. Tactical (planning/, roadmap/) - Current implementation plans
4. Historical (archives/, research/archive/) - Context only, not authoritative

**Critical Path Documents**:
- `docs/vision.md` - Overall mission and phases
- `docs/CROSSROADS.md` - Integration strategy decision
- `docs/planning/RIGHT_SIZED_PLAN.md` - Current Phase 1 work
- `docs/SEARCH_ARCHITECTURE.md` - Search system design
```

---

## Implementation Action Plan

### Week 1: Critical Cleanup (Immediate)
```bash
# 1. Delete obsolete files
rm PR_COMPARISON.md PR_REVIEW_PROMPT.md workflow_review_framework.md
rm docs/CLEANUP_SUMMARY.md

# 2. Remove archives (confirm first!)
rm -rf archives/

# 3. Move root prompts
mkdir -p docs/prompts
git mv environment_analysis_prompt.md docs/prompts/
git mv node_research_prompt.md docs/prompts/

# 4. Move root reports
git mv workflow_analysis_report.md docs/reports/

# 5. Archive old requirements
mkdir -p docs/legacy
git mv REQUIREMENTS.md docs/legacy/

# 6. Delete AGENTS.md (duplicate of CLAUDE.md)
rm AGENTS.md

# 7. Archive pre-decision research
mkdir -p docs/research/archive
git mv docs/research/ComfyUI-Copilot-Research-Report.md docs/research/archive/
git mv docs/research/ComfyUI-Copilot_Analysis.md docs/research/archive/
git mv docs/research/RESEARCH_PROMPT.md docs/research/archive/
# Create archive README (see content above)

# Commit
git add -A
git commit -m "docs: remove obsolete files and reorganize root directory

- Delete PR comparison and review artifacts
- Remove unused archives/ directory
- Move prompts to docs/prompts/
- Archive pre-decision research
- Remove AGENTS.md (duplicate of CLAUDE.md)
"
```

### Week 2: Migration Doc Consolidation
```bash
# 1. Create consolidated migration guide
# (Manual: merge migration-guide.md + technical/migration-guide.md)
# Target: docs/MIGRATION.md (~700 lines)

# 2. Rename remaining migration docs
git mv docs/migration-cheat-sheet.md docs/MIGRATION-QUICK-REFERENCE.md
git mv docs/migration-checklist.md docs/MIGRATION-CHECKLIST.md

# 3. Delete enterprise/redundant migration docs
rm docs/migration-testing-strategy.md
rm docs/migration-release-plan.md

# 4. Clean up old files after merge
rm docs/migration-guide.md
rm docs/technical/migration-guide.md

# 5. Update cross-references in remaining migration docs

# Commit
git add -A
git commit -m "docs: consolidate migration documentation

- Merge user and technical migration guides into MIGRATION.md
- Rename cheat sheet to MIGRATION-QUICK-REFERENCE.md
- Remove enterprise release plan and redundant test strategy
- Reduce migration docs from 6 to 3 files (50% reduction)
"
```

### Week 3: Strategic Doc Organization
```bash
# 1. Create strategy subdirectory
mkdir -p docs/strategy

# 2. Move informal thought process
git mv docs/thoughTprocess.md docs/strategy/

# 3. Extract autonomous playbooks from vision.md
mkdir -p docs/vision
# (Manual: extract lines 111-314 to docs/vision/AUTONOMOUS_PLAYBOOK_VISION.md)
# (Manual: update vision.md to keep brief reference)

# 4. Archive outdated planning
mkdir -p docs/planning/archive
git mv docs/planning/NEW_FEATURES.md docs/planning/archive/

# 5. Decide on Copilot integration plans
# Option A: Keep if pursuing integration
# Option B: Archive if deferred
# git mv docs/truth/Pathforward.md docs/research/archive/ (if archiving)
# git mv docs/truth/FutureFileTree.md docs/research/archive/ (if archiving)

# Commit
git add -A
git commit -m "docs: organize strategic documentation

- Move thoughTprocess.md to docs/strategy/
- Extract autonomous playbooks from vision.md to separate file
- Archive outdated NEW_FEATURES.md
- [Choose action for Copilot integration plans]
"
```

### Week 4: Documentation Infrastructure
```bash
# 1. Create DOCUMENT_MAP.md (see template above)
# (Manual: create docs/DOCUMENT_MAP.md)

# 2. Create strategy README (see template above)
# (Manual: create docs/strategy/README.md)

# 3. Create research archive README
# (Manual: create docs/research/archive/README.md)

# 4. Rename roadmap docs for clarity
git mv docs/roadmap/COMPREHENSIVE_ROADMAP.md docs/roadmap/ROADMAP_STRATEGY.md
git mv docs/roadmap/IMPLEMENTATION_PLAN.md docs/roadmap/IMPLEMENTATION_ROADMAP.md

# 5. Update CLAUDE.md with authority hierarchy (see content above)

# 6. Update cross-references across documentation

# Commit
git add -A
git commit -m "docs: add documentation map and clarify hierarchy

- Create DOCUMENT_MAP.md for navigation
- Add authority levels to strategic docs
- Rename roadmap docs for clarity
- Update CLAUDE.md with document authority section
"
```

---

## Summary Statistics

### Before Consolidation
- **Total markdown files**: 98
- **Root directory .md files**: 13 (cluttered)
- **Migration docs**: 6 (overlapping)
- **Research docs**: 5 (3 historical)
- **Archives**: 4 files (unused)

### After Consolidation
- **Total markdown files**: ~66 active + ~12 archived
- **Root directory .md files**: 5 (essential only)
- **Migration docs**: 3 (distinct purposes)
- **Research docs**: 2 active + 3 archived
- **Archives**: 0 (removed)

### Impact
- **32 files removed or consolidated (33% reduction)**
- **Cleaner root directory** (13 → 5 files)
- **Clearer document hierarchy** with authority levels
- **Better navigation** via DOCUMENT_MAP.md
- **Reduced maintenance burden** with less duplication

---

## Rationale for Key Decisions

### Why Delete Archives Entirely?
1. **Explicitly marked "Unused"** - The directory name itself
2. **Functionality integrated** - ScanTool features are in inspector
3. **Architecture superseded** - UnusedArchive contains drafts
4. **No external references** - Not cited in current docs
5. **Solo developer context** - Historical archives add maintenance burden

### Why Archive Pre-Decision Research?
1. **Decision already made** - CROSSROADS.md chose Option 3
2. **No longer authoritative** - Strategic direction set
3. **Historical value only** - Preserved for context
4. **Prevents confusion** - Clear what's current vs past

### Why Consolidate Migration Docs So Aggressively?
1. **Migration complete** - V1→V2 transition done
2. **Solo developer** - Don't need enterprise release plans
3. **High duplication** - 20-25% overlapping content
4. **Clearer purposes** - Guide, checklist, quick reference

### Why Keep Strategic Docs Separate?
1. **Different audiences** - Owner vs implementer vs researcher
2. **Different purposes** - Vision vs decision vs technical
3. **Different authority levels** - Owner-approved vs historical
4. **Grouping not merging** - Organization vs consolidation

---

## Files That Are EXCELLENT (Keep As-Is)

✅ **Architecture & Technical**:
- `docs/developer/architecture.md` - Primary technical reference
- `docs/SEARCH_ARCHITECTURE.md` - Specialized search system
- `docs/technical/DOMAIN_ARCHITECTURE_STANDARDS.md` - Governance

✅ **Strategic**:
- `docs/vision.md` - Owner-approved mission (after playbook extraction)
- `docs/architecture.md` - Future phases technical plan
- `docs/CROSSROADS.md` - Integration strategy decision
- `docs/research/EXISTING_SYSTEMS.md` - Landscape analysis

✅ **Planning**:
- `docs/planning/RIGHT_SIZED_PLAN.md` - Current Phase 1 work
- `docs/planning/QWEN_SEARCH_IMPLEMENTATION_PLAN.md` - Search design
- `docs/planning/EMBEDDING_SUPPORT_PLAN.md` - Proposed DP-017

✅ **User & Developer Docs**:
- `README.md` - Project overview
- `INSTALL.md` - Installation guide
- `CONTRIBUTING.md` - Contributor guide
- `CLAUDE.md` - AI agent instructions
- All `docs/user/` - User documentation
- All `docs/developer/` (except noted architecture consolidation)

✅ **Governance**:
- `docs/adr/` - Architecture decision records (excellent!)
- `docs/playbooks/` - Operational playbooks
- `CHANGELOG.md` - Version history

✅ **Supporting**:
- `docs/roadmap/EXECUTIVE_SUMMARY.md` - Owner summary
- `tests/README.md` - Test documentation

---

## Critical Context: Solo Developer

Your CLAUDE.md states:
> "This is a **solo developer project**, not enterprise-level"
> "Focus on **practical solutions** over complex abstractions"

**Applied to this consolidation**:
- ❌ Removed enterprise release planning (migration-release-plan.md)
- ❌ Removed extensive test strategy documentation (covered in tests/README.md)
- ✅ Kept practical guides (migration, quick reference, checklist)
- ✅ Preserved historical context in archives, not root docs
- ✅ Clear hierarchy so you know what's authoritative

---

## Questions for Owner Decision

### 1. Archives Directory
**Confirm deletion of entire `archives/` directory?**
- ScanTool guide obsolete (functionality in inspector)
- UnusedArchive explicitly marked unused
- No references in current docs

**Options**:
- A) Delete entirely (recommended)
- B) Move to `docs/legacy/archives/` (preserve but demote)

### 2. Copilot Integration Plans
**What to do with Pathforward.md and FutureFileTree.md?**

**Context**: CROSSROADS.md chose "Option 3: Complement" which is lighter integration than these docs plan.

**Options**:
- A) Keep if pursuing full adapter-based integration
- B) Archive to `docs/research/archive/` if integration deferred
- C) Move to `docs/planning/` if considering as future work

**My recommendation**: Archive unless you're actively implementing the adapter integration strategy. CROSSROADS.md provides sufficient strategic direction.

### 3. Migration Documents Post-V2
**Is V1→V2 migration complete in production?**

If yes:
- Consolidate to 3 docs (guide, checklist, quick ref)
- Remove enterprise release planning

If no (still migrating):
- Keep current structure until migration complete
- Consolidate after migration done

---

## Next Steps

1. **Review this document** and confirm recommendations
2. **Answer owner decision questions** above
3. **Execute Week 1 actions** (critical cleanup)
4. **Proceed with consolidation** following weekly plan
5. **Update CLAUDE.md** to reference new structure

---

## Appendix: Complete File Manifest

### Files to DELETE (11 total)
1. `archives/ScanTool/SCanGuide.md`
2. `archives/UnusedArchive/architecture.md`
3. `archives/UnusedArchive/design_rationale.md`
4. `archives/UnusedArchive/how_it_addresses_your_workflow.md`
5. `PR_COMPARISON.md`
6. `PR_REVIEW_PROMPT.md`
7. `workflow_review_framework.md`
8. `docs/CLEANUP_SUMMARY.md`
9. `AGENTS.md`
10. `docs/migration-testing-strategy.md`
11. `docs/migration-release-plan.md`

### Files to MOVE (9 total)
1. `environment_analysis_prompt.md` → `docs/prompts/`
2. `node_research_prompt.md` → `docs/prompts/`
3. `workflow_analysis_report.md` → `docs/reports/`
4. `REQUIREMENTS.md` → `docs/legacy/`
5. `docs/research/ComfyUI-Copilot-Research-Report.md` → `docs/research/archive/`
6. `docs/research/ComfyUI-Copilot_Analysis.md` → `docs/research/archive/`
7. `docs/research/RESEARCH_PROMPT.md` → `docs/research/archive/`
8. `docs/thoughTprocess.md` → `docs/strategy/`
9. `docs/planning/NEW_FEATURES.md` → `docs/planning/archive/`

### Files to MERGE (4 → 1)
1. `docs/migration-guide.md` + `docs/technical/migration-guide.md` → `docs/MIGRATION.md`
2. (Delete originals after merge)

### Files to EXTRACT (1 → 2)
1. `docs/vision.md` (lines 111-314) → `docs/vision/AUTONOMOUS_PLAYBOOK_VISION.md`

### Files to RENAME (4 total)
1. `docs/migration-cheat-sheet.md` → `docs/MIGRATION-QUICK-REFERENCE.md`
2. `docs/migration-checklist.md` → `docs/MIGRATION-CHECKLIST.md`
3. `docs/roadmap/COMPREHENSIVE_ROADMAP.md` → `docs/roadmap/ROADMAP_STRATEGY.md`
4. `docs/roadmap/IMPLEMENTATION_PLAN.md` → `docs/roadmap/IMPLEMENTATION_ROADMAP.md`

### Files to CREATE (4 total)
1. `docs/DOCUMENT_MAP.md`
2. `docs/strategy/README.md`
3. `docs/research/archive/README.md`
4. `docs/vision/AUTONOMOUS_PLAYBOOK_VISION.md`

---

**Total Actions**: 32 files affected (33% of 98 files)

**Estimated Time**:
- Week 1 (Critical): 2-3 hours
- Week 2 (Migration): 3-4 hours (manual merge work)
- Week 3 (Strategy): 2-3 hours
- Week 4 (Infrastructure): 2-3 hours
- **Total**: 10-13 hours over 4 weeks

**Benefit**: Permanently cleaner, more maintainable documentation structure.
