from __future__ import annotations

import json

from typer.testing import CliRunner

from src.cli import app


def test_resume_ingestion_cli_outputs_node_logs_and_summary(tmp_path) -> None:
    resume = tmp_path / "resume.txt"
    resume.write_text(
        """Jane Doe
jane@example.com

EXPERIENCE
Acme - Senior Engineer
- Built ingestion pipelines.

SKILLS
Python, SQL
""",
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["resume", "ingest", "--file", str(resume)])

    assert result.exit_code == 0
    assert "[resolve_source] status=retrieving" in result.output
    assert "[retrieve_document] filename=resume.txt" in result.output
    assert "[segment_resume] sections=contact,experience,skills" in result.output
    assert "experiences=[Acme - Senior Engineer]" in result.output
    assert "skills=[Python, SQL]" in result.output
    assert "Status: valid" in result.output
    assert "Emails: jane@example.com" in result.output


def test_resume_ingestion_cli_can_output_detailed_node_logs(tmp_path) -> None:
    resume = tmp_path / "resume.txt"
    resume.write_text(
        """Jane Doe
jane@example.com

EXPERIENCE
Acme - Senior Engineer
- Built ingestion pipelines.

SKILLS
Python, SQL
""",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        ["resume", "ingest", "--file", str(resume), "--log-detail", "details"],
    )

    assert result.exit_code == 0
    assert "experiences=[Acme - Senior Engineer]" in result.output
    assert "skills=[Python, SQL]" in result.output


def test_resume_ingestion_cli_outputs_json_without_logs(tmp_path) -> None:
    resume = tmp_path / "resume.txt"
    resume.write_text("SKILLS\nPython, SQL", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        ["resume", "ingest", "--file", str(resume), "--json", "--no-logs"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert {skill["name"] for skill in payload["facts"]["skills"]} == {
        "Python",
        "SQL",
    }


def test_resume_ingestion_cli_requires_openai_api_key(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    resume = tmp_path / "resume.txt"
    resume.write_text("SKILLS\nPython", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        ["resume", "ingest", "--file", str(resume), "--llm", "openai"],
    )

    assert result.exit_code != 0
    assert "OPENAI_API_KEY" in result.output
