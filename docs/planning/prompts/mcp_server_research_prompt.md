# Research & Implementation Prompt: ComfyWatchman MCP Server with Workflow Generation

## Project Overview

You are tasked with researching and designing a comprehensive MCP (Model Context Protocol) server that wraps ComfyWatchman's powerful dependency resolution tools and adds intelligent ComfyUI workflow generation capabilities. This server will enable AI agents to programmatically analyze, create, modify, and validate ComfyUI workflows while ensuring all dependencies are resolved.

## Background Context

### ComfyWatchman Capabilities
ComfyWatchman is a production-ready Python tool (v2.0) that excels at:
- **Workflow Analysis**: Parsing ComfyUI JSON files to extract model dependencies
- **Model Discovery**: Multi-backend search across Civitai, HuggingFace, and web sources via Qwen agent
- **Dependency Resolution**: Automatic download management with state tracking and resume capability
- **Model Inspection**: Safe metadata extraction from model files without loading tensors
- **Local Inventory**: Comprehensive scanning of ComfyUI model directories
- **State Management**: Sophisticated tracking of downloads, failures, and retry logic

### Existing MCP Servers
Two ComfyUI MCP servers already exist:
1. **Overseer66's server**: Features workflow execution, JSON submission, image download
2. **joenorton's server**: Lightweight implementation with WebSocket communication

### The Gap
Current MCP servers can execute workflows but lack:
- Intelligent workflow **generation** from text descriptions
- Connection-aware node linking (preventing invalid connections)
- Dependency resolution before execution
- Model compatibility checking
- Workflow validation and repair

## Research Objectives

### Phase 1: Core MCP Server Implementation

Research and design an MCP server that exposes ComfyWatchman's tools as MCP resources and tools:

#### 1.1 Workflow Analysis Tools
```python
# Example tool definitions needed:
- analyze_workflow(workflow_json: str) -> DependencyReport
- scan_workflows(directory: str) -> List[WorkflowSummary]
- extract_missing_models(workflow_json: str) -> List[ModelReference]
- validate_workflow_structure(workflow_json: str) -> ValidationReport
```

#### 1.2 Model Search & Resolution Tools
```python
# Search across multiple backends
- search_model(filename: str, model_type: str) -> SearchResult
- search_models_batch(models: List[ModelRef]) -> List[SearchResult]
- resolve_dependencies(workflow_json: str) -> ResolutionReport
- generate_download_script(missing_models: List) -> str
```

#### 1.3 Model Inspection Tools
```python
# Safe metadata extraction
- inspect_model(file_path: str) -> ModelMetadata
- get_model_compatibility(model_path: str) -> CompatibilityInfo
- list_local_models(model_type: str) -> List[LocalModel]
- verify_model_integrity(file_path: str) -> IntegrityReport
```

#### 1.4 State Management Resources
```python
# Expose state as MCP resources
- get_download_history() -> List[DownloadRecord]
- get_failed_downloads() -> List[FailureRecord]
- retry_failed_download(model_id: str) -> DownloadResult
- clear_cache(cache_type: str) -> ClearResult
```

### Phase 2: Intelligent Workflow Generation

Research and implement connection-aware workflow generation that creates **valid** ComfyUI workflows:

#### 2.1 Node Type System
Build a comprehensive node type database that includes:
```python
NodeTypeDefinition = {
    "name": "CheckpointLoaderSimple",
    "category": "loaders",
    "inputs": {
        "ckpt_name": {"type": "STRING", "values": "*.safetensors"}
    },
    "outputs": [
        {"name": "MODEL", "type": "MODEL", "slot": 0},
        {"name": "CLIP", "type": "CLIP", "slot": 1},
        {"name": "VAE", "type": "VAE", "slot": 2}
    ],
    "compatible_with": ["KSampler", "CLIPTextEncode", "VAEDecode"]
}
```

#### 2.2 Connection Validation Engine
Research how to implement type-safe connections:
```python
# Connection validation rules
- Type matching: OUTPUT.type must match INPUT.type
- Slot management: Track which outputs connect to which inputs
- Cardinality: Some inputs accept multiple connections, others don't
- Required vs optional: Some inputs must be connected
- Circular dependency detection: Prevent workflow loops
```

