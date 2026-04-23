from __future__ import annotations

from src.ingestion.resumes.models import ResumeFacts, SectionFacts


def merge_facts(target: ResumeFacts, section: SectionFacts) -> None:
    source = section.facts
    if source.person is not None:
        target.person = source.person
    if source.contact is not None:
        target.contact = source.contact
    if source.summary:
        target.summary = source.summary
    target.experiences.extend(source.experiences)
    target.education.extend(source.education)
    target.projects.extend(source.projects)
    target.certifications.extend(source.certifications)
    target.skills.extend(source.skills)
    target.languages.extend(source.languages)
