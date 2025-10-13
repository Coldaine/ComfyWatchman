# ComfyFixerSmart Vision

> **Owner Directive:** The principles and requirements documented here are immutable and must not be altered without explicit approval from the project owner.

> **See also:**
> - [Research Prompt](research/RESEARCH_PROMPT.md) — Ultimate vision for automated workflow generation & optimization
> - [Existing Systems Analysis](research/EXISTING_SYSTEMS.md) — Prior art and recommendations from ComfyUI-Copilot, ComfyScript, ComfyGPT, etc.

## Mission
Make ComfyUI workflows instantly runnable and meaningfully understood by an intelligent, trustworthy assistant that resolves dependencies, explains intent, recommends improvements, and adapts to the user's hardware — all while staying transparent, safe, and under user control.

## Why Now
- Workflows are proliferating faster than documentation and model hosting stability.
- Dependency resolution (models, custom nodes) remains a major friction point.
- LLMs can summarize, compare, and reason about workflows, but they need grounded, local knowledge and tools.
- Teams want repeatable, auditable automation that integrates with CI/CD and enterprise policies.

## Core Outcomes
- Zero‑friction setup: Detect, resolve, download, and verify missing models/nodes.
- Knowledge‑driven understanding: Explain what a workflow does and how to use/tune it.
- Hardware‑aware optimization: Recommend settings and alternatives that fit available VRAM/CPU.
- Continuous improvement: Suggest safer/faster/higher‑quality variants and track regressions.
- Trust and control: Every action is transparent, logged, and user‑approved.

## Guiding Principles
- Reliability first: Deterministic scanning, explicit verification, resumable execution.
- Privacy by default: Keep knowledge and embeddings local; minimize external calls.
- Explainability: Human‑readable reports with linked evidence, diffs, and logs.
- User autonomy: Propose changes; execute only with clear consent.
- Interoperability: Work with ComfyUI Manager, Civitai, HuggingFace, and standard tooling.
- Ethics and compliance: Respect licenses, attribution, and consent; never bypass provider rules.

## North‑Star Use Cases
- Onboarding: “Make these workflows runnable here” — fully resolved with a single command.
- Review: “Tell me the purpose, trade‑offs, and missing pieces of this workflow.”
- Optimization: “Tune this for 8GB VRAM and faster iteration without big quality loss.”
- Regression watch: “Compare this updated workflow to its predecessor; highlight quality/VRAM/runtime changes.”
- Digital twin LoRA (with consent): “Plan data requirements, train LoRAs, and produce workflows for safe, consistent identity.”

## Phase Requirements (Consult Owner Before Any Change)

### Phase 1 — Workflow Readiness Automation
- **Scheduler:** LLM-powered workflow checks run when manually triggered _and_ automatically every 2 hours, provided the machine is awake and sufficient VRAM is free.
- **Master Status Report:** Each cycle regenerates a comprehensive status entry for every workflow under `workflows/`, marking it runnable only when all nodes are present and each referenced model exists in the proper ComfyUI directory.
- **Static Dashboard:** Produce a locally stored (non-hosted) dashboard summarizing workflow readiness and dependency gaps.
- **Caches:** Refresh lightweight caches of installed custom nodes and available models (grouped by type) on the same cadence to feed reports.
- **External Intake Acknowledgment:** An external cron already moves workflow files into place; ComfyFixerSmart simply validates readiness on schedule—no additional ingestion logic required.

### Phase 2 — Knowledge-Guided Resolution
- **Curated Knowledge Base:** Maintain a plain-document knowledge pack (no databases) distilled from research reports and owner-approved materials to ground LLM reasoning.
- **Scheduled Discovery:** On the same cadence (or hourly if testing demonstrates value) attempt to resolve missing models/nodes, updating the dashboard and reports.
- **Search Workflow:**
  - Primary path: Civitai API queries orchestrated by Qwen (current LLM) with web-search fallback tooling.
  - Secondary path: Hugging Face CLI downloads when appropriate.
  - Reasoned deliberation: LLM must think through each step, request review when uncertain, and log its rationale.
