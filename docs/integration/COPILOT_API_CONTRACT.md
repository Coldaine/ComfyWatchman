# ComfyUI-Copilot Remote Integration Contract (Draft)

This document defines a contract-first interface for integrating ComfyWatchman with a remote ComfyUI-Copilot backend. It lets us remove the git submodule while keeping the same capabilities via stable HTTP APIs, clear versioning, and capability negotiation.

> Status: Draft for review. Safe to implement incrementally behind feature flags without breaking current local-submodule behavior.

---

## Goals

- Decouple our codebase from the Copilot source by talking to a well-defined API.
- Make Copilot features optional and discoverable at runtime.
- Enable graceful degradation when the server is absent or a capability is disabled.
- Keep the data shapes aligned with what our adapters already expect today (validation report with structured_summary, ModelScope search results, etc.).

## Deployment modes

- Local process: Copilot backend runs on the same machine (e.g., http://127.0.0.1:8899), no auth or local token.
- Remote service: Hosted Copilot backend with API key.

Both modes must expose the same APIs and schema.

## Capability discovery and health

- GET /health
  - Purpose: Liveness + quick version probe
  - Response 200 JSON:
    - status: "ok"
    - serverVersion: string (semver)
    - apiVersion: "v1"

- GET /v1/capabilities
  - Purpose: Feature negotiation and dependency visibility.
  - Response 200 JSON:
    - features: string[] (e.g., ["validation", "repair", "modelscope_search", "sql_state"]) 
    - dependencies: object
      - modelscope: { available: bool, version?: string }
      - llmProviders: string[] (e.g., ["openai", "claude", "local-llm"])
      - database: { type?: "sqlite|postgres|none", available: bool }
    - limits: object (timeouts, rate limits, max payload sizes)

Clients should cache capabilities briefly and branch behavior accordingly. If a feature is missing, adapters should silently degrade to our local fallback.

## Authentication

- Local mode: none by default
- Remote mode: header X-API-Key: <token>
- 401/403 if missing/invalid

## Error model

- On errors, endpoints return non-200 with JSON body:
  - error: { code: string, message: string, details?: any }

Common codes: invalid_input, timeout, upstream_unavailable, not_supported, internal_error

## Endpoints and Schemas (v1)

### 1) Validate workflow

- POST /v1/validate
- Purpose: Analyze a ComfyUI workflow for structural, parameter, and node issues
- Request JSON:
  - workflow: object | string
    - Either the full ComfyUI workflow JSON object, or a string containing the workflow JSON
  - options?: object
    - session_id?: string
    - locale?: string
    - strict?: boolean (default false)
- Response 200 JSON (ValidationReport):
  - status: "ok" | "issues_found" | "error"
  - errors: array<{ code: string, message: string, path?: string }>
  - warnings: array<{ code: string, message: string, path?: string }>
  - structured_summary?: array<object>
    - Items may include: 
      - { type: "param_update", data: { node_id: string, param: string, from: any, to: any } }
      - { type: "workflow_update", data: { reason?: string, workflow_data: object } }
  - meta?: { duration_ms?: number, engine_version?: string }

Notes:
- The presence of a structured_summary item with type "workflow_update" and data.workflow_data implies a repaired workflow is available (see repair semantics).

### 2) Repair workflow (explicit)

- POST /v1/repair
- Purpose: Attempt auto-repair of a workflow and return the modified workflow JSON if successful
- Request JSON:
  - workflow: object | string
  - options?: { session_id?: string, locale?: string, max_fixes?: number }
- Response 200 JSON:
  - status: "repaired" | "no_change" | "error"
  - repaired_workflow?: object
  - report?: ValidationReport (same shape as validate)

Notes:
- If the validate endpoint already returns a workflow_update in structured_summary, clients may use that and skip /v1/repair.

### 3) ModelScope search

- GET /v1/modelscope/search?q=QUERY&limit=20
- Purpose: Query ModelScope for models matching the text query
- Response 200 JSON:
  - results: array<ModelCandidate>
  - meta?: { total?: number, source: "modelscope", duration_ms?: number }

ModelCandidate (example shape):
- id: string
- name: string
- type?: string (e.g., "checkpoint", "lora")
- size_mb?: number
- download_url?: string
- score?: number
- tags?: string[]
- extra?: object (raw provider fields)

### 4) Optional: SQL state interactions

If the server exposes a state store, endpoints can include:
- POST /v1/state/save
- GET /v1/state/{key}
- DELETE /v1/state/{key}

These must be listed in capabilities or they’re considered unavailable.

## Versioning strategy

- Base path includes version: /v1/...
- Server advertises apiVersion in /health and /v1/capabilities.
- Backward-compatible changes: additive fields only.
- Breaking changes -> bump to /v2 and include both for a deprecation window.

## Timeouts and performance

- Clients should default to sensible timeouts (e.g., 15s validate, 30s repair, 10s search), configurable via our config.toml.
- Server should stream or chunk large responses if needed, but v1 assumes JSON bodies under a reasonable size (documented in limits).

## Security considerations

- Remote deployments should require HTTPS and API keys.
- Avoid returning sensitive environment information in errors. Capabilities can list booleans and versions, not raw tokens or paths.

## Migration plan (high level)

1) Ship this contract and add a client adapter in ComfyWatchman (behind feature flags).
2) Keep current submodule path for local/dev fallback during transition.
3) Implement server endpoints in the Copilot backend (or add a thin API layer if already present).
4) Add integration tests that hit a test server and validate the contract.
5) Deprecate submodule path once the server route is mature.

## Minimal client expectations (from our side)

- Health check before feature calls; retry + degrade on failure.
- Capability discovery to decide which adapters to enable.
- Explicit error handling mapped to our logs and user-facing messages.
- No hard dependency: core downloader/search continues to work offline.

## Example requests

Validate (local):

POST http://127.0.0.1:8899/v1/validate
Content-Type: application/json

{
  "workflow": { "last_node_id": 12, "nodes": [ /* ... */ ] },
  "options": { "session_id": "cw-run-123" }
}

Response:

200 OK
{
  "status": "issues_found",
  "errors": [],
  "warnings": [ { "code": "missing_model", "message": "Model X not found", "path": "nodes[5].inputs.model" } ],
  "structured_summary": [
    { "type": "param_update", "data": { "node_id": "5", "param": "scheduler", "from": "euler", "to": "dpm++" }},
    { "type": "workflow_update", "data": { "reason": "fix missing model path", "workflow_data": { /* repaired workflow JSON */ }}}
  ],
  "meta": { "duration_ms": 1240, "engine_version": "2.1.0" }
}

ModelScope search:

GET https://copilot.example.com/v1/modelscope/search?q=pony+diffusion&limit=10
X-API-Key: sk-...redacted

Response:

200 OK
{
  "results": [
    { "id": "ms:123", "name": "PonyDiffusion V6 XL", "type": "checkpoint", "score": 0.93, "download_url": "https://...", "tags": ["xl","pony"]}
  ],
  "meta": { "total": 1, "source": "modelscope", "duration_ms": 680 }
}

---

By codifying the API surface and adding capability discovery, we don’t need the server’s source code to understand what’s available. We treat the server as a product with a versioned contract, and we enforce that contract with integration tests and graceful fallbacks.
