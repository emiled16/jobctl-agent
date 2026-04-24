# Plan v1.0
[2026-04-23 21:17:52] [plan v1.0] [START] T1: Begin agent-workflow boundary refactor for chat orchestration
[2026-04-23 21:17:52] [plan v1.0] [START] T2: Introduce ChatAgentContext and remove direct OrchestrationState usage from the agent
[2026-04-23 21:17:52] [plan v1.0] [START] T3: Introduce ChatAgentResult and stop returning workflow mutations from the agent
[2026-04-23 21:17:52] [plan v1.0] [START] T4: Rename orchestration_chat to chat_agent and rename JobctlAgentState to ChatAgentState
[2026-04-23 21:17:52] [plan v1.0] [START] T5: Collapse chat agent internals around a single run_chat_agent entrypoint
[2026-04-23 21:17:52] [plan v1.0] [START] T6: Replace encoded workflow actions with typed agent tool outcomes
[2026-04-23 21:17:52] [plan v1.0] [START] T7: Reduce state-manipulation complexity inside the agent
[2026-04-23 21:17:52] [plan v1.0] [START] T8: Redesign OrchestrationState around workflow-owned data only
[2026-04-23 21:17:52] [plan v1.0] [START] T9: Move agent-to-workflow translation into the orchestration chat node
[2026-04-23 21:17:52] [plan v1.0] [START] T10: Replace next_node routing with workflow-owned routing state
[2026-04-23 21:17:52] [plan v1.0] [START] T11: Replace pending user action handling with explicit interaction_state
[2026-04-23 21:17:52] [plan v1.0] [START] T12: Align naming across app, agent, and workflow surfaces
[2026-04-23 21:17:52] [plan v1.0] [START] T13: Rewrite tests around the new agent contract and workflow behavior
[2026-04-23 21:17:52] [plan v1.0] [START] T14: Remove legacy orchestration_chat modules and helpers
[2026-04-23 21:22:56] [plan v1.0] [DONE] T1: Agent and workflow ownership split is enforced in code
[2026-04-23 21:22:56] [plan v1.0] [DONE] T2: ChatAgentContext now defines the chat agent input boundary
[2026-04-23 21:22:56] [plan v1.0] [DONE] T3: ChatAgentResult now defines the chat agent output boundary
[2026-04-23 21:22:56] [plan v1.0] [DONE] T4: Added src/agents/chat_agent and replaced JobctlAgentState with ChatAgentState
[2026-04-23 21:22:56] [plan v1.0] [DONE] T5: run_chat_agent is now the public chat agent entrypoint
[2026-04-23 21:22:56] [plan v1.0] [DONE] T6: Removed encoded action transport and infer outcomes from tool calls plus tool responses
[2026-04-23 21:22:56] [plan v1.0] [DONE] T7: Replaced broad state-update helpers with focused result assembly and workflow translation
[2026-04-23 21:22:56] [plan v1.0] [DONE] T8: OrchestrationState now carries workflow_action and interaction_state instead of agent-owned control fields
[2026-04-23 21:22:56] [plan v1.0] [DONE] T9: The orchestration chat node now adapts OrchestrationState to ChatAgentContext and ChatAgentResult back to workflow state
[2026-04-23 21:22:56] [plan v1.0] [DONE] T10: Graph routing now derives from workflow_action instead of next_node
[2026-04-23 21:22:56] [plan v1.0] [DONE] T11: Pending source follow-up now uses interaction_state=awaiting_resume_source
[2026-04-23 21:22:56] [plan v1.0] [DONE] T12: App text and module imports now use chat agent terminology
[2026-04-23 21:22:56] [plan v1.0] [DONE] T13: Added agent-focused tests and updated orchestration tests for the new contracts
[2026-04-23 21:22:56] [plan v1.0] [DONE] T14: Removed legacy tracked orchestration_chat modules
