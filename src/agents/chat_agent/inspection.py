from __future__ import annotations

from src.ingestion.resumes.models import ExperienceFacts, ProjectFacts, ResumeFacts

NO_RESUME_MESSAGE = (
    "No resume is currently ingested. Ask me to ingest one and then provide the "
    "resume URI or local file path."
)

SECTION_LABELS = {
    "summary": "Summary",
    "contact": "Contact",
    "experiences": "Professional Experiences",
    "education": "Education",
    "projects": "Projects",
    "certifications": "Certifications",
    "skills": "Skills",
    "languages": "Languages",
}

SECTION_ORDER = [
    "summary",
    "contact",
    "experiences",
    "education",
    "projects",
    "certifications",
    "skills",
    "languages",
]

SECTION_ALIASES = {
    "summary": "summary",
    "contact": "contact",
    "contacts": "contact",
    "professional experience": "experiences",
    "professional experiences": "experiences",
    "experience": "experiences",
    "experiences": "experiences",
    "work experience": "experiences",
    "work experiences": "experiences",
    "education": "education",
    "project": "projects",
    "projects": "projects",
    "certification": "certifications",
    "certifications": "certifications",
    "skill": "skills",
    "skills": "skills",
    "language": "languages",
    "languages": "languages",
}


def list_resume_sections(facts: ResumeFacts | None) -> str:
    if facts is None:
        return NO_RESUME_MESSAGE

    lines = ["Ingested resume sections:"]
    for index, section in enumerate(SECTION_ORDER, start=1):
        label = SECTION_LABELS[section]
        count = _section_item_count(facts, section)
        item_label = "item" if count == 1 else "items"
        lines.append(f"{index}. {label}: {count} {item_label}")
    return "\n".join(lines)


def list_section_points(facts: ResumeFacts | None, section: str | None) -> str:
    if facts is None:
        return NO_RESUME_MESSAGE

    normalized = normalize_section_name(section)
    if normalized is None:
        return _unknown_section_message()

    if normalized == "summary":
        return (
            f"Summary\n1. {facts.summary}"
            if facts.summary
            else "Summary\nNo summary is available."
        )
    if normalized == "contact":
        contact_lines = _contact_lines(facts)
        if not contact_lines:
            return "Contact\nNo contact details are available."
        return "Contact\n" + "\n".join(
            f"{index}. {line}" for index, line in enumerate(contact_lines, start=1)
        )
    if normalized == "experiences":
        return _list_experiences(facts.experiences)
    if normalized == "education":
        if not facts.education:
            return "Education\nNo education entries are available."
        return "Education\n" + "\n".join(
            f"{index}. {_education_heading(item)}"
            for index, item in enumerate(facts.education, start=1)
        )
    if normalized == "projects":
        return _list_projects(facts.projects)
    if normalized == "certifications":
        if not facts.certifications:
            return "Certifications\nNo certifications are available."
        return "Certifications\n" + "\n".join(
            f"{index}. {_certification_heading(item)}"
            for index, item in enumerate(facts.certifications, start=1)
        )
    if normalized == "skills":
        if not facts.skills:
            return "Skills\nNo skills are available."
        return "Skills\n" + "\n".join(
            f"{index}. {skill.name}" for index, skill in enumerate(facts.skills, start=1)
        )
    if normalized == "languages":
        if not facts.languages:
            return "Languages\nNo languages are available."
        return "Languages\n" + "\n".join(
            f"{index}. {_language_heading(item)}"
            for index, item in enumerate(facts.languages, start=1)
        )
    return _unknown_section_message()


def show_section_item_detail(
    facts: ResumeFacts | None,
    section: str | None,
    item_index: int | None,
    bullet_index: int | None = None,
) -> str:
    if facts is None:
        return NO_RESUME_MESSAGE

    normalized = normalize_section_name(section)
    if normalized is None:
        return _unknown_section_message()

    if normalized == "summary":
        return facts.summary or "No summary is available."
    if normalized == "contact":
        contact_lines = _contact_lines(facts)
        if not contact_lines:
            return "No contact details are available."
        if item_index is None:
            return "Contact\n" + "\n".join(contact_lines)
        line = _select_index(contact_lines, item_index)
        if line is None:
            return _invalid_item_index_message("contact", item_index, len(contact_lines))
        return line
    if normalized == "experiences":
        item = _select_index(facts.experiences, item_index)
        if item is None:
            return _invalid_item_index_message(
                "professional experiences",
                item_index,
                len(facts.experiences),
            )
        return _experience_detail(item, item_index, bullet_index)
    if normalized == "education":
        item = _select_index(facts.education, item_index)
        if item is None:
            return _invalid_item_index_message("education", item_index, len(facts.education))
        return _education_detail(item, item_index)
    if normalized == "projects":
        item = _select_index(facts.projects, item_index)
        if item is None:
            return _invalid_item_index_message("projects", item_index, len(facts.projects))
        return _project_detail(item, item_index, bullet_index)
    if normalized == "certifications":
        item = _select_index(facts.certifications, item_index)
        if item is None:
            return _invalid_item_index_message(
                "certifications",
                item_index,
                len(facts.certifications),
            )
        return _certification_detail(item, item_index)
    if normalized == "skills":
        item = _select_index(facts.skills, item_index)
        if item is None:
            return _invalid_item_index_message("skills", item_index, len(facts.skills))
        return item.name
    if normalized == "languages":
        item = _select_index(facts.languages, item_index)
        if item is None:
            return _invalid_item_index_message("languages", item_index, len(facts.languages))
        return _language_heading(item)
    return _unknown_section_message()


