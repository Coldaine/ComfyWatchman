# Installation Guide for ComfyFixerSmart

This guide covers all the ways to install and use ComfyFixerSmart.

## Prerequisites

- **Python**: 3.7 or higher
- **Civitai API Key**: Required for model downloads (see Configuration section)
- **Qwen CLI** (optional): For enhanced search capabilities

## Quick Installation

### From PyPI (when published)

```bash
pip install comfyfixersmart
```

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/comfyfixersmart.git
cd comfyfixersmart

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e .[dev]
```

### Using requirements files

```bash
# Install runtime dependencies only
pip install -r requirements.txt

# Install with development dependencies
pip install -r requirements-dev.txt
```

## Configuration

### 1. Civitai API Key

ComfyFixerSmart requires a Civitai API key for downloading models. You have two options:

**Option A: Environment Variable**
```bash
export CIVITAI_API_KEY="your-api-key-here"
```

**Option B: Secrets File**
Create `~/.secrets` file with:
```
CIVITAI_API_KEY=your-api-key-here
```

### 2. ComfyUI Path Configuration

ComfyFixerSmart requires you to configure the path to your ComfyUI installation. There is no default path - you must specify it.

To configure the ComfyUI path, you can:

**Option A: Configuration File (Recommended)**
Create `config/default.toml` with:
```toml
comfyui_root = "/path/to/your/comfyui"
workflow_dirs = [
    "user/default/workflows"
]
```

See `config-example.toml` for a complete configuration template.</search>
</search_and_replace>

**Option A: Environment Variable**
```bash
export COMFYUI_ROOT="/path/to/your/comfyui"
```

**Option B: Configuration File**
Create a custom config file and pass it with `--config`:
```bash
comfyfixer --config /path/to/your/config.toml
```

**Option C: Command Line**
```bash
comfyfixer --comfyui-root /path/to/your/comfyui
```

### 3. Workflow Directories

By default, ComfyFixerSmart scans:
- `$COMFYUI_ROOT/user/default/workflows`

To scan additional directories:
```bash
comfyfixer --dir /path/to/workflows --dir /another/workflow/dir
```

## Usage

### Basic Usage

```bash
# Analyze all workflows in default directories
comfyfixer

# Analyze specific workflow files
comfyfixer workflow1.json workflow2.json

# Analyze workflows in specific directories
comfyfixer --dir /path/to/workflows

# Use different search backends
comfyfixer --search civitai,huggingface

# Change output directory
comfyfixer --output-dir /tmp/comfyfixer-output

# Enable URL verification (requires Qwen CLI)
comfyfixer --verify-urls
```

### Command Line Options

```
Usage: comfyfixer [OPTIONS] [workflows ...]

Options:
  workflows               Specific workflow files to analyze
  --dir, --workflow-dir   Directory to scan for workflow files (can be used multiple times)
  --search, --backends    Comma-separated list of search backends (default: civitai)
  --output-dir            Output directory for results
  --no-script             Skip generating download script
  --verify-urls           Enable URL verification during downloads
  --config                Path to configuration file
  --comfyui-root          Path to ComfyUI installation
  --log-level             Set logging level (DEBUG, INFO, WARNING, ERROR)
  --quiet                 Suppress non-error output
  --version               Show version information
  --help                  Show this help message
```

### Compatibility Modes

```bash
# V1 compatibility mode (incremental processing)
comfyfixer --v1

# V2 mode (batch processing, default)
comfyfixer --v2
```

## Development Installation

For contributors and developers:

```bash
# Clone repository
git clone https://github.com/yourusername/comfyfixersmart.git
cd comfyfixersmart

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e .[dev]

# Run tests
pytest

# Run linting
black src/
flake8 src/
mypy src/
```

## Building for Distribution

To build the package for distribution:

```bash
# Build source distribution and wheel
python -m build

# Or using setuptools
python setup.py sdist bdist_wheel
```

## Docker Installation (Future)

A Docker image will be available for easy deployment:

```bash
# Pull the image
docker pull comfyfixersmart/comfyfixersmart

# Run with mounted volumes
docker run -v /path/to/comfyui:/comfyui -v /path/to/workflows:/workflows \
  -e CIVITAI_API_KEY=your-key \
  comfyfixersmart/comfyfixersmart
```

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Ensure you're using Python 3.7+
   - Try reinstalling: `pip install -e .`

2. **Civitai API errors**
   - Verify your API key is set correctly
   - Check your internet connection
   - Ensure the API key has proper permissions

3. **ComfyUI path not found**
   - Verify the ComfyUI installation path
   - Use `--comfyui-root` to specify the correct path

4. **Permission errors**
   - Ensure write permissions for output directories
   - Check file permissions for ComfyUI model directories

### Getting Help

- Check the logs in the `log/` directory
- Use `--log-level DEBUG` for detailed output
- Review the README.md for detailed usage examples
- Check GitHub issues for known problems

## System Requirements

- **OS**: Linux, macOS, Windows
- **Python**: 3.7, 3.8, 3.9, 3.10, 3.11, 3.12
- **Memory**: 512MB minimum, 2GB recommended
- **Disk**: 100MB for installation, varies for model downloads
- **Network**: Internet connection for API access and downloads