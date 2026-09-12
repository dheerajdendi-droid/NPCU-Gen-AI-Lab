# Architecture

This document describes the intended architecture, the capabilities accepted through Gate 4, and
the Gate 5 evaluation capability implemented pending owner review and live verification.
The foundation, page-aware PDF parsing, and deterministic page-bounded chunk construction are
accepted through Gate 2. Gate 3 metadata-aware semantic retrieval is implemented and accepted
after live OpenAI and Pinecone verification. Gate 4 grounded generation is accepted after offline
verification, a focused six-scenario live test, and owner review. Gate 5 adds a local evaluation
boundary without changing retrieval or generation. Later capabilities remain plans; Gate 6 has not
started.

## Capability boundaries

1. **Ingestion** accepts source material and produces clean, traceable document representations.
   Gate 1 implements born-digital PDF text extraction as one validated result per source page.
   Gate 2 transforms those pages into deterministic word-window chunks without crossing page
   boundaries. Cleaning, OCR, layout reconstruction, and table extraction remain deferred.
2. **Retrieval** finds relevant document evidence. Gate 3 implements one embedding boundary and one
   vector-index boundary: OpenAI text-embedding-3-small produces explicit 1,536-dimensional
   vectors, and Pinecone Serverless stores and queries dense vectors with cosine similarity.
3. **Analytics** answers structured-data questions through deterministic queries and calculations.
4. **Graph** represents and traverses relationships that are awkward to express as document
   similarity or tabular aggregation.
5. **Orchestration** coordinates capabilities and selects the appropriate execution path.
6. **Generation** produces grounded, user-facing responses from supplied evidence. Gate 4 adds one
   provider-independent generation boundary, an OpenAI Responses adapter, application-side citation
   validation, and deterministic rendering.
7. **Evaluation** measures retrieval, grounding, answer quality, and system behavior.
   Gate 5 keeps a protected synthetic case dataset outside ingestion, scores retrieval and grounded
   answers separately, records distinct human review, and emits provider-independent reports and
   fingerprints.

The application domain sits inside these boundaries and does not depend on provider response
types. OpenAI and Pinecone adapters map SDK objects to application-owned vectors, records, matches,
and retrieval results. Deterministic test doubles exercise those boundaries without network access.

## Gate 3 corpus-to-query flow

1. The strict manifest loader validates one metadata row for every PDF under data/raw/policies.
2. The existing ingestion boundary parses PDFs into one-based DocumentPage values.
3. The existing chunker produces page-bounded deterministic Chunk values and IDs.
4. CorpusChunk associates each chunk with title, version, status, effective date, owner, source
   filename, and synthetic provenance without flattening source pages.
5. The embedding boundary maps chunk text to fixed-size vectors.
6. Provider-independent VectorRecord values use Gate 2 chunk IDs as idempotent upsert IDs.
7. The vector-index boundary stores and queries one environment-configured Pinecone namespace.
8. The retrieval service maps matches to ranked RetrievalResult evidence with complete provenance.

The pre-existing foundation Document model remains available, but it is not used to flatten the
Gate 3 corpus. CorpusDocument and CorpusChunk make manifest and page provenance explicit.

Normal retrieval filters provider metadata to CURRENT. Explicit historical retrieval omits that
filter, allowing current Lending Policy v4.0 and superseded v3.1 to coexist in the same namespace.
The index is derived, rebuildable state. Repeated identical indexing uses upsert and does not create
new IDs; stale-record deletion is not implemented in Gate 3.

The live configuration is fixed to dense vectors, 1,536 dimensions, cosine similarity, AWS, and
us-east-1. Only index name and namespace are environment-configured. This deployment is approved
for synthetic data only and must be reconsidered before real organisational, employee, or member
data is processed.

## Retrieval and analytics are distinct

Document retrieval is suited to locating passages by meaning or wording. Structured analytics is
suited to exact filters, joins, aggregations, and calculations over typed data. Numerical answers
must be calculated deterministically rather than inferred from semantically similar passages or
delegated to a language model. Orchestration may eventually route a request to either capability,
but it should not blur their responsibilities.

## High-level delivery sequence

1. Foundation
2. Document ingestion and parsing
3. Deterministic page-aware chunking
4. Metadata-aware embeddings and semantic retrieval
5. Grounded generation and citations
6. Retrieval and answer evaluation
7. Structured analytics
8. Graph capabilities
9. Orchestration, external retrieval, memory, voice, and deployment polish

The core MVP—document RAG, structured analytics, citations, evaluation, and a usable
interface—should be completed and stabilised before optional extensions such as graph retrieval,
memory, voice, and provider-comparison experiments are added.

Gate 2's chunk_index remains an application-level ordering value. Gate 3 separately introduces
vector records and the managed provider index; neither changes the stable Gate 2 chunk contract.

## Gate 4 question-to-answer flow

1. GroundedAnswerService validates and normalizes one nonblank question.
2. The existing Gate 3 service retrieves ten ranked chunks, applying the CURRENT filter unless the
   caller explicitly requests historical evidence.
3. The generation prompt serializes those exact results deterministically by retrieval rank and
   labels their text as untrusted data.
4. The provider-independent generation boundary receives the question and evidence. Its OpenAI
   adapter calls `gpt-5.6-terra` through Responses Structured Outputs with low reasoning effort,
   `store=false`, and no tools.
5. The adapter returns only an application-owned draft containing status, statements, cited chunk
   IDs, optional abstention explanation, and provider-independent token counts.
6. The application rejects IDs outside the exact evidence set and invalid status/content
   combinations. It never accepts model-authored titles, versions, filenames, statuses, or pages.
7. Citations are built from RetrievalResult provenance, de-duplicated by first use, numbered
   deterministically, and rendered with a visible SUPERSEDED label where applicable.
8. Empty retrieval bypasses generation. Otherwise a validated model abstention returns an explicit
   insufficient-evidence result with no answer statements or citations.

This is a single-turn application service, not a general orchestrator. The prompt-injection boundary
is explicit: retrieved text is passed as untrusted reference data and can never directly supply
authoritative citation metadata. Semantic compliance with instructions still depends on model
behavior, while application validation constrains every accepted statement to retrieved chunk IDs.

## Gate 5 evaluation flow

1. The protected loader reads strict JSON only from `data/_evaluation_do_not_index` and validates
   every case against the canonical CorpusBuild document IDs, statuses and populated pages.
2. One evaluator call sends the case question through the accepted GroundedAnswerService. A small
   recording retriever captures the exact single retrieval used for generation.
3. Retrieval scoring measures document hits at fixed depths, reciprocal rank, distinct-document
   recall, page evidence and explicit document/status/duplicate/rank violations.
4. Answer scoring separately compares result status and citations with the case expectations and
   exact recorded evidence. Application-owned provenance remains authoritative.
5. Aggregate scores sum numerators and denominators. Zero denominators remain null and render as
   `N/A` rather than becoming misleading scores.
6. The report retains provider-independent evidence identities, answers, token usage, latency and
   safe failures. Human 0–2 ratings and disposition remain separate.
7. Canonical JSON produces stable dataset, corpus and public-configuration SHA-256 fingerprints.
8. Offline fakes exercise the complete path. The marked live test may query the accepted Pinecone
   namespace and OpenAI only after `--run-live` and direct authorization; its Pinecone surface has
   no mutation method.

Evaluation questions and reference facts are not corpus documents. They are never parsed, chunked,
indexed or supplied as answer evidence. Gate 5 establishes a small synthetic baseline and does not
claim production accuracy or tune the accepted system.
