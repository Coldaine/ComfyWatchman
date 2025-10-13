# API Reference

This document provides a comprehensive reference for the ComfyFixerSmart Python API.

## Package Overview

```python
import comfyfixersmart

# Version information
print(comfyfixersmart.__version__)  # "2.0.0"

# Main classes
from comfyfixersmart import (
    ComfyFixerCore,      # Main orchestrator
    WorkflowScanner,     # Workflow analysis
    ModelInventory,      # Local model management
    ModelSearch,         # Model search across backends
    DownloadManager,     # Download coordination
    StateManager,        # State persistence
)
```

## Core Classes

### ComfyFixerCore

The main orchestrator class that coordinates all ComfyFixerSmart operations.

```python
from comfyfixersmart import ComfyFixerCore

# Initialize
fixer = ComfyFixerCore()

# Run complete analysis and download
result = fixer.run(
    workflow_paths=["workflow1.json", "workflow2.json"],
    output_dir="output/",
    search_backends=["civitai", "huggingface"]
)
```

#### Methods

**`__init__(config=None)`**
Initialize the core fixer.

- **Parameters:**
  - `config` (Config, optional): Configuration object. Uses default if None.

**`run(workflow_paths=None, output_dir=None, search_backends=None, **kwargs)`**
Run the complete ComfyFixerSmart workflow.

- **Parameters:**
  - `workflow_paths` (List[str], optional): Specific workflow files to analyze
  - `output_dir` (str, optional): Output directory for results
  - `search_backends` (List[str], optional): Search backends to use
  - `**kwargs`: Additional options passed to components

- **Returns:** `WorkflowRun` object with execution results

**`analyze_workflows(workflow_paths)`**
Analyze workflows without downloading.

- **Parameters:**
  - `workflow_paths` (List[str]): Workflow files to analyze

- **Returns:** `AnalysisResult` with missing models and metadata

**`download_models(missing_models, output_dir)`**
Download identified missing models.

- **Parameters:**
  - `missing_models` (List[dict]): Models to download
  - `output_dir` (str): Output directory

- **Returns:** `DownloadResult` with success/failure status

### WorkflowScanner

Handles workflow file parsing and model extraction.

```python
from comfyfixersmart import WorkflowScanner

scanner = WorkflowScanner()

# Scan single workflow
result = scanner.scan_workflow("my_workflow.json")

# Scan directory
workflows = scanner.scan_directory("workflows/")

# Extract models from workflow data
models = scanner.extract_models(workflow_data)
```

#### Methods

**`scan_workflow(path)`**
Parse a single workflow file.

- **Parameters:**
  - `path` (str): Path to workflow JSON file

- **Returns:** `WorkflowData` object

**`scan_directory(directory, recursive=True)`**
Scan directory for workflow files.

- **Parameters:**
  - `directory` (str): Directory to scan
  - `recursive` (bool): Scan subdirectories

- **Returns:** `List[WorkflowData]`

**`extract_models(workflow_data)`**
Extract model references from parsed workflow data.

- **Parameters:**
  - `workflow_data` (dict): Parsed workflow JSON

- **Returns:** `List[ModelReference]`

**`validate_workflow(workflow_data)`**
Validate workflow structure and content.

- **Parameters:**
  - `workflow_data` (dict): Workflow data to validate

- **Returns:** `ValidationResult`

### ModelInventory

Manages the local model inventory and provides lookup capabilities.

```python
from comfyfixersmart import ModelInventory

# Create inventory
inventory = ModelInventory()

# Build from ComfyUI directory
inventory.build("/path/to/comfyui")

# Check if model exists
exists = inventory.has_model("model.safetensors")

# Get model info
info = inventory.get_model_info("model.safetensors")

# Find models by type
checkpoints = inventory.get_models_by_type("checkpoint")
```

#### Methods

**`build(comfyui_root)`**
Build inventory from ComfyUI installation.

- **Parameters:**
  - `comfyui_root` (str): Path to ComfyUI root directory

**`has_model(filename)`**
Check if model exists in inventory.

- **Parameters:**
  - `filename` (str): Model filename

- **Returns:** `bool`

**`get_model_info(filename)`**
Get detailed information about a model.

- **Parameters:**
  - `filename` (str): Model filename

- **Returns:** `ModelInfo` or `None`

**`get_models_by_type(model_type)`**
Get all models of a specific type.

- **Parameters:**
  - `model_type` (str): Model type (checkpoint, lora, vae, etc.)

- **Returns:** `List[ModelInfo]`

**`refresh()`**
Refresh the inventory from disk.

**`export_json(path)`**
Export inventory to JSON file.

- **Parameters:**
  - `path` (str): Output file path

### ModelSearch

Handles model search across different backends.

```python
from comfyfixersmart import ModelSearch

search = ModelSearch()

# Search for a model
results = search.search("realisticVisionV51", model_type="checkpoint")

# Search with multiple backends
results = search.search("model_name",
                       backends=["civitai", "huggingface"])

# Get model details
details = search.get_model_details("civitai", "12345")
```

