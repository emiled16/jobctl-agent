from __future__ import annotations

from typing import Literal, TypedDict

from src.ingestion.documents.models import DocumentSource
from src.ingestion.resumes.models import ResumeFacts
from src.llm.base import Message
from src.workflows.resume_ingestion.state import ResumeIngestionState


class OrchestrationState(TypedDict, total=False):
    messages: list[Message]
    user_input: str
    intent: Literal["chat", "ingest_resume", "show_resume_section"]
    next_node: Literal["resume_ingestion", "end"]
    source: DocumentSource | None
    resume_ingestion_state: ResumeIngestionState | None
    resume_facts: ResumeFacts | None
    pending_user_action: Literal["choose_resume_section"] | None
    requested_section: str | None
    requested_selector: str | None
    response: str
    status: Literal["idle", "needs_source", "ingesting", "ready", "failed"]
    error: str | None
