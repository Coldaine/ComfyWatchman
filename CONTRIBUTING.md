# Contributing to ComfyFixerSmart

Thank you for your interest in contributing to ComfyFixerSmart! We welcome contributions from the community and are grateful for your help in making this project better.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)
- [Community](#community)

## Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. By participating, you agree to:

- Be respectful and inclusive
- Focus on constructive feedback
- Accept responsibility for mistakes
- Show empathy towards other contributors
- Help create a positive community

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Git
- A Civitai account with API key (for testing)
- ComfyUI installation (for integration testing)

### Quick Setup

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/comfywatchman.git
cd comfywatchman

# Set up development environment
pip install -e .[dev]

# Run basic tests
pytest tests/unit/ -v
```

## Development Setup

### 1. Fork the Repository

1. Go to https://github.com/yourusername/comfywatchman
2. Click "Fork" in the top right
3. Clone your fork: `git clone https://github.com/YOUR_USERNAME/comfywatchman.git`

### 2. Create a Development Environment

```bash
cd comfywatchman

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

### 3. Configure Development Settings

```bash
# Copy development configuration
cp config/example.toml config/dev.toml

# Edit with your settings
# config/dev.toml
comfyui_root = "/path/to/your/comfyui"
log_level = "DEBUG"
cache_enabled = false  # Disable for development
```

### 4. Run Initial Tests

```bash
# Run quick test to verify setup
comfyfixer --validate-config

# Run unit tests
pytest tests/unit/ -v
```

## Development Workflow

### 1. Choose an Issue

- Check [GitHub Issues](https://github.com/yourusername/comfywatchman/issues) for open tasks
- Look for issues labeled `good first issue` or `help wanted`
- Comment on the issue to indicate you're working on it

### 2. Create a Feature Branch

```bash
# Create and switch to feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-number-description

# Or for documentation
git checkout -b docs/improve-user-guide
```

### 3. Make Changes

Follow the coding standards and make incremental commits:

```bash
# Make your changes
# Test frequently
pytest tests/unit/test_your_feature.py

# Stage and commit
git add .
git commit -m "feat: add new feature description

- What was changed
- Why it was changed
- Any breaking changes
"
```

### 4. Test Thoroughly

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=comfywatchman --cov-report=html

# Run linting
black src/
flake8 src/
mypy src/

# Test CLI
comfyfixer --help
comfyfixer --validate-config
```

### 5. Update Documentation

```bash
# Update relevant documentation
# Add examples for new features
# Update API documentation
```

### 6. Submit Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# Create PR on GitHub with:
# - Clear title and description
# - Reference to issue number
# - Screenshots for UI changes
# - Test results
```

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) conventions
- Use `black` for automatic code formatting (88 character line length)
- Use type hints for function parameters and return values
- Write descriptive variable and function names

### Example Code Style

```python
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ModelDownloader:
    """Handles downloading of ComfyUI models."""

    def __init__(self, api_key: str, timeout: int = 300) -> None:
        self.api_key = api_key
        self.timeout = timeout

    def download_model(
        self,
        model_id: str,
        save_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Download a model from Civitai.

        Args:
            model_id: Civitai model ID
            save_path: Local path to save the model
            progress_callback: Optional callback for download progress

        Returns:
            True if download successful, False otherwise

        Raises:
            DownloadError: If download fails
        """
        try:
            # Implementation here
            logger.info(f"Downloading model {model_id}")
            return True
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise DownloadError(f"Failed to download {model_id}") from e
```

### Commit Messages

Follow [Conventional Commits](https://conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

**Examples:**
```
feat: add HuggingFace backend support
fix: resolve memory leak in download manager
docs: update API reference for new methods
test: add integration tests for CLI
```

## Testing

### Test Structure

```
tests/
├── unit/           # Unit tests (fast, isolated)
├── functional/     # Component integration tests
├── integration/    # End-to-end workflow tests
├── fixtures/       # Test data and fixtures
└── conftest.py     # Shared test configuration
```

### Writing Tests

```python
import pytest
from comfywatchman.scanner import WorkflowScanner

class TestWorkflowScanner:
    """Test cases for WorkflowScanner."""

    def test_parse_valid_workflow(self, sample_workflow_data):
        """Test parsing a valid workflow JSON."""
        scanner = WorkflowScanner()
        result = scanner.parse_workflow_data(sample_workflow_data)

        assert result is not None
        assert len(result.model_references) > 0

    def test_handle_invalid_json(self):
        """Test error handling for invalid JSON."""
        scanner = WorkflowScanner()

        with pytest.raises(ValueError, match="Invalid JSON"):
            scanner.parse_workflow_data("invalid json")

    def test_extract_model_references(self, sample_workflow_data):
        """Test extraction of model references."""
        scanner = WorkflowScanner()
        models = scanner.extract_models(sample_workflow_data)

        assert isinstance(models, list)
        assert all(isinstance(m, ModelReference) for m in models)
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_scanner.py

# Specific test
pytest tests/unit/test_scanner.py::TestWorkflowScanner::test_parse_valid_workflow

# With coverage
pytest --cov=comfywatchman --cov-report=html

# Run only failing tests
pytest --lf

# Run tests in parallel
pytest -n auto
```

### Test Coverage Goals

- **Unit Tests**: 90%+ coverage
- **Integration Tests**: All critical user workflows
- **Performance Tests**: Key operations benchmarked

## Documentation

### Documentation Standards

- Use Markdown for all documentation
- Keep documentation in the `docs/` directory
- Update documentation with code changes
- Include code examples where helpful
- Test documentation builds

### Updating Documentation

```bash
# Update API documentation
# Add new examples
# Update configuration reference
# Test documentation links
```

### Documentation Checklist

- [ ] API documentation updated
- [ ] User guide updated for new features
- [ ] Configuration documentation updated
- [ ] Examples added for new functionality
- [ ] Changelog updated
- [ ] Breaking changes documented

## Submitting Changes

### Pull Request Process

1. **Ensure all tests pass**
2. **Update documentation**
3. **Add changelog entry**
4. **Get code review**
5. **Address review comments**
6. **Merge when approved**

### PR Template

```markdown
## Description
Brief description of the changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests pass
- [ ] Changelog updated
- [ ] Breaking changes documented
```

### Code Review Process

**Reviewers will check:**
- Code quality and style
- Test coverage
- Documentation updates
- Breaking changes
- Security implications
- Performance impact

**Address review comments:**
- Make requested changes
- Explain decisions when needed
- Ask for clarification if unclear
- Mark conversations as resolved

## Reporting Issues

### Bug Reports

**Include:**
- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Error messages and logs
- Minimal reproduction case

**Template:**
```markdown
**Bug Description**
Clear description of the issue.

**Steps to Reproduce**
1. Step 1
2. Step 2
3. Expected: what should happen
4. Actual: what actually happens

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.9.7]
- ComfyFixerSmart: [e.g., 2.0.0]

**Logs**
```
paste logs here
```

**Screenshots**
If applicable, add screenshots.
```

### Feature Requests

**Include:**
- Clear description of the proposed feature
- Use case and benefits
- Implementation suggestions (optional)
- Mockups or examples (if UI-related)

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and design discussions
- **Pull Requests**: Code contributions

### Getting Help

- Check existing issues and documentation first
- Search GitHub discussions
- Open new issue for help
- Be patient and provide context

### Recognition

Contributors are recognized in:
- GitHub contributor statistics
- CHANGELOG.md for significant contributions
- Project documentation

### Governance

- **Maintainers**: Core team responsible for releases and major decisions
- **Contributors**: Community members who contribute code, docs, or issues
- **Users**: Community members who use and provide feedback

## Recognition

We appreciate all contributions, big and small! Contributors may be:

- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Invited to join the maintainer team
- Recognized in project documentation

Thank you for contributing to ComfyFixerSmart! 🎉