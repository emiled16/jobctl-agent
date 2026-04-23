from __future__ import annotations

from src.agents.orchestration_chat.runner import run_orchestration_chat_agent
from src.llm.base import LLMProvider
from src.workflows.orchestration.state import OrchestrationState


def make_chat_agent_node(llm_provider: LLMProvider | None = None):
    def chat_agent(state: OrchestrationState) -> dict:
        return run_orchestration_chat_agent(state, llm_provider=llm_provider)

    return chat_agent
