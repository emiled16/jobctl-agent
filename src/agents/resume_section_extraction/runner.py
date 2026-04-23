from __future__ import annotations

from src.agents.resume_section_extraction.prompts import (
    build_extract_section_messages,
)
from src.agents.resume_section_extraction.schemas import (
    ExtractedSectionFacts,
    to_section_facts,
)
from src.ingestion.resumes.models import ResumeSection, SectionFacts
from src.llm.base import StructuredChatProvider


def extract_section_facts_with_llm(
    section: ResumeSection,
    *,
    source_ref: str,
    provider: StructuredChatProvider,
) -> SectionFacts:
    messages = build_extract_section_messages(section, source_ref=source_ref)
    result = provider.chat_structured(messages, ExtractedSectionFacts, temperature=0.1)
    return to_section_facts(
        result,
        source_ref=source_ref,
        fallback_section_name=section.name,
        raw_text=section.text,
        text_span=(section.start_char or 0, section.end_char or len(section.text)),
    )
