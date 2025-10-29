# Usage Examples

This guide provides practical examples of using ComfyFixerSmart in various scenarios. Each example includes the command, expected output, and explanation.

## Basic Usage Examples

### Example 1: Analyze All Workflows

**Scenario:** You have a ComfyUI installation with multiple workflows and want to find all missing models.

**Command:**
```bash
comfyfixer
```

**Expected Output:**
```
ComfyFixerSmart v2.0 - Incremental Model Downloader
==================================================

Configuration loaded from: config/default.toml
ComfyUI root: /home/user/ComfyUI-stable
Scanning workflows in: user/default/workflows/

Found 5 workflow files
Analyzing workflows...
[1/5] workflow1.json - 3 models (2 missing)
[2/5] workflow2.json - 7 models (1 missing)
[3/5] workflow3.json - 12 models (4 missing)
[4/5] workflow4.json - 5 models (0 missing)
[5/5] workflow5.json - 8 models (2 missing)

Analysis Summary:
- Total workflows: 5
- Total models referenced: 35
- Models available locally: 26
- Missing models: 9

Missing Models:
1. realisticVisionV51_v51VAE.safetensors (checkpoint)
2. detailTweakerXL.safetensors (lora)
3. sdxl_vae_fp16_fix.safetensors (vae)
... (6 more)

Generating download script...
✓ Created: output/download_missing.sh
✓ Created: output/analysis_report.md

Run 'bash output/download_missing.sh' to download missing models.
```

### Example 2: Analyze Specific Workflow

**Scenario:** You want to check a specific workflow file for missing models.

**Command:**
```bash
comfyfixer my_workflow.json
```

**Expected Output:**
```
Analyzing workflow: my_workflow.json

Workflow Analysis:
- File: my_workflow.json
- Nodes: 45
- Model references: 8

Missing Models:
1. epicRealismXL.safetensors
   - Type: checkpoint
   - Expected location: models/checkpoints/
   - Used in: CheckpointLoaderSimple (#12)

Available Models:
- 7 models found locally

Search Results:
Searching Civitai for "epicRealismXL"...
✓ Found: Epic Realism XL (ID: 123456)
  Version: v1.0 (4.2GB)
  Download URL: https://civitai.com/api/download/models/123456

Generated download script: output/download_my_workflow.sh
```

### Example 3: Custom Directory Scan

**Scenario:** Your workflows are in a custom directory structure.

**Command:**
```bash
comfyfixer --dir /path/to/custom/workflows --dir /another/workflow/dir
```

**Configuration:**
```toml
# config/default.toml
workflow_dirs = [
    "custom/workflows",
    "community/workflows"
]
```

## Advanced Examples

### Example 4: Multi-Backend Search

**Scenario:** You want to search both Civitai and HuggingFace for missing models.

**Command:**
```bash
comfyfixer --search civitai,huggingface
```

**Expected Output:**
```
Using search backends: civitai, huggingface

[1/3] Processing: model1.safetensors
  Searching Civitai... ✓ Found
  Downloading from Civitai...

[2/3] Processing: model2.safetensors
  Searching Civitai... ✗ Not found
  Searching HuggingFace... ✓ Found
  Downloading from HuggingFace...

[3/3] Processing: model3.safetensors
  Searching Civitai... ✓ Found (better match)
  Skipping HuggingFace search...
```

### Example 5: Batch Processing with Custom Output

**Scenario:** Process multiple workflows with custom output directory and logging.

**Command:**
```bash
comfyfixer --dir workflows/ --output-dir results/ --log-level DEBUG --log-file results/debug.log
```

**Expected Output:**
```
2025-10-12 14:30:00 DEBUG Loading configuration...
2025-10-12 14:30:00 INFO Found 12 workflow files
2025-10-12 14:30:01 INFO Analyzing workflows...
2025-10-12 14:30:05 INFO Missing models: 8
2025-10-12 14:30:05 INFO Searching Civitai...
2025-10-12 14:30:15 INFO Found 7/8 models
2025-10-12 14:30:15 INFO Generating reports...
2025-10-12 14:30:16 INFO Download script created: results/download_missing.sh
```

