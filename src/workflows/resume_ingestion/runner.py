from __future__ import annotations

from collections.abc import Callable

from src.ingestion.documents.models import DocumentSource
from src.ingestion.documents.store import DocumentStore
from src.llm.base import StructuredChatProvider
from src.workflows.resume_ingestion.graph import build_resume_ingestion_graph
from src.workflows.resume_ingestion.state import ResumeIngestionState

NodeUpdateCallback = Callable[[str, dict], None]


def run_resume_ingestion_workflow(
    *,
    source: DocumentSource,
    document_store: DocumentStore,
    llm_provider: StructuredChatProvider | None,
    on_node_update: NodeUpdateCallback | None = None,
) -> ResumeIngestionState:
    graph = build_resume_ingestion_graph(
        document_store=document_store,
        llm_provider=llm_provider,
    )
    state: ResumeIngestionState = {"source": source}
    for update in graph.stream(state, stream_mode="updates"):
        if on_node_update:
            for node_name, node_update in update.items():
                on_node_update(node_name, node_update)
        for node_update in update.values():
            merge_state_update(state, node_update)
    return state


def merge_state_update(state: dict, update: dict) -> None:
    for key, value in update.items():
        if key == "section_facts":
            state.setdefault(key, [])
            state[key].extend(value)
        elif key in {"warnings", "validation_errors"}:
            state[key] = value
        else:
            state[key] = value
