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
- **Scheduler:** LLM-powered workflow checks run when manually triggered _and_ automatically every 2 hours, provided the machine is awake and sufficient VRAM is free, and comfyUI is open. 
- **Master Status Report:** Each cycle regenerates a comprehensive status entry for every workflow under `workflows/`, marking it runnable only when all nodes are present and each referenced model exists in the proper ComfyUI directory.
- **Static Dashboard:** Produce a locally stored (non-hosted) dashboard summarizing workflow readiness and dependency gaps. 
- **Caches:** Refresh lightweight caches of installed custom nodes and available models (grouped by type) on the same cadence to feed reports.
- **External Intake Acknowledgment:** An external cron already moves workflow files into place; ComfyFixerSmart simply validates readiness on schedule—no additional ingestion logic required. However, sometimes ComfyFixerSmart can review workflows at request, and eventually create them. 

- **Search for workflows associated with model files and or also help make a valid workflow that utilizes a given model** 
It is a CRITICAL goal, that we are able to, given an image, review the metadata both in the image on civitai, but also search the author, posts etc... to try to understand and replicate the workflow that created the image. We cannot always get this information from 

### Phase 2 — Knowledge-Guided Resolution
- **Curated Knowledge Base:** Maintain a plain-document knowledge pack (no databases) distilled from research reports and owner-approved materials to ground LLM reasoning and how to assemble comfy UI workflows, and which models do what etc...
- **Scheduled Discovery:** On the same cadence (or hourly if testing demonstrates value) attempt to resolve missing models/nodes, updating the dashboard and reports.
- **Agentic Search Workflow:** Use Qwen as an agent, to manipulate search tools to resolve model names and get correct models. 
  - **Phase 1**: Civitai API search with intelligent keyword extraction and exact filename validation
  - **Phase 2**: Web search + HuggingFace repository discovery for models not on Civitai
  - **Agent Orchestration**: Qwen LLM coordinates search strategies, validates matches, and logs reasoning
  - **Multi-Source**: Seamlessly handles Civitai, HuggingFace, and ModelScope sources
- **Doubt Handling:** When uncertain (multiple candidates, low confidence), return UNCERTAIN status with candidate list for manual review
- **Owner Workflow Schemas:** Capture lightweight, versioned schemas that reflect preferred build patterns—initially:
  1. **Auto-Inpaint Frontend:** Plug-and-play mask generation chain (SAM + Florence today, but designed for swappable detectors/growth nodes) that supports automatic masking and controlled mask growth without manual painting.
  2. **Image-Cycling Frontend:** Workflow loader that targets one or more folders, feeds images one at a time (not batch style), and advances via random/seed changes between runs. This frontend depends on Workflow Schema #3.
  3. **Dynamic Prompt Generator:** Node bundle (LLM vision optional, tagger optional, preferred LLM for prompt creation) that analyzes the current image, produces descriptive tags, and emits positive/negative prompts tailored to the Image-Cycling Frontend.
> **Note:** The implementation of these schemas was deferred during the initial Phase 2 development to focus on core resolution and knowledge-basing features. This should be prioritized as a fast-follow task.
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

---

## (Deferred) Autonomous Agent Playbook Layer — Post‑Phase Expansion (Owner Approval Required)

> STATUS: NOT ACTIVE. This section is purely forward‑looking. Nothing here is to be built until: (a) Phase 1 & Phase 2 are fully complete and stable, (b) Phase 3 (RAG stretch) is optionally validated with success metrics, and (c) explicit written owner authorization is granted. Do **not** re‑scope earlier Phases on behalf of this layer.

### Intent

Evolve ComfyFixerSmart from a "diagnose & assist" tool into a constrained, auditable autonomous operator that can execute multi‑step improvement missions ("playbooks") end‑to‑end while remaining:

1. Grounded in the local knowledge pack + structured caches
2. Privacy‑preserving (no unapproved data egress)
3. Deterministic at boundaries (clear inputs, reproducible artifacts)
4. Human‑governed (every destructive / high‑impact action gated)

