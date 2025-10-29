# Python Port Review Prompt

## Context

Five bash scripts in `civitai_tools/bash/` have been ported to Python modules in `civitai_tools/python/`. These tools are designed for Civitai model search and download, intended for:
1. **Immediate use:** Qwen AI agent will call them via CLI
2. **Future integration:** Will become MCP tools for Claude Desktop (Phase 3, Weeks 9-14 per ROADMAP.md)
3. **Code reuse:** Eventually integrate into `src/comfyfixersmart/search.py` backends

## Your Task

Perform a comprehensive code review of the Python ports, comparing them against the bash originals to ensure:
- **Algorithm fidelity:** Core logic is preserved exactly
- **Feature completeness:** All bash functionality is replicated
- **Code quality:** Follows Python best practices
- **MCP readiness:** Architecture supports future async MCP integration
- **Error handling:** Proper exception handling and status reporting

---

## Files to Review

### 1. Advanced Search
- **Original:** `civitai_tools/bash/advanced_civitai_search.sh` (639 lines)
- **Port:** `civitai_tools/python/advanced_search.py` (~550 lines)

**Critical algorithms to verify:**
- Scoring algorithm (bash lines 91-133 → Python `ModelScorer.calculate_score()`)
  - Exact match: +100 points
  - Partial match: +50 points
  - Keyword matches: +25 per keyword
  - Direct ID bonus: +50 points
  - Safetensors format: +5 points
- Tag extraction (bash lines 456-478 → Python `TagExtractor.extract_tags()`)
  - Anatomical/style/content term lists match
  - Stop word filtering works correctly
  - Minimum word length (>2 chars) enforced
- Cascading search strategy (bash lines 353-563 → Python `AdvancedCivitaiSearch.search()`)
  - Order: known_models → query_nsfw → query_no_nsfw → tags → creator
  - Each strategy runs only if previous ones failed or returned < N results
  - Results are deduplicated by model_id
  - Final output is sorted by score descending

**Check:**
- [ ] Scoring produces identical results for same inputs
- [ ] Tag extraction identifies same tags as bash version
- [ ] Known models database (known_models.json) is loaded correctly
- [ ] All API parameters match bash version (nsfw, types, limit, sort)
- [ ] JSON output format matches bash script's structure

---

### 2. Direct Downloader
- **Original:** `civitai_tools/bash/civitai_url_downloader.sh` (301 lines)
- **Port:** `civitai_tools/python/direct_downloader.py` (~370 lines)

**Critical features to verify:**
- Model ID extraction (bash lines 31-45 → Python `extract_model_id()`)
  - Regex pattern matches: `https://civitai.com/models/{id}` and `https://civitai.com/models/{id}/{name}`
  - Handles numeric IDs directly
- SHA256 verification (bash lines 142-152 → Python `calculate_sha256()`)
  - Uses same hashing algorithm
  - Compares case-insensitive
  - Deletes file on mismatch
- Download flow (bash lines 200-298 → Python `download_by_id()`)
  - Fetches from `/api/v1/models/{id}` (not search API)
  - Selects primary file or largest file as fallback
  - Constructs download URL: `https://civitai.com/api/download/models/{version_id}`
  - Shows progress during download