- **Doubt Handling:** When the correct model/node is uncertain, trigger the designated backup plan for manual confirmation or alternative strategies.
- **Owner Workflow Schemas:** Capture lightweight, versioned schemas that reflect preferred build patterns—initially:
  1. **Auto-Inpaint Frontend:** Plug-and-play mask generation chain (SAM + Florence today, but designed for swappable detectors/growth nodes) that supports automatic masking and controlled mask growth without manual painting.
  2. **Image-Cycling Frontend:** Workflow loader that targets one or more folders, feeds images one at a time (not batch style), and advances via random/seed changes between runs. This frontend depends on Workflow Schema #3.
  3. **Dynamic Prompt Generator:** Node bundle (LLM vision optional, tagger optional, preferred LLM for prompt creation) that analyzes the current image, produces descriptive tags, and emits positive/negative prompts tailored to the Image-Cycling Frontend.
- **Usage Guardrail:** These schemas inform full refactors or explicit requests only; they should not auto-modify existing workflows without the owner's direction.

### Phase 3 — Extended LLM + RAG Vision (Original Stretch Goals)
- Optional integration of richer retrieval-augmented workflows (embeddings, similarity search, advanced comparisons) once Phases 1 and 2 are complete and stable.
- Expansion of the reviewer to leverage persistent embeddings or vector indexes—potentially through an external RAG service—only if explicitly approved, retaining the document-only default otherwise.
- Exploration of automated optimization, templated workflow synthesis, and agent-driven planning aligned with the original long-term vision.

## Vision For LLM + RAG
- A local, document-based knowledge pack (no databases) that captures how nodes work, how workflows are constructed, and which models suit specific tasks/hardware; regenerated or refreshed on schedule from curated sources.
- An LLM reviewer that uses the document pack plus tool outputs (scanner, hardware profiler, verifiers) to:
  - Explain intent and typical outputs
  - Identify risks, gaps, and improvements
  - Propose hardware‑suitable settings and model choices
  - Generate actionable diffs and install plans aligned with owner-approved workflow schemas when refactors are requested

## Roadmap (High Level)
1. Foundations: Robust scanning, resolution, downloads, verification, status reporting.
2. Understanding: Workflow→graph extraction, hardware profiler, first‑pass LLM reviews (no RAG).
3. RAG (Phase 3 stretch): Local embeddings and search over workflows, node docs, and model metadata, to be activated only after owner approval once Phases 1–2 are complete.
4. Planning: Automated recommendations, parameter tuning, alternative variants (speed/quality/safety).
5. Orchestration: Full “download → review → recommend → verify” loop with opt‑in execution.

## Continuous Workflow Health Report
- Goal: Replace the ad‑hoc `workflow_analysis_report.md` with an automatic, continuously updated, machine‑and‑human readable report that keeps workflows aligned.
- Triggers: On workflow changes, scheduled runs, or CI events; summarizes current health and drift.
- Contents:
  - Dependency status (missing/installed models and nodes) and resolution actions
  - Alignment checks against best‑practice patterns and hardware profile
  - Regressions vs. prior versions (quality hints, VRAM/runtime implications, parameter diffs)
  - Suggested fixes and safe alternatives with links to evidence (logs, search results, node docs)
- Artifacts: Markdown for humans and JSON for tools; per‑workflow pages plus an aggregated index.
- Location: `output/reports/workflows/` with `index.md|json` and `per‑workflow.{md,json}`.
- Outcome: Always‑current visibility that reduces bit‑rot and accelerates onboarding.

## Success Metrics
- Setup efficiency: Missing dependencies resolved on first pass (>95%).
- Usability: Time from clone to runnable workflows (<5 minutes on typical setups).
- Explainability: Users rate reviews ≥4/5 for clarity and usefulness.
- Stability: Resume logic recovers gracefully; no duplicate large downloads.
- Privacy: All RAG data and embeddings stored locally; no unintended data egress.

## Ethics & Safety Guardrails
- Obtain and document consent and rights for any training data.
- Respect model and dataset licenses and attribution requirements.
- Prohibit and detect disallowed content (e.g., minors, non‑consensual impersonation).
- Provide clear disclaimers and escalation points when automated recommendations carry risk.
