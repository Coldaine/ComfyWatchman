# ComfyFixerSmart Architecture
**Automated ComfyUI Workflow Analysis & Model Resolution System**

Version: 1.0
Date: 2025-10-12
Author: AI Agent Architecture Design

---

## Executive Summary

ComfyFixerSmart is an intelligent agent-based system designed to automatically analyze ComfyUI workflows, identify missing models and custom nodes, search Civitai for compatible replacements, and download them to the correct directories. The system leverages existing infrastructure including the Civitai API, ComfyUI's model scanner, and the lora-manager download capabilities.

**Key Capabilities:**
- Parse and validate ComfyUI workflow JSON files
- Detect missing models (checkpoints, LoRAs, VAEs, etc.) and custom nodes
- Search Civitai API for missing models by name/hash
- Automatically download and place models in correct directories
- Generate comprehensive reports and download scripts
- Maintain a cache of model metadata and search results

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ComfyFixerSmart                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │   Workflow   │───▶│   Analyzer   │───▶│   Reporter   │         │
│  │    Parser    │    │   Engine     │    │  Generator   │         │
│  └──────────────┘    └──────────────┘    └──────────────┘         │
│         │                    │                    │                 │
│         ▼                    ▼                    ▼                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │  Model Map   │    │   Civitai    │    │   Download   │         │
│  │   Builder    │    │   Resolver   │    │   Manager    │         │
│  └──────────────┘    └──────────────┘    └──────────────┘         │
│         │                    │                    │                 │
│         └────────────────────┴────────────────────┘                 │
│                              │                                      │
│                    ┌─────────▼──────────┐                          │
│                    │   Cache & Database │                          │
│                    └────────────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │   Civitai   │  │  ComfyUI    │  │  Local FS   │
    │     API     │  │   Scanner   │  │   Models    │
    └─────────────┘  └─────────────┘  └─────────────┘
```

---

## Component Architecture

### 1. Workflow Parser (`workflow_parser.py`)

**Purpose:** Parse ComfyUI workflow JSON files and extract model/node references

**Key Functions:**
```python
def parse_workflow(workflow_path: str) -> WorkflowData
def extract_model_references(workflow_data: dict) -> List[ModelReference]
def extract_node_types(workflow_data: dict) -> List[str]
def validate_workflow_format(workflow_data: dict) -> ValidationResult
```

**Data Structures:**
```python
@dataclass
class ModelReference:
    filename: str
    node_type: str  # CheckpointLoader, LoraLoader, VAELoader, etc.
    expected_type: str  # checkpoint, lora, vae, etc.
    expected_directory: str  # models/checkpoints, models/loras, etc.
    widget_values: dict  # Additional context from node
    node_id: int

@dataclass
class WorkflowData:
    path: str
    workflow_id: str
    nodes: List[dict]
    model_references: List[ModelReference]
    custom_node_types: Set[str]
    metadata: dict
```

**Reuses Existing Code:**
- Extends `/home/coldaine/StableDiffusionWorkflow/ScanTool/workflow_validator.py` parsing logic
- Leverages the `find_model_names()` function pattern
- Uses the node_to_model_type mapping

---

### 2. Model Map Builder (`model_mapper.py`)

**Purpose:** Build comprehensive inventory of locally available models

**Key Functions:**
```python
def build_model_inventory(comfy_root: str) -> ModelInventory
def hash_model_file(path: str) -> str
def detect_model_type_enhanced(path: str, metadata: dict) -> str
def index_civitai_toolkit_cache() -> dict
```

**Data Structures:**
```python
@dataclass
class ModelInventory:
    models_by_name: Dict[str, ModelInfo]
    models_by_hash: Dict[str, ModelInfo]
    models_by_type: Dict[str, List[ModelInfo]]
    scan_timestamp: float

