from __future__ import annotations

from typing import Literal, TypedDict

from src.ingestion.documents.models import DocumentSource
from src.ingestion.resumes.models import ResumeFacts
from src.llm.messages import Message
from src.workflows.resume_ingestion.state import ResumeIngestionState


class OrchestrationState(TypedDict, total=False):
    messages: list[Message]
    user_input: str
    intent: Literal["chat", "ingest_resume", "inspect_resume"]
    workflow_action: Literal["resume_ingestion", "none"]
    interaction_state: Literal["awaiting_resume_source"] | None
    source: DocumentSource | None
    resume_ingestion_state: ResumeIngestionState | None
    resume_facts: ResumeFacts | None
    response: str
    status: Literal["idle", "needs_source", "ingesting", "ready", "failed"]
    error: str | None
