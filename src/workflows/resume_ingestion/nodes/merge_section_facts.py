from src.workflows.resume_ingestion.state import ResumeIngestionState
from src.ingestion.resumes.merging import merge_facts
from src.ingestion.resumes.models import ExtractionWarning, ResumeFacts


def merge_section_facts(state: ResumeIngestionState) -> dict:
    facts = ResumeFacts()
    warnings: list[ExtractionWarning] = []
    for section in state.get("section_facts", []):
        merge_facts(facts, section)
        warnings.extend(section.warnings)
    return {"facts": facts, "warnings": warnings}
