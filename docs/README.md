# ComfyWatchman Documentation

Welcome to the documentation for ComfyWatchman, a library of **agent-callable tools** for analyzing ComfyUI workflows and managing model dependencies.

**🤖 Built for AI Agents** - ComfyWatchman is not a standalone CLI for end users. It's a Python library designed for AI agents (like Claude, ChatGPT, or custom automation) to invoke programmatically.

## Documentation Structure

### 🤖 AI Agent Documentation

- **[AI Agent Guide](../CLAUDE.md)** - Complete guide for agents calling ComfyWatchman tools
- **[API Reference](developer/api-reference.md)** - Python API documentation for all tools

### 🛠️ Developer Documentation

- **[Developer Guide](developer/developer-guide.md)** - Contributing guidelines and development setup
- **[Architecture](developer/architecture.md)** - System architecture and design decisions
- **[API Reference](developer/api-reference.md)** - API documentation for modules
- **[Testing](developer/testing.md)** - Testing guidelines and practices
- **[Release Process](developer/release-process.md)** - Release and deployment process

### 🔧 Technical Documentation

- **[Migration Guide](technical/migration-guide.md)** - Guide for migrating between versions
- **[Performance](technical/performance.md)** - Performance considerations and optimization
- **[Integrations](technical/integrations.md)** - Integration with other tools and systems
- **[FAQ](technical/faq.md)** - Frequently asked questions

### 📋 Project Documentation

- **[README](../README.md)** - Main project README
- **[CHANGELOG](../CHANGELOG.md)** - Version history and changes
- **[CONTRIBUTING](../CONTRIBUTING.md)** - Contribution guidelines
- **[LICENSE](../LICENSE)** - Project license

## Quick Start

### For AI Agents
1. **Integration**: Start with the [AI Agent Guide](../CLAUDE.md)
2. **API Reference**: See [API Reference](developer/api-reference.md) for all callable tools

### For Developers
1. **Setup**: Follow the [Developer Guide](developer/developer-guide.md)
2. **Architecture**: Understand the system in [Architecture](architecture/vision.md)
3. **Testing**: Learn about testing in [Testing](developer/testing.md)

## Building Documentation

To build and validate documentation:

```bash
# Build documentation
make docs

# Validate links and structure
make validate-docs

# Clean build artifacts
make clean-docs
```

## Contributing to Documentation

When contributing to documentation:

1. Follow the established structure and formatting
2. Update cross-references when adding new documents
3. Test documentation builds with `make validate-docs`
4. Keep content up-to-date with code changes
5. Use consistent terminology and formatting

## Support

- **Issues**: Report documentation issues on GitHub
- **Discussions**: Join community discussions for questions
- **Contributing**: See [CONTRIBUTING](../CONTRIBUTING.md) for contribution guidelines

---

*Last updated: 2025-10-12*