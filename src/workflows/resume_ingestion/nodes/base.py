from collections.abc import Callable

from src.workflows.resume_ingestion.state import ResumeIngestionState

GraphNode = Callable[[ResumeIngestionState], dict]
