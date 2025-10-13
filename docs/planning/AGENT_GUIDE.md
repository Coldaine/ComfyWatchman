# Agent Guide: ComfyFixerSmart

**Purpose:** Instructions for AI agents to use ComfyFixerSmart autonomously

**Last Updated:** 2025-10-12

---

## Quick Start

### Basic Usage

```bash
cd /home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart

# Run full pipeline
python comfy_fixer.py --auto

# Monitor progress
python comfy_fixer.py --status
```

### Expected Output

```
=== ComfyFixerSmart ===
Phase: Scanning workflows...
  Found 15 workflows
  Found 234 local models
  Missing: 5 models

Phase: Resolving on Civitai/HuggingFace...
  Civitai: 4/5 found
  HuggingFace: 1/5 found
  Unresolved: 0/5

Phase: Downloading...
  [1/5] hunyuan_lora.safetensors ████████ 100%
  [2/5] checkpoint_v2.safetensors ████████ 100%
  ...

✓ Complete! Downloaded 5/5 models
```

---

## Status Monitoring

### Reading status.json

```python
import json

with open('status.json', 'r') as f:
    status = json.load(f)

print(f"Current phase: {status['phase']}")
print(f"Progress: {status['progress']['percent']}%")
```

### Status Phases

| Phase | Meaning | Next Action |
|-------|---------|-------------|
| `idle` | Not running | Can start new run |
| `scanning` | Scanning workflows/models | Wait |
| `resolving` | Searching Civitai/HF | Wait |
| `downloading` | Downloading models | Wait or monitor progress |
| `complete` | Finished successfully | Read results |
| `error` | Error occurred | Check logs, retry |

### Example Status File

```json
{
  "timestamp": "2025-10-12T14:30:00",
  "phase": "downloading",
  "progress": {
    "current": 2,
    "total": 5,
    "percent": 40
  },
  "data": {
    "workflows_scanned": 15,
    "missing_models": 5,
    "civitai_matches": 4,
    "huggingface_matches": 1,
    "downloads_successful": 2,
    "current_download": "model_name.safetensors"
  }
}
```

---

## Output Files

### Location: `output/`

**1. missing_models.json**
- List of models not found locally
- Generated after scan phase
- Contains: filename, type, workflow source

**Example:**
```json
[
  {
    "filename": "hunyuan_lora.safetensors",
    "expected_type": "lora",
    "workflow": "workflow1.json",
    "node_type": "LoraLoader",
    "node_id": 42
  }
]
```

**2. missing_nodes.json**
- List of custom nodes not installed
- Generated after scan phase
- Contains: node type, workflows using it

**Example:**
```json
[
  {
    "node_type": "CustomNodeType",
    "workflows": ["workflow1.json", "workflow2.json"]
  }
]
```

**3. resolutions.json**
- Results from Civitai/HuggingFace search
- Generated after resolve phase
- Contains: source, download URLs, metadata

**Example:**
```json
[
  {
    "filename": "hunyuan_lora.safetensors",
    "source": "civitai",
    "model_id": 1186768,
    "version_id": 1234567,
    "download_url": "https://civitai.com/api/download/models/1234567",
    "expected_type": "lora"
  },
  {
    "filename": "another_model.safetensors",
    "source": "huggingface",
    "repo_id": "username/model-name",
    "expected_type": "checkpoint"
  }
]
```

**4. summary_report.md**
- Human-readable summary
- Generated at completion
- Overview of what was found/downloaded

---

## Log Files

### Location: `log/`

**Log Naming:**
- `scan_YYYYMMDD_HHMMSS.log` - Scan phase logs
- `resolve_YYYYMMDD_HHMMSS.log` - Resolve phase logs
- `download_YYYYMMDD_HHMMSS.log` - Download phase logs

**Log Format:**
```
2025-10-12 14:30:00 [INFO] ComfyFixerSmart: Logging initialized
2025-10-12 14:30:01 [INFO] workflow_scanner: Scanning directory: /path/to/workflows
2025-10-12 14:30:02 [INFO] workflow_scanner: ✓ Parsed: workflow1.json (8 models)
2025-10-12 14:30:03 [ERROR] workflow_scanner: ✗ Failed to parse workflow2.json: Invalid JSON
```

**Structured Action Logs:**
```
2025-10-12 14:30:04 [INFO] ComfyFixerSmart: ACTION: {"timestamp": "2025-10-12T14:30:04", "action": "model_found", "details": {"filename": "model.safetensors", "source": "civitai"}}
```

**Parsing Structured Logs:**
```python
import re
import json

with open('log/scan_20251012_143000.log') as f:
    for line in f:
        if 'ACTION:' in line:
            # Extract JSON
            match = re.search(r'ACTION: ({.*})', line)
            if match:
                action = json.loads(match.group(1))
                print(f"{action['action']}: {action['details']}")
```

