# ComfyWatchman (ComfyFixerSmart) - Project Context

## Overview

ComfyWatchman (originally called ComfyFixerSmart) is an AI agent-callable Python library for analyzing ComfyUI workflows and automatically downloading missing models from multiple sources (Civitai and HuggingFace). The tool provides intelligent search capabilities using Qwen agents, automatic dependency resolution, and state management for ComfyUI model downloads.

## Project Architecture

### Core Components

- **scanner.py**: Workflow parsing and model extraction from ComfyUI JSON files
- **search.py**: Multi-source search orchestration (Civitai, HuggingFace, Qwen agents)
- **download.py**: Download management with retries, verification, and state tracking
- **inventory.py**: Local model inventory and status tracking
- **config.py**: Configuration management with TOML and environment variable support
- **cli.py**: Command-line interface with v1/v2 compatibility modes

### Key Features

- **Workflow Analysis**: Parses ComfyUI JSON files to extract model dependencies
- **Multi-Backend Search**: Civitai API, HuggingFace, and Qwen-powered agentic search
- **State Management**: Tracks download status and prevents duplicate attempts
- **Automatic Download**: Downloads models to correct ComfyUI subdirectories
- **Embedding Recognition**: Detects textual inversion references automatically
- **Filename Validation**: Early detection of invalid model filenames
- **Hash-Based Lookup**: SHA256 verification and local model identification

## Configuration

### Environment Variables
- `CIVITAI_API_KEY`: Required for Civitai API access
- `COMFYUI_ROOT`: Path to ComfyUI installation directory
- `HF_TOKEN`: Optional HuggingFace token for private models
- `QWEN_BINARY`: Path to Qwen CLI tool (default: `qwen`)

### TOML Configuration
Located in `config/`, with defaults in `config-example.toml`

## Command Line Usage

### Basic Analysis
```bash
# Analyze specific workflow
comfywatchman workflow.json

# Analyze directory
comfywatchman --dir /path/to/workflows

# Use specific search backends
comfywatchman --search qwen,civitai
```

### Scheduler Mode
```bash
# Run continuous background analysis
comfywatchman --scheduler --scheduler-interval 60
```

### Inspector Tool
```bash
# Inspect models without loading tensors
comfywatchman inspect model.safetensors
```

## Development

### Installation
```bash
pip install -e .
# or
pip install -r requirements.txt
```

### Testing
```bash
pytest tests/
```

### Main Entry Points
- `comfyfixersmart.cli:main` - Command line interface
- `comfyfixersmart.core:ComfyFixerCore` - Main orchestrator class
- `comfyfixersmart.search:ModelSearch` - Search orchestration
- `comfyfixersmart.scanner:WorkflowScanner` - Workflow parsing

## Key Design Patterns

### Agentic Search Architecture
The system uses Qwen agents for intelligent model discovery, implementing a multi-phase search strategy:
1. Direct ID lookup from known models database
2. Civitai API search with advanced filtering
3. Web search via Qwen tools for HuggingFace models
4. Hash-based fallback for local models

### Model Type Mapping
Automatically maps ComfyUI node types to appropriate model directories:
- `CheckpointLoaderSimple` → `checkpoints`
- `LoraLoader` → `loras`
- `VAELoader` → `vae`
- `ControlNetLoader` → `controlnet`
- etc.

### State Management
- Tracks download attempts and results via JSON state files
- Implements retry logic with configurable backoff
- Prevents duplicate downloads of the same model

## File Structure
- `src/comfyfixersmart/` - Main Python package
- `tests/` - Unit and integration tests
- `docs/` - Documentation files
- `config/` - Configuration files and examples
- `scripts/` - Utility scripts
- `state/` - Download state tracking
- `log/` - Log files

## Development Guidelines

### Contributing
- Follow PEP 8 style guidelines (enforced with Ruff)
- Write tests for new functionality
- Update documentation for public APIs
- Use type hints where possible

### Architecture Principles
- Maintain backward compatibility where possible
- Keep AI agent integration as the primary use case
- Prioritize reliability over speed for downloads
- Implement comprehensive error handling