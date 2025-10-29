# Final Consolidated Documentation Plan

**Date**: 2025-10-29
**Synthesized from**: FINAL_RECOMMENDATIONS.md + documentation_review_summary.md
**Philosophy**: Clear structure + pragmatic granularity

---

## Executive Summary

After analyzing both the automated review and manual notes, this plan synthesizes the best elements of both approaches:

- **Clear directory structure** with logical grouping (from review summary)
- **Pragmatic granularity** where consolidation would create unwieldy mega-documents (from detailed analysis)
- **Organized archival** with meaningful subdirectories (from review summary)
- **Reports as examples** showcasing tool capabilities (from review summary)
- **Solo developer focus** avoiding enterprise overhead (from detailed analysis)

**Impact**:
- **33% reduction** in active documentation files (98 → ~65)
- **Clear audience-based navigation** (users, developers, strategists, historians)
- **Single source of truth** for each topic
- **Maintainable structure** going forward

---

## New Directory Structure

```
ComfyWatchman/
├── README.md                     # Project overview
├── CHANGELOG.md                  # Version history
├── CONTRIBUTING.md               # How to contribute
├──
├── docs/
│   ├── README.md                 # Documentation table of contents
│   ├── version-management.md    # Versioning policy
│   │
│   ├── user-guide/              # 🆕 All user documentation
│   │   ├── README.md            # User guide index
│   │   ├── installation.md      # From root INSTALL.md
│   │   ├── getting-started.md   # From user/user-guide.md
│   │   ├── cli-reference.md     # From user/
│   │   ├── configuration.md     # From user/
│   │   ├── inspect.md           # From usage/ + tools/model_inspector.md
│   │   ├── troubleshooting.md   # From user/
│   │   ├── faq.md              # From technical/faq.md
│   │   └── examples/           # 🆕 Reports reclassified as examples
│   │       ├── workflow_examples.md  # From user/examples.md
│   │       ├── wan22_mission_analysis.md
│   │       ├── wan22_missionary_analysis.md
│   │       └── validation_report_example.md
│   │
│   ├── developer/               # Developer documentation
│   │   ├── developer-guide.md   # Setup and contributing
│   │   ├── ai-agent-guide.md    # 🆕 Consolidated AI agent instructions
│   │   ├── api-reference.md     # Python API reference
│   │   ├── testing.md          # Test structure and strategy
│   │   └── release-process.md  # Release procedures
│   │
│   ├── architecture/            # 🆕 Architecture documentation
│   │   ├── current.md          # From developer/architecture.md
│   │   ├── vision.md           # From docs/architecture.md (future Phase 2-3)
│   │   ├── search.md           # From SEARCH_ARCHITECTURE.md
│   │   └── domains/            # Detailed domain docs
│   │       └── AUTOMATED_DOWNLOAD_WORKFLOW.md
│   │
│   ├── strategy/               # 🆕 Strategic planning
│   │   ├── README.md           # Document hierarchy and authority
│   │   ├── vision.md           # From docs/vision.md (owner-approved)
│   │   ├── CROSSROADS.md       # Integration decision
│   │   ├── roadmap.md          # 🆕 Consolidated from 3 roadmap files
│   │   ├── pathforward.md      # From truth/ (Copilot integration plan)
│   │   ├── future-file-tree.md # From truth/ (planned structure)
│   │   └── thought-process.md  # From docs/thoughTprocess.md
│   │
│   ├── planning/               # Active planning documents
│   │   ├── RIGHT_SIZED_PLAN.md # Current Phase 1 work
│   │   ├── EMBEDDING_SUPPORT_PLAN.md # DP-017
│   │   ├── QWEN_SEARCH_IMPLEMENTATION_PLAN.md
│   │   ├── INCREMENTAL_WORKFLOW.md
│   │   ├── AGENT_GUIDE.md      # Agent autonomous usage
│   │   └── prompts/            # 🆕 From docs/prompts/ + docs/plans/ + root
│   │       ├── civitai_image_format_research_prompt.md
│   │       ├── comprehensive_workflow_discovery_research_prompt.md
│   │       ├── environment_analysis_prompt.md
│   │       ├── node_research_prompt.md
│   │       ├── mcp_server_research_prompt.md
│   │       ├── model-inspector-agent-prompt.md
│   │       └── FindingWorkflows.md
│   │
│   ├── migration/              # 🆕 Migration documentation (consolidated)
│   │   ├── guide.md            # 🆕 Merge: migration-guide + technical/migration-guide
│   │   ├── checklist.md        # From migration-checklist.md
│   │   └── quick-reference.md  # From migration-cheat-sheet.md
│   │
│   ├── research/               # Research documents
│   │   ├── EXISTING_SYSTEMS.md # Landscape analysis (keep active)
│   │   ├── workflow_tooling_guide.md # From developer/
│   │   └── archive/            # 🆕 Pre-decision research
│   │       ├── README.md       # Context: these led to CROSSROADS decision
│   │       ├── ComfyUI-Copilot-Research-Report.md
│   │       ├── ComfyUI-Copilot_Analysis.md
│   │       └── RESEARCH_PROMPT.md
│   │
│   ├── technical/              # Technical guides
│   │   ├── DOMAIN_ARCHITECTURE_STANDARDS.md
│   │   ├── performance.md
│   │   └── integrations.md
│   │
│   ├── adr/                    # Architecture Decision Records (keep as-is)
│   │   ├── 0001-combined-adr-catalog.md
│   │   └── 2025-10-19-decision-points-and-adr-backlog.md
│   │
│   └── reports/                # Active reports only
│       ├── CLAUDE_VERIFICATION.md
│       └── inpainting_workflow_research_report.md
│
└── archives/                   # 🆕 Historical artifacts
    ├── README.md               # Index of archived materials
    ├── project-history/        # Historical project documents
    │   ├── PR_COMPARISON.md
    │   ├── PR_REVIEW_PROMPT.md
    │   ├── REQUIREMENTS.md
    │   ├── CLEANUP_SUMMARY.md
    │   ├── due_diligence_plan.md
    │   ├── workflow_analysis_report.md
    │   ├── workflow_review_framework.md
    │   ├── migration-release-plan.md    # Enterprise release planning
    │   ├── migration-testing-strategy.md # Test details (covered in tests/README)
    │   └── NEW_FEATURES.md     # Old architecture references
    ├── incident-reports/       # Post-mortems and logs
    │   ├── civitai-api-wrong-metadata-incident.md
    │   └── python312_migration_log.md
    ├── test-logs/             # Specific test run results
    │   └── 2025-10-19-download-test-results.md
    ├── reviews/               # Historical reviews
    │   └── AGENT_TOOLING_REVIEW.md
    ├── design/                # Design artifacts
    │   └── FIGMA_PROMPTS.md
    ├── discussions/           # Historical discussions
    │   └── discussion.md      # ComfyUI-Copilot fork discussion
    └── legacy-tools/          # Old ScanTool and unused architecture
        ├── ScanTool/
        │   └── SCanGuide.md
        └── UnusedArchive/
            ├── architecture.md
            ├── design_rationale.md
            └── how_it_addresses_your_workflow.md
```

