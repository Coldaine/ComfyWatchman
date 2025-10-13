# Developer Guide

This guide provides information for developers who want to contribute to ComfyFixerSmart, including setup, development workflow, and contribution guidelines.

## Development Setup

### Prerequisites

- **Python**: 3.7 or higher
- **Git**: For version control
- **ComfyUI**: For testing workflows
- **Civitai API Key**: For integration testing

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/comfyfixersmart.git
cd comfyfixersmart

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e .[dev]

# Verify installation
comfyfixer --version
pytest --version
```

### Development Dependencies

The `[dev]` extra includes:
- `pytest` - Testing framework
- `black` - Code formatting
- `flake8` - Linting
- `mypy` - Type checking
- `pre-commit` - Git hooks
- `sphinx` - Documentation building

## Development Workflow

### 1. Choose an Issue

- Check [GitHub Issues](https://github.com/yourusername/comfyfixersmart/issues) for open tasks
- Look for issues labeled `good first issue` or `help wanted`
- Comment on the issue to indicate you're working on it

### 2. Create a Branch

```bash
# Create and switch to feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-number-description
```

### 3. Make Changes

Follow the coding standards:
- Use `black` for code formatting
- Add type hints for new functions
- Write comprehensive tests
- Update documentation

### 4. Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_config.py

# Run with coverage
pytest --cov=comfyfixersmart --cov-report=html

# Run linting
black src/
flake8 src/
mypy src/
```

### 5. Commit Changes

```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "feat: add new feature description

- What was changed
- Why it was changed
- Any breaking changes
"

# Follow conventional commit format
# Types: feat, fix, docs, style, refactor, test, chore
```

### 6. Create Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# Create PR on GitHub with:
# - Clear title and description
# - Reference to issue number
# - Screenshots if UI changes
# - Test results
```

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use `black` for automatic formatting
- Maximum line length: 88 characters (black default)
- Use type hints for function parameters and return values

### Example Code Style

```python
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

def process_models(model_names: List[str], api_key: Optional[str] = None) -> List[dict]:
    """
    Process a list of model names and return metadata.

    Args:
        model_names: List of model filenames to process
        api_key: Optional API key for authenticated requests

    Returns:
        List of model metadata dictionaries

    Raises:
        ValueError: If model_names is empty
    """
    if not model_names:
        raise ValueError("model_names cannot be empty")

    results = []
    for name in model_names:
        try:
            metadata = fetch_model_metadata(name, api_key)
            results.append(metadata)
        except Exception as e:
            logger.error(f"Failed to process {name}: {e}")
            continue

    return results
```

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `ModelResolver`)
- **Functions/Methods**: `snake_case` (e.g., `resolve_model`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`)
- **Modules**: `snake_case` (e.g., `civitai_resolver.py`)

### Documentation

- Use docstrings for all public functions, classes, and modules
- Follow Google docstring format
- Include type hints in docstrings when helpful
- Document exceptions that may be raised

## Testing Guidelines

### Test Structure

```python
import pytest
from comfyfixersmart.module import ClassToTest

class TestClassToTest:
    """Test cases for ClassToTest."""

    def test_success_case(self, mock_dependency):
        """Test the happy path."""
        # Arrange
        instance = ClassToTest()
        expected = "expected_result"

        # Act
        result = instance.method("input")

        # Assert
        assert result == expected

    def test_error_case(self):
        """Test error handling."""
        instance = ClassToTest()

        with pytest.raises(ValueError, match="error message"):
            instance.method("invalid_input")

    def test_edge_case(self, tmp_path):
        """Test edge cases with temporary files."""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"key": "value"}')

        result = process_file(test_file)
        assert result["key"] == "value"
```

### Test Coverage

- Aim for 90%+ code coverage
- Test both success and failure paths
- Mock external dependencies (API calls, file I/O)
- Use fixtures for common test setup

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage report
pytest --cov=comfyfixersmart --cov-report=html

# Specific test
pytest tests/unit/test_config.py::TestConfig::test_load_config

# Debug failing test
pytest --pdb -x
```

## Architecture Overview

### Core Components

```
src/comfyfixersmart/
├── __init__.py          # Package initialization
├── cli.py              # Command-line interface
├── core.py             # Main orchestration logic
├── config.py           # Configuration management
├── scanner.py          # Workflow scanning and parsing
├── inventory.py        # Local model inventory management
├── search.py           # Model search across backends
├── download.py         # Download management
├── state_manager.py    # State persistence and tracking
├── logging.py          # Logging configuration
└── utils.py            # Utility functions
```

### Key Design Patterns

1. **Command Pattern**: CLI commands are implemented as separate classes
2. **Strategy Pattern**: Different search backends (Civitai, HuggingFace)
3. **Observer Pattern**: Progress reporting and logging
4. **Factory Pattern**: Component creation and configuration

### Data Flow

```
CLI Args/Config → Core Orchestrator → Scanner → Analyzer → Search → Download
                              ↓
                        State Manager (persistence)
                              ↓
                            Logger (output)
