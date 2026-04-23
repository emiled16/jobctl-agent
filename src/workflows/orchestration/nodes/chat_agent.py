from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from src.agents.orchestration_chat.runner import run_orchestration_chat_agent
from src.workflows.orchestration.state import OrchestrationState


def make_chat_agent_node(chat_model: BaseChatModel | None = None):
    def chat_agent(state: OrchestrationState) -> dict:
        return run_orchestration_chat_agent(state, chat_model=chat_model)

    return chat_agent
