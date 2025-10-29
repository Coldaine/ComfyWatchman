# User Guide

Welcome to ComfyFixerSmart! This guide will help you get started with installing, configuring, and using the tool to automatically analyze your ComfyUI workflows and download missing models.

## What is ComfyFixerSmart?

ComfyFixerSmart is an intelligent agent-based tool that:

1. **Scans** your ComfyUI workflow files
2. **Finds** missing models and custom nodes
3. **Searches** Civitai (and optionally HuggingFace) for replacements
4. **Downloads** models automatically to the correct directories
5. **Verifies** downloads and generates reports

**NEW in v2.0:** Completely redesigned incremental workflow for better reliability and performance.

## Quick Start

### Prerequisites

- **Python**: 3.7 or higher
- **Civitai API Key**: Required for model downloads
- **ComfyUI Installation**: Path to your ComfyUI directory

### Basic Installation

```bash
# Install from source
git clone https://github.com/yourusername/comfyfixersmart.git
cd comfyfixersmart
pip install -e .
```

### Quick Setup

1. **Get Civitai API Key**
   - Visit https://civitai.com/user/account
   - Create an API key
   - Add to `~/.secrets`: `export CIVITAI_API_KEY="your_key_here"`

2. **Configure ComfyUI Path**
   ```bash
   # Option 1: Environment variable
   export COMFYUI_ROOT="/path/to/your/comfyui"

   # Option 2: Configuration file
   # Create config/default.toml with:
   # comfyui_root = "/path/to/your/comfyui"
   ```

3. **Run the Tool**
   ```bash
   comfyfixer
   ```

That's it! ComfyFixerSmart will scan your workflows, find missing models, and download them automatically.

## Installation

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

### Using Requirements Files

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

**Option A: Configuration File (Recommended)**
Create `config/default.toml` with:
```toml
comfyui_root = "/path/to/your/comfyui"
workflow_dirs = [
    "user/default/workflows"
]
```

**Option B: Environment Variable**
```bash
export COMFYUI_ROOT="/path/to/your/comfyui"
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

## How It Works

### Incremental Workflow (v2.0)

For each missing model:

1. **Search Phase (~1.7 min)**
    - Searches Civitai API with smart filtering
    - Falls back to HuggingFace for standard models
    - Exact filename matching

2. **Download Phase (immediate)**
    - Generates individual script: `download_NNN_modelname.sh`
    - Executes download automatically
    - Saves to correct model directory

3. **Verification Phase (every 6 models)**
    - Checks if files exist
    - Verifies file sizes (not corrupted)
    - Reports any failures

### Key Features

✅ **Incremental Processing** - Search & download one model at a time
✅ **Immediate Downloads** - No waiting for all searches to complete
✅ **Auto-Verification** - Checks every 6 downloads
✅ **No Caching** - Fresh searches every time (no preserved failures)
✅ **Individual Scripts** - `download_001_model.sh`, `download_002_model.sh`, etc.
✅ **Real-time Progress** - See each model as it's processed
✅ **Automatic** - Fully unattended after confirmation

### Example Output

```
[1/21] Processing: rife49.pth
  Launching Qwen search...
  ✓ Found on HuggingFace: AlexWortega/RIFE
  Generated: download_001_rife49_pth.sh
  Executing download: download_001_rife49_pth.sh
  ✓ Download completed successfully

[2/21] Processing: sam_vit_b_01ec64.pth
  ...

[6/21] Processing: model006.pth
  ✓ Download completed successfully

===========================================================
Verifying last 6 downloads with Qwen
===========================================================
  ✓ Verified: 6 models

[7/21] Processing: next_model.pth
  ...
```

## Directory Structure

After running ComfyFixerSmart, your project will have:

```
ComfyFixerSmart/
├── comfy_fixer.py               # Main script (v2.0 - Incremental)
├── output/
│   ├── download_001_rife49_pth.sh       # Individual download scripts
│   ├── download_002_sam_vit_b.sh
│   ├── download_003_...sh
│   ├── download_counter.txt              # Tracks script numbering
│   ├── downloaded_models.json            # Successfully downloaded
│   └── missing_models.json               # Original missing list
├── log/
│   ├── run_YYYYMMDD_HHMMSS.log          # Full execution log
│   └── qwen_search_history.log          # Detailed search attempts
└── INCREMENTAL_WORKFLOW.md              # Full workflow documentation
```

## Customization

Edit `comfy_fixer.py` to change:
- `COMFYUI_ROOT` - Path to your ComfyUI installation (line 33)
- `WORKFLOW_DIRS` - Directories to scan for workflows (line 34-36)
- Model type mappings (line 101-113)

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

## Troubleshooting

### Common Issues

**"CIVITAI_API_KEY not found"**
- Add to `~/.secrets`: `export CIVITAI_API_KEY="your_key"`
- Get key from: https://civitai.com/user/account

**"Qwen command not found"**
- Install Qwen CLI first

**"No workflows found"**
- Check `WORKFLOW_DIR` path
- Ensure .json workflow files exist

**"Model not found on Civitai"**
- Check the analysis report for manual search links
- Model may have been removed or renamed

## Next Steps

- Check the [Configuration Guide](configuration.md) for advanced setup options
- See [Examples](examples.md) for detailed usage scenarios
- Visit [Troubleshooting](troubleshooting.md) if you encounter issues
- Review the [CLI Reference](cli-reference.md) for all command options