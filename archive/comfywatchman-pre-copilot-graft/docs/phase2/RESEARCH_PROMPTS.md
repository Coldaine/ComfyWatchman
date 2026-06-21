# Phase 2 Research Prompts

## R2.1: Qwen Agent Framework
**Query:** "How to implement an agentic search workflow using Qwen LLM with LangGraph? Need the LLM to decide search strategies, call multiple search tools (Civitai API, HuggingFace), validate results, and return confidence scores. Looking for tool-calling patterns with Qwen."

---

## R2.2: Local Knowledge Base for LLM Grounding
**Query:** "Best practices for creating a local plain-text knowledge base to ground LLM responses. Need to maintain markdown documents about ComfyUI nodes, models, and workflows. How to structure for easy retrieval without a vector database?"

---

## R2.3: LLM Confidence Scoring
**Query:** "How to extract confidence scores from LLM outputs when searching/matching? Need the model to return a 0-100% confidence along with its reasoning. Prefer techniques that work with open-source models like Qwen."

---

## R2.4: Human-in-the-Loop with LangGraph
**Query:** "LangGraph patterns for human approval gates. Need to pause workflow execution, present options to user, wait for approval (with timeout), then resume. Looking for interrupt/resume patterns."

---

## R2.5: Workflow Intent Analysis
**Query:** "Using LLMs to analyze ComfyUI workflow JSON and extract intent/purpose. What context should be provided to the LLM? How to structure prompts for consistent, accurate explanations?"

---

## R2.6: Multi-Source Search Ranking
**Query:** "Algorithm for ranking search results from multiple sources (Civitai, HuggingFace, ModelScope) when looking for AI models. How to normalize confidence scores across different APIs and filename matching strategies?"

---

## R2.7: Approval Token Security
**Query:** "Secure implementation of time-limited, single-use approval tokens for authorizing agent actions. Need local-only implementation (no auth server) with cryptographic verification and expiration."
