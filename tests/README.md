# ComfyFixerSmart Testing Documentation

This directory contains comprehensive tests for the ComfyFixerSmart application, organized by test type and functionality.

## Test Organization

```
tests/
├── conftest.py              # Shared pytest fixtures and configuration
├── README.md               # This documentation
├── unit/                   # Unit tests for individual components
│   ├── test_config.py      # Configuration module tests
│   ├── test_logging.py     # Logging system tests
│   ├── test_state_manager.py # State management tests
│   └── test_utils.py       # Utility functions tests
├── functional/             # Functional tests for component integration
│   ├── test_scanner.py     # Workflow scanning tests
│   ├── test_inventory.py   # Model inventory tests
│   ├── test_search.py      # Model search functionality tests
│   ├── test_download.py    # Download management tests
│   ├── test_civitai_search.py  # Civitai API search tests
│   └── test_single_search.py   # Individual model search tests
├── integration/            # Integration tests for end-to-end workflows
│   ├── test_core.py        # Core orchestration tests
│   ├── test_cli.py         # Command-line interface tests
│   └── test_end_to_end.py  # Complete workflow tests
├── test_data/              # Test data files
│   ├── sample_workflow.json    # Sample ComfyUI workflow
│   └── mock_civitai_response.json  # Mock API responses
└── fixtures/               # Test fixtures directory
```

## Running Tests

### Prerequisites

Install development dependencies:
```bash
pip install -e .[dev]
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Functional tests only
pytest tests/functional/

# Integration tests only
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_config.py

# Run specific test
pytest tests/unit/test_config.py::TestConfig::test_config_defaults
```

### Test Options

```bash
# Run with coverage report
pytest --cov=comfyfixersmart --cov-report=html

# Run with verbose output
pytest -v

# Run tests in parallel (if pytest-xdist is installed)
pytest -n auto

# Run only tests marked as slow
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

## Test Coverage Goals

- **Unit Tests**: 90%+ coverage of individual functions and classes
- **Functional Tests**: Complete coverage of component interactions
- **Integration Tests**: End-to-end workflow validation
- **Overall Target**: 85%+ total code coverage

## Test Fixtures

### Shared Fixtures (conftest.py)

- `temp_dir`: Temporary directory for the test session
- `temp_config_dir`, `temp_log_dir`, `temp_state_dir`, `temp_output_dir`: Temporary directories for specific components
- `sample_config`: Sample configuration for testing
- `mock_logger`: Mock logger instance
- `state_manager`: StateManager instance for testing
- `sample_workflow_data`: Sample workflow JSON data
- `sample_workflow_file`: Temporary workflow file
- `mock_api_response`: Mock API response data
- `mock_huggingface_response`: Mock HuggingFace response data
- `mock_env_vars`: Mock environment variables
- `mock_requests_get`: Mock requests.get for API testing
- `mock_subprocess_run`: Mock subprocess.run for command execution
- `test_helpers`: Helper utilities for tests

## Test Categories

### Unit Tests

Test individual components in isolation:

- **Config Tests**: Configuration loading, validation, environment overrides
- **Logging Tests**: Logger setup, formatting, file rotation, structured logging
- **State Manager Tests**: Download tracking, persistence, migration, backup/restore
- **Utils Tests**: File operations, validation, JSON handling, model type detection

### Functional Tests

Test component interactions and real file system operations:

- **Scanner Tests**: Workflow parsing, model extraction, validation
- **Inventory Tests**: Model discovery, validation, comparison, export
- **Search Tests**: API backends, caching, result processing
- **Download Tests**: Script generation, execution, verification

### Integration Tests

Test complete workflows and CLI integration:

- **Core Tests**: End-to-end workflow orchestration
- **CLI Tests**: Command parsing, argument handling, output formatting
- **End-to-End Tests**: Complete user workflows with realistic data

## Mocking Strategy

### External Dependencies

- **API Calls**: Mocked using `unittest.mock` and `responses`
- **File System**: Use temporary directories and files
- **Network Requests**: Mocked to avoid external dependencies
- **Subprocess Calls**: Mocked for script execution testing

### Test Data

- **Workflows**: Sample ComfyUI workflow JSON files
- **Models**: Mock model files of various sizes and types
- **API Responses**: Pre-recorded API response data
- **Configurations**: Valid and invalid configuration examples

## Writing New Tests

### Test Structure

```python
import pytest
from comfyfixersmart.module import ClassToTest

class TestClassToTest:
    """Test cases for ClassToTest."""

    def test_method_success_case(self):
        """Test method with valid inputs."""
        # Arrange
        instance = ClassToTest()

        # Act
        result = instance.method(valid_input)

        # Assert
        assert result == expected_output

    def test_method_error_case(self):
        """Test method error handling."""
        # Arrange
        instance = ClassToTest()

        # Act & Assert
        with pytest.raises(ExpectedException):
            instance.method(invalid_input)
```

### Test Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Use descriptive names that explain what is being tested

### Fixtures Usage

```python
def test_with_fixture(self, temp_dir, sample_config):
    """Test using shared fixtures."""
    # temp_dir and sample_config are provided by conftest.py
    assert temp_dir.exists()
    assert sample_config.civitai_api_timeout == 30
```

## Continuous Integration

Tests are designed to run in CI environments:

- No external network calls (all mocked)
- No real file system dependencies
- Fast execution (< 5 minutes for full suite)
- Deterministic results

## Test Data Management

- Test data stored in `tests/test_data/`
- Mock responses in JSON format
- Sample workflows and configurations
- All test data is self-contained

## Coverage Reporting

Coverage reports are generated automatically:

- HTML reports in `htmlcov/`
- Terminal summary with `--cov-report=term-missing`
- Coverage configuration in `pyproject.toml`

## Debugging Tests

### Running Failed Tests

```bash
# Run only failed tests
pytest --lf

# Run with detailed output
pytest -v --tb=long

# Debug with pdb
pytest --pdb
```

### Test Isolation

Each test should be independent and not rely on side effects from other tests. Use fixtures for setup/teardown.

### Performance

- Keep unit tests fast (< 0.1s each)
- Mark slow tests with `@pytest.mark.slow`
- Use appropriate mocking to avoid slow operations

## Contributing

When adding new features:

1. Add corresponding unit tests
2. Add functional tests for component interactions
3. Add integration tests for complete workflows
4. Update this documentation
5. Ensure all tests pass with `pytest`
6. Maintain or improve code coverage

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure PYTHONPATH includes src directory
2. **Fixture Errors**: Check conftest.py for fixture definitions
3. **Mocking Issues**: Verify mock targets and return values
4. **Coverage Issues**: Check source paths in pyproject.toml

### Getting Help

- Check existing test examples
- Review pytest documentation
- Examine conftest.py for available fixtures
- Run tests with `-v` for detailed output