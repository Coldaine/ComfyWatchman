# Path Forward: Multi-Strategy Search Integration

**Date:** 2025-10-29
**Branch:** `feature/integrate-civitai-tools`
**Priority:** HIGH - Unblocks NSFW model search (67% failure rate currently)

---

## Executive Summary

**CRITICAL DISCOVERY:** Multi-strategy adaptive search is **implemented but not used**. The code exists (280+ lines, `search.py:277-558`) but the main workflow doesn't call it.

**Current Behavior:**
```python
search() → DirectIDBackend → Simple API search → NOT_FOUND (stops here)
```

**Intended Behavior:**
```python
search() → DirectIDBackend → Simple API search → Multi-Strategy Search → Qwen fallback → NOT_FOUND
```

**The Fix:** Wire up `search_multi_strategy()` to be called when simple search fails.

---

## Path Forward: Next 5 Features

### ✅ Prerequisites (Already Complete)
- DirectIDBackend integrated into search layer
- Automatic Python downloads operational
- CivitaiBatchDownloader with hash verification working
- State tracking and error handling functional

---

### **Feature 1: Wire Up Multi-Strategy Search** [CRITICAL]

**Priority:** 🔥 HIGHEST (Unblocks 67% of NSFW searches)
**Complexity:** LOW (20-30 lines of code)
**Impact:** HIGH (Makes existing 280+ lines of code actually work)

#### Problem Statement
Multi-strategy search exists at `search.py:277-558` with these capabilities:
- Enhanced NSFW multi-level search with different sort orders
- NSFW parameter combinations (nsfw=true with different levels)
- Advanced tag-based search with NSFW tags
- Creator-based search
- Hidden NSFW fallback mechanisms
- Fuzzy filename matching for NSFW models

**But it's never called.** The main `search()` method stops after one simple API attempt.

#### Implementation Plan

**File:** `src/comfyfixersmart/search.py`

**Change Location:** Line ~179 in `CivitaiSearch.search()`

**Before:**
```python
else:
    # No exact filename match; do not return fuzzy 'FOUND'
    # Provide top candidate context for human review in metadata
    top = results[0]
    meta = {
        "search_attempts": 1,
        "reason": "No exact filename match on Civitai",
        "top_candidate": {
            "id": top.get("id"),
            "name": top.get("name"),
            "type": top.get("type"),
        },
    }
    return SearchResult(
        status="NOT_FOUND", filename=filename, type=model_type, metadata=meta
    )
```

**After:**
```python
else:
    # No exact filename match from simple search
    # Try multi-strategy search before giving up
    self.logger.info("Simple search failed, attempting multi-strategy search...")

    multi_results = self.search_multi_strategy(model_info)

    if multi_results:
        best_result = multi_results[0]
        if best_result.metadata is None:
            best_result.metadata = {}
        best_result.metadata["search_attempts"] = max(
            2, best_result.metadata.get("search_attempts", 1)
        )
        self.logger.info(
            "Multi-strategy found: %s (ID: %s, confidence: %s)",
            best_result.civitai_name,
            best_result.civitai_id,
            best_result.confidence,
        )
        return best_result

    # All strategies exhausted, return NOT_FOUND with context
    top = results[0] if results else None
    meta = {
        "search_attempts": 2,  # Simple + multi-strategy
        "reason": "No match found via simple or multi-strategy search",
    }
    if top:
        meta["top_candidate"] = {
            "id": top.get("id"),
            "name": top.get("name"),
            "type": top.get("type"),
        }

    return SearchResult(
        status="NOT_FOUND", filename=filename, type=model_type, metadata=meta
    )
```

**Also handle the zero-results branch:**
```python
if not results:
    self.logger.info("Simple search returned zero results, attempting multi-strategy search...")
    multi_results = self.search_multi_strategy(model_info)

    if multi_results:
        best_result = multi_results[0]
        if best_result.metadata is None:
            best_result.metadata = {}
        best_result.metadata["search_attempts"] = max(
            2, best_result.metadata.get("search_attempts", 1)
        )
        return best_result

    return SearchResult(
        status="NOT_FOUND",
        filename=filename,
        type=model_type,
        metadata={
            "search_attempts": 2,
            "reason": "Simple + multi-strategy both failed",
        },
    )
```

