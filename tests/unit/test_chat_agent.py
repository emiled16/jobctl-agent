from __future__ import annotations

from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from src.agents.chat_agent.context import ChatAgentContext
from src.agents.chat_agent.runner import run_chat_agent
from src.ingestion.resumes.models import ResumeFacts
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


def test_chat_agent_returns_ingestion_request_for_ingest_command() -> None:
    result = run_chat_agent(
        ChatAgentContext(user_input="/ingest --file resume.txt"),
        model=FakeChatAgentModel(),
    )

    assert result["kind"] == "ingest_resume"
    assert result["source"].file_ref == "resume.txt"
    assert "Starting resume ingestion" in result["response"]


def test_chat_agent_requests_source_when_ingestion_has_no_source() -> None:
    result = run_chat_agent(
        ChatAgentContext(user_input="/ingest"),
        model=FakeChatAgentModel(),
    )

    assert result["kind"] == "awaiting_resume_source"
    assert "Please provide the resume URI or local file path" in result["response"]


def test_chat_agent_returns_inspection_result() -> None:
    facts = ResumeFacts(
        summary="Builder of data tools.",
        experiences=[],
        education=[],
        projects=[],
        certifications=[],
        skills=[],
        languages=[],
        contact=None,
    )
    result = run_chat_agent(
        ChatAgentContext(
            user_input="what sections are currently ingested?",
            resume_facts=facts,
        ),
        model=FakeChatAgentModel(),
    )

    assert result["kind"] == "inspect_resume"
    assert "Ingested resume sections:" in result["response"]


def test_chat_agent_can_resume_ingestion_when_workflow_is_awaiting_source(
    tmp_path: Path,
) -> None:
    resume = tmp_path / "resume.txt"
    _write_resume(resume)

    state = run_orchestration_turn(
        user_input="please ingest my resume",
        chat_model=FakeChatAgentModel(),
        ingestion_provider=None,
    )
    assert state["interaction_state"] == "awaiting_resume_source"

    state = run_orchestration_turn(
        user_input=resume.as_uri(),
        state=state,
        chat_model=FakeChatAgentModel(),
        ingestion_provider=None,
    )

    assert state["status"] == "ready"
    assert state["interaction_state"] is None
    assert state["resume_facts"] is not None


class FakeChatAgentModel(BaseChatModel):
    calls: int = 0

    @property
    def _llm_type(self) -> str:
        return "fake-chat-agent-model"

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
