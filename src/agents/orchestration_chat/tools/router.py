from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.ingestion.documents.models import DocumentSource
from src.llm.base import Message, StructuredChatProvider


class ChatRoute(BaseModel):
    intent: Literal["chat", "ingest_resume", "show_resume_section"] = Field(
        description="The next action the orchestration graph should take."
    )
    section: str | None = Field(
        default=None,
        description="Resume section requested by the user, if any.",
    )
    selector: str | None = Field(
        default=None,
        description="Optional section filter, such as an organization or project name.",
    )
    source_uri: str | None = Field(
        default=None,
        description="Resume URI if the user provided one.",
    )
    source_file_ref: str | None = Field(
        default=None,
        description="Local resume file path if the user provided one.",
    )


ROUTER_SYSTEM_PROMPT = """Classify the user's message for a resume orchestration agent.

Return ingest_resume when the user asks to ingest, parse, upload, load, or process a
resume. Include source_uri or source_file_ref only if the user supplied one.

Return show_resume_section when the user asks to print, show, display, or retrieve a
specific resume section or a specific item inside a section. Use these section values:
summary, contact, experiences, education, projects, certifications, skills, languages.

Return chat for normal conversation or factual questions that can be answered by the
chat agent.
"""


def route_with_llm(
    *,
    provider: StructuredChatProvider,
    user_input: str,
) -> ChatRoute:
    messages: list[Message] = [
        {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]
    return provider.chat_structured(messages, ChatRoute, temperature=0.0)


def document_source_from_route(route: ChatRoute) -> DocumentSource | None:
    if route.source_uri:
        return DocumentSource(kind="uri", uri=route.source_uri)
    if route.source_file_ref:
        return DocumentSource(
            kind="uploaded_file",
            file_ref=route.source_file_ref,
            filename=route.source_file_ref.rsplit("/", maxsplit=1)[-1],
            content_type=None,
        )
    return None
