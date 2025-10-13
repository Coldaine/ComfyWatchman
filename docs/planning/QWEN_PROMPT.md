# Instructions for Qwen: ComfyFixerSmart Toolkit

## Overview

ComfyFixerSmart provides multiple tools for managing ComfyUI workflows and models:

1. **comfy_fixer.py** - Main tool to find missing models and generate download scripts
2. **ScanTool/** - Advanced model management utilities:
   - **comfyui_model_scanner.py** - Scans and indexes all ComfyUI models with metadata
   - **sort_models.py** - Organizes scanned models by type
   - **workflow_validator.py** - Validates workflows against model inventory

## Option 1: Quick Workflow Analysis (Original Tool)

```bash
cd /home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart

# Run the main script
python comfy_fixer.py
```

## What the Script Does

1. **Scans workflows** - Searches for all .json workflow files
2. **Extracts model references** - Parses workflows to find required models
3. **Generates missing list** - Compares against local models directory
4. **Searches Civitai API** - Finds each missing model on Civitai
5. **Generates download script** - Creates bash script with wget commands
6. **Logs everything** - All actions logged with timestamps

## Expected Output

You will see output like:
```
[2025-10-12 14:30:00] ============================================================
[2025-10-12 14:30:00] ComfyFixerSmart - Starting
[2025-10-12 14:30:00] ============================================================
[2025-10-12 14:30:01] === STEP 1: Scanning workflows ===
[2025-10-12 14:30:01]   Scanning: /home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/user/default/workflows
[2025-10-12 14:30:02]   Found 15 workflows
[2025-10-12 14:30:02] Total workflows found: 15
[2025-10-12 14:30:03] Building local model inventory...
[2025-10-12 14:30:05]   Found 234 local models
[2025-10-12 14:30:05] === STEP 3: Generating missing list ===
[2025-10-12 14:30:06]   Analyzing: workflow1.json
[2025-10-12 14:30:07]   ⚠️  Missing: hunyuan_8itchw4lk_2_40.safetensors (loras)
[2025-10-12 14:30:08] Total missing models: 5
[2025-10-12 14:30:09] === STEP 5: Searching Civitai ===
[2025-10-12 14:30:10]   Searching Civitai: hunyuan 8itchw4lk 2 40
[2025-10-12 14:30:12]     ✓ Found: Move Enhancer (ID: 1186768)
[2025-10-12 14:30:15] Resolved: 4/5
[2025-10-12 14:30:16] === STEP 4: Generating download script ===
[2025-10-12 14:30:16] Download script saved: output/download_missing.sh
[2025-10-12 14:30:16] ============================================================
[2025-10-12 14:30:16] ✓ Analysis complete!
[2025-10-12 14:30:16] ============================================================
```

## Output Files Generated

After running, check these files:

1. **output/missing_models.json** - List of missing models
2. **output/resolutions.json** - Civitai search results
3. **output/download_missing.sh** - Executable download script
4. **log/run_YYYYMMDD_HHMMSS.log** - Complete execution log

---

## Option 2: Advanced Model Inventory & Validation (ScanTool)

### Step 1: Scan All Models

```bash
cd /home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart

# Scan ComfyUI models directory and generate inventory
python3 ScanTool/comfyui_model_scanner.py \
  --dir /home/coldaine/StableDiffusionWorkflow/ComfyUI-stable \
  --output ScanTool/scan_results_sorted.json \
  -v

# Optional: Add --hashes flag to compute SHA256 hashes (slower)
```

**What it does:**
- Scans all model directories recursively
- Extracts metadata from .safetensors files
- Detects model types (checkpoint, lora, vae, controlnet)
- Outputs JSON with model information
- Found: **142 models** across 80 loras, 32 checkpoints, 8 VAEs, etc.

**Output:** `ScanTool/scan_results_sorted.json`

### Step 2: Organize Models by Type

```bash
cd /home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart/ScanTool

# Sort and categorize models
python3 sort_models.py
```

**What it does:**
- Groups models by type (checkpoint, lora, vae, etc.)
- Creates summary with model counts
- Sorts models alphabetically within each category
- Shows file sizes and locations

**Output:** `ScanTool/models_organized.json`

**Example summary:**
```
=== Model Scan Summary ===
Total models found: 142

Breakdown by type:
  lora: 80
  checkpoint: 32
  ckpt_or_pt_unsafe: 13
  unknown: 9
  vae: 8
```

### Step 3: Validate Workflows

```bash
cd /home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart/ScanTool

# Validate all workflows against model inventory
python3 workflow_validator.py
```

**What it does:**
- Checks all workflows for missing models
- Validates model types match node types (e.g., LoRA nodes use LoRA files)
- Detects misplaced models (wrong directory for type)
- Generates detailed validation report

**Output:** `workflow_validation_report.md`

**Example findings:**
- Identifies missing SAM2 models
- Finds upscale models not in scan
- Detects checkpoint mismatches
- Reports 12 workflows analyzed with specific issues

### ScanTool Benefits

✅ **Complete inventory** - Know exactly what models you have
✅ **Type detection** - Automatically classify models by purpose
✅ **Workflow validation** - Find missing/misplaced models before running
✅ **Metadata extraction** - See model info without loading files
✅ **Duplicate detection** - Find same models in multiple locations

## Next Steps After Script Completes

1. **Review the results:**
   ```bash
   cat output/resolutions.json
   ```

2. **Execute the download script:**
   ```bash
   bash output/download_missing.sh
   ```

3. **Verify downloads:**
   ```bash
   ls -lh /home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/models/loras/
   ls -lh /home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/models/checkpoints/
   ```

## Prerequisites

- Python 3.7+ installed
- `requests` library installed (if not: `pip install requests`)
- `CIVITAI_API_KEY` set in ~/.secrets
- Internet connection for Civitai API

## Troubleshooting

**If you see "CIVITAI_API_KEY not found":**
```bash
# Check if key exists
grep CIVITAI_API_KEY ~/.secrets

# If missing, it needs to be added to ~/.secrets
# Format: export CIVITAI_API_KEY="your_key_here"
```

**If the script fails:**
- Check the log file in `log/` directory
- Look for ERROR messages with timestamps
- Report the error message from the log

## Success Criteria

✓ Script runs without errors
✓ Output files created in `output/` directory
✓ Download script generated: `output/download_missing.sh`
✓ Log file created with timestamps: `log/run_*.log`

## Report Back

### For Option 1 (comfy_fixer.py):

After execution, provide:
1. Number of workflows scanned
2. Number of missing models found
3. Number of models resolved on Civitai
4. Path to download script
5. Any errors encountered

Example report:
```
ComfyFixerSmart Execution Report (Option 1):
- Workflows scanned: 15
- Missing models: 5
- Found on Civitai: 4/5
- Download script: output/download_missing.sh
- Log file: log/run_20251012_143000.log
- Status: SUCCESS
```

### For Option 2 (ScanTool):

After execution, provide:
1. Total models scanned
2. Models by type breakdown
3. Number of workflows validated
4. Number of missing models identified
5. Number of misplaced models
6. Path to validation report

Example report:
```
ScanTool Execution Report (Option 2):
- Total models scanned: 142
- Breakdown: 80 loras, 32 checkpoints, 8 VAEs, 13 ckpt/pt, 9 unknown
- Workflows validated: 12
- Missing models identified: 25+ across workflows
- Issues found: SAM2 models, upscale models, checkpoints
- Validation report: workflow_validation_report.md
- Model inventory: ScanTool/models_organized.json
- Status: SUCCESS
```
