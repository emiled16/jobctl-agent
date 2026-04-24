# Plan v1.0

## Context
The current orchestration flow mixes two different responsibilities:

- `src/agents/orchestration_chat` contains an agent implementation, but it reads and writes `src/workflows/orchestration/state.py::OrchestrationState` directly.
- The agent produces workflow routing fields such as `next_node`, workflow status fields such as `pending_user_action`, and workflow-owned payloads such as `resume_ingestion_state`.
- Tool execution and state updates are encoded through `JOBCTL_ACTION` strings and decoded later into workflow mutations, which makes the state lifecycle harder to follow.

This creates tight coupling between the `agents` package and the `workflows` package, weakens naming clarity, and makes the orchestration state harder to reason about.

The target design is:

- `src/agents` owns reusable agent logic and agent-local state only.
- `src/workflows` owns LangGraph graph definitions, routing, graph state, and translation between graph state and agent inputs/outputs.
- The current `orchestration_chat` agent is renamed to `chat_agent`.
- The current `JobctlAgentState` is replaced with `ChatAgentState`.
- Backward compatibility is not required. Legacy modules, names, and compatibility shims can be removed.

## Milestones

### M1: Define Clear Agent and Workflow Boundaries

#### Task T1: Define the target package contracts for agents and workflows
- Description: Introduce an explicit architectural contract that separates agent concerns from workflow concerns. Document that agents consume agent-local context and produce agent-local outcomes, while workflows own graph state, node routing, subgraph invocation, and persistence of workflow progress.
- Outputs: A written contract for `src/agents` and `src/workflows`, including ownership of state, routing, tool binding, and workflow transitions.
- Dependencies: None

#### Task T2: Replace workflow-owned agent inputs with a dedicated `ChatAgentContext`
- Description: Define a dedicated input object for the chat agent that contains only the data the agent actually needs, such as conversation history, latest user input, resume availability, current resume facts, and whether the user is expected to provide a source. Remove direct use of `OrchestrationState` from agent modules.
- Inputs: Existing `OrchestrationState`, chat prompt requirements, resume inspection needs.
- Outputs: A `ChatAgentContext` type owned by the `agents.chat_agent` package and used by the chat agent entrypoint.
- Dependencies: T1

#### Task T3: Replace workflow mutations with a dedicated `ChatAgentResult`
- Description: Define an explicit result type returned by the chat agent. The result should express domain outcomes such as `reply`, `intent`, `ingestion_request`, `inspection_request`, or `awaiting_user_input`, without embedding LangGraph routing fields like `next_node` or workflow-owned status mutations.
- Inputs: Current action kinds in `langchain_actions.py`, current workflow routing requirements.
- Outputs: A `ChatAgentResult` contract that is interpreted by orchestration workflow nodes.
- Dependencies: T1

### M2: Refactor the Chat Agent Into an Agent-Local Module

#### Task T4: Rename `orchestration_chat` to `chat_agent` and replace `JobctlAgentState` with `ChatAgentState`
- Description: Rename the package from `src/agents/orchestration_chat` to `src/agents/chat_agent`, update imports, and replace the misleading `JobctlAgentState` name with `ChatAgentState`. Remove legacy names rather than keeping aliases.
- Outputs: A renamed agent package with consistent naming across modules, tests, and imports.
- Dependencies: T2, T3

#### Task T5: Collapse agent internals around a single public `run_chat_agent` entrypoint
- Description: Reorganize the chat agent so the public runner accepts `ChatAgentContext`, binds prompt and tools, invokes LangChain, and returns `ChatAgentResult`. Keep message conversion, prompt generation, and tool binding internal to the agent package. Remove any logic that directly constructs workflow updates.
- Inputs: Existing `runner.py`, `prompts/v1.py`, `utils.py`, tool modules.
- Outputs: A clean agent entrypoint with a minimal public surface and no imports from `src.workflows`.
- Dependencies: T2, T3, T4

#### Task T6: Replace encoded workflow actions with typed agent tool outcomes
- Description: Remove the `JOBCTL_ACTION` string protocol and the decode-and-restore cycle. Refactor tools and post-processing so tool calls produce structured agent-local outcomes that can be converted directly into `ChatAgentResult` without string prefixes or workflow state reconstruction.
- Inputs: Existing `langchain_actions.py`, `utils.extract_action`, `utils.restore_action`, tool implementations.
- Outputs: A simpler tool-to-result pipeline with typed data flow and no string-encoded action transport.
- Dependencies: T3, T5

#### Task T7: Reduce state-manipulation complexity inside the agent
- Description: Eliminate the broad `state_update_from_action` function and replace it with focused transformations: message transcript update, domain outcome selection, and agent result assembly. Keep each transformation local and explicit so the agent’s control flow is easy to follow.
- Outputs: Small, single-purpose functions for transcript handling and result assembly.
- Dependencies: T5, T6

