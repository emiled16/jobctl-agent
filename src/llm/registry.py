"""Factory that instantiates the configured LLMProvider implementation."""

from __future__ import annotations

import os
from pathlib import Path

from src.configs.exceptions import ConfigError
from src.configs.llm import LLMConfig
from src.llm.base import LLMProvider

_PROVIDER_CACHE: dict[str, LLMProvider] = {}


def get_provider(
    config: LLMConfig,
    *,
    cwd: Path | None = None,
    cache: bool = True,
) -> LLMProvider:
    """Instantiate the configured LLM provider.

    The instance is cached per (provider, chat_model, embedding_model) key so
    heavy resources (e.g. the HuggingFace embedder) load only once per process.
    """
    provider_name = config.llm.provider
    cache_key = (
        f"{provider_name}::{config.llm.chat_model}::{config.llm.embedding_model}"
    )
    if cache and cache_key in _PROVIDER_CACHE:
        return _PROVIDER_CACHE[cache_key]

    provider = _build_provider(provider_name, config, cwd)
    if cache:
        _PROVIDER_CACHE[cache_key] = provider
    return provider


def reset_cache() -> None:
    _PROVIDER_CACHE.clear()


def _build_provider(
    provider_name: str,
    config: LLMConfig,
) -> LLMProvider:
    if provider_name == "openai":
        from src.llm.openai.provider import OpenAIProvider

        api_key = os.environ.get(config.llm.openai.api_key_env, "")
        if not api_key:
            raise ConfigError(
                f"OpenAI provider requires ${config.llm.openai.api_key_env} to be set."
            )
        return OpenAIProvider(
            api_key=api_key,
            chat_model=config.llm.chat_model,
            embedding_model=config.llm.embedding_model,
        )

    if provider_name == "ollama":
        from src.llm.ollama.provider import OllamaProvider

        return OllamaProvider(
            host=config.llm.ollama.host,
            chat_model=config.llm.chat_model,
            embedding_model=config.llm.ollama.embedding_model
            or config.llm.embedding_model,
        )

    raise ConfigError(
        f"Unknown llm.provider {provider_name!r}; expected one of 'openai', 'ollama', 'codex'."
    )
