# Learning log

## Gate 0 learning objectives

- Understand why modular architecture matters
- Understand domain models versus provider models
- Understand separation of concerns
- Understand why dependencies are being introduced gradually
- Understand why structured analytics and RAG are different capabilities
- Understand the difference between an MVP timeline and a full architectural demonstration
  timeline
- Understand why testing, evaluation, and documentation must be included in delivery estimates

These are objectives for Gate 0; this log does not claim they have already been mastered.

## Gate 1 learning objectives

- Understand the difference between born-digital text extraction and OCR
- Understand why source-page provenance must be preserved during ingestion
- Understand how an external parser can remain behind an application boundary
- Understand how empty pages affect downstream traceability
- Understand how domain validation differs from parser error handling
- Understand how integration tests complement isolated mapping tests

These are objectives for Gate 1 and do not claim mastery. The observations below record concrete
implementation findings without claiming that every objective has been mastered.

## Gate 1 implementation observations

- `pypdf` may return `None` when a page has no extractable text. Mapping that value to `""` while
  retaining the page object preserves the document's page sequence.
- A separate `DocumentPage` model makes provenance explicit and testable without leaking parser
  page objects into the application domain.
- Parser failures and domain-validation failures serve different purposes: ingestion errors
  explain file-level failures, while Pydantic errors reject invalid application data.
- A real born-digital fixture verifies the external library and PDF structure together; isolated
  mapping tests verify one-based numbering and empty-page behavior without relying on PDF parsing.

## Gate 2 learning objectives

- Understand deterministic word-window construction and advancing-window invariants
- Understand the distinction between model-independent word counts and model-specific tokens
- Understand how overlap affects adjacent chunks and repeated context
- Understand why page-bounded chunks make source provenance explicit
- Understand document-wide ordering and deterministic identifier construction
- Understand how whitespace normalization becomes an application contract
- Understand why ordered page subsets can be valid without inventing missing pages

These are learning objectives and do not claim personal mastery. The observations below record
factual implementation findings without inventing personal reflections.

## Gate 2 implementation observations

- `str.split()` plus a single-space join gives a small, deterministic normalization rule across
  spaces, tabs, and line endings while preserving case and punctuation.
- Requiring `overlap_words < max_words` guarantees the window advances and prevents an infinite
  chunking loop.
- A document-wide chunk index gives a single ordering across pages; blank pages emit no chunk and
  therefore no index, while later chunks retain their original page number.
- Page-order validation is separate from completeness: strictly increasing page subsets can be
  processed without claiming that omitted pages do not exist.
- IDs derived from URL-encoded document identity, page number, and document-wide index are stable
  for identical input and configuration. Changing input order or chunk configuration can change
  later indexes and IDs.

## Gate 3 learning objectives

- Understand the difference between an embedding provider and a vector-index provider
- Understand how fixed vector dimensions must agree across model, application, and index
- Understand how manifest metadata becomes validated retrieval provenance
- Understand idempotent upsert and why a vector index is derived rather than canonical state
- Understand metadata filtering for current and superseded policy versions
- Understand why provider SDK models should remain inside adapters
- Understand deterministic test doubles versus explicitly opted-in live smoke tests
- Understand credential, cost, regional, and data-handling implications of managed retrieval

These are learning objectives and do not claim personal mastery. The observations below record
factual implementation findings without inventing personal reflections.

## Gate 3 implementation observations

- Deriving document IDs from unique PDF filename stems preserves a stable link between the manifest,
  parsed pages, deterministic chunks, vector records, and retrieval results.
- Strict set comparison between manifest filenames and corpus PDFs detects both missing and unlisted
  documents before any paid embedding request can occur.
- Effective dates need an explicit English-month parser to avoid locale-dependent manifest
  behavior; provider metadata uses ISO date strings.
- Separate CorpusDocument and CorpusChunk models retain metadata and page provenance without
  flattening PDFs into the foundation Document.text field.
- Passing explicit dimensions=1536 to the embedding request and validating every returned vector
  makes model/index mismatch visible at the application boundary.
- Reusing Gate 2 chunk IDs as vector IDs makes repeated upsert idempotent for identical input, but
  does not remove records that disappear from a later corpus build.
- A CURRENT metadata filter is simpler and safer than retrieving both versions and discarding
  superseded matches after ranking.
- Deterministic keyword embeddings and an in-memory cosine index can validate mapping, filtering,
  ranking, and provenance without claiming to reproduce real model quality.
- The live adapter validated a ready dense 1,536-dimensional cosine index in AWS us-east-1, and the
  configured namespace reported exactly 194 records after idempotent upsert.
- The four named live queries found their expected current document at ranks 1, 1, 6, and 1 while
  retaining one-based page provenance. This demonstrates a working retrieval path without claiming
  comprehensive retrieval quality.
- The explicit historical query found both Lending v4.0 and superseded v3.1, while normal queries
  returned only CURRENT results.
- Provider verification can succeed even when local test tooling emits unrelated cache warnings;
  the live run's two warnings concerned Windows pytest-cache write permissions, not OpenAI,
  Pinecone, metadata, or retrieval behavior.
