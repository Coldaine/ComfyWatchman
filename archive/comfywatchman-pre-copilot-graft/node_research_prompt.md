# ComfyUI Node Research Agent Prompt: Advanced Inpainting Workflow Development

## Objective
Analyze existing inpainting workflows (ALPHA_INPAINT and BATCH_INPAINT) and develop an enhanced inpainting workflow for clothing replacement, hair styling, and general object replacement with automatic LLM prompt generation and smart masking.

## Research Tasks

### 1. Current Workflow Analysis
- Read and analyze the existing ALPHA_INPAINT and BATCH_INPAINT workflows
- Identify all nodes, their functions, and connections
- Document the current architecture, strengths, and limitations
- Note any existing automatic prompt or masking components

### 2. Available Node Inventory
- Catalog all available inpainting-related nodes in the ComfyUI setup
- Identify nodes for:
  - Mask generation (SAM, Florence, etc.)
  - LLM integration for prompt generation
  - Image processing and inpainting
  - Batch processing capabilities
  - Face/hair/clothing specific tools

### 3. Node Capability Assessment
- Determine which nodes support automatic prompt generation
- Identify nodes that integrate with LLMs for positive/negative prompt creation
- Find nodes that support SAM and Florence for intelligent masking
- Locate nodes optimized for clothing/hair replacement tasks

## Target Workflow Specifications

### Core Requirements
1. **Smart Masking System**
   - Automatic mask generation using SAM and/or Florence
   - Clothing-specific detection and masking
   - Hair-specific detection and masking
   - General object replacement masking capability

2. **LLM-Powered Prompt Generation**
   - Automatic positive prompt creation based on mask content
   - Automatic negative prompt creation to preserve context
   - Style transfer capabilities (e.g., swimwear style → dress style)
   - Context-aware prompting to maintain image coherence

3. **Flexible Replacement Options**
   - Clothing replacement (swimsuits, dresses, tops, etc.)
   - Hair style changes
   - General object replacement
   - Style transfer within masked regions

4. **Scalable Architecture**
   - Support for both single-image and batch processing
   - Performance optimization for real-time or near real-time operation
   - Extensibility for future enhancement

### Node Integration Requirements
- Identify and integrate the best available nodes for each component
- Leverage existing workflow architecture where beneficial
- Propose new node combinations for enhanced functionality
- Ensure compatibility with current ComfyUI setup

## Deliverable Requirements

### 1. Node Configuration Documentation
- Detailed list of required nodes with parameters
- Node connection blueprint
- Workflow execution order specification
- Input/output mapping for each node

### 2. Enhanced Workflow Architecture
- Either modify existing workflows (ALPHA_INPAINT or BATCH_INPAINT) or create new
- Integration of automatic masking systems
- LLM prompt generation pipeline
- Image inpainting and processing chain

### 3. Implementation Plan
- Step-by-step workflow construction guide
- Required model dependencies
- Recommended custom nodes and their sources
- Configuration settings for optimal results

### 4. Performance Considerations
- Expected VRAM requirements
- Processing time estimates
- Hardware optimization recommendations
- Quality vs. speed trade-off settings

## Research Focus Areas

### Current Workflows
- Examine ALPHA_INPAINT for single-image inpainting architecture
- Analyze BATCH_INPAINT for multi-image processing patterns
- Identify reusable components and best practices
- Note current limitations and improvement opportunities

### Available Technologies
- SAM (Segment Anything Model) integration nodes
- Florence object detection and segmentation
- LLM connector nodes (Ollama, OpenAI, etc.)
- Advanced inpainting models (Fooocus, IP-Adapter, etc.)
- Face/hair specific enhancement tools

### Recommended Extensions
- Style control nodes for consistent clothing/hair styles
- Face preservation nodes when hair is being changed
- Color harmony nodes to maintain visual consistency
- Quality enhancement nodes for final refinement

## Output Format Request
1. **Node Inventory Report**: Complete list of available and recommended nodes
2. **Workflow Architecture Diagram**: Visual or textual representation of new/modified workflow
3. **Implementation Guide**: Step-by-step instructions for workflow construction
4. **Performance Analysis**: Hardware requirements and optimization recommendations
5. **Use Case Examples**: Specific configuration examples for clothing replacement and hair styling scenarios

## Priority Considerations
- Prioritize accuracy and quality of mask generation over speed
- Favor LLM integration that maintains semantic coherence
- Emphasize workflows that are extensible to other object replacement tasks
- Balance automation with user control for fine-tuning results