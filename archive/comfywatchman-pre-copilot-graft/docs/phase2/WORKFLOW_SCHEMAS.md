# Owner Workflow Schemas

## Overview
This document provides specifications for the owner-preferred workflow schemas. These schemas are not rigid standards but rather prescriptive guides for how common, complex workflows should be constructed to ensure consistency, quality, and maintainability.

They will be used by the LLM agents to:
*   Ground analysis of existing workflows.
*   Guide refactoring of workflows when requested.
*   Serve as templates for generating new workflows.

## 1. Auto-Inpaint Frontend

### Purpose
To provide a standardized, plug-and-play frontend for automatic masking and inpainting. This schema is designed to be swappable, allowing different object detectors or mask generation models to be used in the future.

### Core Components
1.  **Image Loader:** Loads the input image.
2.  **Object Detector / Mask Generator:**
    *   **Primary:** GroundingDINO for object detection based on a text prompt.
    *   **Alternative:** SAM (Segment Anything Model) for interactive or automatic mask generation.
    *   **Future:** Florence-2, etc.
3.  **Mask Processing:**
    *   Nodes to grow, shrink, or feather the generated mask to achieve better blending.
    *   A boolean switch to enable/disable mask processing.
4.  **Inpainting Model:**
    *   A dedicated inpainting checkpoint loader.
    *   The schema should recommend using specific, high-quality inpainting models.
5.  **Output:** The final inpainted image.

### Guardrails
*   The detector and the inpainting model should be compatible (e.g., SD1.5 inpainting model for an SD1.5-based workflow).
*   The input prompt for the detector should be clearly exposed as a primary input to the workflow.

## 2. Image-Cycling Frontend

### Purpose
To create workflows that can process a directory of images sequentially, applying a consistent set of transformations or analyses to each image. This is distinct from batch processing, as it processes images one at a time and can use the output of one run to influence the next.

### Core Components
1.  **Image Directory Loader:** A node that can read a list of image files from a specified directory.
2.  **Iterator/Selector:** A node that selects one image from the list based on a seed or index.
3.  **Dynamic Prompt Generator (Schema #3):** This sub-workflow is a key component, used to generate prompts based on the content of the current image.
4.  **Main Processing Chain:** The core image manipulation logic (e.g., upscaling, style transfer).
5.  **Seed/Index Incrementer:** A node that increments the seed or index after each run, ensuring that the next image in the sequence is processed on the next run.
6.  **Save Image:** Saves the processed image, often with a modified filename to indicate that it has been processed.

### Guardrails
*   The workflow should be designed to be run multiple times, with the state (the current index/seed) being managed externally or through a simple file-based state mechanism.
*   The workflow should handle the case where it reaches the end of the image list (e.g., by stopping or looping back to the beginning).

## 3. Dynamic Prompt Generator

### Purpose
A sub-workflow designed to be embedded within other workflows (like the Image-Cycling Frontend). It analyzes an input image and generates descriptive positive and negative prompts.

### Core Components
1.  **Image Tagger / Captioner:**
    *   **Primary:** A robust image tagging model (e.g., WD1.4 Tagger) to extract a set of descriptive tags.
    *   **Alternative:** An image-to-text model (e.g., BLIP) to generate a natural language caption.
2.  **LLM for Prompt Synthesis:**
    *   A local or API-based LLM (e.g., Qwen) that takes the tags or caption as input.
    *   The LLM is prompted to synthesize a high-quality positive prompt and a corresponding negative prompt based on the input and a desired style.
3.  **Prompt Output:**
    *   Two text outputs: one for the positive prompt and one for the negative prompt.
    *   These outputs are then wired into the main KSampler of the parent workflow.

### Guardrails
*   The LLM prompt should be carefully engineered to produce prompts in the desired format and style.
*   The sub-workflow should be clearly encapsulated, with a single image input and two text outputs.
*   A "passthrough" switch should be included to allow a user to disable the dynamic prompt generation and provide their own manual prompts.