### M3: Simplify Orchestration Workflow State and Node Responsibilities

#### Task T8: Redesign `OrchestrationState` around workflow-owned data only
- Description: Refactor `src/workflows/orchestration/state.py` so it contains graph-owned state only: conversation transcript, current reply, resume facts, optional ingestion substate, and explicit workflow progress needed across turns. Remove fields that are only temporary control signals for the agent implementation unless they are genuinely workflow-owned.
- Inputs: Current `OrchestrationState`, chat-agent contract from T2 and T3.
- Outputs: A smaller `OrchestrationState` with clearer field ownership and fewer transient mutation paths.
- Dependencies: T2, T3

#### Task T9: Move agent-to-workflow translation into the chat workflow node
- Description: Refactor `src/workflows/orchestration/nodes/chat_agent.py` so the node builds `ChatAgentContext` from `OrchestrationState`, invokes `run_chat_agent`, then translates `ChatAgentResult` into workflow updates and graph routing. This node becomes the only layer that knows both schemas.
- Inputs: `ChatAgentContext`, `ChatAgentResult`, redesigned `OrchestrationState`.
- Outputs: A clear adapter boundary between the chat agent and the orchestration graph.
- Dependencies: T5, T8

#### Task T10: Replace `next_node` string routing with explicit routing derived from workflow state
- Description: Remove the pattern where the agent writes `next_node` into shared state. Either derive routing directly from workflow-owned fields after the chat node runs, or introduce a workflow-local routing enum or command field that is set by the node adapter rather than by the agent.
- Inputs: Existing `route_after_chat_agent`, current `next_node` field, chat node adapter from T9.
- Outputs: Simpler graph routing with ownership kept inside the workflow layer.
- Dependencies: T8, T9

#### Task T11: Simplify pending-ingestion flow into an explicit workflow interaction state
- Description: Replace the current `pending_user_action` plus `status` interplay with a clearer workflow-owned interaction model, for example an explicit `awaiting_resume_source` or `interaction_state` field. Keep the semantics narrow and make the graph/node logic depend on one obvious source of truth.
- Inputs: Current `pending_user_action`, `status`, resume-source follow-up behavior.
- Outputs: A workflow state model for multi-turn follow-up that is easier to reason about than the current combination of flags.
- Dependencies: T8, T9

### M4: Align Application Surface and Tests With the New Architecture

#### Task T12: Rename orchestration workflow surface to match the new mental model
- Description: Review top-level module names and public functions to align with the new separation. Keep `workflows` for LangGraph orchestration and `agents` for reusable agent logic. Rename runner and node modules where that improves clarity, and remove stale terminology inherited from `orchestration_chat`.
- Inputs: Existing module tree under `src/app`, `src/agents`, and `src/workflows`.
- Outputs: A naming scheme that matches package responsibilities and removes misleading legacy names.
- Dependencies: T4, T9, T10

#### Task T13: Rewrite orchestration tests around agent contract and workflow behavior
- Description: Split tests by concern. Add unit tests for `agents.chat_agent` result behavior and separate workflow tests for routing, resume ingestion delegation, and cross-turn state handling. Remove tests that depend on legacy encoded-action internals or old names.
- Inputs: Current `tests/unit/test_orchestration.py`, new agent and workflow contracts.
- Outputs: Test coverage aligned with the new architecture and module boundaries.
- Dependencies: T6, T9, T10, T11

#### Task T14: Remove legacy modules and dead helpers after migration
- Description: Delete obsolete modules, helpers, imports, and compatibility code left behind by the refactor, including the old `orchestration_chat` package and any string-action compatibility helpers that are no longer used.
- Outputs: A clean tree without duplicate architectures or migration leftovers.
- Dependencies: T12, T13

## Proposed Target Structure

```text
src/
  agents/
    chat_agent/
      __init__.py
      runner.py
      state.py
      context.py
      result.py
      prompts.py
      tools.py
      inspection.py
      ingestion_request.py
    resume_section_extraction/
      ...
  workflows/
    orchestration/
      __init__.py
      state.py
      graph.py
      runner.py
      nodes/
        chat_agent.py
        resume_ingestion.py
    resume_ingestion/
      ...
```

## Design Decisions

- Agents may know domain concepts such as resume ingestion requests and resume inspection responses, but they must not know LangGraph routing details or workflow-owned state containers.
- Workflows may translate agent outcomes into graph transitions, but they must not depend on agent-internal helper protocols such as encoded tool-action strings.
- The chat agent should receive a minimal context object, not a mutable workflow state bag.
- The orchestration workflow should keep the multi-turn interaction model explicit and narrow, with one obvious field representing a pending user follow-up.
- Names should reflect role and scope directly: `chat_agent` for the agent package, `ChatAgentState` for LangChain agent state, and `OrchestrationState` only for the LangGraph workflow state.

## Revisions
- v1.0: Initial version.