### Autonomous Operating Model (High‑Level)

| Layer | Responsibility | Current Primitive | Future Augmentation |
|-------|----------------|-------------------|---------------------|
| Observation | Scan workflows, inventory models/nodes, collect hardware/runtime telemetry | Scanner, Inventory, (planned) Scheduler | Continuous diff stream + change events queue |
| Knowledge | Document pack (plain text) + search indexes (Phase 3 optional) | Curated docs, SEARCH_ARCHITECTURE.md | Versioned semantic bundle + provenance graph |
| Reasoning | Single agent (Qwen) executes search prompt | QwenSearch orchestration | Multi‑playbook supervisor with tool budget & guardrail policies |
| Action | Generate download scripts, state updates | Download manager, StateManager | Action dispatcher with dry‑run / approval gates & rollback journal |
| Verification | Size checks, location guards | Existing download verification | Multi‑dimensional: hash sigs, safety scan, license classifier |
| Learning | Manual doc edits | None | Feedback loop: outcome logs → pattern heuristics → prompt adaptation (owner‑approved) |

### Critical Playbooks (Deferred)

Each playbook is a reproducible, multi‑stage plan template. All emit: plan.md, execution_log.json, diff artifacts, and a human summary. None auto‑apply destructive changes without explicit approval tokens.

1. **Discovery & Canonical Landscape Mapping**

- Goal: Identify the "most important" active workflows & models (usage frequency, recency, dependency fan‑out).
- Inputs: Workflow directory snapshots, state history, model inventory metadata.
- Outputs: Ranked list, coverage matrix (workflow → required models present/missing), gap report.
- Pre‑Reqs: Stable scheduler + historical run logs.

1. **Knowledge Base Synthesis & Gap Audit**

- Goal: Ensure every high‑value workflow/model has a concise, updated explainer + parameter rationale.
- Actions: Diff current doc pack vs. discovered landscape; draft missing briefs.
- Guardrail: Drafts land under `docs/generated/` pending manual curation.

1. **Parameter Optimization & Hardware Profiling**

- Goal: Suggest parameter sets for target VRAM / latency / quality envelopes.
- Mechanism: Heuristic + (optional) future micro‑benchmark harness; no blind brute force.
- Output: `optimization_plan_<workflow>.json` with rationale & expected trade‑offs.

1. **Model / LoRA Composition Advisor**

- Goal: Recommend composition strategies (base checkpoint + LoRAs + refiner) aligned with artistic or technical intent.
- Data: Local catalog + known stylistic tags (document pack) + license compatibility.
- Safety: Reject mixes with incompatible or unclear licensing.

1. **Experiment Orchestration & A/B/E Evaluation**

- Goal: Execute controlled prompt or parameter variants, capture metrics (time/VRAM/artifact size) + hashed image fingerprints.
- Output: `experiment_<id>/` folder with manifest, metrics.csv, summary.md.
- NOTE: Image content safety scan hook (owner‑defined) before persistence.

1. **Drift & Regression Watch**

- Goal: Detect regressions between workflow versions (missing node, increased VRAM, quality proxy drop).
- Trigger: Workflow file change, scheduled compare window.
- Output: `regression_report_<workflow>.md` w/ diff of salient params & risk flags.

1. **Safety & License Compliance Audit**

- Goal: Periodic scan ensuring no disallowed content models slipped in; confirm licenses for redistributed artifacts.
- Output: Audit log; high‑severity findings escalate to manual queue.

1. **Frontier Brief Assimilation (Large Spec Ingestion)**

- Goal: Given a large human brief (e.g., new domain style spec), extract actionable tasks: new LoRA candidates, parameter guidance, dependency list.
- Tooling: Chunking + (optional) embeddings if Phase 3 active; plan synthesis stored for review.

  > Redaction: Any brief flagged as potentially sensitive MUST be processed through a local redaction filter (owner‑configurable patterns) before being stored or embedded. This redaction step is mandatory and non‑bypassable.

