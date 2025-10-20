import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict

import pytest

from comfyfixersmart.inspector import inspect_file, inspect_paths


def _create_dummy_file(path: Path, content: bytes = b"data") -> None:
    path.write_bytes(content)


def _write_safetensors(path: Path, metadata: Dict[str, str]) -> None:
    safetensors = pytest.importorskip("safetensors")
    try:
        from safetensors import numpy as safenp  # type: ignore[attr-defined]
    except Exception:
        safenp = None

    if safenp is not None:
        numpy = pytest.importorskip("numpy")
        data = {"weights": numpy.zeros((1,), dtype=numpy.float32)}
        safenp.save_file(data, str(path), metadata=metadata)
        return

    torch = pytest.importorskip("torch")
    from safetensors import torch as safetorch  # type: ignore[attr-defined]

    tensor = torch.zeros(1)
    safetorch.save_file({"weights": tensor}, str(path), metadata=metadata)


def _pythonpath_env() -> Dict[str, str]:
    env = os.environ.copy()
    root = Path(__file__).resolve().parents[2] / "src"
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = f"{root}{os.pathsep}{existing}" if existing else str(root)
    return env


def test_inspect_file_safetensors_metadata(tmp_path):
    metadata = {"ss_network_module": "lora"}

    output_file = tmp_path / "tiny_lora.safetensors"
    _write_safetensors(output_file, metadata)

    info = inspect_file(str(output_file))

    assert info["format"] == "safetensors"
    assert info["metadata"]["ss_network_module"] == "lora"
    assert info["type_hint"] == "lora"
    assert info["warnings"] == []


def test_inspect_file_flux_family(tmp_path):
    metadata = {"modelspec.architecture": "flux", "format": "checkpoint"}

    output_file = tmp_path / "flux_model.safetensors"
    _write_safetensors(output_file, metadata)

    info = inspect_file(str(output_file))

    assert info["family"] == "flux"
    assert info["type_hint"] == "checkpoint"


def test_inspect_pickle_safe_mode(tmp_path):
    file_path = tmp_path / "model.pth"
    _create_dummy_file(file_path)

    info = inspect_file(str(file_path))

    assert info["format"] == "pth"
    assert info["metadata"]["unsafe"] == "disabled"
    assert any("Unsafe" in warning for warning in info["warnings"])


def test_inspect_pickle_unsafe(tmp_path):
    torch = pytest.importorskip("torch", reason="torch required for unsafe test")

    file_path = tmp_path / "state_dict.ckpt"
    tensor = torch.zeros(1)
    torch.save({"layer.weight": tensor}, file_path)

    info = inspect_file(str(file_path), unsafe=True)

    metadata = info["metadata"]["unsafe_top_level"]
    assert metadata["type"] in {"dict", "OrderedDict"}
    assert metadata["key_count"] == 1
    assert metadata["sample_keys"] == ["layer.weight"]


def test_inspect_file_hashing(tmp_path):
    file_path = tmp_path / "model.bin"
    _create_dummy_file(file_path, b"hash-me")

    info = inspect_file(str(file_path), do_hash=True)

    assert info["format"] == "bin"
    assert info["sha256"] is not None
    assert len(info["sha256"]) == 64


def test_inspect_onnx_metadata(tmp_path):
    onnx = pytest.importorskip("onnx")

    from onnx import helper, TensorProto

    node = helper.make_node("Relu", inputs=["X"], outputs=["Y"])
    graph = helper.make_graph(
        [node],
        "TestGraph",
        [helper.make_tensor_value_info("X", TensorProto.FLOAT, [1])],
        [helper.make_tensor_value_info("Y", TensorProto.FLOAT, [1])],
    )
    model = helper.make_model(graph, producer_name="pytest")

    file_path = tmp_path / "model.onnx"
    onnx.save(model, file_path)

    info = inspect_file(str(file_path))

    assert info["format"] == "onnx"
    assert "ir_version" in info["metadata"]
    assert info["warnings"] == []


