from __future__ import annotations

from src.agents.chat_agent.context import ChatAgentContext


def build_system_prompt(context: ChatAgentContext) -> str:
    has_resume = bool(context.get("resume_facts"))
    awaiting_resume_source = context.get("awaiting_resume_source", False)
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
        if awaiting_resume_source
        else "If the user asks to ingest a resume but does not give a URI or file path, "
        "call prepare_resume_ingestion without a source so the system can prompt for it. "
        "Treat /ingest as an ingestion request."
    )
    return (
        "You are the Jobctl chat agent. Be concise. "
        "You can do two jobs: initiate resume ingestion and inspect the currently "
        "ingested resume. "
        f"{resume_instruction} {pending_instruction}"
    )