---

## Key Design Decisions & Rationale

### 1. User Guide Consolidation ✅
**Decision**: Create `docs/user-guide/` merging user/, usage/, and relevant technical docs

**Rationale**:
- Users shouldn't need to know difference between "user" and "usage"
- FAQ is for users, not developers
- INSTALL.md belongs with user documentation
- Reports as examples show what the tool can do

**From**: documentation_review_summary.md (superior approach)

### 2. AI Agent Documentation 📝
**Decision**: Consolidate to `docs/developer/ai-agent-guide.md` but keep playbook separate

**Rationale**:
- `AGENTS.md` + `CLAUDE.md` are redundant → merge
- `docs/planning/AGENT_GUIDE.md` is autonomous usage → merge
- **BUT** `playbooks/model-resolution-playbook.md` is a SPECIFIC algorithm → keep separate as reference

**Synthesis**: More consolidation than my plan, but not as aggressive as review summary

**Structure**:
```
docs/developer/ai-agent-guide.md  # Main consolidated guide
docs/playbooks/                   # Keep directory
└── model-resolution-playbook.md  # Keep as algorithmic reference
```

### 3. Architecture Split 🏗️
**Decision**: Create `docs/architecture/` with current vs vision split

**Rationale**:
- `docs/developer/architecture.md` describes CURRENT system
- `docs/architecture.md` describes FUTURE (Phase 2-3) LLM+RAG
- Different audiences, different timeframes
- Clearer to separate than keep confusingly named

