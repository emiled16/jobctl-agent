# LangGraph Resume Ingestion & Knowledge Graph Pipeline

**Product & Engineering Specification**

---

## 1. Overview

This document specifies the architecture, data flow, and implementation strategy for a LangGraph-based application that:

* Interacts conversationally with a user
* Ingests resumes from a URI
* Extracts and normalizes structured experience data
* Iteratively refines that data with user input
* Converts the refined data into a knowledge graph representation
* Resolves semantic duplicates against an existing knowledge graph
* Executes safe and auditable graph mutations

This system is **stateful, interruptible, and human-in-the-loop**, leveraging LangGraph’s core primitives: **state, nodes, edges, conditional routing, and persistence**.

---

## 2. High-Level Architecture

The system is composed of:

### 2.1 Parent Graph (Conversation Orchestrator)

Responsible for:

* Intent detection
* Routing user input
* Managing workflow state
* Handling interruptions and resumptions

### 2.2 Subgraphs

#### A. Ingestion Subgraph

* Document retrieval
* Parsing
* Initial fact extraction
* Normalization

#### B. Clarification & Refinement Subgraph

* Ambiguity detection
* User interaction loop
* Data refinement and validation

#### C. Graph Resolution & Commit Subgraph

* Graph transformation
* Deduplication / entity resolution
* Mutation planning
* Execution

---

## 3. End-to-End Flow

```text
User Input
   ↓
Conversation Router
   ↓
[Resume Ingestion Intent?]
   ├── No → Standard Chat → END
   └── Yes
         ↓
   Collect Resume URI
         ↓
   Ingestion Subgraph
         ↓
   Clarification Subgraph (loop)
         ↓
   Graph Resolution Subgraph
         ↓
   [Approval Required?]
         ├── Yes → Ask User → Resume
         └── No
         ↓
   Execute Graph Mutations
         ↓
   Summary Response
         ↓
        END
```

---

## 4. State Design

### 4.1 Conversation State

```python
class ConversationState(TypedDict):
    messages: list
    thread_id: str
    active_workflow: str | None
    pending_user_action: str | None
    current_resume_uri: str | None
    workflow_status: str | None
    last_error: str | None
    current_subgraph_state_ref: str | None
```

---

### 4.2 Resume Ingestion State

```python
class ResumeIngestionState(TypedDict):
    resume_uri: str
    raw_document_bytes_ref: str | None
    raw_text: str | None
    parsed_sections: list[dict]
    extraction_candidates: list[dict]
    normalized_experiences: list[dict]
    ambiguities: list[dict]
    clarification_questions: list[dict]
    user_edits: list[dict]
    refined_experiences: list[dict]
    validation_errors: list[dict]
    provenance_map: dict
    ingestion_confidence: float
```

---

### 4.3 Graph Mutation State

```python
class GraphMutationState(TypedDict):
    refined_experiences: list[dict]
    proposed_nodes: list[dict]
    proposed_edges: list[dict]
    candidate_matches: list[dict]
    resolution_actions: list[dict]
    mutation_plan: list[dict]
    write_conflicts: list[dict]
    approval_required: bool
    commit_result: dict | None
```

---

## 5. Canonical Intermediate Schema

All resume data must be normalized into a structured format before graph mapping.

### Example:

```json
{
  "experience_id": "exp_001",
  "type": "employment",
  "organization": {
    "raw": "Google LLC",
    "normalized": "Google"
  },
  "role": {
    "raw": "Senior Software Engineer",
    "normalized": "Software Engineer"
  },
  "start_date": "2021-05",
  "end_date": "2024-02",
  "location": "Montreal, QC",
  "summary": "...",
  "achievement_bullets": [
    {
      "bullet_id": "b1",
      "raw_text": "...",
      "normalized_facts": [...]
    }
  ],
  "skills": ["Python", "Kubernetes"],
  "confidence": 0.86,
  "ambiguities": [],
  "provenance": {}
}
```

---

## 6. Parent Graph Nodes

| Node                     | Description                      |
| ------------------------ | -------------------------------- |
| `conversation_router`    | Classifies user intent           |
| `collect_resume_uri`     | Requests or validates URI        |
| `normal_chat`            | Default conversational handler   |
| `ask_user_clarification` | Presents clarification questions |
| `await_user_reply`       | Interrupt/resume point           |
| `ask_user_approval`      | Handles risky decisions          |
| `summarize_result`       | Outputs final result             |

---

## 7. Ingestion Subgraph

| Node                      | Description           |
| ------------------------- | --------------------- |
| `fetch_document`          | Download resume       |
| `detect_document_type`    | Identify format       |
| `parse_document`          | Extract raw text      |
| `clean_and_segment_text`  | Structure document    |
| `extract_candidate_facts` | Initial extraction    |
| `normalize_experiences`   | Map to schema         |
| `validate_extraction`     | Validate completeness |

---

## 8. Clarification & Refinement Subgraph

