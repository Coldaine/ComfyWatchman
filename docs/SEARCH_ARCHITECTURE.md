# Search Architecture: Agentic Model Discovery

## Overview

ComfyWatchman implements an **agentic search architecture** that uses AI reasoning to intelligently discover and download missing ComfyUI models. Instead of naive keyword matching, the system employs a **multi-phase search strategy** with uncertainty handling and fallback mechanisms.

> **Implementation Status (2025-10-23):** This architecture is now the prescribed baseline for V2 runs. Default backend order MUST remain `['qwen', 'civitai']`, exact filename validation is mandatory, and `UNCERTAIN` results must be surfaced for manual review.

## Architecture Principles

### 1. Agentic Decision-Making

The search system uses **Qwen** (or other LLM agents) to:
- Analyze filenames and extract meaningful search keywords
- Decide which search strategies to employ
- Validate exact filename matches across API results
- Handle uncertainty and request human review when needed
- Learn from failures and try alternative approaches

### 2. Multi-Source Federation

Search spans multiple model repositories:
- **Civitai** - Primary source for community models (checkpoints, LoRAs, VAEs)
- **HuggingFace** - Research models and specialized tools (SAM, RIFE, upscalers)
- **ModelScope** - Alternative model hub (optional, experimental)

### 3. Doubt Handling

When the agent is uncertain about a match:
- Returns `UNCERTAIN` status with candidate list
- Provides reasoning about why confidence is low
- Requests human review before downloading
- Prevents false positive downloads

## Search Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Model Search Request                     │
│          { filename, type, node_type, workflow }             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend Selection                         │
│     config.search.backend_order = ['qwen', 'civitai']       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  QWEN AGENTIC SEARCH                         │
│                   (Primary Backend)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
              ┌────────┴────────┐
              │  Phase 1: API   │
              │  Civitai Search │
              └────────┬────────┘
                       │
                ┌──────┴──────┐
                │  Exact      │
                │  Match?     │
                └──┬─────┬────┘
                   │     │
              YES  │     │ NO
                   │     │
                   ▼     ▼
              ┌─────┐ ┌──────────────────┐
              │FOUND│ │ Phase 2: Web     │
              └─────┘ │ Search + HF      │
                      └────────┬─────────┘
                               │
                        ┌──────┴──────┐
                        │ Found on    │
                        │ HuggingFace?│
                        └──┬─────┬────┘
                           │     │
                      YES  │     │ NO
                           │     │
                           ▼     ▼
                      ┌─────┐ ┌──────────┐
                      │FOUND│ │UNCERTAIN │
                      └─────┘ │   or     │
                              │NOT_FOUND │
                              └──────────┘
```

## Phase 1: Civitai API Search

### Strategy

The agent orchestrates intelligent Civitai searches using the official API:

1. **Keyword Extraction**
   ```
   Input: "rife49.pth"
   Extract:
   - Base terms: ["rife", "49"]
   - Model type: "upscale_models"
   - Semantic: ["frame interpolation", "video"]
   ```

2. **Query Cascade** (Max 5-8 attempts)
   - Exact name without extension
   - Main keyword only
   - Alternative terms based on model type
   - Broader category search

3. **Type Filtering**
   ```python
   type_mapping = {
       'checkpoints': 'Checkpoint',
       'loras': 'LORA',
       'vae': 'VAE',
       'controlnet': 'Controlnet',
       'upscale_models': 'Upscaler',
   }
   ```

4. **Exact Match Validation**
   ```
   For each API result:
     GET https://civitai.com/api/v1/models/{id}
     For each modelVersions[]:
       For each files[]:
         if files[].name == "rife49.pth":  # EXACT match
           MATCH FOUND!
   ```

### API Usage

```bash
# Search API
GET https://civitai.com/api/v1/models
  ?query=<search_term>
  &limit=10
  &types=<model_type>
  &sort=Highest+Rated

Headers:
  Authorization: Bearer $CIVITAI_API_KEY

# Model Details API
GET https://civitai.com/api/v1/models/{model_id}
```

### Success Criteria

- Filename match must be **EXACT** (case-sensitive)
- Must verify against all versions and files
- Returns download URL: `https://civitai.com/api/download/models/{version_id}`

## Phase 2: Web Search + HuggingFace

When Civitai returns no exact matches, the agent pivots to web search:

### 1. Web Search

The agent uses a generic `web_search` tool with smart patterns:

```python
patterns = {
    r'rife.*\.pth$': "rife frame interpolation huggingface",
    r'sam_.*\.pth$': "facebook sam segment anything huggingface",
    r'.*NMKD.*\.pt$': "nmkd upscaler huggingface github",
    r'.*realesrgan.*': "realesrgan upscaler xinntao",
}

# Fallback search
"{filename} site:huggingface.co OR site:github.com"
```