**From**: documentation_review_summary.md (clever solution)

### 4. Strategy Directory 📊
**Decision**: Create `docs/strategy/` for all high-level planning

**Rationale**:
- Groups vision, decisions, roadmap together
- Clear separation from implementation planning
- `docs/truth/` name is unclear → absorb into strategy/

**Files**:
- `vision.md` - Owner-approved phases
- `CROSSROADS.md` - Integration decision
- `roadmap.md` - Consolidated from 3 roadmap files
- `thought-process.md` - Informal owner notes
- `pathforward.md`, `future-file-tree.md` - Integration planning

**Roadmap consolidation**: Merge COMPREHENSIVE_ROADMAP + EXECUTIVE_SUMMARY + IMPLEMENTATION_PLAN
- Review summary is right: these overlap heavily
- Create single source of truth with sections:
  1. Executive Summary (for owner/stakeholders)
  2. Strategic Analysis (initiatives, dependencies)
  3. Implementation Details (day-by-day breakdown)

### 5. Migration Documentation 📦
**Decision**: Keep 3 files in `docs/migration/` directory

**Rationale**:
- Migration complete but docs still useful for reference
- 3 distinct purposes:
  - `guide.md` - How to migrate (consolidated user + technical)
  - `checklist.md` - Governance tracking
  - `quick-reference.md` - Command lookup
- Moving to dedicated directory signals "reference, not active work"

**Difference from review summary**: Keep 3 files, not archive after consolidation
- Solo dev may need to reference migration approach for future versions

### 6. Planning Consolidation 🗂️
**Decision**: Merge `docs/plans/` and `docs/prompts/` into `docs/planning/prompts/`

**Rationale**:
- Distinction between "plans" and "planning" is unclear
- Prompts are planning artifacts
- Root-level prompts belong in docs structure

**From**: documentation_review_summary.md (correct organizational fix)

### 7. Archives Organization 🗄️
**Decision**: Create top-level `archives/` with subdirectories by type

**Rationale**:
- Historical value, but not active documentation
- Subdirectories make archives navigable
- Clear signal: "this is history, not current"

**From**: documentation_review_summary.md (much better than dumping to single dir)

**Subdirectories**:
- `project-history/` - PRs, old requirements, cleanup logs
- `incident-reports/` - Post-mortems and migration logs
- `test-logs/` - Specific test run results
- `reviews/` - Historical reviews
- `design/` - Old design artifacts
- `discussions/` - Historical discussions
- `legacy-tools/` - Old tools and drafts

### 8. Reports as Examples 💡
**Decision**: Move workflow analysis reports to `docs/user-guide/examples/`

**Rationale**:
- These are showcase examples of what the tool produces
- More useful to users as examples than buried in reports/
- Demonstrates tool capabilities

**From**: documentation_review_summary.md (brilliant insight)

---

## Files to Delete Completely

These provide no current or historical value:

1. **`docs/research/ZAI_PROVIDER.md`** - Empty stub file
2. **`docs/technical/migration-guide.md`** - Duplicate of root migration-guide.md (will be merged anyway)

---

## Implementation Plan

### Phase 1: Create New Directories (Week 1, Day 1)
```bash
# Create new directory structure
mkdir -p docs/user-guide/examples
mkdir -p docs/developer
mkdir -p docs/architecture/domains
mkdir -p docs/strategy
mkdir -p docs/planning/prompts
mkdir -p docs/migration
mkdir -p docs/research/archive
mkdir -p archives/{project-history,incident-reports,test-logs,reviews,design,discussions,legacy-tools}

# Commit structure
git add docs/ archives/
git commit -m "docs: create new directory structure for consolidation"
```

