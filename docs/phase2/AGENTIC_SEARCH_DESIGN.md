# Agentic Search Design

## Overview
This document outlines the design of the Qwen-powered agentic search workflow, which is responsible for intelligently finding and resolving missing model dependencies.

## Architecture
The agentic search process will be orchestrated by a `QwenSearchAgent` class. This class will encapsulate the logic for planning, executing, and validating searches. The agent will be exposed as a tool that can be called from within the main LangGraph workflow.

### Core Components
1.  **Search Planner (LLM):** The Qwen LLM will be used to generate a search strategy based on the name of the missing model and the context from the workflow.
2.  **Tool Executor:** A simple tool executor will be responsible for calling the various search backends (e.g., Civitai API, HuggingFace API).
3.  **Result Validator (LLM):** The Qwen LLM will be used to validate and rank the search results, comparing them against the original model name and context to determine the best match.

### `QwenSearchAgent` Pseudocode
```python
class QwenSearchAgent:
    def __init__(self, llm, search_tools):
        self.llm = llm
        self.search_tools = search_tools

    def search(self, model_name: str, context: Dict) -> SearchResult:
        # 1. Plan the search strategy
        strategy_prompt = self.create_strategy_prompt(model_name, context)
        strategy = self.llm.invoke(strategy_prompt) # Returns a structured plan

        # 2. Execute the searches
        search_results = []
        for step in strategy['steps']:
            tool_name = step['tool']
            query = step['query']
            if tool_name in self.search_tools:
                results = self.search_tools[tool_name].invoke(query)
                search_results.extend(results)

        # 3. Validate and rank the results
        validation_prompt = self.create_validation_prompt(model_name, search_results)
        validated_results = self.llm.invoke(validation_prompt) # Returns ranked list with confidence scores

        return validated_results
```

## Qwen Prompt Templates

### 1. Strategy Prompt
This prompt will instruct the LLM to create a search plan.

```jinja2
You are an expert at finding AI models for ComfyUI.
Your task is to create a search strategy to find the model named: `{{ model_name }}`.

Here is some context from the workflow where this model is used:
{{ context | tojson }}

Based on the model name and context, create a plan consisting of a series of search steps.
For each step, specify the tool to use (e.g., `civitai_search`, `huggingface_search`) and the optimal search query.

Return a JSON object with the following structure:
{
  "steps": [
    {"tool": "civitai_search", "query": "a_specific_query"},
    {"tool": "huggingface_search", "query": "another_query"}
  ]
}
```

### 2. Validation Prompt
This prompt will instruct the LLM to evaluate the search results.

```jinja2
You are an expert at validating AI models for ComfyUI.
You are looking for a model named: `{{ model_name }}`.

The following search results were found:
{{ search_results | tojson }}

Your task is to evaluate these results and return a ranked list of candidates.
For each candidate, provide a confidence score (0-100) and a brief reason for your assessment.
A perfect match on the filename should have a high confidence score.

Return a JSON object with the following structure:
{
  "status": "UNCERTAIN" or "FOUND",
  "candidates": [
    {
      "name": "Candidate Name",
      "source": "civitai",
      "confidence": 95,
      "reason": "Exact filename match.",
      "url": "..."
    }
  ]
}
```

## Validation Rules
The LLM-driven validation will be supplemented by the following hard-coded rules:

*   **Exact Filename Match:** A result with a filename that exactly matches the missing model name will be given a high priority.
*   **Model Type Match:** If the workflow context provides a model type (e.g., "checkpoint", "lora"), results that do not match this type will be penalized.
*   **Source Preference:** (Optional) A preferred source (e.g., Civitai) can be configured to be ranked higher.

## Logging and Tracing
The entire agentic search process will be logged for audit and debugging purposes:

*   The generated search strategy will be logged.
*   Each tool call (search query) will be logged.
*   The raw search results will be logged.
*   The final validated results and confidence scores will be logged.

This detailed logging will provide a clear trace of the agent's reasoning process.