#### Testing Strategy

**Test Case 1: NSFW Model with Explicit Terms**
```python
model_info = {
    "filename": "Better detailed pussy and anus v3.0.safetensors",
    "type": "loras"
}

result = civitai_search.search(model_info)
# Expected: FOUND (via multi-strategy, not simple search)
# Should find model ID 1091495
# metadata["search_attempts"] == 2
```

**Test Case 2: Regular Model (Should Use Simple Search)**
```python
model_info = {
    "filename": "sd_xl_base_1.0.safetensors",
    "type": "checkpoints"
}

result = civitai_search.search(model_info)
# Expected: FOUND (via simple search, multi-strategy not needed)
# metadata["search_attempts"] == 1
```

**Test Case 3: Non-existent Model**
```python
model_info = {
    "filename": "definitely_does_not_exist_xyz123.safetensors",
    "type": "checkpoints"
}

result = civitai_search.search(model_info)
# Expected: NOT_FOUND (after both simple and multi-strategy attempts)
# metadata["search_attempts"] == 2
```

**Test Case 4: Empty Simple Search Results**
```python
model_info = {
    "filename": "blocked_by_filter_v1.safetensors",
    "type": "loras"
}

result = civitai_search.search(model_info)
# Mock simple search to return [] and multi-strategy to return one candidate.
# Expected: Found result from cascade, metadata["search_attempts"] == 2
```

#### Success Criteria
- [ ] Multi-strategy search called when simple search returns no exact match
- [ ] Multi-strategy search called when simple search returns zero results
- [ ] NSFW models with explicit terms found successfully
- [ ] Simple models still found quickly (no performance regression)
- [ ] Logging shows which strategy found the model
- [ ] `metadata["search_attempts"]` reflects total attempts (1 for simple, 2+ after cascade)
- [ ] All existing tests still pass
- [ ] New integration test verifies multi-strategy execution

#### Commit Message
```
feat: wire multi-strategy search into main workflow

- Call search_multi_strategy() when simple API search fails
- Enables 280+ lines of existing adaptive search code
- Solves NSFW model search failures (67% → <10% failure rate)
- Adds detailed logging for which strategy succeeded
- Updates metadata to show search_attempts count

Fixes the core issue where advanced search was implemented but never used.
Tests confirm NSFW models with explicit terms now discoverable.
```

---

### **Feature 2: Populate/Verify known_models.json** [OPTIONAL]

**Priority:** MEDIUM (Performance optimization, not critical)
**Complexity:** LOW (Manual data entry or web scraping)
**Impact:** MEDIUM (Instant lookups for known problematic models)

#### Revised Understanding

After discovering Feature 1, `known_models.json` is **not critical** - it's a performance optimization:

**Without known_models.json:**
- DirectIDBackend returns None
- Falls back to simple search (1-2 sec)
- Falls back to multi-strategy search (5-10 sec)
- Result: Works, but slower

**With known_models.json:**
- DirectIDBackend returns result instantly (<0.1 sec)
- Skips all search phases
- Result: 50-100x faster for known models

#### Implementation Options

**Option A: Manual Entry (Quick Start)**
```json
{
  "Better detailed pussy and anus": {
    "civitai_id": 1091495,
    "version_id": null,
    "type": "loras",
    "nsfw_level": 16,
    "notes": "Explicit anatomical terms blocked by API search"
  },
  "Eyes High Definition": {
    "civitai_id": 670378,
    "version_id": null,
    "type": "loras"
  }
}
```

**Option B: Helper Script (Scalable)**
```python
# civitai_tools/scripts/add_known_model.py

def add_known_model(model_name: str, civitai_url: str):
    """
    Parse Civitai URL and add to known_models.json

    Usage:
        python add_known_model.py \
            "Better detailed pussy and anus" \
            "https://civitai.com/models/1091495"
    """
    model_id = extract_id_from_url(civitai_url)
    model_data = fetch_model_metadata(model_id)
    update_known_models_json(model_name, model_data)
```

