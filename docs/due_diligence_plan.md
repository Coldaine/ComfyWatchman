# ComfyUI-Copilot Fork Due Diligence Plan

## Objective

Decide whether adopting the existing ComfyUI-Copilot codebase allows ComfyWatchman to leapfrog Phase 1 functionality with minimal adaptation while remaining compatible with scheduled, headless operation, static reporting, and future RAG expansion.

## Preparation

- Identify the local repository path (`$COPILOT_REPO`).
- Confirm required Python and Node versions; note additional system dependencies.
- Create an isolated Python virtual environment dedicated to evaluation.
- Select 5–10 representative ComfyUI workflows spanning: fully runnable, missing models, missing nodes, ambiguous assets, version mismatches.

## Licensing Review

- Read `$COPILOT_REPO/LICENSE` and document the upstream license type.
- Install the project’s dependencies and capture third-party license obligations (`pip install pip-licenses && pip-licenses > licenses.txt`).
- Flag any copyleft or restrictive terms that would affect redistribution or closed-source integrations.

## Repository Reconnaissance

- Use ripgrep to map critical components:
  - `rg -n "__main__|if __name__ ==|argparse|click|typer" "$COPILOT_REPO"` for CLI/headless entry points.
  - `rg -n "Agent|planner|tool|llm|reason"` for backend agent architecture.
  - `rg -n "@comfyorg|comfyui-frontend|canvas|widget"` for frontend coupling.
  - `rg -n "sqlalchemy|sqlite|Dexie|IndexedDB|localforage"` for database usage.
  - `rg -n "civitai|huggingface|huggingface_hub|hf_hub"` for model/node retrieval.
- Catalogue candidate modules, scripts, and their dependencies; note tight integration points that may require adaptation.

## Environment Setup

- Activate the evaluation venv and run the documented install process (`pip install -e .`, `pip install -r requirements.txt`, etc.).
- Only build the React frontend if backend imports fail without it; record any optional or required build steps.
- Document necessary environment variables (API keys, configuration files) for baseline operation.

## Backend Import Smoke Test

- Launch a Python REPL inside the venv and import the identified agent/backend modules.
- Record any implicit dependencies (config files, env vars) that must be satisfied for a successful import.

## Database Dependency Assessment

- Locate SQLAlchemy engine creation, migration scripts, and schema definitions.
- Stand up the database using the project’s recommended method (SQLite or equivalent). Capture the steps required to initialize and migrate it.
- Run a simple backend operation to confirm the DB can be provisioned quickly and behaves as expected.
- Document data written during analysis runs: tables, row counts, and how persistence is used.

## Headless Workflow Analysis Capability

- Identify functions or CLI commands that accept a workflow JSON and emit diagnostics/remediation guidance.
- Exercise these entry points with one of the sample workflows; record invocation commands, inputs, outputs, and runtime behavior.
- Confirm the analysis pipeline executes without requiring the React UI at runtime.

## Output Artifact Assessment

- Determine whether the backend emits structured outputs suitable for our static dashboard: runnability status, missing assets, remediation steps, indices.
- If outputs differ, sketch the minimal adapter needed to convert native results into:
  - `runnability_report.json`
  - `remediations.json`
  - `indices/*.json` (nodes and models)
- Document the data schema for each artifact.

## Model and Node Resolution Evaluation

- Test the Civitai integration by searching for known models; log the accuracy and metadata returned.
- Trigger fallback mechanisms (e.g., Hugging Face CLI) by supplying ambiguous or missing models; verify evidence and confidence scoring.
- Capture how the system handles uncertainty and whether it produces reviewable rationale.

## Scheduling and Guardrail Fit

- Measure CPU/GPU utilization and runtime for analysis tasks to ensure compatibility with the 2-hour cadence.
- Identify hook points for enforcing VRAM availability or idle-state checks before execution.
- Note any long-running processes or background services that might interfere with scheduled runs.

## Security and Telemetry Review

- Audit the codebase for telemetry endpoints or unsolicited network calls.
- Confirm secrets (API keys) are sourced via environment variables and redacted in logs.
- Review logging defaults to ensure sensitive data is not persisted.

## Pilot Scenario Runs

- For each representative workflow, execute analysis in dry-run mode (and apply mode if available).
- Collect all generated artifacts (JSON reports, logs) and evaluate recommendation quality versus expectations.
- Note successes, gaps, and any manual intervention required.

## Adapter Blueprint (Conditional)

- If the fork appears viable, draft a thin overlay design:
  - Scheduler inputs (workflow directory, cached nodes/models).
  - Invocation of upstream agent.
  - Normalization layer to produce dashboard artifacts.
  - Optional apply mode for automated remediation.
- Estimate effort in developer-days to achieve Phase 1 parity using the forked baseline.

## Decision Report

- Summarize findings for each evaluation step with supporting evidence.
- State pass/fail against key criteria:
  - Headless execution viability.
  - Database setup overhead and stability.
  - Artifact readiness for static dashboard integration.
  - Model/node resolution performance.
- Provide a risk assessment, mitigation paths, and final recommendation (Go with adapter, or revert to selective feature adoption).
- Include effort estimates and recommended follow-up tasks.
