from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from src.configs.exceptions import ConfigError
from src.ingestion.documents.store import DocumentStore
from src.llm.base import LLMProvider, StructuredChatProvider
from src.llm.factory import build_chat_provider, build_structured_chat_provider
from src.workflows.orchestration.runner import run_orchestration_turn
from src.workflows.orchestration.state import OrchestrationState

app = typer.Typer(
    help="Run the orchestration chat agent.",
    invoke_without_command=True,
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def chat(
    ctx: typer.Context,
    documents_dir: Annotated[
        Path,
        typer.Option(
            "--documents-dir",
            help="Directory used to store downloaded documents.",
        ),
    ] = Path(".jobctl/documents"),
    llm: Annotated[
        str,
        typer.Option(
            "--llm",
            help="Chat backend to use: openai, ollama, or heuristic.",
        ),
    ] = "openai",
    model: Annotated[
        str,
        typer.Option("--model", help="Chat model for the selected --llm backend."),
    ] = "gpt-5.4-mini",
    embedding_model: Annotated[
        str,
        typer.Option("--embedding-model", help="Embedding model for the selected backend."),
    ] = "text-embedding-3-small",
    ollama_host: Annotated[
        str,
        typer.Option("--ollama-host", help="Ollama host when --llm ollama."),
    ] = "http://localhost:11434",
    ingestion_llm: Annotated[
        str,
        typer.Option(
            "--ingestion-llm",
            help="Resume extraction backend: same, openai, ollama, or heuristic.",
        ),
    ] = "same",
) -> None:
    """Start an interactive orchestration chat session."""
    if ctx.invoked_subcommand is not None:
        return

    document_store = DocumentStore(documents_dir)
    chat_provider: LLMProvider | None = None
    ingestion_provider: StructuredChatProvider | None = None
    providers_built = False
    state: OrchestrationState = {}
    typer.echo("Jobctl chat. Type /exit or /quit to leave.")
    while True:
        try:
            user_input = typer.prompt("jobctl")
        except (EOFError, KeyboardInterrupt):
            typer.echo("")
            return
        if user_input.strip() in {"/exit", "/quit"}:
            return
        if not user_input.strip():
            continue
        if not providers_built:
            try:
                chat_provider, ingestion_provider = _build_chat_providers(
                    llm=llm,
                    model=model,
                    embedding_model=embedding_model,
                    ollama_host=ollama_host,
                    ingestion_llm=ingestion_llm,
                )
                providers_built = True
            except ConfigError as exc:
                raise typer.BadParameter(str(exc)) from exc
        state = run_orchestration_turn(
            user_input=user_input,
            state=state,
            document_store=document_store,
            chat_provider=chat_provider,
            ingestion_provider=ingestion_provider,
        )
        typer.echo(state.get("response", ""))


@app.command("ask")
def ask(
    message: Annotated[str, typer.Argument(help="Message to send to the chat agent.")],
    documents_dir: Annotated[
        Path,
        typer.Option(
            "--documents-dir",
            help="Directory used to store downloaded documents.",
        ),
    ] = Path(".jobctl/documents"),
    llm: Annotated[
        str,
        typer.Option(
            "--llm",
            help="Chat backend to use: openai, ollama, or heuristic.",
        ),
    ] = "openai",
    model: Annotated[
        str,
        typer.Option("--model", help="Chat model for the selected --llm backend."),
    ] = "gpt-5.4-mini",
    embedding_model: Annotated[
        str,
        typer.Option("--embedding-model", help="Embedding model for the selected backend."),
    ] = "text-embedding-3-small",
    ollama_host: Annotated[
        str,
        typer.Option("--ollama-host", help="Ollama host when --llm ollama."),
    ] = "http://localhost:11434",
    ingestion_llm: Annotated[
        str,
        typer.Option(
            "--ingestion-llm",
            help="Resume extraction backend: same, openai, ollama, or heuristic.",
        ),
    ] = "same",
) -> None:
    """Run one orchestration chat turn."""
    try:
        chat_provider, ingestion_provider = _build_chat_providers(
            llm=llm,
            model=model,
            embedding_model=embedding_model,
            ollama_host=ollama_host,
            ingestion_llm=ingestion_llm,
        )
    except ConfigError as exc:
        raise typer.BadParameter(str(exc)) from exc
    state = run_orchestration_turn(
        user_input=message,
        document_store=DocumentStore(documents_dir),
        chat_provider=chat_provider,
        ingestion_provider=ingestion_provider,
    )
    typer.echo(state.get("response", ""))


def _build_chat_providers(
    *,
    llm: str,
    model: str,
    embedding_model: str,
    ollama_host: str,
    ingestion_llm: str,
) -> tuple[LLMProvider | None, StructuredChatProvider | None]:
    chat_provider = build_chat_provider(
        provider=llm,
        chat_model=model,
        embedding_model=embedding_model,
        ollama_host=ollama_host,
    )
    ingestion_backend = llm if ingestion_llm == "same" else ingestion_llm
    if ingestion_backend == llm and isinstance(chat_provider, StructuredChatProvider):
        return chat_provider, chat_provider
    ingestion_provider = build_structured_chat_provider(
        provider=ingestion_backend,
        chat_model=model,
        embedding_model=embedding_model,
        ollama_host=ollama_host,
    )
    return chat_provider, ingestion_provider
