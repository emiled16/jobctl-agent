from __future__ import annotations

import typer

from src.app.resume_ingestion import app as resume_ingestion_app

app = typer.Typer(help="Jobctl command line tools.")
app.add_typer(resume_ingestion_app, name="resume")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
