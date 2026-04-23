from __future__ import annotations

from pathlib import Path

import httpx

from src.ingestion.documents.models import DocumentArtifact, DocumentSource
from src.ingestion.documents.store import DocumentStore, filename_from_uri


def suffix_from_content_type(content_type: str | None) -> str:
    if not content_type:
        return ""
    normalized = content_type.split(";")[0].strip().lower()
    if normalized == "application/pdf":
        return ".pdf"
    if normalized.startswith("text/"):
        return ".txt"
    return ""


def retrieve_document_artifact(
    source: DocumentSource,
    *,
    store: DocumentStore,
    client: httpx.Client,
) -> DocumentArtifact:
    if source.kind == "uploaded_file":
        file_ref = source.file_ref or ""
        content = Path(file_ref).read_bytes()
        return DocumentArtifact(
            source=source,
            content_ref=file_ref,
            filename=source.filename or Path(file_ref).name,
            content_type=source.content_type,
            size_bytes=len(content),
        )

    uri = source.uri or ""
    response = client.get(uri)
    response.raise_for_status()
    filename = source.filename or filename_from_uri(uri)
    if not Path(filename).suffix:
        suffix = suffix_from_content_type(response.headers.get("content-type"))
        filename = f"{filename}{suffix}"
    content_ref = store.write(filename, response.content)
    return DocumentArtifact(
        source=source,
        content_ref=content_ref,
        filename=filename,
        content_type=source.content_type or response.headers.get("content-type"),
        size_bytes=len(response.content),
    )
