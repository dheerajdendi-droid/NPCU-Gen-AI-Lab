# ADR 0002: PDF parsing and page provenance

## Context

Gate 1 needs a small, understandable path from synthetic, born-digital PDFs to validated
application data. Flattening a whole PDF into one string would lose the source page needed for
later traceability.

## Decision

Use `pypdf` as the sole Gate 1 parsing dependency and keep it inside the ingestion package. Map
each source page to a provider-independent `DocumentPage` containing the document identifier,
one-based page number, and extracted text. Preserve empty pages with `text=""`.

Missing paths raise `FileNotFoundError`. Malformed PDFs raise `InvalidPdfError`. Encrypted PDFs
raise `EncryptedPdfError`; password handling is not supported in this gate.

## Alternatives considered

- Flattening all pages into one string, rejected because it loses page provenance.
- Adding OCR, rejected because scanned documents are outside Gate 1.
- Defining a generic parser interface, rejected because only one implementation is currently
  required.
- Using a broader document or GenAI framework, rejected as unnecessary abstraction.

## Consequences

The implementation is small, page provenance is explicit, and domain consumers do not depend on
`pypdf`. Scanned pages yield empty text, encrypted files are rejected, and supporting another
parser later will require a deliberate new decision.
