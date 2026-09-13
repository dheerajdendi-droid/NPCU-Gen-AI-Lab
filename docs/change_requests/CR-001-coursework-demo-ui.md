# CR-001 — Coursework Demonstration UI

## Change request

- **ID:** CR-001
- **Title:** Coursework Demonstration UI
- **Requested after:** Gate 5 acceptance, while Gate 6 remains paused at design checkpoint
- **Priority:** High for coursework submission
- **Impact on long-term architecture:** Low

## Reason

The original roadmap planned a user interface later. The coursework benefits from a clear live
demonstration of the accepted policy RAG capability before structured analytics is implemented.
Gate 5.5 therefore inserts a small presentation layer without renumbering accepted gates or
claiming that Gate 6 analytics is complete.

## Scope

Add a lightweight Streamlit presentation layer over the existing retrieval and grounded-answer
services. It accepts one policy question, displays the validated answer and authoritative sources,
shows the existing insufficient-evidence outcome, and optionally exposes the exact retrieved
evidence used by the answer path.

## Constraints

- The UI calls the accepted application services and contains no retrieval or generation logic.
- Live composition opens the existing Pinecone index through a query-only surface.
- All displayed document provenance comes from application-owned answer and retrieval models.
- The interface uses synthetic policies only and clearly says so.

## Non-goals

This is not the final NPCU interface. Structured analytics, DuckDB, dashboards, GraphRAG, Neo4j,
external retrieval, orchestration, memory, voice, authentication, persistence, deployment, custom
JavaScript, and production frontend work remain outside CR-001.

## Effect on Gate 6

Gate 6 remains paused before implementation. Its approved/proposed workbook, metric, dependency,
and test design is preserved as a separate checkpoint and will resume only after Gate 5.5 review.
