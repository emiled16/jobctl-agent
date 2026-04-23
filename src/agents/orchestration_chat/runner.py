from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from src.agents.orchestration_chat.langchain_runner import (
    run_langchain_orchestration_chat_agent,
)
from src.workflows.orchestration.state import OrchestrationState


def run_orchestration_chat_agent(
    state: OrchestrationState,
    *,
    chat_model: BaseChatModel | None = None,
) -> dict:
    return run_langchain_orchestration_chat_agent(state, model=chat_model)
