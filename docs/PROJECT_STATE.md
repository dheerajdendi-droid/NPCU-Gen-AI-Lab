# Project state

- **Project:** NPCU GenAI Intelligence Lab
- **Current gate:** Gate 4 — Grounded Answer Generation and Page Citations — Deterministic
  implementation complete, pending live verification and owner review
- **Current implementation:** Capabilities accepted through Gate 3 plus provider-independent grounded
  generation, Structured Outputs mapping, evidence validation, and deterministic page citations
- **Implemented external AI technologies:** OpenAI `text-embedding-3-small`, Pinecone Serverless, and
  an OpenAI `gpt-5.6-terra` Responses adapter awaiting live execution

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

Gate 4 started on 2026-09-12. Its deterministic implementation passes 169 non-live tests, including
one complete offline grounded-answer integration test. The approved OpenAI generation path uses
`gpt-5.6-terra`, Responses Structured Outputs, low reasoning effort, disabled response storage, and
no tools. Answer citations are validated and built from exact Gate 3 evidence, current policy is the
default, historical retrieval is explicit, and empty evidence bypasses generation.

The focused live Gate 4 test is implemented but has not run. The execution safety layer rejected the
attempt because permission to disclose repository-derived synthetic evidence to external providers
was contained in an attached brief rather than a direct active-message approval. No Gate 4 OpenAI
generation request was made and Pinecone was not changed. Gate 4 is not formally accepted and remains
pending direct live-test authorization and owner review. Gate 5 has not started.

## Planned future capability areas

- Retrieval and answer evaluation
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
