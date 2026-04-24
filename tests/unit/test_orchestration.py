from __future__ import annotations

from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from typer.testing import CliRunner

from src.cli import app
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


def test_orchestration_ingests_resume_with_slash_command(
    tmp_path: Path,
) -> None:
    resume = tmp_path / "resume.txt"
    _write_resume(resume)
    model = FakeOrchestrationChatModel()

    state = run_orchestration_turn(
        user_input=f"/ingest --file {resume}",
        chat_model=model,
        ingestion_provider=None,
    )

    assert model.calls >= 1
    assert state["status"] == "ready"
    assert state["resume_facts"] is not None
    assert state["resume_facts"].contact is not None
    assert state["resume_facts"].contact.emails == ["jane@example.com"]
    assert "Resume ingestion complete" in state["response"]


def test_orchestration_ingest_without_source_asks_for_resume_source() -> None:
    state = run_orchestration_turn(
        user_input="/ingest",
        chat_model=FakeOrchestrationChatModel(),
        ingestion_provider=None,
    )

    assert state["status"] == "needs_source"
    assert state["interaction_state"] == "awaiting_resume_source"
    assert "Please provide the resume URI or local file path" in state["response"]


def test_orchestration_ingests_after_user_provides_uri(tmp_path: Path) -> None:
    resume = tmp_path / "resume.txt"
    _write_resume(resume)
    model = FakeOrchestrationChatModel()
    state = run_orchestration_turn(
        user_input="please ingest my resume",
        chat_model=model,
        ingestion_provider=None,
    )

    state = run_orchestration_turn(
        user_input=resume.as_uri(),
        state=state,
        chat_model=model,
        ingestion_provider=None,
    )

    assert state["status"] == "ready"
    assert state["interaction_state"] is None
    assert state["resume_facts"] is not None


def test_orchestration_ingests_after_user_provides_quoted_file_path(
    tmp_path: Path,
) -> None:
    resume = tmp_path / "resume with spaces.txt"
    _write_resume(resume)
    model = FakeOrchestrationChatModel()
    state = run_orchestration_turn(
        user_input="please ingest my resume",
        chat_model=model,
        ingestion_provider=None,
    )

    state = run_orchestration_turn(
        user_input=f'"{resume}"',
        state=state,
        chat_model=model,
        ingestion_provider=None,
    )

    assert state["status"] == "ready"
    assert state["interaction_state"] is None
    assert state["resume_facts"] is not None


def test_orchestration_lists_sections_after_ingestion(
    tmp_path: Path,
) -> None:
    resume = tmp_path / "resume.txt"
    _write_resume(resume)
    model = FakeOrchestrationChatModel()
    state = run_orchestration_turn(
        user_input=f"/ingest --file {resume}",
        chat_model=model,
        ingestion_provider=None,
    )

    state = run_orchestration_turn(
        user_input="what sections are currently ingested?",
        state=state,
        chat_model=model,
        ingestion_provider=None,
    )

    assert state["intent"] == "inspect_resume"
    assert "Ingested resume sections:" in state["response"]
    assert "Professional Experiences: 1 item" in state["response"]
    assert "Projects: 1 item" in state["response"]


def test_orchestration_lists_experiences(
    tmp_path: Path,
) -> None:
    resume = tmp_path / "resume.txt"
    _write_resume(resume)
    model = FakeOrchestrationChatModel()
    state = run_orchestration_turn(
        user_input=f"/ingest --file {resume}",
        chat_model=model,
        ingestion_provider=None,
    )

    state = run_orchestration_turn(
        user_input="what are the professional experiences?",
        state=state,
        chat_model=model,
        ingestion_provider=None,
    )

    assert state["intent"] == "inspect_resume"
    assert "Professional Experiences" in state["response"]
    assert "1. Acme | Senior Engineer" in state["response"]


