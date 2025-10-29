# ComfyWatchman MCP Server: Vision Document

**Version:** 1.0
**Date:** 2025-10-29
**Status:** Planning
**Audience:** Personal reference and future contributors

---

## Executive Summary

The ComfyWatchman MCP (Model Context Protocol) Server bridges the gap between AI assistants and ComfyUI's powerful image generation capabilities. It transforms ComfyWatchman's battle-tested dependency resolution tools into an AI-accessible interface while adding intelligent workflow generation capabilities that ensure valid, dependency-complete workflows every time.

---

## The Problem We're Solving

### Current Pain Points

1. **Manual Workflow Creation** - ComfyUI workflows require clicking through the UI, understanding node connections, and manually testing validity. This is time-consuming and error-prone.

2. **Dependency Hell** - Workflows often fail because:
   - Required models are missing
   - Downloaded models have wrong types
   - Model families are incompatible (SDXL LoRA on SD1.5 checkpoint)
   - Custom nodes aren't installed

3. **Invalid Connections** - It's easy to connect incompatible nodes:
   - Wrong data types (connecting IMAGE to MODEL slot)
   - Missing required inputs
   - Circular dependencies

4. **No AI Access** - AI assistants (Claude, GPT, etc.) can't:
   - Create ComfyUI workflows programmatically
   - Check if workflows will work before running
   - Fix broken workflows automatically
   - Search for and resolve missing models

5. **Trial and Error** - Current workflow:
   - Create workflow in UI
   - Try to run it
   - Error: "Model not found"
   - Manually search Civitai
   - Download model
   - Try again
   - Error: "Invalid connection"
   - Fix in UI
   - Repeat...

### Why This Matters

For a solo developer/power user, ComfyUI is incredibly powerful but:
- Time spent on workflow setup >> time spent generating images
- Can't automate workflow creation for batch tasks
- Can't leverage AI assistants to help with ComfyUI
- Every new workflow is a research project

---

## The Vision: Five Core Goals

### 🎯 Goal 1: AI-First ComfyUI Interface

**What:** Enable AI assistants to interact with ComfyUI as naturally as a human expert would.

**Why:** AI assistants like Claude are getting incredibly good at understanding intent and generating structured data. But they can't help with ComfyUI because there's no programmatic interface they can use.

**Success Looks Like:**
```
User: "Claude, create a workflow that generates anime art at 1024x1024 with ControlNet pose guidance"
Claude: *uses MCP to generate valid workflow with all nodes and connections*
Result: Working workflow, all dependencies resolved, ready to run
```

**Value:** Reduces workflow creation from 20+ minutes of UI clicking to 30 seconds of conversation.

---

### 🔍 Goal 2: Intelligent Dependency Resolution

**What:** Automatically discover, search, and resolve all model dependencies before workflow execution.

**Why:** ComfyWatchman already has best-in-class dependency resolution with multi-backend search (Civitai, HuggingFace, Qwen agent). The MCP server makes this accessible to AI agents.

**Success Looks Like:**
```
AI Agent: analyze_workflow("anime_workflow.json")
MCP: Returns list of missing models with download URLs
AI Agent: resolve_dependencies()
MCP: Downloads all missing models, verifies integrity
Result: Workflow ready to execute, all dependencies satisfied
```

**Value:** Eliminates the "model not found" error completely. No more manual hunting through Civitai.

---

### ✅ Goal 3: Connection-Aware Workflow Generation

**What:** Generate workflows that are structurally valid and will execute without connection errors.

**Why:** ComfyUI's node system is strongly typed but unforgiving. Wrong connections cause silent failures or cryptic errors. AI agents need to understand the rules.

**Success Looks Like:**
```
AI Agent: generate_workflow(prompt="txt2img with upscaling")
MCP:
  - Selects appropriate nodes (Checkpoint, CLIP, KSampler, VAE, Upscaler)
  - Creates valid connections (MODEL->MODEL, CLIP->CLIP, IMAGE->IMAGE)
  - Sets sensible defaults (steps=20, cfg=7)
  - Validates before returning
Result: Workflow executes perfectly on first try
```

**Value:** 95%+ success rate on first execution. No more "NoneType has no attribute" errors.

---

### 🛠️ Goal 4: Workflow Inspection and Repair

**What:** Diagnose why workflows fail and automatically fix common issues.

**Why:** Even with careful generation, workflows can break (outdated node versions, missing parameters, model incompatibilities). The MCP server should be able to fix these.

**Success Looks Like:**
```
User: "This workflow from the internet isn't working"
AI Agent: diagnose_workflow_error(workflow, error_log)
MCP:
  - Identifies missing connection from checkpoint.CLIP to clip_text.clip
  - Detects incompatible model (SD1.5 with SDXL LoRA)
  - Suggests fixes
AI Agent: repair_workflow(workflow, suggested_fixes)
Result: Fixed workflow that executes successfully
```

**Value:** Community workflows "just work" even if outdated or incomplete.

---

### 🤖 Goal 5: Personal Automation Pipeline

**What:** Enable building automated ComfyUI workflows triggered by external events or scripts.

**Why:** ComfyUI is powerful but not automation-friendly. With MCP access, we can integrate it into larger workflows.