### Phase 2: Move Legacy Archives (Week 1, Day 2)
```bash
# Move existing archives to legacy-tools
git mv archives/ScanTool archives/legacy-tools/
git mv archives/UnusedArchive archives/legacy-tools/

# Move historical project files
git mv PR_COMPARISON.md archives/project-history/
git mv PR_REVIEW_PROMPT.md archives/project-history/
git mv REQUIREMENTS.md archives/project-history/
git mv docs/CLEANUP_SUMMARY.md archives/project-history/
git mv docs/due_diligence_plan.md archives/project-history/
git mv workflow_analysis_report.md archives/project-history/
git mv workflow_review_framework.md archives/project-history/

# Move incident reports
git mv docs/reports/civitai-api-wrong-metadata-incident.md archives/incident-reports/
git mv docs/reports/python312_migration_log.md archives/incident-reports/

# Move test logs
git mv docs/testing/2025-10-19-download-test-results.md archives/test-logs/

# Move reviews
git mv docs/review/AGENT_TOOLING_REVIEW.md archives/reviews/

# Move design artifacts
git mv docs/ui/FIGMA_PROMPTS.md archives/design/

# Move discussions
git mv docs/dumps/discussion.md archives/discussions/

# Delete empty stub
rm docs/research/ZAI_PROVIDER.md

# Create archives README
cat > archives/README.md << 'EOF'
# Historical Archives

This directory contains historical artifacts from the project's development. These documents provide context on the project's evolution but are not current documentation.

## Organization

- **project-history/** - PR comparisons, old requirements, cleanup logs, migration planning
- **incident-reports/** - Post-mortems and detailed incident analysis
- **test-logs/** - Specific test run results and logs
- **reviews/** - Historical architecture and tooling reviews
- **design/** - Old design artifacts and UI mockups
- **discussions/** - Historical strategic discussions
- **legacy-tools/** - Previous tool versions and unused architectures

## Current Documentation

For current documentation, see:
- **User Guide**: `docs/user-guide/`
- **Developer Docs**: `docs/developer/`
- **Architecture**: `docs/architecture/`
- **Strategy**: `docs/strategy/`
EOF

git add archives/
git commit -m "docs: archive historical artifacts with organized subdirectories"
```

### Phase 3: Consolidate User Guide (Week 1, Day 3-4)
```bash
# Move user documentation
git mv docs/user/* docs/user-guide/
git mv docs/usage/inspect.md docs/user-guide/
git mv INSTALL.md docs/user-guide/installation.md
git mv docs/technical/faq.md docs/user-guide/

# Merge model_inspector.md into inspect.md
# (Manual: append docs/tools/model_inspector.md to docs/user-guide/inspect.md)

# Move reports as examples
git mv docs/reports/WAN22_POV_MISSION_ANALYSIS.md docs/user-guide/examples/wan22_mission_analysis.md
git mv docs/reports/WAN22_POV_MISSIONARY_ANALYSIS.md docs/user-guide/examples/wan22_missionary_analysis.md
git mv docs/reports/workflow_validation_report.md docs/user-guide/examples/validation_report_example.md

# Merge workflow examples
# (Manual: merge docs/user-guide/examples.md content into new examples/ directory structure)

# Clean up empty directories
rmdir docs/user docs/usage docs/tools

# Create user guide README
cat > docs/user-guide/README.md << 'EOF'
# ComfyWatchman User Guide

Complete documentation for using ComfyWatchman.

## Getting Started
- [Installation](installation.md) - Setup and installation
- [Getting Started](getting-started.md) - Quick start guide
- [CLI Reference](cli-reference.md) - Command-line options

## Core Features
- [Configuration](configuration.md) - Configuration options
- [Model Inspector](inspect.md) - Inspecting model metadata

## Reference
- [FAQ](faq.md) - Frequently asked questions
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

## Examples
- [Workflow Examples](examples/workflow_examples.md) - Usage examples
- [WAN 2.2 Analysis](examples/wan22_mission_analysis.md) - Video workflow analysis
- [Validation Report](examples/validation_report_example.md) - Example output
EOF

git add docs/user-guide/
git commit -m "docs: consolidate user documentation into user-guide/"
```

