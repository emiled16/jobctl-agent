from __future__ import annotations

from collections.abc import Callable

import httpx
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.types import Send

from src.workflows.resume_ingestion.nodes.extract_section import make_extract_section_node
from src.workflows.resume_ingestion.nodes.merge_section_facts import merge_section_facts
from src.workflows.resume_ingestion.nodes.parse_document import make_parse_document_node
from src.workflows.resume_ingestion.nodes.resolve_source import resolve_source
from src.workflows.resume_ingestion.nodes.retrieve_document import (
    make_retrieve_document_node,
)
from src.workflows.resume_ingestion.nodes.segment_resume import segment_resume_node
from src.workflows.resume_ingestion.nodes.validate_facts import validate_facts
from src.workflows.resume_ingestion.state import (
    ResumeIngestionState,
)
from src.ingestion.documents.store import DocumentStore
from src.ingestion.resumes.models import (
    ResumeFacts,
    ResumeIngestionResult,
)
from src.llm.base import StructuredChatProvider

GraphNode = Callable[[ResumeIngestionState], dict]


def build_resume_ingestion_graph(
    *,
    document_store: DocumentStore | None = None,
    llm_provider: StructuredChatProvider | None = None,
    http_client: httpx.Client | None = None,
):
    store = document_store or DocumentStore()
    client = http_client or httpx.Client(follow_redirects=True, timeout=30.0)

    graph = StateGraph(ResumeIngestionState)

    # add nodes
    graph.add_node("resolve_source", resolve_source)
    graph.add_node("retrieve_document", make_retrieve_document_node(store, client))
    graph.add_node("parse_document", make_parse_document_node(store))
    graph.add_node("segment_resume", segment_resume_node)
    graph.add_node("extract_section", make_extract_section_node(llm_provider))
    graph.add_node("merge_section_facts", merge_section_facts)
    graph.add_node("validate_facts", validate_facts)

    # add edges
    graph.add_edge(START, "resolve_source")
    graph.add_conditional_edges(
        "resolve_source",
        route_after_source_resolution,
        {"continue": "retrieve_document", "stop": END},
    )
    graph.add_edge("retrieve_document", "parse_document")
    graph.add_edge("parse_document", "segment_resume")
    graph.add_conditional_edges("segment_resume", dispatch_section_extraction)
    graph.add_edge("extract_section", "merge_section_facts")
    graph.add_edge("merge_section_facts", "validate_facts")
    graph.add_edge("validate_facts", END)
    return graph.compile()


def route_after_source_resolution(state: ResumeIngestionState) -> str:
    if state.get("status") == "needs_source":
        return "stop"
    return "continue"


def dispatch_section_extraction(state: ResumeIngestionState) -> list[Send]:
    document = state.get("document")
    source_ref = document.content_ref if document else "unknown"
    return [
        Send("extract_section", {"source_ref": source_ref, "section": section})
        for section in state.get("sections", [])
    ]


## for testing
def to_ingestion_result(state: ResumeIngestionState) -> ResumeIngestionResult:
    return ResumeIngestionResult(
        facts=state.get("facts") or ResumeFacts(),
        warnings=state.get("warnings", []),
        validation_errors=state.get("validation_errors", []),
    )