def test_orchestration_shows_bullet_detail_for_experience(
    tmp_path: Path,
) -> None:
    resume = tmp_path / "resume.txt"
    _write_resume(resume)
    model = FakeOrchestrationChatModel()
    state = run_orchestration_turn(
        user_input=f"/ingest --file {resume}",
        chat_model=model,
        ingestion_provider=None,
    )

    state = run_orchestration_turn(
        user_input="show me the first bullet point for the first professional experience",
        state=state,
        chat_model=model,
        ingestion_provider=None,
    )

    assert state["intent"] == "inspect_resume"
    assert "Professional experience 1: Acme | Senior Engineer" in state["response"]
    assert "Bullet 1: Built ingestion pipelines." in state["response"]


def test_orchestration_requires_configured_chat_model() -> None:
    try:
        run_orchestration_turn(user_input="/ingest --file resume.txt")
    except ValueError as exc:
        assert "The chat agent requires a configured chat model." in str(exc)
    else:
        raise AssertionError("Expected chat agent to require a model.")


def test_orchestration_cli_chat_defaults_to_interactive_session() -> None:
    result = CliRunner().invoke(app, ["chat"], input="/exit\n")

    assert result.exit_code == 0
    assert "Jobctl chat. Type /exit or /quit to leave." in result.output


def test_orchestration_cli_ask_rejects_heuristic_backend() -> None:
    result = CliRunner().invoke(app, ["chat", "ask", "/ingest", "--llm", "heuristic"])

    assert result.exit_code != 0
    assert "requires --llm openai or --llm" in result.output
    assert "ollama" in result.output


def test_langchain_routes_ingestion_with_tool_call(
    tmp_path: Path,
) -> None:
    resume = tmp_path / "resume.txt"
    _write_resume(resume)
    model = FakeOrchestrationChatModel()

    state = run_orchestration_turn(
        user_input=f"/ingest --file {resume}",
        chat_model=model,
        ingestion_provider=None,
    )

    assert model.calls >= 1
    assert state["status"] == "ready"
    assert state["resume_facts"] is not None
    assert "Resume ingestion complete" in state["response"]


class FakeOrchestrationChatModel(BaseChatModel):
    calls: int = 0

    @property
    def _llm_type(self) -> str:
        return "fake-orchestration-chat-model"

    def bind_tools(self, tools, *, tool_choice=None, **kwargs):
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager=None,
        **kwargs,
    ) -> ChatResult:
        self.calls += 1
        if messages[-1].type == "tool":
            response = AIMessage(content="Completed.")
        else:
            response = AIMessage(content="", tool_calls=[self._tool_call(messages)])
        return ChatResult(generations=[ChatGeneration(message=response)])

    def _tool_call(self, messages: list[BaseMessage]) -> dict:
        user_input = self._latest_user_text(messages).strip()
        normalized = user_input.lower()
        if "sections" in normalized:
            return {
                "id": "call_list_sections",
                "name": "list_resume_sections",
                "args": {},
            }
        if "professional experiences" in normalized:
            return {
                "id": "call_list_experiences",
                "name": "list_section_points",
                "args": {"section": "experiences"},
            }
        if "first bullet point" in normalized and "first professional experience" in normalized:
            return {
                "id": "call_show_detail",
                "name": "show_section_item_detail",
                "args": {
                    "section": "experiences",
                    "item_index": 1,
                    "bullet_index": 1,
                },
            }
        if user_input.startswith("/ingest"):
            return {
                "id": "call_prepare_ingestion",
                "name": "prepare_resume_ingestion",
                "args": {"command_text": user_input},
            }
        if user_input.startswith(("http://", "https://", "file://")):
            return {
                "id": "call_prepare_ingestion",
                "name": "prepare_resume_ingestion",
                "args": {"source_uri": user_input},
            }
        if (
            len(user_input) >= 2
            and user_input[0] == user_input[-1]
            and user_input[0] in {"'", '"'}
        ):
            return {
                "id": "call_prepare_ingestion",
                "name": "prepare_resume_ingestion",
                "args": {"source_file_ref": user_input},
            }
        if "ingest my resume" in normalized or "load my resume" in normalized:
            return {
                "id": "call_prepare_ingestion",
                "name": "prepare_resume_ingestion",
                "args": {},
            }
        return {
            "id": "call_list_sections_default",
            "name": "list_resume_sections",
            "args": {},
        }

    @staticmethod
    def _latest_user_text(messages: list[BaseMessage]) -> str:
        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                return str(message.content)
        return ""
