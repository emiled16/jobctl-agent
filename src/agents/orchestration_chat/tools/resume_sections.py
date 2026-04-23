from __future__ import annotations

from collections.abc import Iterable

from pydantic import BaseModel

from src.ingestion.resumes.models import (
    CertificationFacts,
    EducationFacts,
    ExperienceFacts,
    ProjectFacts,
    ResumeFacts,
)

SECTION_CHOICES = [
    ("summary", "Summary"),
    ("contact", "Contact"),
    ("experiences", "Experience"),
    ("education", "Education"),
    ("projects", "Projects"),
    ("certifications", "Certifications"),
    ("skills", "Skills"),
    ("languages", "Languages"),
]

SECTION_ALIASES = {
    "summary": "summary",
    "contact": "contact",
    "email": "contact",
    "emails": "contact",
    "phone": "contact",
    "experience": "experiences",
    "experiences": "experiences",
    "work": "experiences",
    "job": "experiences",
    "jobs": "experiences",
    "education": "education",
    "school": "education",
    "projects": "projects",
    "project": "projects",
    "certifications": "certifications",
    "certification": "certifications",
    "skills": "skills",
    "skill": "skills",
    "languages": "languages",
    "language": "languages",
}


def format_section_choices() -> str:
    lines = ["Which resume section would you like?"]
    lines.extend(
        f"{index}. {label}" for index, (_, label) in enumerate(SECTION_CHOICES, start=1)
    )
    return "\n".join(lines)


def resolve_section_choice(value: str) -> str | None:
    normalized = value.strip().lower()
    if normalized.isdigit():
        index = int(normalized) - 1
        if 0 <= index < len(SECTION_CHOICES):
            return SECTION_CHOICES[index][0]
    return SECTION_ALIASES.get(normalized)


def infer_section(text: str) -> tuple[str | None, str | None]:
    normalized = text.strip().lower()
    for alias, section in SECTION_ALIASES.items():
        if alias in normalized:
            selector = _extract_selector(normalized, alias)
            return section, selector
    return None, None


def render_resume_section(
    facts: ResumeFacts | None,
    section: str | None,
    selector: str | None = None,
) -> str:
    if facts is None:
        return "No resume has been ingested yet. Use /ingest with a file path or URI first."
    if not section:
        return format_section_choices()

    if section == "summary":
        return facts.summary or "No summary was extracted."
    if section == "contact":
        return _render_contact(facts)
    if section == "experiences":
        return _render_experiences(facts.experiences, selector)
    if section == "education":
        return _render_models(facts.education, "Education")
    if section == "projects":
        return _render_projects(facts.projects, selector)
    if section == "certifications":
        return _render_certifications(facts.certifications)
    if section == "skills":
        return _render_name_list("Skills", [skill.name for skill in facts.skills])
    if section == "languages":
        return _render_name_list(
            "Languages",
            [
                f"{language.name} ({language.proficiency})"
                if language.proficiency
                else language.name
                for language in facts.languages
            ],
        )
    return format_section_choices()


def answer_from_resume_facts(facts: ResumeFacts | None, question: str) -> str | None:
    if facts is None:
        return None
    normalized = question.lower()
    if "name" in normalized and facts.person and facts.person.full_name:
        return facts.person.full_name
    if "email" in normalized and facts.contact and facts.contact.emails:
        return ", ".join(facts.contact.emails)
    if "phone" in normalized and facts.contact and facts.contact.phone_numbers:
        return ", ".join(facts.contact.phone_numbers)
    if "location" in normalized and facts.contact and facts.contact.location:
        return facts.contact.location
    return None


def _extract_selector(text: str, alias: str) -> str | None:
    for marker in ("show ", "print ", "display "):
        if text.startswith(marker) and text.endswith(f" {alias}"):
            candidate = text.removeprefix(marker).removesuffix(f" {alias}").strip()
            return candidate or None
    return None


def _render_contact(facts: ResumeFacts) -> str:
    if not facts.contact:
        return "No contact details were extracted."
    lines = ["Contact"]
    if facts.person and facts.person.full_name:
        lines.append(f"Name: {facts.person.full_name}")
    if facts.contact.emails:
        lines.append(f"Emails: {', '.join(facts.contact.emails)}")
    if facts.contact.phone_numbers:
        lines.append(f"Phone: {', '.join(facts.contact.phone_numbers)}")
    if facts.contact.links:
        lines.append(f"Links: {', '.join(facts.contact.links)}")
    if facts.contact.location:
        lines.append(f"Location: {facts.contact.location}")
    return "\n".join(lines)


def _render_experiences(
    experiences: list[ExperienceFacts],
    selector: str | None,
) -> str:
    selected = _filter_models(experiences, selector)
    if not selected:
        return "No matching experience was extracted."
    lines = ["Experience"]
    for experience in selected:
        heading = " - ".join(
            value
            for value in [experience.organization, experience.title]
            if value is not None
        )
        lines.append(heading or "Untitled experience")
        if experience.start_date or experience.end_date:
            start_date = experience.start_date or "?"
            end_date = experience.end_date or "present"
            lines.append(f"Dates: {start_date} to {end_date}")
        if experience.location:
            lines.append(f"Location: {experience.location}")
        if experience.description:
            lines.append(experience.description)
        lines.extend(f"- {bullet}" for bullet in experience.bullets)
        if experience.technologies:
            lines.append(f"Technologies: {', '.join(experience.technologies)}")
    return "\n".join(lines)


def _render_projects(projects: list[ProjectFacts], selector: str | None) -> str:
    selected = _filter_models(projects, selector)
    if not selected:
        return "No matching project was extracted."
    lines = ["Projects"]
    for project in selected:
        lines.append(project.name or "Untitled project")
        if project.role:
            lines.append(f"Role: {project.role}")
        if project.description:
            lines.append(project.description)
        lines.extend(f"- {bullet}" for bullet in project.bullets)
        if project.technologies:
            lines.append(f"Technologies: {', '.join(project.technologies)}")
        if project.links:
            lines.append(f"Links: {', '.join(project.links)}")
    return "\n".join(lines)


def _render_certifications(certifications: list[CertificationFacts]) -> str:
    if not certifications:
        return "No certifications were extracted."
    lines = ["Certifications"]
    for certification in certifications:
        parts = [certification.name]
        if certification.issuer:
            parts.append(f"issuer: {certification.issuer}")
        if certification.issued_date:
            parts.append(f"issued: {certification.issued_date}")
        lines.append(" | ".join(part for part in parts if part))
    return "\n".join(lines)


def _render_models(models: list[EducationFacts], title: str) -> str:
    if not models:
        return f"No {title.lower()} entries were extracted."
    lines = [title]
    for model in models:
        lines.append(_model_line(model))
    return "\n".join(lines)


def _render_name_list(title: str, values: list[str]) -> str:
    if not values:
        return f"No {title.lower()} were extracted."
    return f"{title}: {', '.join(values)}"


def _filter_models[T: BaseModel](models: list[T], selector: str | None) -> list[T]:
    if not selector:
        return models
    normalized = selector.lower()
    return [model for model in models if normalized in _model_line(model).lower()]


def _model_line(model: BaseModel) -> str:
    values: Iterable[object] = model.model_dump(exclude={"provenance"}).values()
    return " | ".join(str(value) for value in values if value)
