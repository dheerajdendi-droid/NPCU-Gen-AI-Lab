# Current gate: Gate 1 — Document Ingestion and Parsing

## Objective

Implement the smallest complete, provider-independent path for extracting page-aware text from
synthetic, digitally generated PDF documents.

## In scope

- Select and document one minimal PDF parsing dependency (`pypdf`).
- Add a provider-independent page-level representation.
- Preserve one-based source page numbers.
- Keep PDF-library types behind the ingestion boundary.
- Parse a synthetic, born-digital PDF fixture.
- Return validated text associated with every source page.
- Define and test empty-page, invalid-PDF, missing-file, and encrypted-PDF behavior.
- Add unit tests for mapping and validation and an integration test using a real PDF.
- Record the parsing and page-provenance decision in an ADR.

## Out of scope

- Chunking
- Embeddings
- Vector databases
- Retrieval and reranking
- LLM calls
- RAG
- OCR and scanned-document support
- Citations beyond preserving source-page provenance
- APIs and user interfaces
- LangChain and LlamaIndex
- Multiple interchangeable parser implementations
- Structured analytics, graphs, agents, memory, voice, and deployment

## Model decision

`DocumentPage` is the application-level result for one PDF page. It contains a nonblank
`document_id`, a one-based positive `page_number`, and extracted `text`. Empty source pages are
represented with an empty string so page positions are never discarded. The model exposes no
`pypdf` types.

## Expected output

Parsing returns a list of validated `DocumentPage` values in source order, including empty pages.
Each result retains the caller-supplied document identifier and its original one-based page
number. Text is extracted only from born-digital PDF content.

## Error behavior

- A missing or non-file path raises `FileNotFoundError`.
- A malformed or unreadable PDF raises the ingestion-level `InvalidPdfError`.
- Any encrypted PDF raises the ingestion-level `EncryptedPdfError`; password handling is not in
  scope.
- A page with no extractable text produces a `DocumentPage` whose `text` is `""`.
- Invalid page mappings fail Pydantic domain validation.

## Exit criteria

- [x] Gate 0 closure tests continue to pass without the pytest `pythonpath` shortcut
- [x] `DocumentPage` validation and page mapping are unit tested
- [x] A real synthetic, born-digital PDF is parsed in an integration test
- [x] One-based page provenance is preserved, including empty pages
- [x] Missing, invalid, and encrypted PDFs have tested error behavior
- [x] Package imports succeed against the editable installation
- [x] The complete test suite passes
- [x] Ruff passes
- [x] Installed dependencies have no broken requirements
- [x] No post-Gate-1 technology has been introduced
- [x] Architecture and learning documentation reflect the implemented behavior

Gate 1 must not be formally accepted until every criterion above has been demonstrated. Gate 2
must not start as part of this work.
