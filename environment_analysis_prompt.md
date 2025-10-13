# Local Agent Prompt: ComfyUI Environment Analysis for Inpainting Workflow Enhancement

## Objective
Analyze the current ComfyUI environment to identify all available components needed for developing an enhanced inpainting workflow with automatic LLM prompt generation and smart masking capabilities.

## Environment Analysis Tasks

### 1. Custom Node Inventory
- List all installed ComfyUI custom nodes in the environment
- Identify nodes related to:
  - Inpainting (IP-Adapter, ControlNet, etc.)
  - Mask generation (SAM, Florence, etc.)
  - LLM integration (Ollama, OpenAI API, local models)
  - Image processing and enhancement
  - Batch processing capabilities
  - Face/hair/clothing specific tools

### 2. Model Inventory
- Catalog all available models in the ComfyUI models directory
- Categorize by type: checkpoints, LoRAs, VAEs, ControlNets, etc.
- Identify models specifically relevant to inpainting, masking, and enhancement
- Note file sizes and versions of key models

### 3. Current Workflow Files
- Locate and list all existing inpainting workflows (ALPHA_INPAINT, BATCH_INPAINT, etc.)
- Identify any related workflow files that might inform the design
- Note the structure and architecture of existing workflows

### 4. System Dependencies & Capabilities
- Check for installed LLM integration tools (Ollama, vLLM, etc.)
- Identify available Python libraries for SAM/Florence integration
- Verify GPU capabilities and VRAM availability
- Check for required dependencies and their versions

## Intelligence Gathering

### 1. Node Capabilities Assessment
- For each inpainting-related node, document:
  - Input/output specifications
  - Parameter options and ranges
  - Performance characteristics
  - Known limitations

### 2. Integration Possibilities
- Identify how different node types can be combined
- Note any dependencies between nodes
- Document recommended node sequences for optimal results

### 3. Existing Workflow Architecture
- Analyze the structure of current inpainting workflows
- Identify successful patterns and components
- Note any missing or problematic elements

### 4. Hardware Constraints
- Document current GPU specifications and VRAM
- Note any performance bottlenecks in existing workflows
- Identify optimization opportunities

## Required Output

### 1. Complete Environment Inventory
- List of all available custom nodes with brief descriptions
- Catalog of relevant models with file paths and specifications
- Summary of system capabilities and limitations

### 2. Feasibility Assessment
- Which requirements from the target workflow can be met with current nodes
- What components are missing or need to be installed
- Priority list of missing dependencies

### 3. Recommended Architecture
- Optimal node combinations based on current environment
- Workflow structure suggestions leveraging existing components
- Integration points between LLM, masking, and inpainting systems

### 4. Implementation Roadmap
- What can be built immediately with current components
- What needs to be installed/downloaded
- Order of implementation for maximum impact

## Key Questions to Address
1. What inpainting nodes are available and what are their strengths?
2. Which models are available for clothing/hair/object replacement?
3. What LLM integration options exist in the current environment?
4. How can SAM/Florence be integrated with the available nodes?
5. What are the performance characteristics of the current hardware?
6. Which existing workflow components should be preserved/reused?
7. What are the recommended node connection patterns for optimal results?

## Final Deliverable Format
- Executive summary of available components
- Detailed inventory with capabilities
- Recommended workflow architecture based on current capabilities
- Implementation plan with priority ranking
- Missing component identification and suggested replacements

## Success Criteria
- Complete inventory of all relevant components
- Clear understanding of what can be built with current environment
- Specific, actionable recommendations for workflow development
- Identification of any additional required installations
- Optimization suggestions for current resources