# Project Context for Gemini CLI

## Project Overview

This project, named "ComfyWatchman," is a Python library designed to be used by AI agents for managing ComfyUI workflows. Its primary functions include analyzing workflows to identify missing models, searching for these models across various sources like Civitai and HuggingFace, and automating the download process. The main source code for the project is located in the `src/comfywatchman` directory.

## Building and Running

### Installation

To install the project and its dependencies for development, run the following command from the root directory:

```bash
pip install -e .
```

### Running the Application

The project provides a command-line interface. To run it, use the following command:

```bash
python3 -m comfywatchman.cli [ARGUMENTS]
```

There is also a legacy script available, but the modern way to run the tool is via the Python module.

### Running Tests

The project uses `pytest` for testing. To run the test suite, execute:

```bash
pytest
```

## Development Conventions

*   **Linting and Formatting:** The project uses `ruff` for both linting and code formatting.
*   **Type Checking:** `mypy` is used for static type checking.
*   **Dependencies:** Project dependencies are managed in `pyproject.toml` and can be installed with `pip`.
*   **Packaging:** The project is packaged using `setuptools`.
