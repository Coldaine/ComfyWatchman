# Combined ADR Catalog

Date: 2025-10-19
Status: Draft (rolling catalog)
Scope: ComfyFixerSmart (aka ComfyWatchman)

This document consolidates high-priority ADRs into one place with a summary at the top and detailed sections below. It references the backlog at `docs/adr/2025-10-19-decision-points-and-adr-backlog.md`.

Important policy: RAG is disabled locally and delegated to an external, owner-managed backend. Do not build, enable, or persist embeddings or indexes locally. Integration is via an approved API only after explicit written owner authorization.

Related operational guidance: see the Model Resolution Playbook at `docs/playbooks/model-resolution-playbook.md` for an agentic search-and-resolve flow (Civitai → mentions → web → Hugging Face → family-specific fallbacks) aligned with DP-002.

## Decisions summary

| DP | Title | Status | Decision snapshot |
|----|-------|--------|-------------------|
| DP-001 | RAG Activation and Persistence | Accepted (Owner Policy) | External RAG backend only; local RAG stays hard-OFF until explicit written authorization. No local embeddings or indexes. |
| DP-002 | Confidence Thresholds for FOUND/UNCERTAIN/NOT_FOUND | Proposed | Scoring rubric with Auto ≥ 90, Manual 60–89, Not Found < 60; strict source and license allow-lists, integrity and risk checks. |
| DP-004 | Download Execution Model | Proposed (default unchanged) | Keep immediate per-model downloads; design background queue as optional behind a flag. |
| DP-005 | Parallelism & Retry Policy | Proposed | concurrency=3; retries=3 (2s, 8s, 30s); resume with `wget -c`; optional rate limit. |
| DP-006 | Integrity & License Verification | Proposed | Size > 1 MB + license allow-list required; optional SHA256 catalog when available. |
| DP-007 | Continuous Workflow Health Report Schema | Proposed | Versioned, includes readiness, dependencies, confidence bands, risk flags, hints. |
| DP-009 | Feature Flags — Defaults & Scope | Proposed | All advanced features OFF by default; RAG hard-OFF locally; `rag_external` only with owner authorization. |
| DP-010 | Search Backend Ordering | Proposed | qwen-first; skip Civitai for SAM/RIFE/NMKD families; timeout 15 min; max 8 attempts. |
| DP-011 | Knowledge Pack Scope & Provenance | Proposed | Weekly refresh; provenance manifest; any embeddings handled by external RAG backend only. |

For full context and remaining DPs, see the backlog.

---

## DP-001 — RAG Activation and Persistence (Accepted)

- Context: Privacy, complexity, and performance implications around embedding generation and storage.
- Decision: Externalize RAG entirely. This project must not create, store, or manage embeddings or vector indexes locally. If and when RAG is enabled, it will be through an approved external backend via API and only after explicit written owner authorization.
- Consequences:
  - Simpler local architecture and reduced privacy surface area.
  - No local experimentation with embeddings; all RAG experimentation lives in the external service.
  - Feature flags related to RAG remain hard-OFF locally; env overrides must not bypass this policy.
- Status: Accepted (Owner Policy)
- Enforcement:
  - Guardrail text is present in the ADR backlog and here.
  - Any code paths or flags touching RAG remain disabled; changes require a dedicated ADR and owner sign-off.
- References: `docs/adr/2025-10-19-decision-points-and-adr-backlog.md#dp-001-rag-activation-and-persistence-policy`, `docs/vision.md`, `docs/architecture.md`

---

## DP-002 — Confidence Thresholds for FOUND/UNCERTAIN/NOT_FOUND (Proposed)

Goal: Define a clear rubric to determine when the system should auto-download a model vs. route to manual review, and when to report not found.

### Signals considered

- Filename match quality: exact filename match (case-sensitive) vs. normalized/approximate.
- Source trust: source is in allow-list (e.g., Hugging Face orgs like Comfy-Org, official GitHub releases, vendor-official URLs, Civitai with allowed license).
- License check: license ∈ allow-list (e.g., MIT, Apache-2.0, CC-BY for certain assets). Unknown or disallowed ⇒ penalty or block.
- Integrity hints: expected size range, known SHA256/ETag when available, or reproducible hash catalog.
- Context corroboration: reference/docs in workflow notes, model families that are known to live on specific hosts (e.g., SAM on Meta S3, RIFE/NMKD on GitHub/HF).
- Risk flags: NSFW markers where policy applies, suspicious mirrors, repackers, malware reports.

### Scoring rubric (0–100)

- +60 Exact filename match
- +15 Source allow-listed and canonical for the family (HF official org, vendor site, GitHub Release asset)
- +10 License allow-listed and machine-parsed
- +10 Integrity corroboration (size ±10% expected OR matching known checksum/ETag)
- +5 Context corroboration (workflow note/official doc link matches)
- −30 License unknown/ambiguous; −60 license disallowed ⇒ immediate block
- −25 Non-canonical mirror or reseller domain
- −15 Significant filename divergence (normalized match only)
- −20 Any risk flag triggered (malware report, takedown notice)

### Thresholds and actions

- Score ≥ 90 AND no red flags ⇒ FOUND (Auto-download allowed)
- 60 ≤ Score < 90 OR minor flags ⇒ UNCERTAIN (Manual review required)
- Score < 60 OR disallowed license/risk block ⇒ NOT_FOUND (or BLOCKED)

### Early-termination heuristics

- Known families route directly to canonical sources; skip others:
  - SAM: Meta official S3
  - RIFE / FILM / NMKD upscalers: GitHub releases or their official repos/HF mirrors
  - Wan 2.1/2.2: Hugging Face Comfy-Org repackaged repositories
- Cap attempts per backend; prefer freshness of official metadata.

### Implementation notes

- Keep a source allow-list and license allow-list in config (TOML); disallowed licenses are blocked regardless of score.
- Cache integrity metadata (size/hash) when available; otherwise lean on ETag and provider headers.
- Persist decisions with `schema_version` and include confidence, rationale, and links.

- Status: Proposed
- References: Backlog DP-002, `docs/SEARCH_ARCHITECTURE.md`, `docs/planning/QWEN_SEARCH_IMPLEMENTATION_PLAN.md`

---

Notes:

- This catalog will grow as DPs are promoted and accepted. It is intended to remain a single-page overview with detailed sections for the most important decisions.
- For per-ADR deep dives or historical variants, we may still create individual `docs/adr/NNNN-*.md` files and link back here from the summary.

