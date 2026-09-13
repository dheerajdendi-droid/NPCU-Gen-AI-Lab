# Project state

- **Project:** NPCU GenAI Intelligence Lab
- **Current gate:** Gate 5.5 — Coursework Demonstration UI — implementation verified locally and
  pending owner review under CR-001
- **Current implementation:** Capabilities accepted through Gate 5 plus a thin Streamlit coursework
  interface over the existing grounded-answer service; Gate 6 analytics remains paused at its
  preserved design checkpoint
- **Implemented external AI technologies:** OpenAI `text-embedding-3-small`, Pinecone Serverless, and
  a live-verified OpenAI `gpt-5.6-terra` Responses adapter

Gate 0 and Gate 1 were formally accepted on 2026-09-10. Gate 2 was formally accepted on
2026-09-12. Gate 3 started on 2026-09-12 after the owner approved an OpenAI embedding and Pinecone
vector-index stack for the synthetic-only corpus. Manifest validation, PDF-to-chunk enrichment,
embedding and vector-index boundaries, idempotent indexing, metadata-filtered retrieval, and
provider-independent results are implemented. The live OpenAI/Pinecone path passed and Gate 3 was
formally accepted on 2026-09-12.

Current deterministic evidence: 202 tests pass over the 11-PDF, 81-page, 194-chunk corpus, with all
three live tests skipped by default even when credentials are configured. Ruff,
installed-dependency health, editable-package imports, whitespace, credential, and scope checks
pass. Live tests require the explicit `--run-live` option.

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

Gate 5 contains 20 validated cases with the required 12 current, three multi-document, three
unsupported/adversarial and two historical split. After direct authorization, the read-only live
baseline passed all 20 cases against the existing 194-vector namespace without remote mutation.
Document Hit@1 was 14/17, Hit@3 was 16/17, Hit@5 and Hit@10 were 17/17,
multi-document recall was 25/25, and page-evidence hits were 25/26. Answer status was correct for
20/20 cases, all 42 citations referenced supplied chunks, citation-document precision and recall
were both 23/25, all three unsupported cases abstained without citations, and both historical cases
handled version status correctly. There were no provider failures or structural grounding
violations.

The owner formally accepted Gate 5 on 2026-09-13. The baseline is deliberately small and synthetic;
its automated measures do not establish semantic correctness, completeness, production accuracy,
fairness, or safety. Human ratings remain pending, and live provider rankings and prose may change.

Gate 6 entered its documentation-only design checkpoint on 2026-09-13 from clean, synchronized
commit `1070ab5`. Its proposal was preserved at local commit `1f5d381`. No analytics dependency,
workbook, database, or implementation exists. CR-001 temporarily pauses that work and inserts Gate
5.5, a minimal Streamlit coursework interface over the accepted RAG path. Gate 6 will resume only
after Gate 5.5 review; Gate 7 has not started.

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