@dataclass
class ModelInfo:
    name: str
    path: str
    hash: str
    type_hint: str
    size_bytes: int
    civitai_id: Optional[int]
    civitai_version_id: Optional[int]
    metadata: dict
```

**Reuses Existing Code:**
- Integrates `/home/coldaine/StableDiffusionWorkflow/ScanTool/comfyui_model_scanner.py`
- Pulls from Civitai Toolkit's database (`civitai-toolkit/data/*.db`)
- Uses lora-manager's model detection logic

---

### 3. Analyzer Engine (`analyzer.py`)

**Purpose:** Compare workflows against inventory and identify missing items

**Key Functions:**
```python
def analyze_workflow(workflow: WorkflowData, inventory: ModelInventory) -> AnalysisResult
def identify_missing_models(workflow: WorkflowData, inventory: ModelInventory) -> List[MissingModel]
def identify_missing_nodes(workflow: WorkflowData) -> List[MissingNode]
def suggest_replacements(missing: MissingModel, inventory: ModelInventory) -> List[ModelInfo]
```

**Data Structures:**
```python
@dataclass
class MissingModel:
    filename: str
    expected_type: str
    expected_directory: str
    node_type: str
    node_id: int
    context: dict  # Additional info from workflow

@dataclass
class MissingNode:
    node_type: str
    node_id: int
    widget_values: dict

@dataclass
class AnalysisResult:
    workflow_path: str
    missing_models: List[MissingModel]
    missing_nodes: List[MissingNode]
    available_models: List[ModelReference]
    suggestions: Dict[str, List[ModelInfo]]
    timestamp: float
```

**Reuses Existing Code:**
- Extends `/home/coldaine/StableDiffusionWorkflow/ScanTool/workflow_validator.py` validation logic
- Uses type_to_directory mapping from validator
- Implements node_to_model_type lookups

---

### 4. Civitai Resolver (`civitai_resolver.py`)

**Purpose:** Search Civitai API for missing models and resolve download URLs

**Key Functions:**
```python
def search_civitai_by_name(model_name: str, model_type: str) -> List[CivitaiModel]
def search_civitai_by_hash(model_hash: str) -> Optional[CivitaiModel]
def get_model_download_url(model_version_id: int) -> str
def fetch_model_metadata(model_id: int) -> dict
def match_model_fuzzy(query: str, results: List[CivitaiModel]) -> CivitaiModel
```

**Data Structures:**
```python
@dataclass
class CivitaiModel:
    id: int
    name: str
    type: str
    model_versions: List[CivitaiVersion]
    creator: str
    tags: List[str]
    nsfw: bool

@dataclass
class CivitaiVersion:
    id: int
    name: str
    download_url: str
    files: List[CivitaiFile]
    base_model: str
    trained_words: List[str]

@dataclass
class CivitaiFile:
    name: str
    size_kb: int
    type: str  # Model, Pruned Model, VAE, etc.
    download_url: str
    hashes: dict  # SHA256, AutoV2, etc.
```

**API Integration:**
```python
# Civitai API Endpoints (from civitai_api_research.md)
BASE_URL = "https://civitai.com/api/v1"
DOWNLOAD_URL = "https://civitai.com/api/download/models"

# Search endpoint
GET /api/v1/models?query={name}&types={type}&limit=10

# Model details
GET /api/v1/models/{model_id}

# Download endpoint
GET /api/download/models/{version_id}?token={CIVITAI_API_KEY}
```

**Reuses Existing Code:**
- Leverages `civitai-toolkit/utils.py` functions
- Uses existing API key from `~/.secrets` (CIVITAI_API_KEY)
- Integrates with `civitai-toolkit/api.py` helper functions

---

### 5. Download Manager (`download_manager.py`)

**Purpose:** Handle downloading models and placing them in correct directories

**Key Functions:**
```python
def download_model(url: str, save_path: str, progress_callback: Callable) -> bool
def determine_save_location(model: MissingModel, civitai_model: CivitaiModel) -> str
def verify_download(path: str, expected_hash: str) -> bool
def create_download_script(missing_models: List[MissingModel], resolutions: List[CivitaiModel]) -> str
```

**Download Strategy:**
```python
# Priority order for download method:
1. Direct download via Download Manager (automated)
2. Generate bash script for manual review
3. Generate wget commands with API key

# Directory mapping
DIRECTORY_MAP = {
    'checkpoint': 'ComfyUI-stable/models/checkpoints',
    'lora': 'ComfyUI-stable/models/loras',
    'vae': 'ComfyUI-stable/models/vae',
    'controlnet': 'ComfyUI-stable/models/controlnet',
    'upscale_models': 'ComfyUI-stable/models/upscale_models',
    'clip_vision': 'ComfyUI-stable/models/clip_vision',
    'embeddings': 'ComfyUI-stable/models/embeddings',
}
```

**Reuses Existing Code:**
- Integrates `comfyui-lora-manager/py/services/downloader.py` (full-featured async downloader)
- Uses existing download patterns from civitai_api_research.md
- Leverages Civitai API authentication from ~/.secrets

---

### 6. Reporter Generator (`reporter.py`)

**Purpose:** Generate human-readable reports and actionable scripts

**Key Functions:**
```python
def generate_analysis_report(result: AnalysisResult) -> str
def generate_download_script(resolutions: List[Resolution]) -> str
def generate_summary_markdown(results: List[AnalysisResult]) -> str
def export_json_report(results: List[AnalysisResult], path: str) -> None
```

**Report Formats:**

**1. Analysis Report (Markdown)**
```markdown
# Workflow Analysis Report
## Workflow: my_workflow.json

### Missing Models (3)
- **model_name.safetensors**
  - Type: LoRA
  - Expected Location: models/loras/
  - Used in Node: LoraLoader (ID: 42)
  - Civitai Search: [Link](https://civitai.com/models/search?query=model_name)

### Missing Custom Nodes (1)
- **CustomNodeType**
  - Used in Node ID: 15
  - Possible Source: [Research needed]

### Available Models (12)
✅ All checkpoints found
✅ 5/7 LoRAs found
```

**2. Download Script (Bash)**
```bash
#!/bin/bash
# Auto-generated by ComfyFixerSmart
# Workflow: my_workflow.json
# Generated: 2025-10-12

source ~/.secrets

MODELS_DIR="/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/models"

# Download: model_name.safetensors (LoRA)
wget -c --content-disposition \
  --timeout=30 --tries=5 \
  -O "${MODELS_DIR}/loras/model_name.safetensors" \
  "https://civitai.com/api/download/models/123456?token=${CIVITAI_API_KEY}"
```

**3. JSON Export**
```json
{
  "workflow": "my_workflow.json",
  "analyzed_at": 1728691200,
  "missing_models": [...],
  "resolutions": [...],
  "download_commands": [...]
}
```

---

### 7. Cache & Database (`cache_manager.py`)

**Purpose:** Maintain persistent cache of API responses and search results

**Schema:**
```sql
-- Civitai search cache
CREATE TABLE civitai_search_cache (
    query TEXT PRIMARY KEY,
    model_type TEXT,
    results JSON,
    timestamp INTEGER
);

-- Model resolution cache
CREATE TABLE model_resolutions (
    filename TEXT PRIMARY KEY,
    civitai_id INTEGER,
    version_id INTEGER,
    download_url TEXT,
    confidence REAL,
    timestamp INTEGER
);

-- Workflow analysis cache
CREATE TABLE workflow_analyses (
    workflow_path TEXT PRIMARY KEY,
    workflow_hash TEXT,
    analysis_result JSON,
    timestamp INTEGER
);
```

**Key Functions:**
```python
def cache_search_result(query: str, results: List[CivitaiModel]) -> None
def get_cached_search(query: str, max_age_hours: int = 24) -> Optional[List[CivitaiModel]]
def cache_resolution(filename: str, resolution: Resolution) -> None
def get_cached_resolution(filename: str) -> Optional[Resolution]
```

**Reuses Existing Code:**
- Extends Civitai Toolkit's SQLite database structure
- Leverages `civitai-toolkit/utils.py` db_manager patterns
- Uses same caching strategies as existing tools

---

## Data Flow

### Complete Workflow Analysis Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. DISCOVERY PHASE                                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  User Input: Workflow Directory or File                            │
│       │                                                             │
│       ▼                                                             │
│  Glob for *.json workflows                                         │
│       │                                                             │
│       ▼                                                             │
│  Parse each workflow → Extract model refs & node types             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. INVENTORY PHASE                                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Scan ComfyUI models/ directory                                    │
│       │                                                             │
│       ├──▶ Hash safetensors files                                  │
│       ├──▶ Extract metadata                                        │
│       ├──▶ Query Civitai Toolkit cache for known models           │
│       │                                                             │
│       ▼                                                             │
│  Build ModelInventory (name, hash, type indices)                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. ANALYSIS PHASE                                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  For each ModelReference in workflow:                              │
│       │                                                             │
│       ├──▶ Check if filename exists in inventory                   │
│       │    │                                                        │
│       │    ├─[FOUND]──▶ Mark as available                          │
│       │    │                                                        │
│       │    └─[MISSING]──▶ Add to missing_models list               │
│       │                  Record: name, type, node context          │
│       │                                                             │
│  For each node_type in workflow:                                   │
│       │                                                             │
│       └──▶ Check if custom node is installed                       │
│            │                                                        │
│            └─[MISSING]──▶ Add to missing_nodes list                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. RESOLUTION PHASE                                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  For each missing_model:                                           │
│       │                                                             │
│       ├──▶ Check cache for previous resolution                     │
│       │    │                                                        │
│       │    └─[CACHED]──▶ Use cached result                         │
│       │                                                             │
│       ├──▶ Search Civitai API by filename                          │
│       │    │                                                        │
│       │    ├─[FOUND]──▶ Extract version_id, download_url           │
│       │    │            Cache result                               │
│       │    │                                                        │
│       │    └─[NOT FOUND]──▶ Fuzzy search with type filter          │
│       │                     Manual review required                 │
│       │                                                             │
│       └──▶ Verify download URL and file availability               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. DOWNLOAD PHASE (Optional - User Choice)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Mode 1: Automatic Download                                        │
│       │                                                             │
│       ├──▶ For each resolution with high confidence:               │
│       │    │                                                        │
│       │    ├──▶ Determine target directory                         │
│       │    ├──▶ Download with progress callback                    │
│       │    ├──▶ Verify hash if available                           │
│       │    └──▶ Move to final location                             │
│       │                                                             │
│  Mode 2: Generate Script                                           │
│       │                                                             │
│       └──▶ Create bash script with wget commands                   │
│            User reviews and executes manually                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. REPORTING PHASE                                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Generate Markdown Report:                                         │
│       │                                                             │
│       ├──▶ Summary statistics                                      │
│       ├──▶ Missing models with Civitai links                       │
│       ├──▶ Missing custom nodes with sources                       │
│       ├──▶ Download script location                                │
│       └──▶ Next steps recommendations                              │
│                                                                     │
│  Export JSON:                                                       │
│       │                                                             │
│       └──▶ Machine-readable format for further processing          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)
**Goal:** Build foundational components

**Tasks:**
1. ✅ Create project structure in `/ComfyFixerSmart/`
2. ⬜ Implement `workflow_parser.py`
   - Extend existing workflow_validator parsing logic
   - Add model reference extraction
   - Add node type detection
3. ⬜ Implement `model_mapper.py`
   - Integrate comfyui_model_scanner
   - Add Civitai toolkit cache reader
   - Build inventory indices
4. ⬜ Implement `cache_manager.py`
   - Create SQLite database schema
   - Implement cache functions
   - Add expiration logic

**Deliverables:**
- Working workflow parser
- Model inventory builder
- Cache system

---

### Phase 2: Analysis Engine (Week 2)
**Goal:** Detect missing models and nodes

**Tasks:**
1. ⬜ Implement `analyzer.py`
   - Model comparison logic
   - Node type detection
   - Suggestion engine
2. ⬜ Implement `civitai_resolver.py`
   - API integration
   - Search functions
   - Fuzzy matching
3. ⬜ Add unit tests
   - Test workflow parsing
   - Test missing detection
   - Test API mocking

**Deliverables:**
- Complete analysis engine
- Civitai integration
- Test suite

---

### Phase 3: Download System (Week 3)
**Goal:** Automate model downloads

**Tasks:**
1. ⬜ Implement `download_manager.py`
   - Integrate lora-manager downloader
   - Add directory mapping
   - Add verification
2. ⬜ Implement `reporter.py`
   - Markdown report generator
   - Bash script generator
   - JSON export
3. ⬜ Create CLI interface
   - argparse setup
   - Progress display
   - User prompts

**Deliverables:**
- Download automation
- Report generation
- CLI tool

---

### Phase 4: Agent Interface (Week 4)
**Goal:** Create autonomous agent wrapper

**Tasks:**
1. ⬜ Implement `agent.py`
   - Main orchestration logic
   - Error handling
   - Logging system
2. ⬜ Add batch processing
   - Multi-workflow analysis
   - Parallel downloads
   - Summary reports
3. ⬜ Documentation
   - User guide
   - API documentation
   - Example workflows

**Deliverables:**
- Complete agent system
- Documentation
- Example outputs

---

## File Structure

```
ComfyFixerSmart/
├── architecture.md                 # This document
├── README.md                        # User guide
├── requirements.txt                 # Python dependencies
│
├── src/
│   ├── __init__.py
│   ├── workflow_parser.py          # Parse workflow JSON
│   ├── model_mapper.py             # Build model inventory
│   ├── analyzer.py                 # Analyze workflows
│   ├── civitai_resolver.py         # Civitai API integration
│   ├── download_manager.py         # Download handling
│   ├── reporter.py                 # Report generation
│   ├── cache_manager.py            # Cache/database
│   └── agent.py                    # Main orchestrator
│
├── tests/
│   ├── test_parser.py
│   ├── test_analyzer.py
│   ├── test_resolver.py
│   └── fixtures/                   # Test workflows
│
├── scripts/
│   ├── analyze_workflow.py         # CLI: Analyze single workflow
│   ├── analyze_directory.py        # CLI: Batch analyze
│   ├── download_missing.py         # CLI: Download models
│   └── generate_report.py          # CLI: Generate reports
│
├── data/
│   ├── cache.db                    # SQLite cache
│   ├── resolutions.json            # Known model resolutions
│   └── node_sources.json           # Custom node sources
│
└── output/
    ├── reports/                    # Generated markdown reports
    ├── scripts/                    # Generated download scripts
    └── logs/                       # Execution logs
```

---

## Integration Points

### Existing Tools Integration

**1. ComfyUI Model Scanner**
- Location: `/ScanTool/comfyui_model_scanner.py`
- Usage: Import `scan()` function for model discovery
- Benefits: Proven metadata extraction, type detection

**2. Workflow Validator**
- Location: `/ScanTool/workflow_validator.py`
- Usage: Extend `find_model_names()` and validation logic
- Benefits: Existing node type mappings

**3. Civitai Toolkit**
- Location: `/ComfyUI-stable/custom_nodes/civitai-toolkit/`
- Usage: Import utils for API calls, leverage existing cache
- Benefits: Hash-based model lookup, API key management

**4. LoRA Manager Downloader**
- Location: `/custom_nodes/comfyui-lora-manager/py/services/downloader.py`
- Usage: Use `Downloader` class for async downloads
- Benefits: Resumable downloads, progress tracking, auth support

**5. Civitai API**
- Documentation: `civitai_api_research.md`
- Usage: REST API for search and download
- Benefits: Official API, API key from ~/.secrets

---

## API Reference

### Civitai API Endpoints

```python
# Search models
GET https://civitai.com/api/v1/models
Parameters:
  - query: str (search term)
  - types: str (comma-separated: Checkpoint, LORA, etc.)
  - limit: int (max results)
  - sort: str (Highest Rated, Most Downloaded, Newest)

# Get model details
GET https://civitai.com/api/v1/models/{model_id}

# Download model
GET https://civitai.com/api/download/models/{version_id}
Parameters:
  - token: str (API key from ~/.secrets)

Headers:
  - Authorization: Bearer {CIVITAI_API_KEY}
```

---

## Configuration

### Environment Variables
```bash
# Required (from ~/.secrets)
export CIVITAI_API_KEY="your_api_key_here"

# Optional
export COMFYUI_ROOT="/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable"
export COMFY_FIXER_CACHE_DIR="/home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart/data"
export COMFY_FIXER_AUTO_DOWNLOAD=false  # Require confirmation
```

### Settings File (comfy_fixer_config.json)
```json
{
  "comfyui_root": "/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable",
  "cache_expiry_hours": 24,
  "auto_download": false,
  "confidence_threshold": 0.8,
  "max_concurrent_downloads": 3,
  "civitai_api": {
    "timeout": 30,
    "max_retries": 3,
    "rate_limit_delay": 1.0
  },
  "model_directories": {
    "checkpoint": "models/checkpoints",
    "lora": "models/loras",
    "vae": "models/vae",
    "controlnet": "models/controlnet",
    "upscale_models": "models/upscale_models"
  }
}
```

---

## Error Handling Strategy

### Error Categories

**1. Workflow Parse Errors**
- Invalid JSON
- Missing required fields
- Corrupted workflow

**Action:** Log error, skip workflow, continue batch

**2. API Errors**
- Rate limiting (429)
- Authentication (401)
- Not found (404)

**Action:** Implement exponential backoff, cache results, fallback to manual resolution

**3. Download Errors**
- Network timeout
- Insufficient disk space
- Permission errors

**Action:** Resume support, retry with backoff, generate manual script

**4. Model Type Mismatches**
- Wrong directory
- Type detection failure

**Action:** Fuzzy matching, user confirmation, suggest alternatives

---

## Security Considerations

**1. API Key Protection**
- Read from ~/.secrets (600 permissions)
- Never log API keys
- Never include in generated scripts (use environment variables)

**2. Download Safety**
- Verify file hashes when available
- Scan for malicious content (optional)
- Isolate downloads to designated directories

**3. Workflow Validation**
- Sanitize user inputs
- Prevent path traversal
- Validate JSON structure

---

## Performance Optimization

**1. Caching Strategy**
- Cache Civitai API responses (24h TTL)
- Cache model hash computations
- Cache workflow analyses

**2. Parallel Processing**
- Concurrent API requests (rate-limited)
- Parallel downloads (max 3)
- Async I/O for file operations

**3. Incremental Scanning**
- Track file modification times
- Skip unchanged workflows
- Update only modified models

---

## Usage Examples

### Example 1: Analyze Single Workflow
```bash
cd /home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart

python scripts/analyze_workflow.py \
  --workflow "/path/to/workflow.json" \
  --report output/reports/workflow_analysis.md \
  --auto-search

# Output:
# Analyzing workflow: workflow.json
# ✅ Scanned 234 local models
# ⚠️  Found 3 missing models
# 🔍 Searching Civitai...
# ✅ Found 2/3 models on Civitai
# 📄 Report saved to: output/reports/workflow_analysis.md
```

### Example 2: Batch Analysis
```bash
python scripts/analyze_directory.py \
  --directory "/path/to/workflows/" \
  --output output/reports/batch_analysis.md \
  --generate-scripts

# Output:
# Analyzing 15 workflows...
# [1/15] workflow_1.json: 2 missing models
# [2/15] workflow_2.json: 0 missing models
# ...
# 📊 Summary:
#   - Total workflows: 15
#   - Missing models: 8 unique
#   - Civitai matches: 6/8
#   - Download script: output/scripts/download_missing.sh
```

### Example 3: Auto-Download
```bash
python scripts/download_missing.py \
  --analysis output/reports/workflow_analysis.json \
  --auto-download \
  --verify-hashes

# Output:
# Downloading 2 models...
# [1/2] model_name.safetensors (234 MB)
#       ████████████████████ 100% | 5.2 MB/s | ETA: 0s
#       ✅ Downloaded and verified
# [2/2] another_model.safetensors (156 MB)
#       ████████████████████ 100% | 6.1 MB/s | ETA: 0s
#       ✅ Downloaded and verified
#
# 🎉 All models downloaded successfully!
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_parser.py
def test_parse_valid_workflow()
def test_parse_invalid_json()
def test_extract_model_references()
def test_extract_node_types()

# tests/test_analyzer.py
def test_identify_missing_models()
def test_identify_missing_nodes()
def test_suggest_replacements()

# tests/test_resolver.py
def test_search_civitai_by_name()
def test_search_civitai_by_hash()
def test_fuzzy_matching()
```

### Integration Tests
```python
# tests/test_integration.py
def test_end_to_end_workflow_analysis()
def test_batch_processing()
def test_download_with_verification()
```

### Test Fixtures
```
tests/fixtures/
├── valid_workflow.json         # Complete valid workflow
├── missing_models_workflow.json  # Workflow with missing models
├── invalid_workflow.json       # Corrupted workflow
└── mock_api_responses/         # Mocked Civitai responses
```

---

## Future Enhancements

### Phase 5: Advanced Features

**1. Custom Node Resolution**
- Parse custom node metadata
- Search ComfyUI-Manager database
- Auto-clone GitHub repos

**2. Model Alternatives**
- Suggest similar models
- Version compatibility checking
- Base model matching (SD 1.5, SDXL, etc.)

**3. Workflow Repair**
- Auto-update workflows with found models
- Fix broken paths
- Update deprecated nodes

**4. Web UI**
- Flask/FastAPI web interface
- Drag-drop workflow upload
- Interactive model selection
- Download queue management

**5. AI-Powered Matching**
- Embeddings-based similarity search
- Model description analysis
- Tag matching with NLP

---

## Dependencies

```txt
# Core
python >= 3.10

# Existing (already installed)
aiohttp >= 3.9.0
safetensors >= 0.4.0
pyyaml >= 6.0

# New
click >= 8.1.0          # CLI framework
tqdm >= 4.66.0          # Progress bars
fuzzywuzzy >= 0.18.0    # Fuzzy string matching
python-Levenshtein >= 0.21.0  # Fast fuzzy matching
```

---

## Conclusion

ComfyFixerSmart provides an intelligent, automated solution for analyzing ComfyUI workflows and resolving missing dependencies. By leveraging existing tools and the Civitai API, it streamlines the workflow sharing and troubleshooting process.

**Key Benefits:**
- ✅ Automated workflow validation
- ✅ Intelligent model search and matching
- ✅ Resumable, authenticated downloads
- ✅ Comprehensive reporting
- ✅ Minimal user intervention required
- ✅ Reuses proven existing components

**Next Steps:**
1. Review and refine architecture
2. Begin Phase 1 implementation
3. Set up test infrastructure
4. Create example workflows for testing

---

**Architecture Version:** 1.0
**Last Updated:** 2025-10-12
**Status:** Draft - Ready for Implementation
