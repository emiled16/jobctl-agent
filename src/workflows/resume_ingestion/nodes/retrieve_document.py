import httpx

from src.workflows.resume_ingestion.nodes.base import GraphNode
from src.workflows.resume_ingestion.state import ResumeIngestionState
from src.ingestion.documents.models import DocumentSource
from src.ingestion.documents.retrieval import retrieve_document_artifact
from src.ingestion.documents.store import DocumentStore


def require_source(state: ResumeIngestionState) -> DocumentSource:
    source = state.get("source")
    if source is None:
        raise ValueError("Resume ingestion requires source.")
    return source


def make_retrieve_document_node(
    store: DocumentStore,
    client: httpx.Client,
) -> GraphNode:
    def retrieve_document(state: ResumeIngestionState) -> dict:
        source = require_source(state)
        artifact = retrieve_document_artifact(
            source,
            store=store,
            client=client,
        )
        return {"document": artifact, "status": "parsing"}

    return retrieve_document
