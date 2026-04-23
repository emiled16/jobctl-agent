from __future__ import annotations

from src.ingestion.documents.store import DocumentStore
from src.llm.base import StructuredChatProvider
from src.workflows.orchestration.state import OrchestrationState
from src.workflows.resume_ingestion.graph import to_ingestion_result
from src.workflows.resume_ingestion.runner import run_resume_ingestion_workflow


def make_resume_ingestion_node(
    *,
    document_store: DocumentStore | None = None,
    llm_provider: StructuredChatProvider | None = None,
):
    store = document_store or DocumentStore()

    def resume_ingestion(state: OrchestrationState) -> dict:
        source = state.get("source")
        if source is None:
            return {
                "response": "Please provide a resume file path or URI before ingestion.",
                "status": "needs_source",
                "next_node": "end",
            }

        final_state = run_resume_ingestion_workflow(
            source=source,
            document_store=store,
            llm_provider=llm_provider,
        )
        result = to_ingestion_result(final_state)
        response = (
            f"Resume ingestion complete. Status: {final_state.get('status', 'unknown')}. "
            f"Extracted {len(result.facts.experiences)} experience entries, "
            f"{len(result.facts.projects)} projects, and {len(result.facts.skills)} skills."
        )
        return {
            "resume_ingestion_state": final_state,
            "resume_facts": result.facts,
            "response": response,
            "status": "ready" if final_state.get("status") == "valid" else "failed",
            "next_node": "end",
        }

    return resume_ingestion
