# Bugs

## [2026-04-23] B-001: Inspection helpers mismatched the current ResumeFacts schema
- Plan: v1.0
- Status: Fixed
- Severity: Medium
- Description: The new `src/agents/chat_agent/inspection.py` module initially assumed fields such as `contact.full_name`, `contact.locations`, and `experience.highlights`, which do not exist in the current resume fact models.
- Reproduction: Run `pytest tests/unit/test_chat_agent.py tests/unit/test_orchestration.py`.
- Root cause: The refactor copied renderer behavior without first reconciling it with `src/ingestion/resumes/models.py`.
- Fix: Updated the inspection helpers to use `person.full_name`, `contact.location`, `contact.links`, `experience.bullets`, `project.bullets`, and `education.credential`.
- Verification: `pytest tests/unit/test_chat_agent.py tests/unit/test_orchestration.py`
