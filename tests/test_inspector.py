import json
from pathlib import Path

import pytest

from comfyfixersmart.inspector import inspect_file, results_to_json


def test_inspect_missing_file(tmp_path: Path):
    p = tmp_path / "nope.safetensors"
    res = inspect_file(p)
    assert res.error is not None
    assert res.safe_to_load is False
    assert res.format == "missing"


def test_inspect_safetensors_header():
    # Use the small test safetensors present in repo root if available
    p = Path("test_direct_download.safetensors")
    if not p.exists():
        pytest.skip("sample safetensors not available in workspace")
    res = inspect_file(p)
    # Reading headers is safe even if no tensors are present
    assert res.format == "safetensors"
    assert res.safe_to_load is True
    # JSON serialization shouldn't crash
    _ = json.loads(results_to_json([res]))


def test_inspect_pth_is_unsafe(tmp_path: Path):
    p = tmp_path / "model.pth"
    p.write_bytes(b"not really a model")
    res = inspect_file(p)
    assert res.safe_to_load is False
    assert res.format == "pytorch"