### 2. Repository Extraction

From web results, extract:
```
https://huggingface.co/facebook/sam2-hiera-large/blob/main/sam2_hiera_large.safetensors
                      └────┬─────┘ └─────┬────────┘          └──────────┬───────────┘
                        user/org      repo                           file_path
```

### 3. File Verification

Agent verifies file exists using:
```bash
# Option 1: HuggingFace CLI
hf_cli download <repo> --list-files | grep <filename>

# Option 2: Web fetch repo page
curl https://huggingface.co/<repo>/tree/main
```

### 4. Download URL Construction

```python
download_url = f"https://huggingface.co/{user}/{repo}/resolve/main/{file_path}"
```

### Success Criteria

- File verified to exist in repository
- Returns `source='huggingface'` with repo metadata
- Confidence level: 'high' or 'medium' based on verification method

## Phase 3: Doubt Handling

### Uncertainty Flow

When the agent cannot confidently identify the correct model:

```json
{
  "status": "UNCERTAIN",
  "candidates": [
    {
      "source": "civitai",
      "name": "RIFE 4.9 Model",
      "url": "https://civitai.com/models/123456",
      "match_score": 0.7,
      "reason": "Similar name but different file size"
    },
    {
      "source": "huggingface",
      "name": "hfmaster/models-moved",
      "url": "https://huggingface.co/hfmaster/models-moved/rife49.pth",
      "match_score": 0.6,
      "reason": "Exact filename but unverified provenance"
    }
  ],
  "reason": "Multiple candidates found, need manual verification",
  "metadata": {
    "search_attempts": 5,
    "requires_review": true
  }
}
```

### Resolution Strategies

1. **Manual Review Prompt**
   - Present candidates to user with confidence scores
   - Show reasoning for uncertainty
   - Request explicit selection

2. **Fallback to Direct API** (if uncertainty from Qwen)
   - Try direct `CivitaiSearch` backend
   - Use simpler matching heuristics

3. **Mark as NOT_FOUND**
   - Prevents false downloads
   - Logs detailed search history for manual investigation

## Backend Architecture

### ModelSearch Coordinator

```python
class ModelSearch:
    def __init__(self):
        self.backends = {
            'qwen': QwenSearch(),        # PRIMARY - agentic
            'civitai': CivitaiSearch(),  # FALLBACK - direct API
            'modelscope': ModelScopeSearch() # OPTIONAL - experimental
        }

    def search_model(self, model_info):
        for backend_name in config.search.backend_order:
            result = self.backends[backend_name].search(model_info)
            if result.status in ['FOUND', 'ERROR', 'INVALID_FILENAME']:
                return result
        return SearchResult(status='NOT_FOUND')
```

### QwenSearch Backend (Agentic)

```python
class QwenSearch(SearchBackend):
    def search(self, model_info):
        prompt = self._build_agentic_prompt(model_info)

        # Run Qwen with tool access
        subprocess.run([
            'qwen', '-p', prompt, '--yolo'
        ], timeout=900)  # 15 min max

        result = self._parse_qwen_result()
        return result
```

**Qwen's Available Tools:**
- `bash` - Execute shell commands (API calls, CLI tools)
- `web_search` - Web search tool
- `web_fetch` - Fetch and parse web pages
- `file_write` - Write output JSON

### CivitaiSearch Backend (Direct)

```python
class CivitaiSearch(SearchBackend):
    def search(self, model_info):
        # Direct API search without agent reasoning
        response = requests.get(
            f"{self.base_url}/models",
            params={'query': query, 'types': type_filter}
        )
        return self._find_best_match(response.json())
```

**Use Cases:**
- Fallback when Qwen unavailable
- Faster for known model names
- Lower latency for batch operations

## Configuration

### Backend Order

```toml
[search]
backend_order = ["qwen", "civitai"]  # Try Qwen first, fallback to Civitai
enable_cache = true
cache_ttl_hours = 24
```

### Environment Requirements

```bash
# Required for Qwen agentic search
export CIVITAI_API_KEY="your-api-key"
export HF_TOKEN="your-hf-token"  # Optional, for private models

# Required for ModelScope (experimental)
export MODELSCOPE_API_KEY="your-ms-key"
```

### Backend Configuration

```python
@dataclass
class SearchConfig:
    backend_order: List[str] = field(default_factory=lambda: ['qwen', 'civitai'])
    enable_cache: bool = True
    civitai_api_key: Optional[str] = None

    # Qwen-specific settings
    qwen_timeout: int = 900  # 15 minutes
    qwen_max_attempts: int = 5

    # Fallback thresholds
    fallback_on_timeout: bool = True
    fallback_on_uncertain: bool = True
```

## Search Result Schema

### Success (Civitai)

