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
    """List the ingested sections and item counts."""

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
    """List the items currently stored for a specific section."""

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
    """Show the detail for a 1-based section item, optionally scoped to a bullet."""

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
    if not facts.contact:
        return []
    lines: list[str] = []
    if facts.person and facts.person.full_name:
        lines.append(f"Name: {facts.person.full_name}")
    lines.extend(f"Email: {email}" for email in facts.contact.emails)
    lines.extend(f"Phone: {phone}" for phone in facts.contact.phone_numbers)
    lines.extend(f"Link: {link}" for link in facts.contact.links)
    if facts.contact.location:
        lines.append(f"Location: {facts.contact.location}")
    return lines


def _list_experiences(experiences: list[ExperienceFacts]) -> str:
    if not experiences:
        return "Professional Experiences\nNo professional experiences are available."
    return "Professional Experiences\n" + "\n".join(
        f"{index}. {_experience_heading(item)} ({len(item.bullets)} bullets)"
        for index, item in enumerate(experiences, start=1)
    )


def _list_projects(projects: list[ProjectFacts]) -> str:
    if not projects:
        return "Projects\nNo projects are available."
    return "Projects\n" + "\n".join(
        f"{index}. {_project_heading(item)} ({len(item.bullets)} bullets)"
        for index, item in enumerate(projects, start=1)
    )


def _experience_heading(item: ExperienceFacts) -> str:
    parts = [item.organization, item.title]
    heading = " | ".join(part for part in parts if part)
    return heading or "Untitled experience"


def _project_heading(item: ProjectFacts) -> str:
    return item.name or "Untitled project"


def _education_heading(item) -> str:
    parts = [item.institution, item.credential, item.field_of_study]
    heading = " | ".join(part for part in parts if part)
    return heading or "Untitled education entry"


def _certification_heading(item) -> str:
    parts = [item.name, item.issuer]
    heading = " | ".join(part for part in parts if part)
    return heading or "Untitled certification"


def _language_heading(item) -> str:
    if item.proficiency:
        return f"{item.name} ({item.proficiency})"
    return item.name


def _experience_detail(
    item: ExperienceFacts,
    item_index: int | None,
    bullet_index: int | None,
) -> str:
    if bullet_index is not None:
        bullet = _select_index(item.bullets, bullet_index)
        if bullet is None:
            return _invalid_bullet_index_message("experience", bullet_index, len(item.bullets))
        heading = _experience_heading(item)
        return f"Professional experience {item_index}: {heading}\nBullet {bullet_index}: {bullet}"

    lines = [f"Professional experience {item_index}: {_experience_heading(item)}"]
    if item.start_date or item.end_date:
        lines.append(
            f"Dates: {item.start_date or '?'} to {item.end_date or 'present'}"
        )
    if item.location:
        lines.append(f"Location: {item.location}")
    if item.description:
        lines.append(f"Description: {item.description}")
    if item.bullets:
        lines.extend(
            f"Bullet {index}. {bullet}"
            for index, bullet in enumerate(item.bullets, start=1)
        )
    if item.technologies:
        lines.append(f"Technologies: {', '.join(item.technologies)}")
    return "\n".join(lines)


def _project_detail(
    item: ProjectFacts,
    item_index: int | None,
    bullet_index: int | None,
) -> str:
    if bullet_index is not None:
        bullet = _select_index(item.bullets, bullet_index)
        if bullet is None:
            return _invalid_bullet_index_message("project", bullet_index, len(item.bullets))
        heading = _project_heading(item)
        return f"Project {item_index}: {heading}\nBullet {bullet_index}: {bullet}"

    lines = [f"Project {item_index}: {_project_heading(item)}"]
    if item.role:
        lines.append(f"Role: {item.role}")
    if item.description:
        lines.append(f"Description: {item.description}")
    if item.bullets:
        lines.extend(
            f"Bullet {index}. {bullet}"
            for index, bullet in enumerate(item.bullets, start=1)
        )
    if item.technologies:
        lines.append(f"Technologies: {', '.join(item.technologies)}")
    if item.links:
        lines.append(f"Links: {', '.join(item.links)}")
    return "\n".join(lines)


def _education_detail(item, item_index: int | None) -> str:
    lines = [f"Education {item_index}: {_education_heading(item)}"]
    if item.start_date or item.end_date:
        lines.append(
            f"Dates: {item.start_date or '?'} to {item.end_date or 'present'}"
        )
    if item.location:
        lines.append(f"Location: {item.location}")
    return "\n".join(lines)


def _certification_detail(item, item_index: int | None) -> str:
    lines = [f"Certification {item_index}: {_certification_heading(item)}"]
    if item.issued_date:
        lines.append(f"Issued: {item.issued_date}")
    if item.expiration_date:
        lines.append(f"Expires: {item.expiration_date}")
    return "\n".join(lines)


def _select_index[T](items: list[T], item_index: int | None) -> T | None:
    if item_index is None or item_index < 1 or item_index > len(items):
        return None
    return items[item_index - 1]


def _invalid_item_index_message(
    section_label: str,
    item_index: int | None,
    item_count: int,
) -> str:
    return (
        f"Item {item_index} is not available in {section_label}. "
        f"There are {item_count} items."
    )


def _invalid_bullet_index_message(
    item_label: str,
    bullet_index: int,
    bullet_count: int,
) -> str:
    return (
        f"Bullet {bullet_index} is not available in that {item_label}. "
        f"There are {bullet_count} bullets."
    )


def _unknown_section_message() -> str:
    valid_sections = ", ".join(SECTION_LABELS[section] for section in SECTION_ORDER)
    return f"Unknown resume section. Valid sections: {valid_sections}."
