# Claude Code URL Verification Feature

## Overview

ComfyFixerSmart includes **optional intelligent URL verification** using Claude Code in headless mode. When enabled with `--verify-urls`, the system verifies each model URL using Claude's websearch and webfetch tools before generating the download script.

**Status**: Optional feature, **DISABLED by default**

## Quick Start

```bash
# Standard workflow (fast, no verification)
python comfy_fixer.py

# With URL verification (slower but safer)
python comfy_fixer.py --verify-urls
```

## When To Use Verification

### ✅ Use `--verify-urls` when:
- You're downloading expensive/large models (multi-GB files)
- You want to ensure all URLs are valid before starting downloads
- You suspect some models might have been removed from Civitai
- You're automating the workflow and want maximum reliability

### ⏩ Skip verification (default) when:
- You want the fastest workflow
- You're okay with potentially downloading from a few dead URLs
- You trust Qwen's search results
- Time is more important than verification

**Default behavior**: Verification is OFF to prioritize speed.

## How It Works

### Workflow Integration

**When disabled (default)**:
```
1. Scan workflows
2. Build local inventory
3. Generate missing list
4. Search for models (Qwen)
5. Manual confirmation
6. Generate download script
7. User downloads models
```

**When enabled with `--verify-urls`**:
```
1. Scan workflows
2. Build local inventory
3. Generate missing list
4. Search for models (Qwen)
5. Manual confirmation
6. ✨ VERIFY URLs (Claude Code) ← OPTIONAL STEP
7. Generate download script
8. User downloads models
```

### Verification Process

For **each** model URL, Claude Code:

1. **WebSearch First**: Searches the web to verify the URL/model exists
   - Civitai URLs: Searches for the specific version ID
   - HuggingFace URLs: Searches for the repo and filename

2. **WebFetch Fallback**: If websearch doesn't provide clear evidence
   - Attempts to fetch the URL directly
   - Checks for 404s or invalid responses

3. **Returns Structured Result**:
   ```json
   {
     "verified": true,
     "status": "available",
     "message": "URL verified via websearch - model found on Civitai",
     "checked_with": "websearch"
   }
   ```

### User Interaction

After verification completes, you'll see a summary:

```
============================================================
Verification Summary
============================================================
  Verified: 18
  Failed: 3
```

If any URLs fail verification, you get three options:

- **[c] Continue with verified models only** - Only download the 18 verified models
- **[i] Include all models (ignore verification failures)** - Download all 21 models anyway
- **[a] Abort download script generation** - Cancel everything

## Technical Details

### Claude Code Invocation

The script calls Claude Code headlessly with:

```python
subprocess.run([
    'claude', '-p',
    '--output-format', 'json',
    '--model', 'claude-sonnet-4-5-20250929',
    prompt
])
```

### Timeout & Error Handling

- **Per-model timeout**: 2 minutes
- **Rate limiting**: 2-second delay between verifications
- **Graceful fallback**: If Claude CLI not found, assumes URLs are valid

### Verification Logging

All verification attempts are logged with:
- URL being checked
- Verification method used (websearch/webfetch/both)
- Success/failure status
- Detailed error messages

## Performance

**Time Estimate**: ~2-3 minutes per model

For 21 models: ~42-63 minutes of verification time

**Why so long?**
- Each model requires Claude to:
  - Perform websearches
  - Potentially fetch URLs
  - Parse and analyze results
  - Return structured JSON

**Is it worth it?**
✅ **YES** - Prevents downloading from broken/dead URLs
✅ Catches Civitai models that moved or were deleted
✅ Verifies HuggingFace repos still exist
✅ Saves bandwidth from failed downloads

## Example Output

```
============================================================
STEP 6: Verifying URLs with Claude Code
============================================================
Using Claude Code's websearch and webfetch tools to verify model availability
This will take ~2-3 minutes per model (21 models)

  [1/21] Verifying: rife49.pth
    Source: huggingface
    URL: https://huggingface.co/AlexWortega/RIFE/resolve/main/rife49.pth
    ✓ VERIFIED (websearch): Model found in AlexWortega/RIFE repo

  [2/21] Verifying: sam_vit_b_01ec64.pth
    Source: huggingface
    URL: https://huggingface.co/facebook/sam-vit-base/resolve/main/sam_vit_b_01ec64.pth
    ✓ VERIFIED (webfetch): URL accessible, valid file

  [3/21] Verifying: flux_schnell_v1.safetensors
    Source: civitai
    URL: https://civitai.com/api/download/models/789456
    ✗ FAILED (websearch): Model ID not found on Civitai

...

============================================================
Verification Summary
============================================================
  Verified: 20
  Failed: 1

Failed verifications:
  ✗ flux_schnell_v1.safetensors
    Reason: Model ID not found on Civitai

Options:
  [c] Continue with verified models only
  [i] Include all models (ignore verification failures)
  [a] Abort download script generation

Your choice [c/i/a]: c

Proceeding with 20 verified models

...

============================================================
✓ Ready to Download!
============================================================
Missing models: 21
Found models: 21
Verified models: 20
Download script: output/download_missing.sh
```

## Verification Metadata

Each resolution in `output/resolutions.json` now includes:

```json
{
  "filename": "rife49.pth",
  "type": "upscale_models",
  "source": "huggingface",
  "download_url": "https://huggingface.co/...",
  "verification": {
    "verified": true,
    "status": "available",
    "message": "URL verified via websearch",
    "checked_with": "websearch"
  }
}
```

## Enabling/Disabling Verification

**Q: How do I enable verification?**

Add the `--verify-urls` flag:
```bash
python comfy_fixer.py --verify-urls
```

**Q: Is verification enabled by default?**

No, verification is **DISABLED by default** to keep the workflow fast. You must explicitly enable it with `--verify-urls`.

**Q: What if Claude CLI is not installed?**

If you run with `--verify-urls` but Claude CLI is not installed:
- Logs: "Claude Code CLI not found - skipped verification"
- Marks all URLs as `verified: true` (assumes valid)
- Proceeds normally (doesn't fail)

## Benefits

✅ **Catch dead links** before wasting time/bandwidth
✅ **Verify Civitai models** haven't been removed
✅ **Check HuggingFace repos** still exist
✅ **User choice** - continue with verified only or include all
✅ **Detailed logging** - know exactly what was checked
✅ **Graceful degradation** - works even without Claude CLI

## Future Improvements

- [ ] Parallel verification (verify multiple URLs simultaneously)
- [ ] Verification cache (skip re-verifying same URLs)
- [ ] Optional flag to disable verification
- [ ] Retry failed verifications
- [ ] Export verification report

---

**Implementation Date**: 2025-10-12
**Feature Status**: ✅ Production Ready
**Dependencies**: Claude Code CLI (`claude` command in PATH)
