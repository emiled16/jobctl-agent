from __future__ import annotations

import shlex
from pathlib import Path

from src.ingestion.documents.models import DocumentSource


def source_from_ingest_command(command: str) -> DocumentSource | None:
    parts = shlex.split(command)
    if len(parts) < 2:
        return None
    if "--file" in parts:
        index = parts.index("--file") + 1
        return _file_source(parts[index]) if index < len(parts) else None
    if "-f" in parts:
        index = parts.index("-f") + 1
        return _file_source(parts[index]) if index < len(parts) else None
    if "--uri" in parts:
        index = parts.index("--uri") + 1
        return _uri_source(parts[index]) if index < len(parts) else None
    if "-u" in parts:
        index = parts.index("-u") + 1
        return _uri_source(parts[index]) if index < len(parts) else None
    value = parts[1]
    if value.startswith(("http://", "https://")):
        return _uri_source(value)
    return _file_source(value)


def _file_source(value: str) -> DocumentSource:
    path = Path(value)
    return DocumentSource(
        kind="uploaded_file",
        file_ref=str(path),
        filename=path.name,
        content_type=None,
    )


def _uri_source(value: str) -> DocumentSource:
    return DocumentSource(kind="uri", uri=value)
