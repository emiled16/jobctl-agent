# Checklist for Plan v1.0

## Milestone M1: Define Clear Agent and Workflow Boundaries
- [x] T1: Define the target package contracts for agents and workflows
- [x] T2: Replace workflow-owned agent inputs with a dedicated `ChatAgentContext`
- [x] T3: Replace workflow mutations with a dedicated `ChatAgentResult`

## Milestone M2: Refactor the Chat Agent Into an Agent-Local Module
- [x] T4: Rename `orchestration_chat` to `chat_agent` and replace `JobctlAgentState` with `ChatAgentState`
- [x] T5: Collapse agent internals around a single public `run_chat_agent` entrypoint
- [x] T6: Replace encoded workflow actions with typed agent tool outcomes
- [x] T7: Reduce state-manipulation complexity inside the agent

## Milestone M3: Simplify Orchestration Workflow State and Node Responsibilities
- [x] T8: Redesign `OrchestrationState` around workflow-owned data only
- [x] T9: Move agent-to-workflow translation into the chat workflow node
- [x] T10: Replace `next_node` string routing with explicit routing derived from workflow state
- [x] T11: Simplify pending-ingestion flow into an explicit workflow interaction state

## Milestone M4: Align Application Surface and Tests With the New Architecture
- [x] T12: Rename orchestration workflow surface to match the new mental model
- [x] T13: Rewrite orchestration tests around agent contract and workflow behavior
- [x] T14: Remove legacy modules and dead helpers after migration
