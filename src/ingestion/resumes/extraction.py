from __future__ import annotations

from src.ingestion.resumes.models import (
    ContactFacts,
    FactProvenance,
    PersonFacts,
    ProjectFacts,
    ResumeFacts,
    ResumeSection,
    SectionFacts,
    SkillFacts,
)
from src.ingestion.resumes.text_utils import (
    extract_block_items,
    extract_emails,
    extract_items,
    extract_links,
    extract_phone_numbers,
    first_nonempty_line,
    normalize_space,
    split_skill_text,
)


def extract_section_facts_heuristic(
    section: ResumeSection, *, source_ref: str
) -> SectionFacts:
    provenance = FactProvenance(
        source_ref=source_ref,
        section=section.name,
        text_span=(section.start_char or 0, section.end_char or len(section.text)),
        raw_text=section.text,
        confidence=0.45,
    )
    facts = ResumeFacts()

    match section.name:
        case "contact":
            facts.contact = ContactFacts(
                emails=extract_emails(section.text),
                phone_numbers=extract_phone_numbers(section.text),
                links=extract_links(section.text),
                provenance=provenance,
            )
            first_line = first_nonempty_line(section.text)
            if first_line and "@" not in first_line and len(first_line.split()) <= 5:
                facts.person = PersonFacts(full_name=first_line, provenance=provenance)
        case "skills":
            facts.skills = [
                SkillFacts(name=skill, provenance=provenance)
                for skill in split_skill_text(section.text)
            ]
        case "experience":
            facts.experiences = extract_block_items(section.text, provenance)
        case "projects":
            facts.projects = [
                ProjectFacts(
                    name=item.title, bullets=item.bullets, provenance=provenance
                )
                for item in extract_items(section.text)
            ]
        case "summary":
            facts.summary = normalize_space(section.text)
        case _:
            pass
    return SectionFacts(section_name=section.name, facts=facts)
