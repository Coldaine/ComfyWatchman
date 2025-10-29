# Proposed Architecture: LLM + RAG Extensions

> **Owner Directive:** Architectural rules and requirements here must not be changed without the owner's explicit consent.

> **See also:**
> - [Research Prompt](research/RESEARCH_PROMPT.md) — Ultimate vision for automated workflow generation & optimization
> - [Existing Systems Analysis](research/EXISTING_SYSTEMS.md) — Comprehensive review of existing tools with adoption recommendations

This document outlines an architecture that respects the Phase 1 and Phase 2 requirements while layering LLM + RAG capabilities on top of ComfyFixerSmart's dependency resolution core.

## Overview
- Schedule: Every 2 hours (or on demand) trigger the full readiness check if the machine is awake and VRAM is sufficient.
- Ingest: Scan workflows and local models/custom nodes, refreshing caches each cycle.
- Resolve: Find/download missing models with verification and resume.
- Understand: Convert workflows to typed graphs and summarize purpose.
- Retrieve: Assemble a document-based knowledge pack from curated sources.
- Review: Use an LLM with retrieved context and tool outputs to generate assessments and recommendations.
- Act (opt‑in): Propose diffs, install scripts, and parameter presets tailored to hardware.

## Major Components
- Scheduler & Guardrails
  - Triggers runs manually or every 2 hours when the machine is awake and VRAM is above the defined threshold.
  - Skips or postpones runs when VRAM is low or the system is sleeping, logging the reason.
  - Coordinates cache refresh, scanning, and reporting tasks.

- Scanner & Inventory
  - Parses ComfyUI workflow JSONs
  - Extracts model references, node types, and parameters
  - Builds local model index by type (checkpoint, lora, vae, controlnet, upscalers, etc.)
  - Refreshes cached views of installed nodes and models on every scheduled run

- Resolver & Verifier
  - **Agentic Search**: Qwen-orchestrated multi-phase search (PRIMARY - see [Search Architecture](SEARCH_ARCHITECTURE.md))
  - **Phase 1**: Civitai API with intelligent keyword extraction and exact filename validation
  - **Phase 2**: Web search (Tavily) + HuggingFace repository discovery
  - **Doubt Handling**: UNCERTAIN status with candidate list when confidence is low
  - Backends: Pluggable SearchBackend API (Civitai direct, ModelScope experimental)
  - Integrity checks (size, hash if available), resumable downloads

- **Handles the low-level download mechanics** (e.g., executing `wget`), placing files into correct ComfyUI directories with type validation. It is orchestrated by the **Automated Download & Verification Service**.

- Automated Download & Verification Service
  - **Evolves the Downloader from a manual script generator into a true, "fire-and-forget" background service.**
  - **Persistent Job Queue:** Uses a lightweight, file-based queue (`persist-queue`) to manage a list of pending download jobs. The main application dispatches jobs to this queue instead of generating a script.
  - **Background Worker (`download_worker.py`):** A standalone, long-running process that pulls jobs from the queue, executes downloads with automatic retries and resume (`wget -c`), and triggers the verification step.
  - **Agentic Verification:** Upon successful download, the worker invokes a specialized Qwen agent with a strict rubric to verify the integrity and correctness of the downloaded file (e.g., checking for unexpected file types or executables in archives).
  - **Logging and State Management:** All actions, including verification failures, are logged and tracked in the central state manager, making the entire process observable through the UI.
  - **Exhaustive Framework:** For a complete breakdown of this service, see the detailed domain document: **[Automated Download & Verification Workflow](domains/AUTOMATED_DOWNLOAD_WORKFLOW.md)**.

- Workflow Graph Builder
  - Normalizes each workflow into a typed DAG of nodes/edges/params
  - Computes derived features: modality, samplers, resource intensity, I/O footprint
  - Caches graph representation for RAG and comparison

- Hardware Profiler
  - Detects GPU(s), VRAM, CPU cores, storage, precision support
  - Produces a `HardwareProfile` used by recommendations (precision, batch, tiling, model choices)

