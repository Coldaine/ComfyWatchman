# ADR Backlog: High-Priority Decision Points

Date: 2025-10-19
Status: Draft (seeking owner consultation)
Scope: ComfyFixerSmart (aka ComfyWatchman) — Phases 1–2 active, Phase 3 optional, autonomy deferred

> Note: Per owner directives, Phase 1 and Phase 2 scope must not change without explicit approval. RAG enablement and any autonomous playbooks remain opt-in and require written authorization.

---

## Binding Policy: RAG is disabled locally and delegated to an external backend

Until explicitly instructed in writing by the owner:

- Do not implement, generate, persist, or manage any embeddings or vector indexes locally.
- Do not enable any RAG- or embedding-related feature flags, environment overrides, or experimental code paths.
- A separate, owner-managed RAG backend is being set up; this project will only ever interface with that service via an approved API when/if authorized.
- All references to RAG in this backlog are design placeholders for that external integration. They must not be activated or prototyped locally.
- Any change to this policy requires a dedicated ADR, explicit owner approval, and a gated rollout behind feature flags.

Callouts within this backlog: DP-001 (RAG Activation), DP-009 (Feature Flags), DP-011 (Knowledge Pack/Provenance).

---

## How to promote an item to a formal ADR

- Create a file: `docs/adr/NNNN-short-title.md` (increment NNNN)
- Template:
  - Title
  - Context
  - Decision
  - Consequences
  - Status (Proposed | Accepted | Rejected | Superseded)
  - References
- Each ADR should reference this backlog entry and the relevant documentation sections.

---

## DP-001: RAG Activation and Persistence Policy

- Question: Should we enable RAG in the near term, and if so, how are embeddings stored?
- Options:
  0) External RAG backend only — no local embeddings, no local vector DB; integrate via approved API when explicitly authorized
  1) Keep RAG disabled (document-only baseline)
  2) Ephemeral embeddings per run (no persistent index)
  3) Local persistent index with TTL + provenance
- Proposed default (draft): 0) Defer to external RAG backend and keep all local RAG disabled until explicit written owner authorization. When/if authorized, interface with the external service only; do not create or persist local embeddings or indexes.
- Why it matters: Privacy, complexity, performance envelope
- References: `docs/vision.md` (Phase 3 stretch, Vision for LLM + RAG), `docs/architecture.md` (Proposed Architecture: LLM + RAG)

## DP-002: Confidence Thresholds for FOUND vs UNCERTAIN vs NOT_FOUND

- Question: What scoring rubric and thresholds gate automatic downloads vs. manual review?
- Options:
  - Exact filename + known source + size/hash ⇒ FOUND (auto)
  - Filename match but license/source unclear ⇒ UNCERTAIN
  - No match after attempts ⇒ NOT_FOUND
- Proposed default (draft): Exact filename and allowed source and license ∈ allow-list ⇒ FOUND; otherwise UNCERTAIN
- References: `docs/SEARCH_ARCHITECTURE.md` (Doubt Handling), `docs/planning/QWEN_SEARCH_IMPLEMENTATION_PLAN.md` (Decision Tree)

## DP-003: Scheduler Cadence and Guardrails

- Question: Interval, VRAM threshold, and "awake" definition for scheduled cycles
- Options: Fixed 2h cadence vs. adaptive; VRAM ≥ N GB; skip when GPU busy/low VRAM
- Proposed default (draft): 120 minutes, min_vram_gb = 6.0, skip when GPU memory usage > 70%
- References: `docs/vision.md` (Phase 1 — Scheduler), `docs/architecture.md` (Scheduler & Guardrails)

## DP-004: Download Execution Model (Immediate vs Queue Service)

- Question: Continue per-model immediate downloads or move to a persistent background queue + worker?
- Options:
  1) Current incremental immediate model (Production Ready)
  2) Background job queue worker (persist-queue) with retries/resume
  3) Hybrid (immediate for small, queue for large)
