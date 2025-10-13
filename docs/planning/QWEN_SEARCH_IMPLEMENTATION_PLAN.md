# Qwen-Based Model Search Implementation Plan

## Executive Summary

Replace the naive Civitai search with an autonomous Qwen agent that intelligently searches both Civitai and HuggingFace, validates filename matches, and handles fallback strategies.

**Current Problem**: Script downloads "Pony Diffusion V6 XL" (6.5GB) 7+ times for unrelated models like `rife49.pth`, `4xNMKDSuperscale.pt`, etc.

**Solution**: Let Qwen autonomously iterate through search strategies until finding correct match or exhaustively confirming NOT_FOUND.

## Research Agent Feedback (Grade: 8/10)

### Key Insights Discovered:

1. **Civitai API limitation**: No filename search - must search by model name, then check files
2. **HuggingFace CLI limitation**: No search command - must use web search + verification
3. **Hash-based fallback**: Civitai supports `/api/v1/model-versions/by-hash/{sha256}`
4. **Smart pattern recognition**: Known model types should skip certain sources

## Implementation Strategy

### Phase 1: Civitai Search (Max 8 attempts)

**Intelligent Keyword Extraction**:
```python
"rife49.pth" → ["rife", "frame interpolation", "rife 4.9"]
"4xNMKDSuperscale_4xNMKDSuperscale.pt" → ["nmkd", "superscale", "4x", "upscale"]
"BIGLOVEsubtle-rayness2-xl25.safetensors" → ["biglove", "rayness", "xl", "sdxl"]
```

**Query Cascade**:
1. Exact name without extension
2. Main keyword only
3. Alternative terms based on type
4. Broader category with type filter

**Type Filtering via API**:
```
upscale_models → &types=Upscaler
checkpoints → &types=Checkpoint
loras → &types=LORA
vae → &types=VAE
controlnet → &types=Controlnet
```

**Validation Loop**:
```
For each search result:
  Fetch /api/v1/models/{id}
  For each modelVersions[]:
    For each files[]:
      If files[].name == exact_filename:
        MATCH FOUND!
```

### Phase 2: HuggingFace Search

**Web Search Strategies**:
1. `"{filename} site:huggingface.co"`
2. `"{model_name} huggingface model"`
3. Pattern-specific searches:
   - `rife*.pth` → "rife frame interpolation huggingface"
   - `sam_*.pth` → "facebook sam huggingface"
   - `*NMKD*.pt` → "nmkd upscaler huggingface"

**Verification**:
```bash
# Option 1: List files and grep
hf download <repo> --list-files | grep {filename}

# Option 2: Web fetch repo page
curl https://huggingface.co/<repo>/tree/main | parse for filename
```

**Download URL Construction**:
```
https://huggingface.co/{user}/{repo}/resolve/main/{file_path}
```

### Phase 3: Hash-Based Fallback

**For models that exist locally but need metadata**:
```bash
# Calculate hash
sha256sum /path/to/model.safetensors

# Query Civitai
curl https://civitai.com/api/v1/model-versions/by-hash/{hash}
```

**Use Case**: User has file but doesn't know which Civitai model it came from

### Phase 4: Smart Give-Up Heuristics

**Early Termination Patterns**:
```python
DIRECT_TO_HUGGINGFACE = [
    r'^sam_.*\.pth$',           # Segment Anything Model
    r'^sam2_.*\.safetensors$',  # SAM 2
    r'rife\d+\.pth$',           # RIFE frame interpolation
    r'.*realesrgan.*\.pth$',    # RealESRGAN upscalers
    r'.*umt5.*\.safetensors$',  # T5 text encoders
    r'.*NMKD.*\.pt$',           # NMKD upscalers
]

LIKELY_NOT_ON_CIVITAI = [
    r'.*\?.*',  # Contains URL query params (malformed)
    r'.*\n.*',  # Contains newlines (malformed)
]
```

**Decision Tree**:
```
If filename matches LIKELY_NOT_ON_CIVITAI:
  → Return INVALID_FILENAME

If filename matches DIRECT_TO_HUGGINGFACE:
  → Skip Civitai, go straight to HuggingFace

If 5 Civitai searches return 0 results:
  → Skip to HuggingFace

If 8 Civitai searches with results but no filename match:
  → Try HuggingFace

If HuggingFace also fails:
  → Return NOT_FOUND
```

## Qwen Prompt Template

### Full Autonomous Prompt:

