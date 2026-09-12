# Gate 2 — Deterministic Page-Aware Chunking — ACCEPTED

Gate 2 was formally accepted by the project owner on **2026-09-12** after every exit criterion was
reverified. The project is awaiting explicit Gate 3 initiation. This document retains the accepted
Gate 2 contract and evidence; it does not define Gate 3.

## Objective

Implement a small, provider-independent, deterministic transformation from validated
`DocumentPage` values into validated `Chunk` values while preserving source-document and
one-based source-page provenance.

## In scope

- One understandable word-window chunking strategy
- Positive `max_words` and non-negative `overlap_words` configuration
- Page-bounded chunks produced in source order
- Explicit whitespace and line-ending normalization
- Deterministic chunk text, ordering, indexes, and identifiers
- Empty-page handling and page-sequence validation
- Focused unit tests and a PDF-to-pages-to-chunks integration test
- Documentation of decisions, behavior, limitations, and learning observations

## Out of scope

- Embeddings and model-specific tokenization
- Vector databases, indexes, similarity search, retrieval, and reranking
- LLM calls, prompts, generation, RAG, and citations beyond provenance fields
- OCR, layout reconstruction, and table extraction
- Semantic or agentic chunking and multiple chunking strategies
- LangChain and LlamaIndex
- APIs, command-line tools, and user interfaces
- Analytics, graphs, agents, memory, voice, and deployment
- Gate 3 functionality and placeholder dependencies for future gates

## Model and provenance decision

`Chunk.page` is renamed to required `Chunk.page_number` so `DocumentPage` and `Chunk` use the same
one-based terminology. A chunk cannot span pages. `chunk_index` is a zero-based, document-wide
sequence over emitted chunks, so empty pages do not create gaps and chunks remain unambiguously
ordered across the input document.

The pre-existing optional `section` and `metadata` fields remain part of the domain contract, but
Gate 2 does not infer or populate them because word windows do not provide reliable section or
metadata semantics.

Chunk IDs have the form:

```text
<URL-encoded-document-id>:p<four-digit-page-number>:c<six-digit-document-index>
```

For example, `policy-001:p0002:c000003`. IDs are derived only from validated provenance and
ordering; no random values are used.

## Chunk-size, overlap, and normalization behavior

- Text is split with Python's `str.split()`, which trims leading and trailing whitespace and
  treats runs of spaces, tabs, and line endings as a single separator.
- Chunk text is rebuilt with one ASCII space between words.
- Case, punctuation, and word content are otherwise preserved.
- Every chunk contains at most `max_words` words.
- The next window advances by `max_words - overlap_words`.
- Adjacent chunks from the same page share exactly `overlap_words` words when another window is
  required and enough words exist.
- Overlap never crosses a page boundary.
- Empty and whitespace-only pages produce no chunks and do not change later page numbers.

## Input and error behavior

- No pages returns an empty list after configuration validation.
- One page and ordered page subsets are accepted.
- Page numbers must be strictly increasing, but need not begin at 1 or be contiguous. This lets
  callers chunk a valid subset without inventing missing content.
- All pages in one call must have the same `document_id`.
- Duplicate or out-of-order page numbers raise `ValueError`.
- Mixed document IDs raise `ValueError`.
- `max_words` must be an integer greater than zero.
- `overlap_words` must be an integer greater than or equal to zero and strictly smaller than
  `max_words`; invalid configuration raises `ValueError` before page iteration.
- Inputs that are not `DocumentPage` instances raise `TypeError`.
- Invalid `DocumentPage` and `Chunk` construction fails Pydantic domain validation.

## Expected output

The chunker returns validated `Chunk` values in deterministic document order. Consumers see only
application-domain types and need not know whether pages originated from `pypdf` or another
earlier ingestion step.

## Exit criteria

- [x] Gate 1 is formally recorded as accepted with its verification evidence retained
- [x] Valid pages produce validated chunks deterministically
- [x] Deterministic IDs and zero-based document-wide indexes are tested
- [x] Every chunk retains its document ID and one-based page provenance
- [x] Chunks are page-bounded and maximum word size and overlap are enforced
- [x] Empty and whitespace-only page behavior is documented and tested
- [x] Invalid configuration, mixed documents, and invalid page sequences fail clearly
- [x] Unit tests cover chunking boundaries and domain validation
- [x] An integration test covers synthetic PDF parsing followed by chunking
- [x] The complete test suite passes without unexpected warnings
- [x] Ruff passes
- [x] Editable-package imports succeed without a pytest path shortcut
- [x] Installed dependencies have no broken requirements
- [x] Documentation and the Gate 2 ADR describe actual behavior
- [x] No secrets, Gate 3 implementation, or future provider SDKs are present

Gate 2 is **ACCEPTED**. Gate 3 has not started.
