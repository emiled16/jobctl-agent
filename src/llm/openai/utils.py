from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from src.llm.base import ToolCall, ToolSpec

logger = logging.getLogger(__name__)

MAX_RETRY_ATTEMPTS = 3
StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


def retry(operation: Callable[[], Any]) -> Any:
    try:
        from openai import APIConnectionError, APIError, APITimeoutError, RateLimitError
    except ModuleNotFoundError:
        APIConnectionError = APIError = APITimeoutError = RateLimitError = Exception  # type: ignore[assignment]

    transient = (RateLimitError, APITimeoutError, APIConnectionError, APIError)
    last_error: Exception | None = None
    for attempt in range(MAX_RETRY_ATTEMPTS):
        try:
            return operation()
        except transient as exc:
            last_error = exc
            if attempt == MAX_RETRY_ATTEMPTS - 1:
                break
            time.sleep(2**attempt)
    assert last_error is not None
    raise last_error


def tool_specs_to_openai(tools: list[ToolSpec] | None) -> list[dict[str, Any]] | None:
    if not tools:
        return None
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("parameters", {"type": "object", "properties": {}}),
            },
        }
        for t in tools
    ]


def parse_openai_tool_calls(raw: Any) -> list[ToolCall]:
    if not raw:
        return []
    calls: list[ToolCall] = []
    for tc in raw:
        fn = getattr(tc, "function", None)
        name = getattr(fn, "name", "") if fn else ""
        args_raw = getattr(fn, "arguments", "") if fn else ""
        try:
            args = json.loads(args_raw) if args_raw else {}
        except json.JSONDecodeError:
            args = {"_raw": args_raw}
        calls.append(
            ToolCall(id=getattr(tc, "id", "") or "", name=name or "", arguments=args),
        )
    return calls
