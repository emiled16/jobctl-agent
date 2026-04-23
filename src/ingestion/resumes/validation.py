from __future__ import annotations

from src.ingestion.resumes.models import ExtractionWarning, ResumeFacts


def validate_resume_facts(facts: ResumeFacts) -> list[ExtractionWarning]:
    errors: list[ExtractionWarning] = []
    if not any(
        [
            facts.experiences,
            facts.education,
            facts.projects,
            facts.skills,
            facts.certifications,
        ]
    ):
        errors.append(
            ExtractionWarning(
                code="no_resume_facts",
                message="No experience, education, project, skill, or certification facts were extracted.",
                severity="error",
            )
        )
    if facts.contact is None or not (facts.contact.emails or facts.contact.links):
        errors.append(
            ExtractionWarning(
                code="missing_contact_anchor",
                message="No email or profile link was extracted from the resume.",
                severity="warning",
                related_field="contact",
            )
        )
    return errors