- Knowledge Pack (Document-Based)
  - Extractors: workflow graphs → text descriptors; curated research summaries → owner-approved documents; model metadata → plain-text facts.
  - Storage: simple folders of Markdown/JSON/TOML files (no databases) refreshed on schedule.
  - Retrieval: On-demand parsing and (optional) ephemeral embeddings per run; nothing persisted beyond files.
  - Context Packers: assemble prompt-ready bundles (Workflow Summary, Node Behavior, Hardware Profile, Similar Workflows, Known Issues).
  - Phase 3 option: introduce persistent embeddings/vector search—or connect to an approved external RAG service—only with owner approval once the document workflow is rock-solid.
- Workflow Schema Library
  - Maintains owner-preferred mini schemas for recurring patterns (auto-inpaint frontend, image-cycling frontend, dynamic prompt generator).
  - Stores schemas as versioned documents/JSON (no database) within the knowledge pack.
  - Provides utilities to inject or validate these schemas only during full refactors or when explicitly requested.
  - Supports swapping underlying nodes (e.g., SAM/Florence replacements, prompt LLM choices) without changing the schema contract.

- Reviewer Orchestrator
  - Deterministic prompt templates that consume tool outputs + retrieved contexts
  - Produces structured JSON and human‑readable Markdown
  - Topics: purpose, improvements, regressions, missing nodes/models, hardware suitability, risks

- Recommender & Planner (Optional Execution)
  - Suggests node/parameter changes and safe alternatives by hardware tier
  - Generates install/download scripts and workflow diffs (textual JSON diffs)
  - Requires explicit user confirmation before modifying files or running commands

- Continuous Workflow Health Reporter
  - Watches workflow directories (or runs on the mandated schedule) to produce an always‑current report
  - Aggregates scan, diff, verification, review, and recommendation summaries
  - Outputs per‑workflow `{md,json}` plus a consolidated index for dashboards/CI annotations
  - Backed by deterministic, idempotent generation and resume‑safe execution

- CLI & Status Manager
  - Phases: scanning → resolving → downloading → reviewing → complete
  - `status.json` with progress, counts, and current action
  - Flags to enable/disable LLM features, knowledge-pack refresh, and verification

- Logging & Telemetry
  - Structured logs in `log/` with ACTION entries for easy machine parsing
  - Privacy‑respecting by default; no external telemetry

## Data Flow
1. Schedule Check: Determine if a run should execute (time elapsed, machine awake, VRAM sufficient).
2. Cache Refresh: Update node and model caches from the live ComfyUI installation.
3. Scan: Collect `Workflows[]`, `Nodes[]`, and `ModelRefs[]`.
4. Inventory: Build local `Models[]` with type classification.
5. Diff: `Missing = ModelRefs - Models`.
6. Knowledge Pack Refresh: Rebuild document bundle from curated sources if changed.
7. Resolve: For each `Missing`, use agentic search (Qwen) to orchestrate multi-phase discovery:
   - Phase 1: Civitai API with exact filename validation (max 5-8 attempts)
   - Phase 2: Tavily web search + HuggingFace repository discovery
   - Phase 3: Return FOUND, UNCERTAIN (with candidates), or NOT_FOUND
8. Download: Materialize models with integrity checks; update progress.
9. Graph: Serialize workflow DAGs for contextual analysis.
10. Review: Assemble context; run LLM; emit `review.json|md`.
11. Recommend: Propose changes and scripts; wait for user confirmation.
12. Report (Continuous): Generate/refresh `output/reports/workflows/` artifacts (index + per‑workflow).