- Proposed default (draft): Keep 1) for now; design 2) as an optional mode behind a flag
- References: `docs/planning/INCREMENTAL_WORKFLOW.md` (Production Ready), `docs/architecture.md` (Automated Download & Verification Service), `docs/domains/AUTOMATED_DOWNLOAD_WORKFLOW.md`

## DP-005: Parallelism and Retry Policy for Downloads

- Question: Max concurrent downloads, backoff strategy, resume behavior, bandwidth caps
- Options: Concurrency 2–4; exponential backoff; `wget -c` resume; global rate limit; per-source rate caps
- Proposed default (draft): concurrency=3, retries=3 with exponential backoff (2s, 8s, 30s), `wget -c`, optional `--limit-rate`
- References: `docs/planning/INCREMENTAL_WORKFLOW.md` (Future Enhancements), `AGENTS.md` (Failure-first policy)

## DP-006: Integrity and License Verification Depth

- Question: Beyond size checks, what integrity signals and license gates are required?
- Options: size-only; SHA256 catalog for known models; strict license allow-list; unknown ⇒ block/UNCERTAIN
- Proposed default (draft): size>1MB check + license allow-list enforcement; optional hash catalog when available
- References: `docs/vision.md` (Ethics & Safety Guardrails; License Handling Clarification), `docs/architecture.md` (Resolver & Verifier)

## DP-007: Continuous Workflow Health Report Schema

- Question: Finalize JSON/MD contract, versioning, and triggers
- Options: Minimal vs. enriched with graph roles, confidence, risk flags
- Proposed default (draft): Include readiness, dependencies, confidence bands, risk flags, optimization hints; version each artifact (`schema_version`)
- References: `docs/vision.md` (Continuous Workflow Health Report)

## DP-008: Workflow Graph Role Taxonomy and Depth

- Question: Which roles do we classify and persist? How deep is parameter normalization?
- Options: loader/generator/conditioning/control/upscale/output; optional sampler/modality labels
- Proposed default (draft): Adopt the 6 core roles + sampler label; persist as `workflow_graph_v1.json`
- References: `docs/architecture.md` (Workflow Graph Builder), `docs/vision.md` (Understanding, Roadmap)

## DP-009: Feature Flags — Defaults and Scope

- Question: Which advanced features are enabled by default? Where are flags defined?
- Options: TOML `feature_flags.toml`; env overrides; default OFF for profiler, experiments, RAG, proposals
- Proposed default (draft): All advanced features OFF by default; flags in TOML with env override. RAG is hard-OFF locally and may only be enabled to use an external, owner-managed RAG backend via a dedicated `rag_external` integration flag after explicit written owner authorization; local RAG/embeddings must remain disabled regardless of env overrides.
- References: `AGENTS.md` (Configuration guardrails), `docs/architecture.md` (Configuration), `docs/vision.md` (Priority order)

## DP-010: Search Backend Ordering and Early-Termination Heuristics

- Question: Confirm `qwen → civitai` order, timeouts, and pattern-based skips (SAM/RIFE/NMKD)
- Options: Keep qwen-first; skip Civitai for known non-Civitai families; cap attempts at 5–8
- Proposed default (draft): qwen-first; skip Civitai for SAM/RIFE/NMKD; timeout 15 min; max 8 attempts
- References: `docs/SEARCH_ARCHITECTURE.md` (Backend Order), `docs/planning/QWEN_SEARCH_IMPLEMENTATION_PLAN.md` (Smart Give-Up Heuristics)

## DP-011: Knowledge Pack Scope, Cadence, and Provenance

- Question: Which sources are allowed, how often to refresh, and how to track provenance and redactions?
- Options: Owner-approved docs only; scheduled refresh daily/weekly; manifest with hashes/timestamps
- Proposed default (draft): Weekly refresh; provenance manifest with content hashes and source URLs; redaction log. Embedding generation and provenance tracking for RAG, if any, are handled by the external RAG backend; this project only consumes curated outputs or APIs from that service when explicitly authorized. No local scraping/indexing/embedding is permitted.
- References: `docs/vision.md` (Curated Knowledge Base, Vision for LLM + RAG), `docs/architecture.md` (Knowledge Pack)

