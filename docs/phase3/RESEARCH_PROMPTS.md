# Phase 3 Research Prompts (DEFERRED)

> These research prompts should NOT be executed until Phase 1 & 2 are complete and owner approves Phase 3.

## R3.1: Local Vector Store Comparison
**Query:** "Compare ChromaDB, FAISS, and Qdrant for local-only vector storage. Need privacy-preserving, no-cloud option for storing embeddings of 100-1000 ComfyUI workflows. Evaluation criteria: performance, persistence, LangGraph integration."

## R3.2: Workflow Embedding Strategies
**Query:** "How to embed ComfyUI workflow JSON for semantic similarity search? Should I embed the raw JSON, extract structured features, or generate text summaries first? Need embeddings that capture both structure and intent."

## R3.3: RAG + LangGraph Integration Patterns
**Query:** "LangGraph examples of retrieval-augmented generation (RAG) with local vector stores. Need to retrieve relevant documents from ChromaDB/FAISS during LLM reasoning steps without external API calls."

## R3.4: Regression Detection Metrics
**Query:** "Metrics for detecting quality regressions in AI image generation workflows. Need automated, objective measures that don't require running the workflows. Consider parameter changes, model swaps, resolution changes."

## R3.5: Privacy-Preserving Embeddings
**Query:** "How to ensure vector embeddings don't leak sensitive information? Best practices for local-only embedding storage, preventing data exfiltration, and auditing vector store access."