```json
{
  "status": "FOUND",
  "filename": "ponyDiffusionV6XL_v6StartWithThisOne.safetensors",
  "source": "civitai",
  "civitai_id": 257749,
  "version_id": 290640,
  "civitai_name": "Pony Diffusion V6 XL",
  "version_name": "v6 (start with this one)",
  "download_url": "https://civitai.com/api/download/models/290640",
  "confidence": "exact",
  "metadata": {
    "search_attempts": 1,
    "validation_checks": 3,
    "reasoning": "Exact filename match in model version files"
  }
}
```

### Success (HuggingFace)

```json
{
  "status": "FOUND",
  "filename": "rife49.pth",
  "source": "huggingface",
  "download_url": "https://huggingface.co/hfmaster/models-moved/resolve/main/rife49.pth",
  "confidence": "high",
  "metadata": {
    "repo": "hfmaster/models-moved",
    "file_path": "rife49.pth",
    "search_attempts": 6,
    "reasoning": "File verified via HF CLI list-files"
  }
}
```

### Not Found

```json
{
  "status": "NOT_FOUND",
  "filename": "nonexistent_model.safetensors",
  "metadata": {
    "civitai_searches": 5,
    "web_searches": 3,
    "backends_tried": ["qwen", "civitai"],
    "reason": "Exhausted all search strategies. Model may be private, renamed, or removed."
  }
}
```

### Invalid Filename

```json
{
  "status": "INVALID_FILENAME",
  "filename": "big-love?modelVersionId=1990969 )",
  "error_message": "Filename contains URL parameters or invalid characters",
  "metadata": {
    "detected_issues": ["url_params", "special_chars"]
  }
}
```

## Example Search Flows

### Flow 1: Known Civitai Model

```
1. User workflow references: "hunyuan_8itchw4lk_2_40.safetensors"
2. ModelSearch invokes QwenSearch
3. Qwen analyzes filename:
   - Keywords: ["hunyuan", "8itchw4lk", "2", "40"]
   - Type: "loras" → API filter "LORA"
4. Qwen queries Civitai API: "hunyuan 8itchw4lk"
5. API returns "Move Enhancer" (ID: 1186768)
6. Qwen validates: version files contain exact filename ✓
7. Returns: FOUND (civitai, version_id=1990969)
8. Download URL: https://civitai.com/api/download/models/1990969
```

### Flow 2: HuggingFace-Only Model

```
1. User workflow references: "sam_vit_h_4b8939.pth"
2. ModelSearch invokes QwenSearch
3. Qwen tries Civitai (5 attempts):
   - "sam vit" → No exact filename matches
   - "segment anything" → No exact filename matches
4. Qwen pivots to web search:
   - Query: "facebook sam segment anything huggingface"
   - Finds: huggingface.co/facebook/sam-vit-huge
5. Qwen verifies file exists:
   - hf download facebook/sam-vit-huge --list-files
   - Confirms: sam_vit_h_4b8939.pth ✓
6. Returns: FOUND (huggingface, repo="facebook/sam-vit-huge")
7. Download URL: https://huggingface.co/facebook/sam-vit-huge/resolve/main/sam_vit_h_4b8939.pth
```

### Flow 3: Uncertain Match

```
1. User workflow references: "myCustom_model_v2.safetensors"
2. ModelSearch invokes QwenSearch
3. Qwen searches Civitai:
   - Finds 3 models with similar names
   - None have exact filename match
4. Qwen searches HuggingFace:
   - Finds 2 repos with similar files
   - File sizes differ from expected
5. Qwen returns: UNCERTAIN with candidates
6. System presents options to user:
   ```
   Multiple candidates found for "myCustom_model_v2.safetensors":

   1. [Civitai] Custom Model Collection (6.2GB)
      Match: 70% | Reason: Similar name, different version

   2. [HuggingFace] username/custom-models (5.8GB)
      Match: 60% | Reason: Exact name but unverified source

   Select option (1-2) or skip (s):
   ```
```

### Flow 4: Early Termination (Pattern Recognition)

```
1. User workflow references: "big-love?modelVersionId=1990969 )"
2. ModelSearch invokes QwenSearch
3. Qwen analyzes filename:
   - Detects: URL query parameters ('?')
   - Detects: Invalid characters (')')
4. Qwen returns: INVALID_FILENAME immediately
5. System logs warning and skips download
6. No API calls made (efficient early exit)
```

## Performance Characteristics

### Latency

- **Direct Civitai**: 1-3 seconds per search
- **Qwen Agentic**: 10-60 seconds per search (reasoning overhead)
- **Web Search Fallback**: +5-15 seconds
- **Batch Operations**: Parallelizable (rate-limited)

### Accuracy

**Before Agentic Search (Naive Matching):**
- False Positive Rate: ~70%
- Example: Downloaded "Pony Diffusion" (6.5GB) 7 times for unrelated models