**Option C: Auto-populate on Success (Best Long-term)**
```python
# Requires new API: DirectIDBackend.add_known_model()
# Guarded to validate input and persist safely to JSON.
# Call after successful multi-strategy search once the helper exists.
```

#### Decision Point

**Wait until Feature 1 is deployed**, then assess:
- If multi-strategy search finds everything → known_models.json is optional
- If some models still fail → implement Option C (auto-populate)
- If performance is slow → implement Option B (helper script)
- Any debugging improvements should extend `src/comfyfixersmart/civitai_tools/search_debugger.py`
  and the existing bash wrapper instead of introducing parallel tooling.

---

### **Feature 3: Enhanced Qwen Integration** [ROADMAP Phase 1B]

**Priority:** MEDIUM (Fallback for truly hard cases)
**Complexity:** HIGH (AI agent integration, error handling)
**Impact:** MEDIUM (Catches the remaining ~10% of failed searches)

#### Configuration Dependency

Ensure `ComfyFixerCore` honors `config.search.backend_order` so Qwen runs first when enabled:
```python
if search_backends is None:
    search_backends = config.search.backend_order
```

**Testing / Acceptance**
- Unit test: instantiate `ComfyFixerCore`, leave `search_backends=None`, set `config.search.backend_order = ["qwen", "civitai"]`, and assert `ModelSearch.search_model` is invoked with `qwen` first (mock/log expectations).
- Integration smoke: run `comfywatchman --auto` with Qwen enabled and confirm log ordering shows Qwen before Civitai.

#### Current State

- `QwenSearch.search()` now shells out to the configured Qwen binary, writes prompts/results to disk, and parses the returned JSON into `SearchResult` objects.
- Cached responses are stored in `$TEMP_DIR/qwen_cache` for 30 days and marked with `metadata["cached"] = True`.
- Helper CLI: `scripts/run_qwen_search.py` executes a single lookup for manual validation (`--type`, `--node-type`, `--temp-dir`, `--cache-dir` supported).

#### Usage & Configuration Notes

- `config.search.enable_qwen`, `qwen_timeout`, `qwen_cache_ttl`, and `qwen_binary` control runtime behavior (overridable via `ENABLE_QWEN`, `QWEN_TIMEOUT`, `QWEN_CACHE_TTL`, `QWEN_BINARY`).
- Additional CLI flags can be injected with `QWEN_EXTRA_ARGS` or `config.search.qwen_extra_args`.
- When the binary is unavailable or exits non-zero, the backend logs the error and returns `NOT_FOUND` so downstream backends can proceed.

#### Validation Checklist
- [x] Qwen backend invokes the real CLI (no placeholder responses).
- [x] Graceful degradation when agent unavailable or times out.
- [x] Cached responses reused within 30-day TTL.
- [x] Manual verification possible via `scripts/run_qwen_search.py`.

---

### **Feature 4: Embedding (Textual Inversion) Support** [ROADMAP Phase 2]

**Priority:** MEDIUM (Common missing dependency)
**Complexity:** LOW (Uses existing infrastructure)
**Impact:** MEDIUM (Handles new model type)

#### Current State

- `WorkflowScanner.extract_models_from_workflow()` recognises `embedding:<name>` patterns across widget values and node inputs, adding `ModelReference` entries that target `models/embeddings/<name>.pt`.
- Search pipeline maps the `embeddings` model type to Civitai's `TextualInversion` filter, and download targets ensure the `models/embeddings/` directory is created automatically.
- CLI helper `scripts/find_embeddings.py` lists detected embeddings within one or more workflow files for manual inspection.

#### Validation Checklist
- [x] Embedding references are surfaced during workflow scans.
- [x] Search requests include `types=TextualInversion` for embedding models.
- [x] Downloads land in `ComfyUI/models/embeddings/`, creating the directory when necessary.
- [x] CLI output confirms which textual inversions a workflow requires.

---

### **Feature 5: Guardrailed Scheduler** [ROADMAP Phase 2 / RIGHT_SIZED_PLAN Phase 1]