```python
QWEN_PROMPT = f"""You are an autonomous model discovery agent. Your task is to find the correct download source for an AI model file.

INPUT DATA:
- Filename: {model['filename']}
- Model Type: {model['type']}
- Node Type: {model['node_type']}

ENVIRONMENT:
- CIVITAI_API_KEY is available in environment
- You have access to: bash, web_search, web_fetch, file_write tools

YOUR GOAL:
Find where to download this exact file, or confirm it doesn't exist on Civitai/HuggingFace.

SEARCH STRATEGY:

=== PHASE 1: CIVITAI SEARCH (Max 8 attempts) ===

1. Extract search keywords from filename:
   - Remove extensions: .pth, .pt, .safetensors, .ckpt, .bin
   - Split on delimiters: _, -, .
   - Identify: version numbers, model types, keywords

   Examples:
   "rife49.pth" → ["rife", "49", "frame interpolation"]
   "BIGLOVEsubtle-rayness2-xl25.safetensors" → ["biglove", "rayness", "xl", "sdxl"]

2. Query cascade (try in order until match):
   a) Exact name without extension: "{model['filename'].rsplit('.', 1)[0]}"
   b) Main keyword only
   c) Alternative terms based on model type
   d) Broader category with type filter

3. Use type filtering in API calls:
   - upscale_models → add "&types=Upscaler"
   - checkpoints → add "&types=Checkpoint"
   - loras → add "&types=LORA"
   - vae → add "&types=VAE"

   API: https://civitai.com/api/v1/models?query=<term>&limit=10&types=<type>

4. For EACH result:
   - Fetch full details: https://civitai.com/api/v1/models/{{id}}
   - Check ALL modelVersions[].files[].name for EXACT match to "{model['filename']}"
   - Log: "Checked model {{id}} '{{name}}': {{result}}"

5. CRITICAL: Match must be EXACT (case-sensitive, full filename with extension)

=== PHASE 2: HUGGINGFACE SEARCH (If Civitai fails) ===

1. Smart pattern recognition:
   - If filename matches "sam_*.pth" → Search: "facebook sam huggingface"
   - If filename matches "rife*.pth" → Search: "rife frame interpolation huggingface"
   - If filename contains "NMKD" → Search: "nmkd upscaler huggingface"
   - Otherwise → Search: "{model['filename']} site:huggingface.co"

2. Extract repo from web search results:
   - Look for patterns: huggingface.co/<user>/<repo>/blob/main/<path>
   - Extract: user, repo, file_path

3. Verify file exists:
   - Method 1: hf download <repo> --list-files | grep {model['filename']}
   - Method 2: Fetch https://huggingface.co/<repo>/tree/main and check for filename

4. If found, construct download URL:
   https://huggingface.co/<user>/<repo>/resolve/main/<file_path>

=== PHASE 3: DECISION & OUTPUT ===

SUCCESS - Found on Civitai:
Write to /tmp/qwen_search_result.json:
{{{{
  "status": "FOUND",
  "source": "civitai",
  "civitai_id": <model_id>,
  "version_id": <version_id>,
  "civitai_name": "<model_name>",
  "version_name": "<version_name>",
  "download_url": "https://civitai.com/api/download/models/<version_id>",
  "metadata": {{{{
    "search_attempts": <count>,
    "validation_checks": <count>
  }}}}
}}}}

SUCCESS - Found on HuggingFace:
Write to /tmp/qwen_search_result.json:
{{{{
  "status": "FOUND",
  "source": "huggingface",
  "repo": "<user>/<repo>",
  "file_path": "<path>",
  "download_url": "https://huggingface.co/<user>/<repo>/resolve/main/<path>",
  "metadata": {{{{
    "search_attempts": <count>
  }}}}
}}}}

FAILURE - Not Found:
Write to /tmp/qwen_search_result.json:
{{{{
  "status": "NOT_FOUND",
  "metadata": {{{{
    "civitai_searches": <count>,
    "huggingface_searches": <count>,
    "reason": "<detailed explanation>"
  }}}}
}}}}

INVALID - Malformed Filename:
If filename contains '?' or newlines or looks like notes:
Write to /tmp/qwen_search_result.json:
{{{{
  "status": "INVALID_FILENAME",
  "reason": "Filename contains URL params or invalid characters"
}}}}

LOGGING:
Print to stderr your reasoning as you search. Example:
[QWEN] Extracting keywords from "{model['filename']}"...
[QWEN] Keywords: ["rife", "49"]
[QWEN] Civitai query 1: "rife" → 3 results
[QWEN]   Checking model 123456 "RIFE Frame Interpolation"...
[QWEN]   Version v4.9 files: [rife49.pth, rife49_lite.pth]
[QWEN]   ✓ MATCH FOUND: rife49.pth

CRITICAL RULES:
1. Filename validation must be EXACT match
2. Try multiple search strategies before giving up
3. Always write output JSON to /tmp/qwen_search_result.json
4. Be autonomous - iterate until success or exhausted all options
5. Maximum 15 minutes timeout

BEGIN SEARCH NOW.
"""
```

## Python Integration Code

### Updated search_civitai Function:

```python
import subprocess
import json
import os
import tempfile
from pathlib import Path

def search_civitai(model):
    """Search for model using autonomous Qwen agent"""
    api_key = get_api_key()

    log(f"  Launching Qwen search for: {model['filename']}")

    # Create temp directory for results
    temp_dir = Path("/tmp/qwen_search_results")
    temp_dir.mkdir(exist_ok=True)

    # Sanitize filename for temp file
    safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', model['filename'])
    result_file = temp_dir / f"{safe_name}.json"

    # Build Qwen prompt (using template above)
    prompt = QWEN_PROMPT  # Full prompt from template

    try:
        # Run Qwen with YOLO mode (auto-approve all actions)
        result = subprocess.run(
            ['qwen', '-p', prompt, '--yolo'],
            capture_output=True,
            text=True,
            timeout=900,  # 15 minutes max
            env={**os.environ, 'CIVITAI_API_KEY': api_key},
            cwd=str(temp_dir)
        )

        # Check if Qwen wrote output file
        if not result_file.exists():
            log(f"    ✗ Qwen did not create output file")
            log(f"    Qwen stdout: {result.stdout[-500:]}")  # Last 500 chars
            log(f"    Qwen stderr: {result.stderr[-500:]}")
            return None

        # Read Qwen's result
        with open(result_file) as f:
            qwen_result = json.load(f)

        # Handle different outcomes
        if qwen_result.get('status') == 'INVALID_FILENAME':
            log(f"    ⚠️  Invalid filename: {qwen_result.get('reason')}")
            return None

        if qwen_result.get('status') == 'NOT_FOUND':
            metadata = qwen_result.get('metadata', {})
            log(f"    ✗ Not found after {metadata.get('civitai_searches', 0)} Civitai + "
                f"{metadata.get('huggingface_searches', 0)} HF searches")
            log(f"    Reason: {metadata.get('reason', 'Unknown')}")
            return None

        if qwen_result.get('status') == 'FOUND':
            source = qwen_result['source']

            if source == 'civitai':
                resolution = {
                    'filename': model['filename'],
                    'type': model['type'],
                    'source': 'civitai',
                    'civitai_id': qwen_result['civitai_id'],
                    'version_id': qwen_result['version_id'],
                    'civitai_name': qwen_result['civitai_name'],
                    'version_name': qwen_result['version_name'],
                    'download_url': qwen_result['download_url']
                }
                log(f"    ✓ Found on Civitai: {qwen_result['civitai_name']} "
                    f"(ID: {qwen_result['civitai_id']})")

            elif source == 'huggingface':
                resolution = {
                    'filename': model['filename'],
                    'type': model['type'],
                    'source': 'huggingface',
                    'repo': qwen_result['repo'],
                    'file_path': qwen_result['file_path'],
                    'download_url': qwen_result['download_url']
                }
                log(f"    ✓ Found on HuggingFace: {qwen_result['repo']}")

            else:
                log(f"    ✗ Unknown source: {source}")
                return None

            return resolution

        # Unknown status
        log(f"    ✗ Unknown Qwen status: {qwen_result.get('status')}")
        return None

    except subprocess.TimeoutExpired:
        log(f"    ✗ Qwen search timed out after 15 minutes")
        return None
    except json.JSONDecodeError as e:
        log(f"    ✗ Failed to parse Qwen output: {e}")
        if result_file.exists():
            log(f"    Raw output: {result_file.read_text()[:500]}")
        return None
    except Exception as e:
        log(f"    ✗ Qwen search error: {e}")
        return None
```

### Updated generate_download_script Function:

