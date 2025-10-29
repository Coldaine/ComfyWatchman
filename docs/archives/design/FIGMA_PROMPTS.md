# Figma Make Prompts for ComfyFixerSmart UI

This document contains three distinct, detailed prompts for generating UI concepts for the ComfyFixerSmart dashboard using an AI design tool like Figma Make. Each prompt is designed for a solo developer and prioritizes functionality, a strong aesthetic, and ease of implementation with a specified tech stack.

---

## Prompt 1: The Hive Mind (Hexagonal Grid)

**Core Function & User Flow:**
The primary goal of this interface is to provide a high-level, "at-a-glance" visual health check of my entire ComfyUI model library. The main user flow is: 1. See the entire "hive" of models immediately. 2. Instantly identify problems via color-coded glowing borders. 3. Filter the hive by model type to isolate specific assets. 4. Click on a model to see its details and which workflows it connects to in a side panel.

**Tech Stack & Component Library:**
-   **Framework:** React
-   **Styling:** Tailwind CSS
-   **Core Component:** The hexagonal grid should be the central element. For implementation, assume a library like `react-hexagon` could be used to generate the individual cells.

**Information Hierarchy & Layout:**
-   **Overall Layout:** A full-screen, single-page application.
-   **Header:** A minimal, fixed header containing the title "Model Hive" and the filter buttons.
-   **Main Content:** A zoomable, pannable canvas that contains the hexagonal grid.
-   **Details Panel:** A slide-out panel that appears from the right when a hexagon is selected.

**Key Interactive Components & Their States:**
-   **Hexagon Cell (The Model):**
    -   **Default State:** A dark gray hexagon containing a simple, white icon representing the model type (e.g., a brain for a checkpoint, a smaller shape for a LoRA).
    -   **Status States (Borders):**
        -   **Unused:** A soft, dim white glow.
        -   **Used & Ready:** A bright, solid green glow.
        -   **Missing but Required:** A slow, pulsing red glow.
    -   **Hover State:** The hexagon scales up slightly (1.1x) and a tooltip appears with the full model filename.
    -   **Selected State:** The hexagon's border turns a solid, bright cyan. All other hexagons dim to 50% opacity. Animated lines draw from the selected hex to the relevant workflow hexes.
-   **Workflow Cluster:**
    -   Workflows appear on the grid as larger, named hexagons. When a model is selected, lines connect to the relevant workflow hexes.
-   **Filter Buttons:**
    -   Simple toggle buttons for each model type (Checkpoint, LoRA, VAE, etc.).
    -   **Active State:** The button has a solid background color. When active, only hexes of that type remain at 100% opacity.

**Visual Theme & Aesthetic:**
-   **Reference:** The aesthetic should be a "cyberpunk HUD." Think of the interface from *Cyberpunk 2077* or *Blade Runner*.
-   **Color Palette:** A very dark (near black) background. Use bright, neon glows for the status states: `#00ff00` (green), `#ff0055` (red), and `#00ffff` (cyan for selection).
-   **Typography:** Use a clean, technical sans-serif font like 'Roboto Mono' or 'Fira Code'.

---

## Prompt 2: The Neural Network (Node Graph)

**Core Function & User Flow:**
The primary goal is to make the relationships and dependencies between models and workflows explicitly clear. The main flow is: 1. See all workflows as central nodes in a graph. 2. Immediately identify broken workflows by their red, dashed dependency lines. 3. Explore the graph by panning, zooming, and dragging nodes. 4. Switch to a "model-centric" view to see the impact of a single model across all workflows.

**Tech Stack & Component Library:**
-   **Framework:** React
-   **Styling:** Tailwind CSS
-   **Core Component:** The node graph is the entire interface. Generate code using the `react-flow` library, including its background and minimap components.

