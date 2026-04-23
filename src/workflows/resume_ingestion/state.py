from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict

from src.ingestion.documents.models import (
    DocumentArtifact,
    DocumentSource,
    ParsedDocument,
)
from src.ingestion.resumes.models import (
    ExtractionWarning,
    ResumeFacts,
    ResumeSection,
    SectionFacts,
)


class ResumeIngestionState(TypedDict, total=False):
    source: DocumentSource
    document: DocumentArtifact | None
    parsed_document: ParsedDocument | None
    sections: list[ResumeSection]
    section_facts: Annotated[list[SectionFacts], operator.add]
    facts: ResumeFacts | None
    warnings: Annotated[list[ExtractionWarning], operator.add]
    validation_errors: Annotated[list[ExtractionWarning], operator.add]
    status: Literal[
        "needs_source",
        "retrieving",
        "parsing",
        "extracting",
        "valid",
        "invalid",
        "failed",
    ]
    error: str | None


class SectionExtractionState(TypedDict):
    source_ref: str
    section: ResumeSection
