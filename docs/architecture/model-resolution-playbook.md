# Model Resolution Playbook (Agentic Guidance)

Date: 2025-10-19
Scope: ComfyFixerSmart model discovery and download guidance

This is a flexible, heuristic playbook for an agent to discover and retrieve missing models. It gives priorities and guardrails, not rigid steps. Respect the repository guardrails and ADR decisions at all times.

## Key guardrails

- RAG: Disabled locally. Do not build/store embeddings. If/when authorized, use only the external RAG backend via approved API.
- Destination: All downloads go under ${COMFYUI_ROOT}/models/\<type\>/ — never commit binaries to this repo.
- Failure-first: Abort if models_dir cannot be resolved or guardrails fail.
- Licensing: Enforce license allow-list. Unknown/disallowed licenses ⇒ manual review or block.

## Inputs the agent uses

- Workflow references: bare filenames (e.g., `sam_vit_b_01ec64.pth`), path-ish names (`PONY/Concepts/cheekpuff.safetensors`), or notes with URLs.
- Context: Node type that referenced the file (e.g., `LoraLoader`, `CheckpointLoaderSimple`, `UpscaleModelLoader`, `UltralyticsDetectorProvider`).
- Known families: SAM, RIFE/FILM/NMKD, Wan 2.1/2.2, YOLO/Ultralytics, Real-ESRGAN, etc.

## Priority of search sources (stop early when confident)

1) Civitai API (primary for community LoRAs/checkpoints)
   - Endpoint: [civitai.com/api/v1/models](https://civitai.com/api/v1/models) with query `?query=\<q\>&limit=\<n\>`
   - Resolve model by exact filename or base name; examine `modelVersions[].files[].downloadUrl` and `baseModel`.
   - Read model description and, if needed, page HTML to mine alternative names/aliases if API lacks comments.
   - Extract license from API payload or page; if unknown, keep confidence lower.
2) Mentions and aliases
   - Look for the reference across workflow notes, local docs, and provider pages/comments for alias names or forks.
   - Normalize names: replace spaces/underscores/dashes; trim prefixes/suffixes (e.g., `v1.0`, `fp16`).
3) Web search (broad sweep)
   - Query `<name> safetensors` and `<name> download`.
   - Prefer canonical domains (civitai.com, huggingface.co, github.com vendor releases, official vendor S3/CDNs). Avoid sketchy mirrors.
4) Hugging Face (especially for Wan, official orgs, repackaged model sets)
   - Search: [huggingface.co/api/models](https://huggingface.co/api/models) with `?search=\<q\>`
   - Inspect model card for license and file list; prefer orgs you trust (e.g., `Comfy-Org` for Wan).
5) Family-specific fallbacks (short-circuits)
   - SAM: Meta official S3 e.g., `dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth`.
   - RIFE / FILM / NMKD upscalers: GitHub Releases from official repos, or recognized HF mirrors.
   - Ultralytics YOLOv8: GitHub releases under `ultralytics/assets` (e.g., `yolov8m.pt`).
   - Real-ESRGAN: GitHub releases under `xinntao/Real-ESRGAN`.

## Signals to capture (for confidence rubric)

- Match quality: exact filename vs normalized.
- Source trust: domain/org in allow-list.
- License: allow-listed vs unknown/disallowed.
- Integrity: size, ETag, known SHA256 (when available).
- Context corroboration: workflow notes, family alignment, baseModel compatibility.
- Risk flags: takedowns, malware reports, sketchy mirrors.

## Flexible decision bands (see DP-002 for full rubric)

- Auto (FOUND): score ≥ 90, no red flags, license/source allowed, integrity corroborated.
- Manual (UNCERTAIN): score 60–89, or missing license/integrity, or minor discrepancies.
- Not Found / Blocked: score < 60, or disallowed license, or flagged source.

## Type inference (what folder to use)

- Use node type + filename extension + naming cues:
  - LoRA loaders → `loras/`
  - Checkpoint loaders → `checkpoints/`
  - VAE loaders → `vae/`
  - ControlNet → `controlnet/`
  - Upscale models (e.g., `*.pth` for ESRGAN/NMKD) → `upscale_models/`
  - Detectors (Ultralytics YOLO) → `bbox/` or provider’s expected tree under `models/`
- Cross-check against `config.model_type_mapping` to avoid misplacement.

## Primary download mechanisms (when cleared to proceed)

- Civitai: Use `files[].downloadUrl` with `CIVITAI_API_KEY` header if required. Prefer `.safetensors` over `.ckpt`.
- Hugging Face: Use `.../resolve/main/<path>` URLs. Add `Authorization: Bearer $HF_TOKEN` if needed for gated/private.
- GitHub Releases: Direct asset URLs resolved via 302 to signed CDN links; use `wget -c` to resume.
- Vendor official: Use documented URLs (e.g., Meta S3 for SAM) and verify headers.

## Operational guidelines (agentic)

- Normalize then fan-out: start with the exact name, then alias variants. Stop when a high-confidence candidate is found.
- Prefer canonical hosts and orgs; de-prioritize aggregators/mirrors.
- Mine descriptions/notes/comments for alternate names and base models.
- Record provenance: URLs tried, chosen URL, license snapshot, integrity hints, and decision score.
- Never place files in this repo. Generate a download script targeting ${COMFYUI_ROOT}/models/\<type\>/.

## Minimal agent trace template

- reference: \<string\>
- attempts: [ { source: civitai|hf|github|vendor|web, query: "...", url: "...", result: 200|404|timeout, notes: "..." } ]
- candidate: { url, type: lora|checkpoint|vae|upscale|detector, license, size, hash/etag }
- score: \<int\> (per DP-002); decision: AUTO|MANUAL|BLOCKED; rationale: ["signals..."]
- destination: ${COMFYUI_ROOT}/models/\<type\>/\<filename\>

## Examples (from current workflows)

- `sam_vit_b_01ec64.pth` → Vendor (Meta S3). Type: SAM model (detector/segmenter). Decision: Manual until license verified.
- `RealESRGAN_x4plus.pth` → GitHub Release (xinntao/Real-ESRGAN). Type: upscale_models. Decision: Manual until license verified.
- `wan_2.1_vae.safetensors` → HF `Comfy-Org/Wan_2.2_ComfyUI_Repackaged`. Type: vae. Decision: Manual until license verified.
- `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` → HF `Comfy-Org/Wan_2.2_ComfyUI_Repackaged`. Type: checkpoint/diffusion model. Decision: Manual (very large; require explicit confirmation and license check).

## Notes

- This playbook is compatible with the ADR backlog and combined ADR catalog; it adapts to future policy changes without code changes.
- Where APIs don’t expose comments, prefer parsing provider pages responsibly, but do not scrape to build a local RAG index.
