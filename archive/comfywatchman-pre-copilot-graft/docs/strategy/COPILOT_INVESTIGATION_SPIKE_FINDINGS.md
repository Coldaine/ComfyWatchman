# Copilot Investigation Spike Findings

Date: 2026-05-27

## Summary

The fastest path to "whip me up a ComfyUI workflow that does X" is to use
ComfyUI-Copilot as the product shell, then selectively port the local Agent Mode
work from `vehoelite` PR #130. ComfyWatchman should not remain the top-level UI
or agent shell. Its useful role is as a readiness and dependency engine exposed
to Copilot as local tools after the Copilot shell is live.

This is not yet an adoption plan. It is the investigation result that should
gate the longer implementation plan.

## Repositories Inspected

- Upstream Copilot: `AIDC-AI/ComfyUI-Copilot`
  at `f04a01a9fce8e3cb21f2a21a14fc971d5753dc36`.
- PR fork: `vehoelite/ComfyUI-Copilot`, PR #130 head
  at `2916691782d159b1327b93ac6662c37051e657aa`.
- Local clones were created outside this repo so ComfyWatchman history stayed
  clean during inspection.
- ComfyWatchman was inspected only for salvage value.

## Evidence Snapshot

- Upstream Copilot documents the hosted API service suspension and says users
  must provide their own API key/base URL to continue agent capabilities:
  [`README.md` at `f04a01a`](https://github.com/AIDC-AI/ComfyUI-Copilot/blob/f04a01a9fce8e3cb21f2a21a14fc971d5753dc36/README.md#L51).
- Upstream already advertises prompt-to-workflow creation, workflow debug, node
  recommendation, model recommendation, and downstream subgraph recommendation:
  [`README.md` lines 88-128](https://github.com/AIDC-AI/ComfyUI-Copilot/blob/f04a01a9fce8e3cb21f2a21a14fc971d5753dc36/README.md#L88-L128).
- PR #130 adds the Agent Mode backend route:
  [`conversation_api.py` at `2916691`](https://github.com/vehoelite/ComfyUI-Copilot/blob/2916691782d159b1327b93ac6662c37051e657aa/backend/controller/conversation_api.py#L1092).
- PR #130 adds the frontend Agent Mode stream client and toggle path:
  [`workflowChatApi.ts`](https://github.com/vehoelite/ComfyUI-Copilot/blob/2916691782d159b1327b93ac6662c37051e657aa/ui/src/apis/workflowChatApi.ts#L893)
  and [`workflowChat.tsx`](https://github.com/vehoelite/ComfyUI-Copilot/blob/2916691782d159b1327b93ac6662c37051e657aa/ui/src/workflowChat/workflowChat.tsx#L398).
- PR #130 implements local constrained mode for Groq/LM Studio and skips MCP in
  that mode:
  [`agent_mode.py` provider detection](https://github.com/vehoelite/ComfyUI-Copilot/blob/2916691782d159b1327b93ac6662c37051e657aa/backend/service/agent_mode.py#L105)
  and [`agent_mode.py` local tools](https://github.com/vehoelite/ComfyUI-Copilot/blob/2916691782d159b1327b93ac6662c37051e657aa/backend/service/agent_mode.py#L158).
- PR #130 adds tool budgets and loop-prevention limits:
  [`agent_mode_tools.py` per-tool limits](https://github.com/vehoelite/ComfyUI-Copilot/blob/2916691782d159b1327b93ac6662c37051e657aa/backend/service/agent_mode_tools.py#L155)
  and [`agent_mode_tools.py` global limit](https://github.com/vehoelite/ComfyUI-Copilot/blob/2916691782d159b1327b93ac6662c37051e657aa/backend/service/agent_mode_tools.py#L164).
- PR #130 still contains hosted defaults:
  [`globals.py` backend URL](https://github.com/vehoelite/ComfyUI-Copilot/blob/2916691782d159b1327b93ac6662c37051e657aa/backend/utils/globals.py#L102)
  and [`globals.py` LLM default URL](https://github.com/vehoelite/ComfyUI-Copilot/blob/2916691782d159b1327b93ac6662c37051e657aa/backend/utils/globals.py#L108).
- PR #130's `validate_workflow` calls the same gateway used for execution, and
  that gateway posts to ComfyUI `/api/prompt`:
  [`agent_mode_tools.py`](https://github.com/vehoelite/ComfyUI-Copilot/blob/2916691782d159b1327b93ac6662c37051e657aa/backend/service/agent_mode_tools.py#L366)
  and [`comfy_gateway.py`](https://github.com/vehoelite/ComfyUI-Copilot/blob/2916691782d159b1327b93ac6662c37051e657aa/backend/utils/comfy_gateway.py#L54).
- ComfyWatchman salvage candidates are concrete source modules:
  `src/comfywatchman/scanner.py`, `src/comfywatchman/inventory.py`,
  `src/comfywatchman/search.py`, and `src/comfywatchman/download.py`.

## Recommendation

Fork upstream `AIDC-AI/ComfyUI-Copilot` as the product shell, then port only the
selected PR #130 pieces that support local-first Agent Mode:

- Agent Mode route and orchestration.
- Provider configuration and LM Studio/OpenAI-compatible fixes.
- Tool loop limits, timeout handling, and loop prevention.
- Workflow save/read tools, node search, object info, and local model listing.
- Frontend Agent Mode toggle/progress UI.

Do not adopt the `vehoelite` fork wholesale yet. It is valuable, but it also
contains broad generated docs/assets, hosted defaults, remote MCP paths, and
tool semantics that need review before real use.

Do not port Copilot into ComfyWatchman. Copilot already owns the right runtime:
it is a ComfyUI custom node with in-process access to ComfyUI routes, canvas
state, React UI, workflow cards, debug/rewrite flows, and PromptServer routes.
Rebuilding that shell here would waste time.

## Feature Map

| What we want | Upstream Copilot has | PR #130 adds | ComfyWatchman can contribute | Missing or risky |
| --- | --- | --- | --- | --- |
| Natural-language workflow creation | Prompt-to-workflow chat and workflow cards; README documents "Generate First Version Workflow". | Agent Mode can plan and save workflows directly through tools. | Readiness checks after workflow creation. | Local constrained mode must be tested against a real ComfyUI install. |
| Current canvas/workflow context | Frontend saves `app.graphToPrompt()` before chat; rewrite/debug tools read session workflow. | Agent tools read current workflow from session storage. | Dependency scanner can analyze the resulting workflow. | Need one canonical current-workflow adapter; avoid duplicate state paths. |
| Node and object awareness | Node recommendations, selected-node context, downstream subgraph recommendations. | Local `search_nodes` and `get_node_details` use `/api/object_info`. | Missing custom-node detection and readiness reporting. | Installed-node search is textual and should be hardened with better ranking. |
| Local model awareness | Model recommendation/download UX exists. | `list_available_models` reads ComfyUI `folder_paths`. | Model inventory and model-type mapping. | PR #130 model listing is local only; ComfyWatchman search is needed for external discovery. |
| Save generated workflow | Upstream can load accepted workflow cards to canvas and save checkpoints. | `save_workflow` persists workflow data and emits frontend `workflow_update` events. | Validate dependencies before accepting or executing. | Need rollback/restore policy around mutating canvas state. |
| Validate workflow | Debug flow can run validation-like checks. | `validate_workflow` exists. | Dependency readiness report can be true dry-run validation. | PR #130 `validate_workflow` calls ComfyUI `/api/prompt`; that may enqueue execution, so it is not a safe dry-run validator. |
| Execute workflow | Upstream debug/runtime paths can call ComfyUI. | `execute_workflow` and result polling exist. | Readiness gate before execution. | Execution must remain explicit or policy-controlled; not automatic during early Agent Mode testing. |
| Run without suspended hosted service | README says hosted API service is suspended but custom keys/base URLs can be used. | LM Studio/Groq constrained mode skips hosted MCP and uses local tools only. | Offline/local dependency engine. | Defaults still point at hosted OnRender URLs; OpenAI/Anthropic path still uses remote MCP. |
| Dependency resolution and install planning | Some model download UX exists. | Not the main focus. | Scanner, inventory, Civitai/Qwen search, download script planning. | Downloads/custom-node installs should start as approval-first plans, not agent mutations. |
| Dashboard/product UX | Copilot has the ComfyUI-integrated chat shell. | Agent Mode progress/toggle UI. | Dashboard mocks contain useful readiness concepts. | ComfyWatchman dashboard is mock-backed and should not compete with Copilot shell. |

## Acceptance Checks

Can a local agent take a natural-language request and produce a valid workflow?

- Code path exists in PR #130, especially constrained local mode using
  `search_nodes`, `get_node_details`, `list_available_models`, and
  `save_workflow`.
- This is not live-verified yet. The next gate is installing the fork in a real
  ComfyUI environment and proving one prompt creates a loadable workflow.

Can it read current ComfyUI state?

- Yes, partly. Copilot reads canvas/workflow checkpoints from the frontend and
  PR #130 reads `/api/object_info`, session workflow data, and ComfyUI model
  lists through `folder_paths`.

Can it save, validate, and optionally execute a workflow?

- Save: yes, PR #130 has `save_workflow` and emits workflow update events.
- Execute: yes, PR #130 has `execute_workflow`.
- Validate: risky. PR #130's `validate_workflow` says it does not run the
  workflow, but the implementation calls `ComfyGateway.run_prompt()`, which
  posts to `/api/prompt`. Treat this as execution until proven otherwise.

Can it run without the suspended hosted service?

- Partially. LM Studio and Groq constrained mode skip hosted MCP and rely on
  local tools.
- Not fully. Hosted OnRender defaults remain, and the OpenAI/Anthropic path
  still uses remote MCP servers. Local-first hardening is required before this
  is dependable.

Can ComfyWatchman add something Copilot lacks?

- Yes. ComfyWatchman has better dependency scanning, model inventory, model
  search, readiness reporting, and install/download planning concepts.
- It should contribute those as tools or a small local service after Copilot is
  working, not as the main app shell.

## ComfyWatchman Salvage Decision

Keep and port as local tools:

- `WorkflowScanner` dependency extraction.
- `ModelInventory` local model inventory.
- `SearchResult` / `ModelSearch` external model search shape.
- Readiness report concepts from the core/dashboard work.
- Download script generation, but only after an approval-first dry-run plan
  exists.

Defer or discard:

- ComfyWatchman dashboard as the product shell.
- Current Copilot adapter direction if it requires importing Copilot into
  ComfyWatchman.
- Root-level experimental tests/scripts that are not part of the configured
  pytest suite.
- Direct mutation/download tools until approval, rollback, and Manager-aware
  install behavior are defined.

## Next Gate Before Longer Plan

The longer plan should not start with dashboard or CLI hardening. It should
start with a live Copilot proof:

1. Install upstream Copilot or a forked branch in the target ComfyUI environment.
2. Port the minimum PR #130 Agent Mode/provider/UI pieces.
3. Configure LM Studio or another OpenAI-compatible local provider.
4. Run one prompt that creates a valid workflow and saves it to the canvas.
5. Replace unsafe "validation" with a true dry-run/readiness check before
   execution is trusted.
6. Expose `WorkflowScanner` (`src/comfywatchman/scanner.py`) as a read-only
   ComfyWatchman tool callable by Copilot Agent Mode for dependency scanning.

If that proof works, write the longer implementation plan around Copilot as the
shell and ComfyWatchman as local readiness/dependency tooling. If it fails for
structural reasons, abandon this repo as product shell only after identifying
whether a thinner Copilot fork or another ComfyUI-native shell can own the same
goal faster.
