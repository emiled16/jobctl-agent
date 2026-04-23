from __future__ import annotations

from src.ingestion.resumes.models import ResumeSection
from src.llm.base import Message

SECTION_EXTRACTION_SYSTEM_PROMPT = (
    "Extract only facts explicitly supported by the resume section. "
    "Do not infer graph entities, merge duplicates, ask questions, or "
    "rewrite the candidate's history. Preserve raw wording where useful. "
    "Do not include provenance; the workflow adds provenance after extraction."
)


def build_extract_section_messages(
    section: ResumeSection,
    *,
    source_ref: str,
) -> list[Message]:
    return [
        {
            "role": "system",
            "content": SECTION_EXTRACTION_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": (
                f"Source ref: {source_ref}\n"
                f"Section name: {section.name}\n"
                f"Heading: {section.heading or ''}\n\n"
                f"{section.text}"
            ),
        },
    ]
