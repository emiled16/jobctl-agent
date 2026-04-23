from __future__ import annotations

from pathlib import Path

from src.ingestion.documents.models import DocumentSource


def build_document_source(
    *,
    file: Path | None,
    uri: str | None,
) -> DocumentSource:
    if file is not None:
        return DocumentSource(
            kind="uploaded_file",
            file_ref=str(file),
            filename=file.name,
            content_type=None,
        )
    return DocumentSource(kind="uri", uri=uri)