**Success Looks Like:**
```
# Example automation
Cron job triggers daily:
  1. MCP generates workflow for "trending art style of the week"
  2. MCP resolves dependencies (downloads new LoRAs if needed)
  3. MCP validates workflow
  4. Triggers ComfyUI execution
  5. Results uploaded to gallery

OR

Watch folder for images:
  - New image arrives
  - MCP generates upscaling workflow
  - Auto-processes image
  - Saves result
```

**Value:** ComfyUI becomes a programmable tool, not just an interactive application.

---

## Why MCP? Why Not REST API or Direct Integration?

### Why MCP (Model Context Protocol):

1. **AI-Native** - Designed specifically for AI agent interaction
2. **Tool Discovery** - AI agents automatically discover available tools
3. **Type Safety** - Built-in parameter validation and type checking
4. **Streaming** - Progress updates during long operations
5. **Standard Protocol** - Works with Claude Desktop, future AI tools
6. **Bidirectional** - Server can provide resources (node definitions) and tools

### Why Not Alternatives:

- **REST API**: Requires client implementation for each AI, no tool discovery
- **Direct Integration**: Tight coupling, can't use with Claude Desktop
- **ComfyUI API**: Only handles execution, not generation or validation
- **Python Library**: Not accessible to AI agents in sandboxed environments

---

## Target Use Cases (Personal)

### Primary Use Case: AI-Assisted Workflow Creation
"I want to try [new technique] but don't know what nodes to use" → Ask Claude, get working workflow

### Secondary Use Cases:
1. **Batch Processing** - Generate 100 variations of a workflow with different parameters
2. **Workflow Templates** - "Make me a workflow like X but for Y model"
3. **Model Discovery** - "Find the best SDXL LoRA for cyberpunk style"
4. **Dependency Auditing** - "What models do I need for all my saved workflows?"
5. **Workflow Migration** - "Update this SD1.5 workflow to SDXL"

---

## Success Metrics

### Quantitative:
- ✅ 95%+ of generated workflows execute successfully on first try
- ✅ 90%+ of missing dependencies resolved automatically
- ✅ <3 seconds to generate basic workflow
- ✅ <10 seconds to resolve dependencies for typical workflow
- ✅ 100% of connections are type-valid

### Qualitative:
- ✅ Creating workflows feels natural in conversation with Claude
- ✅ Dependency resolution "just works" - no manual intervention
- ✅ Errors are rare and clearly explained when they occur
- ✅ Can confidently use community workflows without debugging

---

## Non-Goals (Out of Scope)

### What We're NOT Building:

1. **ComfyUI Replacement** - Still use ComfyUI for execution and preview
2. **Model Training** - Only consumption of existing models
3. **Custom Node Development** - Use existing nodes, don't create new ones
4. **Public API** - Personal use only, no authentication/rate limiting
5. **Workflow Hosting** - Local execution only
6. **GUI** - CLI/MCP only, leverage Claude Desktop for UI
7. **Multi-User Support** - Single user, local installation

---

## Technical Philosophy

### Principles:

1. **Safe by Default** - Validate everything, never generate invalid workflows
2. **Fail Gracefully** - Clear error messages, no silent failures
3. **Progressive Enhancement** - Start with basics, add intelligence over time
4. **Code Reuse** - Leverage ComfyWatchman's proven tools
5. **Keep It Simple** - Personal use allows for simpler architecture
6. **Hackable** - Easy to modify and extend for personal needs

### Non-Principles:

- ❌ Don't optimize for scale (single user)
- ❌ Don't over-engineer for "what if" scenarios
- ❌ Don't build features I won't use
- ❌ Don't worry about backward compatibility (can break my own stuff)

---

## The Path Forward

### Phase 1: Foundation (Weeks 1-2)
- Wrap existing ComfyWatchman tools in MCP
- Basic workflow analysis and dependency resolution
- Integration with Claude Desktop

**Milestone:** Claude can analyze my workflows and tell me what's missing

### Phase 2: Generation (Weeks 3-4)
- Node type database
- Template-based workflow generation
- Connection validation

**Milestone:** Claude can generate simple txt2img workflows

### Phase 3: Intelligence (Weeks 5-6)
- Smart workflow builder
- Model compatibility checking
- Workflow repair

**Milestone:** Claude can create complex workflows with ControlNet, LoRAs, etc.

### Phase 4: Automation (Future)
- Event triggers
- Batch processing
- Workflow optimization

**Milestone:** Automated daily art generation pipelines

---

## Why This Project Matters (Personal)

### For Me:
- **Time Savings** - Stop wasting hours on workflow setup
- **Learning Tool** - AI explains what nodes do and why
- **Creative Freedom** - Focus on art direction, not technical plumbing
- **Experimentation** - Try new techniques without research overhead

### For the Community (If Shared):
- **Reference Implementation** - Shows how to build MCP servers for complex tools
- **ComfyUI Accessibility** - Makes ComfyUI approachable for non-experts
- **AI Integration Pattern** - Demonstrates AI-first tool design

---

## Conclusion

The ComfyWatchman MCP Server is about making ComfyUI accessible to AI assistants, which makes it more accessible to me. By combining ComfyWatchman's dependency resolution excellence with intelligent workflow generation, we eliminate the tedious parts of using ComfyUI while preserving its power and flexibility.

This isn't about replacing ComfyUI or building a competitor - it's about making the tool I already love more usable through AI assistance. The end goal is simple: have a conversation with Claude, get a working workflow, generate amazing images.

**Next Steps:** See `implementationPlan.md` for technical roadmap.
