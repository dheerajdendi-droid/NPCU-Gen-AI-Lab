# ADR 0004: Metadata-aware semantic retrieval

## Status

Accepted for Gate 3 implementation on 2026-09-12. Gate 3 itself remains pending formal owner
acceptance.

## Context

Gate 3 introduces the project's first external AI and vector-storage providers. It must make the
embedding, record construction, metadata filtering, and result mapping mechanics visible without
allowing provider SDK types to become application contracts. The canonical corpus deliberately
contains both current Lending Policy v4.0 and superseded v3.1, so retrieval must distinguish them.

The project owner approved managed services for synthetic-only data and acknowledged that the
Pinecone Builder plan is restricted to AWS `us-east-1`. This decision must be revisited before any
real organisational, employee, or member data is processed.

## Decision

Use OpenAI `text-embedding-3-small` with an explicit 1,536-dimensional output behind an embedding
boundary. Use one Pinecone Serverless dense index with 1,536 dimensions, cosine similarity, AWS
cloud, and `us-east-1` region behind a separate vector-index boundary. Require environment-driven
index name and namespace. Read `OPENAI_API_KEY` and `PINECONE_API_KEY` only from environment
settings and never log or persist them.

The application layer owns embedding vectors, vector records, scored matches, retrieval results,
and error types. OpenAI and Pinecone SDK request/response objects remain within their adapters.
Normal tests use deterministic doubles; only an explicitly marked smoke test may call the real
providers, and it skips unless all live configuration is available.

Load metadata from `data/corpus_manifest.csv` and content only from matching PDFs in
`data/raw/policies`. Derive `document_id` from each PDF filename stem. Require unique filenames
and document IDs and an exact one-to-one set match between manifest rows and PDFs. Parse effective
dates using `%d %B %Y`; accept only `CURRENT` or `SUPERSEDED`, and require the synthetic marker
to be `YES`.

For each existing deterministic Gate 2 chunk ID, upsert one Pinecone record containing its vector
and primitive metadata: document ID, text, one-based page number, title, version, status, effective
date as ISO text, owner, source filename, and synthetic boolean. Identical input therefore targets
the same record IDs. Corpus construction uses the accepted Gate 2 baseline of max_words=300 and
overlap_words=50. The lab index is derived and rebuildable, so it is created with deletion
protection disabled; Gate 3 does not reconcile records that disappear from later source input.

Queries are embedded with the same model and dimensions. Retrieval applies a `CURRENT` metadata
filter by default. Explicit inclusion of superseded content omits that filter. Provider matches are
mapped to provider-independent ranked evidence. Scores use Pinecone's cosine-similarity semantics,
where higher is more similar; equal scores are ordered by chunk ID where application ordering is
controllable.

Before creating or using a live index, validate the approved configuration exactly: dense vector
type, 1,536 dimensions, cosine metric, AWS cloud, `us-east-1` region, configured index name, and
configured namespace. An incompatible existing index fails clearly instead of being modified.

## Alternatives considered

- Local `sentence-transformers/all-MiniLM-L6-v2` with local Qdrant would keep data and computation
  local and avoid service credentials, but adds heavier model/runtime dependencies and does not
  teach the approved managed-service operations.
- Pinecone integrated embedding was rejected because it would hide the separate embedding request
  and response mapping that Gate 3 is intended to teach.
- Storing only record IDs in Pinecone was rejected because it would require a second content lookup
  store before provider-independent results could include chunk text and provenance.
- Replacing or rebuilding the entire index on every run was rejected for this gate in favour of
  idempotent upsert. Explicit stale-record cleanup remains a documented limitation.
- Multiple provider implementations, LangChain, and LlamaIndex were rejected as unnecessary scope.

## Consequences

The corpus-to-query path has explicit, independently testable provider boundaries and complete
provenance. Current and superseded versions can coexist while the normal retrieval policy remains
current-only. Remote state can be recreated and repeated identical indexing does not duplicate
records.

The system depends on two external services for live operation, incurs provider cost and rate-limit
exposure, and sends synthetic chunk/query text outside the local machine. Builder deployment is in
the US. Exact semantic rankings can change if a provider changes model behavior behind the model
alias. Stale vectors require an explicit index rebuild or future reconciliation, and neither
stale-record deletion nor production data-governance controls are part of Gate 3. Disabling
deletion protection is appropriate only for this rebuildable synthetic lab index.
