# ComfyFixerSmart Architecture

**Automated ComfyUI Workflow Analysis & Model Resolution System**

> **See also:**
> - [Research Prompt](../research/RESEARCH_PROMPT.md) — Ultimate vision for automated workflow generation & optimization
> - [Existing Systems Analysis](../research/EXISTING_SYSTEMS.md) — Prior art from ComfyUI-Copilot, ComfyScript, ComfyGPT, and others
> - [Vision Document](../vision.md) — High-level mission and roadmap
> - [Proposed Architecture](../architecture.md) — LLM + RAG extensions

## Executive Summary

ComfyFixerSmart is an intelligent agent-based system designed to automatically analyze ComfyUI workflows, identify missing models and custom nodes, search Civitai for compatible replacements, and download them to the correct directories. The system leverages existing infrastructure including the Civitai API, ComfyUI's model scanner, and the lora-manager download capabilities.

**Key Capabilities:**
- Parse and validate ComfyUI workflow JSON files
- Detect missing models (checkpoints, LoRAs, VAEs, etc.) and custom nodes
- Search Civitai API for missing models by name/hash
- Automatically download and place models in correct directories
- Generate comprehensive reports and download scripts
- Maintain a cache of model metadata and search results

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
# Civitai API Endpoints
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

source ~/.secrets  # Load CIVITAI_API_KEY

MODELS_DIR="/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/models"

# Download: model_name.safetensors (LoRA)
# Civitai ID: 1186768, Version: 1234567
wget -c --content-disposition \
  --timeout=30 --tries=5 --retry-connrefused \
  -O "${MODELS_DIR}/loras/model_name.safetensors" \
  "https://civitai.com/api/download/models/1234567?token=${CIVITAI_API_KEY}"
```

**3. JSON Export**
```json
{
  "workflow": "my_workflow.json",
  "analyzed_at": 1728691200,
  "missing_models": [...],
}
```

### 7. Cache & Database (`cache_manager.py`)

**Purpose:** Cache API responses and model metadata for performance

**Key Functions:**
```python
def get_cached_search(query: str, model_type: str) -> Optional[List[CivitaiModel]]
def cache_search_result(query: str, model_type: str, results: List[CivitaiModel]) -> None
def cleanup_expired_cache() -> int
def get_cache_stats() -> dict
```

**Database Schema:**
```sql
-- Search cache table
CREATE TABLE search_cache (
    id INTEGER PRIMARY KEY,
    query TEXT NOT NULL,
    model_type TEXT NOT NULL,
    results_json TEXT NOT NULL,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    UNIQUE(query, model_type)
);

-- Model metadata cache
CREATE TABLE model_cache (
    civitai_id INTEGER PRIMARY KEY,
    metadata_json TEXT NOT NULL,
    last_updated REAL NOT NULL
);
```

**Cache Strategy:**
- Search results cached for 24 hours
- Model metadata cached for 7 days
- Automatic cleanup of expired entries
- SQLite database for persistence

## Integration Points

### Existing Tools Integration

**ComfyUI Scanner (`ScanTool/comfyui_model_scanner.py`)**
- Model detection and hashing
- File type identification
- Directory traversal logic

**Civitai Toolkit (`civitai-toolkit/`)**
- API authentication and requests
- Model metadata parsing
- Download URL resolution

**Lora Manager (`comfyui-lora-manager/`)**
- Async download capabilities
- Progress tracking
- Resume support

### Configuration Integration

**Settings File (`comfy_fixer_config.json`)**
```json
{
  "comfyui_root": "/path/to/comfyui",
  "workflow_dirs": ["user/default/workflows"],
  "search_backends": ["civitai", "huggingface"],
  "download_concurrency": 3,
  "cache_enabled": true,
  "cache_ttl_hours": 24
}
```

**Environment Variables**
- `CIVITAI_API_KEY`: API authentication
- `COMFYUI_ROOT`: ComfyUI installation path
- `HF_TOKEN`: HuggingFace access (optional)

## Security Considerations

### API Key Management
- API keys stored in `~/.secrets` file
- Never logged or exposed in reports
- Environment variable override support

### Download Security
- HTTPS-only downloads
- Certificate validation enabled
- File integrity verification via hashes

### File System Security
- Proper permission handling
- Path traversal protection
- Safe directory creation

## Performance Optimization

### Caching Strategy
- API response caching reduces network calls
- Model inventory caching speeds up repeated scans
- Persistent cache survives application restarts

### Concurrent Processing
- Multiple workflow analysis in parallel
- Concurrent downloads with configurable limits
- Async I/O for network operations

### Memory Management
- Streaming downloads for large files
- Lazy loading of model metadata
- Automatic cache size limits

## Error Handling & Resilience

### Network Resilience
- Retry logic for failed API calls
- Timeout handling for slow connections
- Fallback to alternative search methods

### Data Validation
- JSON schema validation for workflows
- API response validation
- File integrity checks

### Recovery Mechanisms
- Resume interrupted downloads
- Cache corruption detection and repair
- Graceful degradation on component failures

## Development & Testing

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow validation
- **Functional Tests**: Component interaction testing

### Mocking Strategy
- API responses mocked for deterministic testing
- File system operations mocked for isolation
- External dependencies abstracted for testability

## Future Extensions

### Additional Search Backends
- HuggingFace model hub integration
- Model metadata cross-referencing
- Community model repositories

### Advanced Features
- Model compatibility checking
- Automatic dependency resolution
- Batch processing optimization

### Monitoring & Analytics
- Usage statistics collection
- Performance metrics tracking
- Error reporting and analysis

---

*This architecture document is consolidated from the original design documents in `archives/UnusedArchive/` and updated to reflect the current modular structure.*