from __future__ import annotations

from src.agents.orchestration_chat.tools.resume_ingestion import (
    source_from_ingest_command,
)
from src.agents.orchestration_chat.tools.resume_sections import (
    answer_from_resume_facts,
    format_section_choices,
    infer_section,
    render_resume_section,
    resolve_section_choice,
)
from src.agents.orchestration_chat.tools.router import (
    document_source_from_route,
    route_with_llm,
)
from src.llm.base import LLMProvider, Message, StructuredChatProvider
from src.workflows.orchestration.state import OrchestrationState


def run_orchestration_chat_agent(
    state: OrchestrationState,
    *,
    llm_provider: LLMProvider | None = None,
) -> dict:
    user_input = state.get("user_input", "").strip()
    messages = [*state.get("messages", []), Message(role="user", content=user_input)]

    if state.get("pending_user_action") == "choose_resume_section":
        return _handle_section_choice(state, messages, user_input)

    source = state.get("source")
    if user_input.startswith("/ingest"):
        source = source_from_ingest_command(user_input) or source
        if source is None:
            response = (
                "Please provide a resume file path or URI, for example: "
                "/ingest --file resume.txt"
            )
            return {
                "messages": [*messages, Message(role="assistant", content=response)],
                "intent": "ingest_resume",
                "response": response,
                "status": "needs_source",
                "next_node": "end",
            }
        return {
            "messages": messages,
            "intent": "ingest_resume",
            "source": source,
            "status": "ingesting",
            "next_node": "resume_ingestion",
        }

    if _asks_for_section_without_name(user_input):
        response = format_section_choices()
        return {
            "messages": [*messages, Message(role="assistant", content=response)],
            "intent": "show_resume_section",
            "pending_user_action": "choose_resume_section",
            "response": response,
            "next_node": "end",
        }

    facts_answer = answer_from_resume_facts(state.get("resume_facts"), user_input)
    if facts_answer:
        return {
            "messages": [*messages, Message(role="assistant", content=facts_answer)],
            "intent": "chat",
            "response": facts_answer,
            "next_node": "end",
        }

    if isinstance(llm_provider, StructuredChatProvider):
        routed = _run_llm_routing(state, messages, user_input, llm_provider)
        if routed is not None:
            return routed

    section, selector = infer_section(user_input)
    if section:
        response = render_resume_section(state.get("resume_facts"), section, selector)
        return {
            "messages": [*messages, Message(role="assistant", content=response)],
            "intent": "show_resume_section",
            "requested_section": section,
            "requested_selector": selector,
            "response": response,
            "next_node": "end",
        }

    response = _normal_chat_response(llm_provider, messages, bool(state.get("resume_facts")))
    return {
        "messages": [*messages, Message(role="assistant", content=response)],
        "intent": "chat",
        "response": response,
        "next_node": "end",
    }


def _handle_section_choice(
    state: OrchestrationState,
    messages: list[Message],
    user_input: str,
) -> dict:
    section = resolve_section_choice(user_input)
    if section:
        response = render_resume_section(state.get("resume_facts"), section)
        return {
            "messages": [*messages, Message(role="assistant", content=response)],
            "pending_user_action": None,
            "requested_section": section,
            "response": response,
            "next_node": "end",
            "status": state.get("status", "idle"),
        }
    response = format_section_choices()
    return {
        "messages": [*messages, Message(role="assistant", content=response)],
        "response": response,
        "next_node": "end",
    }


def _asks_for_section_without_name(user_input: str) -> bool:
    normalized = user_input.strip().lower()
    return normalized in {
        "print a section",
        "show a section",
        "display a section",
        "print section",
        "show section",
        "which sections can i print",
    }


def _normal_chat_response(
    llm_provider: LLMProvider | None,
    messages: list[Message],
    has_resume: bool,
) -> str:
    if llm_provider is not None:
        return llm_provider.chat(
            _with_chat_system_prompt(messages, has_resume),
            temperature=0.2,
        ).get("content", "")
    if has_resume:
        return "I can answer questions about the ingested resume facts or print a resume section."
    return "I can help with resume ingestion. Use /ingest with a file path or URI to start."


def _run_llm_routing(
    state: OrchestrationState,
    messages: list[Message],
    user_input: str,
    llm_provider: StructuredChatProvider,
) -> dict | None:
    route = route_with_llm(provider=llm_provider, user_input=user_input)
    if route.intent == "ingest_resume":
        source = document_source_from_route(route) or state.get("source")
        if source is None:
            response = (
                "Please provide a resume file path or URI, for example: "
                "/ingest --file resume.txt"
            )
            return {
                "messages": [*messages, Message(role="assistant", content=response)],
                "intent": "ingest_resume",
                "response": response,
                "status": "needs_source",
                "next_node": "end",
            }
        return {
            "messages": messages,
            "intent": "ingest_resume",
            "source": source,
            "status": "ingesting",
            "next_node": "resume_ingestion",
        }
    if route.intent == "show_resume_section":
        response = render_resume_section(
            state.get("resume_facts"),
            route.section,
            route.selector,
        )
        return {
            "messages": [*messages, Message(role="assistant", content=response)],
            "intent": "show_resume_section",
            "requested_section": route.section,
            "requested_selector": route.selector,
            "response": response,
            "next_node": "end",
        }
    return None


def _with_chat_system_prompt(
    messages: list[Message],
    has_resume: bool,
) -> list[Message]:
    resume_instruction = (
        "Resume facts are available. Answer questions using the extracted facts when "
        "the user asks about the resume. If a fact is unavailable, say that it was "
        "not found in the extracted resume facts."
        if has_resume
        else "No resume facts are available yet. If the user wants resume-specific "
        "help, ask them to ingest a resume first."
    )
    return [
        {
            "role": "system",
            "content": (
                "You are the Jobctl resume orchestration chat agent. Be concise. "
                "You can route resume ingestion requests to the ingestion graph, "
                "and you can help users inspect extracted resume facts. "
                f"{resume_instruction}"
            ),
        },
        *messages,
    ]