#### 2.3 Workflow Templates
Create a template system for common workflows:
```python
Templates = {
    "txt2img_basic": {
        "required_nodes": ["CheckpointLoader", "CLIPTextEncode", "KSampler", "VAEDecode", "SaveImage"],
        "connections": [
            ("checkpoint.MODEL", "sampler.model"),
            ("checkpoint.CLIP", "clip.clip"),
            ("clip.CONDITIONING", "sampler.positive"),
            # ... etc
        ]
    },
    "img2img_upscale": { ... },
    "controlnet_pose": { ... }
}
```

#### 2.4 Smart Workflow Builder
Implement an intelligent builder that:
```python
class WorkflowBuilder:
    def from_prompt(self, prompt: str) -> ComfyWorkflow:
        """Generate workflow from natural language"""
        # 1. Identify intent (txt2img, img2img, upscale, etc.)
        # 2. Select appropriate template
        # 3. Add required nodes with proper IDs
        # 4. Establish valid connections
        # 5. Set default parameters
        # 6. Validate the result

    def add_node(self, node_type: str, position: tuple) -> NodeID:
        """Add a node ensuring all requirements are met"""

    def connect(self, from_node: NodeID, from_slot: str,
                to_node: NodeID, to_slot: str) -> bool:
        """Create connection with validation"""

    def validate(self) -> ValidationResult:
        """Check workflow completeness and correctness"""
```

### Phase 3: Advanced Features

#### 3.1 Model Compatibility Matrix
Research building a compatibility database:
```python
CompatibilityMatrix = {
    "model_families": {
        "SDXL": {
            "base_models": ["sd_xl_base_1.0.safetensors"],
            "compatible_loras": ["style:sdxl_*", "character:sdxl_*"],
            "compatible_vae": ["sdxl_vae.safetensors"],
            "incompatible_with": ["SD1.5", "SD2.x"],
            "node_requirements": {
                "width": [1024, 1536, 2048],
                "height": [1024, 1536, 2048]
            }
        },
        "Flux": { ... },
        "Pony": { ... }
    }
}
```

#### 3.2 Workflow Optimization
Implement optimization strategies:
```python
class WorkflowOptimizer:
    def optimize_for_speed(self, workflow: dict) -> dict:
        """Reduce steps, use faster samplers"""

    def optimize_for_vram(self, workflow: dict) -> dict:
        """Add tiling, reduce batch size, use sequential processing"""

    def optimize_for_quality(self, workflow: dict) -> dict:
        """Increase steps, use better samplers, add refinement"""
```

#### 3.3 Error Recovery & Repair
Build intelligent error handling:
```python
class WorkflowRepair:
    def diagnose_error(self, error_msg: str, workflow: dict) -> Diagnosis:
        """Identify the root cause of execution errors"""

    def suggest_fix(self, diagnosis: Diagnosis) -> List[Fix]:
        """Generate potential fixes for the error"""

    def auto_repair(self, workflow: dict, error: str) -> dict:
        """Attempt automatic repair of common issues"""
```

## Key Research Questions

### Architecture & Design
1. **MCP Integration**: How should ComfyWatchman's modules be wrapped as MCP tools vs resources?
2. **Async Operations**: How to handle long-running operations (downloads, searches) in MCP?
3. **Streaming**: Should search results and download progress be streamed?
4. **Caching Strategy**: How to efficiently cache node definitions and compatibility data?

### Workflow Generation
1. **Node Discovery**: How to dynamically discover available nodes and their specifications?
2. **Connection Rules**: Where to source the complete connection validation rules?
3. **Parameter Defaults**: How to determine sensible defaults for each node type?
4. **Template Learning**: Can we learn templates from existing successful workflows?

### Validation & Safety
1. **Type System**: How to implement a robust type system for ComfyUI connections?
2. **Resource Limits**: How to predict and validate VRAM/RAM requirements?
3. **Circular Dependencies**: How to detect and prevent workflow loops?
4. **Model Compatibility**: How to validate model family compatibility?

### Integration Points
1. **ComfyUI API**: Which ComfyUI APIs should we call for validation?
2. **Custom Nodes**: How to handle custom nodes with unknown specifications?
3. **Model Metadata**: How to extract and use model metadata for compatibility?
4. **Existing MCP Servers**: Should we extend existing servers or build standalone?

## Implementation Requirements