#### Methods

**`search(query, model_type=None, backends=None)`**
Search for models across backends.

- **Parameters:**
  - `query` (str): Search query
  - `model_type` (str, optional): Model type filter
  - `backends` (List[str], optional): Backends to search

- **Returns:** `List[SearchResult]`

**`get_model_details(backend, model_id)`**
Get detailed information for a specific model.

- **Parameters:**
  - `backend` (str): Backend name
  - `model_id` (str): Model identifier

- **Returns:** `ModelDetails`

**`add_backend(backend)`**
Add a custom search backend.

- **Parameters:**
  - `backend` (SearchBackend): Backend implementation

### DownloadManager

Manages model downloads and provides progress tracking.

```python
from comfyfixersmart import DownloadManager

downloader = DownloadManager()

# Download single model
result = downloader.download_model(
    url="https://example.com/model.safetensors",
    save_path="/path/to/models/model.safetensors"
)

# Download multiple models
results = downloader.download_models(model_list, output_dir="models/")

# Generate download script
script = downloader.generate_script(missing_models)
```

#### Methods

**`download_model(url, save_path, progress_callback=None)`**
Download a single model file.

- **Parameters:**
  - `url` (str): Download URL
  - `save_path` (str): Local save path
  - `progress_callback` (callable, optional): Progress callback

- **Returns:** `DownloadResult`

**`download_models(models, output_dir, concurrency=3)`**
Download multiple models concurrently.

- **Parameters:**
  - `models` (List[dict]): List of model download specs
  - `output_dir` (str): Base output directory
  - `concurrency` (int): Number of concurrent downloads

- **Returns:** `List[DownloadResult]`

**`generate_script(missing_models, template=None)`**
Generate download script.

- **Parameters:**
  - `missing_models` (List[dict]): Models to include
  - `template` (str, optional): Script template

- **Returns:** `str` - Generated script content

**`verify_download(path, expected_hash=None)`**
Verify downloaded file integrity.

- **Parameters:**
  - `path` (str): File path to verify
  - `expected_hash` (str, optional): Expected hash

- **Returns:** `bool`

### StateManager

Manages persistent state and download tracking.

```python
from comfyfixersmart import StateManager

state = StateManager()

# Track download
state.record_download("model.safetensors", "civitai", "12345")

# Check if downloaded
downloaded = state.is_downloaded("model.safetensors")

# Get download history
history = state.get_download_history()

# Export state
state.export_json("state.json")
```

#### Methods

**`record_download(filename, source, source_id)`**
Record a successful download.

- **Parameters:**
  - `filename` (str): Model filename
  - `source` (str): Download source
  - `source_id` (str): Source identifier

**`is_downloaded(filename)`**
Check if model has been downloaded.

- **Parameters:**
  - `filename` (str): Model filename

- **Returns:** `bool`

**`get_download_history()`**
Get complete download history.

- **Returns:** `List[DownloadRecord]`

**`clear_history()`**
Clear download history.

**`export_json(path)`**
Export state to JSON file.

- **Parameters:**
  - `path` (str): Output file path

## Data Classes

### WorkflowData

Represents parsed workflow information.

```python
@dataclass
class WorkflowData:
    path: str                    # File path
    workflow_id: str            # Unique workflow ID
    nodes: List[dict]           # Raw node data
    model_references: List[ModelReference]  # Extracted models
    custom_node_types: Set[str] # Custom node types used
    metadata: dict              # Additional metadata
```

### ModelReference

Represents a model reference in a workflow.

```python
@dataclass
class ModelReference:
    filename: str               # Model filename
    node_type: str              # ComfyUI node type
    expected_type: str          # Model type (checkpoint, lora, etc.)
    expected_directory: str     # Expected directory
    widget_values: dict         # Node widget values
    node_id: int                # Node ID in workflow
```

### SearchResult

Represents a search result from a backend.

```python
@dataclass
class SearchResult:
    backend: str                # Search backend name
    model_id: str               # Unique model identifier
    name: str                   # Model name
    filename: str               # Primary filename
    model_type: str             # Model type
    download_url: str           # Download URL
    size_bytes: int             # File size
    hash_sha256: str            # SHA256 hash
    metadata: dict              # Additional metadata
    confidence: float           # Match confidence (0.0-1.0)
```

### DownloadResult

Represents the result of a download operation.

```python
@dataclass
class DownloadResult:
    filename: str               # Model filename
    success: bool               # Download success
    save_path: str              # Local save path
    size_downloaded: int        # Bytes downloaded
    duration: float             # Download duration in seconds
    error_message: str          # Error message if failed
    verified: bool              # File integrity verified
```

## Configuration

### Config Class

Central configuration management.

```python
from comfyfixersmart import config

# Access configuration
print(config.comfyui_root)
print(config.workflow_dirs)

# Modify configuration
config.comfyui_root = Path("/new/path")
config.civitai_api_timeout = 60
```

#### Key Attributes

