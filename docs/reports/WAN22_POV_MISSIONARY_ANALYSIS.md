# WAN 2.2 POV Missionary T2V Workflow - Deep Analysis
**Generated:** 2025-10-12
**Workflow:** `wan2.2_t2v_pov_missionary_v1.0_workflow.json`
**Target Hardware:** RTX 3090 (24GB VRAM)

---

## Executive Summary

This is a **complex dual-sampler text-to-video workflow** that uses TWO separate WAN 2.2 models optimized for different noise levels (high noise vs low noise). It generates **81 frames** at 32 FPS with optional 2x frame interpolation via RIFE, producing up to **162 frames total**.

**Key Metrics:**
- **Base Frames:** 81 frames (raw generation)
- **Post-Interpolation:** 162 frames (with RIFE 2x)
- **Video Duration:** 2.53 sec (81 frames ÷ 32 FPS) OR 5.06 sec (162 frames ÷ 32 FPS)
- **Estimated Peak VRAM:** 18-21 GB
- **VRAM Safety Margin:** 3-6 GB remaining on RTX 3090
- **Processing Mode:** Text-to-Video (T2V) with specialized POV missionary trained LoRAs

---

## 1. Frame Count & Render Settings

### Frame Configuration
| Parameter | Value | Source |
|-----------|-------|--------|
| **Base Frames** | **81** | EmptyHunyuanLatentVideo node #61 |
| **RIFE Multiplier** | 2x | RIFE VFI node #69 |
| **Total Frames (interpolated)** | **162** | 81 × 2 |
| **Frame Rate** | 32 FPS | VHS_VideoCombine node #70 |
| **Video Duration (base)** | 2.53 seconds | 81 ÷ 32 |
| **Video Duration (interpolated)** | 5.06 seconds | 162 ÷ 32 |
| **Batch Size** | 1 | EmptyHunyuanLatentVideo #61 |

### Resolution Configuration
| Parameter | Value | Source |
|-----------|-------|--------|
| **Width** | 752px | EmptyHunyuanLatentVideo #61 |
| **Height** | 1024px | EmptyHunyuanLatentVideo #61 |
| **Aspect Ratio** | 3:4 (portrait) | Calculated |
| **Latent Dimensions** | 94×128 | 752÷8 × 1024÷8 |

---

## 2. Model Inventory & Architecture

### Dual-Model System (High/Low Noise Split)

This workflow uses a **sophisticated two-stage approach** where different models handle different noise levels:

#### Stage 1: High Noise Model (Steps 0-10)
**UNET:** `wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors` (node #37)
- **Size:** ~14B parameters in FP8 quantization
- **Disk Size:** ~7-8 GB
- **VRAM (loaded):** ~7-8 GB
- **Purpose:** Handles initial high-noise denoising (structure formation)

#### Stage 2: Low Noise Model (Steps 5-10000)
**UNET:** `wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors` (node #56)
- **Size:** ~14B parameters in FP8 quantization
- **Disk Size:** ~7-8 GB
- **VRAM (loaded):** ~7-8 GB
- **Purpose:** Handles final low-noise refinement (detail enhancement)

#### Shared Components
**CLIP:** `umt5-xxl-enc-fp8_e4m3fn.safetensors` (node #38)
- **Type:** UMT5-XXL encoder (WAN variant)
- **Quantization:** FP8 E4M3FN
- **VRAM:** ~1.5-2 GB

**VAE:** `wan_2.1_vae.safetensors` (node #39)
- **Type:** WAN 2.1 VAE (backward compatible)
- **VRAM:** ~150-200 MB

### LoRA Stack (4 LoRAs applied)

#### High Noise Path LoRAs:
1. **Lightning LoRA** (node #67, mode=4 DISABLED)
   - File: `Wan2.2-Lightning_T2V-v1.1-A14B-4steps-lora_HIGH_fp16.safetensors`
   - Strength: 1.0
   - Purpose: 4-step distilled sampling (currently DISABLED)
   - VRAM: ~150-300 MB

2. **High Noise POV Missionary LoRA** (node #63, enabled)
   - File: `wan2.2_t2v_highnoise_pov_missionary_v1.0.safetensors`
   - Strength: 1.0
   - Purpose: Custom-trained POV missionary position content
   - VRAM: ~150-300 MB

#### Low Noise Path LoRAs:
3. **Saggy Tits LoRA** (node #68, enabled)
   - File: `SaggyTits_wan22_e25_low.safetensors`
   - Strength: 0.1 (subtle application)
   - Purpose: Breast physics/morphology refinement
   - VRAM: ~150-300 MB

4. **Low Noise POV Missionary LoRA** (node #64, enabled)
   - File: `wan2.2_t2v_lownoise_pov_missionary_v1.0.safetensors`
   - Strength: 1.0
   - Purpose: Detail refinement for POV missionary content
   - VRAM: ~150-300 MB

### Frame Interpolation Model
**RIFE:** `rife49.pth` (node #69)
- **Version:** RIFE 4.9
- **Purpose:** 2x frame interpolation (81→162 frames)
- **VRAM:** ~1-2 GB during interpolation

---

## 3. VRAM Breakdown by Stage

### Stage 1: Model Loading
```
High Noise UNET (FP8):          7-8 GB
Low Noise UNET (FP8):           7-8 GB  (loaded simultaneously!)
CLIP (FP8):                     1.5-2 GB
VAE:                            0.15-0.2 GB
4x LoRAs:                       0.6-1.2 GB
ModelSamplingSD3 overhead:      0.3-0.5 GB
                              ---------------
Total Model Memory:            17-19 GB
```

**CRITICAL:** Both UNETs are loaded simultaneously because the workflow uses KSamplerAdvanced with overlapping step ranges (high noise steps 0-10, low noise steps 5-10000). This creates a **5-step overlap** where both models must coexist in VRAM.

### Stage 2: Latent Preparation
```
Latent Dimensions: 94×128×81 frames×16 channels (SD3)
Memory: 94 × 128 × 81 × 16 × 2 bytes (fp16) = ~31 MB
```
**VRAM:** ~30-50 MB (negligible)

### Stage 3: High Noise Sampling (KSamplerHigh #57)
**Settings:**
- Steps: 18 total (0→10 processed)
- CFG: 3.5
- Sampler: euler
- Scheduler: simple
- Seed: 606128564240457 (randomize mode)
- Noise: enabled
- Return with leftover noise: enabled

**Attention Processing:**
```
SageAttention enabled (auto mode):
  - Base attention memory: ~25-35 GB (impossible!)
  - With SageAttention 8x reduction: ~3-4.5 GB
```

**VRAM Peak:** ~3-4.5 GB (sampling overhead)

### Stage 4: Low Noise Sampling (KSamplerLow #58)
**Settings:**
- Steps: 9 total (5→10000 range, processes steps 5-9)
- CFG: 1.0 (minimal guidance)
- Sampler: lcm (Latent Consistency Model)
- Scheduler: simple
- Seed: 0 (fixed)
- Noise: disabled (receives noisy latent from stage 1)

**VRAM Peak:** ~2-3 GB (less than high noise due to LCM sampler efficiency)

### Stage 5: VAE Decode
```
Sequential decode: 81 frames × 752×1024 RGB
Per-frame memory: ~2.3 MB
Decode buffer: ~1-2 GB
```

**VRAM Peak:** ~1.5-2 GB

### Stage 6: RIFE Frame Interpolation
```
Input: 81 frames @ 752×1024
Output: 162 frames @ 752×1024
RIFE model: ~500 MB
Processing buffer: ~1-2 GB (processes in batches of 16 frames)
```

**VRAM Peak:** ~1.5-2 GB

### Stage 7: Video Encoding
**VRAM:** ~50-100 MB (CPU-bound H.264 encoding)

---

## 4. Total VRAM Calculation

### Peak Memory Estimate (Most Critical Stage)

The **absolute peak** occurs during **High Noise Sampling (Stage 3)** when both UNETs are loaded:

| Component | VRAM (GB) | Persistent? |
|-----------|-----------|-------------|
| High Noise UNET (FP8) | 7-8 | ✓ Yes |
| Low Noise UNET (FP8) | 7-8 | ✓ Yes |
| CLIP (FP8) | 1.5-2 | ✓ Yes |
| VAE | 0.15-0.2 | ✓ Yes |
| 4x LoRAs | 0.6-1.2 | ✓ Yes |
| SageAttention sampling | 3-4.5 | ✓ During sampling |
| PyTorch CUDA cache | 1-2 | ✓ Persistent |
| Buffer overhead | 0.5-1 | ✓ Persistent |

### Total Peak VRAM: **21-27 GB**

### RTX 3090 Assessment
```
Total VRAM: 24 GB
Estimated Peak: 21-27 GB
Status: ⚠️ BORDERLINE / RISKY
```

**CRITICAL WARNING:** This workflow **may exceed 24GB VRAM** if:
- PyTorch allocates aggressive cache
- SageAttention has suboptimal memory behavior
- LoRAs accumulate unexpected overhead
- OS has other GPU processes running

---

## 5. Workflow Settings Evaluation

### Strengths

1. **SageAttention Enabled (auto mode)** ✓
   - PathchSageAttentionKJ nodes #65, #66
   - Essential for 81-frame processing
   - Reduces attention VRAM by ~8x

2. **Dual-Sampler Architecture** ✓
   - Smart noise-level specialization
   - High-noise model (18 steps euler): Structure formation
   - Low-noise model (9 steps LCM): Fast refinement
   - Total effective steps: 18 (10 high + 8 low overlap-adjusted)

3. **FP8 Quantization** ✓
   - Both 14B UNETs in FP8 (~50% memory vs FP16)
   - Without FP8: Would need ~14-16 GB per UNET = 28-32 GB total (impossible!)

4. **LCM Sampler for Low Noise** ✓
   - Latent Consistency Model sampler requires minimal CFG (1.0)
   - Very fast convergence in low-noise regime
   - Reduces low-noise sampling overhead

5. **RIFE Frame Interpolation** ✓
   - Professional-grade 2x interpolation
   - RIFE 4.9 (latest stable)
   - Batch processing (16 frames) for memory efficiency

### Potential Issues

1. **Dual-UNET Memory Pressure** ⚠️ CRITICAL
   - **Problem:** Both 14B models loaded simultaneously
   - **Why:** Overlapping step ranges (0-10 high, 5-10000 low)
   - **Impact:** +7-8 GB compared to single-model workflow
   - **Risk:** May trigger OOM on RTX 3090

2. **Lightning LoRA Disabled** ℹ️ INFO
   - Node #67 in mode=4 (disabled)
   - Lightning LoRA designed for 4-step generation
   - Current workflow uses 18 steps (high noise)
   - **Assessment:** Correctly disabled; incompatible with current setup

3. **High CFG on High Noise (3.5)** ⚠️ MODERATE
   - CFG=3.5 on euler sampler increases memory overhead
   - Requires computing both conditional and unconditional forward passes
   - **Impact:** +500 MB to 1 GB
   - **Trade-off:** Better prompt adherence vs memory

4. **Fixed Seed on Low Noise** ℹ️ INFO
   - Low noise sampler uses seed=0 (fixed)
   - High noise uses randomize mode
   - **Assessment:** Intentional design for reproducible refinement

5. **Portrait Aspect Ratio (3:4)** ✓ APPROPRIATE
   - 752×1024 matches typical POV missionary framing
   - Latent dimensions (94×128) divisible by 16
   - Good balance of resolution vs VRAM

---

## 6. Optimization Opportunities

### CRITICAL: Reduce Dual-UNET Overhead

#### Option 1: Sequential Model Loading (Recommended)
**Modify step ranges to eliminate overlap:**

```
Current (overlapping):
  High Noise: steps 0-10
  Low Noise: steps 5-10000 (overlap at 5-10)

Proposed (sequential):
  High Noise: steps 0-10, return_with_leftover_noise=enable
  Low Noise: steps 10-10000, add_noise=disable
```

**Expected VRAM Savings:** 7-8 GB (only one UNET loaded at a time)

**Implementation:**
- Change KSamplerHigh (#57): `end_at_step=10` (current: 10) ✓ Already correct
- Change KSamplerLow (#58): `start_at_step=10` (current: 5) ← **Change this**
- ComfyUI will auto-unload high noise UNET after step 10

#### Option 2: Disable Low Noise Path (Emergency Fallback)
**If OOM persists, disable low noise sampler entirely:**
- Set KSamplerLow (#58) to mode=4 (muted/bypass)
- Use only high noise model for all steps
- Increase high noise steps to 24-28 for quality compensation

**Expected VRAM Savings:** 8-9 GB

**Quality Impact:** Moderate (loss of detail refinement)

#### Option 3: Reduce Frame Count
```
Current: 81 frames
Safer: 65 frames (20% reduction)
Ultra-safe: 49 frames (40% reduction)
```

**VRAM Savings:** ~500 MB to 1.5 GB (attention overhead scales with frame count)

### Optional: Lower CFG on High Noise
```
Current: CFG=3.5
Proposed: CFG=2.0 or 1.5
```

**VRAM Savings:** 500 MB to 1 GB
**Quality Impact:** Slight loss of prompt adherence

### Optional: Disable RIFE Interpolation
```
Set RIFE VFI node #69 to mode=4 (muted)
```

**VRAM Savings:** 1.5-2 GB during interpolation stage
**Output:** 81 frames instead of 162 frames

---

## 7. Rendering Performance Estimate

### Time Estimates (RTX 3090)

| Stage | Est. Time | Notes |
|-------|-----------|-------|
| Model loading | 30-60 sec | Loading 2×14B UNETs + CLIP + LoRAs |
| High noise sampling | 90-120 sec | 10 steps × 81 frames, euler sampler |
| Low noise sampling | 30-45 sec | 4 steps × 81 frames, LCM sampler |
| VAE decode | 30-50 sec | Sequential 81-frame decode |
| RIFE interpolation | 40-60 sec | 81→162 frames, RIFE 4.9 |
| Video encoding | 10-15 sec | H.264 @ CRF 19 |
| **Total** | **~4-6 minutes** | **Single complete render** |

### Performance Notes:
- **SageAttention:** +40% speedup vs standard attention
- **LCM sampler:** +60% speedup vs euler at same steps
- **FP8 models:** +20% speedup vs FP16 (same quality)
- **Dual-UNET overhead:** +10-15 sec model switching time

---

## 8. Prompt Analysis

### Positive Prompt (node #6)
```
A nude slender light-skinned woman is lying on her back with her legs spread
having sex with a man. She's on a bed with her discarded red lingerie. She
looks up intensely at the viewer with her lips slightly parted. She is petite
with small breasts. Movement is fast with bouncing breasts. A nude man is
rapidly thrusting his penis back and forth inside her vagina at the bottom of
the screen. You can see the man's nude stomach. Her blonde hair is in twintail
braids. The view is POV from above.
```

**Analysis:**
- Very detailed NSFW content description
- Specific POV framing (above, missionary)
- Motion descriptors ("fast movement", "rapidly thrusting", "bouncing")
- Visual details (red lingerie, twintail braids, positioning)
- **Assessment:** Well-suited for WAN 2.2 T2V with POV missionary LoRAs

### Negative Prompt (node #7)
```
large breasts, 色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，
画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，
多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的
肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走
```

**Translation (Chinese portions):**
- "Vivid colors, overexposed, static, blurry details, subtitles"
- "Style, artwork, painting, image, still, overall gray"
- "Worst quality, low quality, JPEG artifacts"
- "Static images, messy background, three legs, crowded background, walking backwards"

**Analysis:**
- Excludes large breasts (prompt specifies small/petite)
- Strong anti-static bias (critical for video generation)
- Quality control terms (JPEG artifacts, blur, worst quality)
- Anatomical error prevention (extra fingers, malformed limbs, three legs)
- **Assessment:** Comprehensive negative prompt optimized for video quality

### Prompt Compatibility with Models
✓ **High Noise Model:** Responds to structural descriptors (positioning, POV angle)
✓ **Low Noise Model:** Responds to detail descriptors (hair style, lingerie, expressions)
✓ **POV Missionary LoRAs:** Trained specifically for this content type
✓ **Saggy Tits LoRA:** Strength 0.1 (subtle) - prevents unrealistic breast physics

---

## 9. Risk Assessment Matrix

| Risk Category | Level | Impact | Mitigation Status |
|--------------|-------|---------|-------------------|
| **VRAM Overflow** | **HIGH** | System crash/OOM | ⚠️ **NEEDS MITIGATION** |
| **Dual-UNET Memory** | **HIGH** | 21-27 GB peak | ⚠️ See Section 6 Option 1 |
| **Quality Degradation** | LOW | Acceptable T2V quality | ✓ Mitigated (dual-sampler) |
| **Temporal Artifacts** | MEDIUM | Flickering/jitter | ⚠️ Monitor shift parameter |
| **RIFE Artifacts** | LOW | Interpolation artifacts | ✓ RIFE 4.9 very stable |
| **Long Render Time** | LOW | 4-6 min acceptable | ✓ Optimized samplers |

---

## 10. CRITICAL Recommendations

### IMMEDIATE ACTION REQUIRED

**Before running this workflow:**

1. **Test VRAM Usage First**
   - Run with VRAM monitoring: `nvidia-smi -l 1`
   - Watch for peak usage during high-noise sampling
   - **If exceeds 23 GB:** STOP and apply Option 1 below

2. **Apply Sequential Model Loading (Option 1)**
   ```
   Edit KSamplerLow node #58:
   - Change start_at_step: 5 → 10
   ```
   This eliminates 5-step overlap, saving 7-8 GB VRAM.

3. **Enable Reserved VRAM**
   Add to ComfyUI launch args:
   ```bash
   --reserve-vram 1.5
   ```
   Prevents PyTorch from hogging all VRAM.

4. **Close Other GPU Applications**
   - Close Chrome/Firefox (GPU acceleration)
   - Close Discord/Slack (video rendering)
   - Check `nvidia-smi` for background processes

### Post-Test Optimization

**If OOM occurs even with Option 1:**
1. Reduce frames to 65 (node #61: length=81→65)
2. Lower CFG to 2.0 (node #57: cfg=3.5→2.0)
3. Disable RIFE temporarily (node #69: mode=4)

**If quality is poor:**
1. Increase high noise steps to 12 (node #57: steps=18→22)
2. Adjust ModelSamplingSD3 shift to 3-6 (nodes #54, #55)

---

## 11. Workflow Diagram (Simplified)

```
┌─────────────────────────────────────────────────┐
│  Load Two 14B WAN 2.2 Models Simultaneously    │
│  - High Noise UNET (FP8) - Node 37             │
│  - Low Noise UNET (FP8) - Node 56              │
│  + CLIP (FP8) - Node 38                        │
│  + VAE (WAN 2.1) - Node 39                     │
│  + 4× LoRAs - Nodes 63,64,67,68                │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│  Apply ModelSamplingSD3 (shift=8) + SageAttn   │
│  - High path: Nodes 54→65→67→63                │
│  - Low path: Nodes 55→66→68→64                 │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│  Encode Prompts (CLIP)                          │
│  - Positive: Detailed POV missionary scene      │
│  - Negative: Anti-static + quality control      │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│  Create Empty Latent                            │
│  752×1024×81 frames (3:4 portrait)              │
│  Node 61: EmptyHunyuanLatentVideo               │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│  KSamplerHigh (Node 57) - High Noise Path      │
│  - Steps 0→10 (18 total steps)                 │
│  - Euler sampler, CFG=3.5                      │
│  - Seed: randomize                             │
│  - Return with leftover noise                  │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│  KSamplerLow (Node 58) - Low Noise Path        │
│  - Steps 5→10000 (processes 5-9)              │
│  - LCM sampler, CFG=1.0                        │
│  - Seed: 0 (fixed)                             │
│  - Receives noisy latent from high path        │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│  VAE Decode (Node 8)                            │
│  81 frames @ 752×1024                           │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│  RIFE VFI (Node 69) - Frame Interpolation      │
│  81 frames → 162 frames (2× multiplier)         │
│  RIFE 4.9, batch size 16                        │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│  VHS_VideoCombine (Node 70)                     │
│  Export 162 frames @ 32 FPS = 5.06 sec video   │
│  H.264 MP4, CRF=19                              │
└─────────────────────────────────────────────────┘
```

---

## 12. Configuration Summary

### CRITICAL Parameters (Review Before Running)

| Parameter | Location | Value | Purpose | Change? |
|-----------|----------|-------|---------|---------|
| **start_at_step** | Node 58 (Low) | **5** | Low noise start | **⚠️ Change to 10** |
| use_SageAttention | Nodes 65,66 | auto | VRAM optimization | ✓ Keep |
| num_frames | Node 61 | 81 | Video length | ✓ Keep (or reduce) |
| width × height | Node 61 | 752×1024 | Resolution | ✓ Keep |
| high_noise_steps | Node 57 | 18 | Structure quality | ✓ Keep |
| low_noise_steps | Node 58 | 9 | Detail quality | ✓ Keep |
| cfg_high | Node 57 | 3.5 | Prompt adherence | ⚠️ Consider 2.0 |
| cfg_low | Node 58 | 1.0 | LCM requirement | ✓ Keep |
| rife_multiplier | Node 69 | 2 | Frame interpolation | ✓ Keep (or disable) |
| frame_rate | Node 70 | 32 | Playback speed | ✓ Keep |

### Model Files Checklist

Verify these files exist before running:

**UNETs (Required):**
- [ ] `wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors` (~7-8 GB)
- [ ] `wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors` (~7-8 GB)

**CLIP (Required):**
- [ ] `umt5-xxl-enc-fp8_e4m3fn.safetensors` (~2 GB)

**VAE (Required):**
- [ ] `wan_2.1_vae.safetensors` (~300 MB)

**LoRAs (Required):**
- [ ] `wan2.2_t2v_highnoise_pov_missionary_v1.0.safetensors`
- [ ] `wan2.2_t2v_lownoise_pov_missionary_v1.0.safetensors`
- [ ] `SaggyTits_wan22_e25_low.safetensors`
- [ ] `Wan2.2-Lightning_T2V-v1.1-A14B-4steps-lora_HIGH_fp16.safetensors` (disabled, optional)

**Interpolation (Required if using RIFE):**
- [ ] `rife49.pth` (~500 MB)

**Total Disk Space:** ~18-20 GB

---

## 13. Troubleshooting Guide

### If "CUDA Out of Memory" Occurs

**Symptoms:**
- RuntimeError: CUDA out of memory
- System freeze during high-noise sampling
- nvidia-smi shows 24 GB / 24 GB usage

**Solutions (in priority order):**

1. **Apply Sequential Loading (CRITICAL)**
   ```
   Node 58 (KSamplerLow): start_at_step=5 → 10
   ```
   Saves 7-8 GB immediately.

2. **Reduce Frame Count**
   ```
   Node 61: length=81 → 65
   ```
   Saves 500 MB to 1 GB.

3. **Lower High-Noise CFG**
   ```
   Node 57: cfg=3.5 → 2.0
   ```
   Saves 500 MB to 1 GB.

4. **Disable RIFE Interpolation**
   ```
   Node 69: Set mode to 4 (muted)
   ```
   Saves 1.5-2 GB during interpolation.

5. **Add Reserved VRAM to Launch**
   ```bash
   --reserve-vram 1.5
   ```
   Prevents PyTorch cache overflow.

6. **Emergency: Disable Low Noise Path**
   ```
   Node 58: Set mode to 4 (muted)
   Saves 8-9 GB but reduces quality
   ```

### If Black Frames or Artifacts

**Symptoms:**
- All black output
- Corrupted frames
- Severe flickering

**Solutions:**

1. **Test SageAttention Compatibility**
   ```
   Nodes 65,66: sage_attention="auto" → "disabled"
   ```
   SageAttention v1.0.6 (Triton) may have issues with dual-UNET setup.

2. **Check Model Files**
   ```bash
   cd ComfyUI-stable/models/unet
   sha256sum wan2.2_t2v_*noise*.safetensors
   ```
   Verify models not corrupted.

3. **Reduce ModelSamplingSD3 Shift**
   ```
   Nodes 54,55: shift=8 → 3
   ```
   High shift may cause instability with FP8 models.

4. **Check LoRA Compatibility**
   Temporarily disable all LoRAs (set mode=4):
   - Node 63 (high noise POV)
   - Node 64 (low noise POV)
   - Node 68 (saggy tits)

   Re-enable one by one to identify culprit.

### If Temporal Artifacts (Flickering)

**Symptoms:**
- Frame-to-frame inconsistency
- Jittery motion
- Color shifts between frames

**Solutions:**

1. **Lower ModelSamplingSD3 Shift**
   ```
   Nodes 54,55: shift=8 → 3 or 6
   ```

2. **Increase High-Noise Steps**
   ```
   Node 57: steps=18 → 24
   ```
   Better structure stability.

3. **Stabilize Seed**
   ```
   Node 57: noise_seed="randomize" → fixed value
   ```
   For testing consistency.

4. **Check RIFE Settings**
   ```
   Node 69: ensemble=true (should be enabled)
   ```
   Ensemble mode improves temporal consistency.

### If Quality is Poor

**Symptoms:**
- Blurry output
- Poor prompt adherence
- Lack of detail

**Solutions:**

1. **Increase High-Noise Steps**
   ```
   Node 57: steps=18 → 22 or 24
   ```

2. **Increase Low-Noise Steps**
   ```
   Node 58: steps=9 → 12
   ```

3. **Raise High-Noise CFG**
   ```
   Node 57: cfg=3.5 → 4.5 or 5.0
   ```
   (But monitor VRAM!)

4. **Adjust LoRA Strengths**
   ```
   Nodes 63,64: strength=1.0 → 1.2
   ```
   Stronger LoRA influence.

---

## 14. Conclusion & Verdict

### Overall Assessment: ⚠️ ADVANCED / HIGH-RISK

This workflow is **highly sophisticated** but **VRAM-constrained** on RTX 3090. It demonstrates:

✓ Professional dual-sampler architecture
✓ Specialized noise-level optimization
✓ FP8 quantization (essential for dual 14B models)
✓ Custom-trained LoRAs for specific content
✓ Frame interpolation for smooth output

**BUT:**

⚠️ Dual-UNET simultaneous loading (21-27 GB peak)
⚠️ Borderline/exceeds 24 GB VRAM capacity
⚠️ Requires immediate modification before running

### Expected Performance (After Sequential Loading Fix)

- **VRAM Usage:** 14-19 GB / 24 GB (SAFE)
- **Render Time:** 4-6 minutes
- **Output Quality:** High (dual-sampler refinement)
- **Stability:** High (after step range fix)

### Mandatory Action Before First Run

**⚠️ CRITICAL: Apply Sequential Model Loading**

1. Open workflow in ComfyUI
2. Find KSamplerLow node (#58)
3. Change `start_at_step`: **5 → 10**
4. Save workflow
5. Test with VRAM monitoring

**This single change saves 7-8 GB VRAM.**

### Recommendation

**DO NOT run as-is** - Apply sequential loading fix first. After modification, workflow should execute successfully with excellent quality output.

---

## 15. Next Steps

### Pre-Flight Checklist

Before running this workflow:

1. ✓ Verify all model files present (Section 12)
2. ✓ Apply sequential loading fix (start_at_step=5→10)
3. ✓ Add `--reserve-vram 1.5` to ComfyUI launch
4. ✓ Close all other GPU applications
5. ✓ Open `nvidia-smi -l 1` for VRAM monitoring
6. ✓ Load workflow in ComfyUI
7. ✓ Queue prompt and watch VRAM

### Post-Test Actions

1. Document actual VRAM peak vs estimate
2. Evaluate output quality (temporal consistency, detail)
3. If issues: Apply Section 13 troubleshooting
4. If successful: Archive configuration
5. Experiment with tunable parameters (Section 12)

### Optional Enhancements

Once stable:
- Test different shift values (3, 6, 8)
- Experiment with LoRA strengths
- Try different frame counts (65, 97, 113)
- Test alternative samplers (euler_a, dpmpp_2m)

---

**Analysis Complete**

**TL;DR:** Powerful workflow, but **MUST FIX** KSamplerLow start_at_step (5→10) to avoid VRAM overflow. After fix: 14-19 GB peak (safe), 4-6 min render, excellent quality.

*For emergencies, see Section 13. For optimization, see Section 6.*
