"""
Shared pytest fixtures for ComfyWatchman test suite.

Note: ComfyUI workflows use a node-list format where each node has
'id', 'type', 'widgets_values', and 'inputs' fields.
"""
import json

import pytest


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
    f.write_text(json.dumps(simple_workflow), encoding="utf-8")
    return f


@pytest.fixture
def complex_workflow_file(tmp_path, complex_workflow):
    """Write the complex workflow to a temporary JSON file on disk."""
    f = tmp_path / "complex_workflow.json"
    f.write_text(json.dumps(complex_workflow), encoding="utf-8")
    return f


@pytest.fixture
def empty_workflow_file(tmp_path, empty_workflow):
    """Write the empty workflow to a temporary JSON file on disk."""
    f = tmp_path / "empty_workflow.json"
    f.write_text(json.dumps(empty_workflow), encoding="utf-8")
    return f
