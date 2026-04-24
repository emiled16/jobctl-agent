from __future__ import annotations

from typing import Literal, TypedDict

from src.ingestion.documents.models import DocumentSource


class ChatAgentResult(TypedDict, total=False):
    kind: Literal["chat", "inspect_resume", "ingest_resume", "awaiting_resume_source"]
    response: str
    source: DocumentSource
