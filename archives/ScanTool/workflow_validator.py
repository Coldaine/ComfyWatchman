#!/usr/bin/env python3
import json
import os
from pathlib import Path
import re

def find_model_names(node):
    """Extracts model names from a workflow node."""
    model_names = []
    # Pattern to find model filenames
    model_pattern = re.compile(r'([\\/])([^\\/]+\.(?:safetensors|ckpt|pt))')

    # Check in 'inputs' which often contains the direct name
    if 'inputs' in node and isinstance(node['inputs'], dict):
        for key, value in node['inputs'].items():
            if isinstance(value, str) and any(ext in value for ext in ['.safetensors', '.ckpt', '.pt']):
                model_names.append(Path(value).name)

    # Check in 'widgets_values' which is a common place for filenames
    if 'widgets_values' in node and isinstance(node['widgets_values'], list):
        for value in node['widgets_values']:
            if isinstance(value, str):
                # Check for full paths or just filenames
                match = model_pattern.search(value)
                if match:
                    model_names.append(match.group(2))
                elif any(ext in value for ext in ['.safetensors', '.ckpt', '.pt']):
                    model_names.append(Path(value).name)
                    
    # Check in properties as a fallback
    if 'properties' in node and isinstance(node['properties'], dict):
        for key, value in node['properties'].items():
             if isinstance(value, str) and any(ext in value for ext in ['.safetensors', '.ckpt', '.pt']):
                model_names.append(Path(value).name)

    return list(set(model_names))


def main():
    """
    Validates ComfyUI workflows against a model inventory, checking for missing
    or misplaced models.
    """
    base_dir = Path('/home/coldaine/StableDiffusionWorkflow/')
    scan_tool_dir = Path('/home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart/ScanTool')
    workflows_dir = base_dir / 'ComfyUI-stable/user/default/workflows'
    models_file = scan_tool_dir / 'models_organized.json'
    report_file = Path('/home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart/workflow_validation_report.md')

    # 1. Load the model database
    try:
        with open(models_file, 'r') as f:
            model_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Could not load or parse {models_file}. Please run the scanner first.")
        print(e)
        return

    # Create a fast lookup map: { "model_name.safetensors": {"path": "...", "type_hint": "..."} }
    model_map = {}
    for model_type, models in model_data.get('models_by_type', {}).items():
        for model in models:
            model_name = Path(model['path']).name
            if model_name not in model_map:
                model_map[model_name] = model

    # 2. Define the mapping from ComfyUI node types to model types
    node_to_model_type = {
        'CheckpointLoaderSimple': 'checkpoint',
        'CheckpointLoader': 'checkpoint',
        'LoraLoader': 'lora',
        'VAELoader': 'vae',
        'ControlNetLoader': 'controlnet',
        'UpscaleModelLoader': 'upscale_models',
        'CLIPVisionLoader': 'clip_vision',
    }
    
    # Expected directory for each model type
    type_to_directory = {
        'checkpoint': 'checkpoints',
        'lora': 'loras',
        'vae': 'vae',
        'controlnet': 'controlnet',
        'upscale_models': 'upscale_models',
        'clip_vision': 'clip_vision',
        'embeddings': 'embeddings',
        'hypernetworks': 'hypernetworks',
        'gligen': 'gligen',
    }


    report_content = ["# Workflow Validation Report\n\n"]
    found_issues = False

    # 3. Find and iterate through workflows
    workflow_files = sorted(list(workflows_dir.glob('*.json')))
    print(f"Found {len(workflow_files)} workflows to analyze...")

    for wf_path in workflow_files:
        try:
            with open(wf_path, 'r', encoding='utf-8') as f:
                # Handle potential single-line dense JSON
                content = f.read()
                # Attempt to fix JSON if it's just a string literal
                if content.startswith('"') and content.endswith('"'):
                    content = content[1:-1].replace('\\"', '"').replace('\\\\', '\\')
                
                # More robustly find the start of the JSON object
                start_index = content.find('{')
                if start_index != -1:
                    content = content[start_index:]
                    
                wf_data = json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Could not read or parse workflow: {wf_path.name}")
            print(f"  Error: {e}")
            report_content.append(f"## Workflow: `{wf_path.name}`\n\n- **ERROR**: Could not parse this file. It may be corrupted or not a valid JSON workflow.\n\n")
            found_issues = True
            continue

        missing_models = []
        misplaced_models = []

        nodes = wf_data.get('nodes', [])
        if not nodes and isinstance(wf_data, list): # Handle older list-based format
             nodes = wf_data

        for node in nodes:
            node_type = node.get('type')
            model_names = find_model_names(node)

            for model_name in model_names:
                # Validation 1: Check if model exists
                if model_name not in model_map:
                    missing_models.append(f"- **{model_name}**: Used in a `{node_type}` node, but not found in your model scan.")
                    found_issues = True
                    continue

                # Validation 2: Check if model is in the right folder/used by the right node
                expected_model_type = node_to_model_type.get(node_type)
                if expected_model_type:
                    actual_model_record = model_map[model_name]
                    actual_model_type = actual_model_record.get('type_hint', 'unknown')
                    
                    # Check type hint first
                    if actual_model_type != 'unknown' and actual_model_type != expected_model_type:
                         misplaced_models.append(f"- **{model_name}**: This model is a **`{actual_model_type}`**, but it's being loaded by a **`{node_type}`** node, which expects a `{expected_model_type}`.")
                         found_issues = True
                    
                    # Also check the directory path
                    expected_dir = type_to_directory.get(expected_model_type)
                    if expected_dir and f'/{expected_dir}/' not in actual_model_record.get('path', ''):
                        misplaced_models.append(f"- **{model_name}**: This model is used as a `{expected_model_type}`, which should be in the **`{expected_dir}/`** directory, but it was found at `{actual_model_record.get('path')}`.")
                        found_issues = True


        if missing_models or misplaced_models:
            report_content.append(f"## Workflow: `{wf_path.name}`\n")
            if missing_models:
                report_content.append("### 🚨 Missing Models\n")
                report_content.extend(sorted(list(set(missing_models))))
                report_content.append("\n")
            if misplaced_models:
                report_content.append("### 📂 Misplaced or Mismatched Models\n")
                report_content.extend(sorted(list(set(misplaced_models))))
                report_content.append("\n")

    if not found_issues:
        report_content.append("✅ **Excellent! No missing or misplaced models were found in any of your workflows.**\n")

    final_report = "\n".join(report_content)
    
    # 4. Save and print the report
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(final_report)
        print(f"\nValidation complete. Report saved to: {report_file}")
    except IOError as e:
        print(f"Error writing report file: {e}")

    print("\n--- Validation Summary ---")
    print(final_report)


if __name__ == "__main__":
    main()
