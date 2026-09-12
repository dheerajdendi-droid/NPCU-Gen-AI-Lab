# Project state

- **Project:** NPCU GenAI Intelligence Lab
- **Current gate:** Gate 3 — Metadata-Aware Embeddings and Semantic Retrieval — In progress
- **Current implementation:** Gate 0–2 capabilities accepted; Gate 3 provider-independent path and
  provider adapters implemented locally, with live smoke verification pending
- **Implemented external AI technologies:** OpenAI `text-embedding-3-small` and Pinecone Serverless

Gate 0 and Gate 1 were formally accepted on 2026-09-10. Gate 2 was formally accepted on
2026-09-12. Gate 3 started on 2026-09-12 after the owner approved an OpenAI embedding and Pinecone
vector-index stack for the synthetic-only corpus. Manifest validation, PDF-to-chunk enrichment,
embedding and vector-index boundaries, idempotent indexing, metadata-filtered retrieval, and
provider-independent results are implemented. All deterministic verification passes. No live
provider call or Pinecone index creation occurred because the four live environment settings were
not available. Gate 3 is not accepted; the explicit live smoke test and owner review remain.

Current deterministic evidence: 130 non-live tests pass over the 11-PDF, 81-page, 194-chunk corpus;
Ruff and installed-dependency health checks pass; editable-package imports resolve correctly.

## Planned future capability areas

- RAG answer generation and citations
- Structured analytics
- Graph retrieval
- External retrieval
- Memory
- Orchestration
- Evaluation
- Voice

These are planned capability areas and have not been implemented.

## Estimated delivery

- **Core MVP:** approximately 10–16 weeks at three focused hours per day
- **Full planned demonstration:** approximately 22–34 weeks at three focused hours per day

These figures are planning estimates, not guarantees. They assume approximately 15–20 focused
hours per week and include learning, testing, debugging, documentation, and architectural review.
The core MVP is prioritised before optional extensions.
