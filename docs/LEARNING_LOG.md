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

## Gate 4 learning objectives

- Understand the distinction between schema-valid structured output and evidence-grounded output
- Understand why a language model may select chunk IDs but must not author citation provenance
- Understand statement-level grounding and application-side citation validation
- Understand deterministic citation normalization, numbering, and rendering
- Understand how no-evidence bypass differs from model-selected insufficient evidence
- Understand how stable instructions and untrusted evidence data form a prompt-security boundary
- Understand current-only answers versus explicit historical comparisons
- Understand stateless Responses API requests, disabled storage, and provider-independent usage
- Understand deterministic generation doubles versus focused live answer review

These are learning objectives and do not claim personal mastery. The observations below record
factual implementation findings without inventing personal reflections.

## Gate 4 implementation observations

- OpenAI SDK 3.8.0 exposes `responses.parse` with a Pydantic `text_format`, so Structured Outputs can
  be used without manually parsing JSON or adding another dependency.
- A parsed schema cannot prove that cited chunk IDs were supplied for the request. Comparing every
  cited ID with an exact evidence map remains a separate application responsibility.
- Resolving titles, versions, statuses, filenames, and pages from RetrievalResult values avoids
  trusting duplicated provenance generated by the model.
- First-use chunk numbering makes repeated citations stable and allows two distinct chunks from the
  same page to remain independently traceable.
- Retrieving no evidence is sufficient for a local abstention and avoids a needless provider call.
  When evidence exists, Gate 4 deliberately uses model abstention rather than an uncalibrated score
  threshold.
- Serializing evidence as deterministic JSON keeps ordering and field ownership testable. Explicit
  instructions treat all retrieved text, including instruction-like text, as untrusted reference
  data; this reduces authority but does not make model compliance mathematically guaranteed.
- The focused live test can protect accepted remote state by failing when the index is absent and by
  using a control wrapper that has no creation path.
- The first live-test attempt made no provider call because the execution safety layer required
  direct active-message permission to disclose repository-derived synthetic evidence.
- The authorized focused live test exercised six query-to-answer scenarios without rebuilding or
  mutating the existing 194-vector index. Every answered statement retained application-validated
  chunk citations and positive one-based page provenance.
- The unsupported synthetic question produced `INSUFFICIENT_EVIDENCE` without citations, while the
  historical Lending comparison cited both v4.0 and v3.1 and labelled v3.1 `SUPERSEDED`.
- The six live generation responses used 24,374 input tokens and 1,889 output tokens. Provider usage
  can therefore be retained for cost learning without exposing provider response objects.
- A pytest marker describes a test but does not disable it. A collection hook requiring
  `--run-live` is needed so the presence of credentials cannot accidentally authorize provider
  calls or cost.

## Gate 5 learning objectives

- Understand why retrieval quality and answer quality require separate measures
- Understand Hit@K, reciprocal rank, multi-document recall, and page-evidence recall
- Understand citation precision and recall against declared evidence expectations
- Understand why zero denominators must remain visible rather than becoming misleading scores
- Understand the boundary between automated structural checks and human semantic review
- Understand how canonical serialization produces stable dataset, corpus, and configuration
  fingerprints
- Understand how evaluation ground truth can leak into a retrieval corpus if directories are not
  explicitly separated and tested
- Understand why baseline measurement precedes retrieval or prompt tuning
- Understand deterministic offline evaluation versus an authorization-gated live baseline

These are learning objectives and do not claim personal mastery. Implementation observations will
record concrete findings without inventing personal reflections.

## Gate 5 implementation observations

- A relevance-free unsupported case cannot use Hit@K or reciprocal rank honestly; retaining a zero
  denominator and null value distinguishes “not applicable” from a retrieval miss.
- Multi-document recall must compare distinct document IDs rather than chunk counts because several
  highly ranked chunks from one policy do not satisfy a cross-policy evidence requirement.
- Citation validity, document precision and document recall answer different questions. A citation
  can be a valid retrieved chunk while still coming from a document the case did not allow.
