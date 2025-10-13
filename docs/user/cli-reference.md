# CLI Reference

This document provides a complete reference for all ComfyFixerSmart command-line options and usage patterns.

## Synopsis

```bash
comfyfixer [OPTIONS] [WORKFLOWS ...]
```

## Description

ComfyFixerSmart analyzes ComfyUI workflow files, identifies missing models and custom nodes, searches for replacements on Civitai and HuggingFace, and generates download scripts.

## Options

### Core Options

| Option | Short | Description |
|--------|-------|-------------|
| `--help` | `-h` | Show help message and exit |
| `--version` | `-V` | Show version information and exit |
| `--config PATH` | | Path to configuration file (default: config/default.toml) |
| `--comfyui-root PATH` | | Path to ComfyUI installation |

### Workflow Selection

| Option | Short | Description |
|--------|-------|-------------|
| `--dir PATH` | `-d` | Directory to scan for workflow files (can be used multiple times) |
| `--workflow-dir PATH` | | Alias for --dir |
| `WORKFLOWS` | | Specific workflow files to analyze |

### Search Configuration

| Option | Short | Description |
|--------|-------|-------------|
| `--search BACKENDS` | | Comma-separated list of search backends (default: civitai) |
| `--backends BACKENDS` | | Alias for --search |
| `--no-cache` | | Disable caching for this run |
| `--cache-ttl HOURS` | | Cache time-to-live in hours (default: 24) |

### Download Configuration

| Option | Short | Description |
|--------|-------|-------------|
| `--output-dir PATH` | `-o` | Output directory for results (default: output) |
| `--no-script` | | Skip generating download script |
| `--verify-urls` | | Enable URL verification during downloads |
| `--download-timeout SEC` | | Download timeout in seconds (default: 300) |
| `--concurrency N` | | Number of concurrent downloads (default: 3) |

### Logging and Output

| Option | Short | Description |
|--------|-------|-------------|
| `--log-level LEVEL` | | Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `--log-file PATH` | | Path to log file |
| `--quiet` | `-q` | Suppress non-error output |
| `--verbose` | `-v` | Enable verbose output |
| `--progress` | | Show progress bars |

### Compatibility and Modes

| Option | Short | Description |
|--------|-------|-------------|
| `--v1` | | Run in v1 compatibility mode (incremental processing) |
| `--v2` | | Run in v2 mode (batch processing, default) |
| `--legacy` | | Enable legacy compatibility features |

### Advanced Options

| Option | Short | Description |
|--------|-------|-------------|
| `--dry-run` | | Show what would be done without making changes |
| `--validate-config` | | Validate configuration and exit |
| `--force` | | Force overwrite existing files |
| `--resume` | | Resume interrupted operations |
| `--max-workers N` | | Maximum number of worker threads |

## Usage Examples

### Basic Usage

```bash
# Analyze all workflows in default directories
comfyfixer

# Analyze specific workflow files
comfyfixer workflow1.json workflow2.json

# Analyze workflows in specific directory
comfyfixer --dir /path/to/workflows

# Use custom configuration
comfyfixer --config /path/to/config.toml
```

### Search and Download

```bash
# Use only Civitai search
comfyfixer --search civitai

# Use multiple search backends
comfyfixer --search civitai,huggingface

# Disable caching
comfyfixer --no-cache

# Custom output directory
comfyfixer --output-dir /tmp/results
```

### Logging and Debugging

```bash
# Debug mode
comfyfixer --log-level DEBUG

# Verbose output
comfyfixer --verbose

# Quiet mode (errors only)
comfyfixer --quiet

# Custom log file
comfyfixer --log-file /var/log/comfyfixer.log
```

### Advanced Configuration

```bash
# Custom ComfyUI path
comfyfixer --comfyui-root /opt/comfyui

# Multiple workflow directories
comfyfixer --dir /workflows --dir /more/workflows

# Download configuration
comfyfixer --concurrency 5 --download-timeout 600

# Validation only
comfyfixer --validate-config
```

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Network error |
| 4 | File system error |
| 5 | Validation error |
| 10 | Interrupted by user |

## Environment Variables

ComfyFixerSmart respects the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `CIVITAI_API_KEY` | Civitai API key | Required |
| `COMFYUI_ROOT` | ComfyUI installation path | Required |
| `HF_TOKEN` | HuggingFace API token | Optional |
| `LOG_LEVEL` | Logging level | INFO |
| `OUTPUT_DIR` | Output directory | output |
| `CACHE_ENABLED` | Enable caching | true |
| `DOWNLOAD_CONCURRENCY` | Concurrent downloads | 3 |

## Configuration File

