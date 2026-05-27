# Architecture Decision: LangGraph StateGraph

**Date:** 2025-10-30

## Decision

The core orchestration logic for ComfyWatchman will be implemented using **LangGraph's StateGraph**.

## Rationale

The primary objective is to transform ComfyWatchman from a CLI tool into a long-running, intelligent workflow assistant. This requires a robust, stateful, and resilient orchestration framework. A `StateGraph` is the ideal choice for the following reasons:

1.  **Persistent State Management:** The vision requires the system to maintain state across its 2-hour monitoring cycles. This includes workflow statuses, model inventories, and system health checks. `StateGraph` provides a formal, typed structure for this state, which can be easily persisted using LangGraph's built-in checkpointers (e.g., SQLite for local, private storage).

2.  **Complex Conditional Logic:** The system's execution is highly conditional. For example, the main analysis cycle should only run if there is sufficient VRAM and ComfyUI is running. `StateGraph` provides powerful conditional edges that allow for this complex routing based on the current state.

3.  **Modularity and Specialization:** The architecture breaks down the problem into a series of specialized nodes (e.g., `scan_workflows`, `build_model_inventory`, `generate_reports`). `StateGraph` allows each of these components to be implemented as a distinct node, promoting separation of concerns and making the system easier to test and maintain.

4.  **Human-in-the-Loop Integration:** Phase 2 and beyond require human approval for actions like downloading models. `StateGraph` has first-class support for `interrupts`, allowing the graph to pause execution, wait for external input, and then resume, which is a perfect fit for this requirement.

5.  **Observability and Debugging:** The explicit state representation in `StateGraph` makes it much easier to debug and trace the execution of the system. The state at any given point is a clear, human-readable snapshot of the system's knowledge.

## Alternatives Considered

*   **MessageGraph:** While `MessageGraph` is excellent for conversational agents, it is less suited for this use case. The state is represented as a sequence of messages, which would be cumbersome for managing the structured, non-conversational state of ComfyWatchman.
*   **Custom Orchestrator:** Building a custom orchestration engine would be a significant undertaking, requiring manual implementation of state management, persistence, and conditional logic. This would be reinventing the wheel and would not be as robust or feature-rich as the battle-tested LangGraph framework.

In summary, `StateGraph` provides the right balance of structure, flexibility, and power to build the reliable, long-running, and intelligent system required by the project vision.
