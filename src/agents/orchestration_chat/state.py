from __future__ import annotations

from typing import Any, NotRequired

from langchain.agents import AgentState


class JobctlAgentState(AgentState):
    jobctl_action: NotRequired[dict[str, Any]]
