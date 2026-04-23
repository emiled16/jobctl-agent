from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.messages import ToolMessage as LangChainToolMessage

from src.agents.orchestration_chat.state import JobctlAgentState
from src.agents.orchestration_chat.tools.langchain_actions import (
    action_payload_from_tool_content,
)
from src.agents.orchestration_chat.tools.langchain_tools import (
    make_orchestration_tools,
)
from src.llm.messages import Message
from src.workflows.orchestration.state import OrchestrationState


def run_langchain_orchestration_chat_agent(
    state: OrchestrationState,
    *,
    model: BaseChatModel | None = None,
) -> dict:
    if model is None:
        raise ValueError("The orchestration chat agent requires a configured chat model.")

    messages = [*_to_langchain_messages(state.get("messages", []))]
    user_input = state.get("user_input", "").strip()
    messages.append(HumanMessage(content=user_input))
    conversation_messages = [
        *state.get("messages", []),
        {"role": "user", "content": user_input},
    ]

    agent = create_agent(
        model=model,
        tools=make_orchestration_tools(state),
        system_prompt=_system_prompt(state),
        state_schema=JobctlAgentState,
    )
    result = agent.invoke({"messages": messages})
    action = _extract_action(result)
    return _state_update_from_action(
        action,
        messages=conversation_messages,
        fallback_response=_last_ai_text(result.get("messages", [])),
    )


def _state_update_from_action(
    action: dict[str, Any] | None,
    *,
    messages: list[Message],
    fallback_response: str,
) -> dict:
    response = action.get("response", fallback_response) if action else fallback_response
    transcript = [*messages, {"role": "assistant", "content": response}]

    if action is None:
        return {
            "messages": transcript,
            "intent": "chat",
            "response": response,
            "next_node": "end",
        }

    kind = action.get("kind")
    if kind == "ingest_resume":
        return {
            "messages": transcript,
            "intent": "ingest_resume",
            "source": action.get("source"),
            "pending_user_action": None,
            "status": "ingesting",
            "response": response,
            "next_node": "resume_ingestion",
        }
    if kind == "needs_source":
        return {
            "messages": transcript,
            "intent": "ingest_resume",
            "pending_user_action": "provide_resume_source",
            "response": response,
            "status": "needs_source",
            "next_node": "end",
        }
    if kind == "inspect_resume":
        return {
            "messages": transcript,
            "intent": "inspect_resume",
            "response": response,
            "next_node": "end",
        }
    return {
        "messages": transcript,
        "intent": "chat",
        "response": response,
        "next_node": "end",
    }


def _extract_action(result: dict[str, Any]) -> dict[str, Any] | None:
    action = result.get("jobctl_action")
    if action:
        return _restore_action(action)
    for message in reversed(result.get("messages", [])):
        if isinstance(message, LangChainToolMessage):
            payload = action_payload_from_tool_content(str(message.content))
            if payload:
                return _restore_action(payload)
    return None


def _restore_action(action: dict[str, Any]) -> dict[str, Any]:
    if isinstance(action.get("source"), dict):
        from src.ingestion.documents.models import DocumentSource

        action = {**action, "source": DocumentSource(**action["source"])}
    return action


def _last_ai_text(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and isinstance(message.content, str):
            return message.content
    return "I could not complete that request."


def _to_langchain_messages(messages: list[Message]) -> list[BaseMessage]:
    converted: list[BaseMessage] = []
    for message in messages:
        role = message.get("role")
        content = message.get("content", "")
        if role == "user":
            converted.append(HumanMessage(content=content))
        elif role == "assistant":
            converted.append(AIMessage(content=content))
    return converted


def _system_prompt(state: OrchestrationState) -> str:
    has_resume = bool(state.get("resume_facts"))
    pending_user_action = state.get("pending_user_action")
    resume_instruction = (
        "A resume is currently ingested. For questions about what is stored, use the "
        "resume inspection tools instead of answering from memory. Use list_resume_sections "
        "to summarize what is available, list_section_points to enumerate items in a "
        "section, and show_section_item_detail to show one item or one bullet."
        if has_resume
        else "No resume is currently ingested. If the user asks to ingest, load, upload, "
        "or parse a resume, use prepare_resume_ingestion."
    )
    pending_instruction = (
        "You are waiting for the user to provide a resume URI or local file path. "
        "If the latest user message contains one, call prepare_resume_ingestion with "
        "that value. Otherwise ask for the resume URI or local file path again."
        if pending_user_action == "provide_resume_source"
        else "If the user asks to ingest a resume but does not give a URI or file path, "
        "call prepare_resume_ingestion without a source so the system can prompt for it. "
        "Treat /ingest as an ingestion request."
    )
    return (
        "You are the Jobctl resume orchestration chat agent. Be concise. "
        "You can do two jobs: initiate resume ingestion and inspect the currently "
        "ingested resume. "
        f"{resume_instruction} {pending_instruction}"
    )
