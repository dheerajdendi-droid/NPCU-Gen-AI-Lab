# Gate 3 — Metadata-Aware Embeddings and Semantic Retrieval — ACCEPTED

Gate 3 started and was formally accepted on **2026-09-12** after the accepted Gate 2 baseline was
reverified. The project owner approved OpenAI `text-embedding-3-small` with explicit
1,536-dimensional output and a Pinecone Serverless dense index using cosine similarity in AWS
`us-east-1` for the synthetic-only corpus.

## Objective

Implement the smallest understandable path from the canonical synthetic PDF corpus to ranked,
provider-independent semantic retrieval results with complete document and one-based page
provenance.

## In scope

- Load and validate `data/corpus_manifest.csv` as the canonical descriptive metadata source
- Require a one-to-one relationship between manifest rows and PDFs in `data/raw/policies`
- Parse PDFs through the existing Gate 1 ingestion boundary
- Chunk pages through the existing Gate 2 deterministic page-bounded word-window chunker
- Associate each chunk with document title, version, status, effective date, owner, filename, and
  synthetic marker
- Embed chunk and query text with OpenAI `text-embedding-3-small` using exactly 1,536 dimensions
- Upsert vectors into one Pinecone Serverless dense index with cosine similarity in AWS
  `us-east-1`
- Configure the Pinecone index name and namespace through environment settings
- Use existing deterministic chunk IDs as Pinecone record IDs
- Retrieve ranked top-k evidence through provider-independent application models
- Exclude superseded documents by default and include them only when explicitly requested
- Use deterministic provider test doubles for routine tests and one explicitly marked live smoke
  test that skips when either provider credential is absent
- Add a small named set of synthetic retrieval smoke questions across distinct policy areas

Only PDFs are indexed. The editable source Markdown exists for corpus maintenance and must not be
indexed because doing so would duplicate content.

## Out of scope

- LLM answer generation, RAG prompts, final-answer generation, or answer citations
- Reranking, lexical search, hybrid search, or provider-comparison experiments
- Multiple embedding providers or vector databases
- Model-specific, semantic, layout-aware, or agentic chunking
- OCR, scanned-document support, or layout reconstruction
- Structured analytics, graph retrieval, orchestration, routing, agents, or memory
- APIs, command-line interfaces, user interfaces, deployment, or Gate 4 work
- LangChain and LlamaIndex

## Accepted decisions

- The embedding boundary returns application-owned vectors and exposes no OpenAI response types.
- The vector-index boundary accepts application-owned records and returns application-owned scored
  matches; Pinecone response types remain inside its adapter.
- The OpenAI embedding adapter always sends model `text-embedding-3-small` and
  `dimensions=1536`.
- The Pinecone adapter may create an index only after validating all six approved settings: dense
  vectors, 1,536 dimensions, cosine metric, AWS cloud, `us-east-1` region, and a configured index
  name. Namespace is also required and environment-configured.
- Stable manifest document IDs are derived from the PDF filename stem. Filenames and derived IDs
  must both be unique.
- Manifest status is the closed set `CURRENT` and `SUPERSEDED`; synthetic is the closed manifest
  value `YES`. Effective dates use the manifest format `%d %B %Y` and provider metadata uses ISO
  `YYYY-MM-DD` strings.
- Indexing uses idempotent upsert with existing Gate 2 chunk IDs. The vector index is derived,
  rebuildable state and is created with deletion protection disabled; this gate does not add
  deletion or stale-record reconciliation.
- The corpus build uses the accepted Gate 2 validation baseline of max_words=300 and
  overlap_words=50.
- Chunk text is stored with primitive provenance metadata so a retrieval match can be mapped
  without a provider-shaped domain model or a second content store.
- Retrieval scores are Pinecone cosine similarity scores: higher means more similar. Tests do not
  rely on exact live-provider scores.
- When scores tie, application results are ordered by descending score and then ascending chunk
  ID, providing deterministic ordering where the application controls it.

See ADR 0004 for the rationale and consequences.

## Public behavior and errors

- Manifest paths must exist and refer to regular files.
- The header must match the required schema exactly. Blank values, malformed dates, invalid status
  or synthetic values, duplicate filenames, duplicate document IDs, missing PDFs, and unlisted PDFs
  fail with a manifest-validation error that identifies the problem.
- Embedding inputs must be nonblank. Provider-returned vector counts and dimensions are validated.
- Query text must be nonblank and `top_k` must be a positive non-boolean integer.
- `top_k` larger than the number of matches returns all available matches; no matches returns an
  empty list.
- Retrieval defaults to a `CURRENT` status metadata filter. Explicit superseded inclusion omits
  that filter so both versions may coexist and be searched.
- Missing OpenAI or Pinecone credentials/configuration fail during live adapter construction with
  configuration errors, without displaying secret values.
- Provider SDK exceptions are translated to application embedding or vector-index errors.
- Any vector dimension other than 1,536, or a mismatched existing Pinecone index configuration,
  fails before upsert/query proceeds.
- The live smoke test is explicitly marked and skips cleanly unless both API keys, index name, and
  namespace are configured.

## Expected outputs

Indexing returns a provider-independent summary containing document, chunk, and upsert counts.
Retrieval returns ranked values containing chunk ID, document ID, chunk text, one-based page
number, title, version, document status, source filename, rank, and similarity score.

## Acceptance evidence

- All four required live settings were present through the normal Settings path, and `.env` was
  confirmed ignored without revealing any values.
- The explicit live test passed: one test selected and 130 deterministic tests deselected.
- The configured Pinecone index reported dense vectors, 1,536 dimensions, cosine similarity, AWS,
  `us-east-1`, ready status, and exactly 194 vectors in the configured namespace.
- All named current-policy queries returned ten CURRENT results and found their expected document:
  member eligibility at rank 1/page 3, lending affordability at rank 1/page 5, vulnerable members
  at rank 6/page 5, and supplier change at rank 1/page 4.
- Explicit historical Lending retrieval found both current v4.0 and superseded v3.1.
- The deterministic suite passed 130 tests with the live test deselected.
- Ruff, dependency health, editable imports, whitespace, secret, and out-of-scope scans passed.
- The live run emitted two local PytestCacheWarning messages because the elevated Windows process
  could not write pytest cache files; these did not affect providers, retrieval, or test results.

## Exit criteria

- [x] Gate 2 is formally accepted, committed, and reverified
- [x] The owner approved the OpenAI/Pinecone stack and regional constraint
- [x] The approved provider, index, metadata, filtering, and rebuild decisions are recorded
- [x] Manifest and one-to-one corpus validation are implemented and tested
- [x] Every indexed chunk retains correct document and one-based page provenance
- [x] OpenAI request/response mapping and vector dimensions are tested with deterministic doubles
- [x] Pinecone record construction, configuration validation, and idempotent upsert are tested
- [x] Current-only retrieval and explicit superseded inclusion are demonstrated
- [x] Nonblank query, positive top-k, empty results, tie ordering, and provider errors are tested
- [x] A local end-to-end synthetic PDF-to-retrieval integration test passes without network access
- [x] Named retrieval smoke questions are documented and exercised
- [x] The complete deterministic test suite and Ruff pass
- [x] Installed dependencies are healthy and editable-package imports succeed
- [x] The real-provider smoke test passes with all four live settings configured
- [x] No secrets or out-of-scope technologies are present
- [x] Documentation describes actual implemented behavior and Gate 4 has not started

Gate 3 is **ACCEPTED**. Gate 4 has not started.
