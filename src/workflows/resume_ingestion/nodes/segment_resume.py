from src.workflows.resume_ingestion.state import ResumeIngestionState
from src.ingestion.resumes.segmentation import segment_resume


def segment_resume_node(state: ResumeIngestionState) -> dict:
    parsed = state.get("parsed_document")
    if parsed is None:
        return {"status": "failed", "error": "No parsed document to segment."}
    return {"sections": segment_resume(parsed.text), "status": "extracting"}
