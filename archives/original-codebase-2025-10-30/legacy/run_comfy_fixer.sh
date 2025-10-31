#!/bin/bash
# ComfyFixer - Automated workflow analysis and model downloader
# Uses Qwen agent to scan workflows, find missing models, and generate download scripts

set -e  # Exit on error

COMFYUI_ROOT="/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable"
WORKFLOW_DIR="/home/coldaine/StableDiffusionWorkflow"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load API keys
source ~/.secrets

# Create output directories
mkdir -p "$SCRIPT_DIR/output/reports"
mkdir -p "$SCRIPT_DIR/output/scripts"

# Run Qwen agent with the complete prompt
qwen --yolo --prompt "$(cat <<'PROMPT_END'
You are ComfyFixer, an automated workflow analysis agent. Your task is to scan ComfyUI workflows, identify missing models, search for them on Civitai, and generate download scripts.

## Task Overview:

1. **Scan all workflow files** in /home/coldaine/StableDiffusionWorkflow/ (look for *.json files recursively)
2. **Build local model inventory** by scanning /home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/models/
3. **Identify missing models** by comparing workflow requirements against local inventory
4. **Search Civitai API** for each missing model
5. **Generate bash download script** with wget commands using CIVITAI_API_KEY
6. **Place models in correct directories** based on their type

## Implementation Steps:

### Step 1: Scan Workflows

Parse each workflow JSON file and extract:
- Model filenames from node 'widgets_values' arrays (look for .safetensors, .ckpt, .pt files)
- Node types to determine expected model type
- Use this node type mapping:
  - CheckpointLoaderSimple → checkpoint → models/checkpoints/
  - LoraLoader → lora → models/loras/
  - VAELoader → vae → models/vae/
  - CLIPLoader → clip → models/clip/
  - ControlNetLoader → controlnet → models/controlnet/
  - UNETLoader → diffusion_models → models/diffusion_models/
  - DualCLIPLoader → text_encoders → models/text_encoders/

### Step 2: Build Local Inventory

Scan /home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/models/ recursively:
- Find all .safetensors, .ckpt, .pt, .bin files
- Build a set of filenames for fast lookup
- Note: Just use filenames, no need for hashing

### Step 3: Identify Missing Models

For each model referenced in workflows:
- Check if filename exists in local inventory
- If missing, add to missing list with:
  - filename
  - expected_type (lora, checkpoint, etc.)
  - expected_directory (models/loras/, etc.)
  - workflow it came from

### Step 4: Search Civitai API

For each missing model:
- Clean filename: remove .safetensors extension, replace underscores with spaces
- Call Civitai API: GET https://civitai.com/api/v1/models?query={cleaned_name}&limit=5
- Use Authorization header: Bearer $CIVITAI_API_KEY
- Parse response to get model ID and version ID
- Extract download URL: https://civitai.com/api/download/models/{version_id}

### Step 5: Generate Download Script

Create a bash script at /home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart/output/scripts/download_missing.sh:

```bash
#!/bin/bash
source ~/.secrets

MODELS_DIR="/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/models"

# For each missing model:
wget -c --content-disposition \\
  --timeout=30 --tries=5 --retry-connrefused \\
  -O "\${MODELS_DIR}/{type_directory}/{filename}" \\
  "https://civitai.com/api/download/models/{version_id}?token=\${CIVITAI_API_KEY}"
```

Make it executable: chmod +x download_missing.sh

### Step 6: Generate Report

Create a markdown report at /home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart/output/reports/analysis.md with:
- Number of workflows scanned
- Total models referenced
- Number of missing models
- List of missing models with their Civitai links
- Instructions to run the download script

## Output Files:

1. /home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart/output/scripts/download_missing.sh (executable)
2. /home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart/output/reports/analysis.md (report)
3. /home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart/output/missing_models.json (structured data)

## Important Notes:

- Use CIVITAI_API_KEY from environment (loaded from ~/.secrets)
- Handle API errors gracefully (some models may not be found)
- If a model isn't found on Civitai, note it in the report for manual search
- Keep the implementation simple - focus on getting it working first
- Don't over-engineer - this is a utility script, not enterprise software

## Success Criteria:

✅ All workflows scanned
✅ Missing models identified
✅ Civitai searches performed
✅ Download script generated and executable
✅ Report created with summary
✅ Script can be run by user to download models

Begin the task now. Work through each step methodically. Show your progress as you go.
PROMPT_END
)"

echo ""
echo "====================================="
echo "ComfyFixer Analysis Complete!"
echo "====================================="
echo ""
echo "Generated files:"
echo "  - output/scripts/download_missing.sh"
echo "  - output/reports/analysis.md"
echo "  - output/missing_models.json"
echo ""
echo "Next steps:"
echo "  1. Review: cat output/reports/analysis.md"
echo "  2. Download: bash output/scripts/download_missing.sh"
echo ""
