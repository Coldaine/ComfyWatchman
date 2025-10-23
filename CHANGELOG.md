# Changelog

All notable changes to ComfyFixerSmart will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Model Inspection & Metadata
- **Safe Model Metadata Inspector** - `comfy-inspect` command and library module for deterministic inspection
  - Supports safetensors, ONNX, and optional pickle formats (.ckpt, .pt, .pth)
  - SHA256 hashing for integrity verification
  - Memory-safe inspection without loading full tensors
  - Comprehensive CLI with `--format`, `--hash`, `--recursive`, `--unsafe` options
- `comfywatchman inspect` subcommand for integrated inspection workflow
- `comfyfixersmart.inspector` library module with safe inspection APIs
  - `inspect_file()` - Single file inspection
  - `inspect_paths()` - Batch directory inspection
  - `InspectionResult` dataclass with metadata, tensor info, and hashes

#### ComfyUI-Copilot Integration
- **Adapter pattern foundation** for extensible external integrations
  - `BaseAdapter` abstract base class with initialization lifecycle
  - Three production adapters:
    - `CopilotValidatorAdapter` - Workflow validation via ComfyUI-Copilot
    - `SqlStateAdapter` - Optional SQL-based state persistence (alternative to JSON)
    - `ModelScopeSearchAdapter` - ModelScope model hub search backend
  - `ModelScopeSearchFallback` - Download fallback for ModelScope models
- Copilot integration as git submodule at `src/copilot_backend/`
- Adapter configuration in TOML with enable/disable flags
- Integration strategy documentation explaining complementary positioning

#### Multi-Backend Search System
- **ModelScope search backend** - Alternative to Civitai with fallback download capability
- **Agentic search orchestration** via Qwen agent with multi-phase approach:
  - Phase 1: Structured search with Civitai API
  - Phase 2: Web search via Tavily for extended discovery
  - Phase 3: HuggingFace hub integration
  - Decision-making for best download source
- Enhanced search architecture with configurable backend ordering
- Backend selection now uses config defaults (qwen, civitai, huggingface) instead of hardcoded

#### Documentation & Planning
- **40+ new documentation files** organized into logical sections:
  - `docs/planning/` - Feature plans and implementation guides
    - `EMBEDDING_SUPPORT_PLAN.md` - Embedding model support (1099 lines)
    - `QWEN_SEARCH_IMPLEMENTATION_PLAN.md` - Agentic search architecture
    - `AGENT_GUIDE.md` - Guidance for AI agents using this tool
    - `INCREMENTAL_WORKFLOW.md` - Incremental processing patterns
  - `docs/reports/` - Incident reports and analysis
    - `civitai-api-wrong-metadata-incident.md` - Root cause and lessons learned
    - `WAN22_POV_MISSIONARY_ANALYSIS.md` - Workflow analysis (817 lines)
    - `WAN22_POV_MISSION_ANALYSIS.md` - Mission-focused analysis (525 lines)
    - `CLAUDE_VERIFICATION.md` - AI verification results
  - `docs/developer/` - Developer guides
    - `api-reference.md` - Complete API documentation (660 lines)
    - `developer-guide.md` - Development workflow guide (535 lines)
    - `release-process.md` - Version management and releases (348 lines)
    - `testing.md` - Testing strategy and frameworks
    - `workflow_tooling_guide.md` - Workflow analysis tooling
  - `docs/user/` - User-facing guides
    - `cli-reference.md` - Complete CLI documentation
    - `configuration.md` - Configuration guide (442 lines)
    - `examples.md` - Usage examples and workflows
    - `troubleshooting.md` - Common issues and solutions
  - `docs/technical/` - Technical specifications
    - `DOMAIN_ARCHITECTURE_STANDARDS.md` - Architecture design standards
    - `integrations.md` - Integration patterns and APIs (769 lines)
    - `performance.md` - Performance tuning guide (452 lines)
    - `faq.md` - Frequently asked questions (530 lines)
  - `docs/research/` - Research and analysis
    - `ComfyUI-Copilot-Research-Report.md` - Deep integration analysis
    - `EXISTING_SYSTEMS.md` - Landscape of 15+ related tools
  - `docs/adr/` - Architecture decision records
  - `docs/vision.md` - Long-term vision and roadmap

