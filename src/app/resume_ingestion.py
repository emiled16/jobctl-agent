from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from openai import OpenAIError

from src.configs.exceptions import ConfigError
from src.ingestion.documents.sources import build_document_source
from src.ingestion.documents.store import DocumentStore
from src.llm.factory import build_structured_chat_provider
from src.utils.json import to_jsonable
from src.workflows.resume_ingestion.graph import (
    to_ingestion_result,
)
from src.workflows.resume_ingestion.output import format_resume_ingestion_summary
from src.workflows.resume_ingestion.runner import run_resume_ingestion_workflow
from src.workflows.resume_ingestion.tracing import summarize_node_update

app = typer.Typer(help="Run resume ingestion workflows.")


@app.command("ingest")
def ingest_resume(
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-f",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Local resume file to ingest.",
        ),
    ] = None,
    uri: Annotated[
        str | None,
        typer.Option("--uri", "-u", help="Remote resume URI to ingest."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print the final ResumeIngestionResult as JSON."),
    ] = False,
    show_state: Annotated[
        bool,
        typer.Option("--show-state", help="Print the final raw workflow state as JSON."),
    ] = False,
    logs: Annotated[
        bool,
        typer.Option("--logs/--no-logs", help="Print one summary line per node update."),
    ] = True,
    log_detail: Annotated[
        str,
        typer.Option(
            "--log-detail",
            help="Node log detail level: summary or details.",
        ),
    ] = "details",
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
            help="Extraction backend to use: heuristic or openai.",
        ),
    ] = "heuristic",
    model: Annotated[
        str,
        typer.Option("--model", help="OpenAI chat model for --llm openai."),
    ] = "gpt-5.4",
    embedding_model: Annotated[
        str,
        typer.Option("--embedding-model", help="OpenAI embedding model."),
    ] = "text-embedding-3-small",
) -> None:
    """Run the resume ingestion workflow manually."""
    if bool(file) == bool(uri):
        raise typer.BadParameter("Provide exactly one of --file or --uri.")
    if log_detail not in {"summary", "details"}:
        raise typer.BadParameter("--log-detail must be either 'summary' or 'details'.")

    try:
        provider = build_structured_chat_provider(
            provider=llm,
            chat_model=model,
            embedding_model=embedding_model,
        )
        source = build_document_source(file=file, uri=uri)
        final_state = run_resume_ingestion_workflow(
            source=source,
            document_store=DocumentStore(documents_dir),
            llm_provider=provider,
            on_node_update=(
                lambda node_name, update: typer.echo(
                    summarize_node_update(node_name, update, detail=log_detail)
                )
                if logs
                else None
            ),
        )
    except ConfigError as exc:
        raise typer.BadParameter(str(exc)) from exc
    except OpenAIError as exc:
        typer.echo(f"OpenAI request failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if show_state:
        typer.echo(json.dumps(to_jsonable(final_state), indent=2))
        return

    result = to_ingestion_result(final_state)
    if json_output:
        typer.echo(result.model_dump_json(indent=2))
        return

    typer.echo(format_resume_ingestion_summary(final_state.get("status"), result))
