# Batch Workflow Finder

Automated tool for finding ComfyUI workflows that use a specific LoRA model from Civitai.

## Overview

Given a Civitai LoRA model ID, this script will:

1. **Fetch model metadata** - Get LoRA information including all filenames and versions
2. **Search for workflows** - Use multiple strategies to find workflows:
   - Direct workflow model search by tags/keywords
   - Creator's workflow models (workflows published by the LoRA creator)
   - PNG images with embedded workflow metadata
3. **Download and verify** - Download each workflow and verify it's valid
4. **Check LoRA usage** - Parse workflows to confirm they actually reference the LoRA
5. **Generate report** - Create comprehensive JSON and text reports with findings

## Installation

```bash
# Required dependencies
pip install requests pillow

# Ensure CIVITAI_API_KEY is set in ~/.secrets
echo 'export CIVITAI_API_KEY="your_key_here"' >> ~/.secrets
source ~/.secrets
```

## Usage

### Basic Usage

```bash
# Search for workflows using LoRA model 1952032 (Perfect Fingering)
python batch_workflow_finder.py 1952032
```

### Advanced Options

```bash
# Extended search with all strategies
python batch_workflow_finder.py 1952032 \
  --limit 50 \
  --creator-workflows \
  --download-pngs \
  --tags "pony,sdxl"

# Search specific version
python batch_workflow_finder.py 1952032 --version-id 2209481

# More examples
python batch_workflow_finder.py 1952032 --limit 100  # Increase search limit
python batch_workflow_finder.py 1952032 --tags "anime,character"  # Custom tags
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `model_id` | Civitai LoRA model ID (required) | - |
| `--version-id` | Specific version ID to focus on | Latest |
| `--limit` | Limit per search strategy | 20 |
| `--creator-workflows` | Search workflows by LoRA creator | Off |
| `--download-pngs` | Extract workflows from PNG images | Off |
| `--tags` | Comma-separated tags for search | None |

## Search Strategies

### Strategy 1: Tag-Based Workflow Search
Searches Civitai workflow models using specified tags.

**Example:**
```bash
python batch_workflow_finder.py 1952032 --tags "pony,sdxl,character"
```

### Strategy 2: Creator Workflows
Finds workflows published by the same creator who made the LoRA.

**Rationale:** LoRA creators often publish example workflows demonstrating their models.

```bash
python batch_workflow_finder.py 1952032 --creator-workflows
```

### Strategy 3: PNG Metadata Extraction
Downloads PNG images from the LoRA's gallery and extracts embedded workflow metadata.

**How it works:**
- ComfyUI embeds workflow JSON in PNG metadata chunks
- Script downloads PNGs, extracts workflow data, checks for LoRA usage
- Cleans up PNGs after extraction (keeps only workflow JSON)

```bash
python batch_workflow_finder.py 1952032 --download-pngs
```

## Output Structure

All outputs are saved to `output/workflow_finder/run_{model_id}_{timestamp}/`

### Files Created

1. **`workflow_finder_report.json`** - Complete JSON report with:
   - LoRA model metadata
   - Search statistics
   - All findings with full details
   - Timestamp

2. **`workflow_finder_summary.txt`** - Human-readable summary:
   - Statistics
   - List of workflows found
   - Model dependencies for each workflow

3. **`workflow_{model_id}_{version_id}_{name}.json`** - Downloaded workflow files

4. **`workflow_from_png_{image_id}.json`** - Workflows extracted from PNG images

### Example Report Structure

```json
{
  "lora_model": {
    "id": 1952032,
    "name": "Perfect Fingering",
    "creator": "username",
    "type": "LORA"
  },
  "statistics": {
    "duration_seconds": 45.2,
    "api_calls": 15,
    "workflows_found": 8,
    "workflows_downloaded": 8,
    "workflows_with_lora": 5,
    "png_images_checked": 20,
    "png_with_workflow": 12,
    "errors": 0,
    "success_rate": 62.5
  },
  "findings": [
    {
      "model_id": 1234567,
      "model_name": "Example Workflow",
      "version_name": "v1.0",
      "workflow_file": "path/to/workflow.json",
      "matched_loras": ["perfect_fingering_v1.safetensors"],
      "all_models": {
        "checkpoints": ["ponyDiffusionXL_v6.safetensors"],
        "loras": ["perfect_fingering_v1.safetensors", "other_lora.safetensors"],
        "vae": ["sdxl_vae.safetensors"]
      },
      "source": "workflow_model"
    }
  ]
}
```

## Features

### Defensive Programming

Following lessons from `docs/reports/civitai-api-wrong-metadata-incident.md`:

1. **Response Validation** - Always validates API returns match requested IDs
2. **Request Logging** - Logs all API calls with params and responses
3. **Error Handling** - Graceful handling of failures with detailed error messages
4. **Rate Limiting** - Respects API rate limits (1 second delay between calls)
5. **Statistics Tracking** - Tracks errors, success rates, and API usage

### Workflow Verification

1. **Format Validation** - Checks JSON structure for ComfyUI workflow format
2. **LoRA Presence Check** - Searches workflow for actual LoRA filename references
3. **Model Extraction** - Parses all model dependencies (checkpoints, LoRAs, VAE, etc.)
4. **Deduplication** - Handles same workflow from multiple sources

### API Key Management

- Uses `CIVITAI_API_KEY` from environment (loaded from `~/.secrets`)
- Validates API key format before use
- Automatically adds API key to download URLs

## Example Session

```bash
$ python batch_workflow_finder.py 1952032 --creator-workflows --download-pngs