1. **Continuous Improvement & Retrospective**

- Goal: Summarize last N runs of all playbooks; propose prioritized backlog with impact estimate & confidence.
- Output: `autonomy_retrospective_<date>.md`.

1. **Autonomous Execution Guardrails**

- Unified policy layer: max concurrent downloads, allowed model sources, size caps, license allow‑list.
- Approval tokens: Human issues ephemeral token (`approve:<plan_id>`); agent must embed token in action log line to proceed.

### Approval Token (Definition)
An **approval token** is a short, single‑use, owner‑generated string (format: `approve:<plan_id>:<nonce>`) that authorizes execution of a specific prepared plan manifest. Properties:

- Scope‑bound: Valid only for the referenced plan hash + version.
- Time‑boxed: Expires after configurable TTL (default 30 minutes) if not observed in the action journal.
- One‑shot: Consumed on first successful match; replays require a fresh token.
- Audited: Every consumption logged (timestamp, operator, plan hash, resulting artifact digests).

No token → plan remains in DRY‑RUN state.

### Change Journals & Auditing (Immutable Requirement)
All state‑mutating actions (adding/removing models, generating or editing workflow JSON, placing LoRAs, creating experiment folders) MUST:

1. Write an append‑only journal entry (JSON line) with: timestamp, actor, action_type, inputs, outputs (hashes/paths), pre/post existence flags.
2. Emit a summarized human‑readable line to a rotating audit log.
3. Never modify historical journal entries (corrections use compensating entries).

Workflow JSON modifications (when eventually allowed) are done by producing new versioned copies (`<name>.vN.json`)—no in‑place overwrite.

### Telemetry Scope (Initial Constraint)
Telemetry collection is LIMITED to local runtime performance metrics captured during explicitly approved experiment playbooks:

- Metrics: wall_clock_duration, peak_vram (if detectable), average_step_time, output_artifact_size, model_load_ms.
- Opt‑in per experiment plan; default OFF.
- No image content hashes or embeddings stored unless Phase 3 RAG is activated & approved.

### License Handling Clarification
Initial autonomous stage does NOT perform probabilistic license inference. Instead:

- Enforce allow‑list of known explicit licenses (MIT, Apache‑2.0, CC‑BY 4.0, CC0, etc.).
- If license unknown or ambiguous → block action, mark item for manual review queue.
- Future (optional) enhancement: add a lightweight SPDX text classifier (needs owner approval).

### Decision Points (Deferred Until Implementation Kickoff)

| Decision | Options | Default Stance |
|----------|---------|----------------|
| Quality proxies | Runtime heuristics, CLIP similarity, LPIPS, aesthetic model | Defer selection; log requirements only |
| LoRA stacking depth | Single, Multi (bounded N), Unlimited | Start Single; Multi only via explicit request token |
| Parameter search strategy | Grid, Heuristic narrowing, Bayesian lite | Heuristic narrowing (no brute force) |
| Redaction policy | Regex only, Heuristic + regex, Manual pre‑screen | Regex only initial |
| Vision model set | BLIP / Florence / SAM2 / CLIP variants | Research & proposal before enabling |

### Vision & Prompt Model Research Milestone (Pre‑Autonomous Enablement)
Introduce a dedicated research milestone (post Phase 2, pre Phase 3 activation) to:

1. Catalog candidate vision/prompt helper models (classification, segmentation, captioning, tag extraction).
2. Evaluate local resource footprints (VRAM, load latency) & license compatibility.
3. Produce a `vision_models_catalog.md` with recommended minimal set (e.g., SAM2 variant, lightweight captioner, zero‑shot classifier).
4. Implement pluggable loader stubs gated behind config flags.

This milestone is required before any playbook can request zero‑shot classification or prompt enrichment.

### Zero‑Shot Classifier & Targeted Tagging Path
When enabled (post research milestone):

