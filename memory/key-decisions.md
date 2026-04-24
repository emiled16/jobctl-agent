## [2026-04-23] D-001: Keep the chat agent isolated behind explicit context and result types
- Plan: v1.0
- Context: The previous chat agent read and wrote OrchestrationState directly, which coupled the agent package to the orchestration workflow and made state mutations difficult to follow.
- Options considered:
  - Keep a shared TypedDict between the agent and workflow
  - Introduce a narrow ChatAgentContext and ChatAgentResult boundary
- Decision: Introduce `ChatAgentContext` and `ChatAgentResult` owned by `src/agents/chat_agent`.
- Rationale: This makes the dependency direction explicit. Agents now depend only on agent-local contracts, while the workflow node is the single adapter layer that understands both schemas.
- Consequences: The orchestration node gained translation logic, but the agent package is now reusable and much easier to reason about.

## [2026-04-23] D-002: Remove encoded workflow action payloads and infer outcomes from tool execution
- Plan: v1.0
- Context: The previous implementation pushed workflow mutations through `JOBCTL_ACTION`-prefixed strings, then decoded them later into workflow state updates.
- Options considered:
  - Keep encoded action payloads and only rename modules
  - Infer agent outcomes from the executed tool call, tool arguments, and tool response
- Decision: Remove the encoded payload protocol and derive `ChatAgentResult` from LangChain tool-call output.
- Rationale: This removes an unnecessary transport layer, reduces custom parsing logic, and keeps workflow mutations out of the agent package.
- Consequences: The runner now contains light result interpretation logic tied to the tool surface, which is acceptable because it remains agent-local and typed.

## [2026-04-23] D-003: Replace next_node and pending_user_action with workflow-owned fields
- Plan: v1.0
- Context: The agent previously wrote `next_node` and `pending_user_action` directly into workflow state.
- Options considered:
  - Preserve the existing state shape with renamed fields
  - Introduce workflow-owned `workflow_action` and `interaction_state` fields
- Decision: Use `workflow_action` for routing and `interaction_state` for cross-turn follow-up.
- Rationale: These fields are owned by the workflow, not the agent. They make graph routing and pending-input behavior explicit and narrower.
- Consequences: Tests and nodes had to be updated, but state ownership is now much clearer.
