# ComfyUI Node Knowledge Base

This document provides grounding information for the Qwen agent about common ComfyUI nodes and their functions.

## Core Nodes

- **KSampler:** The primary node for generating images. It takes a model, positive and negative conditioning, a latent image, and various sampling parameters.
- **CheckpointLoaderSimple:** Loads a `.safetensors` or `.ckpt` model file. This is the starting point for most workflows.
- **CLIPTextEncode:** Takes a CLIP model and a text prompt and produces conditioning (`CONDITIONING`). This is used for both positive and negative prompts.
- **VAEDecode:** Decodes a latent image into a pixel-space image. This is usually the last step before saving the image.
- **VAEEncode:** Encodes a pixel-space image into a latent image. Used for image-to-image workflows.
- **SaveImage:** Saves an image to the output directory.
- **LoadImage:** Loads an image from the input directory.

## Custom Nodes (Commonly Used)

- **ControlNet:** A powerful class of nodes that allow for fine-grained control over image generation by providing an additional conditioning image (e.g., a canny edge map, a human pose estimation).
- **SAM (Segment Anything Model):** Used for object segmentation and masking.
- **RIFE (Real-time Intermediate Flow Estimation):** Used for frame interpolation and creating smooth animations.