## DP-012: Reporting UX — Static vs Minimal Web Viewer

- Question: Remain static MD/JSON or add a local HTML viewer?
- Options: Static only; simple local HTML renderer; CLI pretty tables
- Proposed default (draft): Static MD/JSON (Phase 1 requirement), optional CLI pretty tables later
- References: `docs/vision.md` (Phase 1 — Static Dashboard, Continuous Workflow Health Report)

## DP-013: Telemetry and Metrics Retention Policy

- Question: What metrics to collect, how long to retain, and strict privacy limits
- Options: wall_clock_duration, peak_vram (if detectable), cache hits; retention 30–90 days; no content hashes unless RAG approved
- Proposed default (draft): Collect timing + counts; no content hashes; rotate logs monthly
- References: `docs/vision.md` (Telemetry Scope), `docs/architecture.md` (Logging & Telemetry)

## DP-014: Owner Workflow Schemas — Usage Boundaries

- Question: When can we propose schema-aligned refactors and what approvals are required?
- Options: Propose only; require explicit owner approval + versioned copy for any mutation
- Proposed default (draft): Advise-only by default; any mutation requires explicit approval; versioned `.vN.json` copies
- References: `docs/vision.md` (Owner Workflow Schemas; Usage Guardrail; Immutable Boundaries; Approval Token)

## DP-015: Secret Management and Environment Policy

- Question: Source of CIVITAI_API_KEY, HF_TOKEN, etc., and prohibitions on persistence
- Options: Load via environment or `~/.secrets`; never commit; validate presence on startup
- Proposed default (draft): `~/.secrets` + env; runtime checks; never write to disk beyond env/session
- References: `AGENTS.md` (API Keys), `docs/architecture.md` (Security & Privacy)

---

## Recommended next ADRs to formalize (top 4)

1) DP-004 Download Execution Model (Immediate vs Queue) — impacts reliability and UX
2) DP-002 Confidence Thresholds — safety vs. automation trade-off
3) DP-006 Integrity & License Verification Depth — compliance gate clarity
4) DP-007 Health Report Schema — becomes the canonical source of truth

## Notes


## DP-016: Model Metadata Inspector Utility (CLI + Library)

- Question: Should we add a first-class "model inspector" that reads per-file metadata safely and concisely for any given file or directory?
- Options:
  1) Minimal CLI subcommand in comfywatchman (e.g., `comfywatchman inspect <file|dir>`), outputs human-readable and JSON
  2) Standalone script under `scripts/` integrated later into CLI
  3) Defer and rely on external tools
- Proposed default (draft): 1) Add a built-in `inspect` command that:
  - For `.safetensors`: uses `safetensors.safe_open(...).metadata()` (no tensor load)
  - For `.pth/.pt/.ckpt`: avoid `torch.load` by default (pickle risk); extract basic info (size, suspected type by filename and known families). Optionally gated `--unsafe` mode for local manual checks on trusted files
  - For `.onnx`: use `onnx` to read model graph meta if available (optional dependency)
  - Normalize output fields: `filename`, `path`, `size_bytes`, `format`, `type_hint`, `metadata` (subset), `sha256` (optional `--hash`), `source_hints` (if known)
  - Output formats: `--format text|json` and `--summary` (concise)
- Why it matters: Fast verification of downloads, safer triage, consistent inputs to confidence rubric, and a portable knowledge-gathering tool for single files or batches
- Acceptance criteria:
  - Runs on a single file and on a directory (recursive optional)
  - Never loads tensors for `.safetensors`; never unpickles by default for `.pth/.pt/.ckpt`
  - Produces a concise summary (<=10 lines) and a structured JSON per file
  - Exit code 0 on success, non-zero on fatal errors; partial failures reported per file
  - Tests cover happy path + unreadable/corrupt files
- Testing plan (next phase):
  - Integrate archived `archives/ScanTool/comfyui_model_scanner.py` patterns
  - Create sample fixtures: small `.safetensors` with metadata, dummy `.pt` (no unpickle), `.onnx` tiny model
  - Validate CLI text output and JSON schema; measure performance on 100+ files

