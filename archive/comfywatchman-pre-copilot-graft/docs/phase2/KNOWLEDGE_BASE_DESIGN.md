# Knowledge Base Design

## Overview
This document describes the structure and management of the plain-text, document-based Knowledge Base (KB) that will ground the LLM's reasoning.

## Core Principles
*   **Local and Private:** The entire KB will consist of Markdown files stored within the repository. No external databases or services will be used for knowledge storage.
*   **Human-Curated:** The content of the KB will be curated and maintained by the project owner to ensure accuracy and quality.
*   **Version Controlled:** All changes to the KB will be tracked through Git, providing a complete history of the knowledge.
*   **Simple Retrieval:** The initial retrieval mechanism will be based on keyword matching and simple file lookups. Semantic search using vector embeddings is deferred to Phase 3.

## Taxonomy and Structure
The KB will be organized into the following directory structure within `src/comfywatchman/knowledge/`:

```
knowledge/
├── nodes/
│   ├── samplers.md
│   ├── loaders.md
│   ├── upscalers.md
│   └── ...
├── models/
│   ├── checkpoints-sdxl.md
│   ├── loras-concepts.md
│   ├── controlnets.md
│   └── ...
├── workflows/
│   ├── inpainting-patterns.md
│   ├── upscaling-patterns.md
│   └── ...
└── schemas/
    ├── auto-inpaint-frontend.md
    ├── image-cycling-frontend.md
    └── dynamic-prompt-generator.md
```

### `nodes/`
*   **Purpose:** Contains documents explaining the function and common usage of different categories of ComfyUI nodes.
*   **Example (`samplers.md`):** Explanations of different samplers (Euler, DPM++, etc.), their trade-offs (speed vs. quality), and typical step counts.

### `models/`
*   **Purpose:** Provides context on different types of models, their purposes, and how to identify them.
*   **Example (`checkpoints-sdxl.md`):** Information about common SDXL base models, what they are good for, and how they differ from SD1.5 models.

### `workflows/`
*   **Purpose:** Documents common high-level patterns and techniques used in workflows.
*   **Example (`inpainting-patterns.md`):** Describes different approaches to inpainting, the nodes involved, and the expected results.

### `schemas/`
*   **Purpose:** Contains detailed specifications for the "Owner Workflow Schemas" mentioned in the vision document. These are prescriptive guides for how specific, complex workflows should be constructed.

## Content Sourcing Strategy
*   **Initial Content:** The initial content for the KB will be distilled from the existing research documents (`EXISTING_SYSTEMS.md`, `vision.md`) and from curated, high-quality community resources (e.g., tutorials, guides).
*   **Ongoing Updates:** The KB will be updated on an ad-hoc basis as new techniques, nodes, and models emerge. The project owner is responsible for curating and committing new content.

## Retrieval Patterns
The LLM-powered agents will use the KB in the following ways:

1.  **Keyword-Based Retrieval:** Before prompting the LLM for tasks like "explain workflow" or "search for model," the system will perform a simple keyword search across the KB documents. The content of the most relevant documents will be injected into the LLM's context.
2.  **Schema Grounding:** When a workflow is identified as matching one of the owner's schemas, the content of the corresponding schema document will be provided to the LLM to ground its analysis and recommendations.

## Versioning and Updates
The KB is part of the main codebase and will be versioned alongside it. Updates to the KB will be committed to the Git repository like any other code change, ensuring that the knowledge used by the agents is always in sync with the current version of the tool.