**Priority:** MEDIUM-LOW (Nice to have, not critical)
**Complexity:** HIGH (Background daemon, resource monitoring)
**Impact:** HIGH (Makes tool truly automatic)

#### Current State

- `Scheduler` (see `src/comfyfixersmart/scheduler.py`) runs `ComfyFixerCore` on a timed interval, with optional GPU VRAM guard using `nvidia-smi`.
- CLI flags `--scheduler`, `--scheduler-interval`, `--scheduler-min-vram`, and `--scheduler-disable-vram-guard` control scheduling behavior. The loop runs in the foreground until interrupted.
- Runs respect existing CLI options: `--no-script`, `--verify-urls`, workflow overrides, and custom backend lists.

#### Usage
```bash
# Run scheduler every 2 hours with default VRAM guard (8 GB)
comfywatchman --scheduler --scheduler-interval 120

# Run every 30 minutes without VRAM guard (e.g., CPU-only machines)
comfywatchman --scheduler --scheduler-interval 30 --scheduler-disable-vram-guard
```

---

## Agent Review Prompt

**Task:** Verify this path forward accounts for all integration points in the codebase.

### Search and Review Instructions

Please perform the following searches and analysis to verify nothing was missed:

#### 1. Search for Multi-Strategy Usage
```bash
# Find all calls to search_multi_strategy
grep -r "search_multi_strategy" src/ --include="*.py"

# Expected: Should only find definition, not calls from main workflow
# After Feature 1: Should find calls from CivitaiSearch.search()
```

**Questions:**
- Is `search_multi_strategy()` called from anywhere currently?
- Are there config options to enable/disable multi-strategy search?
- Is there a CLI flag to force multi-strategy search?

#### 2. Search for DirectIDBackend Integration Points
```bash
# Find all DirectIDBackend imports and usage
grep -r "DirectIDBackend" src/ --include="*.py"

# Check if known_models.json exists and has content
find . -name "known_models.json" -exec cat {} \;
```

**Questions:**
- Is DirectIDBackend only used in search.py or elsewhere?
- Does known_models.json exist? Is it populated or empty?
- Are there scripts to populate known_models.json?

#### 3. Check Backend Order Configuration
```bash
# Search for backend_order configuration
grep -r "backend_order" src/ config/ --include="*.py" --include="*.toml"

# Look for search backend registration
grep -r "register.*backend\|add.*backend" src/comfyfixersmart/search.py
```

**Questions:**
- What is the current `config.search.backend_order`?
- When multi-strategy is wired up, will it be called in the right order?
- Is there a way to enable multi-strategy via config without code changes?

#### 4. Check for Other Adaptive Search Code
```bash
# Search for other search-related methods that might not be used
grep -r "def _search" src/comfyfixersmart/search.py | grep -v "    #"

# Look for any TODO or FIXME comments in search.py
grep -r "TODO\|FIXME\|XXX\|HACK" src/comfyfixersmart/search.py
```

**Questions:**
- Are there other search helper methods that should be called?
- Any TODO comments indicating incomplete integration?
- Are all the `_search_nsfw_*` methods actually called from `search_multi_strategy()`?

#### 5. Review Test Expectations
```bash
# Find tests for search functionality
find tests/ -name "*search*" -o -name "*civitai*"

# Check what behavior tests expect
grep -r "search_multi_strategy\|multi.strategy" tests/ --include="*.py"
```

**Questions:**
- Do tests expect multi-strategy to be called automatically?
- Are there integration tests that verify the full search cascade?
- Do tests mock multi-strategy or expect it to run?

#### 6. Check CLI Integration
```bash
# Search for CLI options related to search
grep -r "argparse\|click\|@cli" src/comfyfixersmart/cli.py -A 5

# Look for search-related CLI flags
grep -r "search.*backend\|multi.*strategy" src/comfyfixersmart/cli.py
```

**Questions:**
- Can users enable multi-strategy via CLI flag?
- Is there a `--search-strategy` or `--enable-multi-strategy` option?
- Should there be a CLI option to test multi-strategy in isolation?

