from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from src.ingestion.documents.store import DocumentStore
from src.workflows.orchestration.graph import build_orchestration_graph
from src.workflows.orchestration.state import OrchestrationState


def run_orchestration_turn(
    *,
    user_input: str,
    state: OrchestrationState | None = None,
    document_store: DocumentStore | None = None,
    chat_model: BaseChatModel | None = None,
    ingestion_provider: BaseChatModel | None = None,
) -> OrchestrationState:
    graph = build_orchestration_graph(
        document_store=document_store,
        chat_model=chat_model,
        ingestion_provider=ingestion_provider,
    )
    next_state: OrchestrationState = {**(state or {}), "user_input": user_input}
    return graph.invoke(next_state)
