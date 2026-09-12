# Gate 5 — Retrieval and Grounded Answer Evaluation

Gate 5 started on **2026-09-12** from the formally accepted Gate 4 baseline at commit `0126705`.
Gate 5 evaluates the accepted retrieval and grounded-generation behavior without tuning it. It is
not formally accepted, and Gate 6 has not started.

## Objective

Build the smallest reproducible, provider-independent evaluation harness that measures retrieval
quality separately from grounded-answer and citation quality. Normal evaluation must be completely
deterministic and offline; a separately authorized live baseline may use the accepted OpenAI and
Pinecone adapters without changing the existing vector index.

## Scope

- Load a strict, version-controlled synthetic evaluation dataset from
  `data/_evaluation_do_not_index/gate5_cases.json`.
- Validate case structure, unique IDs, manifest document IDs, document statuses, expected pages,
  category rules, and supported answer expectations.
- Cover 12 current-policy questions across all ten current documents, three multi-document
  questions, three unsupported or adversarial questions, and two current-versus-superseded Lending
  comparisons.
- Score retrieval rankings, page evidence, required and forbidden sources, answers, citations,
  abstention, historical status handling, and structural grounding.
- Keep automated scores separate from optional 0–2 human-review ratings.
- Render deterministic JSON and readable Markdown reports with per-case and aggregate evidence.
- Fingerprint the dataset, canonical corpus, and evaluation configuration using canonical JSON and
  SHA-256.
- Add deterministic fakes and one explicitly opted-in, read-only live integration test.
- Preserve the accepted Gate 3 and Gate 4 configuration and behavior.

## Dataset contract

Every case has a stable ID, question, category, superseded-evidence flag, expected answer status,
relevant documents, required and allowed citation documents, forbidden documents or statuses,
optional document/page expectations, concise reference facts, and human-review guidance.

`ANSWERED` cases require relevant evidence and at least one required citation document.
`INSUFFICIENT_EVIDENCE` cases cannot declare relevant evidence, required or allowed citations, page
expectations, or historical retrieval. Current-policy cases forbid superseded evidence. Historical
comparison cases explicitly allow superseded retrieval and name both current and superseded
Lending documents. Every named document and expected page is checked against the canonical built
corpus before evaluation.

The evaluation directory is test-only input. Canonical ingestion remains restricted to the
manifest and PDFs under `data/raw/policies`; evaluation questions and reference facts must never
become parsed pages, chunks, embedding inputs, vector records, retrieved evidence, or generation
evidence.

## Retrieval measures

- **Document Hit@1, @3, @5 and @10:** whether at least one relevant document occurs within the
  first N retrieved chunks. Unsupported cases have no relevant-document denominator and report
  this measure as not applicable rather than as a success or failure.
- **Mean Reciprocal Rank:** the reciprocal of the first relevant rank, averaged only over cases
  that declare relevant documents. A miss contributes zero.
- **Multi-document recall:** distinct relevant documents retrieved at the configured depth divided
  by distinct relevant documents expected.
- **Page evidence hits:** expected document/page pairs represented in the retrieved evidence divided
  by expected pairs. Cases without page expectations retain an explicit zero denominator.
- **Unexpected superseded retrieval:** superseded results returned when the case did not permit
  them.
- **Required and forbidden violations:** missing relevant documents, explicitly forbidden document
  IDs, forbidden statuses, duplicate chunk IDs, and inconsistent result ranks are recorded rather
  than hidden.

## Grounded-answer measures

- Expected `ANSWERED` versus `INSUFFICIENT_EVIDENCE` accuracy.
- Citation chunk-ID validity against the exact evidence supplied to generation.
- Citation document precision against the case's allowed citation documents.
- Citation document recall against required citation documents.
- Citation-free behavior for unsupported questions.
- Historical `SUPERSEDED` labelling and current-versus-superseded metadata correctness.
- Structural grounding violations, including unknown citations, duplicate citation records,
  mismatched application provenance, invalid statement references, and non-positive pages.

Automated metrics measure declared invariants, not semantic completeness of prose. No model judges
another model in this Gate.

## Human review

Each case has a separate review template with optional integer ratings from 0 to 2 for correctness,
completeness, relevance, appropriate evidence use, clarity, and version/status handling. Reviewer
notes and a final disposition remain visibly separate from automated results. Unreviewed cases use
the `PENDING` disposition and no numeric ratings.