### Example 6: Incremental Download Mode

**Scenario:** Use the new v2.0 incremental download mode for better reliability.

**Command:**
```bash
comfyfixer --v2
```

**Expected Output:**
```
ComfyFixerSmart v2.0 - Incremental Mode
=======================================

[1/15] Processing: rife49.pth
  Launching Qwen search...
  ✓ Found on HuggingFace: AlexWortega/RIFE
  Generated: download_001_rife49_pth.sh
  Executing download: download_001_rife49_pth.sh
  ✓ Download completed successfully

[2/15] Processing: sam_vit_b_01ec64.pth
  Searching Civitai...
  ✓ Found: SAM ViT B (ID: 123456)
  Generated: download_002_sam_vit_b.sh
  Executing download...
  ✓ Download completed successfully

[6/15] Processing: model006.pth
  ✓ Download completed successfully

===========================================================
Verifying last 6 downloads with Qwen
===========================================================
  ✓ Verified: 6 models (all files present and correct size)

[7/15] Processing: next_model.pth
  ...
```

## Configuration Examples

### Example 7: Basic Configuration

**File:** `config/default.toml`
```toml
# ComfyUI Installation
comfyui_root = "/home/user/ComfyUI-stable"

# Workflow Scanning
workflow_dirs = [
    "user/default/workflows"
]

# Search Configuration
search_backends = ["civitai"]
civitai_api_timeout = 30

# Download Configuration
download_concurrency = 3
download_timeout = 300
verify_downloads = true

# Output
output_dir = "output"
log_level = "INFO"
```

### Example 8: Advanced Configuration

**File:** `config/production.toml`
```toml
# Production configuration with optimizations
comfyui_root = "/opt/comfyui"
workflow_dirs = [
    "user/default/workflows",
    "user/custom/workflows",
    "community/workflows"
]

# Multi-backend search
search_backends = ["civitai", "huggingface"]
civitai_api_timeout = 60
huggingface_timeout = 30

# High-performance downloads
download_concurrency = 5
download_timeout = 600
download_retries = 5
verify_downloads = true

# Caching for performance
cache_enabled = true
cache_ttl_hours = 48
cache_max_size_mb = 500

# Detailed logging
log_level = "WARNING"
log_file = "logs/comfyfixer.log"
log_max_size_mb = 100
log_backup_count = 10

# Output organization
output_dir = "output"
reports_dir = "reports"
scripts_dir = "scripts"
```

## Workflow-Specific Examples

### Example 9: SDXL Workflow Analysis

**Scenario:** Analyze an SDXL workflow with specific model requirements.

**Workflow excerpt:**
```json
{
  "nodes": {
    "12": {
      "type": "CheckpointLoaderSimple",
      "widgets_values": ["sdxl_base_1.0.safetensors"]
    },
    "15": {
      "type": "LoraLoader",
      "widgets_values": ["sdxl_detailTweaker.safetensors", 1.0]
    }
  }
}
```

**Command:**
```bash
comfyfixer sdxl_workflow.json
```

**Expected Output:**
```
Analyzing SDXL workflow: sdxl_workflow.json

Missing Models:
1. sdxl_base_1.0.safetensors (checkpoint)
   - Expected: models/checkpoints/
   - Found on Civitai: SDXL Base v1.0

2. sdxl_detailTweaker.safetensors (lora)
   - Expected: models/loras/
   - Found on Civitai: SDXL Detail Tweaker

Generated optimized download script for SDXL models.
```

### Example 10: ControlNet Workflow

**Scenario:** Workflow using multiple ControlNet models.

**Command:**
```bash
comfyfixer controlnet_workflow.json --concurrency 2
```

**Expected Output:**
```
ControlNet workflow analysis:

Missing ControlNet models:
1. control_v11p_sd15_canny.pth
2. control_v11p_sd15_depth.pth
3. control_v11p_sd15_normal.pth

All models found on Civitai.
Downloading with reduced concurrency to manage memory...
```

## Automation Examples

### Example 11: Cron Job for Regular Checks

**Scenario:** Set up automated workflow checking.

