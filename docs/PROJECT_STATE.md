# Project state

- **Project:** NPCU GenAI Intelligence Lab
- **Current gate:** Gate 3 — Metadata-Aware Embeddings and Semantic Retrieval — Accepted
- **Current implementation:** Foundation, page-aware ingestion, deterministic chunking, manifest
  enrichment, embeddings, vector indexing, and semantic retrieval accepted through Gate 3
- **Implemented external AI technologies:** OpenAI `text-embedding-3-small` and Pinecone Serverless

Gate 0 and Gate 1 were formally accepted on 2026-09-10. Gate 2 was formally accepted on
2026-09-12. Gate 3 started on 2026-09-12 after the owner approved an OpenAI embedding and Pinecone
vector-index stack for the synthetic-only corpus. Manifest validation, PDF-to-chunk enrichment,
embedding and vector-index boundaries, idempotent indexing, metadata-filtered retrieval, and
provider-independent results are implemented. The live OpenAI/Pinecone path passed and Gate 3 was
formally accepted on 2026-09-12.

Current deterministic evidence: 130 non-live tests pass over the 11-PDF, 81-page, 194-chunk corpus;
Ruff and installed-dependency health checks pass; editable-package imports resolve correctly. The
configured Pinecone namespace contains 194 vectors, all named current-policy retrieval questions
found their expected documents with page provenance, and explicit historical retrieval found both
Lending v4.0 and superseded v3.1.

Gate 4 has not started. The project is awaiting explicit Gate 4 initiation.

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