======================================================================
Batch Workflow Finder - Starting
======================================================================
LoRA Model ID: 1952032
Search limit: 20
Creator workflows: True
PNG extraction: True

Fetching model info for ID: 1952032
  Model: Perfect Fingering
  Type: LORA
  Creator: example_user
  Versions: 2

LoRA filenames to search for: ['perfect_fingering_v1.safetensors', 'perfect_fingering_v2.safetensors']

======================================================================
Strategy 1: Creator's workflow models
======================================================================
Searching for workflows by creator: example_user
  Found 5 workflow models
  Processing workflow model: Character Workflow (ID: 1234567)
    Downloading: workflow_example.json
    ✅ FOUND LoRA in workflow: ['perfect_fingering_v1.safetensors']

======================================================================
Strategy 2: PNG images with workflow metadata
======================================================================
Fetching images for model 1952032
  Found 20 images
    ✅ FOUND LoRA in PNG workflow: ['perfect_fingering_v2.safetensors']

======================================================================
Generating Report
======================================================================

📊 Report saved to:
  JSON: output/workflow_finder/run_1952032_20251023_140530/workflow_finder_report.json
  Summary: output/workflow_finder/run_1952032_20251023_140530/workflow_finder_summary.txt

======================================================================
Batch Workflow Finder - Complete
======================================================================
Duration: 45.2 seconds
API Calls: 15
Workflows Found: 8
Workflows with LoRA: 5
Success Rate: 62.5%

Results saved to: output/workflow_finder/run_1952032_20251023_140530
```

## Integration with ComfyWatchman

The found workflows can be used with ComfyWatchman for dependency analysis:

```bash
# 1. Find workflows
python batch_workflow_finder.py 1952032 --creator-workflows --download-pngs

# 2. Analyze dependencies
cd output/workflow_finder/run_1952032_*/
comfywatchman workflow_*.json

# 3. Download missing models
bash output/download_missing_*.sh
```

## Error Handling

The script handles various error conditions:

- **Model not found** - Validates model exists before searching
- **No workflows found** - Exits with code 1 if no workflows contain LoRA
- **API errors** - Logs and continues with remaining strategies
- **Download failures** - Skips failed downloads, continues with others
- **Invalid workflows** - Validates JSON structure before processing
- **Rate limits** - Automatic delays between requests

## Performance

- **Rate limiting**: 1 second between API calls
- **Parallel strategies**: All strategies run in sequence but independently
- **PNG cleanup**: Removes PNG files after workflow extraction (keeps JSON only)
- **Typical runtime**: 30-60 seconds for default settings

## Troubleshooting

### No workflows found

```bash
# Try increasing limit
python batch_workflow_finder.py 1952032 --limit 50

# Enable all strategies
python batch_workflow_finder.py 1952032 --creator-workflows --download-pngs
```

### API key errors

```bash
# Verify API key is set
echo $CIVITAI_API_KEY

# Re-source secrets file
source ~/.secrets
```

### Connection timeouts

- Check internet connection
- Civitai API may be temporarily unavailable
- Try again later or increase timeout in script

## Logging

Logs are saved to `log/batch_workflow_finder_{timestamp}.log`

Log levels:
- **INFO** - General progress messages
- **DEBUG** - API requests and responses
- **ERROR** - Failures and exceptions
- **WARN** - Non-fatal issues
- **SUCCESS** - Successful LoRA findings

## Future Enhancements

Potential improvements:
- [ ] Support for searching by multiple LoRA IDs
- [ ] Workflow quality scoring (by downloads, ratings)
- [ ] Direct ComfyUI workflow installation
- [ ] Cached results to avoid re-downloading
- [ ] Top users search strategy (most popular workflow creators)
- [ ] Model version matching (ensure workflow uses specific version)

## Related Scripts

- **`download_workflow.py`** - Downloads single workflow from URL
- **`test_png_extraction.py`** - Tests PNG workflow extraction capability
- **ComfyWatchman CLI** - Main dependency analysis tool

## License

Part of ComfyWatchman project. See main project LICENSE.
