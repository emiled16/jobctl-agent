from __future__ import annotations

import os

from src.configs.exceptions import ConfigError
from src.llm.base import StructuredChatProvider
from src.llm.openai.provider import OpenAIProvider


def build_structured_chat_provider(
    *,
    provider: str,
    chat_model: str,
    embedding_model: str,
) -> StructuredChatProvider | None:
    normalized = provider.strip().lower()
    if normalized == "heuristic":
        return None
    if normalized != "openai":
        raise ConfigError("--llm must be either 'heuristic' or 'openai'.")

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ConfigError("OpenAI extraction requires $OPENAI_API_KEY to be set.")
    return OpenAIProvider(
        api_key=api_key,
        chat_model=chat_model,
        embedding_model=embedding_model,
    )
