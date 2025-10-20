#!/bin/bash
# Download script for kacey-f1-inpaining-v1.0-workflow.json models
# Generated: 2025-10-12

set -Eeuo pipefail

# Resolve COMFYUI_ROOT with guardrails (AGENTS.md)
COMFYUI_ROOT_DEFAULT="/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable"
COMFYUI_ROOT="${COMFYUI_ROOT:-$COMFYUI_ROOT_DEFAULT}"
MODELS_ROOT="${COMFYUI_ROOT}/models"

if [[ ! -d "$MODELS_ROOT" ]]; then
    echo "❌ Models directory not found: $MODELS_ROOT" >&2
    echo "Set COMFYUI_ROOT or create the directory. Aborting per failure-first policy." >&2
    exit 1
fi

if ! command -v wget >/dev/null 2>&1; then
    echo "❌ wget not found in PATH. Please install wget." >&2
    exit 1
fi

echo "=============================================="
echo "Downloading Models for Kacey F1 Inpainting Workflow"
echo "=============================================="

# Create directories
mkdir -p "$MODELS_ROOT/unet"
mkdir -p "$MODELS_ROOT/clip"
mkdir -p "$MODELS_ROOT/vae"
mkdir -p "$MODELS_ROOT/sams"
mkdir -p "$MODELS_ROOT/grounding-dino"

# Track progress
SUCCESS=0
FAILED=0
TOTAL=5

# 1. Flux UNET (fp8) - 11GB
echo ""
echo "[1/$TOTAL] Downloading flux1-dev-fp8.safetensors (11GB)..."
if wget -c --progress=bar:force \
    -O "$MODELS_ROOT/unet/flux1-dev-fp8.safetensors" \
    "https://huggingface.co/Kijai/flux-fp8/resolve/main/flux1-dev-fp8.safetensors"; then
    echo "✓ Success: flux1-dev-fp8.safetensors"
    ((SUCCESS++))
else
    echo "✗ Failed: flux1-dev-fp8.safetensors"
    ((FAILED++))
fi

# 2. T5-XXL Text Encoder (fp8) - 4.89GB
echo ""
echo "[2/$TOTAL] Downloading t5xxl_fp8_e4m3fn.safetensors (4.89GB)..."
if wget -c --progress=bar:force \
    -O "$MODELS_ROOT/clip/t5xxl_fp8_e4m3fn.safetensors" \
    "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors"; then
    echo "✓ Success: t5xxl_fp8_e4m3fn.safetensors"
    ((SUCCESS++))
else
    echo "✗ Failed: t5xxl_fp8_e4m3fn.safetensors"
    ((FAILED++))
fi

# 3. Flux VAE - 335MB
echo ""
echo "[3/$TOTAL] Downloading ae.safetensors (335MB)..."
if wget -c --progress=bar:force \
    -O "$MODELS_ROOT/vae/ae.safetensors" \
    "https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/ae.safetensors"; then
    echo "✓ Success: ae.safetensors"
    ((SUCCESS++))
else
    echo "✗ Failed: ae.safetensors"
    ((FAILED++))
fi

# 4. SAM HQ (ViT-H) - 2.57GB
echo ""
echo "[4/$TOTAL] Downloading sam_hq_vit_h.pth (2.57GB)..."
if wget -c --progress=bar:force \
    -O "$MODELS_ROOT/sams/sam_hq_vit_h.pth" \
    "https://huggingface.co/lkeab/hq-sam/resolve/main/sam_hq_vit_h.pth"; then
    echo "✓ Success: sam_hq_vit_h.pth"
    ((SUCCESS++))
else
    echo "✗ Failed: sam_hq_vit_h.pth"
    ((FAILED++))
fi

# 5. GroundingDINO SwinB - 938MB
echo ""
echo "[5/$TOTAL] Downloading GroundingDINO_SwinB (938MB)..."
if wget -c --progress=bar:force \
    -O "$MODELS_ROOT/grounding-dino/groundingdino_swinb_cogcoor.pth" \
    "https://huggingface.co/ShilongLiu/GroundingDINO/resolve/main/groundingdino_swinb_cogcoor.pth"; then
    echo "✓ Success: groundingdino_swinb_cogcoor.pth"
    ((SUCCESS++))
else
    echo "✗ Failed: groundingdino_swinb_cogcoor.pth"
    ((FAILED++))
fi

# Download GroundingDINO config file
echo ""
echo "Downloading GroundingDINO config file..."
if wget -c --progress=bar:force \
    -O "$MODELS_ROOT/grounding-dino/GroundingDINO_SwinB.cfg.py" \
    "https://huggingface.co/ShilongLiu/GroundingDINO/resolve/main/GroundingDINO_SwinB.cfg.py"; then
    echo "✓ Success: GroundingDINO_SwinB.cfg.py"
else
    echo "⚠ Warning: Config file download failed (may auto-download later)"
fi

# Summary
echo ""
echo "=============================================="
echo "Download Summary"
echo "=============================================="
echo "Successful: $SUCCESS/$TOTAL"
echo "Failed: $FAILED/$TOTAL"
echo ""
echo "Models saved to: $MODELS_ROOT"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✓ All downloads completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Load the workflow in ComfyUI"
    echo "2. Workflow location: $MODELS_ROOT/../user/default/workflows/kacey-f1-inpaining-v1.0-workflow.json"
    exit 0
else
    echo "⚠ Some downloads failed. You can re-run this script to retry."
    exit 1
fi