#### Testing Infrastructure
- **Comprehensive test suite** with 5,000+ lines of test code
  - Unit tests: `test_config.py`, `test_inspector.py`, `test_logging.py`, `test_state_manager.py`, `test_utils.py` (874 lines)
  - Integration tests: `test_cli.py`, `test_core.py`, `test_end_to_end.py`
  - Functional tests: `test_scanner.py`, `test_search.py`, `test_download.py`, `test_inventory.py`, `test_civitai_search.py`, `test_single_search.py`
  - Test fixtures and conftest with extensive fixtures (237 lines)
  - Mock data and sample workflows for reproducibility

#### Configuration & Deployment
- `.kilocodemodes` configuration for Kilo Code IDE integration
- `.gitignore` hardened to exclude model weights and generated artifacts
- Pre-commit git hooks (`.githooks/pre-commit`) to prevent large file commits (≥90MB)
- `config/default.toml` - Default production configuration
- `config-example.toml` - Template configuration with all options
- Environment variable support for all configuration options

#### Utilities & Helpers
- Enhanced utility functions in `utils.py` (132+ lines added)
  - URL parsing and validation
  - String sanitization for model names
  - Download verification helpers
  - Path manipulation utilities
- Download script generation with safety checks
- Comprehensive error messages and user feedback

### Changed

#### Search & Discovery
- **V2 mode search backend fix** - Now uses config-defined backends (Qwen, Civitai, HuggingFace) instead of hardcoded Civitai-only
  - Enables full agentic search capabilities as originally intended
  - Respects backend ordering from configuration
- Search architecture completely redesigned with adapter pattern
- Backend selection now configurable per mode (V1 vs V2)
- Search result confidence scoring improved with multi-source data

#### Model Inspection
- Inspector refactored from single module to structured submodule:
  - `inspector/__init__.py` - Public API exports
  - `inspector/cli.py` - CLI implementation (127 lines)
  - `inspector/inspector.py` - Core inspection logic (560 lines)
  - `inspector/logging.py` - Inspector-specific logging
- Moved from `cli_inspect.py` to proper submodule structure

#### Documentation & Communication
- **README.md** updated with:
  - Prominent "Relationship to ComfyUI-Copilot" section
  - Integration positioning (complementary vs competitive)
  - Upstream remote explanation (for different codebase)
  - Feature differentiation callouts
  - Modern formatting and badges
- **CLAUDE.md** expanded with explicit integration strategy:
  - Strategic positioning section (193 lines added)
  - Hybrid architecture details
  - Integration pathways (adapters, standalone mode, API)
  - Key documents and references
  - Clear upstream remote purpose
- Configuration documentation expanded (442 lines in `docs/user/configuration.md`)
- Comprehensive integration guide (769 lines in `docs/technical/integrations.md`)

#### Configuration System
- TOML configuration now fully integrated with environment variable override
- Configuration validation with fail-fast for missing required fields (COMFYUI_ROOT)
- Backend ordering configuration with sensible defaults
- Adapter configuration flags for optional features

#### Build & Package Management
- `pyproject.toml` updated with:
  - New optional dependency groups: `[inspector]`, `[copilot]`, `[modelscope]`, `[full]`
  - Entry point for `comfy-inspect` standalone tool
  - Updated classifiers and metadata
- `setup.py` modernized with package discovery

#### Download Management
- Generated download scripts now force ComfyUI/models directory (no user path override)
- Download verification enhanced with better error messages
- State tracking improved for multi-phase operations

### Fixed

#### Critical Issues
- **Civitai API Wrong Metadata Incident** - Documented root cause analysis:
  - Image metadata was incorrectly retrieved from model objects instead of file objects
  - Search was returning wrong image previews in some cases
  - Code fixes applied to search.py for proper metadata extraction
  - Comprehensive incident report in `docs/reports/civitai-api-wrong-metadata-incident.md`