### Core Technologies
- **Language**: Python 3.10+ (matching ComfyWatchman)
- **MCP SDK**: Latest MCP Python SDK
- **Async Framework**: asyncio for concurrent operations
- **Type Safety**: Full type hints with mypy validation
- **Testing**: Comprehensive test suite with pytest

### Data Structures
```python
@dataclass
class NodeDefinition:
    type: str
    category: str
    display_name: str
    inputs: Dict[str, InputSpec]
    outputs: List[OutputSpec]
    optional_inputs: Dict[str, InputSpec]
    min_inputs: int
    max_inputs: int

@dataclass
class ConnectionRule:
    from_type: str
    to_type: str
    compatible: bool
    adapter_needed: Optional[str]

@dataclass
class WorkflowValidation:
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationWarning]
    missing_connections: List[RequiredConnection]
    unused_nodes: List[NodeID]
```

### API Design
```python
# MCP Server endpoints
class ComfyWatchmanMCPServer:
    # Analysis tools
    async def analyze_workflow(self, params: Dict) -> Dict
    async def find_missing_models(self, params: Dict) -> Dict

    # Search tools
    async def search_models(self, params: Dict) -> Dict
    async def resolve_dependencies(self, params: Dict) -> Dict

    # Generation tools
    async def generate_workflow(self, params: Dict) -> Dict
    async def add_node_to_workflow(self, params: Dict) -> Dict
    async def validate_connection(self, params: Dict) -> Dict

    # Repair tools
    async def diagnose_workflow_error(self, params: Dict) -> Dict
    async def repair_workflow(self, params: Dict) -> Dict

    # Resources
    async def get_node_definitions(self) -> Dict
    async def get_model_inventory(self) -> Dict
    async def get_compatibility_matrix(self) -> Dict
```

## Deliverables

### Phase 1 Deliverables (Week 1-2)
1. **Research Document**: Complete analysis of ComfyUI node system and connection rules
2. **Node Database**: JSON/YAML file with 50+ common node definitions
3. **Basic MCP Server**: Wrapper for ComfyWatchman's core tools
4. **Test Suite**: Tests for all MCP endpoints

### Phase 2 Deliverables (Week 3-4)
1. **Workflow Generator**: Basic template-based workflow generation
2. **Connection Validator**: Type-safe connection validation engine
3. **Compatibility Matrix**: Database of model family compatibility
4. **Documentation**: API documentation and usage examples

### Phase 3 Deliverables (Week 5-6)
1. **Smart Builder**: AI-powered workflow generation from prompts
2. **Workflow Repair**: Automatic error diagnosis and repair
3. **Optimization Engine**: Speed/quality/resource optimization
4. **Integration Guide**: How to integrate with Claude, GPT, and other AI agents

## Success Metrics

### Functionality Metrics
- ✅ Successfully wraps all ComfyWatchman tools as MCP endpoints
- ✅ Generates valid workflows for 10+ common use cases
- ✅ Correctly validates/rejects 95%+ of connection attempts
- ✅ Identifies and resolves 90%+ of missing dependencies
- ✅ Repairs 80%+ of common workflow errors automatically

### Quality Metrics
- 🎯 100% type hint coverage
- 🎯 90%+ test coverage
- 🎯 <100ms response time for validation operations
- 🎯 <1s for workflow generation
- 🎯 Zero invalid workflows generated

### Integration Metrics
- 🔌 Works with Claude Desktop via MCP
- 🔌 Works with existing ComfyUI installations
- 🔌 Compatible with 1000+ popular custom nodes
- 🔌 Handles SDXL, Flux, Pony, and SD1.5 model families

## Research Resources

