# Changelog

All notable changes to ComfyFixerSmart will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `comfywatchman inspect` command for deterministic model metadata summaries
- Standalone `comfy-inspect` console script exposing the inspector without the main CLI
- `comfyfixersmart.inspector` library module with safe inspection APIs
- Usage guide at `docs/usage/inspect.md`
- Comprehensive documentation structure in `docs/` directory
- User guides, developer documentation, and API reference
- Performance optimization guides and troubleshooting documentation
- Integration guides for CI/CD, Docker, and enterprise systems

### Changed
- Reorganized documentation into logical sections
- Updated README with modern formatting and badges
- Consolidated existing documentation from archives

### Fixed
- Documentation links and cross-references
- Formatting consistency across all documents

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
