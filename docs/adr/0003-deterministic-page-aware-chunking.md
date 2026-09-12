# ADR 0003: Deterministic page-aware chunking

## Context

Gate 2 needs to turn validated page text into stable chunks while making size, overlap, ordering,
and provenance mechanics visible. Embeddings, retrieval providers, and model tokenizers have not
been introduced.

## Decision

Use one deterministic word-window strategy in the ingestion package. Split page text with
`str.split()` and join each window with a single space. This collapses whitespace runs and line
endings while preserving case, punctuation, and word content.

Each window contains at most `max_words`. Its next start advances by `max_words - overlap_words`;
overlap must be non-negative and smaller than the maximum. Windows never cross source pages.
Empty and whitespace-only pages emit no chunks.

Rename `Chunk.page` to required `Chunk.page_number` for consistency with `DocumentPage`. Assign a
single zero-based `chunk_index` across emitted chunks for the complete call. Build IDs as
`<URL-encoded-document-id>:p<four-digit-page-number>:c<six-digit-document-index>`. This produces
stable IDs from source provenance and order without UUIDs.

Require one document ID and strictly increasing page numbers per call. Accept ordered,
non-contiguous subsets because the chunker should not infer or invent missing input pages.

## Alternatives considered

- Model-specific token windows were deferred because no model has been selected and token counts
  would introduce provider coupling.
- Cross-page windows were rejected because they make source-page provenance ambiguous.
- Paragraph, semantic, and agentic strategies were deferred because Gate 2 requires one
  understandable baseline.
- Page-local indexes were rejected because they do not provide one unambiguous order across a
  document.
- Random UUIDs were rejected because identical inputs must produce identical identifiers.
- Requiring a complete contiguous document was rejected so valid page subsets can be processed.

## Consequences and limitations

Results are reproducible, provider-independent, easy to inspect, and directly traceable to one
page. Word counts will not match future model-token counts. Normalization does not preserve exact
layout or whitespace. Page boundaries may create short chunks, overlap repeats text, and changing
chunk settings or input order can change subsequent document-wide indexes and IDs.
