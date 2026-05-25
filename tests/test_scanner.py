"""
Unit tests for WorkflowScanner (scanner.py).

The scanner uses the ComfyUI native node-list format:
    {"nodes": [{"id": ..., "type": ..., "widgets_values": [...], "inputs": {...}}]}

Model filenames are discovered by inspecting each node's widgets_values for
strings that end in recognised model extensions (.safetensors, .ckpt, .pt,
.bin, .pth).  Embedding references are extracted from text strings matching
the "embedding:<name>" pattern.
"""
def WorkflowScanner(*args, **kwargs):
    from comfywatchman.scanner import WorkflowScanner as _WorkflowScanner

    return _WorkflowScanner(*args, **kwargs)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_workflow(path, data):
    import json

    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


# ---------------------------------------------------------------------------
# Test: scan_workflows / _scan_specific_paths
# ---------------------------------------------------------------------------

class TestScanWorkflows:
    def test_scan_specific_valid_path(self, tmp_path, simple_workflow):
        """scan_workflows returns the path when it points to an existing JSON file."""
        f = tmp_path / "wf.json"
        _write_workflow(f, simple_workflow)
        scanner = WorkflowScanner()
        result = scanner.scan_workflows(specific_paths=[str(f)])
        assert str(f) in result

    def test_scan_specific_nonexistent_file_is_skipped(self, tmp_path):
        """Non-existent specific path is silently skipped."""
        scanner = WorkflowScanner()
        result = scanner.scan_workflows(specific_paths=[str(tmp_path / "ghost.json")])
        assert result == []

    def test_scan_specific_non_json_file_is_skipped(self, tmp_path):
        """A file that doesn't end in .json is excluded even if it exists."""
        f = tmp_path / "not_a_workflow.txt"
        f.write_text("{}", encoding="utf-8")
        scanner = WorkflowScanner()
        result = scanner.scan_workflows(specific_paths=[str(f)])
        assert result == []

    def test_scan_directory_returns_json_files(self, tmp_path, simple_workflow):
        """scan_workflows finds JSON files when given a directory."""
        _write_workflow(tmp_path / "a.json", simple_workflow)
        _write_workflow(tmp_path / "b.json", simple_workflow)
        scanner = WorkflowScanner()
        result = scanner.scan_workflows(workflow_dirs=[str(tmp_path)])
        assert len(result) == 2

    def test_scan_nonexistent_directory_returns_empty(self, tmp_path):
        """scan_workflows returns empty list for a directory that does not exist."""
        scanner = WorkflowScanner()
        result = scanner.scan_workflows(workflow_dirs=[str(tmp_path / "does_not_exist")])
        assert result == []


# ---------------------------------------------------------------------------
# Test: extract_models_from_workflow
# ---------------------------------------------------------------------------