### Phase 4: Consolidate Developer Docs (Week 1, Day 5)
```bash
# Create consolidated AI agent guide
cat > docs/developer/ai-agent-guide.md << 'EOF'
# AI Agent Guide for ComfyWatchman

This guide consolidates instructions for AI agents working with this codebase.

[Content merged from: AGENTS.md, CLAUDE.md, docs/planning/AGENT_GUIDE.md]

## Project Context
[From AGENTS.md and CLAUDE.md - project overview, relationship to ComfyUI-Copilot]

## Development Workflow
[From CLAUDE.md - development patterns, testing, code quality]

## Autonomous Usage
[From docs/planning/AGENT_GUIDE.md - how agents use the tool]

## Model Resolution Algorithm
See [Model Resolution Playbook](../playbooks/model-resolution-playbook.md) for the
detailed heuristic-based algorithm for discovering and retrieving missing models.
EOF

# Move research doc
git mv docs/developer/workflow_tooling_guide.md docs/research/

# Delete original AI agent files
rm AGENTS.md
# (Manual: merge CLAUDE.md content into ai-agent-guide.md, then delete)
# Note: Keep CLAUDE.md for now with note redirecting to new location

# Update CLAUDE.md with redirect
cat > CLAUDE.md << 'EOF'
# CLAUDE.md

**Note**: The comprehensive AI agent guide has been consolidated into
`docs/developer/ai-agent-guide.md`. This file remains for compatibility
but will redirect you there.

See: [AI Agent Guide](docs/developer/ai-agent-guide.md)

## Quick Context

This is ComfyWatchman (formerly ComfyFixerSmart), a Python CLI tool for
analyzing ComfyUI workflows and resolving missing models.

**Key Documents**:
- [AI Agent Guide](docs/developer/ai-agent-guide.md) - Complete guide for AI agents
- [Developer Guide](docs/developer/developer-guide.md) - Setup and contributing
- [Architecture](docs/architecture/current.md) - System architecture
- [Strategy](docs/strategy/vision.md) - Project vision and roadmap
EOF

git add docs/developer/
git commit -m "docs: consolidate AI agent documentation"
```

### Phase 5: Organize Architecture (Week 2, Day 1)
```bash
# Move architecture documents
git mv docs/developer/architecture.md docs/architecture/current.md
git mv docs/architecture.md docs/architecture/vision.md
git mv docs/SEARCH_ARCHITECTURE.md docs/architecture/search.md
git mv docs/domains docs/architecture/domains

# Create architecture README
cat > docs/architecture/README.md << 'EOF'
# Architecture Documentation

## Current System
- [Current Architecture](current.md) - Phase 1 system (implemented)
- [Search Architecture](search.md) - Agentic multi-phase search
- [Domain Architectures](domains/) - Detailed subsystem designs

## Future Vision
- [Vision Architecture](vision.md) - Phase 2-3 LLM+RAG extensions

## Standards
See [Domain Architecture Standards](../technical/DOMAIN_ARCHITECTURE_STANDARDS.md)
for guidance on creating detailed domain documents.
EOF

git add docs/architecture/
git commit -m "docs: organize architecture documentation with current vs vision split"
```

### Phase 6: Create Strategy Directory (Week 2, Day 2-3)
```bash
# Move strategic documents
git mv docs/vision.md docs/strategy/
git mv docs/CROSSROADS.md docs/strategy/
git mv docs/truth/Pathforward.md docs/strategy/pathforward.md
git mv docs/truth/FutureFileTree.md docs/strategy/future-file-tree.md
git mv docs/thoughTprocess.md docs/strategy/thought-process.md

# Clean up empty directory
rmdir docs/truth

# Consolidate roadmap files
# (Manual: merge COMPREHENSIVE_ROADMAP + EXECUTIVE_SUMMARY + IMPLEMENTATION_PLAN)
cat > docs/strategy/roadmap.md << 'EOF'
# ComfyWatchman Roadmap

[Consolidated from: COMPREHENSIVE_ROADMAP, EXECUTIVE_SUMMARY, IMPLEMENTATION_PLAN]

## Executive Summary
[High-level overview from EXECUTIVE_SUMMARY.md]

## Current State & Priorities
[Gap analysis and critical path from EXECUTIVE_SUMMARY.md]

## Strategic Analysis
[Initiative matrix, dependencies, risks from COMPREHENSIVE_ROADMAP.md]

## 90-Day Plan
[Detailed day-by-day breakdown from IMPLEMENTATION_PLAN.md]

## Success Metrics
[Metrics and monitoring from IMPLEMENTATION_PLAN.md]
EOF

# Delete originals after merge
rm docs/roadmap/COMPREHENSIVE_ROADMAP.md
rm docs/roadmap/EXECUTIVE_SUMMARY.md
rm docs/roadmap/IMPLEMENTATION_PLAN.md
rmdir docs/roadmap

# Create strategy README
cat > docs/strategy/README.md << 'EOF'
# Strategic Documentation

This directory contains high-level strategic planning and decision documents.

## Document Hierarchy

### Owner-Approved (Requires explicit consent to modify)
1. **[vision.md](vision.md)** - Mission and phased requirements (Phase 1-3)
2. Related: **[../architecture/vision.md](../architecture/vision.md)** - Technical architecture for Phase 2-3

### Strategic Decisions
3. **[CROSSROADS.md](CROSSROADS.md)** - Integration strategy decision (Oct 2025)
   - Decision: Option 3 (Complement ComfyUI-Copilot)

### Planning Documents
4. **[roadmap.md](roadmap.md)** - 90-day strategic roadmap with implementation details
5. **[pathforward.md](pathforward.md)** - Flexible fork integration plan
6. **[future-file-tree.md](future-file-tree.md)** - Planned architecture for Copilot integration

### Historical Context
7. **[thought-process.md](thought-process.md)** - Owner's informal vision refinement notes

## For Implementation Plans
See `docs/planning/` for active tactical planning documents.
EOF

git add docs/strategy/
git commit -m "docs: create strategy directory with consolidated roadmap"
```