**Paths:**
- `comfyui_root: Path` - ComfyUI installation root
- `workflow_dirs: List[Path]` - Workflow search directories
- `output_dir: Path` - Output directory
- `log_dir: Path` - Log directory
- `state_dir: Path` - State persistence directory

**API Settings:**
- `civitai_api_base: str` - Civitai API base URL
- `civitai_download_base: str` - Civitai download base URL
- `civitai_api_timeout: int` - API timeout in seconds

**Model Settings:**
- `model_extensions: List[str]` - Recognized model file extensions
- `model_type_mapping: Dict[str, str]` - Node type to model directory mapping

**Download Settings:**
- `download_concurrency: int` - Concurrent download limit
- `download_timeout: int` - Download timeout in seconds
- `verify_downloads: bool` - Enable download verification

## Utility Functions

### File Operations

**`save_json_file(data, path, indent=2)`**
Save data as JSON file.

```python
from comfyfixersmart import save_json_file

data = {"models": ["model1.safetensors", "model2.safetensors"]}
save_json_file(data, "models.json")
```

**`ensure_directory(path)`**
Ensure directory exists, creating if necessary.

```python
from comfyfixersmart import ensure_directory

ensure_directory("output/models")
ensure_directory("logs")
```

### Logging

**`get_logger(name=None)`**
Get configured logger instance.

```python
from comfyfixersmart import get_logger

logger = get_logger("comfyfixer")
logger.info("Starting analysis...")
```

## Exceptions

### ComfyFixerError

Base exception for ComfyFixerSmart errors.

```python
from comfyfixersmart import ComfyFixerError

try:
    # Some operation
    pass
except ComfyFixerError as e:
    print(f"ComfyFixerSmart error: {e}")
```

### Specific Exceptions

- `ConfigurationError` - Configuration-related errors
- `WorkflowParseError` - Workflow parsing failures
- `APISearchError` - Search backend failures
- `DownloadError` - Download failures
- `ValidationError` - Data validation failures

## Examples

### Complete Workflow

```python
from comfyfixersmart import ComfyFixerCore

# Initialize
fixer = ComfyFixerCore()

# Run complete analysis and download
result = fixer.run(
    workflow_paths=["workflow1.json", "workflow2.json"],
    output_dir="output/",
    search_backends=["civitai"]
)

print(f"Processed {result.workflows_scanned} workflows")
print(f"Found {result.models_missing} missing models")
print(f"Downloaded {result.models_resolved} models")
```

### Custom Analysis

```python
from comfyfixersmart import WorkflowScanner, ModelInventory, ModelSearch

# Scan workflows
scanner = WorkflowScanner()
workflows = scanner.scan_directory("workflows/")

# Build inventory
inventory = ModelInventory()
inventory.build("/path/to/comfyui")

# Search for missing models
search = ModelSearch()
for workflow in workflows:
    for model_ref in workflow.model_references:
        if not inventory.has_model(model_ref.filename):
            results = search.search(model_ref.filename, model_ref.expected_type)
            if results:
                print(f"Found {model_ref.filename} on {results[0].backend}")
```

### Download Management

```python
from comfyfixersmart import DownloadManager

downloader = DownloadManager()

# Download with progress callback
def progress_callback(filename, downloaded, total):
    percent = (downloaded / total) * 100
    print(f"{filename}: {percent:.1f}%")

result = downloader.download_model(
    url="https://example.com/model.safetensors",
    save_path="models/model.safetensors",
    progress_callback=progress_callback
)

if result.success:
    print(f"Downloaded {result.size_downloaded} bytes in {result.duration:.1f}s")
else:
    print(f"Download failed: {result.error_message}")
```

## Threading and Async

ComfyFixerSmart uses threading for concurrent operations:

- **Download concurrency** controlled by `download_concurrency` setting
- **Search operations** may use threads for multiple backends
- **Progress callbacks** run in main thread for UI responsiveness

For async usage, consider wrapping calls with `asyncio.to_thread()`:

```python
import asyncio
from comfyfixersmart import ComfyFixerCore

async def run_fixer_async():
    fixer = ComfyFixerCore()
    # Run in thread pool to avoid blocking
    result = await asyncio.to_thread(fixer.run, workflow_paths=["workflow.json"])
    return result

# Usage
result = asyncio.run(run_fixer_async())
```

## Best Practices

### Error Handling

```python
from comfyfixersmart import ComfyFixerError

try:
    result = fixer.run(workflow_paths=["workflow.json"])
except ComfyFixerError as e:
    logger.error(f"Fixer failed: {e}")
    # Handle error appropriately
```

### Resource Management

```python
# Use context managers where available
with tempfile.TemporaryDirectory() as temp_dir:
    result = fixer.run(output_dir=temp_dir)

# Clean up resources
fixer.cleanup()
```

### Performance Optimization

```python
# Enable caching for repeated runs
config.cache_enabled = True

# Increase concurrency for fast networks
config.download_concurrency = 5

# Use specific backends for better performance
result = fixer.run(search_backends=["civitai"])  # Skip slower backends
```

This API reference covers the main public interfaces. For internal implementation details, see the source code and architecture documentation.