```

## Adding New Features

### 1. Plan the Feature

- Define the problem and solution
- Consider impact on existing code
- Plan backward compatibility
- Design API and configuration options

### 2. Implement Core Logic

```python
# Example: Add new search backend
class NewBackend:
    def search(self, query: str) -> List[ModelResult]:
        # Implementation
        pass

    def download(self, model_id: str) -> bytes:
        # Implementation
        pass
```

### 3. Add Configuration

```toml
# config/default.toml
[search]
backends = ["civitai", "huggingface", "newbackend"]

[search.newbackend]
api_url = "https://api.newbackend.com"
timeout = 30
```

### 4. Update CLI

```python
# cli.py
@click.option('--search', default='civitai',
              help='Search backends (comma-separated)')
def main(search):
    backends = search.split(',')
    # Use backends...
```

### 5. Add Tests

```python
def test_new_backend_search():
    backend = NewBackend()
    results = backend.search("test model")
    assert len(results) > 0
    assert results[0].name == "test model"
```

### 6. Update Documentation

- Add to user guide
- Update configuration reference
- Add examples

## Debugging

### Enable Debug Logging

```bash
comfyfixer --log-level DEBUG --verbose
```

### Debug Configuration

```bash
# Validate configuration
comfyfixer --validate-config

# Show configuration sources
comfyfixer --show-config
```

### Common Debug Scenarios

1. **API Issues**:
   ```bash
   # Test API connectivity
   curl -H "Authorization: Bearer $CIVITAI_API_KEY" \
        https://civitai.com/api/v1/models?limit=1
   ```

2. **Configuration Problems**:
   ```python
   # Debug config loading
   python -c "from comfyfixersmart.config import load_config; print(load_config())"
   ```

3. **Workflow Parsing**:
   ```python
   # Test workflow parsing
   python -c "
   from comfyfixersmart.scanner import scan_workflow
   result = scan_workflow('test.json')
   print(result)
   "
   ```

## Performance Optimization

### Profiling

```bash
# Profile execution
python -m cProfile -s time comfy_fixer.py

# Memory profiling
pip install memory-profiler
python -m memory_profiler comfy_fixer.py
```

### Optimization Techniques

1. **Caching**: Cache API responses and model metadata
2. **Async I/O**: Use async downloads for concurrency
3. **Lazy Loading**: Load data only when needed
4. **Batch Processing**: Process multiple items together

### Performance Monitoring

```python
import time
from functools import wraps

def time_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper
```

## Contributing Guidelines

### Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Update** documentation
6. **Submit** pull request

### PR Requirements

- [ ] Tests pass (`pytest`)
- [ ] Code formatted (`black`)
- [ ] Linting passes (`flake8`)
- [ ] Type checking passes (`mypy`)
- [ ] Documentation updated
- [ ] Changelog updated (if needed)

### Code Review Process

1. **Automated Checks**: CI runs tests and linting
2. **Peer Review**: At least one maintainer reviews
3. **Discussion**: Address review comments
4. **Approval**: Maintainers approve and merge

### Release Process

1. **Version Bump**: Update version in `pyproject.toml`
2. **Changelog**: Update `CHANGELOG.md`
3. **Tag**: Create git tag
4. **Build**: CI builds and publishes
5. **Announce**: Create GitHub release

## Getting Help

### Resources

- **Issues**: https://github.com/yourusername/comfyfixersmart/issues
- **Discussions**: https://github.com/yourusername/comfyfixersmart/discussions
- **Documentation**: https://comfyfixersmart.readthedocs.io/

### Communication

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Pull Requests**: For code contributions

### Community

- Follow conventional commit messages
- Be respectful and inclusive
- Help other contributors
- Share knowledge and best practices

## Advanced Topics

### Custom Search Backends

Implement the `SearchBackend` interface:

```python
from abc import ABC, abstractmethod
from typing import List
from .models import ModelResult

class SearchBackend(ABC):
    @abstractmethod
    def search(self, query: str, model_type: str = None) -> List[ModelResult]:
        """Search for models matching the query."""
        pass

    @abstractmethod
    def get_model_details(self, model_id: str) -> ModelResult:
        """Get detailed information for a specific model."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Backend name for configuration."""
        pass
```

### Plugin System

ComfyFixerSmart supports plugins for extending functionality:

```python
# plugin_example.py
from comfyfixersmart.plugin import Plugin

class ExamplePlugin(Plugin):
    name = "example"
    version = "1.0.0"

    def setup(self, app):
        # Register hooks, add commands, etc.
        pass
```

### Internationalization

For adding new languages:

1. Extract strings to `.pot` file
2. Create `.po` files for each language
3. Compile to `.mo` files
4. Use `gettext` for translations

This developer guide provides the foundation for contributing to ComfyFixerSmart. Remember to always test your changes and follow the established patterns and conventions.