### Phase 7: Consolidate Planning (Week 2, Day 4)
```bash
# Move prompts
git mv environment_analysis_prompt.md docs/planning/prompts/
git mv node_research_prompt.md docs/planning/prompts/
git mv docs/prompts/* docs/planning/prompts/
git mv docs/plans/* docs/planning/prompts/

# Clean up
rmdir docs/prompts docs/plans

# Archive outdated planning doc
git mv docs/planning/NEW_FEATURES.md archives/project-history/

# Update planning README
cat > docs/planning/README.md << 'EOF'
# Active Planning Documents

## Current Phase 1 Work
- [RIGHT_SIZED_PLAN.md](RIGHT_SIZED_PLAN.md) - Phase 1 execution priorities

## Proposed Features
- [EMBEDDING_SUPPORT_PLAN.md](EMBEDDING_SUPPORT_PLAN.md) - DP-017 design (awaiting approval)

## Implementation Plans
- [QWEN_SEARCH_IMPLEMENTATION_PLAN.md](QWEN_SEARCH_IMPLEMENTATION_PLAN.md) - Agentic search design
- [INCREMENTAL_WORKFLOW.md](INCREMENTAL_WORKFLOW.md) - Incremental download redesign

## Agent Usage
- [AGENT_GUIDE.md](AGENT_GUIDE.md) - How AI agents use the tool autonomously

## Research Prompts
See [prompts/](prompts/) for AI agent prompts used in planning and research.

## For Strategic Planning
See `docs/strategy/` for high-level vision and roadmap.
EOF

git add docs/planning/
git commit -m "docs: consolidate planning documents and prompts"
```

### Phase 8: Organize Migration Docs (Week 2, Day 5)
```bash
# Consolidate migration guides
# (Manual: merge migration-guide.md + technical/migration-guide.md)
cat > docs/migration/guide.md << 'EOF'
# ComfyWatchman Migration Guide

[Consolidated from: migration-guide.md + technical/migration-guide.md]

## What's New in 2.0
[Breaking changes and key improvements from technical guide]

## Pre-Migration Preparation
[Backup and dependency checks from user guide]

## Step-by-Step Migration
[Combined step-by-step from both guides]

## API Migration
[API breaking changes from technical guide]

## Troubleshooting
[Combined troubleshooting sections]

## Rollback Procedures
[Rollback instructions from user guide]
EOF

# Move other migration docs
git mv docs/migration-checklist.md docs/migration/checklist.md
git mv docs/migration-cheat-sheet.md docs/migration/quick-reference.md

# Archive enterprise migration docs
git mv docs/migration-release-plan.md archives/project-history/
git mv docs/migration-testing-strategy.md archives/project-history/

# Delete originals after consolidation
rm docs/migration-guide.md
rm docs/technical/migration-guide.md

# Create migration README
cat > docs/migration/README.md << 'EOF'
# Migration Documentation

Documentation for migrating from v1.x to v2.0.

## Main Guide
- [Migration Guide](guide.md) - Complete step-by-step migration instructions

## Reference
- [Migration Checklist](checklist.md) - Governance tracking and sign-off
- [Quick Reference](quick-reference.md) - Command translation and quick fixes

## Status
Migration to v2.0 is complete. These docs are maintained for reference and
future version migrations.
EOF

git add docs/migration/
git commit -m "docs: consolidate migration documentation"
```

