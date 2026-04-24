from __future__ import annotations

import shlex
from pathlib import Path
from urllib.parse import unquote, urlparse

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


def source_from_ingestion_request(
    *,
    source_file_ref: str | None = None,
    source_uri: str | None = None,
    command_text: str | None = None,
) -> DocumentSource | None:
    if source_uri:
        source_uri = _strip_wrapping_quotes(source_uri.strip())
        if source_uri.startswith("file://"):
            return _file_source(_path_from_file_uri(source_uri))
        return _uri_source(source_uri)
    if source_file_ref:
        return _file_source(source_file_ref)
    if command_text:
        stripped = command_text.strip()
        if stripped.startswith("/ingest"):
            return source_from_ingest_command(stripped)
        stripped = _strip_wrapping_quotes(stripped)
        if stripped.startswith("file://"):
            return _file_source(_path_from_file_uri(stripped))
        if stripped.startswith(("http://", "https://")):
            return _uri_source(stripped)
        if not any(character.isspace() for character in stripped):
            return _file_source(stripped)
    return None


def _file_source(value: str) -> DocumentSource:
    path = Path(_strip_wrapping_quotes(value.strip()))
    return DocumentSource(
        kind="uploaded_file",
        file_ref=str(path),
        filename=path.name,
        content_type=None,
    )


def _uri_source(value: str) -> DocumentSource:
    return DocumentSource(kind="uri", uri=value)


def _path_from_file_uri(value: str) -> str:
    parsed = urlparse(value)
    return unquote(parsed.path)


def _strip_wrapping_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
