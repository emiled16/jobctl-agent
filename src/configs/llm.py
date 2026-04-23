"""Configuration loading and persistence for jobctl projects."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OpenAIConfig:
    api_key_env: str = "OPENAI_API_KEY"


@dataclass(frozen=True)
class OllamaConfig:
    host: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"


@dataclass(frozen=True)
class LLMConfig:
    provider: str = "codex"
    chat_model: str = "gpt-5.4-mini"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