### Phase 9: Archive Research (Week 3, Day 1)
```bash
# Move pre-decision research to archive
git mv docs/research/ComfyUI-Copilot-Research-Report.md docs/research/archive/
git mv docs/research/ComfyUI-Copilot_Analysis.md docs/research/archive/
git mv docs/research/RESEARCH_PROMPT.md docs/research/archive/

# Create archive README
cat > docs/research/archive/README.md << 'EOF'
# Archived Research

These documents were part of the strategic analysis conducted in October 2025
that led to the CROSSROADS.md decision.

## Documents

- **ComfyUI-Copilot-Research-Report.md** - Technical analysis of Copilot's architecture
- **ComfyUI-Copilot_Analysis.md** - Strategic recommendations for learning from Copilot
- **RESEARCH_PROMPT.md** - Original research questions that guided analysis

## Decision Outcome

After this research, the decision was documented in
[docs/strategy/CROSSROADS.md](../../strategy/CROSSROADS.md):

**Option 3: Integrate/Complement** - ComfyWatchman provides advanced dependency
management that can work standalone OR integrate with ComfyUI-Copilot.

## Current References

For current strategic direction:
- [Strategy Documents](../../strategy/)
- [EXISTING_SYSTEMS.md](../EXISTING_SYSTEMS.md) - Landscape analysis (still current)
EOF

git add docs/research/
git commit -m "docs: archive pre-decision research with context"
```

### Phase 10: Final Cleanup (Week 3, Day 2)
```bash
# Update main docs README
cat > docs/README.md << 'EOF'
# ComfyWatchman Documentation

## For Users
- **[User Guide](user-guide/)** - Installation, usage, troubleshooting, examples

## For Developers
- **[Developer Guide](developer/)** - Setup, contributing, API reference, AI agent guide
- **[Architecture](architecture/)** - System architecture (current and future vision)
- **[Testing](developer/testing.md)** - Test structure and strategy

## Strategic Planning
- **[Strategy](strategy/)** - Vision, decisions, roadmap, integration plans
- **[Planning](planning/)** - Active implementation plans and design documents

## Technical Reference
- **[ADRs](adr/)** - Architecture Decision Records
- **[Technical](technical/)** - Performance, integrations, domain standards
- **[Migration](migration/)** - v1→v2 migration guide

## Research
- **[Research](research/)** - Landscape analysis, research documents, archived analyses

## Historical
- **[Archives](../archives/)** - Historical artifacts, incident reports, old tools

## Quick Links
- [Installation](user-guide/installation.md)
- [Getting Started](user-guide/getting-started.md)
- [CLI Reference](user-guide/cli-reference.md)
- [FAQ](user-guide/faq.md)
- [AI Agent Guide](developer/ai-agent-guide.md)
EOF

# Update main README to reflect new structure
# (Manual: update README.md links to point to new locations)

# Update CLAUDE.md redirect
# (Already done in Phase 4)

# Clean up now-empty directories
find docs/ -type d -empty -delete

git add docs/README.md
git commit -m "docs: update documentation index and clean up empty directories"
```

### Phase 11: Verification (Week 3, Day 3)
```bash
# Verify all markdown files are accounted for
find . -name "*.md" -type f | sort > /tmp/new_structure.txt

# Check for broken internal links
# (Manual: use markdown link checker tool)

# Verify no empty directories remain
find docs/ -type d -empty

# Test documentation navigation
# (Manual: navigate through docs/README.md hierarchy)

git status  # Ensure clean state
```

---

## Summary Statistics

### Before
- **Total .md files**: 98
- **Root directory**: 13 .md files
- **docs/ subdirectories**: 20+ scattered directories
- **Unclear organization**: planning vs plans vs prompts, user vs usage, etc.

### After
- **Total active .md files**: ~65 (33% reduction)
- **Root directory**: 4 essential .md files (README, CHANGELOG, CONTRIBUTING, CLAUDE redirect)
- **docs/ subdirectories**: 9 clear categories
- **Archived files**: ~30 in organized subdirectories

### File Distribution
- **User guide**: 8 files + 4 examples
- **Developer**: 5 files
- **Architecture**: 4 files
- **Strategy**: 7 files
- **Planning**: 6 files + prompts
- **Migration**: 3 files
- **Research**: 2 active + 3 archived
- **Technical**: 3 files
- **ADR**: 2 files (unchanged)
- **Reports**: 2 active
- **Archives**: ~30 files organized by type

