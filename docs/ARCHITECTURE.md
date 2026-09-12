# Architecture

This document describes the intended architecture and the capabilities implemented through Gate 3.
The foundation, page-aware PDF parsing, and deterministic page-bounded chunk construction are
accepted through Gate 2. Gate 3 metadata-aware semantic retrieval is implemented locally and
awaiting live-provider verification and formal owner acceptance. All later capabilities remain
plans.

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
6. **Generation** produces grounded, user-facing responses from supplied evidence or results.
7. **Evaluation** measures retrieval, grounding, answer quality, and system behavior.

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
