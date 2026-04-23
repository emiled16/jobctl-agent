from __future__ import annotations

from typing import Any, cast

from langchain_core.language_models.chat_models import BaseChatModel

from src.agents.resume_section_extraction.prompts.v1 import (
    build_extract_section_messages,
)
from src.agents.resume_section_extraction.schemas import (
    ExtractedSectionFacts,
    to_section_facts,
)
from src.ingestion.resumes.models import ResumeSection, SectionFacts


def extract_section_facts_with_llm(
    section: ResumeSection,
    *,
    source_ref: str,
    model: BaseChatModel,
) -> SectionFacts:
    messages = build_extract_section_messages(section, source_ref=source_ref)
    runnable = cast(
        Any,
        model.bind(temperature=0.1).with_structured_output(ExtractedSectionFacts),
    )
    result = cast(ExtractedSectionFacts, runnable.invoke(messages))
    return to_section_facts(
        result,
        source_ref=source_ref,
        fallback_section_name=section.name,
        raw_text=section.text,
        text_span=(section.start_char or 0, section.end_char or len(section.text)),
    )
