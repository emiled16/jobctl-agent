from __future__ import annotations

import os

from src.configs.exceptions import ConfigError
from src.llm.base import LLMProvider, StructuredChatProvider
from src.llm.ollama.provider import OllamaProvider
from src.llm.openai.provider import OpenAIProvider


def build_chat_provider(
    *,
    provider: str,
    chat_model: str,
    embedding_model: str,
    ollama_host: str = "http://localhost:11434",
) -> LLMProvider | None:
    normalized = provider.strip().lower()
    if normalized == "heuristic":
        return None
    if normalized == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ConfigError("OpenAI chat requires $OPENAI_API_KEY to be set.")
        return OpenAIProvider(
            api_key=api_key,
            chat_model=chat_model,
            embedding_model=embedding_model,
        )
    if normalized == "ollama":
        return OllamaProvider(
            host=ollama_host,
            chat_model=chat_model,
            embedding_model=embedding_model,
        )
    raise ConfigError("--llm must be one of 'heuristic', 'openai', or 'ollama'.")


def build_structured_chat_provider(
    *,
    provider: str,
    chat_model: str,
    embedding_model: str,
    ollama_host: str = "http://localhost:11434",
) -> StructuredChatProvider | None:
    normalized = provider.strip().lower()
    if normalized == "heuristic":
        return None
    if normalized == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ConfigError("OpenAI extraction requires $OPENAI_API_KEY to be set.")
        return OpenAIProvider(
            api_key=api_key,
            chat_model=chat_model,
            embedding_model=embedding_model,
        )
    if normalized == "ollama":
        return OllamaProvider(
            host=ollama_host,
            chat_model=chat_model,
            embedding_model=embedding_model,
        )
    raise ConfigError("--llm must be one of 'heuristic', 'openai', or 'ollama'.")
