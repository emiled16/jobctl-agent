from __future__ import annotations

import re

from src.ingestion.resumes.models import ResumeSection

SECTION_ALIASES: dict[str, set[str]] = {
    "summary": {"summary", "profile", "professional summary", "about"},
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "career history",
    },
    "projects": {"projects", "selected projects", "project experience"},
    "education": {"education", "academic background"},
    "skills": {"skills", "technical skills", "technologies", "core skills"},
    "certifications": {"certifications", "certificates", "licenses"},
    "languages": {"languages"},
    "contact": {"contact", "contact information"},
}

HEADING_PATTERN = re.compile(r"^\s*([A-Z][A-Z /\-&]{2,}|[A-Z][A-Za-z /\-&]{2,})\s*$")


def segment_resume(text: str) -> list[ResumeSection]:
    lines = text.splitlines()
    headings: list[tuple[int, str, str]] = []
    offset = 0
    for line in lines:
        heading = canonical_heading(line)
        if heading:
            headings.append((offset, heading, line.strip()))
        offset += len(line) + 1

    if not headings:
        return [
            ResumeSection(
                name="full_resume",
                text=text,
                start_char=0,
                end_char=len(text),
            )
        ]

    sections: list[ResumeSection] = []
    for index, (start, name, raw_heading) in enumerate(headings):
        next_start = headings[index + 1][0] if index + 1 < len(headings) else len(text)
        heading_end = start + len(raw_heading)
        section_text = text[heading_end:next_start].strip()
        if section_text:
            sections.append(
                ResumeSection(
                    name=name,
                    heading=raw_heading,
                    text=section_text,
                    start_char=start,
                    end_char=next_start,
                )
            )

    preamble = text[: headings[0][0]].strip()
    if preamble:
        sections.insert(
            0,
            ResumeSection(
                name="contact",
                heading=None,
                text=preamble,
                start_char=0,
                end_char=headings[0][0],
            ),
        )
    return sections or [
        ResumeSection(name="full_resume", text=text, start_char=0, end_char=len(text))
    ]


def canonical_heading(line: str) -> str | None:
    candidate = line.strip()
    if len(candidate) > 48:
        return None
    if not HEADING_PATTERN.match(candidate):
        return None
    normalized = re.sub(r"\s+", " ", candidate.lower())
    for canonical, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return canonical
    return None
