# Architecture decisions

## DEC-001 — Use Python 3.12

Python 3.12 is the supported language runtime, providing a modern, explicit baseline.

## DEC-002 — Use a src package layout

Application code lives under `src/` so tests exercise the installed package rather than relying on
the repository root being importable.

## DEC-003 — Keep domain models provider-independent

Core models represent application concepts and must not include fields or types belonging to a
vector database, model provider, or orchestration framework.

## DEC-004 — Do not use LangChain or LlamaIndex during foundational RAG-learning stages

**Reason:** The project is educational, and the underlying RAG mechanics should be understood
before framework abstractions are introduced.

## DEC-005 — Separate structured analytics from document retrieval

**Reason:** Numerical aggregation and calculation should be performed deterministically rather
than by vector retrieval or a language model.

## DEC-006 — Build a core MVP before optional advanced capabilities

**Reason:** A usable, evaluated document-RAG and structured-analytics system provides value sooner
and reduces the risk of spending months integrating technologies without a stable foundation.

## DEC-007 — Estimate delivery using focused hours rather than calendar optimism

**Reason:** The project includes learning, debugging, testing, documentation, and review—not only
implementation.

## DEC-008 — Use pypdf for Gate 1 born-digital PDF parsing

**Reason:** `pypdf` is a focused, pure-Python dependency that can extract text from digitally
generated PDFs without introducing an orchestration framework or provider-specific domain types.
OCR and parser interchangeability are deliberately deferred.

## DEC-009 — Use deterministic, page-bounded word-window chunking in Gate 2

**Reason:** Word windows expose chunk sizing and overlap mechanics without coupling the domain to
a model tokenizer. Chunks use required one-based `page_number` provenance, zero-based
document-wide indexes, and IDs derived from the URL-encoded document ID, page, and index. Pages
must be strictly ordered but may be non-contiguous so validated subsets remain usable. See ADR
0003 for the full behavior and trade-offs.

## DEC-010 — Use OpenAI embeddings and Pinecone Serverless for Gate 3

**Decision:** Use OpenAI `text-embedding-3-small` with explicit 1,536-dimensional output and one
Pinecone Serverless dense index using cosine similarity in AWS `us-east-1`. Keep embedding
generation and vector storage behind separate application-owned boundaries. Index name and
namespace are environment-configured; credentials are environment-only.

**Reason:** This exposes the mechanics of embedding and managed vector retrieval without a GenAI
framework, supports metadata-filtered semantic search, and matches the project owner's approved
Builder-plan constraint. It is approved only for synthetic data and must be reconsidered before
real organisational, employee, or member data is used.

## DEC-011 — Treat the manifest as the canonical metadata contract

**Decision:** Index only PDFs under `data/raw/policies`. Load descriptive metadata from
`data/corpus_manifest.csv`, derive stable document IDs from filename stems, require a one-to-one
manifest/PDF relationship, validate `CURRENT` and `SUPERSEDED` statuses and the `YES` synthetic
marker, and serialize effective dates as ISO strings in provider metadata.

**Reason:** A single canonical content source avoids duplicates while validated primitive metadata
preserves version, status, ownership, and page provenance across the provider boundary.

## DEC-012 — Treat the vector index as idempotently upserted, rebuildable state

**Decision:** Reuse deterministic Gate 2 chunk IDs as Pinecone record IDs and upsert complete
records. The index is derived from committed synthetic PDFs, manifest metadata, deterministic
chunking settings, and the configured embedding model. Gate 3 uses the accepted 300-word maximum
and 50-word overlap baseline, creates the lab index with deletion protection disabled, and does not
implement stale-record deletion.

**Reason:** Identical indexing input updates the same records instead of creating duplicates, and
the remote index can be recreated without making it a system of record. See ADR 0004.

## DEC-013 — Use one stateless OpenAI generation adapter for Gate 4

**Decision:** Use OpenAI `gpt-5.6-terra` through the Responses API with Structured Outputs, low
reasoning effort, response storage disabled, and no model tools. Keep these values explicit in one
generation configuration module and do not provide a model fallback. The provider-independent
generation boundary receives the original question and ordered Gate 3 retrieval evidence and
returns an application-owned structured draft.

**Reason:** A single explicit adapter exposes the grounding and structured-response mechanics while
keeping OpenAI SDK request, response, usage, parsing, and exception types outside application
contracts. Stateless requests and no tools keep the gate bounded to supplied synthetic evidence.

## DEC-014 — Validate citations and build provenance in the application

**Decision:** Retrieve ten chunks and exclude superseded documents by default. The model may choose
answer status, factual statement text, and cited retrieved chunk IDs only. The application rejects
unknown IDs and invalid status/content combinations, normalizes duplicate citations by first use,
and constructs all title, version, status, filename, chunk, and one-based page metadata from the
exact `RetrievalResult` set. No-evidence retrieval bypasses generation; otherwise the model may
return `INSUFFICIENT_EVIDENCE` without an uncalibrated similarity threshold.

**Reason:** Structured syntax alone cannot establish grounding. Application-side validation makes
the trust boundary explicit, preserves traceability, and prevents model-authored provenance from
becoming authoritative. See ADR 0005.

## DEC-015 — Evaluate retrieval and grounded answers separately with a local harness

**Decision:** Use a version-controlled synthetic dataset and a provider-independent local evaluation
harness. Score retrieval rankings before separately scoring answer status, citations, provenance,
and version handling. Express ratios with explicit numerators and denominators, keep 0–2 human
review separate from automated measures, and fingerprint canonical dataset, corpus, and public
configuration content with SHA-256. Evaluation data is never corpus or answer evidence.

**Reason:** Retrieval and generation have different failure modes, and transparent local metrics
make those mechanics inspectable without a hosted evaluation service, LLM judge, new framework, or
new dependency. See ADR 0006.

## DEC-016 — Insert a minimal coursework UI before Gate 6 implementation

**Decision:** CR-001 inserts Gate 5.5 after accepted Gate 5 and while Gate 6 is paused at its design
checkpoint. Use Streamlit as a thin presentation layer over the existing grounded-answer service.
Expose exact retrieval evidence through a request-local recording wrapper, retain no mutable
request state in the cached service, and open the existing Pinecone index through a query-only
surface. Preserve the Gate 6 design separately and resume it after Gate 5.5.

**Reason:** The coursework requires a clear live demonstration of policy RAG, citations, version
filtering, and abstention. A small interface improves demonstrability without moving retrieval or
generation logic into the presentation layer or claiming structured analytics is implemented.
