from __future__ import annotations

from typing import Literal

from src.ingestion.documents.models import DocumentArtifact, ParsedDocument
from src.ingestion.resumes.models import ResumeFacts, ResumeSection, SectionFacts

LogDetail = Literal["summary", "details"]
MAX_DETAIL_ITEMS = 12


def summarize_node_update(
    node_name: str,
    update: dict,
    *,
    detail: LogDetail = "summary",
) -> str:
    if document := update.get("document"):
        return summarize_document(node_name, document)

    if parsed_document := update.get("parsed_document"):
        return summarize_parsed_document(node_name, parsed_document)

    if sections := update.get("sections"):
        return summarize_sections(node_name, sections)

    if section_facts := update.get("section_facts"):
        return summarize_section_facts(node_name, section_facts, detail=detail)

    if facts := update.get("facts"):
        warnings = update.get("warnings", [])
        summary = f"[{node_name}] {summarize_facts(facts)} warnings={len(warnings)}"
        if detail == "details":
            return append_fact_details(summary, facts)
        return summary

    if validation_errors := update.get("validation_errors"):
        status = update.get("status", "unknown")
        return (
            f"[{node_name}] status={status} validation_errors={len(validation_errors)}"
        )

    if "validation_errors" in update:
        status = update.get("status", "unknown")
        return f"[{node_name}] status={status} validation_errors=0"

    if "status" in update or "error" in update:
        status = update.get("status", "unknown")
        error = update.get("error")
        if error:
            return f"[{node_name}] status={status} error={error}"
        return f"[{node_name}] status={status}"

    return f"[{node_name}] updated={','.join(sorted(update.keys()))}"


def summarize_document(node_name: str, document: DocumentArtifact) -> str:
    filename = document.filename or document.content_ref
    content_type = document.content_type or "unknown"
    return (
        f"[{node_name}] filename={filename} type={content_type} "
        f"size_bytes={document.size_bytes}"
    )


def summarize_parsed_document(node_name: str, document: ParsedDocument) -> str:
    return (
        f"[{node_name}] parser={document.parser} chars={len(document.text)} "
        f"pages={len(document.page_texts)}"
    )


def summarize_sections(node_name: str, sections: list[ResumeSection]) -> str:
    names = ",".join(section.name for section in sections) or "none"
    return f"[{node_name}] sections={names}"


def summarize_section_facts(
    node_name: str,
    section_facts: list[SectionFacts],
    *,
    detail: LogDetail,
) -> str:
    parts = [
        summarize_section_fact(section, detail=detail) for section in section_facts
    ]
    return f"[{node_name}] " + "; ".join(parts)


def summarize_section_fact(section: SectionFacts, *, detail: LogDetail) -> str:
    summary = f"section={section.section_name} {summarize_facts(section.facts)}"
    if detail == "details":
        return append_fact_details(summary, section.facts)
    return summary


def summarize_facts(facts: ResumeFacts) -> str:
    return (
        f"experiences={len(facts.experiences)} "
        f"education={len(facts.education)} "
        f"projects={len(facts.projects)} "
        f"certifications={len(facts.certifications)} "
        f"skills={len(facts.skills)}"
    )


def append_fact_details(summary: str, facts: ResumeFacts) -> str:
    details = summarize_fact_details(facts)
    if not details:
        return summary
    return f"{summary} ({'; '.join(details)})"


def summarize_fact_details(facts: ResumeFacts) -> list[str]:
    details: list[str] = []
    if facts.experiences:
        details.append(
            "experiences="
            + format_limited_items(
                [
                    join_present_parts(experience.organization, experience.title)
                    for experience in facts.experiences
                ]
            )
        )
    if facts.education:
        details.append(
            "education="
            + format_limited_items(
                [
                    join_present_parts(education.institution, education.credential)
                    for education in facts.education
                ]
            )
        )
    if facts.projects:
        details.append(
            "projects="
            + format_limited_items(
                [
                    project.name or project.description or "untitled project"
                    for project in facts.projects
                ]
            )
        )
    if facts.certifications:
        details.append(
            "certifications="
            + format_limited_items(
                [certification.name for certification in facts.certifications]
            )
        )
    if facts.skills:
        details.append(
            "skills=" + format_limited_items([skill.name for skill in facts.skills])
        )
    return details


def join_present_parts(*parts: str | None) -> str:
    present = [part for part in parts if part]
    return " - ".join(present) if present else "unknown"


def format_limited_items(items: list[str | None]) -> str:
    normalized = [item for item in items if item]
    shown = normalized[:MAX_DETAIL_ITEMS]
    suffix = ""
    if len(normalized) > MAX_DETAIL_ITEMS:
        suffix = f", +{len(normalized) - MAX_DETAIL_ITEMS} more"
    return "[" + ", ".join(shown) + suffix + "]"
