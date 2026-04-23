from langchain_core.language_models.chat_models import BaseChatModel

from src.agents.resume_section_extraction.runner import (
    extract_section_facts_with_llm,
)
from src.workflows.resume_ingestion.nodes.base import GraphNode
from src.workflows.resume_ingestion.state import SectionExtractionState
from src.ingestion.resumes.extraction import extract_section_facts_heuristic


def make_extract_section_node(
    llm_provider: BaseChatModel | None,
) -> GraphNode:
    def extract_section(state: SectionExtractionState) -> dict:
        if llm_provider is None:
            section_facts = extract_section_facts_heuristic(
                state["section"],
                source_ref=state["source_ref"],
            )
        else:
            section_facts = extract_section_facts_with_llm(
                state["section"],
                source_ref=state["source_ref"],
                model=llm_provider,
            )
        return {"section_facts": [section_facts]}

    return extract_section
