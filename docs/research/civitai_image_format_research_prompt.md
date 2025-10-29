# Research Agent Prompt: Civitai Image Format and Workflow Metadata

## Research Question

**Primary Question**: Does Civitai convert uploaded images to JPEG format, stripping PNG workflow metadata in the process?

**Secondary Questions**:
1. What image formats does Civitai accept for upload?
2. What image formats does Civitai serve in their gallery/API?
3. Does Civitai preserve PNG metadata chunks (tEXt/iTXt) where ComfyUI embeds workflow JSON?
4. Are there any official Civitai documentation or community discussions about this behavior?
5. Do users have methods to preserve/access original PNGs with workflow metadata on Civitai?

## Context

We performed empirical testing and found:
- Downloaded 10 images from Civitai API for model ID 611918
- All 10 images were JPEG format (`.jpeg` extension, JFIF metadata only)
- Available metadata keys: `['jfif', 'jfif_version', 'jfif_unit', 'jfif_density', 'exif', 'dpi']`
- **Zero PNG workflow metadata found**
- ComfyUI typically embeds workflow JSON in PNG 'workflow' or 'Workflow' chunks

This contradicts web research that suggested workflows ARE embedded in images shared on Civitai.

## Research Tasks

### Task 1: Official Civitai Documentation
Search for official Civitai documentation about:
- Image upload requirements and processing
- Supported image formats (upload vs serving)
- Image optimization/compression policies
- Metadata preservation policies
- Workflow sharing mechanisms

**Search queries**:
- "Civitai image format upload documentation"
- "Civitai PNG JPEG conversion"
- "Civitai workflow metadata"
- "Civitai image processing pipeline"
- site:github.com/civitai "image format" OR "image processing"
- site:civitai.com/wiki OR site:docs.civitai.com "image format"

### Task 2: Community Discussions
Search for community discussions about workflow sharing on Civitai:
- Reddit discussions about Civitai workflow extraction
- Civitai Discord/forum discussions about image formats
- GitHub issues on Civitai repository about metadata
- ComfyUI community discussions about Civitai integration

**Search queries**:
- "Civitai ComfyUI workflow extraction"
- "Civitai converts PNG to JPEG"
- "Civitai image metadata stripped"
- site:reddit.com/r/StableDiffusion "Civitai workflow metadata"
- site:reddit.com/r/comfyui "Civitai PNG JPEG"
- "how to extract ComfyUI workflow from Civitai image"

### Task 3: Technical Analysis
Research the technical implementation:
- Civitai's image CDN (image.civitai.com) behavior
- URL parameters that might affect format (?original=true, ?format=png, etc.)
- Civitai GitHub repository for image processing code
- Civitai API documentation about image endpoints

**Search queries**:
- "image.civitai.com URL parameters"
- site:github.com/civitai/civitai "image" "format" "optimization"
- "Civitai API images endpoint documentation"
- "Civitai original=true parameter"

### Task 4: Alternative Workflow Sharing Methods
Research how users actually share ComfyUI workflows on Civitai:
- Are workflows shared as separate "Workflow" model type?
- Are workflows shared in description/comments as JSON?
- Are workflows hosted externally (GitHub, Pastebin, etc.)?
- Do users upload both JPEG (for display) and PNG (for workflow) versions?

**Search queries**:
- "Civitai workflow model type"
- "how to share ComfyUI workflow on Civitai"
- "Civitai workflow JSON download"
- site:civitai.com/models type:Workflows

### Task 5: Test Case Verification
Find specific examples to test:
- Find a Civitai image that users claim has workflow metadata
- Find documentation or tutorials showing successful workflow extraction from Civitai
- Find counter-examples where workflow extraction worked
- Check if recent Civitai updates changed image handling

**Search queries**:
- "extract workflow from Civitai image tutorial"
- "drag and drop Civitai image ComfyUI workflow"
- "Civitai image workflow not working"
- "Civitai 2024 2025 image format change"

## Expected Findings Format

Please provide findings in this structure:

### Finding 1: Image Format Conversion
**Status**: CONFIRMED / DENIED / INCONCLUSIVE
**Evidence**:
- [URL/Source 1]: Description of finding
- [URL/Source 2]: Description of finding

**Summary**: 1-2 sentence conclusion

### Finding 2: Metadata Preservation
**Status**: CONFIRMED / DENIED / INCONCLUSIVE
**Evidence**:
- [URL/Source 1]: Description of finding
- [URL/Source 2]: Description of finding

**Summary**: 1-2 sentence conclusion

### Finding 3: Workflow Sharing Methods
**Actual methods used**:
- Method 1: [description]
- Method 2: [description]

**Evidence**:
- [URL/Source]: Description

### Finding 4: Community Workarounds
**If Civitai does convert to JPEG, how do users work around it?**
- Workaround 1: [description]
- Workaround 2: [description]

**Evidence**:
- [URL/Source]: Description

## Validation Criteria

Your research should answer:
1. ✅ **CONFIRMED**: Does Civitai convert images to JPEG? (YES/NO with evidence)
2. ✅ **CONFIRMED**: Does this strip PNG workflow metadata? (YES/NO with evidence)
3. ✅ **DOCUMENTED**: What are the official/unofficial workflow sharing methods on Civitai?
4. ✅ **ACTIONABLE**: If our hypothesis is correct, what should users do instead?

## Output Requirements

1. **Summary**: 2-3 paragraph executive summary of findings
2. **Evidence Table**: All sources with URLs, dates, and credibility assessment
3. **Contradictions**: Note any conflicting information found
4. **Confidence Level**: High/Medium/Low for each finding
5. **Recommendations**: Based on research, what should we do with our tooling?

## Time Box

- **Suggested time**: 30-45 minutes of research
- **Minimum sources**: 5 credible sources (official docs, GitHub, technical blogs)
- **Preferred sources**: Official Civitai documentation, GitHub repository code, recent community discussions (2024-2025)

## Additional Context for the Agent

**What we need to know**:
- Our automation tool (`batch_workflow_finder.py`) includes PNG extraction as a search strategy
- If Civitai always converts to JPEG, we should remove that strategy and update documentation
- If there's a way to get original PNGs (e.g., URL parameters), we should implement that
- If workflows are ONLY shared as separate "Workflow" models, our search-by-keyword strategy is correct

**Why this matters**:
- We don't want to build features that can never work
- We want to document accurate limitations for users
- We want to guide users to methods that actually work
- We spent significant time investigating PNG extraction and need to confirm if it's viable

## Success Criteria

Research is successful if it provides:
1. ✅ Definitive answer about JPEG conversion (with evidence)
2. ✅ Documentation of actual workflow sharing practices on Civitai
3. ✅ Technical explanation of why/how conversion happens (if it does)
4. ✅ Actionable recommendations for our tooling

---

**Agent Instructions**:
- Use WebSearch extensively
- Prioritize official sources and recent information (2024-2025)
- Look for technical implementation details, not just user anecdotes
- Cross-reference multiple sources for each finding
- Note the date of information (Civitai may have changed policies)
- If you find contradictions, investigate which is current/correct
