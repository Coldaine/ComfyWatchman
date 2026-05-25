"""
Shared pytest fixtures for ComfyWatchman test suite.

Note: ComfyUI workflows use a node-list format where each node has
'id', 'type', 'widgets_values', and 'inputs' fields.
"""
import logging
import os
import sys
import tempfile
from pathlib import Path

import pytest

_ORIG_CWD = None
_SESSION_TMPDIR = None
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"


def pytest_sessionstart(session):
    """Isolate import-time Config directory creation from the checkout."""
    global _ORIG_CWD, _SESSION_TMPDIR

    _ORIG_CWD = os.getcwd()
    for path in (_REPO_ROOT, _SRC_ROOT):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)

    _SESSION_TMPDIR = tempfile.TemporaryDirectory()
    os.chdir(_SESSION_TMPDIR.name)

    for env_var in ("OUTPUT_DIR", "LOG_DIR", "TEMP_DIR"):
        os.environ.setdefault(env_var, _SESSION_TMPDIR.name)


def pytest_sessionfinish(session, exitstatus):
    """Restore the original working directory after the test session."""
    global _ORIG_CWD, _SESSION_TMPDIR

    for logger_obj in logging.Logger.manager.loggerDict.values():
        if not isinstance(logger_obj, logging.Logger):
            continue
        for handler in list(logger_obj.handlers):
            handler.close()
            logger_obj.removeHandler(handler)

    if _ORIG_CWD is not None:
        os.chdir(_ORIG_CWD)
        _ORIG_CWD = None

    if _SESSION_TMPDIR is not None:
        _SESSION_TMPDIR.cleanup()
        _SESSION_TMPDIR = None


def write_workflow_json(path, workflow):
    import json

    path.write_text(json.dumps(workflow), encoding="utf-8")
    return path


@pytest.fixture
def simple_workflow():
    """Minimal valid ComfyUI workflow with one checkpoint loader node."""
    return {
        "nodes": [
            {
                "id": 1,
                "type": "CheckpointLoaderSimple",
                "widgets_values": ["dreamshaper_8.safetensors"],
                "inputs": {},
            },
            {
                "id": 2,
                "type": "KSampler",
                "widgets_values": [42, "euler", "normal", 7.0, 20, "fixed"],
                "inputs": {"model": [1, 0], "positive": [3, 0]},
            },
        ]
    }


@pytest.fixture
def complex_workflow():
    """Workflow with multiple model types: checkpoint, LoRA, and ControlNet."""
    return {
        "nodes": [
            {
                "id": 1,
                "type": "CheckpointLoaderSimple",
                "widgets_values": ["realistic_vision_v6.safetensors"],
                "inputs": {},
            },
            {
                "id": 2,
                "type": "LoraLoader",
                "widgets_values": ["detail_tweaker.safetensors", 0.8, 0.8],
                "inputs": {"model": [1, 0]},
            },
            {
                "id": 3,
                "type": "ControlNetLoader",
                "widgets_values": ["control_v11p_sd15_canny.pth"],
                "inputs": {},
            },
            {
                "id": 4,
                "type": "KSampler",
                "widgets_values": [42, "euler", "normal", 7.0, 20, "fixed"],
                "inputs": {},
            },
        ]
    }


@pytest.fixture
def empty_workflow():
    """Workflow with no model loader nodes — only text encoding and sampling."""
    return {
        "nodes": [
            {
                "id": 1,
                "type": "CLIPTextEncode",
                "widgets_values": ["a cat sitting on a bench"],
                "inputs": {"clip": [2, 0]},
            },
            {
                "id": 2,
                "type": "KSampler",
                "widgets_values": [42, "euler", "normal", 7.0, 20, "fixed"],
                "inputs": {},
            },
        ]
    }


@pytest.fixture
def embedding_workflow():
    """Workflow that references embeddings via 'embedding:name' tokens in prompt text."""
    return {
        "nodes": [
            {
                "id": 1,
                "type": "CLIPTextEncode",
                "widgets_values": ["a photo of embedding:BadDream style"],
                "inputs": {},
            },
            {
                "id": 2,
                "type": "CLIPTextEncode",
                "widgets_values": ["embedding:EasyNegative ugly"],
                "inputs": {},
            },
        ]
    }


@pytest.fixture
def workflow_file(tmp_path, simple_workflow):
    """Write the simple workflow to a temporary JSON file on disk."""
    f = tmp_path / "test_workflow.json"
    return write_workflow_json(f, simple_workflow)


@pytest.fixture
def complex_workflow_file(tmp_path, complex_workflow):
    """Write the complex workflow to a temporary JSON file on disk."""
    f = tmp_path / "complex_workflow.json"
    return write_workflow_json(f, complex_workflow)


@pytest.fixture
def empty_workflow_file(tmp_path, empty_workflow):
    """Write the empty workflow to a temporary JSON file on disk."""
    f = tmp_path / "empty_workflow.json"
    return write_workflow_json(f, empty_workflow)
