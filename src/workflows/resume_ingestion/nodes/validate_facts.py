from __future__ import annotations

from src.workflows.resume_ingestion.state import ResumeIngestionState
from src.ingestion.resumes.models import ResumeFacts
from src.ingestion.resumes.validation import validate_resume_facts


def validate_facts(state: ResumeIngestionState) -> dict:
    facts = state.get("facts") or ResumeFacts()
    validation_errors = validate_resume_facts(facts)
    status = (
        "invalid"
        if any(error.severity == "error" for error in validation_errors)
        else "valid"
    )
    return {"validation_errors": validation_errors, "status": status}