## Storage & Schemas (selected)
- `output/missing_models.json`: [{ filename, expected_type, workflow, node_type, node_id }]
- `output/resolutions.json`: [{ filename, source, download_url, expected_type, verification? }]
- `output/reviews/<wf>.json`: {
  purpose, summary, findings: { improvements[], regressions[], gaps[] },
  hardware: { suitability, suggestions[] }, recommendations[], evidence[]
}
- `knowledge_pack/` (folder): curated Markdown/JSON/TOML docs regenerated from research; includes manifest with hashes/timestamps.
- `output/reports/workflows/index.json|md`: aggregated health snapshot
- `output/reports/workflows/<workflow>.json|md`: detailed, diff‑aware health reports

## APIs (internal)
- SearchBackend
  - `search(query, type?) -> list[SearchResult]`
  - `get_model_details(id) -> dict`

- DownloadHandler
  - `supports_url(url) -> bool`
  - `download(url, save_path, progress_cb?) -> Result`

- Retrieval
  - `index(paths|objects, metadata)`
  - `retrieve(query, k=8, filters=None) -> list[Chunk]`
  - `pack(workflow_graph, hardware, topics=[]) -> ContextBundle`

## Configuration (TOML excerpts)
```toml
[schedule]
enabled = true
interval_minutes = 120
min_vram_gb = 6.0

[llm]
enabled = true
provider = "qwen"
model = "qwen2.5-coder"

[knowledge_pack]
source_dirs = ["docs/research", "docs"]
output_dir = "knowledge_pack"

[review]
generate_markdown = true
generate_json = true

[verification]
enable_url_verification = false

[report]
continuous = true
output_dir = "output/reports/workflows"
```

## Security & Privacy
- API keys loaded via env or config; never committed to disk in plaintext.
- Knowledge pack remains plain-text files; any embeddings are ephemeral per run (no databases).
- Clear provenance: Every generated recommendation references retrieved sources.
- Content safeguards: Optional rule checks (e.g., license/consent assertions) before execution.

## Extensibility
- New search backends (e.g., model hubs, internal artifact stores).
- Alternative embedding models (still ephemeral, no persistent vector stores).
- Additional reviewers (quality, bias/safety, performance) as independent plugins.
- Exporters (HTML reports, Slack/Discord notifications, CI annotations).

## Testing Strategy
- Unit tests: parsers, type classifiers, graph builder, hardware profiler.
- Golden tests: prompt templates with frozen tool outputs to validate reviewer stability.
- Integration tests: end‑to‑end runs on fixture workflows with mocked backends.
- Performance tests: large workflow libraries; resume under network interruption.

## CLI Additions (proposed)
- `--run-cycle` Force a single scheduled cycle regardless of timer
- `--llm-review` Run the reviewer on scanned workflows
- `--knowledge-pack` Regenerate the document pack immediately
- `--hardware-profile auto|<file>` Use detected or supplied profile
- `--verify-urls` Enable optional URL verification step
- `--no-network` Force offline mode (skip remote searches; use cached knowledge pack only)
- `--report` Generate workflow health report once and exit

## Implementation Phases
1. **Scheduler + Caches (Phase 1 core):** Two-hour guardrailed runner, node/model cache refresh, VRAM checks, and static dashboard + master status regeneration.
2. **Graph + Hardware:** Workflow graph cache and hardware profiler feeding reports and future recommendations.
3. **Knowledge Pack Builder:** Document extraction pipeline (no database) with owner-approved sources and manifests.
4. **LLM Search & Resolution:** Civitai API orchestration, Hugging Face CLI fallback, reasoning logs, and doubt-handling flow.
5. **Workflow Schema Library:** Capture/update auto-inpaint, image-cycling, and dynamic prompt schemas with versioning and integration hooks.
6. **Reviewer Enhancements:** Context packers, markdown/JSON reviews, hardware-aware suggestions, backup-plan integration, schema-aware guidance.
7. **Stretch & Polish (Phase 2 wrap-up):** Optional recommendations, UX refinements, automation helpers, integration hooks.
8. **Phase 3 (Optional RAG/Advanced):** Introduce persistent embeddings/vector search or integrate with an approved external RAG service, along with advanced planning, only upon owner approval.