---

## Key Improvements

### 1. Clear Audience-Based Navigation ✅
- **Users** → `docs/user-guide/`
- **Developers** → `docs/developer/`, `docs/architecture/`
- **Strategists** → `docs/strategy/`
- **Planners** → `docs/planning/`
- **Historians** → `archives/`

### 2. Single Source of Truth ✅
- One user guide (not user/ + usage/)
- One AI agent guide (not 4 scattered files)
- One roadmap (not 3 overlapping files)
- One architecture split (current vs vision)

### 3. Organized Historical Archives ✅
- Subdirectories by artifact type
- Clear README explaining context
- Separate from active documentation

### 4. Reports as Examples ✅
- Workflow analyses demonstrate tool capabilities
- More useful to users than buried in reports/
- Shows real-world usage

### 5. Cleaner Root Directory ✅
- 4 essential files only
- All prompts moved to docs/
- All reports either archived or examples

---

## Open Questions for Owner

### 1. AI Agent Guide Consolidation
**Proposed**: Merge AGENTS.md + CLAUDE.md + planning/AGENT_GUIDE.md into one

**Keep separate**: `playbooks/model-resolution-playbook.md` (algorithmic reference)

**Question**: Should the model resolution playbook also be merged, or keep as separate algorithmic reference?

**Recommendation**: Keep separate - it's a specific algorithm, not general guidance

### 2. CLAUDE.md in Root
**Proposed**: Keep as redirect to `docs/developer/ai-agent-guide.md`

**Alternative**: Delete entirely and update references

**Question**: Keep redirect or delete?

**Recommendation**: Keep redirect for Claude Code compatibility (it may look for CLAUDE.md specifically)

### 3. Current vs Future Architecture
**Proposed**: Split into `architecture/current.md` and `architecture/vision.md`

**Alternative**: Keep as one file with clear section breaks

**Question**: Is the split helpful or confusing?

**Recommendation**: Split is clearer - different audiences and timeframes

---

## Success Criteria

✅ **User can find documentation in <2 clicks** from docs/README.md
✅ **Developer can find AI agent guide immediately**
✅ **Strategic documents clearly show authority hierarchy**
✅ **No duplicate content** in active documentation
✅ **Historical artifacts preserved** but not cluttering active docs
✅ **All links updated** to new structure
✅ **Solo developer can maintain** without excessive overhead

---

## Maintenance Going Forward

### Adding New Documentation
1. **User docs** → `docs/user-guide/`
2. **Developer docs** → `docs/developer/`
3. **Planning docs** → `docs/planning/`
4. **Research** → `docs/research/`
5. **Historical** → `archives/[appropriate-subdir]/`

### Archiving Old Documentation
When a document becomes historical:
1. Move to appropriate `archives/` subdirectory
2. Update `archives/README.md` with context
3. Add redirect note in original location (if needed)
4. Update links in active documentation

### Creating Examples
When generating impressive output:
1. Save sanitized version to `docs/user-guide/examples/`
2. Add brief description in examples README
3. Link from user-guide.md

---

## Estimated Effort

- **Phase 1 (Structure)**: 30 minutes
- **Phase 2 (Archives)**: 1 hour
- **Phase 3 (User Guide)**: 2-3 hours (includes merging content)
- **Phase 4 (Developer)**: 2 hours (includes AI agent guide consolidation)
- **Phase 5 (Architecture)**: 1 hour
- **Phase 6 (Strategy)**: 3 hours (includes roadmap consolidation)
- **Phase 7 (Planning)**: 1 hour
- **Phase 8 (Migration)**: 2 hours (includes guide consolidation)
- **Phase 9 (Research)**: 30 minutes
- **Phase 10 (Cleanup)**: 1 hour
- **Phase 11 (Verification)**: 1 hour

**Total**: 14-15 hours over 3 weeks

---

## Next Steps

1. **Review this plan** - Confirm approach and answer open questions
2. **Execute Phase 1** - Create directory structure
3. **Execute Phases 2-11** - Systematic consolidation following plan
4. **Verify completeness** - Check all files accounted for, links updated
5. **Update CLAUDE.md** - Ensure AI agents understand new structure

---

**This plan synthesizes the best elements of both the automated analysis and manual review, providing clear structure while maintaining pragmatic granularity where consolidation would create unwieldy documents.**
