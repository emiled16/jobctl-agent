from __future__ import annotations

import os

from src.configs.exceptions import ConfigError


def build_chat_model(
    *,
    provider: str,
    chat_model: str,
    ollama_host: str = "http://localhost:11434",
    temperature: float = 0.2,
):
    normalized = provider.strip().lower()
    if normalized == "heuristic":
        return None
    if normalized == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ConfigError("OpenAI chat requires $OPENAI_API_KEY to be set.")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=chat_model, api_key=api_key, temperature=temperature)
    if normalized == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=chat_model, base_url=ollama_host, temperature=temperature
        )
    raise ConfigError("--llm must be one of 'heuristic', 'openai', or 'ollama'.")
