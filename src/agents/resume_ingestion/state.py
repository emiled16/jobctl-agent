from typing import TypedDict


class ResumeIngestionState(TypedDict):
    resume_uri: str
    raw_document_bytes_ref: str | None
    raw_text: str | None
    parsed_sections: list[dict]
    extraction_candidates: list[dict]
    normalized_experiences: list[dict]
    ambiguities: list[dict]
    clarification_questions: list[dict]
    user_edits: list[dict]
    refined_experiences: list[dict]
    validation_errors: list[dict]
    provenance_map: dict
    ingestion_confidence: float