---

## Error Handling

### Common Errors

**1. "No workflows found"**
- **Cause:** workflow_directories empty or invalid
- **Solution:** Check config.json, verify paths exist
- **Recovery:** Update config, re-run with `--scan`

**2. "Civitai API error: 401"**
- **Cause:** Invalid or missing CIVITAI_API_KEY
- **Solution:** Check ~/.secrets, verify API key is valid
- **Recovery:** Update API key, re-run with `--resolve`

**3. "Download failed: timeout"**
- **Cause:** Network issue or slow download
- **Solution:** Check internet connection
- **Recovery:** Re-run with `--download` (will resume)

**4. "Model not found on Civitai or HuggingFace"**
- **Cause:** Model doesn't exist or name mismatch
- **Solution:** Check output/resolutions.json for unresolved items
- **Recovery:** Manual search or update workflow

### Error States in status.json

```json
{
  "phase": "error",
  "errors": [
    {
      "timestamp": "2025-10-12T14:30:00",
      "error": "Civitai API error: 401",
      "details": "Invalid API key"
    }
  ]
}
```

### Recovery Actions

```python
with open('status.json') as f:
    status = json.load(f)

if status['phase'] == 'error':
    for error in status['errors']:
        print(f"Error: {error['error']}")

        if 'API error: 401' in error['error']:
            print("Action: Check API key in ~/.secrets")
        elif 'timeout' in error['error']:
            print("Action: Re-run with --resume")
        elif 'not found' in error['error']:
            print("Action: Review output/resolutions.json")
```

---

## Resume Logic

### When to Resume

- Download interrupted by network failure
- Process killed mid-execution
- Timeout on large downloads

### How to Resume

```bash
python comfy_fixer.py --resume
```

**What --resume does:**
1. Checks for existing output files
2. Skips completed phases
3. Resumes from last incomplete phase
4. Skips already downloaded models

**Resume Logic:**
```python
# Pseudo-code for resume logic
if exists('output/resolutions.json'):
    # Skip scan and resolve phases
    resolutions = load('output/resolutions.json')

    # Check which models are already downloaded
    for resolution in resolutions:
        target_path = determine_save_path(resolution)

        if exists(target_path):
            logger.info(f"Skipping {resolution['filename']}: already exists")
            continue

        # Download missing ones
        download(resolution)
```

---

## Agent Workflow Example

### Full Autonomous Agent

```python
#!/usr/bin/env python3
"""
Autonomous agent using ComfyFixerSmart
"""

import subprocess
import json
import time
import sys


def run_comfy_fixer():
    """Run ComfyFixerSmart and monitor progress"""

    print("Starting ComfyFixerSmart...")

    # Start process in background
    process = subprocess.Popen(
        ['python', 'comfy_fixer.py', '--auto'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Monitor status
    last_phase = None
    while True:
        # Check if process is still running
        if process.poll() is not None:
            print("Process completed")
            break

        # Read status
        try:
            with open('status.json') as f:
                status = json.load(f)
        except FileNotFoundError:
            time.sleep(1)
            continue

        # Report phase changes
        current_phase = status['phase']
        if current_phase != last_phase:
            print(f"\nPhase: {current_phase}")
            last_phase = current_phase

        # Report progress
        if 'progress' in status and status['progress']['total'] > 0:
            percent = status['progress']['percent']
            current = status['progress']['current']
            total = status['progress']['total']
            print(f"  Progress: [{current}/{total}] {percent}%", end='\r')

        # Check for errors
        if current_phase == 'error':
            print("\n✗ Error occurred!")
            for error in status.get('errors', []):
                print(f"  - {error['error']}")
            return False

        # Check for completion
        if current_phase == 'complete':
            print("\n✓ Complete!")
            break

        time.sleep(2)

    # Read results
    print("\n=== Results ===")

    with open('output/missing_models.json') as f:
        missing = json.load(f)
        print(f"Missing models found: {len(missing)}")

    with open('output/resolutions.json') as f:
        resolutions = json.load(f)
        civitai = sum(1 for r in resolutions if r['source'] == 'civitai')
        hf = sum(1 for r in resolutions if r['source'] == 'huggingface')
        not_found = sum(1 for r in resolutions if r['source'] == 'not_found')

        print(f"Resolved on Civitai: {civitai}")
        print(f"Resolved on HuggingFace: {hf}")
        print(f"Not found: {not_found}")

    # Check final status
    with open('status.json') as f:
        final_status = json.load(f)
        downloads_successful = final_status['data'].get('downloads_successful', 0)
        downloads_failed = final_status['data'].get('downloads_failed', 0)

        print(f"Downloads successful: {downloads_successful}")
        print(f"Downloads failed: {downloads_failed}")

    return downloads_failed == 0


if __name__ == '__main__':
    success = run_comfy_fixer()
    sys.exit(0 if success else 1)
```

