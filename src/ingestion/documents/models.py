from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ParsedDocument(BaseModel):
    text: str
    page_texts: list[str] = Field(default_factory=list)
    parser: str


class DocumentSource(BaseModel):
    kind: Literal["uri", "uploaded_file"]
    uri: str | None = None
    file_ref: str | None = None
    filename: str | None = None
    content_type: str | None = None


class DocumentArtifact(BaseModel):
    source: DocumentSource
    content_ref: str
    filename: str | None = None
    content_type: str | None = None
    size_bytes: int
