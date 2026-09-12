# Project state

- **Project:** NPCU GenAI Intelligence Lab
- **Current gate:** Gate 5 — Retrieval and Grounded Answer Evaluation — implemented pending owner
  review and a separately authorized live baseline
- **Current implementation:** Capabilities accepted through Gate 4 plus a provider-independent local
  evaluation harness, protected synthetic cases, deterministic metrics, human-review templates,
  reports, and fingerprints
- **Implemented external AI technologies:** OpenAI `text-embedding-3-small`, Pinecone Serverless, and
  a live-verified OpenAI `gpt-5.6-terra` Responses adapter

Gate 0 and Gate 1 were formally accepted on 2026-09-10. Gate 2 was formally accepted on
2026-09-12. Gate 3 started on 2026-09-12 after the owner approved an OpenAI embedding and Pinecone
vector-index stack for the synthetic-only corpus. Manifest validation, PDF-to-chunk enrichment,
embedding and vector-index boundaries, idempotent indexing, metadata-filtered retrieval, and
provider-independent results are implemented. The live OpenAI/Pinecone path passed and Gate 3 was
formally accepted on 2026-09-12.

Current deterministic evidence: 169 tests pass over the 11-PDF, 81-page, 194-chunk corpus, with the
two live tests skipped by default even when credentials are configured. Ruff, installed-dependency
health, editable-package imports, whitespace, credential, and scope checks pass. Live tests now
require the explicit `--run-live` option.

Gate 4 started on 2026-09-12. Its deterministic implementation passes 169 non-live tests, including
one complete offline grounded-answer integration test. The approved OpenAI generation path uses
`gpt-5.6-terra`, Responses Structured Outputs, low reasoning effort, disabled response storage, and
no tools. Answer citations are validated and built from exact Gate 3 evidence, current policy is the
default, historical retrieval is explicit, and empty evidence bypasses generation.

After direct authorization, the focused Gate 4 live test passed all six scenarios against the
existing 194-vector Pinecone namespace without indexing or modifying remote state. Current-policy
answers cited application-owned page provenance, the unsupported question returned insufficient
evidence without citations, and the historical Lending comparison cited both current v4.0 and
superseded v3.1 with explicit status labelling. The owner formally accepted Gate 4 on 2026-09-12.

Gate 5 started on 2026-09-12 from clean, synchronized commit `0126705`. Its accepted scope is a
local provider-independent evaluation harness, twenty protected synthetic cases, separate retrieval
and grounded-answer measures, deterministic reports and fingerprints, distinct human review, and
one explicitly authorized read-only live baseline. No retrieval or generation tuning, hosted eval
service, LLM judge, framework, or new dependency is planned. Gate 6 has not started.

Gate 5 implementation now contains 20 validated cases with the required 12 current, three
multi-document, three unsupported/adversarial and two historical split. The complete deterministic
suite passes 202 tests and skips three live tests by default. The read-only Gate 5 live test is
implemented but has not run; it requires direct authorization and `--run-live`. Gate 5 is not
formally accepted, and Gate 6 has not started.

## Planned future capability areas

- Retrieval and answer evaluation
- Structured analytics
- Graph retrieval
- External retrieval
- Memory
- Orchestration
- Evaluation
- Voice

These are planned capability areas and have not been implemented.

## Estimated delivery

- **Core MVP:** approximately 10–16 weeks at three focused hours per day
- **Full planned demonstration:** approximately 22–34 weeks at three focused hours per day

These figures are planning estimates, not guarantees. They assume approximately 15–20 focused
hours per week and include learning, testing, debugging, documentation, and architectural review.
The core MVP is prioritised before optional extensions.
