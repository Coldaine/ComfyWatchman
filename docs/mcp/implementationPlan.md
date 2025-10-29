# ComfyWatchman MCP Server: Implementation Plan

**Version:** 1.0
**Date:** 2025-10-29
**Status:** Planning → Implementation
**Target:** Personal use, local deployment
**Complexity:** Medium (3-6 weeks, incremental)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Phase 1: Foundation](#phase-1-foundation-weeks-1-2)
5. [Phase 2: Workflow Generation](#phase-2-workflow-generation-weeks-3-4)
6. [Phase 3: Advanced Features](#phase-3-advanced-features-weeks-5-6)
7. [Testing Strategy](#testing-strategy)
8. [Integration Guide](#integration-guide)
9. [Milestones & Deliverables](#milestones--deliverables)
10. [Open Questions](#open-questions)

---

## Architecture Overview

### Design Decision: Option C (Top-Level Folder)

**Rationale:** Personal use only → maximum flexibility, minimal packaging overhead.

```
ComfyWatchman/
├── src/comfyfixersmart/          # Existing library (unchanged)
├── mcp_server/                    # NEW - MCP server (standalone)
│   ├── server.py                 # Main MCP server entry point
│   ├── tools/                    # MCP tool implementations
│   │   ├── __init__.py
│   │   ├── analysis.py           # Workflow analysis tools
│   │   ├── search.py             # Model search tools
│   │   ├── inspection.py         # Model inspection tools
│   │   └── generation.py         # Workflow generation tools
│   ├── generation/               # Workflow generation logic
│   │   ├── __init__.py
│   │   ├── node_database.py      # Node type definitions
│   │   ├── validator.py          # Connection validation
│   │   ├── builder.py            # Workflow builder
│   │   └── templates.py          # Template management
│   ├── data/                     # Static data files
│   │   ├── node_types.json       # Node type database
│   │   ├── templates/            # Workflow templates
│   │   │   ├── txt2img_basic.json
│   │   │   ├── img2img.json
│   │   │   └── controlnet.json
│   │   └── compatibility.json    # Model compatibility matrix
│   ├── tests/                    # MCP server tests
│   │   ├── test_tools.py
│   │   ├── test_generation.py
│   │   └── test_integration.py
│   ├── config.py                 # MCP server configuration
│   ├── requirements.txt          # MCP-specific dependencies
│   ├── README.md                 # Setup and usage guide
│   └── .env.example              # Environment variables template
└── scripts/
    ├── start_mcp.sh              # Launch MCP server
    └── test_mcp.sh               # Test MCP server
```

### Key Architecture Principles

1. **Separation of Concerns**
   - ComfyWatchman: Core library (dependency resolution, model search)
   - MCP Server: API layer + workflow generation logic

2. **Direct Imports**
   ```python
   # mcp_server can import ComfyWatchman directly
   from comfyfixersmart.core import ComfyFixerCore
   from comfyfixersmart.inspector import inspect_file
   # ComfyWatchman is installed with `pip install -e .`
   ```

3. **Stateless Tools**
   - Each MCP tool is independent
   - No shared mutable state
   - Can be called in any order

4. **Async-First**
   - All tools are async for long-running operations
   - Progress streaming for downloads and searches
   - Non-blocking execution

---

## Technology Stack

### Core Dependencies

```txt
# mcp_server/requirements.txt

# MCP Framework
mcp>=0.9.0                    # Model Context Protocol SDK
pydantic>=2.0.0               # Data validation and schemas

# Async/Networking
websockets>=12.0              # WebSocket communication for MCP
aiohttp>=3.9.0                # Async HTTP client
asyncio                       # Built-in async runtime

# Workflow Generation
jsonschema>=4.0.0             # JSON validation for workflows
jinja2>=3.0.0                 # Template rendering (optional)

# Utilities
python-dotenv>=1.0.0          # Environment variable management
pyyaml>=6.0.0                 # YAML parsing for templates
```

### Python Version
- **Minimum:** Python 3.10+ (for modern async features and type hints)
- **Recommended:** Python 3.11+ (better performance)

### Development Tools

```txt
# Development dependencies (add to requirements-dev.txt)
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
black>=23.0.0
mypy>=1.5.0
ruff>=0.1.0                   # Fast linter
```

---

## Project Structure (Detailed)

### File-by-File Breakdown

#### `mcp_server/server.py` (Main Entry Point)
```python
"""
ComfyWatchman MCP Server
Main entry point for the MCP server
"""
from mcp.server import Server
from tools import analysis, search, inspection, generation

app = Server("comfyui-watchman")

# Register all tools from modules
analysis.register_tools(app)
search.register_tools(app)
inspection.register_tools(app)
generation.register_tools(app)

if __name__ == "__main__":
    import asyncio
    asyncio.run(app.run())
```

#### `mcp_server/tools/analysis.py`
```python
"""
Workflow analysis MCP tools
Wraps ComfyWatchman's workflow scanning and analysis
"""
from typing import Dict, List, Optional
from comfyfixersmart.core import ComfyFixerCore
from comfyfixersmart.scanner import WorkflowScanner

async def analyze_workflow(workflow_path: str) -> Dict:
    """Analyze a workflow and return missing models"""
    ...

async def scan_workflows(directory: str, recursive: bool = True) -> List[Dict]:
    """Scan directory for workflows and return summary"""
    ...

async def extract_models(workflow_path: str) -> List[Dict]:
    """Extract all model references from workflow"""
    ...

def register_tools(app):
    """Register analysis tools with MCP server"""
    app.tool()(analyze_workflow)
    app.tool()(scan_workflows)
    app.tool()(extract_models)
```

#### `mcp_server/generation/node_database.py`
```python
"""
Node type database and query interface
"""
from typing import Dict, List, Optional
from pydantic import BaseModel

class InputSpec(BaseModel):
    name: str
    type: str  # "MODEL", "CLIP", "IMAGE", "STRING", etc.
    required: bool = True
    default: Optional[str] = None

class OutputSpec(BaseModel):
    name: str
    type: str
    slot: int

class NodeType(BaseModel):
    type: str
    category: str
    display_name: str
    inputs: List[InputSpec]
    outputs: List[OutputSpec]
    description: str

class NodeDatabase:
    """Query interface for node types"""
    def __init__(self, db_path: str = "data/node_types.json"):
        self.nodes = self._load_database(db_path)

    def get_node(self, node_type: str) -> Optional[NodeType]:
        ...

    def find_nodes_by_category(self, category: str) -> List[NodeType]:
        ...

    def can_connect(self, from_type: str, from_slot: int,
                    to_type: str, to_slot: int) -> bool:
        """Check if connection is valid"""
        ...
```

#### `mcp_server/data/node_types.json` (Example)
```json
{
  "nodes": [
    {
      "type": "CheckpointLoaderSimple",
      "category": "loaders",
      "display_name": "Load Checkpoint",
      "inputs": [
        {
          "name": "ckpt_name",
          "type": "STRING",
          "required": true,
          "widget": "combo"
        }
      ],
      "outputs": [
        {"name": "MODEL", "type": "MODEL", "slot": 0},
        {"name": "CLIP", "type": "CLIP", "slot": 1},
        {"name": "VAE", "type": "VAE", "slot": 2}
      ],
      "description": "Loads a checkpoint file for image generation"
    },
    {
      "type": "KSampler",
      "category": "sampling",
      "display_name": "KSampler",
      "inputs": [
        {"name": "model", "type": "MODEL", "required": true},
        {"name": "positive", "type": "CONDITIONING", "required": true},
        {"name": "negative", "type": "CONDITIONING", "required": true},
        {"name": "latent_image", "type": "LATENT", "required": true},
        {"name": "seed", "type": "INT", "required": true, "default": "0"},
        {"name": "steps", "type": "INT", "required": true, "default": "20"},
        {"name": "cfg", "type": "FLOAT", "required": true, "default": "7.0"},
        {"name": "sampler_name", "type": "STRING", "required": true, "default": "euler"},
        {"name": "scheduler", "type": "STRING", "required": true, "default": "normal"},
        {"name": "denoise", "type": "FLOAT", "required": true, "default": "1.0"}
      ],
      "outputs": [
        {"name": "LATENT", "type": "LATENT", "slot": 0}
      ],
      "description": "Main sampling node for image generation"
    }
  ]
}
```

---

## Phase 1: Foundation (Weeks 1-2)

### Goal
Wrap existing ComfyWatchman tools as MCP endpoints and integrate with Claude Desktop.

### Tasks

#### Week 1: Setup & Basic Tools

**Day 1-2: Project Setup**
- [ ] Create `mcp_server/` directory structure
- [ ] Write `requirements.txt` with MCP dependencies
- [ ] Create `.env.example` with configuration template
- [ ] Write basic `server.py` with MCP initialization
- [ ] Test MCP server starts without errors

**Day 3-4: Analysis Tools**
- [ ] Implement `tools/analysis.py`:
  - [ ] `analyze_workflow()` - Wrap `ComfyFixerCore.run_workflow_analysis()`
  - [ ] `scan_workflows()` - Wrap `WorkflowScanner.scan_workflows()`
  - [ ] `extract_models()` - Wrap `extract_models_from_workflow()`
- [ ] Write unit tests for each tool
- [ ] Test with sample workflows

**Day 5-7: Search & Inspection Tools**
- [ ] Implement `tools/search.py`:
  - [ ] `search_model()` - Single model search
  - [ ] `search_models_batch()` - Batch search
  - [ ] `resolve_dependencies()` - Full resolution with download URLs
- [ ] Implement `tools/inspection.py`:
  - [ ] `inspect_model()` - Wrap `inspect_file()`
  - [ ] `list_local_models()` - Wrap `build_local_inventory()`
  - [ ] `get_model_info()` - Extended metadata
- [ ] Write tests for all tools
- [ ] Test end-to-end with real searches

#### Week 2: Integration & Polish

**Day 8-10: Claude Desktop Integration**
- [ ] Write Claude Desktop MCP configuration
- [ ] Create `~/.config/claude/mcp.json` entry
- [ ] Test tool discovery in Claude Desktop
- [ ] Test actual tool execution from Claude
- [ ] Write usage examples in `mcp_server/README.md`

**Day 11-12: State Management Tools**
- [ ] Implement state query tools:
  - [ ] `get_download_history()` - View past downloads
  - [ ] `get_failed_downloads()` - View failures
  - [ ] `retry_download()` - Retry failed download
- [ ] Test state persistence across server restarts

**Day 13-14: Documentation & Testing**
- [ ] Write comprehensive `mcp_server/README.md`:
  - [ ] Installation instructions
  - [ ] Configuration guide
  - [ ] Tool reference
  - [ ] Example conversations with Claude
- [ ] Create `scripts/start_mcp.sh` launcher
- [ ] Write integration tests
- [ ] Test all tools end-to-end

### Phase 1 Deliverables

✅ **Working MCP server** with 10+ tools wrapping ComfyWatchman
✅ **Claude Desktop integration** - Can call tools from Claude
✅ **Full test suite** - Unit and integration tests passing
✅ **Documentation** - README with setup and usage
✅ **Example workflows** - Demonstrated in Claude Desktop

### Phase 1 Success Criteria

- [ ] Can analyze workflows from Claude: "Check this workflow for missing models"
- [ ] Can search for models: "Find sdxl_vae.safetensors on Civitai"
- [ ] Can inspect models: "What type of model is this file?"
- [ ] All tools return structured data (JSON)
- [ ] No crashes or unhandled exceptions

---

## Phase 2: Workflow Generation (Weeks 3-4)

### Goal
Implement connection-aware workflow generation from templates.

### Tasks

#### Week 3: Node Database & Validation

**Day 15-16: Node Type Database**
- [ ] Create `data/node_types.json` with 30+ core nodes:
  - [ ] Loaders: CheckpointLoaderSimple, LoraLoader, VAELoader, etc.
  - [ ] Conditioning: CLIPTextEncode, CLIPTextEncodeSDXL, etc.
  - [ ] Sampling: KSampler, KSamplerAdvanced, etc.
  - [ ] Latent: EmptyLatentImage, VAEEncode, VAEDecode, etc.
  - [ ] Image: SaveImage, PreviewImage, ImageScale, etc.
- [ ] Implement `generation/node_database.py`:
  - [ ] Load and parse node definitions
  - [ ] Query by type, category
  - [ ] Validate node specifications

**Day 17-18: Connection Validator**
- [ ] Implement `generation/validator.py`:
  - [ ] Type compatibility checking (MODEL->MODEL, CLIP->CLIP, etc.)
  - [ ] Required input validation
  - [ ] Circular dependency detection
  - [ ] Unused node detection
- [ ] Write comprehensive validation tests
- [ ] Test with valid and invalid workflows

**Day 19-21: Workflow Templates**
- [ ] Create workflow templates:
  - [ ] `templates/txt2img_basic.json` - Simple text-to-image
  - [ ] `templates/txt2img_sdxl.json` - SDXL text-to-image
  - [ ] `templates/img2img.json` - Image-to-image
  - [ ] `templates/upscale.json` - Image upscaling
  - [ ] `templates/controlnet_pose.json` - ControlNet with pose
- [ ] Implement `generation/templates.py`:
  - [ ] Load templates from files
  - [ ] Parameter substitution
  - [ ] Template validation

#### Week 4: Workflow Builder

**Day 22-24: Workflow Builder Core**
- [ ] Implement `generation/builder.py`:
  - [ ] `WorkflowBuilder` class
  - [ ] `add_node()` - Add node with auto-ID generation
  - [ ] `connect()` - Create connection with validation
  - [ ] `set_parameter()` - Set node parameter
  - [ ] `validate()` - Full workflow validation
  - [ ] `to_json()` - Export as ComfyUI JSON

**Day 25-26: Generation Tools**
- [ ] Implement `tools/generation.py`:
  - [ ] `generate_workflow()` - Create workflow from template
  - [ ] `validate_workflow()` - Validate existing workflow
  - [ ] `add_node_to_workflow()` - Modify workflow
  - [ ] `fix_connections()` - Auto-fix connection issues
- [ ] Write generation tests
- [ ] Test with Claude Desktop

**Day 27-28: Integration & Testing**
- [ ] Test workflow generation end-to-end
- [ ] Test generated workflows in ComfyUI
- [ ] Fix any validation issues
- [ ] Update documentation with generation examples

### Phase 2 Deliverables

✅ **Node database** with 30+ core nodes
✅ **Connection validator** ensuring type safety
✅ **5+ workflow templates** for common use cases
✅ **Workflow builder** with validation
✅ **Generation tools** accessible from Claude
✅ **Documentation** with generation examples

### Phase 2 Success Criteria

- [ ] Can generate basic txt2img workflow from Claude
- [ ] Generated workflows validate successfully
- [ ] Generated workflows execute in ComfyUI without errors
- [ ] Can customize workflows (change model, resolution, steps)
- [ ] 95%+ connection validity rate

---

## Phase 3: Advanced Features (Weeks 5-6)

### Goal
Add intelligent features: compatibility checking, workflow repair, optimization.

### Tasks

#### Week 5: Model Compatibility

**Day 29-31: Compatibility Matrix**
- [ ] Create `data/compatibility.json`:
  - [ ] Model families (SDXL, SD1.5, SD2.x, Flux, Pony)
  - [ ] Compatible LoRAs per family
  - [ ] Compatible VAEs per family
  - [ ] Resolution requirements
- [ ] Implement compatibility checker:
  - [ ] Detect model family from filename/metadata
  - [ ] Validate LoRA compatibility
  - [ ] Suggest alternatives when incompatible
- [ ] Write compatibility tests

**Day 32-33: Smart Model Selection**
- [ ] Implement intelligent model selection:
  - [ ] Parse user intent ("anime", "realistic", "cyberpunk")
  - [ ] Query local inventory for matching models
  - [ ] Search Civitai if not found locally
  - [ ] Recommend best match with reasoning
- [ ] Add to generation tools

**Day 34-35: Workflow Repair**
- [ ] Implement `repair_workflow()` tool:
  - [ ] Diagnose missing connections
  - [ ] Detect incompatible models
  - [ ] Identify missing required inputs
  - [ ] Suggest fixes
  - [ ] Apply fixes automatically (with confirmation)
- [ ] Test with broken workflows from community

#### Week 6: Optimization & Polish

**Day 36-37: Workflow Optimization**
- [ ] Implement optimization strategies:
  - [ ] `optimize_for_speed()` - Reduce steps, faster samplers
  - [ ] `optimize_for_vram()` - Add tiling, reduce batch size
  - [ ] `optimize_for_quality()` - Increase steps, better samplers
- [ ] Add as MCP tools

**Day 38-39: Advanced Generation**
- [ ] Implement intent-to-workflow:
  - [ ] Parse natural language descriptions
  - [ ] Select appropriate template
  - [ ] Customize parameters based on intent
  - [ ] Validate and return
- [ ] Test with varied prompts

**Day 40-42: Final Polish**
- [ ] Performance optimization
- [ ] Error message improvements
- [ ] Documentation update
- [ ] Create video demos
- [ ] Final integration testing

### Phase 3 Deliverables

✅ **Compatibility matrix** for major model families
✅ **Workflow repair** tool
✅ **Optimization** strategies
✅ **Intent-based generation** (natural language → workflow)
✅ **Complete documentation**
✅ **Demo videos**

### Phase 3 Success Criteria

- [ ] Can detect and fix incompatible model combinations
- [ ] Can repair community workflows automatically
- [ ] Can generate workflows from natural language
- [ ] Can optimize workflows for different goals
- [ ] Complete end-to-end workflow: intent → generation → validation → execution

---

## Testing Strategy

### Test Pyramid

```
        /\
       /  \      End-to-End (5%)
      /____\     Integration (20%)
     /      \    Unit (75%)
    /________\
```

### Unit Tests

**Location:** `mcp_server/tests/test_*.py`

**Coverage:**
- Each MCP tool independently
- Node database queries
- Validator logic
- Template loading
- Builder operations

**Example:**
```python
# tests/test_validation.py
def test_connection_type_matching():
    validator = ConnectionValidator(node_db)
    # MODEL -> MODEL should pass
    assert validator.can_connect(
        from_node="checkpoint", from_slot=0,  # MODEL output
        to_node="sampler", to_slot=0           # MODEL input
    )
    # MODEL -> CLIP should fail
    assert not validator.can_connect(
        from_node="checkpoint", from_slot=0,  # MODEL output
        to_node="clip", to_slot=0             # CLIP input
    )
```

### Integration Tests

**Location:** `mcp_server/tests/test_integration.py`

**Coverage:**
- MCP server startup
- Tool registration
- End-to-end tool execution
- ComfyWatchman integration

**Example:**
```python
# tests/test_integration.py
async def test_analyze_workflow_integration():
    # Start MCP server
    server = await start_test_server()

    # Call tool
    result = await server.call_tool(
        "analyze_workflow",
        {"workflow_path": "tests/data/sample_workflow.json"}
    )

    # Verify result structure
    assert "missing_models" in result
    assert isinstance(result["missing_models"], list)
```

### End-to-End Tests

**Location:** `mcp_server/tests/test_e2e.py`

**Coverage:**
- Claude Desktop interaction (manual testing)
- Generated workflows in ComfyUI
- Full workflow: generation → validation → execution

**Process:**
1. Generate workflow via MCP
2. Save to file
3. Load in ComfyUI
4. Execute and verify success

### Test Data

```
mcp_server/tests/data/
├── workflows/
│   ├── valid_txt2img.json
│   ├── invalid_connections.json
│   ├── missing_models.json
│   └── circular_dependency.json
├── models/
│   └── test_model.safetensors
└── expected/
    └── generated_workflow.json
```

### CI/CD (Future)

```yaml
# .github/workflows/test_mcp.yml
name: Test MCP Server
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install ComfyWatchman
        run: pip install -e .
      - name: Install MCP dependencies
        run: pip install -r mcp_server/requirements.txt
      - name: Run tests
        run: pytest mcp_server/tests/
```

---

## Integration Guide

### Claude Desktop Setup

**Step 1: Install ComfyWatchman**
```bash
cd /home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart
pip install -e .
```

**Step 2: Install MCP Dependencies**
```bash
cd mcp_server
pip install -r requirements.txt
```

**Step 3: Configure Environment**
```bash
# mcp_server/.env
COMFYUI_ROOT=/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable
MCP_LOG_LEVEL=INFO
```

**Step 4: Add to Claude Desktop Config**
```json
// ~/.config/claude/mcp.json
{
  "mcpServers": {
    "comfywatchman": {
      "command": "python",
      "args": [
        "/home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart/mcp_server/server.py"
      ],
      "env": {
        "COMFYUI_ROOT": "/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable"
      }
    }
  }
}
```

**Step 5: Restart Claude Desktop**

**Step 6: Test**
In Claude Desktop:
> "List the available ComfyWatchman tools"

Should see all registered MCP tools.

### Example Conversations

**Example 1: Workflow Analysis**
```
User: Analyze the workflow at ~/workflows/anime_workflow.json

Claude: *calls analyze_workflow tool*
I've analyzed your workflow. It requires 3 models:
1. animagine-xl-3.safetensors (checkpoint) - Found locally
2. sdxl_vae.safetensors (VAE) - Found locally
3. anime_style_lora.safetensors (LoRA) - Missing

Would you like me to search for the missing LoRA?
```

**Example 2: Workflow Generation**
```
User: Create a basic txt2img workflow for SDXL at 1024x1024

Claude: *calls generate_workflow tool*
I've generated an SDXL text-to-image workflow with:
- CheckpointLoaderSimple (SDXL base model)
- CLIPTextEncodeSDXL (positive and negative prompts)
- EmptyLatentImage (1024x1024)
- KSampler (20 steps, euler, cfg 7.0)
- VAEDecode
- SaveImage

All connections are valid and the workflow is ready to use.
Shall I save it to a file?
```

---

## Milestones & Deliverables

### Milestone 1: MCP Foundation (Week 2)
**Date:** End of Week 2
**Deliverables:**
- ✅ Working MCP server with analysis/search/inspection tools
- ✅ Claude Desktop integration
- ✅ Basic tests passing
- ✅ README with setup instructions

**Demo:** Analyze workflow and search for models from Claude

---

### Milestone 2: Workflow Generation (Week 4)
**Date:** End of Week 4
**Deliverables:**
- ✅ Node database with 30+ nodes
- ✅ Connection validator
- ✅ 5+ workflow templates
- ✅ Workflow builder and generation tools

**Demo:** Generate txt2img workflow from Claude, execute in ComfyUI

---

### Milestone 3: Advanced Features (Week 6)
**Date:** End of Week 6
**Deliverables:**
- ✅ Compatibility matrix
- ✅ Workflow repair tool
- ✅ Optimization strategies
- ✅ Natural language workflow generation
- ✅ Complete documentation

**Demo:** Full workflow from description to execution

---

## Open Questions

### Questions to Resolve During Implementation

1. **Node Discovery**
   - Q: Should we dynamically query ComfyUI for node types, or maintain static database?
   - A: Start with static, add dynamic as Phase 4 enhancement

2. **Custom Nodes**
   - Q: How to handle 1000+ custom nodes we don't know about?
   - A: Start with core nodes only, add popular custom nodes on-demand

3. **Workflow Execution**
   - Q: Should MCP server trigger ComfyUI execution, or just generate workflows?
   - A: Phase 1: Generation only. Phase 4: Optional execution via ComfyUI API

4. **Error Handling**
   - Q: How detailed should error messages be?
   - A: Very detailed - include suggestions for fixes

5. **Model Compatibility**
   - Q: How to reliably detect model families?
   - A: Combination of filename heuristics + metadata + user hints

6. **Performance**
   - Q: What's acceptable latency for workflow generation?
   - A: <3s for basic workflows, <10s for complex

7. **Template Evolution**
   - Q: How to add new templates easily?
   - A: Simple JSON files in `data/templates/`, no code changes needed

8. **Validation Strictness**
   - Q: Should validation be strict or permissive?
   - A: Strict by default, add `--force` flag to bypass

---

## Risk Assessment & Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| MCP API changes | Low | High | Pin MCP version, monitor updates |
| ComfyUI node changes | Medium | Medium | Version compatibility matrix |
| Connection rules incomplete | High | Medium | Start with core nodes, expand iteratively |
| Template maintenance | Medium | Low | Keep templates simple and few |
| Performance issues | Low | Medium | Profile and optimize bottlenecks |

### Personal Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Lose interest | Medium | High | Focus on personal use cases, quick wins |
| Time constraints | High | Medium | Incremental development, MVP first |
| Scope creep | High | Low | Stick to phases, defer non-essential features |
| Tool not useful | Low | High | Test with real workflows early |

---

## Success Definition

### Must Have (Phase 1)
- ✅ Can analyze workflows from Claude
- ✅ Can search for models
- ✅ Can inspect models
- ✅ Never crashes

### Should Have (Phase 2)
- ✅ Can generate basic workflows
- ✅ Generated workflows are valid
- ✅ Can validate existing workflows

### Nice to Have (Phase 3)
- ✅ Can repair broken workflows
- ✅ Can optimize workflows
- ✅ Natural language generation

### Won't Have (Deferred)
- ❌ Workflow execution
- ❌ Custom node support (beyond core)
- ❌ GUI/web interface
- ❌ Multi-user support

---

## Appendix: File Templates

### `.env.example`
```bash
# ComfyUI Installation
COMFYUI_ROOT=/path/to/ComfyUI

# MCP Server Configuration
MCP_HOST=localhost
MCP_PORT=9000
MCP_LOG_LEVEL=INFO

# ComfyWatchman Configuration
CIVITAI_API_KEY=your_key_here
HUGGINGFACE_TOKEN=your_token_here
TAVILY_API_KEY=your_key_here

# Optional
CACHE_DIR=./cache
LOG_DIR=./logs
```

### `scripts/start_mcp.sh`
```bash
#!/bin/bash
set -e

cd "$(dirname "$0")/../mcp_server"

# Load environment
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Activate venv if exists
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# Start MCP server
echo "Starting ComfyWatchman MCP Server..."
python server.py
```

### `scripts/test_mcp.sh`
```bash
#!/bin/bash
set -e

cd "$(dirname "$0")/../mcp_server"

# Run tests with coverage
pytest tests/ \
    --cov=. \
    --cov-report=term \
    --cov-report=html \
    -v
```

---

## Next Steps

### Immediate Actions (This Week)

1. **Create project structure** - Set up folders and files
2. **Install dependencies** - MCP SDK and requirements
3. **Write server.py** - Basic MCP server skeleton
4. **Test MCP startup** - Verify server starts without errors
5. **Write first tool** - `analyze_workflow()` as proof of concept

### Week 1 Goals

- Complete Phase 1 Day 1-4 tasks
- Have 3-5 working MCP tools
- Test with Claude Desktop

### Decision Points

- **End of Week 2:** Evaluate Phase 1 progress, adjust Phase 2 plan
- **End of Week 4:** Evaluate Phase 2 progress, decide on Phase 3 priorities
- **End of Week 6:** Evaluate overall project, plan future enhancements

---

## Conclusion

This implementation plan provides a clear, phased roadmap from basic MCP tool wrapping to advanced workflow generation. The incremental approach allows for learning and adjustment while delivering value at each milestone.

**Key Success Factors:**
1. Start simple - wrap existing tools first
2. Test early and often - especially with Claude Desktop
3. Focus on personal use cases - solve real problems
4. Iterate based on usage - add features as needed
5. Keep it maintainable - avoid over-engineering

**Timeline Summary:**
- **Week 2:** Foundation complete, Claude integration working
- **Week 4:** Workflow generation functional
- **Week 6:** Advanced features complete, full system operational

**Next Document:** See `mcp_server/README.md` for setup instructions (create after Week 1)
