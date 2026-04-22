"""Ollama implementation of the LLMProvider protocol."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from typing import Any

import httpx

from src.llm.base import ChatChunk, ChatResponse, Message, ToolSpec
from src.llm.ollama.utils import (
    StructuredModel,
    parse_ollama_tool_calls,
    tool_specs_to_ollama,
)

logger = logging.getLogger(__name__)


class OllamaProvider:
    """LLMProvider that talks to an Ollama HTTP server."""

    def __init__(
        self,
        host: str = "http://localhost:11434",
        chat_model: str = "llama3.2",
        embedding_model: str = "nomic-embed-text",
        client: httpx.Client | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.host = host.rstrip("/")
        self.chat_model = chat_model
        self.embedding_model = embedding_model
        self._client = client or httpx.Client(timeout=timeout)

    def chat(
        self,
        messages: list[Message],
        *,
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.7,
    ) -> ChatResponse:
        payload: dict[str, Any] = {
            "model": self.chat_model,
            "messages": list(messages),
            "stream": False,
            "options": {"temperature": temperature},
        }
        ollama_tools = tool_specs_to_ollama(tools)
        if ollama_tools:
            payload["tools"] = ollama_tools

        response = self._client.post(f"{self.host}/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        message = data.get("message", {}) or {}
        content = message.get("content", "") or ""
        tool_calls = parse_ollama_tool_calls(message.get("tool_calls"))
        result: ChatResponse = {"content": content}
        if tool_calls:
            result["tool_calls"] = tool_calls
        return result

    def stream(
        self,
        messages: list[Message],
        *,
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.7,
    ) -> Iterator[ChatChunk]:
        payload: dict[str, Any] = {
            "model": self.chat_model,
            "messages": list(messages),
            "stream": True,
            "options": {"temperature": temperature},
        }
        ollama_tools = tool_specs_to_ollama(tools)
        if ollama_tools:
            payload["tools"] = ollama_tools

        with self._client.stream(
            "POST", f"{self.host}/api/chat", json=payload
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    logger.debug("skipping non-JSON ollama stream line: %r", line)
                    continue
                message = data.get("message", {}) or {}
                text = message.get("content", "") or ""
                tool_calls = parse_ollama_tool_calls(message.get("tool_calls"))
                chunk: ChatChunk = {}
                if text:
                    chunk["delta"] = text
                if tool_calls:
                    chunk["tool_call_delta"] = tool_calls[0]
                if chunk:
                    yield chunk
                if data.get("done"):
                    yield {"done": True}
                    return

    def chat_structured(
        self,
        messages: list[Message],
        response_format: type[StructuredModel],
        *,
        temperature: float = 0.3,
    ) -> StructuredModel:
        schema_json = json.dumps(response_format.model_json_schema(), sort_keys=True)
        instruction: Message = {
            "role": "system",
            "content": (
                "Return ONLY a JSON object matching this schema. "
                "Do not add prose, markdown fences, or comments.\n"
                f"Schema:\n{schema_json}"
            ),
        }
        augmented = [instruction, *messages]
        payload: dict[str, Any] = {
            "model": self.chat_model,
            "messages": augmented,
            "stream": False,
            "format": "json",
            "options": {"temperature": temperature},
        }
        response = self._client.post(f"{self.host}/api/chat", json=payload)
        response.raise_for_status()
        content = (response.json().get("message") or {}).get("content", "")
        try:
            return response_format.model_validate_json(content)
        except Exception as exc:
            raise ValueError(
                f"Ollama structured response did not validate against schema: {exc}"
            ) from exc

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.post(
            f"{self.host}/api/embed",
            json={"model": self.embedding_model, "input": texts},
        )
        response.raise_for_status()
        data = response.json()
        embeddings = data.get("embeddings")
        if embeddings is None and "embedding" in data:
            embeddings = [data["embedding"]]
        return embeddings or []
