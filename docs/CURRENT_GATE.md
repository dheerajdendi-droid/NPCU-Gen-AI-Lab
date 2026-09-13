# Gate 5.5 — Coursework Demonstration UI

Gate 5.5 was inserted on **2026-09-13** by CR-001 after Gate 5 acceptance and while Gate 6 remained
paused at its documentation-only design checkpoint. It brings forward a small coursework
presentation surface without renumbering accepted gates or claiming that structured analytics has
been implemented. Gate 6 will resume after this change is reviewed; Gate 7 has not started.

## Objective

Provide a minimal Streamlit interface over the accepted policy retrieval and grounded-answer path
so a coursework reviewer can ask a question, see the validated answer and authoritative citations,
observe the existing insufficient-evidence behavior, and inspect the exact retrieval evidence.

## In scope

- One Streamlit page titled **NPCU Policy Intelligence Assistant**.
- One policy-question input and Ask action.
- Grounded statement rendering using existing application answer models.
- Citation rendering using application-owned title, version, status, page, and filename metadata.
- A clearly visible insufficient-evidence result with no generic fallback answer.
- A collapsed retrieval-details panel containing real rank, similarity score, provenance, and a
  short source-text preview.
- Five example questions, including one intentionally unsupported question.
- Existing environment configuration and live OpenAI/Pinecone adapters.
- A query-only composition over the existing Pinecone index; the UI cannot create or upsert data.
- Focused offline tests of the presentation integration boundary.

## Architecture

The Streamlit module performs input handling and rendering only. `CourseworkDemoService` wraps the
accepted `GroundedAnswerService` with a recording retriever so the exact evidence already supplied
to generation can be shown for demonstration. It does not change ranking, filtering, prompting,
generation, grounding, citation validation, or fallback rules.

The live composition loads existing environment settings, confirms that the configured Pinecone
index exists, and supplies `PineconeVectorIndex` with a control and data surface that expose only
index description and query operations. A missing index fails clearly instead of being created.

```text
USER
  |
  v
STREAMLIT UI
  |
  v
COURSEWORK DEMO SERVICE
  |
  v
ACCEPTED GROUNDED ANSWER SERVICE
  |
  +--> SEMANTIC RETRIEVAL --> EXISTING PINECONE INDEX (QUERY ONLY)
  |
  +--> OPENAI GENERATION --> VALIDATED GROUNDED ANSWER
```

## User and data boundary

The interface states that the policies are synthetic and contain no real member data. Questions
and retrieved synthetic evidence are sent through the already accepted live provider path. API
keys, index names, namespaces, stack traces, complete prompts, and provider response objects are
not displayed.

## Errors

- Blank input produces a local warning and makes no service call.
- Application retrieval or generation errors produce one user-readable availability message.
- Unexpected exceptions produce a generic message while local logs retain developer diagnostics.
- A missing or incompatible index and missing settings fail through existing application errors.
- No exception detail, credential, or stack trace is rendered in the page.

## Verification

- Unit tests prove that the UI integration invokes the existing answer path once.
- Citation metadata and exact retrieval evidence are preserved.
- Empty retrieval retains the accepted insufficient-evidence result and bypasses generation.
- The Pinecone data wrapper exposes query but no upsert operation.
- The Streamlit module imports and the local application launches successfully.
- One current-policy question, one version-sensitive question, one cross-document question, and one
  unsupported question are inspected through the UI only when their provider calls are authorized.
- The complete deterministic suite and repository checks must remain passing.

Local verification on **2026-09-13** confirmed that the page launches, the synthetic-data notice and
five examples render, blank input remains local, and retrieval details are collapsed by default.
The complete deterministic suite passed **206 tests** with the three authorization-gated live tests
skipped; Ruff, dependency health, imports, and whitespace checks passed.

Four authorized questions were then submitted through the page. The current Join and Borrow limit
and minimum-score questions cited the current Lending and Affordability Policy v4.0 on page 4. The
payroll-failure question combined current Onboarding v2.2 page 6 and Credit Control v3.0 page 6.
The cryptocurrency question returned `INSUFFICIENT_EVIDENCE` without sources. The expanded
retrieval panel displayed application-owned rank, similarity score, version, status, page, and
source-text previews. These four checks issued query-only provider operations; no index creation or
vector mutation path was exposed.

## Out of scope

- Gate 6 structured analytics, Excel, DuckDB, or management-information dashboards
- Retrieval, chunking, embedding, prompt, or generation changes
- Hybrid search, lexical search, reranking, or threshold calibration
- Evaluation dashboards or hard-coded evaluation percentages
- Historical-mode controls beyond the accepted current-only default path
- APIs, custom JavaScript, elaborate CSS, authentication, user management, or persistence
- GraphRAG, Neo4j, external web retrieval, orchestration, agents, memory, or voice
- Deployment and the final NPCU product interface
- Gate 7 implementation

## Exit criteria

- [x] CR-001 records the reason, scope, constraints, and effect on Gate 6
- [x] The Gate 6 design checkpoint is preserved separately without implementation
- [x] Streamlit is the sole new runtime dependency
- [x] The UI reuses the accepted RAG services and contains no RAG business logic
- [x] Grounded answers, authoritative citations, and fallback status remain distinct
- [x] Retrieval details use only existing application evidence and scores
- [x] Live Pinecone composition cannot create, update, upsert, or delete remote data
- [x] Focused deterministic UI-boundary tests pass
- [x] The Streamlit application launches and is inspected locally
- [x] Authorized demonstration questions show expected answer, citation, version, and fallback behavior
- [x] The complete tests, Ruff, dependencies, imports, whitespace, credential, and scope checks pass
- [x] Documentation describes the implemented interface and exact launch command
- [x] One local implementation commit contains the Gate 5.5 change
- [x] Gate 5.5 remains pending owner review; Gate 6 implementation and Gate 7 have not started
