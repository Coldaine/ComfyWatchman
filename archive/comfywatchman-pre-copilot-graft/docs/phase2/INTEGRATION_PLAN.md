# Phase 2 Integration Plan: Knowledge-Guided Resolution

## Overview
Extend Phase 1 system with LLM-powered model search, knowledge base integration, and intelligent dependency resolution that can explain WHY models are chosen and WHEN it's uncertain.

## New Components

### 2.1: Knowledge Base Builder
**Purpose:** Maintain plain-text document pack for LLM grounding
**Structure:**
```
knowledge/
├── nodes/
│ ├── samplers.md
│ ├── loaders.md
│ └── ...
├── models/
│ ├── checkpoints-sdxl.md
│ ├── loras-concepts.md
│ └── ...
├── workflows/
│ ├── inpainting-patterns.md
│ ├── upscaling-patterns.md
│ └── ...
└── schemas/
 ├── auto-inpaint-frontend.md
 ├── image-cycling-frontend.md
 └── dynamic-prompt-generator.md
```

**Refresh Strategy:** Update docs on demand or weekly from curated sources

### 2.2: Qwen Agent Search Orchestrator
**Purpose:** Use Qwen LLM to coordinate multi-backend search with reasoning
**Architecture:**
```python
class QwenSearchAgent:
 def search(self, model_name: str, context: Dict) -> SearchResult:
 # 1. Extract keywords from model name
 keywords = self.extract_keywords(model_name, context)
 # 2. Decide search strategy
 strategy = self.plan_search_strategy(keywords)
 # 3. Execute searches (Civitai, HuggingFace, etc.)
 results = self.execute_searches(strategy)
 # 4. Validate and rank results
 validated = self.validate_results(results, model_name)
 # 5. Return with confidence score
 return self.rank_and_return(validated)
```

**Key Features:**
- Reasoning logged at each step
- Confidence scoring (0-100%)
- UNCERTAIN status when confidence < 70%
- Tool usage tracked for audit

### 2.3: LLM Workflow Explainer
**Purpose:** Generate human-readable explanations of workflow intent
**Inputs:**
- Workflow JSON
- Knowledge base context (retrieved docs)
- Model inventory

**Outputs:**
- Purpose statement
- Expected outputs
- Hardware requirements estimate
- Quality/speed trade-offs

**Example Output:**
```markdown
## Workflow: turbo-upscale-x4.json

**Purpose:** Fast 4x image upscaling using SDXL Turbo for speed

**Process:**
1. Loads SDXL Turbo checkpoint (low-quality, fast)
2. Applies ControlNet Tile for structure preservation
3. Upscales in 2x2 tile batches
4. Minimal denoising steps (4-8)

**Hardware Requirements:**
- VRAM: ~6GB
- Speed: ~30 sec for 1024x1024 -> 4096x4096

**Trade-offs:**
- ✅ Very fast
- ⚠️ Lower quality than full SDXL
- ⚠️ May have tile seams on complex images
```

### 2.4: Uncertainty Handler (NEW)
**Purpose:** Present multiple candidates to user when uncertain
**Triggers:** Confidence < 70% OR multiple good matches
**Outputs:**
```json
{
"status": "UNCERTAIN",
"model_name": "realistic_vision_v5.safetensors",
"candidates": [
 {
"name": "Realistic Vision V5.1",
"source": "civitai",
"confidence": 0.85,
"reason": "Exact filename match",
"url": "https://civitai.com/models/12345"
 },
 {
"name": "Realistic Vision V5.0",
"source": "civitai",
"confidence": 0.75,
"reason": "Similar filename, older version",
"url": "https://civitai.com/models/12340"
 }
 ],
"recommendation": "First candidate is likely correct (exact filename match)",
"action": "Please review and approve download"
}
```

## Updated LangGraph Workflow

**New Nodes Added to Phase 1 Graph:**
- `load_knowledge_base` - Loads relevant docs into context
- `explain_workflows` - LLM generates workflow explanations
- `agentic_search` - Qwen agent searches for missing models
- `handle_uncertainty` - Prompts user when confidence low
- `download_approved` - Downloads only approved models

**Human-in-the-Loop Integration:**
```python
workflow.add_node("handle_uncertainty", present_candidates_to_user)
workflow.add_conditional_edges(
"handle_uncertainty",
lambda state: "approved" if state["user_approved"] else "skip",
 {
"approved": "download_approved",
"skip": END
 }
)
```

## Implementation Milestones

| Milestone | Deliverable | Time Estimate |
|-----------|-------------|---------------|
| M2.1 | Knowledge base structure | 3 days |
| M2.2 | Document pack initial content | 5 days |
| M2.3 | Qwen agent search integration | 5 days |
| M2.4 | LLM workflow explainer | 4 days |
| M2.5 | Uncertainty handler UI | 3 days |
| M2.6 | Approval token system | 3 days |
| M2.7 | Download queue with approval gates | 3 days |
| M2.8 | End-to-end testing | 4 days |
| **TOTAL** | **Phase 2 Complete** | **~4-5 weeks** |

## Success Criteria

- [ ] Knowledge base contains 50+ curated documents
- [ ] LLM explanations rated ≥4/5 for clarity by owner
- [ ] Agentic search resolves 90%+ of missing models
- [ ] Uncertainty handler triggers for ambiguous cases
- [ ] No downloads occur without explicit approval
- [ ] Search reasoning logged for audit

## Open Questions

1. Which Qwen model version? (Qwen2.5 recommended)
2. Local vs. API-based LLM inference?
3. Knowledge base update cadence?
4. How to source initial knowledge base content?
```