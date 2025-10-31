# ComfyUI Model Knowledge Base

This document provides grounding information for the Qwen agent about common ComfyUI model types and their typical locations.

## Model Types

- **Checkpoints (`.safetensors`, `.ckpt`):** These are the main generative models. They contain the bulk of the weights for the diffusion model.
  - **Location:** `ComfyUI/models/checkpoints/`
- **LoRAs (`.safetensors`):** Low-Rank Adaptations. These are small files that are used to modify the output of a checkpoint model, often to produce a specific character or style.
  - **Location:** `ComfyUI/models/loras/`
- **VAEs (`.pt`, `.safetensors`):** Variational Autoencoders. These are used to encode and decode images to and from the latent space. While many checkpoints have a VAE baked in, using a separate, higher-quality VAE can often improve the final image.
  - **Location:** `ComfyUI/models/vae/`
- **ControlNet Models (`.pth`, `.safetensors`):** These models are used with ControlNet custom nodes to provide additional conditioning to the generation process.
  - **Location:** `ComfyUI/models/controlnet/`
- **Upscale Models (`.pth`, `.pt`):** These models are used with upscaling nodes to increase the resolution of an image.
  - **Location:** `ComfyUI/models/upscale_models/`
- **Embeddings / Textual Inversions (`.pt`):** These are very small files that are used to add new concepts or styles to the model's vocabulary. They are referenced in prompts using the `embedding:` keyword.
  - **Location:** `ComfyUI/models/embeddings/`
