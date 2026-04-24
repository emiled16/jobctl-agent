from __future__ import annotations

from typing import TypedDict

from src.ingestion.resumes.models import ResumeFacts
from src.llm.messages import Message


class ChatAgentContext(TypedDict, total=False):
    messages: list[Message]
    user_input: str
    resume_facts: ResumeFacts | None
    awaiting_resume_source: bool
