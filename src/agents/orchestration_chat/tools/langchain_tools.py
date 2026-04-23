from __future__ import annotations

from langchain.tools import tool

from src.agents.orchestration_chat.tools.langchain_actions import (
    action_from_ingestion_request,
    encode_action,
    inspect_resume_action,
)
from src.agents.orchestration_chat.tools.resume_inspection import (
    list_resume_sections as render_resume_sections,
    list_section_points as render_section_points,
    show_section_item_detail as render_section_item_detail,
)
from src.workflows.orchestration.state import OrchestrationState


def make_orchestration_tools(state: OrchestrationState):
    resume_facts = state.get("resume_facts")

    @tool
    def prepare_resume_ingestion(
        source_file_ref: str | None = None,
        source_uri: str | None = None,
        command_text: str | None = None,
    ) -> str:
        """Prepare resume ingestion from a local file path, URI, or raw /ingest command."""
        return encode_action(
            action_from_ingestion_request(
                source_file_ref=source_file_ref,
                source_uri=source_uri,
                command_text=command_text,
            )
        )

    @tool
    def list_resume_sections() -> str:
        """List the ingested resume sections and how many items are in each section."""
        return encode_action(inspect_resume_action(render_resume_sections(resume_facts)))

    @tool
    def list_section_points(section: str) -> str:
        """List the numbered items currently ingested for a given resume section."""
        return encode_action(
            inspect_resume_action(render_section_points(resume_facts, section))
        )

    @tool
    def show_section_item_detail(
        section: str,
        item_index: int | None = None,
        bullet_index: int | None = None,
    ) -> str:
        """Show the detail for a specific section item, optionally narrowed to one bullet."""
        return encode_action(
            inspect_resume_action(
                render_section_item_detail(
                    resume_facts,
                    section,
                    item_index,
                    bullet_index,
                )
            )
        )

    return [
        prepare_resume_ingestion,
        list_resume_sections,
        list_section_points,
        show_section_item_detail,
    ]