ComfyFixerSmart can be configured via TOML files. Command-line options override configuration file settings.

Example `config/default.toml`:

```toml
comfyui_root = "/path/to/comfyui"
workflow_dirs = ["user/default/workflows"]
search_backends = ["civitai", "huggingface"]
download_concurrency = 3
log_level = "INFO"
output_dir = "output"
```

## Output Files

ComfyFixerSmart generates the following output files in the output directory:

### Reports

- `analysis_report.md` - Markdown report of analysis results
- `missing_models.json` - JSON list of missing models
- `available_models.json` - JSON list of available models
- `download_summary.json` - Summary of download operations

### Scripts

- `download_missing.sh` - Bash script to download all missing models
- `download_001_model.sh` - Individual download scripts (incremental mode)
- `download_002_model.sh` - Individual download scripts (incremental mode)

### Logs

- `comfyfixer_YYYYMMDD_HHMMSS.log` - Detailed execution log
- `search_history.log` - Search operation history
- `download_history.log` - Download operation history

### Cache

- `cache.db` - SQLite cache database (if enabled)
- `cache/` - Cache directory for temporary files

## Workflow Formats

ComfyFixerSmart supports ComfyUI workflow files in JSON format:

### Supported Node Types

- **CheckpointLoaderSimple** - Model checkpoints
- **LoraLoader** - LoRA models
- **VAELoader** - VAE models
- **ControlNetLoader** - ControlNet models
- **CLIPLoader** - CLIP models
- **UpscaleModelLoader** - Upscale models
- **CLIPVisionLoader** - CLIP Vision models

### Model Type Detection

ComfyFixerSmart automatically detects model types based on:

- Node type in workflow
- File extension
- Directory structure
- File content analysis

## Search Backends

### Civitai Backend

- **API**: https://civitai.com/api/v1
- **Authentication**: API key required
- **Features**: Model metadata, versions, download URLs
- **Limitations**: Requires API key, rate limited

### HuggingFace Backend

- **API**: https://huggingface.co/api
- **Authentication**: Optional token for private repos
- **Features**: Model discovery, direct downloads
- **Limitations**: Less metadata than Civitai

## Error Handling

### Common Errors

**Configuration Errors:**
```
Error: comfyui_root is not a valid directory
Suggestion: Check COMFYUI_ROOT environment variable or config file
```

**API Errors:**
```
Error: Civitai API key not found
Suggestion: Set CIVITAI_API_KEY environment variable or add to ~/.secrets
```

**Network Errors:**
```
Error: Connection timeout
Suggestion: Check internet connection or increase timeout with --download-timeout
```

**File System Errors:**
```
Error: Permission denied
Suggestion: Check write permissions for output directory
```

### Recovery Options

- `--resume` - Resume interrupted downloads
- `--force` - Overwrite existing files
- `--dry-run` - Preview operations without executing

## Performance Tuning

### Memory Usage

- **Default**: ~256MB base memory
- **Per workflow**: ~50MB additional
- **Large workflows**: Monitor memory usage

### Network Optimization

- **Concurrency**: Default 3 concurrent downloads
- **Timeout**: Default 300 seconds per download
- **Retries**: Automatic retry on failure

### Caching

- **Search cache**: 24 hour TTL by default
- **Model cache**: Reduces API calls for repeated models
- **File cache**: Resume support for large downloads

## Compatibility

### Operating Systems

- **Linux**: Fully supported
- **macOS**: Fully supported
- **Windows**: Supported via WSL or native Python

### Python Versions

- **Python 3.7+**: Required
- **Python 3.8+**: Recommended
- **Python 3.11+**: Best performance

### ComfyUI Versions

- **ComfyUI 1.0+**: Fully supported
- **Custom nodes**: Automatic detection
- **Workflow formats**: JSON workflows supported

## Troubleshooting

### Getting Help

```bash
# Show help
comfyfixer --help

# Show version
comfyfixer --version

# Validate configuration
comfyfixer --validate-config

# Debug mode
comfyfixer --log-level DEBUG --verbose
```

### Common Issues

1. **No workflows found**
   - Check `--dir` paths
   - Verify workflow files are JSON format
   - Check file permissions

2. **API connection failed**
   - Verify API key
   - Check internet connection
   - Try different search backend

3. **Download failed**
   - Check disk space
   - Verify write permissions
   - Try manual download with generated script

4. **Out of memory**
   - Reduce `--concurrency`
   - Process fewer workflows at once
   - Increase system memory

### Support Resources

- **Documentation**: See docs/ directory
- **Logs**: Check log files for detailed error information
- **Configuration**: Run `--validate-config` to check setup
- **Verbose mode**: Use `--verbose` for detailed operation info