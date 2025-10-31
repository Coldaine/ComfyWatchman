# FastCode1030 Implementation Brief (Revised)

## Context Snapshot
- Repository: `ComfyFixerSmart` (package `comfywatchman`).
- Focus: end-to-end search/download automation (Civitai + HuggingFace + Qwen).
- Recent change: `CivitaiSearch` now routes zero-results/no-exact-match paths through `search_multi_strategy`; `ComfyFixerCore` respects configured backend order.
- `QwenSearch` remains a stub; embedding/Textual Inversion handling is incomplete; known_models tooling is minimal.

## Mission for the Fast Coding Agent
Implement the remaining roadmap features as production functionality. The goal is to ship working code, not artificial tests or mocks. Exercise real APIs (Civitai, Qwen CLI) wherever relevant to confirm behavior.

### Scope of Work
1. **Feature 1 Hardening (real-world validation)**
   - Confirm the cascade logic works against live Civitai queries.
   - Add a lightweight CLI utility (`scripts/diagnose_cascade.py`) that takes a filename and shows the cascade steps + metadata so we can observe behavior empirically.
   - Document usage in `docs/priority/pathforward.md` (e.g., “run `diagnose_cascade.py` to verify multi-strategy success for difficult filenames”).

2. **Feature 2: Known Models Helper**
   - Implement `DirectIDBackend.add_known_model()` (input validation, normalization, atomic JSON write).
   - Provide a CLI helper (`scripts/add_known_model.py`) that adds/updates entries by hitting the real Civitai API to confirm IDs/versions before writing.
   - Update `civitai_tools/config/README.md` describing how to use the helper and recommended workflow (e.g., run cascade, add result, re-run search for instant success).

3. **Feature 3: Full Qwen Integration**
   - Replace the placeholder `QwenSearch.search()` with a real implementation that:
     * Generates the agentic prompt (existing builder).
     * Invokes the Qwen CLI (use env var `QWEN_BINARY` or default `qwen`).
     * Stores the agent’s JSON output next to other cache files (30-day TTL).
     * Handles timeouts, missing binaries, malformed JSON by logging warnings and returning `NOT_FOUND` so downstream backends can proceed.
   - Provide a small CLI harness (`scripts/run_qwen_search.py`) that lets us run Qwen search for a given filename/type and dumps the JSON result.
   - Update `docs/planning/QWEN_SEARCH_IMPLEMENTATION_PLAN.md` with real run instructions, expected caching behavior, and dependency notes.

4. **Feature 4: Embedding/Textual Inversion Support**
   - Extend `scanner.py` to detect `embedding:<name>` and similar patterns in workflow nodes; emit `ModelReference` entries pointing to `models/embeddings/<name>.pt` (and `.safetensors` if present in workflows).
   - Ensure `config.py` / `utils.determine_model_type()` map relevant nodes to `embeddings` (double-check existing mappings so we don’t regress other components).
   - Make sure `search.py` cascades treat `embeddings` as `TextualInversion` when talking to Civitai.
   - Guarantee downloads land in `models/embeddings/` (create directory if missing).
   - Provide a quick CLI (`scripts/find_embeddings.py`) that scans a workflow file and prints detected embedding names for manual validation.

### Non-Goals / Constraints
- Do **not** add or rely on artificial mocks in the product code or ancillary utilities.
- No new automated tests are required for this phase. Verification is done via the real-world CLI utilities you provide.
- Maintain existing logging conventions (`get_logger`). No raw prints except in CLI tools where UX demands it.
- Keep configuration flexible: if Feature 3 introduces toggles (e.g., `enable_qwen`, `qwen_timeout`), wire them through `SearchConfig` and `config/default.toml`.
- Preserve `known_models.json` formatting (two-space indentation) and existing keys.

### Deliverables
- Updated Python modules implementing the functionality above.
- New CLI scripts (under `scripts/`) with executable bits and usage instructions in docstrings or README sections.
- Documentation updates reflecting new workflows (pathforward roadmap, Qwen plan, known_models README, etc.).
- Manual verification notes (e.g., README snippets) describing how to run the new tools and observe success.

### Suggested Sequence
1. Build the cascade diagnostic CLI and validate behavior against real filenames (recreates the old manual “cascade check” process).
2. Implement `add_known_model()` + helper script; use the diagnostic CLI to confirm the new entry produces instant success.
3. Wire Qwen end-to-end (CLI + caching + fallback) and test with a real CLI run (include instructions for setting `QWEN_BINARY`).
4. Add embedding detection/support; verify by running the embedding finder on a workflow and running the main CLI to ensure embeddings are queued for download.

### Completion Criteria
- Each feature’s CLI utility demonstrates working behavior without mocks.
- Main CLI (`comfywatchman --auto`) benefits from the new functionality (cascade faster when known model added, Qwen invoked when enabled, embeddings recognized).
- Docs clearly explain how to exercise each new capability manually.
- No failing lint or runtime errors when tools are executed in a real environment.

When finished, provide a change summary and detail how you verified each feature via the CLI utilities.
