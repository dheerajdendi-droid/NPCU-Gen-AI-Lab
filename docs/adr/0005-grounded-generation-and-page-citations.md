# ADR 0005: Grounded generation and page citations

## Status

Accepted for Gate 4 implementation on 2026-09-12 and formally accepted on the same date after the
focused live OpenAI/Pinecone test passed and the owner reviewed its answers and citations.

## Context

Gate 3 returns ranked, provider-independent evidence with stable chunk IDs and complete document
and page provenance. Gate 4 needs to turn that evidence into a concise answer without trusting a
language model to invent or reproduce authoritative source metadata. Retrieved document text is
also untrusted input and may contain instruction-like language.

The owner approved OpenAI `gpt-5.6-terra` through the Responses API with Structured Outputs and low
reasoning effort. Official OpenAI documentation confirms that this model supports the Responses
endpoint, Structured Outputs, and low reasoning effort. Installed OpenAI SDK 3.8.0 provides the
Pydantic `responses.parse` path required for schema-backed parsing.

## Decision

Use one provider-independent generation boundary. It accepts the normalized question and an ordered
sequence of Gate 3 `RetrievalResult` evidence, and returns an application-owned structured draft.
The sole adapter uses `gpt-5.6-terra`, Responses API Structured Outputs, reasoning effort `low`,
`store=false`, and an empty tools list. There is no fallback model, web search, file search, or other
model tool.

Keep stable grounding instructions separate from dynamic question and evidence content. Serialize
evidence deterministically by retrieval rank with explicit block boundaries and application-owned
chunk IDs, titles, versions, statuses, one-based page numbers, filenames, and text. Instructions
state that evidence is untrusted reference data, document-contained instructions must be ignored,
outside knowledge and unstated inferences are forbidden, conflicts must be exposed, and insufficient
evidence requires abstention.

The Structured Output schema lets the model choose only `ANSWERED` or `INSUFFICIENT_EVIDENCE`,
statement text with cited chunk IDs, and an optional insufficient-evidence explanation. OpenAI SDK
types and the adapter's parsing schema do not cross the provider boundary. Provider-independent
token counts may be retained for cost learning.

An application service retrieves `top_k=10`, excluding superseded documents by default and allowing
explicit historical inclusion. Empty retrieval bypasses the model. After generation, the service
validates semantic invariants that schema parsing alone cannot prove. Every answered statement must
cite at least one ID in that request's exact evidence set. Unknown IDs, answered drafts without
cited evidence, and insufficient drafts with fabricated statements or citations reject the complete
draft.

The application normalizes duplicate chunk citations in first-occurrence order and assigns stable
numbers globally by first use. It constructs citation records only from matched `RetrievalResult`
metadata. Distinct chunks remain distinct citations even when they share a page. Concise rendering
uses `[Title, version X, page Y]` and explicitly adds `SUPERSEDED` for historical sources; structured
records retain document ID, title, version, status, source filename, page, and chunk ID.

Insufficient evidence is decided from the supplied evidence and validated model result, except that
no evidence always abstains locally. Gate 4 adds no similarity threshold because threshold
calibration belongs with later evaluation.

## Alternatives considered

- Free-form Markdown or manually parsed JSON was rejected because the approved SDK supports a
  schema-backed Structured Outputs path.
- Trusting model-generated page or document metadata was rejected because it creates an avoidable
  hallucination surface despite authoritative metadata already existing in retrieval results.
- Embedding citation markers directly in answer prose was rejected because statement-to-evidence
  relationships and validation would be harder to inspect.
- A similarity threshold was deferred because it would be uncalibrated before evaluation.
- Model fallback, multiple providers, orchestration frameworks, LangChain, and LlamaIndex were
  rejected as outside the smallest Gate 4 path.

## Consequences

The answer path is small, stateless, testable without network access, and traceable from every
statement to an exact retrieved chunk and one-based page. Prompt injection defenses are explicit,
but they remain model instructions rather than a mathematical guarantee; application-side citation
validation limits the resulting authority to retrieved evidence.

Live generation incurs OpenAI token costs and semantic behavior may vary behind the model alias.
Top-ten vector retrieval can omit useful evidence, and a language model can abstain despite useful
evidence or select a less useful retrieved chunk. Gate 4 smoke assertions therefore test safety,
grounding, status, and provenance invariants rather than exact wording. Comprehensive calibration
and answer-quality measurement remain Gate 5 work.
