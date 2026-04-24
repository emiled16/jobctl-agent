from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from src.agents.chat_agent import ChatAgentContext, run_chat_agent
from src.agents.chat_agent.result import ChatAgentResult
from src.workflows.orchestration.state import OrchestrationState


def make_chat_agent_node(chat_model: BaseChatModel | None = None):
    def chat_agent(state: OrchestrationState) -> dict:
        context: ChatAgentContext = {
            "messages": state.get("messages", []),
            "user_input": state.get("user_input", ""),
            "resume_facts": state.get("resume_facts"),
            "awaiting_resume_source": (
                state.get("interaction_state") == "awaiting_resume_source"
            ),
        }
        result = run_chat_agent(context, model=chat_model)
        return workflow_update_from_chat_result(
            state,
            result,
            user_input=context["user_input"],
        )

    return chat_agent


def workflow_update_from_chat_result(
    state: OrchestrationState,
    result: ChatAgentResult,
    *,
    user_input: str,
) -> dict:
    response = result.get("response", "")
    transcript = [
        *state.get("messages", []),
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": response},
    ]
    kind = result.get("kind", "chat")
    base_update = {
        "messages": transcript,
        "response": response,
        "workflow_action": "none",
    }
    if kind == "ingest_resume":
        return {
            **base_update,
            "intent": "ingest_resume",
            "source": result.get("source"),
            "interaction_state": None,
            "status": "ingesting",
            "workflow_action": "resume_ingestion",
        }
    if kind == "awaiting_resume_source":
        return {
            **base_update,
            "intent": "ingest_resume",
            "interaction_state": "awaiting_resume_source",
            "status": "needs_source",
        }
    if kind == "inspect_resume":
        return {
            **base_update,
            "intent": "inspect_resume",
            "interaction_state": state.get("interaction_state"),
            "status": state.get("status", "idle"),
        }
    return {
        **base_update,
        "intent": "chat",
        "interaction_state": state.get("interaction_state"),
        "status": "ready" if state.get("resume_facts") else "idle",
    }