**Cron configuration:**
```bash
# Check workflows daily at 2 AM
0 2 * * * cd /path/to/ComfyFixerSmart && /usr/bin/comfyfixer --quiet --output-dir automated/
```

**Script wrapper:**
```bash
#!/bin/bash
# daily_workflow_check.sh
cd /path/to/ComfyFixerSmart
source ~/.secrets  # Load API keys

# Run analysis
comfyfixer --quiet --output-dir automated/

# Check if any models are missing
if [ -f "automated/download_missing.sh" ]; then
    echo "Missing models found. Run: bash automated/download_missing.sh"
    # Send notification
    notify-send "ComfyFixerSmart" "Missing models detected"
fi
```

### Example 12: CI/CD Integration

**Scenario:** Integrate ComfyFixerSmart into a CI/CD pipeline.

**GitHub Actions workflow:**
```yaml
name: Check Workflows
on: [push, pull_request]

jobs:
  check-workflows:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: pip install -e .
    - name: Check workflows
      env:
        CIVITAI_API_KEY: ${{ secrets.CIVITAI_API_KEY }}
        COMFYUI_ROOT: /tmp/comfyui
      run: |
        mkdir -p /tmp/comfyui/user/default/workflows
        cp workflows/*.json /tmp/comfyui/user/default/workflows/
        comfyfixer --validate-config
        comfyfixer --dry-run
```

## Troubleshooting Examples

### Example 13: Debug Problematic Workflow

**Scenario:** Debug a workflow that's causing parsing errors.

**Command:**
```bash
comfyfixer problematic_workflow.json --log-level DEBUG --verbose
```

**Expected Output:**
```
DEBUG: Loading workflow: problematic_workflow.json
DEBUG: Parsing JSON... ✓ Valid JSON
DEBUG: Extracting nodes... Found 45 nodes
DEBUG: Processing node 12 (CheckpointLoaderSimple)...
DEBUG: Model reference: checkpoint.safetensors
DEBUG: Checking local inventory...
WARNING: Model not found locally: checkpoint.safetensors
DEBUG: Searching Civitai with query: checkpoint
DEBUG: API response: 200 OK
DEBUG: Found 1 match
...
```

### Example 14: Memory-Constrained Environment

**Scenario:** Run on a system with limited memory.

**Command:**
```bash
comfyfixer --concurrency 1 --cache-enabled false --log-level WARNING
```

**Configuration:**
```toml
# Low-memory configuration
download_concurrency = 1
cache_enabled = false
log_level = "WARNING"

# Reduce memory usage
max_workers = 1
memory_limit_mb = 256
```

### Example 15: Offline Mode

**Scenario:** Work with cached results when offline.

**Command:**
```bash
comfyfixer --cache-only --no-download
```

**Expected Output:**
```
Offline mode: Using cached results only

Analysis Results (from cache):
- Missing models: 3 (cached from last run)
- Available downloads: 2 (cached URLs still valid)

Note: Run without --cache-only to refresh search results.
```

## Advanced Scripting Examples

### Example 16: Custom Report Generation

**Scenario:** Generate custom reports for integration with other tools.

**Script:**
```bash
#!/bin/bash
# custom_report.sh

# Run analysis
comfyfixer --output-dir reports/

# Generate JSON report for API integration
python -c "
import json
with open('reports/missing_models.json') as f:
    data = json.load(f)
print(f'Missing models: {len(data)}')
for model in data:
    print(f'- {model[\"filename\"]} ({model[\"type\"]})')
"
```

### Example 17: Model Validation Script

**Scenario:** Validate that downloaded models work correctly.

**Script:**
```bash
#!/bin/bash
# validate_models.sh

echo "Validating downloaded models..."

# Check file sizes
for model in $(cat downloaded_models.json | jq -r '.models[].path'); do
    if [ -f "$model" ]; then
        size=$(stat -f%z "$model" 2>/dev/null || stat -c%s "$model")
        echo "✓ $model: $(($size / 1024 / 1024))MB"
    else
        echo "✗ Missing: $model"
    fi
done

echo "Validation complete."
```

These examples demonstrate the flexibility and power of ComfyFixerSmart for various use cases, from simple one-off checks to complex automation scenarios.