class TestExtractModels:
    def test_checkpoint_model_extracted(self, tmp_path, simple_workflow):
        """A CheckpointLoaderSimple node yields one ModelReference."""
        path = _write_workflow(tmp_path / "wf.json", simple_workflow)
        scanner = WorkflowScanner()
        models = scanner.extract_models_from_workflow(path)
        assert len(models) == 1
        assert models[0].filename == "dreamshaper_8.safetensors"

    def test_checkpoint_type_is_checkpoints(self, tmp_path, simple_workflow):
        """Model type for CheckpointLoaderSimple is 'checkpoints'."""
        path = _write_workflow(tmp_path / "wf.json", simple_workflow)
        scanner = WorkflowScanner()
        models = scanner.extract_models_from_workflow(path)
        assert models[0].type == "checkpoints"

    def test_checkpoint_node_type_preserved(self, tmp_path, simple_workflow):
        """node_type on the ModelReference matches the source node's type field."""
        path = _write_workflow(tmp_path / "wf.json", simple_workflow)
        scanner = WorkflowScanner()
        models = scanner.extract_models_from_workflow(path)
        assert models[0].node_type == "CheckpointLoaderSimple"

    def test_lora_model_extracted(self, tmp_path, complex_workflow):
        """A LoraLoader node yields a ModelReference of type 'loras'."""
        path = _write_workflow(tmp_path / "wf.json", complex_workflow)
        scanner = WorkflowScanner()
        models = scanner.extract_models_from_workflow(path)
        loras = [m for m in models if m.node_type == "LoraLoader"]
        assert len(loras) == 1
        assert loras[0].filename == "detail_tweaker.safetensors"
        assert loras[0].type == "loras"

    def test_controlnet_model_extracted(self, tmp_path, complex_workflow):
        """A ControlNetLoader node yields a ModelReference of type 'controlnet'."""
        path = _write_workflow(tmp_path / "wf.json", complex_workflow)
        scanner = WorkflowScanner()
        models = scanner.extract_models_from_workflow(path)
        controlnets = [m for m in models if m.node_type == "ControlNetLoader"]
        assert len(controlnets) == 1
        assert controlnets[0].filename == "control_v11p_sd15_canny.pth"
        assert controlnets[0].type == "controlnet"

    def test_complex_workflow_yields_three_models(self, tmp_path, complex_workflow):
        """The complex workflow (checkpoint + lora + controlnet) yields exactly 3 models."""
        path = _write_workflow(tmp_path / "wf.json", complex_workflow)
        scanner = WorkflowScanner()
        models = scanner.extract_models_from_workflow(path)
        assert len(models) == 3

    def test_empty_workflow_yields_no_models(self, tmp_path, empty_workflow):
        """A workflow with no model-loader nodes yields an empty list."""
        path = _write_workflow(tmp_path / "wf.json", empty_workflow)
        scanner = WorkflowScanner()
        models = scanner.extract_models_from_workflow(path)
        assert models == []

    def test_path_prefixes_are_stripped_from_filename(self, tmp_path):
        """Model references that include directory prefixes are stripped to basename only."""
        workflow = {
            "nodes": [
                {
                    "id": 1,
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["subdir/v1-5-pruned.safetensors"],
                    "inputs": {},
                }
            ]
        }
        path = _write_workflow(tmp_path / "wf.json", workflow)
        scanner = WorkflowScanner()
        models = scanner.extract_models_from_workflow(path)
        assert models[0].filename == "v1-5-pruned.safetensors"

    def test_invalid_json_returns_empty_list(self, tmp_path):
        """Malformed JSON causes extract_models_from_workflow to return an empty list."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{not valid json", encoding="utf-8")
        scanner = WorkflowScanner()
        models = scanner.extract_models_from_workflow(str(bad_file))
        assert models == []

    def test_file_not_found_returns_empty_list(self, tmp_path):
        """Missing file returns an empty list (not an exception)."""
        scanner = WorkflowScanner()
        models = scanner.extract_models_from_workflow(str(tmp_path / "ghost.json"))
        assert models == []

    def test_non_model_extensions_ignored(self, tmp_path):
        """Strings with non-model extensions in widgets_values are not extracted."""
        workflow = {
            "nodes": [
                {
                    "id": 1,
                    "type": "CheckpointLoaderSimple",
                    "widgets_values": ["readme.txt", "config.yaml", 42, True],
                    "inputs": {},
                }
            ]
        }
        path = _write_workflow(tmp_path / "wf.json", workflow)
        scanner = WorkflowScanner()
        models = scanner.extract_models_from_workflow(path)
        assert models == []

    def test_return_node_count_flag(self, tmp_path, simple_workflow):
        """return_node_count=True returns a (models, count) tuple."""
        path = _write_workflow(tmp_path / "wf.json", simple_workflow)
        scanner = WorkflowScanner()
        result = scanner.extract_models_from_workflow(path, return_node_count=True)
        assert isinstance(result, tuple)
        models, count = result
        # simple_workflow has 2 nodes
        assert count == 2
        assert len(models) == 1

    def test_return_node_types_flag(self, tmp_path, complex_workflow):
        """return_node_types=True returns a (models, count, node_types) tuple."""
        path = _write_workflow(tmp_path / "wf.json", complex_workflow)
        scanner = WorkflowScanner()
        models, count, node_types = scanner.extract_models_from_workflow(
            path, return_node_types=True
        )
        assert "CheckpointLoaderSimple" in node_types
        assert "LoraLoader" in node_types
        assert "ControlNetLoader" in node_types

    def test_embedding_token_extracted_from_prompt(self, tmp_path, embedding_workflow):
        """embedding:<name> tokens in CLIPTextEncode prompts are extracted as embeddings type."""
        path = _write_workflow(tmp_path / "wf.json", embedding_workflow)
        scanner = WorkflowScanner()
        models = scanner.extract_models_from_workflow(path)
        embedding_types = [m for m in models if m.type == "embeddings"]
        assert [m.filename for m in embedding_types] == ["BadDream.pt", "EasyNegative.pt"]

    def test_duplicate_embedding_not_extracted_twice(self, tmp_path):
        """The same embedding referenced in two nodes is only extracted once."""
        workflow = {
            "nodes": [
                {
                    "id": 1,
                    "type": "CLIPTextEncode",
                    "widgets_values": ["embedding:MyEmbed positive"],
                    "inputs": {},
                },
                {
                    "id": 2,
                    "type": "CLIPTextEncode",
                    "widgets_values": ["embedding:MyEmbed negative"],
                    "inputs": {},
                },
            ]
        }
        path = _write_workflow(tmp_path / "wf.json", workflow)
        scanner = WorkflowScanner()
        models = scanner.extract_models_from_workflow(path)
        embedding_names = [m.filename for m in models if m.type == "embeddings"]
        assert embedding_names.count("MyEmbed.pt") == 1

    def test_model_reference_has_workflow_path(self, tmp_path, simple_workflow):
        """ModelReference.workflow_path matches the path passed to the scanner."""
        path = _write_workflow(tmp_path / "wf.json", simple_workflow)
        scanner = WorkflowScanner()
        models = scanner.extract_models_from_workflow(path)
        assert models[0].workflow_path == path

    def test_vae_loader_type_is_vae(self, tmp_path):
        """VAELoader nodes produce ModelReferences of type 'vae'."""
        workflow = {
            "nodes": [
                {
                    "id": 1,
                    "type": "VAELoader",
                    "widgets_values": ["vae-ft-mse-840000-ema-pruned.safetensors"],
                    "inputs": {},
                }
            ]
        }
        path = _write_workflow(tmp_path / "wf.json", workflow)
        scanner = WorkflowScanner()
        models = scanner.extract_models_from_workflow(path)
        assert len(models) == 1
        assert models[0].type == "vae"


# ---------------------------------------------------------------------------
# Test: validate_workflow
# ---------------------------------------------------------------------------

class TestValidateWorkflow:
    def test_valid_workflow_passes(self, tmp_path, simple_workflow):
        """A well-formed workflow reports is_valid=True with no errors."""
        path = _write_workflow(tmp_path / "wf.json", simple_workflow)
        scanner = WorkflowScanner()
        result = scanner.validate_workflow(path)
        assert result["is_valid"] is True
        assert result["errors"] == []

    def test_invalid_json_fails_validation(self, tmp_path):
        """Malformed JSON sets is_valid=False and populates errors."""
        bad = tmp_path / "bad.json"
        bad.write_text("{ broken json }", encoding="utf-8")
        scanner = WorkflowScanner()
        result = scanner.validate_workflow(str(bad))
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0

    def test_stats_include_node_and_model_count(self, tmp_path, simple_workflow):
        """validate_workflow stats dict includes node_count and model_count."""
        path = _write_workflow(tmp_path / "wf.json", simple_workflow)
        scanner = WorkflowScanner()
        result = scanner.validate_workflow(path)
        assert "node_count" in result["stats"]
        assert "model_count" in result["stats"]
        assert result["stats"]["node_count"] == 2
        assert result["stats"]["model_count"] == 1