```python
def generate_download_script(resolutions):
    """Generate download script supporting both Civitai and HuggingFace"""
    log("=== STEP 4: Generating download script ===")

    script_lines = [
        "#!/bin/bash",
        "# Auto-generated by ComfyFixerSmart",
        f"# Generated: {datetime.now()}",
        "",
        "source ~/.secrets",
        "",
        f'MODELS_DIR="{COMFYUI_ROOT}/models"',
        "",
        "set -e  # Exit on error",
        ""
    ]

    for res in resolutions:
        target_dir = f"${{MODELS_DIR}}/{res['type']}"
        target_path = f"{target_dir}/{res['filename']}"

        # Handle subdirectories in filename (e.g., XL\model.safetensors)
        if '\\' in res['filename'] or '/' in res['filename']:
            # Extract subdirectory
            subdir = os.path.dirname(res['filename'].replace('\\', '/'))
            filename = os.path.basename(res['filename'])
            target_dir = f"{target_dir}/{subdir}"
            target_path = f"{target_dir}/{filename}"

        script_lines.append(f"# Source: {res.get('source', 'civitai')}")

        if res.get('source') == 'huggingface':
            # HuggingFace download
            script_lines.extend([
                f"echo 'Downloading from HuggingFace: {res['filename']}'",
                f"mkdir -p {target_dir}",
                f"# Using HuggingFace CLI",
                f"hf download {res['repo']} {res['file_path']} \\",
                f"  --local-dir {target_dir} \\",
                f"  --local-dir-use-symlinks False",
                "",
                f"# Alternative: Direct wget",
                f"# wget -O \"{target_path}\" \"{res['download_url']}\"",
                ""
            ])
        else:
            # Civitai download
            download_url = f"{res['download_url']}?token=${{CIVITAI_API_KEY}}"
            name_info = f"{res.get('civitai_name', 'Unknown')} - {res.get('version_name', 'Unknown')}"

            script_lines.extend([
                f"# {name_info}",
                f"echo 'Downloading from Civitai: {res['filename']}'",
                f"mkdir -p {target_dir}",
                f"wget -c \\",  # Removed --content-disposition (conflicts with -O)
                f"  --timeout=30 --tries=5 \\",
                f"  -O \"{target_path}\" \\",
                f"  \"{download_url}\"",
                ""
            ])

    script_path = f"{OUTPUT_DIR}/download_missing.sh"
    with open(script_path, 'w') as f:
        f.write('\n'.join(script_lines))

    os.chmod(script_path, 0o755)
    log(f"Download script saved: {script_path}")
    return script_path
```

## Testing Strategy

### Test Cases:

1. **Known Civitai Model**:
   - `ponyDiffusionV6XL_v6StartWithThisOne.safetensors`
   - Should find on Civitai with exact filename match

2. **Known HuggingFace Model**:
   - `rife49.pth`
   - Should skip to HuggingFace, find at hfmaster/models-moved

3. **Ambiguous Name**:
   - `bigLove_photo1.safetensors`
   - May need multiple query attempts on Civitai

4. **Malformed Filename**:
   - `big-love?modelVersionId=1990969 )`
   - Should detect as INVALID_FILENAME

5. **Not Found**:
   - `nonexistent_model_abc123.safetensors`
   - Should exhaust searches and return NOT_FOUND

### Manual Test Command:

```bash
# Test single model search
python3 -c "
import sys
sys.path.insert(0, '/home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart')
from comfy_fixer import search_civitai

model = {
    'filename': 'rife49.pth',
    'type': 'upscale_models',
    'node_type': 'UpscaleModelLoader'
}

result = search_civitai(model)
print(result)
"
```

## Security Considerations

### Filename Sanitization:

```python
import re

def sanitize_filename(filename):
    """Sanitize filename for safe use in bash/filesystem"""
    # Remove/replace dangerous characters
    safe = re.sub(r'[;&|`$(){}[\]<>"\']', '_', filename)
    # Limit length
    if len(safe) > 255:
        safe = safe[:255]
    return safe
```

### URL Validation:

```python
ALLOWED_DOMAINS = ['civitai.com', 'huggingface.co']

def validate_download_url(url):
    """Ensure download URL is from trusted domain"""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    return any(domain.endswith(allowed) for allowed in ALLOWED_DOMAINS)
```

## Rollback Plan

If Qwen integration fails, fallback to:
1. Keep old search_civitai logic as `search_civitai_simple()`
2. Add flag: `USE_QWEN_SEARCH = os.getenv('USE_QWEN_SEARCH', 'true').lower() == 'true'`
3. Toggle via environment variable

## Success Metrics

### Before (Current State):
- 21 models searched
- ~15 wrong matches (Pony Diffusion for everything)
- ~45GB wasted disk space
- Success rate: ~30%

### After (Target):
- 21 models searched
- Civitai matches: ~8 correct
- HuggingFace matches: ~4 correct
- NOT_FOUND: ~8 (manual sourcing needed)
- INVALID: ~1 (malformed filename)
- Success rate: ~60-70%
- Zero wrong downloads

## Implementation Timeline

1. **Phase 1** (30 min): Write improved search_civitai() with full prompt
2. **Phase 2** (15 min): Update generate_download_script() for HF support
3. **Phase 3** (30 min): Test with 5 known cases
4. **Phase 4** (15 min): Run full 21-model batch, review results
5. **Phase 5** (15 min): Adjust prompt based on failures, retest

**Total estimated time**: ~2 hours

## Next Steps

1. ✅ Write this plan document
2. ⏳ Implement improved search_civitai()
3. ⏳ Implement updated generate_download_script()
4. ⏳ Add import re to top of comfy_fixer.py
5. ⏳ Test with rife49.pth
6. ⏳ Test with ponyDiffusionV6XL
7. ⏳ Run full batch
8. ⏳ Analyze results and iterate

---

**Author**: Claude Code
**Date**: 2025-10-12
**Status**: READY FOR IMPLEMENTATION