#### 7. Review Core Orchestration
```bash
# Check how core.py calls search
grep -r "ModelSearch\|search_model" src/comfyfixersmart/core.py -B 3 -A 10

# Look for search backend configuration in core
grep -r "backend.*order\|search.*backends" src/comfyfixersmart/core.py
```

**Questions:**
- Does core.py pass `backends` parameter to `search_model()`?
- Can users override backend order when running workflow analysis?
- Will multi-strategy be used when called via `ComfyFixerCore`?

#### 8. Check State Manager Integration
```bash
# See how search results are tracked
grep -r "mark_download_attempted\|update_download_status" src/comfyfixersmart/

# Check if multi-strategy results are logged differently
grep -r "multi.strategy\|search_attempts" src/comfyfixersmart/state_manager.py
```

**Questions:**
- Are multi-strategy search attempts tracked in state?
- Does metadata include which strategy succeeded?
- Can users see search strategy performance over time?

---

### Analysis Checklist

After running the searches above, verify:

- [ ] Multi-strategy is currently only defined, never called (confirms Feature 1 is needed)
- [ ] No config option exists to enable multi-strategy (confirms it's hardcoded off)
- [ ] DirectIDBackend is only called from one place in search.py
- [ ] known_models.json either doesn't exist or is empty/minimal
- [ ] All `_search_nsfw_*` helper methods are called from `search_multi_strategy()`
- [ ] No other adaptive search code is orphaned/unused
- [ ] Tests don't expect multi-strategy (or they're currently failing)
- [ ] CLI has no `--enable-multi-strategy` flag
- [ ] Core orchestration will automatically use multi-strategy once wired
- [ ] State manager will log which strategy succeeded once implemented

---

### Report Format

Please provide findings in this structure:

```markdown
## Agent Review: Multi-Strategy Search Integration

**Date:** [date]
**Reviewer:** [agent name/model]

### 1. Multi-Strategy Usage (grep results)
[paste grep output]

**Finding:** [Is it called? Where? Any surprises?]

### 2. DirectIDBackend Integration (grep results)
[paste grep output]

**Finding:** [How many integration points? known_models.json status?]

### 3. Backend Order Configuration (grep results)
[paste grep output]

**Finding:** [Current order? Can multi-strategy be enabled via config?]

### 4. Other Adaptive Search Code (grep results)
[paste grep output]

**Finding:** [Any other unused methods? TODOs?]

### 5. Test Expectations (grep results)
[paste grep output]

**Finding:** [Do tests expect multi-strategy? Will they break?]

### 6. CLI Integration (grep results)
[paste grep output]

**Finding:** [Any CLI flags missing? Should we add --test-multi-strategy?]

### 7. Core Orchestration (grep results)
[paste grep output]

**Finding:** [Will core.py automatically use multi-strategy?]

### 8. State Manager Integration (grep results)
[paste grep output]

**Finding:** [Is strategy tracking implemented? Need to add metadata?]

---

## Missing Integration Points

[List any integration points missed in the path forward]

## Recommended Changes to Path Forward

[Suggest modifications to Feature 1-5 based on findings]

## Additional Features Needed

[Any features discovered that aren't in the current plan]
```

---

## Summary

**Immediate Action:** Implement Feature 1 (wire up multi-strategy search)

**Timeline:**
- Feature 1: 1-2 hours (code change + testing)
- Feature 2: Optional (decide after Feature 1 results)
- Feature 3: 1-2 days (Qwen integration)
- Feature 4: 4-6 hours (embedding support)
- Feature 5: 2-3 days (scheduler implementation)

**Risk Assessment:**
- **LOW RISK:** Features 1, 2, 4 (use existing infrastructure)
- **MEDIUM RISK:** Feature 3 (LLM integration, new external dependency)
- **HIGH RISK:** Feature 5 (background daemon, resource monitoring)

**Success Metrics:**
- Feature 1: NSFW search success rate >90% (up from 33%)
- Feature 3: Overall search success rate >95% (Civitai + Qwen)
- Feature 4: Embedding workflows load successfully
- Feature 5: Zero manual intervention for 7+ days of operation

---

**Next Step:** Run the agent review prompt above to verify this plan is complete, then implement Feature 1.