- **V2 search mode backend selection** - V2 now respects config defaults and full backend chain
- **Git hygiene** - Pre-commit hooks prevent accidental large file commits

#### Code Quality
- Fixed all code review feedback from ModelScope integration
- Improved error handling in adapter initialization
- Enhanced logging throughout all modules
- Better exception messages with context

### Removed

#### Legacy Code
- Old Node.js/React UI code (moved to Copilot submodule)
- Legacy backend implementation files
- Hardcoded search backend configuration
- Manual configuration templates (replaced with TOML)

#### Unnecessary Files
- Old assets and image files
- Outdated localization files (zh/en JSON)
- Legacy entry point scripts
- Old test data files (replaced with new fixtures)

### Security

#### Safety Improvements
- **Pre-commit hooks** block commits with files ≥90MB to prevent accidental large file uploads
- **Safe model inspection** - Inspector never loads full tensors into memory
- Pickle format inspection requires explicit `--unsafe` flag with user confirmation
- Input validation and sanitization throughout CLI
- File path validation to prevent directory traversal
- HTTPS-only for all external API communication

#### Repository Hygiene
- Model weights explicitly excluded from git tracking (.gitignore)
- Tighter ignore patterns for generated artifacts
- Clear separation between tracked code and data artifacts
- Security policy documented for safe model handling

## [2.0.0] - 2025-10-12

### Added
- **Incremental Workflow System** - Complete redesign for better performance
  - Search and download one model at a time
  - Immediate downloads without waiting for batch completion
  - Built-in verification every 6 downloads
  - Real-time progress visibility
- **Enhanced Configuration System** - TOML-based configuration with environment variable support
- **Multi-Backend Search** - Support for Civitai and HuggingFace APIs
- **Comprehensive CLI** - Full command-line interface with extensive options
- **State Management** - Persistent tracking of downloads and operations
- **Detailed Reporting** - Human-readable reports and JSON exports
- **Caching System** - Intelligent caching to reduce API calls
- **Resume Support** - Ability to resume interrupted downloads
- **Cross-Platform Support** - Windows, macOS, and Linux compatibility

### Changed
- **Architecture Overhaul** - Modular design with clear separation of concerns
- **Performance Improvements** - 3x faster for typical workflows
- **Memory Usage** - 50% reduction in memory footprint
- **Error Handling** - Robust error recovery and user-friendly messages
- **API Design** - Clean Python API for programmatic usage

### Removed
- Legacy batch processing mode (available as `--v1` compatibility)
- Hardcoded paths and configurations
- Manual script execution requirements

### Fixed
- Race conditions in concurrent downloads
- Memory leaks in long-running operations
- API rate limiting issues
- File permission handling
- Network timeout issues

### Security
- Secure API key handling
- HTTPS-only communications
- Input validation and sanitization
- Safe file operations

## [1.5.0] - 2025-09-15

### Added
- HuggingFace backend support as fallback
- Progress bars for long operations
- JSON export functionality
- Basic caching for API responses

### Changed
- Improved error messages and user feedback
- Better handling of network timeouts
- Enhanced logging with structured output

### Fixed
- Issues with special characters in model names
- Memory usage for large workflow files
- API authentication edge cases

## [1.0.0] - 2025-08-01

### Added
- Initial release of ComfyFixerSmart
- Basic workflow analysis functionality
- Civitai API integration
- Automatic model downloading
- Command-line interface
- Basic configuration support

### Changed
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- Basic input validation
- Safe file operations

---

## Version Numbering

We use [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 2.1.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

## Types of Changes

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** in case of vulnerabilities

## Release Frequency

- **Major releases**: As needed for breaking changes
- **Minor releases**: Monthly for new features
- **Patch releases**: As needed for bug fixes

## Support Timeline

- **Current version**: Full support
- **Previous major version**: Critical fixes only
- **Older versions**: Security fixes only

---

For the most up-to-date information, check the [GitHub Releases](https://github.com/yourusername/comfyfixersmart/releases) page.
