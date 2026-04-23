from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.constants import END, START
from langgraph.graph import StateGraph

from src.ingestion.documents.store import DocumentStore
from src.workflows.orchestration.nodes.chat_agent import make_chat_agent_node
from src.workflows.orchestration.nodes.resume_ingestion import (
    make_resume_ingestion_node,
)
from src.workflows.orchestration.state import OrchestrationState


def build_orchestration_graph(
    *,
    document_store: DocumentStore | None = None,
    chat_model: BaseChatModel | None = None,
    ingestion_provider: BaseChatModel | None = None,
):
    graph = StateGraph(OrchestrationState)
    graph.add_node("chat_agent", make_chat_agent_node(chat_model))
    graph.add_node(
        "resume_ingestion",
        make_resume_ingestion_node(
            document_store=document_store,
            llm_provider=ingestion_provider,
        ),
    )

    graph.add_edge(START, "chat_agent")
    graph.add_conditional_edges(
        "chat_agent",
        route_after_chat_agent,
        {"resume_ingestion": "resume_ingestion", "end": END},
    )
    graph.add_edge("resume_ingestion", END)
    return graph.compile()


def route_after_chat_agent(state: OrchestrationState) -> str:
    return state.get("next_node", "end")
