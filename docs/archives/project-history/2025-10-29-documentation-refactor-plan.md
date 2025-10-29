# Documentation Refactor Plan (2025-10-29)

This document outlines the final, approved plan for reorganizing and consolidating the project's Markdown documentation. This plan was executed on 2025-10-29.

### The Final Plan

**Phase 1: Create New Directory Structure**
Create the new, organized directory structure. All archived materials will now be placed under `docs/archives/`.

*   `docs/user-guide/`
*   `docs/user-guide/examples/`
*   `docs/strategy/`
*   `docs/architecture/`
*   `docs/planning/prompts/`
*   `docs/archives/`
*   `docs/archives/project-history/`
*   `docs/archives/incident-reports/`
*   `docs/archives/test-logs/`
*   `docs/archives/reviews/`
*   `docs/archives/design/`
*   `docs/archives/discussions/`
*   `docs/archives/legacy-tools/`

**Phase 2: Consolidate User-Facing Documentation**
Merge all user-focused documents into the new `docs/user-guide/` directory to create a single, comprehensive resource for end-users.

1.  Move all content from `docs/user/` and `docs/usage/` into `docs/user-guide/`.
2.  Move `docs/technical/faq.md` to `docs/user-guide/faq.md`.
3.  Merge the content of `docs/tools/model_inspector.md` into `docs/user-guide/inspect.md`.
4.  Move `INSTALL.md` from the root directory into `docs/user-guide/installation.md`.

**Phase 3: Consolidate Strategic & Architectural Documentation**
Group all high-level vision, strategy, and architecture documents for clarity and easy reference.

1.  Merge `COMPREHENSIVE_ROADMAP.md`, `EXECUTIVE_SUMMARY.md`, and `IMPLEMENTATION_PLAN.md` into a single `docs/strategy/ROADMAP.md`.
2.  Move `docs/vision.md`, `docs/CROSSROADS.md`, and all files from `docs/truth/` into `docs/strategy/`.
3.  Create `docs/architecture/current.md` from the content of `docs/developer/architecture.md`.
4.  Move the future-facing `docs/architecture.md` to `docs/architecture/vision.md`.
5.  Move `docs/playbooks/model-resolution-playbook.md` to `docs/architecture/model-resolution-playbook.md`.

**Phase 4: Consolidate Developer & Planning Documentation**
Streamline the documentation intended for developers and for internal planning.

1.  Merge `AGENTS.md`, `CLAUDE.md`, and `docs/planning/AGENT_GUIDE.md` into a single `docs/developer/ai-agent-guide.md`.
2.  Move the research document `docs/developer/workflow_tooling_guide.md` to `docs/research/`.
3.  Merge the contents of `docs/plans/` and `docs/prompts/` into `docs/planning/prompts/`.

**Phase 5: Archive All Historical and Non-Essential Files**
Move all historical logs, one-time analyses, and superseded plans into the new `docs/archives/` directory to clean up the active documentation tree.

1.  Consolidate all migration-related documents into a single `migration-guide.md` and move it to `docs/archives/project-history/`.
2.  Move all other files designated for archiving into their respective `docs/archives/` subdirectories (e.g., `PR_COMPARISON.md`, `CLEANUP_SUMMARY.md`, `docs/dumps/discussion.md`, etc.).
3.  Move the workflow analysis reports from `docs/reports/` to `docs/user-guide/examples/`.

**Phase 6: Final Cleanup**
Finally, remove all the now-empty or redundant files and directories to complete the reorganization.

1.  Delete the now-empty directories (`docs/user`, `docs/usage`, `docs/tools`, `docs/truth`, `docs/plans`, `docs/prompts`, `docs/playbooks`, `docs/dumps`, `docs/tasks`, `docs/review`, `docs/testing`).
2.  Delete the empty stub file `docs/research/ZAI_PROVIDER.md`.
3.  Delete the now-redundant root files: `AGENTS.md`, `CLAUDE.md`, `INSTALL.md`, `PR_COMPARISON.md`, and `REQUIREMENTS.md`.
