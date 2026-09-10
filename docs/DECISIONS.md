# Architecture decisions

## DEC-001 — Use Python 3.12

Python 3.12 is the supported language runtime, providing a modern, explicit baseline.

## DEC-002 — Use a src package layout

Application code lives under `src/` so tests exercise the installed package rather than relying on
the repository root being importable.

## DEC-003 — Keep domain models provider-independent

Core models represent application concepts and must not include fields or types belonging to a
vector database, model provider, or orchestration framework.

## DEC-004 — Do not use LangChain or LlamaIndex during foundational RAG-learning stages

**Reason:** The project is educational, and the underlying RAG mechanics should be understood
before framework abstractions are introduced.

## DEC-005 — Separate structured analytics from document retrieval

**Reason:** Numerical aggregation and calculation should be performed deterministically rather
than by vector retrieval or a language model.

## DEC-006 — Build a core MVP before optional advanced capabilities

**Reason:** A usable, evaluated document-RAG and structured-analytics system provides value sooner
and reduces the risk of spending months integrating technologies without a stable foundation.

## DEC-007 — Estimate delivery using focused hours rather than calendar optimism

**Reason:** The project includes learning, debugging, testing, documentation, and review—not only
implementation.

## DEC-008 — Use pypdf for Gate 1 born-digital PDF parsing

**Reason:** `pypdf` is a focused, pure-Python dependency that can extract text from digitally
generated PDFs without introducing an orchestration framework or provider-specific domain types.
OCR and parser interchangeability are deliberately deferred.
