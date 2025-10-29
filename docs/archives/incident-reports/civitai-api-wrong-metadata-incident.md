# Civitai API Incident Report: Wrong Image Metadata Retrieved

**Date:** 2025-10-23
**Image URL:** https://civitai.com/images/96712457
**Severity:** Medium - Led to incorrect workflow creation

---

## Summary

When attempting to retrieve workflow metadata for Civitai image ID `96712457`, the Civitai Images API returned metadata for a completely different image (ID `9173928`), leading to creation of an incorrect workflow with wrong parameters, models, and prompts.

---

## Timeline of Events

### 1. Initial Request
- **Target:** Image ID `96712457` (WoW Blood Elf - Pony Diffusion)
- **Method:** Direct API call to `/api/v1/images/96712457`
- **Result:** 404 Not Found

### 2. Fallback Approach
- **Method:** WebFetch HTML page content
- **Finding:** Discovered `postId: 21452546` in page metadata
- **Issue:** No direct image metadata found in HTML

### 3. Alternative API Query
```bash
curl -H "Authorization: Bearer $CIVITAI_API_KEY" \
  "https://civitai.com/api/v1/images?ids=96712457&limit=1"
```

**Response:** Returned image ID `9173928` instead of `96712457`

### 4. The Critical Mistake
**What I did:**
- Received API response with different image ID
- **Failed to validate** that returned `id: 9173928` ≠ requested `id: 96712457`
- Proceeded to use metadata from wrong image

**Wrong Metadata Retrieved:**
```json
{
  "id": 9173928,
  "meta": {
    "prompt": "AtomicHeartTwinsCosplay in absolute darkness...",
    "seed": 1938345220,
    "steps": 45,
    "cfgScale": 5,
    "sampler": "DPM++ 2M",
    "civitaiResources": [
      {"type": "checkpoint", "modelVersionId": 345685},
      {"type": "lora", "weight": 0.8, "modelVersionId": 426333}
    ]
  }
}
```

This was for an **Atomic Heart Twins** image, not the requested WoW Blood Elf image.

### 5. User Correction
User provided actual metadata showing completely different parameters:

**Correct Metadata:**
```
Prompt: score_9, score_8_up, score_7_up, score_6_up, masterpiece...
        mature blood elf, World of Warcraft, 1girl...
Steps: 30
CFG: 3
Seed: 1716271426
Checkpoint: Pony Diffusion XL
```

---

## Root Causes

### 1. **API Behavior Issue**
The Civitai Images API with `?ids=` parameter returned a different image instead of:
- Returning empty results
- Returning an error
- Indicating the requested ID doesn't exist

This is either:
- A bug in Civitai's API
- Intentional fallback behavior (undocumented)
- Image ID 96712457 was deleted/restricted and API returned a "similar" image

### 2. **Missing Validation**
**Critical flaw in my approach:**
```python
# What I did:
response = api.get("images?ids=96712457")
result = response.json()['items'][0]
# Used result without checking result['id'] == 96712457

# What I should have done:
response = api.get("images?ids=96712457")
result = response.json()['items'][0]
if result['id'] != 96712457:
    raise ValueError(f"API returned wrong image: {result['id']}")
```

### 3. **Insufficient Error Handling**
- Did not check if API returned empty results
- Did not verify response data matched request
- Assumed API would return correct image or fail cleanly

---

## Consequences

1. **Downloaded Wrong Models:**
   - atomic_heart_twins.safetensors (218MB)
   - xl_weapon_orbstaff.safetensors (218MB)
   - Multiple other LoRAs for wrong image style

2. **Created Wrong Workflow:**
   - SDXL checkpoint instead of Pony Diffusion
   - CFG: 5, Steps: 45 instead of CFG: 3, Steps: 30
   - Completely different prompt and style

3. **Wasted Resources:**
   - ~1GB of incorrect model downloads
   - Time spent creating wrong workflow
   - User had to manually provide correct parameters

---

## Lessons Learned

### For Future Implementation

1. **Always Validate API Responses:**
```python
def fetch_civitai_image(image_id: int) -> dict:
    """Fetch image with validation."""
    response = requests.get(f"https://civitai.com/api/v1/images?ids={image_id}")
    data = response.json()

    if not data['items']:
        raise NotFoundError(f"Image {image_id} not found")

    result = data['items'][0]

    # CRITICAL: Validate returned ID matches requested ID
    if result['id'] != image_id:
        raise ValueError(
            f"API returned wrong image. "
            f"Requested: {image_id}, Got: {result['id']}"
        )

    return result
```

2. **Better Error Messages:**
```python
# Before
return SearchResult(status='NOT_FOUND', filename=filename)

# After
return SearchResult(
    status='NOT_FOUND',
    filename=filename,
    error_message=f"Image {image_id} not found on Civitai. "
                  f"It may have been deleted or is restricted."
)
```

3. **Implement Sanity Checks:**
```python
def validate_workflow_metadata(requested_url: str, metadata: dict) -> bool:
    """Basic sanity checks on retrieved metadata."""

    # Check for Pony Diffusion indicators
    if 'score_9' in metadata.get('prompt', ''):
        if metadata.get('cfgScale', 0) > 4:
            warnings.warn("Pony workflows typically use CFG 2-4")

    # Check for SDXL vs Pony checkpoint mismatch
    # etc.
```

4. **Log API Responses:**
```python
logger.debug(f"Requested image ID: {image_id}")
logger.debug(f"Received image ID: {result['id']}")
logger.debug(f"Image URL: {result.get('url')}")
```

---

## Recommendations

### Short Term
1. Add validation to `CivitaiSearch` class in `src/comfyfixersmart/search.py`
2. Create utility function `validate_civitai_response()` in `utils.py`
3. Document known API quirks in `docs/technical/integrations.md`

### Long Term
1. Consider creating a Civitai API wrapper class with built-in validation
2. Implement caching of API responses with metadata for debugging
3. Add integration tests that catch ID mismatches
4. Create a "verify mode" that shows user metadata before downloading

---

## Related Issues

- Civitai API lacks comprehensive error codes
- `/api/v1/images/{id}` returns 404, but `/api/v1/images?ids={id}` returns wrong data
- No way to verify if image is deleted vs restricted vs never existed
- API documentation doesn't mention fallback behavior

---

## Action Items

- [ ] Add ID validation to search.py
- [ ] Create test case for this scenario
- [ ] Document Civitai API quirks
- [ ] Update download_workflow.py script with validation
- [ ] Add "--verify" flag to CLI for metadata preview

---

## Appendix: API Comparison

| Method | Requested ID | Returned ID | Status | Correct? |
|--------|-------------|-------------|---------|----------|
| `/api/v1/images/96712457` | 96712457 | N/A | 404 | N/A |
| `/api/v1/images?ids=96712457` | 96712457 | 9173928 | 200 | ❌ NO |
| `/api/v1/images?postId=21452546` | via post | 9173928 | 200 | ❌ NO |
| User provided metadata | 96712457 | 96712457 | - | ✅ YES |

---

**Conclusion:** This incident highlights the importance of defensive programming when working with external APIs. Never assume API responses are correct - always validate, especially when dealing with user-provided URLs or IDs.
