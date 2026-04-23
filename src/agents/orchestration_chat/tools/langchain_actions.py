from __future__ import annotations

import json
from typing import Any

from src.agents.orchestration_chat.tools.resume_ingestion import (
    source_from_ingestion_request,
)
from src.ingestion.documents.models import DocumentSource

ACTION_PREFIX = "JOBCTL_ACTION:"


def action_payload_from_tool_content(content: str) -> dict[str, Any] | None:
    if not content.startswith(ACTION_PREFIX):
        return None
    return json.loads(content.removeprefix(ACTION_PREFIX))


def action_from_ingestion_request(
    *,
    source_file_ref: str | None,
    source_uri: str | None,
    command_text: str | None = None,
) -> dict[str, Any]:
    source = source_from_ingestion_request(
        source_file_ref=source_file_ref,
        source_uri=source_uri,
        command_text=command_text,
    )
    if source is None:
        return {
            "kind": "needs_source",
            "response": (
                "Please provide the resume URI or local file path you want to ingest."
            ),
        }
    return {
        "kind": "ingest_resume",
        "source": source,
        "response": "Starting resume ingestion.",
    }


def inspect_resume_action(response: str) -> dict[str, Any]:
    return {"kind": "inspect_resume", "response": response}


def encode_action(payload: dict[str, Any]) -> str:
    return f"{ACTION_PREFIX}{json.dumps(_jsonable(payload), sort_keys=True)}"


def _jsonable(value: Any) -> Any:
    if isinstance(value, DocumentSource):
        return value.model_dump()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value