def test_inspect_onnx_missing_dependency(tmp_path, monkeypatch):
    file_path = tmp_path / "missing.onnx"
    _create_dummy_file(file_path)

    original_import_module = importlib.import_module

    def fake_import(name):
        if name == "onnx":
            raise ImportError("onnx unavailable")
        return original_import_module(name)

    monkeypatch.setattr(importlib, "import_module", fake_import)

    info = inspect_file(str(file_path))

    assert info["format"] == "onnx"
    assert "onnx not installed" in info["warnings"][0]


def test_inspect_paths_directory_recursive(tmp_path):
    (tmp_path / "sub").mkdir()
    file_a = tmp_path / "sub" / "b_model.safetensors"
    file_b = tmp_path / "sub" / "a_model.bin"
    _create_dummy_file(file_a)
    _create_dummy_file(file_b)

    results = inspect_paths([str(tmp_path)], recursive=True, fmt="json")

    filenames = [entry["filename"] for entry in results]
    assert filenames == sorted(filenames)


def test_diffusers_directory_summary(tmp_path):
    repo = tmp_path / "diff_repo"
    (repo / "unet").mkdir(parents=True)
    (repo / "text_encoder").mkdir()

    model_index = {
        "_class_name": "StableDiffusionPipeline",
        "_diffusers_version": "0.20.0",
    }
    (repo / "model_index.json").write_text(json.dumps(model_index), encoding="utf-8")
    (repo / "unet" / "diffusion_pytorch_model.bin").write_bytes(b"123")
    (repo / "text_encoder" / "model.safetensors").write_bytes(b"456")

    info = inspect_file(str(repo))
    assert info["format"] == "diffusers"
    assert "pipeline_class" in info["metadata"]
    component_names = {item["name"] for item in info["metadata"]["files"]}
    assert {
        "model_index.json",
        "text_encoder/model.safetensors",
        "unet/diffusion_pytorch_model.bin",
    }.issubset(component_names)

    results = inspect_paths([str(repo)], fmt="json", include_components=False)
    assert isinstance(results, list)
    assert "files" not in results[0]["metadata"]


def test_type_hint_from_directory(tmp_path):
    target_dir = tmp_path / "loras"
    target_dir.mkdir()
    file_path = target_dir / "style.safetensors"
    _create_dummy_file(file_path)

    info = inspect_file(str(file_path))
    assert info["type_hint"] == "lora"


def test_source_hints_from_path(tmp_path):
    file_path = tmp_path / "models" / "huggingface" / "adapter.bin"
    file_path.parent.mkdir(parents=True)
    _create_dummy_file(file_path)

    info = inspect_file(str(file_path))
    assert "huggingface" in info["source_hints"]


def test_text_output_with_metadata_and_hash(tmp_path):
    file_path = tmp_path / "model.ckpt"
    _create_dummy_file(file_path, b"text-output")

    text_output = inspect_paths(
        [str(file_path)],
        fmt="text",
        summary=False,
        do_hash=True,
    )

    assert "metadata:" in text_output
    assert "sha256:" in text_output
    assert "warnings:" in text_output


def test_cli_inspect_text_single_file(tmp_path):
    file_path = tmp_path / "model.bin"
    _create_dummy_file(file_path)

    proc = subprocess.run(
        [sys.executable, "-m", "comfyfixersmart.cli", "inspect", str(file_path)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_pythonpath_env(),
    )

    assert "model.bin" in proc.stdout


def test_cli_inspect_json_single_file(tmp_path):
    file_path = tmp_path / "model.safetensors"
    _create_dummy_file(file_path)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "comfyfixersmart.cli",
            "inspect",
            str(file_path),
            "--format",
            "json",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_pythonpath_env(),
    )

    payload = json.loads(proc.stdout.strip())
    assert payload["filename"] == "model.safetensors"
    assert payload["format"] == "safetensors"


def test_cli_inspector_module_no_summary(tmp_path):
    file_path = tmp_path / "model.ckpt"
    _create_dummy_file(file_path)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "comfyfixersmart.inspector.cli",
            str(file_path),
            "--no-summary",
            "--hash",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_pythonpath_env(),
    )

    assert "metadata:" in proc.stdout
    assert "sha256:" in proc.stdout