| Node                            | Description                 |
| ------------------------------- | --------------------------- |
| `identify_ambiguities`          | Detect missing/unclear data |
| `generate_refinement_proposals` | Suggest edits               |
| `decide_if_user_needed`         | Gate human involvement      |
| `apply_auto_refinements`        | Safe transformations        |
| `ask_clarification_questions`   | Ask user                    |
| `ingest_user_clarification`     | Parse responses             |
| `apply_user_edits`              | Apply updates               |
| `quality_gate`                  | Ensure readiness            |

### Loop Condition

Continue until:

* ambiguity count below threshold
* all required fields complete
* no redundant entries

---

## 9. Graph Resolution & Commit Subgraph

| Node                                  | Description            |
| ------------------------------------- | ---------------------- |
| `map_experiences_to_graph_primitives` | Transform to ontology  |
| `retrieve_similar_graph_entities`     | Graph-RAG retrieval    |
| `resolve_entities_and_experiences`    | Deduplication          |
| `build_mutation_plan`                 | Generate operations    |
| `approval_gate`                       | Optional user approval |
| `execute_graph_mutations`             | Write to KG            |
| `post_commit_audit`                   | Logging & provenance   |

---

## 10. Knowledge Graph Model

### Core Entities

* Person
* Organization
* Role
* Experience
* Skill
* Project
* Achievement
* DateRange
* Location

### Core Relationships

* WORKED_AT
* HELD_ROLE
* HAS_EXPERIENCE
* EXPERIENCE_AT
* EXPERIENCE_ROLE
* EXPERIENCE_DURING
* EXPERIENCE_USED_SKILL
* EXPERIENCE_INCLUDED_ACHIEVEMENT

---

## 11. Deduplication Strategy

### 11.1 Rule-Based Matching

* Exact name match
* Date overlap
* Role equivalence

### 11.2 Semantic Matching

* Embeddings similarity
* Skill overlap
* Achievement similarity

### 11.3 Graph-Aware Matching

* Shared neighbors
* Same organization context
* Timeline overlap

### 11.4 Decision Outcomes

* CREATE_NEW
* MERGE_EXISTING
* ATTACH_ALIAS
* SKIP_REDUNDANT
* ESCALATE_TO_HUMAN

---

## 12. Human-in-the-Loop Integration

### 12.1 Clarification Stage

Triggered when:

* Missing dates
* Ambiguous roles
* Complex bullet points

### 12.2 Resolution Stage

Triggered when:

* Potential duplicate entities
* Conflicting knowledge
* Medium-confidence matches

---

## 13. Persistence & Memory

### Short-Term (Thread State)

* Active workflow
* Pending clarifications
* Current resume state

### Long-Term

* Ontology rules
* Alias mappings
* Historical merge decisions

### External System

* Knowledge Graph (source of truth)

---

## 14. Failure Handling

| Scenario                  | Handling               |
| ------------------------- | ---------------------- |
| URI invalid               | Request new input      |
| Unsupported format        | Ask alternative        |
| Parsing failure           | Retry / fallback       |
| Low extraction confidence | Increase clarification |
| User abandons             | Persist + timeout      |
| Graph conflict            | Escalate               |
| Write failure             | Retry / rollback       |

---

## 15. MVP Scope (Phase 1)

* Resume ingestion from URI
* Basic parsing & extraction
* Canonical schema normalization
* Clarification loop
* Graph write (no advanced dedup)
* Exact duplicate avoidance only

---

## 16. Phase 2 Enhancements

* Semantic deduplication
* Entity resolution engine
* Approval workflows
* Provenance tracking

---

## 17. Phase 3 Enhancements

* Graph-aware ranking
* Learned resolution policies
* Ontology expansion
* Advanced analytics & replay tooling

---

## 18. Key Design Principles

1. **Never write directly from extraction to graph**
2. **Always normalize before refinement**
3. **Separate transformation from resolution**
4. **Use human-in-the-loop selectively**
5. **Treat graph updates as planned mutations**
6. **Persist everything for replay/debugging**

---

## 19. Implementation Notes

* Use LangGraph `StateGraph` for all workflows
* Enable checkpoint persistence from day one
* Use subgraphs for modularity
* Strong typing for all state objects
* Keep ontology stable and versioned
* Maintain full provenance for every graph write

---

## 20. Deliverables

Engineering should implement:

* Parent orchestration graph
* Three subgraphs (Ingestion, Refinement, Graph Resolution)
* Canonical schema layer
* Graph mutation engine
* Deduplication pipeline (progressive)
* Persistence layer
* Human-in-the-loop interfaces

---

## 21. Summary

This system is a **stateful, multi-stage, human-assisted knowledge extraction and graph construction pipeline**.

LangGraph is used because:

* workflows are non-linear
* require loops and branching
* must pause for human input
* require durable state and resumability

The design ensures:

* high data quality
* auditability
* minimal duplication
* scalable graph enrichment

---
