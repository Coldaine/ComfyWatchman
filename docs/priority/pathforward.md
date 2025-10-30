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

    if multi_results and len(multi_results) > 0:
        # Return best match (already sorted by confidence)
        best_result = multi_results[0]
        self.logger.info(
            f"Multi-strategy found: {best_result.civitai_name} "
            f"(ID: {best_result.civitai_id}, confidence: {best_result.confidence})"
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
```

**Test Case 2: Regular Model (Should Use Simple Search)**
```python
model_info = {
    "filename": "sd_xl_base_1.0.safetensors",
    "type": "checkpoints"
}

result = civitai_search.search(model_info)
# Expected: FOUND (via simple search, multi-strategy not needed)
```

**Test Case 3: Non-existent Model**
```python
model_info = {
    "filename": "definitely_does_not_exist_xyz123.safetensors",
    "type": "checkpoints"
}

result = civitai_search.search(model_info)
# Expected: NOT_FOUND (after both simple and multi-strategy attempts)
# metadata should show search_attempts=2
```

#### Success Criteria
- [ ] Multi-strategy search called when simple search returns no exact match
- [ ] NSFW models with explicit terms found successfully
- [ ] Simple models still found quickly (no performance regression)
- [ ] Logging shows which strategy found the model
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
# In search.py, after successful multi-strategy search:

if result.status == "FOUND" and result.confidence == "fuzzy":
    # This was hard to find - cache it for next time
    direct_backend.add_known_model(
        name=result.filename,
        civitai_id=result.civitai_id,
        auto_added=True
    )
```

#### Decision Point

**Wait until Feature 1 is deployed**, then assess:
- If multi-strategy search finds everything → known_models.json is optional
- If some models still fail → implement Option C (auto-populate)
- If performance is slow → implement Option B (helper script)

---

### **Feature 3: Enhanced Qwen Integration** [ROADMAP Phase 1B]

**Priority:** MEDIUM (Fallback for truly hard cases)
**Complexity:** HIGH (AI agent integration, error handling)
**Impact:** MEDIUM (Catches the remaining ~10% of failed searches)

#### Current State

`QwenSearch` exists but returns placeholder `NOT_FOUND`:
```python
# search.py:880
def search(self, model_info: Dict[str, Any]) -> SearchResult:
    filename = model_info["filename"]
    return SearchResult(
        status="NOT_FOUND",
        filename=filename,
        metadata={"reason": "not implemented yet"},
    )
```

#### What to Build

**Phase 1B Goal:** Make Qwen actually call an LLM and search intelligently

**Integration Points:**
1. Qwen receives `model_info` that failed multi-strategy search
2. Qwen has access to:
   - `known_models.json` (check if manually added)
   - `search_by_id()` (if it discovers a Civitai ID)
   - `search_multi_strategy()` (can retry with different parameters)
   - Web search via Tavily API
3. Qwen returns `SearchResult` with high confidence or UNCERTAIN status

**Implementation:**
```python
def search(self, model_info: Dict[str, Any]) -> SearchResult:
    filename = model_info["filename"]
    model_type = model_info.get("type", "")

    # Build agentic prompt
    prompt = self._build_agentic_prompt(filename, model_type)

    # Write prompt to temp file for agent execution
    result_file = self.temp_dir / f"{sanitize_filename(filename)}_result.json"
    prompt_file = self.temp_dir / f"{sanitize_filename(filename)}_prompt.txt"

    with open(prompt_file, "w") as f:
        f.write(prompt)

    # Execute Qwen agent (via qwen2.5-coder or similar)
    try:
        result = self._execute_qwen_agent(prompt_file, result_file, timeout=900)
        return self._parse_qwen_result(result, filename)
    except TimeoutError:
        return SearchResult(
            status="ERROR",
            filename=filename,
            error_message="Qwen agent timed out after 15 minutes"
        )
```

#### Success Criteria
- [ ] Qwen actually invokes LLM (not placeholder)
- [ ] >80% accuracy on models that failed multi-strategy
- [ ] Graceful degradation (system works if Qwen unavailable)
- [ ] Result caching (30-day TTL)
- [ ] Can discover models via web search + HuggingFace

---

### **Feature 4: Embedding (Textual Inversion) Support** [ROADMAP Phase 2]

**Priority:** MEDIUM (Common missing dependency)
**Complexity:** LOW (Uses existing infrastructure)
**Impact:** MEDIUM (Handles new model type)

#### Current State

Embeddings are not detected or downloaded:
```python
# Workflow JSON might contain:
{
  "inputs": {
    "text": "photo of a woman, embedding:easy_negative"
  }
}

# Current scanner.py: Doesn't detect "embedding:easy_negative"
# Current search.py: Doesn't filter by TextualInversion type
```

#### What to Build

**1. Detection** (`scanner.py`)
```python
def extract_models_from_workflow(self, workflow_path: str) -> List[Dict]:
    # Add regex pattern:
    embedding_pattern = r"embedding:(\w+)"

    for match in re.finditer(embedding_pattern, text):
        embedding_name = match.group(1)
        models.append({
            "filename": f"{embedding_name}.pt",  # or .safetensors
            "type": "embeddings",
            "node_id": node_id,
            "workflow": workflow_path
        })
```

**2. Search** (`search.py`)
```python
def _get_type_filter(self, model_type: str) -> Optional[str]:
    type_mapping = {
        "checkpoints": "Checkpoint",
        "loras": "LORA",
        "vae": "VAE",
        "embeddings": "TextualInversion",  # Add this
        # ...
    }
    return type_mapping.get(model_type)
```

**3. Download** (`download.py`)
```python
# Already handles this via model_type field:
target_dir = config.models_dir / model_type
# embeddings → ComfyUI/models/embeddings/
```

#### Testing
```python
test_workflow = {
    "nodes": {
        "1": {
            "inputs": {
                "text": "photo, embedding:easy_negative"
            }
        }
    }
}

# Should detect:
# {"filename": "easy_negative.pt", "type": "embeddings"}

# Should search Civitai with type filter:
# GET /api/v1/models?query=easy_negative&types=TextualInversion

# Should download to:
# ComfyUI/models/embeddings/easy_negative.pt
```

---

### **Feature 5: Guardrailed Scheduler** [ROADMAP Phase 2 / RIGHT_SIZED_PLAN Phase 1]

**Priority:** MEDIUM-LOW (Nice to have, not critical)
**Complexity:** HIGH (Background daemon, resource monitoring)
**Impact:** HIGH (Makes tool truly automatic)

#### What to Build

**New Module:** `src/comfyfixersmart/scheduler.py`

```python
class Scheduler:
    """
    Background scheduler that runs workflow analysis at intervals.

    Features:
    - Configurable interval (default: 120 minutes)
    - VRAM guard (skip if GPU memory < threshold)
    - Machine awake detection (skip if sleeping/hibernating)
    - Graceful shutdown on SIGTERM
    - State persistence (next run time, last results)
    """

    def __init__(
        self,
        interval_minutes: int = 120,
        min_vram_gb: float = 8.0,
        enable_vram_guard: bool = True
    ):
        self.interval = timedelta(minutes=interval_minutes)
        self.min_vram_gb = min_vram_gb
        self.enable_vram_guard = enable_vram_guard

    def start(self):
        """Start background scheduler loop"""

    def stop(self):
        """Graceful shutdown"""

    def _should_run(self) -> Tuple[bool, str]:
        """Check if conditions met to run analysis"""
        # Check VRAM available
        # Check machine awake
        # Check not running already
```

**CLI Integration:**
```bash
# Start scheduler in background
comfywatchman --scheduler

# Stop scheduler
comfywatchman --scheduler-stop

# Check scheduler status
comfywatchman --scheduler-status
```

**Configuration:** `config/default.toml`
```toml
[schedule]
enabled = false
interval_minutes = 120
min_vram_gb = 8.0
enable_vram_guard = true
```

#### Use Case
```bash
# User starts scheduler once:
comfywatchman --scheduler

# System runs every 2 hours automatically:
# - Scans ComfyUI/user/workflows for new .json files
# - Identifies missing models
# - Searches and downloads automatically
# - User never has to run the tool manually
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

- [ ] Multi-strategy is only defined, never called (confirms Feature 1 is needed)
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