**After Agentic Search (Qwen + Validation):**
- False Positive Rate: <5%
- Exact filename validation prevents wrong downloads
- Doubt handling requests human review for uncertain cases

### Resource Usage

- **API Calls**: 1-8 per model (cascading queries)
- **Rate Limiting**: 0.5s delay between searches (API-friendly)
- **Caching**: 24-hour TTL reduces redundant searches
- **Qwen Timeout**: 15 minutes max per search

## Error Handling

### Timeout Handling

```python
try:
    result = subprocess.run(['qwen', ...], timeout=900)
except subprocess.TimeoutExpired:
    # Fallback to direct CivitaiSearch
    return civitai_backend.search(model_info)
```

### API Failures

```python
if response.status_code == 429:  # Rate limit
    time.sleep(60)  # Wait 1 minute
    retry_search()

if response.status_code >= 500:  # Server error
    log_error("Civitai API unavailable")
    try_alternative_backend()
```

### Invalid Responses

```python
try:
    qwen_result = json.load(result_file)
except json.JSONDecodeError:
    log_error("Qwen produced invalid JSON")
    return SearchResult(status='ERROR', error_message="Invalid agent output")
```

## Future Enhancements

### Planned Features

1. **Multi-Agent Consensus**
   - Run multiple agents in parallel
   - Vote on best match with confidence weighting

2. **Hash-Based Lookup**
   - Calculate SHA256 of local files
   - Query: `GET /api/v1/model-versions/by-hash/{hash}`
   - Identify models without known filename

3. **Learning from User Corrections**
   - Track manual selections after UNCERTAIN results
   - Build preference model for ambiguous cases

4. **Alternative Backends**
   - ModelScope integration (China-based hub)
   - Custom enterprise model repositories
   - Local network caches

5. **Semantic Search**
   - Embed model descriptions
   - Similarity search on purpose/capabilities
   - "Find upscaler similar to RealESRGAN"

## Best Practices

### For Users

1. **API Keys**: Ensure all required keys are set
   ```bash
   # Check keys
   echo $CIVITAI_API_KEY
   ```

2. **Backend Selection**: Choose based on use case
   - `['qwen']` - Maximum accuracy, slower
   - `['civitai']` - Fast, works for known models
   - `['qwen', 'civitai']` - Balanced (default)

3. **Review Uncertain Results**: Don't blindly download
   - Check candidate sources
   - Verify file sizes match expectations
   - Prefer official repositories

### For Developers

1. **Extend Search Backends**: Implement `SearchBackend` interface
   ```python
   class CustomSearch(SearchBackend):
       def search(self, model_info):
           # Your search logic
           return SearchResult(...)
   ```

2. **Add Pattern Recognition**: Update Qwen prompt templates
   ```python
   # In search.py
   KNOWN_PATTERNS = {
       r'your_pattern': "specific search strategy"
   }
   ```

3. **Monitor Agent Reasoning**: Enable debug logging
   ```python
   logger.setLevel(logging.DEBUG)
   # Logs Qwen's step-by-step reasoning
   ```

## Related Documentation

- **[Qwen Search Implementation Plan](planning/QWEN_SEARCH_IMPLEMENTATION_PLAN.md)** - Original design document
- **[Qwen Operator Guide](planning/QWEN_PROMPT.md)** - Prompt engineering details
- **[Vision Document](vision.md)** - Phase 2 search requirements
- **[Architecture Document](architecture.md)** - LLM + RAG integration
- **[API Reference](developer/api-reference.md)** - Python API documentation

## Summary

ComfyWatchman's agentic search architecture represents a paradigm shift from naive keyword matching to **intelligent, reasoning-driven model discovery**. By leveraging LLM agents (Qwen) with tool access, the system:

✅ **Validates exact filename matches** across API results
✅ **Handles multi-source federation** (Civitai, HuggingFace, ModelScope)
✅ **Manages uncertainty** with doubt handling and human review
✅ **Prevents false downloads** through rigorous verification
✅ **Learns and adapts** search strategies based on patterns

This architecture eliminates the "download wrong model" problem that plagued earlier versions, while maintaining extensibility for future enhancements.

---

## Next Steps: Automated Download & Verification

Once the agentic search phase successfully returns a `FOUND` result with a high-confidence download URL, the process transitions from discovery to execution. This next stage is handled by the **Automated Download & Verification Service**.

This service is a persistent, background system that manages the entire download lifecycle, including:
- A persistent job queue for pending downloads.
- A "fire-and-forget" background worker for asynchronous execution.
- Automatic retries and resume for interrupted downloads.
- An intelligent, agent-driven verification step to ensure file integrity.

For the complete details of this subsequent process, see the exhaustive framework document: **[Automated Download & Verification Workflow](domains/AUTOMATED_DOWNLOAD_WORKFLOW.md)**.