- Recording retrieval inside the grounded-answer call lets evaluation reuse the exact evidence sent
  to generation instead of paying for or comparing against a second, potentially different query.
- Canonical JSON with sorted keys and compact separators provides stable SHA-256 fingerprints while
  excluding credentials, deployment names, latency and provider objects.
- The protected JSON contains questions and reference facts, but canonical ingestion still accepts
  only manifest-listed PDFs. Regression tests verify that indexing inputs and evidence provenance
  remain the 194 PDF-derived chunks.
- Automated checks can assess declared status, citations and provenance, but cannot establish that
  prose is fully correct or complete. The separate 0–2 human template preserves that responsibility.
- A read-only Pinecone wrapper that exposes describe and query but no create or upsert operation
  makes the live evaluation mutation boundary executable rather than merely documentary.
- The authorized 20-case live baseline completed without provider failures or structural grounding
  violations while leaving the existing 194-vector namespace unchanged by design.
- Perfect Hit@5 and Hit@10 can coexist with lower Hit@1 and Hit@3. The observed 14/17 Hit@1 and
  16/17 Hit@3 results make ranking quality visible instead of reducing retrieval to a binary pass.
- Page-evidence hits of 25/26 and citation-document precision and recall of 23/25 show that valid
  chunk citations alone do not prove complete use of the expected documents and pages.
- All three unsupported cases abstained without citations, and both historical cases labelled the
  superseded Lending version correctly; these focused checks demonstrate the intended behavior only
  for the small synthetic dataset.
- Passing automated measures does not complete the human-review rubric. Semantic correctness,
  completeness, relevance, evidence use, clarity, and version handling still require human ratings,
  while live rankings and prose remain provider-variable.

## Gate 6 learning objectives

- Understand why exact management metrics belong in structured analytics rather than retrieval or
  generation
- Understand workbook validation as a boundary between weakly typed Excel cells and typed records
- Understand table grain, primary keys, foreign keys, and pre-aggregation as controls against
  double-counting
- Understand additive measures, ratios, explicit denominators, and zero-denominator semantics
- Understand PAR30 as an at-risk outstanding-balance ratio rather than an arrears-balance ratio
- Understand deterministic parameterized SQL and stable calculation identities
- Understand workbook-to-database reconciliation and rebuildable derived state
- Understand the difference between measured facts, associations, possible contributing factors,
  and causal claims
- Understand why a hand-reconciled synthetic scenario is useful but cannot establish production
  accuracy or causality

These are proposed Gate 6 learning objectives and do not claim mastery. Implementation observations
will be added only after the design checkpoint is approved and evidence exists.

## Gate 5.5 learning objectives

- Understand the presentation layer as a consumer of application services
- Understand why Streamlit must not own retrieval, generation, grounding, or citation logic
- Understand the difference between a focused coursework demo and a production interface
- Understand how authoritative citations and visible abstention help users assess trust
- Understand how exact retrieval evidence can explain an answer without exposing chain-of-thought
- Understand why a roadmap insertion requires an explicit change request and preserved history

These are Gate 5.5 objectives and do not claim mastery. Implementation observations will be added
only when evidence exists.

## Gate 5.5 implementation observations

- A request-local recording wrapper can expose the exact retrieval supplied to generation without
  issuing a second query or coupling Streamlit to a provider response type. Retaining the recorder
  in a globally cached service would allow concurrent requests to overwrite one another's evidence.
- A separate query-only Pinecone surface makes the demo's no-write boundary executable: index
  existence and compatibility are inspected, but creation and upsert are unavailable.
- Application-owned citation records keep the model from inventing page, version, status, or source
  labels; the matching retrieval result supplies the already-validated effective date for display.
- Visible insufficient-evidence status is a product behavior, not merely an evaluation metric. The
  unsupported live question produced no source cards or generic answer.
- The cross-document payroll scenario visibly demonstrated that one answer can cite two current
  policies while preserving statement-level citation markers.
- Streamlit 1.49.1 was selected because its runtime remains compatible with the existing Python
  environment; a newer release introduced a Starlette range that conflicted with installed FastAPI.
