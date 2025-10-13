# Configuration Guide

This guide covers all configuration options available in ComfyFixerSmart, including environment variables, configuration files, and command-line options.

## Configuration Methods

ComfyFixerSmart supports multiple configuration methods, applied in this priority order:

1. **Command-line arguments** (highest priority)
2. **Environment variables**
3. **Configuration file** (`config/default.toml`)
4. **Default values** (lowest priority)

## Configuration File

The recommended way to configure ComfyFixerSmart is through a TOML configuration file.

### Basic Configuration

Create `config/default.toml`:

```toml
# ComfyUI Installation Path (REQUIRED)
comfyui_root = "/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable"

# Workflow Directories to Scan
workflow_dirs = [
    "user/default/workflows",
    "user/custom/workflows"
]

# Search Backends (in priority order)
search_backends = ["civitai", "huggingface"]

# Download Configuration
download_concurrency = 3
download_timeout = 300
verify_downloads = true

# Caching
cache_enabled = true
cache_ttl_hours = 24

# Logging
log_level = "INFO"
log_file = "logs/comfyfixer.log"

# Output
output_dir = "output"
```

### Advanced Configuration

```toml
# ComfyUI Installation Path
comfyui_root = "/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable"

# Workflow Scanning
workflow_dirs = [
    "user/default/workflows",
    "user/custom/workflows",
    "community_workflows"
]
scan_hidden_dirs = false
follow_symlinks = true

# Search Configuration
search_backends = ["civitai", "huggingface"]
civitai_api_timeout = 30
civitai_search_limit = 10
huggingface_timeout = 30

# Download Configuration
download_concurrency = 3
download_timeout = 300
download_retries = 3
download_chunk_size = 8192
verify_downloads = true
resume_downloads = true

# Model Directories (custom mappings)
model_directories = [
    { type = "checkpoint", path = "models/checkpoints" },
    { type = "lora", path = "models/loras" },
    { type = "vae", path = "models/vae" },
    { type = "controlnet", path = "models/controlnet" },
    { type = "upscale", path = "models/upscale_models" },
    { type = "clip_vision", path = "models/clip_vision" },
    { type = "embeddings", path = "models/embeddings" }
]

# Caching
cache_enabled = true
cache_ttl_hours = 24
cache_max_size_mb = 100
cache_dir = ".cache"

# Logging
log_level = "INFO"
log_file = "logs/comfyfixer.log"
log_max_size_mb = 10
log_backup_count = 5
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Output
output_dir = "output"
reports_dir = "reports"
scripts_dir = "scripts"

# Security
api_key_file = "~/.secrets"
allow_insecure_downloads = false

# Performance
max_workers = 4
memory_limit_mb = 1024

# Experimental Features
experimental_features = []
```

## Environment Variables

### Required Variables

```bash
# Civitai API Key (REQUIRED)
export CIVITAI_API_KEY="your-civitai-api-key"

# ComfyUI Installation Path (REQUIRED)
export COMFYUI_ROOT="/path/to/comfyui"
```

### Optional Variables

```bash
# Search Configuration
export CIVITAI_API_TIMEOUT="30"
export HF_TOKEN="your-huggingface-token"

# Download Configuration
export DOWNLOAD_CONCURRENCY="3"
export DOWNLOAD_TIMEOUT="300"

# Logging
export LOG_LEVEL="INFO"
export LOG_FILE="logs/comfyfixer.log"

# Output
export OUTPUT_DIR="output"

# Caching
export CACHE_ENABLED="true"
export CACHE_TTL_HOURS="24"
```

## Command-Line Options

### Core Options

```bash
# Configuration
--config PATH              # Path to configuration file
--comfyui-root PATH        # ComfyUI installation path

# Workflow Selection
--dir PATH                 # Directory to scan for workflows (can be used multiple times)
--workflow PATH            # Specific workflow file to analyze

# Search Configuration
--search BACKENDS          # Comma-separated search backends (civitai,huggingface)
--no-cache                 # Disable caching for this run

# Download Configuration
--output-dir PATH          # Output directory for results
--no-script                # Skip generating download script
--verify-urls              # Enable URL verification during downloads

# Logging
--log-level LEVEL          # Set logging level (DEBUG, INFO, WARNING, ERROR)
--quiet                    # Suppress non-error output
--verbose                  # Enable verbose output

# Other
--version                  # Show version information
--help                     # Show help message
```

### Examples

```bash
# Use custom config file
comfyfixer --config /path/to/custom.toml

# Scan specific directory
comfyfixer --dir /path/to/workflows

# Use only HuggingFace search
comfyfixer --search huggingface

# Debug mode with verbose output
comfyfixer --log-level DEBUG --verbose

# Custom output directory
comfyfixer --output-dir /tmp/results
```

## Configuration Sections

### ComfyUI Configuration