### Minimal Status Check

```python
import json

with open('status.json') as f:
    status = json.load(f)

if status['phase'] == 'complete':
    data = status['data']
    print(f"✓ Scanned {data['workflows_scanned']} workflows")
    print(f"✓ Downloaded {data['downloads_successful']} models")
elif status['phase'] == 'error':
    print("✗ Error occurred, check logs")
else:
    print(f"Running: {status['phase']} ({status['progress']['percent']}%)")
```

---

## Configuration

### config.json

**Location:** `ComfyFixerSmart/config.json`

**Required Fields:**
```json
{
  "comfyui_root": "/path/to/ComfyUI-stable",
  "workflow_directories": [
    "/path/to/workflows"
  ]
}
```

**Optional Fields:**
```json
{
  "download": {
    "max_concurrent": 3,
    "timeout_seconds": 600
  },
  "search": {
    "fuzzy_threshold": 0.7
  }
}
```

### Environment Variables

**Required:**
- `CIVITAI_API_KEY` - Get from https://civitai.com/user/account
- Stored in `~/.secrets`
- Auto-loaded by shell

**Optional:**
- `HF_TOKEN` - HuggingFace token for authenticated access
- Stored in `~/.secrets`

### Verify Configuration

```bash
# Check if API keys are set
echo $CIVITAI_API_KEY
echo $HF_TOKEN

# Check config.json
cat config.json | python -m json.tool
```

---

## Troubleshooting

### Issue: "Permission denied"
**Solution:** Ensure execute permissions
```bash
chmod +x comfy_fixer.py
```

### Issue: "Module not found"
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "Status file not found"
**Solution:** Process hasn't started yet or failed to initialize
```bash
# Check if process is running
ps aux | grep comfy_fixer

# Check logs
tail -f log/*.log
```

### Issue: "Download stuck at 0%"
**Solution:** Network issue or API key problem
```bash
# Check network
ping civitai.com

# Check API key
grep CIVITAI_API_KEY ~/.secrets

# Check logs for details
tail -f log/download_*.log
```

---

## Best Practices for Agents

### 1. Always Check Status First
```python
# Before starting new run
with open('status.json') as f:
    status = json.load(f)

if status['phase'] not in ['idle', 'complete', 'error']:
    print("Already running, monitoring instead")
    monitor_progress()
else:
    start_new_run()
```

### 2. Use --resume for Reliability
```bash
# Instead of --auto
python comfy_fixer.py --resume
```
- Idempotent (safe to run multiple times)
- Skips completed work
- Recovers from failures

### 3. Monitor Logs for Details
```python
import subprocess

# Tail logs in real-time
subprocess.Popen(['tail', '-f', 'log/download_*.log'])
```

### 4. Handle Errors Gracefully
```python
try:
    run_comfy_fixer()
except Exception as e:
    # Log error
    with open('log/agent_error.log', 'a') as f:
        f.write(f"{datetime.now()}: {e}\n")

    # Update status
    update_status('error', {'error': str(e)})

    # Notify user
    print(f"Error: {e}")
    print("Check log/agent_error.log for details")
```

### 5. Verify Results
```python
# After completion
with open('output/resolutions.json') as f:
    resolutions = json.load(f)

unresolved = [r for r in resolutions if r['source'] == 'not_found']
if unresolved:
    print(f"Warning: {len(unresolved)} models not found:")
    for r in unresolved:
        print(f"  - {r['filename']}")
```

---

## FAQ for Agents

**Q: Can I run multiple instances in parallel?**
A: No, status.json is shared. Run one instance at a time or use separate directories.

**Q: How do I know if a download is stuck?**
A: Check if `status.json` timestamp is updating. If unchanged for >5 minutes, likely stuck.

**Q: What if Civitai API is rate-limited?**
A: Tool will retry with exponential backoff. Check logs for rate limit messages.

**Q: Can I add custom search locations?**
A: Yes, edit `config.json` → `workflow_directories` array.

**Q: How do I handle unresolved models?**
A: Check `output/resolutions.json` for `"source": "not_found"` items. May need manual search or workflow updates.

---

## Command Reference

```bash
# Full pipeline
python comfy_fixer.py --auto

# Individual phases
python comfy_fixer.py --scan      # Phase 1: Scan only
python comfy_fixer.py --resolve   # Phase 2: Search only
python comfy_fixer.py --download  # Phase 3: Download only

# Utilities
python comfy_fixer.py --status    # Show current status
python comfy_fixer.py --resume    # Resume from last state

# Help
python comfy_fixer.py --help
```

---

**For questions or issues, check:**
1. `log/` directory for execution logs
2. `status.json` for current state
3. `output/` directory for results
4. README.md for user documentation

---

**Agent Instructions Complete**
**Last Updated:** 2025-10-12