1. Playbook identifies workflow type (e.g., inpainting) via node graph analysis.
2. Select classifier/tagger models from approved catalog (e.g., clothing, hair, accessory tags).
3. Run classifiers on sample frames or reference images (explicit user‑approved inputs only).
4. Produce `classification_context.json` used to augment prompt generation (never overwrite original user prompts).
5. Store results under `output/context/<workflow_id>/` with hashes for reproducibility.

### LoRA Composition Policy (Initial)
- Agent may **suggest** composition stacks but MUST NOT auto‑apply multiple LoRAs unless explicitly approved per stack with an approval token referencing the stack hash.
- Compatibility heuristics (style vs. structural, base model family alignment, intended resolution range) logged before suggestion.
- Ambiguous compatibility → mark as experimental; requires manual intervention.

### Immutable Boundaries (Restated)
These constraints are non‑negotiable absent owner amendment:

1. No external uploads, publishing, or dataset scraping.
2. No silent workflow JSON mutation—always versioned copy.
3. No automatic LoRA stacking beyond single unless explicit approval token present.
4. All telemetry local; no outbound transmission.
5. Redaction mandatory for flagged briefs before storage or embedding.

### Deferred Capability Boundaries

| Category | Explicitly In Scope (Deferred) | Explicitly Out of Scope (Unless Re‑approved) |
|----------|--------------------------------|----------------------------------------------|
| Data Generation | Local test images for benchmarking | Large dataset scraping or unapproved external uploads |
| Training | Planning LoRA training steps | Executing full training loops automatically |
| Model Distribution | Local placement into ComfyUI models dir | Publishing / uploading models externally |
| Automated Changes | Generating diffs & scripts | Direct in‑place workflow mutation without approval |

### Prerequisite Gates (Must All Be Green Before Activation)
1. Phase 1 SLAs met for 30 consecutive days (scheduler reliability, ≤1 missed cycle).
2. Phase 2 knowledge pack coverage ≥95% for "important" workflows (from Discovery playbook draft run in advisory mode).
3. (If adopted) Phase 3 embedding index convergence tests stable & latency acceptable.
4. No open P0 security / license issues.
5. Owner issues written ENABLE_AUTONOMOUS directive with scope & timebox.

### Execution Framework (Conceptual Path)
1. Plan Synthesis: Agent produces structured plan (YAML/JSON) → stored → waits for approval.
2. Validation: Static analyzer ensures only allowed tools & bounded resource usage.
3. Execution: Action dispatcher runs steps; each step logs start/stop, tool call summary, artifact hash.
4. Verification: Post‑condition checks (file counts, sizes, optional hash table) before marking success.
5. Rollback (if needed): Use journal to revert file moves or state entries; never delete original workflows without snapshot.

### Minimal Additional Components (Anticipated)
- `playbooks/` module: Registry + schemas for plan definitions.
- `agent_supervisor.py`: Orchestrates plan lifecycle & guardrails.
- `policy/` directory: Declarative YAML for limits & allow‑lists.
- `docs/generated/` (git‑ignored) for draft content awaiting curation.

### Open Research Questions (To Be Answered Before Build)
1. Best lightweight metric for image quality regression without subjective bias (SSIM? CLIP similarity? Size heuristics?).
2. License inference confidence thresholds—when to escalate vs. block automatically.
3. Optimal prompt budget & tool selection policy for multi‑stage reasoning without cost runaway.
4. Feasibility of unified hash catalog for local models (performance vs. benefit trade‑off).

### Activation Definition of Done (When Eventually Implemented)
- All prerequisite gates satisfied; owner sign‑off recorded.
- At least three playbooks run in "dry‑run" mode with accurate artifact generation and zero unsafe actions.
- Guardrail tests: simulation suite proves enforcement (e.g., blocked oversized download, rejected unapproved source).
- Observability: Central timeline view listing plan → steps → artifacts with drill‑down logs.

> REMINDER: This entire layer is aspirational and **must not** influence scoping, acceptance, or delivery criteria for Phases 1‑3 unless explicitly re‑authorized.