### Official Documentation
- [MCP Specification](https://modelcontextprotocol.io/docs)
- [ComfyUI API Docs](https://github.com/comfyanonymous/ComfyUI/wiki/API)
- [ComfyUI Node Definitions](https://github.com/comfyanonymous/ComfyUI/tree/master/nodes)

### Existing Implementations
- [Overseer66's MCP Server](https://github.com/Overseer66/comfyui-mcp-server)
- [joenorton's MCP Server](https://github.com/joenorton/comfyui-mcp-server)
- [ComfyUI-Copilot](https://github.com/AIDC-AI/ComfyUI-Copilot) (multi-agent approach)
- [ComfyWatchman](https://github.com/Coldaine/ComfyWatchman) (this project)

### Node Definition Sources
- ComfyUI core nodes: `/ComfyUI/nodes/*.py`
- Custom node definitions: `/ComfyUI/custom_nodes/*/nodes.py`
- ComfyUI Manager database: Node compatibility lists
- Community workflow JSON files: Extract patterns from successful workflows

### Testing Resources
- Sample workflows: `/ComfyUI-stable/user/default/workflows/`
- Model files: `/ComfyUI-stable/models/checkpoints/`
- Error logs: Common ComfyUI execution errors
- Edge cases: Invalid connections, missing models, resource limits

## Open Questions for Investigation

1. **Dynamic Node Discovery**: Can we query ComfyUI at runtime for available nodes instead of maintaining a static database?

2. **Custom Node Handling**: How do we handle the 1000+ custom nodes with varying specifications?

3. **Version Compatibility**: How do we handle different ComfyUI versions with different node specifications?

4. **Model Family Detection**: Can we reliably auto-detect model family (SDXL, Flux, etc.) from model files?

5. **Workflow Complexity**: What's the maximum complexity we should support (number of nodes, connections)?

6. **Error Message Parsing**: Can we reliably parse ComfyUI error messages to diagnose issues?

7. **Performance Optimization**: Should we cache node definitions, or load them dynamically?

8. **Multi-Agent Coordination**: Should we integrate with ComfyUI-Copilot's agent system?

## Implementation Notes

### Starting Point
Begin by studying the existing MCP servers and understanding their WebSocket communication patterns. Then wrap ComfyWatchman's tools one by one, starting with the simplest (model inspection) and progressing to more complex operations (workflow generation).

### Testing Strategy
1. Unit tests for each MCP endpoint
2. Integration tests with real ComfyUI instances
3. End-to-end tests with AI agents (Claude, GPT)
4. Performance benchmarks for all operations
5. Stress tests with complex workflows

### Documentation Requirements
1. API reference with all endpoints
2. Integration guide for AI developers
3. Workflow generation cookbook
4. Troubleshooting guide
5. Model compatibility reference

## Example Use Cases

### Use Case 1: Dependency Resolution
```python
# AI Agent Request
"Check if workflow.json has all required models and download missing ones"

# MCP Server Response
{
    "missing_models": [
        {"name": "sdxl_vae.safetensors", "type": "vae"},
        {"name": "sdxl_offset_lora.safetensors", "type": "lora"}
    ],
    "search_results": [
        {"model": "sdxl_vae.safetensors", "found": true, "url": "..."},
        {"model": "sdxl_offset_lora.safetensors", "found": true, "url": "..."}
    ],
    "download_script": "wget https://..."
}
```

### Use Case 2: Workflow Generation
```python
# AI Agent Request
"Create a workflow to generate an anime girl with blue hair at 1024x1024"

# MCP Server Response
{
    "workflow": { /* Valid ComfyUI JSON */ },
    "nodes_used": ["CheckpointLoader", "CLIPTextEncode", "KSampler", "VAEDecode", "SaveImage"],
    "models_required": ["animagine-xl-3.safetensors", "sdxl_vae.safetensors"],
    "estimated_vram": "8GB",
    "validation": {"valid": true, "warnings": []}
}
```

### Use Case 3: Workflow Repair
```python
# AI Agent Request
"Fix this workflow that's giving 'NoneType' errors"

# MCP Server Response
{
    "diagnosis": "Missing connection from CheckpointLoader.CLIP to CLIPTextEncode.clip",
    "repairs_made": [
        {"action": "connect", "from": "checkpoint:1", "to": "clip:2"},
        {"action": "set_default", "node": "sampler:3", "param": "steps", "value": 20}
    ],
    "fixed_workflow": { /* Repaired JSON */ },
    "validation": {"valid": true}
}
```

## Conclusion

This MCP server will bridge the gap between ComfyWatchman's excellent dependency management and the need for intelligent workflow generation. By combining these capabilities with connection-aware validation, we'll enable AI agents to confidently create, modify, and debug ComfyUI workflows while ensuring all dependencies are properly resolved.

The modular design allows for incremental development, starting with basic tool wrapping and progressively adding more sophisticated generation and validation capabilities. The end result will be a powerful tool that makes ComfyUI accessible to AI agents and automation workflows.