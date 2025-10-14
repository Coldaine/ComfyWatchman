# ComfyWatchman

**Automated ComfyUI Workflow Readiness, Analysis & Model Resolution**

[![PyPI version](https://badge.fury.io/py/comfywatchman.svg)](https://pypi.org/project/comfywatchman/)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

ComfyWatchman is an intelligent, scheduled assistant that continuously analyzes ComfyUI workflows, identifies missing models and custom nodes, searches for replacements on Civitai and HuggingFace, and downloads them to the correct directories while generating readiness reports and a local dashboard.

**✨ Key Features:**
- 🔍 **Automatic Workflow Analysis** - Parses ComfyUI JSON workflows
- 🔎 **Intelligent Model Search** - Searches Civitai and HuggingFace APIs
- 📥 **Smart Downloads** - Incremental processing with immediate downloads
- ✅ **Built-in Verification** - File integrity and compatibility checks
- 🛠️ **Comprehensive CLI** - Full command-line interface with extensive options
- 📊 **Detailed Reporting** - Human-readable reports and JSON exports
- 🔧 **Highly Configurable** - TOML-based configuration system
- 🐳 **Container Ready** - Docker and CI/CD integration support

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
pip install comfywatchman

# Or install from source
git clone https://github.com/yourusername/comfywatchman.git
cd comfywatchman
pip install -e .
```

### Basic Usage

```bash
# Analyze all workflows in default directories
comfywatchman

# Analyze specific workflow
comfywatchman my_workflow.json

# Analyze workflows in custom directory
comfywatchman --dir /path/to/workflows
```

### Configuration

1. **Get Civitai API Key:**
   - Visit https://civitai.com/user/account
   - Generate API key

2. **Configure Environment:**
   ```bash
   export CIVITAI_API_KEY="your-api-key"
   export COMFYUI_ROOT="/path/to/comfyui"
   ```

3. **Or use configuration file:**
   ```toml
   # config/default.toml
   comfyui_root = "/path/to/comfyui"
   civitai_api_key = "your-api-key"
   ```

## 📖 Documentation

📚 **[Full Documentation](docs/README.md)** - Complete user and developer guides

### Current Roadmap Status (October 2025)

We are actively executing **Phase 1: Strengthen Core** from the three-phase roadmap in `docs/CROSSROADS.md`.

- ✅ Completed: consolidated Python package (`src/comfyfixersmart`), unified CLI (`comfywatchman` command), agentic search pipeline (Qwen → Civitai → web fallback), state-backed download manager, and TOML/env-based configuration.
- 🔄 In Progress: documentation polish and developer onboarding materials (this README + `docs/` refresh), packaging cleanup for PyPI, and CLI ergonomics.
- ⏳ Not Yet Started (Phase 1 items): external plugin API surface, optional telemetry hooks, extended integration examples.

Phase 2 (optimization layer) and Phase 3 (ecosystem integrations) remain future work; no engineering has begun on those tracks yet.

### Quick Links

- **[User Guide](docs/user/user-guide.md)** - Installation, setup, and usage
- **[Configuration](docs/user/configuration.md)** - Detailed configuration options
- **[CLI Reference](docs/user/cli-reference.md)** - All command-line options
- **[Troubleshooting](docs/user/troubleshooting.md)** - Common issues and solutions
- **[Examples](docs/user/examples.md)** - Usage examples and tutorials
- **[Developer Guide](docs/developer/developer-guide.md)** - Contributing and development
- **[API Reference](docs/developer/api-reference.md)** - Python API documentation

### Vision & Architecture

- **[Vision](docs/vision.md)** — Where ComfyWatchman is headed (LLM + RAG, hardware‑aware reviews, safety, and automation philosophy)
- **[Proposed Architecture](docs/architecture.md)** — Component design for LLM‑assisted review, local knowledge pack/RAG, and end‑to‑end orchestration
- **[Search Architecture](docs/SEARCH_ARCHITECTURE.md)** — Agentic search system (Qwen + Tavily), multi-source federation (Civitai, HuggingFace), and doubt handling

### Research & Strategic Direction

- **[🔀 CROSSROADS: Strategic Decision Framework](docs/CROSSROADS.md)** — **Critical decision point:** Fork, extend, complement, or build? Evaluation of 4 strategic paths forward
- **[Research Prompt](docs/research/RESEARCH_PROMPT.md)** — Ultimate vision for automated ComfyUI workflow generation & optimization
- **[Existing Systems Analysis](docs/research/EXISTING_SYSTEMS.md)** — Comprehensive review of 15+ existing tools (ComfyUI-Copilot, ComfyScript, ComfyGPT, etc.)
- **[ComfyUI-Copilot Deep Dive](docs/research/ComfyUI-Copilot-Research-Report.md)** — Detailed analysis of ComfyUI-Copilot architecture and capabilities

### Search System Details

- **[Search Architecture](docs/SEARCH_ARCHITECTURE.md)** — Complete guide to agentic search with Qwen + Tavily
- **[Qwen Search Plan](docs/planning/QWEN_SEARCH_IMPLEMENTATION_PLAN.md)** — Original implementation plan and requirements
- **[Qwen Operator Guide](docs/planning/QWEN_PROMPT.md)** — Prompt engineering and agent instructions
- **[Agent Guide](docs/planning/AGENT_GUIDE.md)** — Guide for AI agents using ComfyWatchman

Planned: Automatic, continuously updated Workflow Health Report (supersedes `workflow_analysis_report.md`). See [Vision](docs/vision.md) and [Proposed Architecture](docs/architecture.md).

> **Owner Directive:** Phase 1 and Phase 2 requirements documented in the Vision, Architecture, and Thought Process files are mandatory and must not be modified without the owner's explicit consent.

## 📋 Requirements

**Required:**

- Python 3.7+
- Civitai API key (free account)
- ComfyUI installation

**Optional:**

- HuggingFace token (for private models)
- Qwen CLI (for agentic search - recommended)
- Tavily API key (for web search fallback)

## 🔧 How It Works

1. **Workflow Analysis** - Parses ComfyUI JSON workflows to extract model references
2. **Inventory Check** - Compares against local ComfyUI model directories
3. **Agentic Search** - Uses Qwen AI agent to intelligently search Civitai and HuggingFace with exact filename validation
4. **Web Search Fallback** - Falls back to Tavily web search for models not found via APIs
5. **Smart Downloads** - Downloads models to correct directories with verification
6. **Comprehensive Reporting** - Generates detailed reports and download scripts

## 🎯 Use Cases

- **Workflow Setup** - Quickly download all models needed for a workflow
- **Batch Processing** - Analyze entire workflow collections
- **CI/CD Integration** - Automate model management in deployment pipelines
- **Model Management** - Keep model libraries synchronized with workflows
- **Troubleshooting** - Identify and resolve missing dependency issues

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](docs/CONTRIBUTING.md) for details.

- 🐛 **Bug Reports** - [GitHub Issues](https://github.com/yourusername/comfywatchman/issues)
- 💡 **Feature Requests** - [GitHub Discussions](https://github.com/yourusername/comfywatchman/discussions)
- 🛠️ **Code Contributions** - Pull requests welcome

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- ComfyUI community for the amazing ecosystem
- Civitai for providing comprehensive model APIs
- HuggingFace for open model hosting
- All contributors and users

---

**Ready to get started?** Check out the [User Guide](docs/user/user-guide.md) for detailed instructions!
