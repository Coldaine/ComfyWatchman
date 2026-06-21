# Batch Workflow Finder - Quick Reference

## Common Usage Patterns

### 1. Quick Search (Basic)
Find workflows for a LoRA with minimal API calls:
```bash
python batch_workflow_finder.py <MODEL_ID>
```
**Searches:** Workflow models only
**API Calls:** ~5-10
**Time:** ~10-20 seconds

### 2. Thorough Search (Recommended)
Search using all available strategies:
```bash
python batch_workflow_finder.py <MODEL_ID> \
  --creator-workflows \
  --download-pngs \
  --limit 30
```
**Searches:** Workflow models + Creator workflows + PNG images
**API Calls:** ~40-60
**Time:** ~60-90 seconds

### 3. Creator-Only Search
Focus on workflows by the LoRA creator:
```bash
python batch_workflow_finder.py <MODEL_ID> --creator-workflows
```
**Why:** Creators often publish example workflows
**Best for:** Popular LoRAs with active creators

### 4. PNG-Only Search
Extract workflows from example images:
```bash
python batch_workflow_finder.py <MODEL_ID> --download-pngs --limit 50
```
**Why:** Many users share workflows via PNG metadata
**Best for:** LoRAs with rich image galleries

### 5. Targeted Tag Search
Search workflows with specific themes:
```bash
python batch_workflow_finder.py <MODEL_ID> \
  --tags "pony,character,anime" \
  --limit 50
```
**Best for:** Genre-specific LoRAs (anime, realistic, etc.)

## Real-World Examples

### Example 1: Perfect Fingering LoRA
```bash
# Model: https://civitai.com/models/1952032
python batch_workflow_finder.py 1952032 \
  --creator-workflows \
  --download-pngs \
  --tags "pony,hands" \
  --limit 30
```

### Example 2: Specific Version Search
```bash
# When you need workflows for a specific version
python batch_workflow_finder.py 1952032 \
  --version-id 2209481 \
  --download-pngs \
  --limit 20
```

### Example 3: High-Volume Search
```bash
# Cast a wide net (more API calls, longer runtime)
python batch_workflow_finder.py 1952032 \
  --creator-workflows \
  --download-pngs \
  --tags "pony,sdxl,character" \
  --limit 100
```

## Output Files Quick Reference

```
output/workflow_finder/run_{model_id}_{timestamp}/
├── workflow_finder_report.json          # Complete JSON data
├── workflow_finder_summary.txt          # Human-readable summary
├── workflow_{model}_{version}_{name}.json  # Downloaded workflows
└── workflow_from_png_{image_id}.json    # PNG-extracted workflows
```

## Quick Tips

### 🎯 Finding Workflows Efficiently

1. **Start basic** - Run without flags first
2. **Add creator search** - If basic search yields few results
3. **Enable PNG extraction** - If creator search still insufficient
4. **Increase limit** - If you need more options
5. **Use tags** - If you want themed/categorized workflows

### ⚡ Performance Optimization

- **Minimal search**: No flags, limit=10 (~10 sec)
- **Balanced search**: `--creator-workflows --limit 20` (~30 sec)
- **Thorough search**: All flags, limit=50 (~120 sec)

### 🔍 Troubleshooting Quick Fixes

**No workflows found?**
```bash
# Try increasing limit and adding strategies
python batch_workflow_finder.py <MODEL_ID> \
  --creator-workflows --download-pngs --limit 50
```

**Too slow?**
```bash
# Reduce limit
python batch_workflow_finder.py <MODEL_ID> --limit 10
```

**API key errors?**
```bash
source ~/.secrets
echo $CIVITAI_API_KEY  # Should show your key
```

## Integration with ComfyWatchman

### Complete Workflow Discovery → Installation Pipeline

```bash
# 1. Find workflows
python batch_workflow_finder.py 1952032 \
  --creator-workflows --download-pngs

# 2. Navigate to results
cd output/workflow_finder/run_1952032_*/

# 3. Analyze dependencies for all found workflows
comfywatchman workflow_*.json

# 4. Review missing models
cat output/missing_models_*.json

# 5. Download missing models
bash output/download_missing_*.sh

# 6. Copy workflows to ComfyUI
cp workflow_*.json ~/StableDiffusionWorkflow/ComfyUI-stable/user/default/workflows/
```

## Success Rate Interpretation

| Success Rate | Meaning | Action |
|-------------|---------|--------|
| 80-100% | Excellent - LoRA widely used in workflows | Use any found workflow |
| 50-79% | Good - Several valid workflows found | Review workflow quality |
| 25-49% | Fair - Limited workflow availability | Try increasing `--limit` |
| 0-24% | Poor - Few/no workflows found | Try all strategies + tags |

## Common Model IDs for Testing

```bash
# Perfect Fingering (hand LoRA)
python batch_workflow_finder.py 1952032

# Add your frequently-used LoRA IDs here for quick reference
```

## Flags Cheat Sheet

| Flag | Purpose | Cost | When to Use |
|------|---------|------|-------------|
| *(none)* | Basic workflow search | Low | First try |
| `--creator-workflows` | Creator's workflows | Medium | Popular creators |
| `--download-pngs` | Extract from images | High | Rich galleries |
| `--tags "x,y,z"` | Tagged workflow search | Medium | Specific themes |
| `--limit N` | Results per strategy | Scales | Need more results |
| `--version-id` | Specific version | None | Version-specific |

**Cost** = API calls + time

## One-Liners for Common Scenarios

```bash
# "Find me ANY workflow using this LoRA"
python batch_workflow_finder.py <ID> --creator-workflows --download-pngs

# "Quick check - does anyone use this?"
python batch_workflow_finder.py <ID> --limit 5

# "Find workflows for this specific version"
python batch_workflow_finder.py <ID> --version-id <VID>

# "Cast a wide net, I'll wait"
python batch_workflow_finder.py <ID> --creator-workflows --download-pngs --limit 100
```