## Reports and fingerprints

Per-case results retain the question category, exact retrieved evidence IDs, retrieval measures,
answer measures, provider-independent token usage, latency, safe failure text, and human-review
template. Aggregate metrics always expose numerator and denominator; a zero denominator renders a
null value and `N/A`, never an invented zero or perfect score. Cases and mappings render in stable
order, and floating-point values are rounded consistently.

Dataset and corpus fingerprints cover the validated application-owned content. Configuration
fingerprints cover the retrieval depth and accepted provider model identifiers, not credentials,
index names, namespaces, timestamps, latency, or provider response objects.

## Live boundary

The focused live test is marked `live` and remains skipped unless pytest receives `--run-live`.
It loads the accepted provider settings normally, confirms the existing Pinecone index and
194-vector namespace, and exposes no credential values. The index control is read-only: it may
describe and query the existing index but cannot create, upsert, update, or delete anything.

The final 20-case live baseline is expected to make approximately 20 OpenAI query-embedding calls,
20 Pinecone searches, and up to 20 stateless `gpt-5.6-terra` generation calls. It records each
case's evidence once and reuses that exact evidence for retrieval and answer scoring. It must not
run until the owner directly authorizes the questions, synthetic evidence disclosure, provider
calls, cost, and read-only remote effects. The future command will be:

```text
python -m pytest --run-live tests/integration/test_live_evaluation.py -vv -s
```

## Errors

- Missing, unreadable, malformed, or structurally invalid evaluation JSON fails clearly.
- Duplicate case IDs, unknown corpus documents, invalid pages or statuses, and inconsistent case
  rules fail before evaluation begins.
- Retrieval or generation failures become safe per-case failures in a report; credentials, complete
  prompts, full evidence text, and raw provider objects are never included.
- Metric functions reject duplicate retrieved chunks and invalid result ordering while retaining
  explicit violation evidence.

## Out of scope

- Retrieval, chunking, embedding, prompt, or generation tuning
- Reranking, hybrid or keyword search, and similarity-threshold calibration
- LLM-as-judge scoring, automatic prompt optimization, or hosted evaluation services
- New provider, vector database, evaluation framework, or dependency
- Real organisational, employee, or member data
- APIs, user interfaces, dashboards, analytics, orchestration, agents, LangChain, or LlamaIndex
- Gate 6 implementation

## Exit criteria

- [x] Gate 4 is formally accepted and its synchronized baseline is reverified
- [x] Gate 5 objective, dataset rules, measures, live boundary, exclusions, and decisions are
  documented before implementation
- [x] Twenty human-traced synthetic cases satisfy the documented category coverage
- [x] Dataset validation rejects malformed records and inconsistent ground truth
- [x] Evaluation data is proven excluded from ingestion, indexing, retrieval, and answer evidence
- [x] Retrieval and grounded-answer measures expose explicit numerators and denominators
- [x] Human-review models and templates remain separate from automated measures
- [x] JSON and Markdown reports and all fingerprints are deterministic
- [x] A read-only live evaluator records exact evidence once per case and requires `--run-live`
- [x] Comprehensive deterministic unit and integration tests pass
- [x] Ruff, dependency, imports, whitespace, credential, and scope checks pass
- [x] One local implementation commit contains only Gate 5 work
- [x] Gate 5 remains pending owner review and Gate 6 has not started

## Implementation evidence

The protected dataset contains exactly 20 cases: 12 current-policy cases covering all ten current
documents, three multi-document cases, three unsupported or adversarial cases, and two historical
Lending comparisons. Every declared document and page validates against the 11-document,
81-page, 194-chunk canonical corpus.

The complete offline suite passes 202 tests, with all three live tests skipped by default. Explicit
`--run-live --collect-only` selection discovers the Gate 3, Gate 4 and Gate 5 live tests without
executing them. The dataset, corpus and public-configuration fingerprints are respectively:

- `25ce198cc8e0761d0c1b116512e81de113ff9e9b44dd3f2ac586090c30413272`
- `a744c7cb9f3d8ab377a06a15bab6512315513df1a16d7575212230a849fe0006`
- `41a7741c895c61666d40ffb7ebec136f0c03e07683aba96837d3ea9b1064b577`

Gate 5 is **implemented pending owner review and a separately authorized live baseline**. It is not
formally accepted, and Gate 6 has not started.
