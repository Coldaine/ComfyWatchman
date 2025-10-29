## feat: Advanced Civitai search + downloader suite, adapters, and tooling overhaul

This PR is a large, multi-module update that brings an advanced Civitai search and download workflow to ComfyWatchman, along with a unified lint/format toolchain and extensive documentation. It also introduces an Architecture Decision Record (ADR) for the project’s Python version policy.

### What’s included

- Civitai advanced search and download suite
  - `src/comfyfixersmart/civitai_tools/advanced_search.py`: multi-strategy search
  - `src/comfyfixersmart/civitai_tools/direct_id_backend.py`: known models + direct-ID lookup
  - `src/comfyfixersmart/civitai_tools/direct_downloader.py`: resilient file downloader
  - `src/comfyfixersmart/civitai_tools/batch_downloader.py`: batch with retry
  - `src/comfyfixersmart/civitai_tools/fuzzy_finder.py`: interactive fuzzy finder
  - `src/comfyfixersmart/civitai_tools/search_debugger.py`, `search_diagnostics.py`
  - Bash helpers under `civitai_tools/bash/` with README
- Core and CLI/refactors
  - `src/comfyfixersmart/search.py`: multi-backend search architecture, hooks for Civitai, HF, Qwen
  - `src/comfyfixersmart/core.py`, `scanner.py`, `inventory.py`, `download.py`, `state_manager.py`: orchestration + state/tracking improvements and compat shims
  - `src/comfyfixersmart/cli.py`: modernized CLI; primary command remains `comfywatchman`
  - `src/comfyfixersmart/logging.py`, `utils.py`: structured logging and helper upgrades
  - Adapters: ModelScope fallback and Copilot integration stubs refined
- Documentation
  - Design/strategy notes, usage examples, and implementation docs
  - ADR-0001: Python Version Policy (docs/adr/0001-python-version-policy.md)
  - Civitai search notes and implementation guidance
- Tooling
  - Migrate to a Ruff-only toolchain (replacing Black + flake8)
  - `pyproject.toml` updated: ruff config, excludes, pyupgrade ignores for py37 target
  - Add `.kilocode/mcp.json` for AI agent tooling consistency

### Motivation

ComfyWatchman now provides robust, multi-strategy discovery and retrieval of models referenced by ComfyUI workflows. This enables better automation, recovery for problematic models, and easier diagnostics when upstream metadata is inconsistent.

### Scope and impact

- Adds 12,755 LOC and removes ~2,386 LOC across 73 files (see `git diff --stat`).
- Introduces new public modules under `comfyfixersmart.civitai_tools`.
- Refactors search, state tracking, and CLI layers to support advanced workflows.
- Aligns linting to Ruff for speed and simplicity.

### Breaking/behavior changes to note

- CLI: `comfywatchman` is the canonical entry point. If prior `comfyfixer` aliasing is expected, we should add/restore an alias before merge to avoid surprises in scripts.
- Config semantics tightened in places; default paths and validation behavior changed and will need test updates (see Quality Gates below).

### ADR-0001: Python version policy

- Accepted policy: Require Python 3.12+, test/support 3.13; hold on 3.14 for now.
- Current branch does NOT yet flip `requires-python` nor the Ruff target to 3.12; this PR documents the policy and sets the foundation. Follow-up tasks below.

### Quality gates (current status)

- Lint: Ruff reports issues primarily in demo/test/legacy files (e.g., import order, trailing whitespace). Many are autofixable. Recommendation: run `ruff check --fix` and address remaining issues pre-merge or in a fast follow.
- Tests: Failing broadly across unit, functional, and integration suites. Key themes:
  - `Config` API deltas: validation messages, env var overrides, missing properties/methods (e.g., `get_missing_models_file`, `get_resolutions_file`), and differing default path handling.
  - Logging timestamp format expectations (UTC vs local) and API aliasing (`setup_logging` vs `get_logger`).
  - Search stack expectations: several mocks assume older behaviors and shapes; new backends and results change shapes and edge-cases.
  - CLI arg parsing: changed flags/semantics (tests expecting older `comfyfixer` behaviors).
  - File/path utilities: stronger validation and formatting changes (e.g., `format_file_size`, `sanitize_filename`).

Given the scope and refactors, we should treat test failures as the next integration phase:

1) Lock interfaces where stable, update the tests to target new behavior; 2) where we intend backward compatibility, add shims to preserve legacy outputs and messages.

### Follow-ups requested before merge (or immediately after, if we split)

- Packaging/tooling
  - [ ] Update `requires-python` to `>=3.12` and set Ruff `target-version = "py312"` per ADR-0001.
  - [ ] CI matrix: required 3.12, allowed 3.13; gate on `ruff check` and tests.
- Lint/tests cleanup
  - [ ] Run Ruff with `--fix` on repo and resolve non-autofixable warnings (legacy/demo OK to exclude).
  - [ ] Update tests to the new `Config`, logging, CLI, and search behaviors; or restore legacy aliases where compatibility is desired.
- CLI UX
  - [ ] Add `comfyfixer` alias if needed to avoid breaking existing scripts.
- Docs
  - [ ] README: call out the new Civitai toolkit and basic usage, plus Python 3.12+ requirement from ADR-0001.

### How I reviewed this change

- Compared commits against `origin/master`:
  - Notable commits include the Civitai suite additions, CLI/core refactors, state manager compatibility, and the Ruff migration. See `git log --oneline origin/master..HEAD` for full list.
- Assessed file-level changes: see diffstat for distribution by directory.
- Executed test suite and linter locally to surface regressions and compilation issues.

### Manual verification suggestions (smoke tests)

- Search
  - Run `demonstrate_civitai_advanced_search.py` locally with `CIVITAI_API_KEY` set; verify that direct-ID and fuzzy strategies resolve real models.
- Batch download
  - Use `civitai_tools/bash/batch_civitai_downloader.sh` with a small CSV of model IDs; confirm downloaded files and logs.
- CLI
  - Run `comfywatchman --help` and basic scan-only mode. Confirm state output and logs are created under the configured directories.

### Risks

- Test suite is currently red; merging as-is will regress CI unless the suite is updated or temporarily quarantined.
- Behavior changes in CLI/config may break existing automation until shims/aliases land.

### Request for reviewers

- Architecture/API: please focus on `search.py`, `core.py`, `config.py`, CLI surfaces, and new civitai_tools APIs.
- DX/Tooling: verify Ruff migration and pyproject settings meet team expectations; confirm we want to flip to py312 imminently per ADR.

---

Thanks for reviewing this mega-PR. I’m happy to split targeted follow-ups for: (1) tests alignment, (2) CLI compatibility aliasing, and (3) packaging/CI updates per ADR-0001.
