from src.workflows.resume_ingestion.nodes.base import GraphNode
from src.workflows.resume_ingestion.state import ResumeIngestionState
from src.ingestion.documents.parsing import parse_document_bytes
from src.ingestion.documents.store import DocumentStore


def make_parse_document_node(store: DocumentStore) -> GraphNode:
    def parse_document(state: ResumeIngestionState) -> dict:
        document = state.get("document")
        if document is None:
            return {"status": "failed", "error": "No retrieved document to parse."}
        content = store.read(document.content_ref)
        parsed = parse_document_bytes(
            content,
            filename=document.filename,
            content_type=document.content_type,
        )
        return {"parsed_document": parsed}

    return parse_document