def normalize_section_name(section: str | None) -> str | None:
    if not section:
        return None
    return SECTION_ALIASES.get(section.strip().lower())


def _section_item_count(facts: ResumeFacts, section: str) -> int:
    if section == "summary":
        return 1 if facts.summary else 0
    if section == "contact":
        return len(_contact_lines(facts))
    if section == "experiences":
        return len(facts.experiences)
    if section == "education":
        return len(facts.education)
    if section == "projects":
        return len(facts.projects)
    if section == "certifications":
        return len(facts.certifications)
    if section == "skills":
        return len(facts.skills)
    if section == "languages":
        return len(facts.languages)
    return 0


def _contact_lines(facts: ResumeFacts) -> list[str]:
    lines: list[str] = []
    person = facts.person
    if person and person.full_name:
        lines.append(person.full_name)
    contact = facts.contact
    if contact is None:
        return lines
    lines.extend(contact.emails)
    lines.extend(contact.phone_numbers)
    if contact.location:
        lines.append(contact.location)
    lines.extend(contact.links)
    return lines


def _list_experiences(items: list[ExperienceFacts]) -> str:
    if not items:
        return "Professional Experiences\nNo professional experiences are available."
    return "Professional Experiences\n" + "\n".join(
        f"{index}. {_experience_heading(item)}"
        for index, item in enumerate(items, start=1)
    )


def _list_projects(items: list[ProjectFacts]) -> str:
    if not items:
        return "Projects\nNo projects are available."
    return "Projects\n" + "\n".join(
        f"{index}. {_project_heading(item)}"
        for index, item in enumerate(items, start=1)
    )


def _experience_detail(
    item: ExperienceFacts,
    item_index: int | None,
    bullet_index: int | None,
) -> str:
    heading = f"Professional experience {item_index}: {_experience_heading(item)}"
    if bullet_index is not None:
        bullet = _select_index(item.bullets, bullet_index)
        if bullet is None:
            return _invalid_item_index_message(
                "experience bullets",
                bullet_index,
                len(item.bullets),
            )
        return f"{heading}\nBullet {bullet_index}: {bullet}"
    lines = [heading]
    lines.extend(f"Bullet {index}: {bullet}" for index, bullet in enumerate(item.bullets, start=1))
    return "\n".join(lines)


def _project_detail(
    item: ProjectFacts,
    item_index: int | None,
    bullet_index: int | None,
) -> str:
    heading = f"Project {item_index}: {_project_heading(item)}"
    if bullet_index is not None:
        bullet = _select_index(item.bullets, bullet_index)
        if bullet is None:
            return _invalid_item_index_message(
                "project bullets",
                bullet_index,
                len(item.bullets),
            )
        return f"{heading}\nBullet {bullet_index}: {bullet}"
    lines = [heading]
    lines.extend(f"Bullet {index}: {bullet}" for index, bullet in enumerate(item.bullets, start=1))
    return "\n".join(lines)


def _education_detail(item, item_index: int | None) -> str:
    return f"Education {item_index}: {_education_heading(item)}"


def _certification_detail(item, item_index: int | None) -> str:
    return f"Certification {item_index}: {_certification_heading(item)}"


def _experience_heading(item: ExperienceFacts) -> str:
    return " | ".join(part for part in [item.organization, item.title] if part)


def _project_heading(item: ProjectFacts) -> str:
    return item.name or "Untitled project"


def _education_heading(item) -> str:
    return " | ".join(part for part in [item.institution, item.credential] if part)


def _certification_heading(item) -> str:
    return " | ".join(part for part in [item.name, item.issuer] if part)


def _language_heading(item) -> str:
    return " | ".join(part for part in [item.name, item.proficiency] if part)


def _select_index(items: list, index: int | None):
    if index is None or index < 1 or index > len(items):
        return None
    return items[index - 1]


def _invalid_item_index_message(label: str, index: int | None, count: int) -> str:
    return (
        f"I could not find {label} item {index}. "
        f"There {'is' if count == 1 else 'are'} {count} available."
    )


def _unknown_section_message() -> str:
    return "I could not determine which resume section to inspect."
