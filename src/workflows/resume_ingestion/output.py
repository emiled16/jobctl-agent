from __future__ import annotations

from src.ingestion.resumes.models import ResumeIngestionResult


def format_resume_ingestion_summary(
    status: str | None,
    result: ResumeIngestionResult,
) -> str:
    facts = result.facts
    lines = ["", f"Status: {status or 'unknown'}"]
    if facts.contact:
        emails = ", ".join(facts.contact.emails) or "none"
        lines.append(f"Emails: {emails}")
    lines.extend(
        [
            f"Experiences: {len(facts.experiences)}",
            f"Education: {len(facts.education)}",
            f"Projects: {len(facts.projects)}",
            f"Certifications: {len(facts.certifications)}",
            f"Skills: {len(facts.skills)}",
            f"Warnings: {len(result.warnings)}",
            f"Validation errors: {len(result.validation_errors)}",
        ]
    )
    return "\n".join(lines)
