from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from src.llm.base import ChatChunk, ChatResponse, Message, ToolSpec
from src.llm.openai.utils import (
    StructuredModel,
    parse_openai_tool_calls,
    retry,
    tool_specs_to_openai,
)


class OpenAIProvider:
    """LLMProvider that talks to the OpenAI HTTP API via the official SDK."""

    def __init__(
        self,
        api_key: str,
        chat_model: str,
        embedding_model: str,
        client: Any | None = None,
    ) -> None:
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
        self._client = client
        self.chat_model = chat_model
        self.embedding_model = embedding_model

    def chat(
        self,
        messages: list[Message],
        *,
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.7,
    ) -> ChatResponse:
        kwargs: dict[str, Any] = {
            "model": self.chat_model,
            "messages": list(messages),
            "temperature": temperature,
        }
        openai_tools = tool_specs_to_openai(tools)
        if openai_tools:
            kwargs["tools"] = openai_tools

        response = retry(lambda: self._client.chat.completions.create(**kwargs))
        message = response.choices[0].message
        content = getattr(message, "content", "") or ""
        tool_calls = parse_openai_tool_calls(getattr(message, "tool_calls", None))
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
        kwargs: dict[str, Any] = {
            "model": self.chat_model,
            "messages": list(messages),
            "temperature": temperature,
            "stream": True,
        }
        openai_tools = tool_specs_to_openai(tools)
        if openai_tools:
            kwargs["tools"] = openai_tools

        stream = retry(lambda: self._client.chat.completions.create(**kwargs))
        for event in stream:
            try:
                delta = event.choices[0].delta
            except (AttributeError, IndexError):
                continue
            text = getattr(delta, "content", None) or ""
            tc_delta = getattr(delta, "tool_calls", None)
            chunk: ChatChunk = {}
            if text:
                chunk["delta"] = text
            if tc_delta:
                parsed = parse_openai_tool_calls(tc_delta)
                if parsed:
                    chunk["tool_call_delta"] = parsed[0]
            if chunk:
                yield chunk
        yield {"done": True}

    def chat_structured(
        self,
        messages: list[Message],
        response_format: type[StructuredModel],
        *,
        temperature: float = 0.3,
    ) -> StructuredModel:
        response = retry(
            lambda: self._client.beta.chat.completions.parse(
                model=self.chat_model,
                messages=list(messages),
                response_format=response_format,
                temperature=temperature,
            )
        )
        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise ValueError(
                "OpenAI structured response did not include parsed content"
            )
        return parsed

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = retry(
            lambda: self._client.embeddings.create(
                model=self.embedding_model, input=texts
            )
        )
        return [item.embedding for item in response.data]