**Information Hierarchy & Layout:**
-   **Overall Layout:** A full-screen canvas for the graph.
-   **Toolbar:** A small, floating toolbar in the top-left corner with controls for "Zoom In," "Zoom Out," "Fit to View," and a toggle to switch between "Workflow View" and "Model View."
-   **Details Panel:** A slide-out panel that appears from the right when any node is clicked, showing its metadata.

**Key Interactive Components & Their States:**
-   **Workflow Node:**
    -   **Appearance:** A large, rectangular node with a distinct icon and the workflow's filename.
    -   **Status:** The node's border is green if all dependencies are met, and red if any are missing.
-   **Model Node:**
    -   **Appearance:** A smaller, circular node with an icon for the model type.
    -   **Status:** The node's border is solid if the file is present, and dashed if it is missing.
-   **Edge (The Connection Line):**
    -   **Appearance:** A simple, animated line that "flows" from the workflow to the model it requires.
    -   **Status:** The line is solid green if the model is available, and a dashed, glowing red if the model is missing.
-   **View Modes:**
    -   **Workflow View (Default):** Workflows are the primary nodes, connected to their required models.
    -   **Model View:** Models are the primary nodes. Clicking one highlights it and its connections to all the workflows that use it.

**Visual Theme & Aesthetic:**
-   **Reference:** The aesthetic should replicate **"GitHub's Dark Mode."**
-   **Color Palette:** Use GitHub's dark theme colors precisely: a dark gray background (`#0d1117`), lighter gray for nodes (`#161b22`), white/gray for text, green (`#238636`) for success/available states, and red (`#da3633`) for error/missing states.
-   **Typography:** Use a standard, clean sans-serif font like GitHub uses (e.g., Segoe UI, Helvetica).

---

## Prompt 3: The Engineer's Desk (Functional Brutalism)

**Core Function & User Flow:**
The goal is maximum information density, speed, and keyboard-driven efficiency. The flow is: 1. See a dense list of all workflows and their status. 2. Use the up/down arrow keys to navigate this list. 3. Instantly see the required models for the selected workflow appear in the adjacent panel. No mouse clicks are necessary for the primary task.

**Tech Stack & Component Library:**
-   **Framework:** React
-   **Styling:** Tailwind CSS
-   **Component Library:** None. Use raw, styled HTML elements to achieve the brutalist aesthetic. Do not use a pre-built library like Material UI or Shadcn/UI.

**Information Hierarchy & Layout:**
-   **Overall Layout:** A static, two-panel layout.
-   **Left Panel (40% width):** A scrollable list of all workflows. Contains a header indicating the view ("Workflows").
-   **Right Panel (60% width):** Displays the details of the workflow selected in the left panel.
-   **Navigation:** A simple text-based toggle at the top of the left panel to switch between "Workflows" and "Models" lists.

**Key Interactive Components & Their States:**
-   **List Item:**
    -   **Default State:** A single line of text.
    -   **Selected State:** The text line has a solid background color to indicate selection. The selection should be controllable via arrow keys.
    -   **Status Indicator:** Use text characters at the start of the line: `[✓]` for a ready workflow, `[✗]` for a workflow with missing models.
-   **Details Panel (Dependency Tree):**
    -   **Appearance:** This is a text-only view. It displays the dependencies of the selected item as an indented tree structure using ASCII-like characters.
    -   **Example Structure:**
        ```
        workflow_A.json
        └─ Requires:
           ├─ [✓] remacri_original.safetensors
           └─ [✗] missing_lora_v1.safetensors
        ```

**Visual Theme & Aesthetic:**
-   **Reference:** The aesthetic should be that of a modern terminal application like **"Warp"** or **"iTerm2"** using the **"Dracula"** color theme.
-   **Color Palette:** Use the Dracula theme colors: dark purple/gray background (`#282a36`), white/light gray foreground text (`#f8f8f2`), green for success (`#50fa7b`), red for error (`#ff5555`), and a brighter purple for selection highlights (`#bd93f9`).
-   **Typography:** Use a high-quality, monospaced font such as 'Fira Code', 'JetBrains Mono', or 'Source Code Pro'.