```toml
[comfyui]
root = "/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable"
custom_nodes_dir = "custom_nodes"
models_dir = "models"
workflows_dir = "user/default/workflows"
outputs_dir = "output"
temp_dir = "temp"
```

### Search Backend Configuration

```toml
[search]
backends = ["civitai", "huggingface"]
default_backend = "civitai"

[search.civitai]
api_key = "your-api-key"  # Can also use env var
timeout = 30
search_limit = 10
rate_limit_delay = 1.0

[search.huggingface]
token = "your-token"  # Optional
timeout = 30
use_mirror = false
```

### Download Configuration

```toml
[download]
concurrency = 3
timeout = 300
retries = 3
chunk_size = 8192
verify = true
resume = true
progress_bar = true

[download.wget]
use_wget = true
wget_options = ["--continue", "--progress=bar", "--timeout=30"]
```

### Cache Configuration

```toml
[cache]
enabled = true
ttl_hours = 24
max_size_mb = 100
dir = ".cache"
auto_cleanup = true

[cache.sqlite]
path = ".cache/comfyfixer.db"
pragma_journal_mode = "WAL"
pragma_synchronous = "NORMAL"
```

### Logging Configuration

```toml
[logging]
level = "INFO"
file = "logs/comfyfixer.log"
max_size_mb = 10
backup_count = 5
format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

[logging.console]
enabled = true
level = "INFO"

[logging.file]
enabled = true
level = "DEBUG"
```

## Model Directory Mappings

ComfyFixerSmart automatically maps model types to their correct directories in ComfyUI:

```toml
# Default mappings
model_directories = [
    { type = "checkpoint", path = "models/checkpoints" },
    { type = "lora", path = "models/loras" },
    { type = "vae", path = "models/vae" },
    { type = "controlnet", path = "models/controlnet" },
    { type = "upscale", path = "models/upscale_models" },
    { type = "clip_vision", path = "models/clip_vision" },
    { type = "embeddings", path = "models/embeddings" },
    { type = "hypernetwork", path = "models/hypernetworks" },
    { type = "photomaker", path = "models/photomaker" },
    { type = "insightface", path = "models/insightface" },
    { type = "ultralytics", path = "models/ultralytics" }
]
```

You can override these mappings in your configuration file.

## Validation

ComfyFixerSmart validates your configuration on startup:

### Required Settings

- `comfyui_root`: Must be a valid directory
- `civitai_api_key`: Must be set (via config, env var, or secrets file)

### Optional Validations

- Directory paths: Checked for existence and permissions
- API timeouts: Must be positive integers
- Concurrency: Must be between 1-10
- Log levels: Must be DEBUG, INFO, WARNING, ERROR, CRITICAL

### Configuration Errors

If configuration is invalid, ComfyFixerSmart will:

1. Show specific error messages
2. Suggest corrections
3. Exit with non-zero status code

Example error output:
```
Configuration Error: comfyui_root is not a valid directory
Path: /invalid/path
Suggestion: Check that ComfyUI is installed at the specified location
```

## Environment-Specific Configuration

### Development Configuration

```toml
# config/dev.toml
log_level = "DEBUG"
cache_enabled = false
download_concurrency = 1
verify_downloads = false
```

### Production Configuration

```toml
# config/prod.toml
log_level = "WARNING"
cache_enabled = true
download_concurrency = 5
verify_downloads = true
```

Use with: `comfyfixer --config config/prod.toml`

## Secrets Management

### API Keys

ComfyFixerSmart supports multiple ways to manage API keys:

1. **Environment Variables** (recommended for CI/CD)
2. **Secrets File** (`~/.secrets`)
3. **Configuration File** (not recommended for production)

### Secrets File Format

Create `~/.secrets`:
```
CIVITAI_API_KEY=your-civitai-key
HF_TOKEN=your-huggingface-token
```

File permissions should be `600` (owner read/write only).

## Troubleshooting Configuration

### Common Issues

**"Configuration file not found"**
- Ensure the file exists at the specified path
- Check file permissions
- Use absolute paths

**"Invalid TOML syntax"**
- Validate your TOML syntax
- Check for missing quotes around strings
- Ensure arrays are properly formatted

**"Environment variable not set"**
- Check variable name spelling
- Ensure the variable is exported
- Use `env | grep VARIABLE` to verify

**"Permission denied"**
- Check directory permissions
- Ensure ComfyUI directories are writable
- Run with appropriate user permissions

### Debugging Configuration

Enable debug logging to see configuration loading:

```bash
comfyfixer --log-level DEBUG --verbose
```

This will show:
- Configuration file paths being checked
- Environment variables being read
- Configuration values being applied
- Validation results

### Configuration Validation

Test your configuration without running the full analysis:

```bash
comfyfixer --validate-config
```

This will:
- Load and validate configuration
- Check ComfyUI installation
- Verify API key accessibility
- Report any issues found