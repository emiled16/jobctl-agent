from __future__ import annotations

from typing import Any

from langchain.agents import AgentState, create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from src.agents.chat_agent.context import ChatAgentContext
from src.agents.chat_agent.ingestion_request import source_from_ingestion_request
from src.agents.chat_agent.prompts import build_system_prompt
from src.agents.chat_agent.result import ChatAgentResult
from src.agents.chat_agent.tools import make_chat_agent_tools
from src.llm.messages import Message


def run_chat_agent(
    context: ChatAgentContext,
    *,
    model: BaseChatModel | None = None,
) -> ChatAgentResult:
    if model is None:
        raise ValueError("The chat agent requires a configured chat model.")

    user_input = context.get("user_input", "").strip()
    messages = [*to_langchain_messages(context.get("messages", []))]
    messages.append(HumanMessage(content=user_input))

    agent = create_agent(
        model=model,
        tools=make_chat_agent_tools(context),
        system_prompt=build_system_prompt(context),
        state_schema=AgentState,
    )
    result = agent.invoke({"messages": messages})
    return result_from_invoke_output(result)


def result_from_invoke_output(result: dict[str, Any]) -> ChatAgentResult:
    tool_call = last_tool_call(result.get("messages", []))
    if tool_call is None:
        return {
            "kind": "chat",
            "response": last_ai_text(result.get("messages", [])),
        }

    tool_name = str(tool_call.get("name", ""))
    tool_args = tool_call.get("args", {})
    tool_response = last_tool_response(result.get("messages", []), tool_call.get("id"))
    if tool_name == "prepare_resume_ingestion":
        source = source_from_ingestion_request(**tool_args)
        if source is None:
            return {
                "kind": "awaiting_resume_source",
                "response": tool_response
                or "Please provide the resume URI or local file path you want to ingest.",
            }
        return {
            "kind": "ingest_resume",
            "source": source,
            "response": tool_response or "Starting resume ingestion.",
        }
    if tool_name in {
        "list_resume_sections",
        "list_section_points",
        "show_section_item_detail",
    }:
        return {
            "kind": "inspect_resume",
            "response": tool_response or last_ai_text(result.get("messages", [])),
        }
    return {
        "kind": "chat",
        "response": last_ai_text(result.get("messages", [])),
    }


def last_tool_call(messages: list[BaseMessage]) -> dict[str, Any] | None:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            tool_calls = getattr(message, "tool_calls", None) or []
            if tool_calls:
                return tool_calls[-1]
    return None


def last_tool_response(
    messages: list[BaseMessage],
    tool_call_id: str | None,
) -> str:
    if tool_call_id:
        for message in reversed(messages):
            if isinstance(message, ToolMessage) and message.tool_call_id == tool_call_id:
                return str(message.content)
    for message in reversed(messages):
        if isinstance(message, ToolMessage):
            return str(message.content)
    return ""


def last_ai_text(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and isinstance(message.content, str):
            return message.content
    return "I could not complete that request."


def to_langchain_messages(messages: list[Message]) -> list[BaseMessage]:
    converted: list[BaseMessage] = []
    for message in messages:
        role = message.get("role")
        content = message.get("content", "")
        if role == "user":
            converted.append(HumanMessage(content=content))
        elif role == "assistant":
            converted.append(AIMessage(content=content))
    return converted
