from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from src.agents.orchestration_chat.tools.router import ChatRoute
from src.cli import app
from src.llm.base import Message
from src.workflows.orchestration.runner import run_orchestration_turn


def _write_resume(path: Path) -> None:
    path.write_text(
        """Jane Doe
jane@example.com

SUMMARY
Builder of data tools.

EXPERIENCE
Acme - Senior Engineer
- Built ingestion pipelines.
- Improved data quality checks.

PROJECTS
Resume Agent
- Parsed resumes into structured facts.

SKILLS
Python, SQL, LangGraph
""",
        encoding="utf-8",
    )


def test_orchestration_ingests_resume_with_slash_command(tmp_path: Path) -> None:
    resume = tmp_path / "resume.txt"
    _write_resume(resume)

    state = run_orchestration_turn(user_input=f"/ingest --file {resume}")

    assert state["status"] == "ready"
    assert state["resume_facts"] is not None
    assert state["resume_facts"].contact is not None
    assert state["resume_facts"].contact.emails == ["jane@example.com"]
    assert "Resume ingestion complete" in state["response"]


def test_orchestration_ingest_without_source_asks_for_resume_source() -> None:
    state = run_orchestration_turn(user_input="/ingest")

    assert state["status"] == "needs_source"
    assert "Please provide a resume file path or URI" in state["response"]


def test_orchestration_print_section_asks_mcq_after_ingestion(tmp_path: Path) -> None:
    resume = tmp_path / "resume.txt"
    _write_resume(resume)
    state = run_orchestration_turn(user_input=f"/ingest {resume}")

    state = run_orchestration_turn(user_input="print a section", state=state)

    assert state["pending_user_action"] == "choose_resume_section"
    assert "1. Summary" in state["response"]
    assert "3. Experience" in state["response"]


def test_orchestration_nested_section_choice_renders_selected_section(
    tmp_path: Path,
) -> None:
    resume = tmp_path / "resume.txt"
    _write_resume(resume)
    state = run_orchestration_turn(user_input=f"/ingest {resume}")
    state = run_orchestration_turn(user_input="print a section", state=state)

    state = run_orchestration_turn(user_input="3", state=state)

    assert state["pending_user_action"] is None
    assert "Experience" in state["response"]
    assert "Acme - Senior Engineer" in state["response"]
    assert "- Built ingestion pipelines." in state["response"]


def test_orchestration_direct_experience_request_filters_experience(
    tmp_path: Path,
) -> None:
    resume = tmp_path / "resume.txt"
    _write_resume(resume)
    state = run_orchestration_turn(user_input=f"/ingest {resume}")

    state = run_orchestration_turn(user_input="show Acme experience", state=state)

    assert state["requested_section"] == "experiences"
    assert "Acme - Senior Engineer" in state["response"]
    assert "Resume Agent" not in state["response"]


def test_orchestration_answers_fact_question_after_ingestion(tmp_path: Path) -> None:
    resume = tmp_path / "resume.txt"
    _write_resume(resume)
    state = run_orchestration_turn(user_input=f"/ingest {resume}")

    state = run_orchestration_turn(user_input="what is the email?", state=state)

    assert state["response"] == "jane@example.com"


def test_orchestration_cli_runs_one_chat_turn(tmp_path: Path) -> None:
    resume = tmp_path / "resume.txt"
    _write_resume(resume)

    result = CliRunner().invoke(
        app,
        ["chat", "ask", f"/ingest --file {resume}", "--llm", "heuristic"],
    )

    assert result.exit_code == 0
    assert "Resume ingestion complete" in result.output


def test_orchestration_cli_chat_defaults_to_interactive_session() -> None:
    result = CliRunner().invoke(app, ["chat"], input="/exit\n")

    assert result.exit_code == 0
    assert "Jobctl chat. Type /exit or /quit to leave." in result.output


def test_orchestration_llm_router_can_route_ingestion_request(tmp_path: Path) -> None:
    resume = tmp_path / "resume.txt"
    _write_resume(resume)
    provider = FakeRoutingProvider(
        ChatRoute(intent="ingest_resume", source_file_ref=str(resume))
    )

    state = run_orchestration_turn(
        user_input="please load my resume",
        chat_provider=provider,
        ingestion_provider=None,
    )

    assert state["status"] == "ready"
    assert state["resume_facts"] is not None
    assert "Resume ingestion complete" in state["response"]


class FakeRoutingProvider:
    def __init__(self, route: ChatRoute) -> None:
        self.route = route

    def chat_structured(
        self,
        messages: list[Message],
        response_format: type[ChatRoute],
        *,
        temperature: float = 0.3,
    ) -> ChatRoute:
        return self.route

    def chat(
        self,
        messages: list[Message],
        *,
        tools: list | None = None,
        temperature: float = 0.7,
    ) -> dict:
        return {"content": "hello"}