**Check:**
- [ ] ID extraction works for all URL formats (with/without model name)
- [ ] SHA256 calculation matches standard implementations
- [ ] File is deleted if hash verification fails
- [ ] Primary file selection logic matches bash (prefer primary, fallback to largest)
- [ ] Download uses streaming to handle large files
- [ ] Progress indicator works (or at least doesn't break)

---

### 3. Search Diagnostics
- **Original:** `civitai_tools/bash/debug_civitai_search.sh` (300 lines)
- **Port:** `civitai_tools/python/search_diagnostics.py` (~350 lines)

**Critical features to verify:**
- Diagnostic flow (bash lines 113-253 → Python `diagnose_search()`)
  - Tests query with nsfw=true
  - Tests query without nsfw parameter
  - Tests tag-based search for extracted tags
  - Displays API URLs and HTTP status codes
  - Shows raw item counts
- Diagnosis logic (bash lines 256-286 → Python `_generate_diagnosis()`)
  - Detects zero results (term filtering)
  - Detects results that don't match search term
  - Detects API failures
- Suggestions (bash lines 289-300 → Python `_generate_suggestions()`)
  - Suggests direct ID lookup
  - Suggests alternative tags
  - Suggests checking creators

**Check:**
- [ ] All search strategies are tested in same order as bash
- [ ] Diagnostic messages categorize issues correctly
- [ ] Suggestions are actionable and match bash version
- [ ] JSON export includes all diagnostic data
- [ ] HTTP status codes are captured and displayed

---

### 4. Batch Downloader
- **Original:** `civitai_tools/bash/batch_civitai_downloader.sh` (207 lines)
- **Port:** `civitai_tools/python/batch_downloader.py` (~240 lines)

**Critical features to verify:**
- Retry logic with exponential backoff
  - Max retries = 3 (configurable)
  - Wait time = attempts * 2 seconds
- Batch processing
  - Processes models sequentially
  - Delays between successful downloads (rate limiting)
  - Continues on failure (or stops based on flag)
- Summary reporting
  - Counts: total, successful, failed, skipped
  - Per-job status tracking

**Check:**
- [ ] Retry logic uses exponential backoff (2s, 4s, 6s)
- [ ] Delay between downloads is configurable
- [ ] Can read JSON input files with model list
- [ ] Summary export includes all job details
- [ ] continue_on_failure flag works correctly

---

### 5. Fuzzy Finder
- **Original:** `civitai_tools/bash/fuzzy_civitai_finder.sh` (388 lines)
- **Port:** `civitai_tools/python/fuzzy_finder.py` (~230 lines)

**Critical features to verify:**
- Interactive selection
  - Displays candidates with confidence indicators (🟢 high, 🟡 medium, 🔴 low)
  - Accepts numeric input (1-10) to select
  - Accepts 'i' + number for detailed info
  - Accepts 'q' to quit
- Auto-download mode
  - Downloads top result without interaction
- Batch mode
  - Processes multiple search terms
  - Exports results to JSON

**Check:**
- [ ] Confidence indicators map correctly (high=🟢, medium=🟡, low=🔴)
- [ ] Interactive prompt accepts all input formats
- [ ] Auto-download mode works without prompts
- [ ] Batch mode processes all terms and exports results
- [ ] KeyboardInterrupt (Ctrl+C) is handled gracefully

---

## General Code Quality Review

For ALL modules, check:

### 1. Type Safety
- [ ] All functions have type hints for parameters and return values
- [ ] Dataclasses are used for structured data (not dicts where possible)
- [ ] Enums are used for status/strategy/level constants
- [ ] Optional types are used correctly (Optional[T] for nullable values)

### 2. Error Handling
- [ ] Network errors are caught and logged
- [ ] JSON parsing errors are handled
- [ ] File I/O errors are handled
- [ ] API errors (4xx, 5xx) produce clear error messages
- [ ] No bare `except:` clauses (always specify exception types)

### 3. Code Structure
- [ ] Functions are single-purpose and focused
- [ ] No function exceeds ~50 lines (except main orchestrators)
- [ ] Magic numbers are replaced with named constants
- [ ] Duplicate code is extracted into helper methods
- [ ] Class methods are properly organized (public → private)

### 4. Documentation
- [ ] Module docstring explains purpose and bash original
- [ ] All classes have docstrings
- [ ] All public methods have docstrings with Args/Returns sections
- [ ] Complex algorithms have inline comments
- [ ] "Port of:" references point to bash line numbers

### 5. CLI Interface
- [ ] argparse is used consistently
- [ ] Help text is clear and includes examples
- [ ] Required vs optional arguments are correct
- [ ] Default values match bash script defaults
- [ ] Exit codes indicate success (0) or failure (non-zero)

### 6. MCP Readiness
- [ ] Functions can be called programmatically (not CLI-only)
- [ ] Return values are JSON-serializable dicts/dataclasses
- [ ] No global state or mutable singletons
- [ ] Functions are pure (same inputs → same outputs)
- [ ] Architecture supports future async refactor (no blocking I/O in loops)

---

## Testing Recommendations

### Unit Tests to Write
For each module:
1. Test with valid inputs (happy path)
2. Test with invalid inputs (error handling)
3. Test edge cases (empty results, malformed JSON, etc.)
4. Mock API calls to avoid actual network requests

### Integration Tests to Write
1. Test bash vs Python output equivalence:
   ```bash
   # Run bash script
   bash civitai_tools/bash/advanced_civitai_search.sh "test query" > bash_output.json

   # Run Python script
   python -m civitai_tools.python.advanced_search "test query" > python_output.json

   # Compare (ignoring timestamps/metadata)
   diff <(jq 'del(.metadata.timestamp)' bash_output.json) \
        <(jq 'del(.metadata.timestamp)' python_output.json)
   ```

2. Test with known problematic models:
   - Model 1091495: "Better detailed pussy and anus v3.0"
   - Model 670378: "Eyes High Definition V1"
   - Verify direct ID lookup works for both

3. Test full workflow:
   - Search → Select top result → Download → Verify hash

---

## Expected Deliverables

After completing the review, provide:

### 1. Review Summary Document
Create: `docs/reviews/python_port_review_results.md`

Structure:
```markdown
# Python Port Review Results

## Executive Summary
- Overall assessment: [PASS/FAIL/NEEDS_WORK]
- Critical issues found: [count]
- Non-critical issues found: [count]

## Module-by-Module Results

### advanced_search.py
- Algorithm fidelity: ✅/❌ [details]
- Feature completeness: ✅/❌ [details]
- Code quality: ✅/❌ [details]
- MCP readiness: ✅/❌ [details]
- Issues found: [list]

[... repeat for each module ...]

## Critical Issues
[List issues that MUST be fixed before merge]

## Recommendations
[List nice-to-have improvements]

## Test Results
[Summary of manual testing performed]
```

### 2. Annotated Code Comments
If you find issues, add inline comments to the code:
```python
# REVIEW: This scoring logic differs from bash (lines 91-133)
# Bash adds +100 for exact match, but this adds +90
# FIX NEEDED: Change to match bash behavior exactly
def calculate_score(self, ...):
    score = 90  # Should be 100
```

### 3. Test Cases (Optional but Recommended)
Create: `tests/test_civitai_tools_python.py`

Include at least:
- One test per module verifying core algorithm
- One integration test comparing bash vs Python output
- One test for error handling

---

## Review Guidelines

### What Constitutes a PASS
- All critical algorithms match bash versions exactly
- All bash features are implemented
- Code follows Python best practices
- No critical bugs or security issues
- MCP integration is straightforward

### What Constitutes NEEDS_WORK
- Minor algorithm discrepancies (e.g., off-by-one in scoring)
- Missing non-critical features (e.g., progress bars)
- Code quality issues (e.g., missing type hints)
- Fixable with < 2 hours of work

### What Constitutes a FAIL
- Major algorithm differences that affect results
- Missing critical features (e.g., hash verification)
- Security vulnerabilities (e.g., command injection)
- Requires significant refactoring (> 4 hours)

---

## Questions to Answer

As you review, answer these:

1. **Algorithm Fidelity:**
   - Do the Python ports produce identical results to bash for the same inputs?
   - Are there any edge cases where behavior differs?

2. **Feature Completeness:**
   - Is any bash functionality missing from Python?
   - Are there any regressions in capabilities?

3. **Code Quality:**
   - Would you feel confident deploying this code?
   - Are there any obvious bugs or anti-patterns?

4. **Integration Readiness:**
   - Can Qwen call these via CLI today? (Phase 1B)
   - Can they be wrapped as MCP tools tomorrow? (Phase 3)

5. **Maintainability:**
   - If you had to add a new feature, would the architecture support it?
   - Is the code self-documenting or does it need more comments?

---

## Additional Context

### Project Roadmap (from ROADMAP.md)
- **Phase 1A (Current):** Building these tools to fix Civitai search issues
- **Phase 1B (Weeks 3-4):** Qwen will use these tools via CLI
- **Phase 3 (Weeks 9-14):** Wrap as MCP server for Claude Desktop

### Known Issues from Bash Scripts
These issues exist in bash and should NOT be carried over to Python:
1. URL encoding is basic (only handles spaces, &, +, parentheses) - Python should use urllib.parse.quote
2. jq gymnastics with base64 encoding for passing data between functions - Python should use native objects
3. No type safety or input validation - Python should add validation
4. Error messages sometimes unclear - Python should improve clarity

### References
- Bash scripts: `civitai_tools/bash/`
- Implementation plan: `docs/implementation/implementation1029.md`
- Roadmap: `docs/strategy/ROADMAP.md`
- Known models database: `civitai_tools/config/known_models.json`

---

## How to Use This Prompt

1. **Read all files mentioned** in the review scope
2. **Compare algorithms** line-by-line between bash and Python
3. **Run the code** manually with test inputs
4. **Document findings** using the template above
5. **Provide concrete recommendations** with code examples where possible

Take your time. A thorough review now prevents bugs in production later.

---

**Review Start Date:** [Fill in when you start]
**Estimated Completion Time:** 3-4 hours
**Reviewer:** [Your name/agent ID]
