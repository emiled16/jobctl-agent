from __future__ import annotations

from pathlib import Path

from src.workflows.resume_ingestion.graph import (
    build_resume_ingestion_graph,
    to_ingestion_result,
)
from src.ingestion.documents.models import DocumentSource
from src.ingestion.resumes.segmentation import segment_resume


def test_segment_resume_detects_common_sections() -> None:
    text = """Jane Doe
jane@example.com

SUMMARY
Builder of data tools.

EXPERIENCE
Acme - Senior Engineer
- Built ingestion pipelines.

SKILLS
Python, SQL
"""

    sections = segment_resume(text)

    assert [section.name for section in sections] == [
        "contact",
        "summary",
        "experience",
        "skills",
    ]


def test_resume_ingestion_graph_extracts_facts_from_uploaded_text(
    tmp_path: Path,
) -> None:
    resume = tmp_path / "resume.txt"
    resume.write_text(
        """Jane Doe
jane@example.com
https://github.com/janedoe

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
    graph = build_resume_ingestion_graph()

    state = graph.invoke(
        {
            "source": DocumentSource(
                kind="uploaded_file",
                file_ref=str(resume),
                filename="resume.txt",
                content_type="text/plain",
            )
        }
    )
    result = to_ingestion_result(state)

    assert state["status"] == "valid"
    assert result.facts.contact is not None
    assert result.facts.contact.emails == ["jane@example.com"]
    assert result.facts.experiences[0].organization == "Acme"
    assert result.facts.experiences[0].title == "Senior Engineer"
    assert result.facts.projects[0].name == "Resume Agent"
    assert {skill.name for skill in result.facts.skills} == {
        "LangGraph",
        "Python",
        "SQL",
    }


def test_resume_ingestion_graph_does_not_emit_refinement_or_graph_state(
    tmp_path: Path,
) -> None:
    resume = tmp_path / "resume.txt"
    resume.write_text("SKILLS\nPython", encoding="utf-8")
    graph = build_resume_ingestion_graph()

    state = graph.invoke(
        {
            "source": DocumentSource(
                kind="uploaded_file",
                file_ref=str(resume),
                filename="resume.txt",
                content_type="text/plain",
            )
        }
    )

    assert "clarification_questions" not in state
    assert "mutation_plan" not in state
    assert "candidate_matches" not in state
