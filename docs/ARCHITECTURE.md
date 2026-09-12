# Architecture

This document describes the intended architecture. The foundation, page-aware PDF parsing, and
deterministic page-bounded chunk construction are complete and accepted through Gate 2. The
project is awaiting Gate 3 initiation; all later capabilities remain plans.

## Capability boundaries

1. **Ingestion** accepts source material and produces clean, traceable document representations.
   Gate 1 implements born-digital PDF text extraction as one validated result per source page.
   Gate 2 transforms those pages into deterministic word-window chunks without crossing page
   boundaries. Cleaning, OCR, layout reconstruction, and table extraction remain deferred.
2. **Retrieval** finds relevant document evidence through independently replaceable strategies.
3. **Analytics** answers structured-data questions through deterministic queries and calculations.
4. **Graph** represents and traverses relationships that are awkward to express as document
   similarity or tabular aggregation.
5. **Orchestration** coordinates capabilities and selects the appropriate execution path.
6. **Generation** produces grounded, user-facing responses from supplied evidence or results.
7. **Evaluation** measures retrieval, grounding, answer quality, and system behavior.

The application domain sits inside these boundaries and does not depend on a storage, retrieval,
model, or orchestration provider. Provider-specific adapters will be introduced only when the
relevant gate requires them.

## Retrieval and analytics are distinct

Document retrieval is suited to locating passages by meaning or wording. Structured analytics is
suited to exact filters, joins, aggregations, and calculations over typed data. Numerical answers
must be calculated deterministically rather than inferred from semantically similar passages or
delegated to a language model. Orchestration may eventually route a request to either capability,
but it should not blur their responsibilities.

## High-level delivery sequence

1. Foundation
2. Document ingestion and parsing
3. Chunking and indexing
4. Retrieval and grounded generation
5. Evaluation and citations
6. Structured analytics
7. Graph capabilities
8. Orchestration and external retrieval
9. Memory, voice, and deployment polish

The core MVP—document RAG, structured analytics, citations, evaluation, and a usable
interface—should be completed and stabilised before optional extensions such as graph retrieval,
memory, voice, and provider-comparison experiments are added.

Gate 2's “indexing” is limited to deterministic application-level `chunk_index` values. It does
not create a vector, search, or provider index.
