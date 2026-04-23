from src.workflows.resume_ingestion.state import ResumeIngestionState


def resolve_source(state: ResumeIngestionState) -> dict:
    source = state.get("source")
    if source is None:
        return {
            "status": "needs_source",
            "error": "Resume ingestion requires a URI or uploaded file reference.",
        }
    if source.kind == "uri" and not source.uri:
        return {"status": "needs_source", "error": "URI resume source is missing uri."}
    if source.kind == "uploaded_file" and not source.file_ref:
        return {
            "status": "needs_source",
            "error": "Uploaded resume source is missing file_ref.",
        }
    return {"status": "retrieving", "error": None}
