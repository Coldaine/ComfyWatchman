# ADR Workstream Checklist

Date: 2025-10-19
Owner: Unassigned (pairing with Copilot)
Scope: Track promotion of backlog decision points into formal ADRs and implementation plans.

> Binding policy: RAG is disabled locally and delegated to an external, owner-managed backend. Do not build, enable, or persist embeddings or indexes locally. Only interface with the external service via approved API when explicitly authorized in writing by the owner.

## How to use this checklist

- Work through items top-to-bottom unless the owner reprioritizes.
- For each DP, create `docs/adr/NNNN-short-title.md` when promoted.
- Each ADR must include: Context, Decision, Consequences, Status, References, Rollout, Revert.
- Link back to the backlog file for cross-reference.

## To-do items

- [ ] DP-001: RAG Activation and Persistence Policy — Promote ADR clarifying externalized RAG only and local hard-off policy. See: `docs/adr/2025-10-19-decision-points-and-adr-backlog.md#dp-001-rag-activation-and-persistence-policy`
- [ ] DP-002: Confidence Thresholds for FOUND vs UNCERTAIN vs NOT_FOUND — Define scoring rubric and thresholds. See: `docs/adr/2025-10-19-decision-points-and-adr-backlog.md#dp-002-confidence-thresholds-for-found-vs-uncertain-vs-not_found`
- [ ] DP-003: Scheduler Cadence and Guardrails — Finalize intervals and VRAM guardrails. See: `docs/adr/2025-10-19-decision-points-and-adr-backlog.md#dp-003-scheduler-cadence-and-guardrails`
- [ ] DP-004: Download Execution Model (Immediate vs Queue Service) — Decide execution model and flags. See: `docs/adr/2025-10-19-decision-points-and-adr-backlog.md#dp-004-download-execution-model-immediate-vs-queue-service`
- [ ] DP-005: Parallelism and Retry Policy for Downloads — Concurrency, backoff, resume. See: `docs/adr/2025-10-19-decision-points-and-adr-backlog.md#dp-005-parallelism-and-retry-policy-for-downloads`
- [ ] DP-006: Integrity and License Verification Depth — Size/hash/license requirements. See: `docs/adr/2025-10-19-decision-points-and-adr-backlog.md#dp-006-integrity-and-license-verification-depth`
- [ ] DP-007: Continuous Workflow Health Report Schema — Contract and versioning. See: `docs/adr/2025-10-19-decision-points-and-adr-backlog.md#dp-007-continuous-workflow-health-report-schema`
- [ ] DP-008: Workflow Graph Role Taxonomy and Depth — Role set and persistence format. See: `docs/adr/2025-10-19-decision-points-and-adr-backlog.md#dp-008-workflow-graph-role-taxonomy-and-depth`
- [ ] DP-009: Feature Flags — Defaults and Scope — Ensure RAG hard-off and flag structure. See: `docs/adr/2025-10-19-decision-points-and-adr-backlog.md#dp-009-feature-flags-—-defaults-and-scope`
- [ ] DP-010: Search Backend Ordering and Early-Termination Heuristics — Confirm ordering and give-up policy. See: `docs/adr/2025-10-19-decision-points-and-adr-backlog.md#dp-010-search-backend-ordering-and-early-termination-heuristics`
- [ ] DP-011: Knowledge Pack Scope, Cadence, and Provenance — External RAG provenance; local no-embed. See: `docs/adr/2025-10-19-decision-points-and-adr-backlog.md#dp-011-knowledge-pack-scope-cadence-and-provenance`
- [ ] DP-012: Reporting UX — Static vs Minimal Web Viewer — Decide reporting surface for Phase 1. See: `docs/adr/2025-10-19-decision-points-and-adr-backlog.md#dp-012-reporting-ux-—-static-vs-minimal-web-viewer`
- [ ] DP-013: Telemetry and Metrics Retention Policy — Metrics scope and retention. See: `docs/adr/2025-10-19-decision-points-and-adr-backlog.md#dp-013-telemetry-and-metrics-retention-policy`
- [ ] DP-014: Owner Workflow Schemas — Usage Boundaries — Advise-only and mutation rules. See: `docs/adr/2025-10-19-decision-points-and-adr-backlog.md#dp-014-owner-workflow-schemas-—-usage-boundaries`
- [ ] DP-015: Secret Management and Environment Policy — Source and prohibitions. See: `docs/adr/2025-10-19-decision-points-and-adr-backlog.md#dp-015-secret-management-and-environment-policy`

- [ ] DP-016: Model Metadata Inspector Utility — Add `inspect` command (CLI + library), safe per-file/directory metadata extraction; text and JSON outputs; tests and fixtures. See: `docs/adr/2025-10-19-decision-points-and-adr-backlog.md#dp-016-model-metadata-inspector-utility-cli--library`
