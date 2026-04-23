from __future__ import annotations

import mimetypes
from pathlib import Path

import fitz

from src.ingestion.documents.models import ParsedDocument


def detect_content_type(filename: str | None, content_type: str | None) -> str:
    if content_type:
        return content_type.split(";")[0].strip().lower()
    if filename:
        guessed, _ = mimetypes.guess_type(filename)
        if guessed:
            return guessed
    return "application/octet-stream"


def parse_document_bytes(
    content: bytes,
    *,
    filename: str | None,
    content_type: str | None,
) -> ParsedDocument:
    detected = detect_content_type(filename, content_type)
    suffix = Path(filename or "").suffix.lower()
    if detected == "application/pdf" or suffix == ".pdf":
        return parse_pdf(content)
    if detected.startswith("text/") or suffix in {".txt", ".md"}:
        return ParsedDocument(
            text=content.decode("utf-8", errors="replace"),
            parser="plain_text",
        )
    raise ValueError(f"Unsupported document type: {detected}")


def parse_pdf(content: bytes) -> ParsedDocument:
    page_texts: list[str] = []
    with fitz.open(stream=content, filetype="pdf") as document:
        for page in document:
            page_texts.append(page.get_text("text"))
    return ParsedDocument(
        text="\n\n".join(page_texts).strip(),
        page_texts=page_texts,
        parser="pymupdf",
    )
