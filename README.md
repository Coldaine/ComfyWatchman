# ComfyWatchman

**Agent-Callable Tools for ComfyUI Workflow Analysis & Model Resolution**

[![PyPI version](https://badge.fury.io/py/comfywatchman.svg)](https://pypi.org/project/comfywatchman/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

ComfyWatchman provides **Python APIs and tools designed for AI agents** to analyze ComfyUI workflows, identify missing models, search across multiple sources (Civitai, HuggingFace), and automatically download dependencies.

**🤖 Built for AI Agents** - Not a standalone CLI tool for end users. ComfyWatchman is a library of callable functions that AI agents (like Claude, ChatGPT, or custom automation) invoke to manage ComfyUI workflows programmatically.

**🔗 Designed to complement [ComfyUI-Copilot](https://github.com/AIDC-AI/ComfyUI-Copilot)** - While Copilot excels at workflow generation and interactive debugging, ComfyWatchman provides superior dependency management and multi-backend search as callable tools.

**✨ Key Features:**
- 🤖 **Agent-Callable APIs** - Python functions designed for AI agents to invoke
- 🔍 **Workflow Analysis Tools** - Parse ComfyUI JSON and extract model dependencies
- 🔎 **Multi-Backend Search** - Civitai + HuggingFace + Qwen AI agent
- 📥 **Automatic Downloads** - Download models with SHA256 verification and retry logic
- 🎯 **Granular Control** - Agents decide when to scan, search, or download
- 📊 **Structured Returns** - All functions return JSON/dataclass results for agent decision-making
- 🔧 **DirectID Backend** - Known model lookup database for instant resolution
- 🧠 **Embedding Awareness** - Detects textual inversion references and queues them automatically
- 🕒 **Guardrailed Scheduler** - Optional background automation with GPU VRAM safety checks
- 🔌 **Integration Ready** - Adapters for ComfyUI-Copilot and other tools

## 🚀 Quick Start for AI Agents

### Installation

```bash
# Install as a library
pip install comfywatchman

# Or install from source
git clone https://github.com/yourusername/comfywatchman.git
cd comfywatchman
pip install -e .
```

### Agent Usage Example

```python
from comfyfixersmart.scanner import WorkflowScanner
from comfyfixersmart.search import ModelSearch
from comfyfixersmart.civitai_tools.direct_downloader import CivitaiDirectDownloader

# Agent calls these functions as needed:

# 1. Scan a workflow
scanner = WorkflowScanner()
models = scanner.extract_models_from_workflow("workflow.json")

# 2. Search for a missing model (now with Qwen intelligence)
search = ModelSearch()
result = search.search_model({"filename": "rife49.pth"})  # Automatically detects HuggingFace model

# 3. Download if found
if result.status == "FOUND":
    if result.source == "civitai":
        downloader = CivitaiDirectDownloader()
        download_result = downloader.download_by_id(
            result.civitai_id,
            result.version_id
        )
    elif result.source == "huggingface":
        # New: HuggingFace download support
        hf_downloader = HuggingFaceDownloader()
        download_result = hf_downloader.download_from_repo(
            result.repo_name,
            result.file_path
        )
elif result.status == "UNCERTAIN":
    # New: Handle uncertain matches with human review
    print(f"Multiple candidates found for {result.filename}")
    for candidate in result.candidates:
        print(f"- {candidate['source']}: {candidate['name']} (confidence: {candidate['match_score']})")
```

### Configuration

Set environment variables for API access:

```bash
export CIVITAI_API_KEY="your-api-key"
export COMFYUI_ROOT="/path/to/comfyui"
export HF_TOKEN="your-huggingface-token"  # Optional
```

### New Qwen Search Features

ComfyWatchman now includes advanced AI-powered search capabilities:

#### 🤖 Qwen Agentic Search
- **Intelligent Pattern Recognition**: Automatically detects model types and sources from filenames
- **Multi-Phase Search Strategy**: Civitai API → Web Search → HuggingFace verification
- **Exact Filename Validation**: Prevents downloading wrong models with strict matching

#### 🔍 Smart Pattern Recognition
The system recognizes common model patterns:
- `rife*.pth` → Frame interpolation models (HuggingFace)
- `sam_*.pth` → Facebook SAM models (HuggingFace)
- `*.safetensors` → Checkpoints (Civitai primary)
- `*.pt` → Various model types with context-aware routing

#### 🌐 Web search via Qwen
When Civitai doesn't have exact matches, the system:
- Uses Qwen's built-in web_search tool to search HuggingFace and GitHub
- Extracts repository information from search results
- Verifies file existence before download
- Provides confidence scoring for uncertain matches

#### 🔐 Hash-Based Fallback
For models already downloaded locally:
- Calculates SHA256 hashes
- Uses hash lookup for model identification
- Enables identification without known filenames

#### ✅ Enhanced Filename Validation
Early detection and rejection of invalid filenames:
- URL parameters (`?modelVersionId=123`)
- Invalid characters and special symbols
- Prevents wasted API calls on malformed inputs

## 📖 Documentation

📚 **[Full Documentation](docs/README.md)** - Complete user and developer guides

### Current Roadmap Status (October 2025)

We are actively executing **Phase 1: Strengthen Core** from the three-phase roadmap in `docs/CROSSROADS.md`.

- ✅ Completed: consolidated Python package (`src/comfyfixersmart`), unified CLI (`comfywatchman` command), agentic search pipeline (Qwen → Civitai → web fallback), state-backed download manager, and TOML/env-based configuration.
- 🔄 In Progress: documentation polish and developer onboarding materials (this README + `docs/` refresh), packaging cleanup for PyPI, and CLI ergonomics.
- ⏳ Not Yet Started (Phase 1 items): external plugin API surface, optional telemetry hooks, extended integration examples.

Phase 2 (optimization layer) and Phase 3 (ecosystem integrations) remain future work; no engineering has begun on those tracks yet.

### Quick Links

- **[AI Agent Guide](CLAUDE.md)** - Complete guide for AI agents using ComfyWatchman
- **[Developer Guide](docs/developer/developer-guide.md)** - Contributing and development
- **[API Reference](docs/developer/api-reference.md)** - Python API documentation

### Vision & Architecture

- **[Vision](docs/vision.md)** — Where ComfyWatchman is headed (LLM + RAG, hardware‑aware reviews, safety, and automation philosophy)
- **[Proposed Architecture](docs/architecture.md)** — Component design for LLM‑assisted review, local knowledge pack/RAG, and end‑to‑end orchestration
- **[Search Architecture](docs/SEARCH_ARCHITECTURE.md)** — Agentic search system (Qwen web search), multi-source federation (Civitai, HuggingFace), and doubt handling

### Research & Strategic Direction

- **[🔀 CROSSROADS: Strategic Decision Framework](docs/CROSSROADS.md)** — **Critical decision point:** Fork, extend, complement, or build? Evaluation of 4 strategic paths forward
- **[Research Prompt](docs/research/RESEARCH_PROMPT.md)** — Ultimate vision for automated ComfyUI workflow generation & optimization
- **[Existing Systems Analysis](docs/research/EXISTING_SYSTEMS.md)** — Comprehensive review of 15+ existing tools (ComfyUI-Copilot, ComfyScript, ComfyGPT, etc.)
- **[ComfyUI-Copilot Deep Dive](docs/research/ComfyUI-Copilot-Research-Report.md)** — Detailed analysis of ComfyUI-Copilot architecture and capabilities

### Search System Details

- **[Search Architecture](docs/SEARCH_ARCHITECTURE.md)** — Complete guide to agentic search with Qwen
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

## 🔧 How AI Agents Use It

AI agents call ComfyWatchman functions to manage ComfyUI workflows:

1. **Scan** - `scanner.extract_models_from_workflow()` → Returns list of model dependencies
2. **Search** - `search.search_model(model_info)` → Returns SearchResult with download URL
3. **Download** - `downloader.download_by_id(civitai_id)` → Downloads and verifies model
4. **Inventory** - `inventory.build_inventory()` → Lists locally available models

Agents make decisions based on structured returns (SearchResult, DownloadResult, etc.) and invoke only the tools they need.

## 🎯 Use Cases

- **AI Agent Assistants** - Claude/ChatGPT helping users set up ComfyUI workflows
- **Automated Pipelines** - Bots that analyze and prepare workflows automatically
- **Workflow Validation** - Agents checking if workflows will run before execution
- **Dependency Resolution** - Tools that automatically fix missing model issues
- **MCP Servers** - Model Context Protocol servers exposing these tools

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

**Ready to integrate?** Check out the [AI Agent Guide](CLAUDE.md) for complete API documentation and usage patterns!
