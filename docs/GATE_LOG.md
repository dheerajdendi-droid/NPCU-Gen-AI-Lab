# Gate log

## Gate 0 — ACCEPTED

Formally accepted on **2026-09-10** after successful package-import, domain-model test, lint,
dependency, secret, and scope verification.

## Gate 1 — ACCEPTED

Started and formally accepted on **2026-09-10**. Acceptance retained the demonstrated evidence:
43 tests passed, Ruff passed, editable-package imports succeeded without a pytest path shortcut,
installed requirements were healthy, the synthetic born-digital PDF integration test passed, and
secret and post-Gate-1 technology scans were clean.

## Gate 2 — ACCEPTED

Started on **2026-09-10** and formally accepted on **2026-09-12**. Acceptance evidence: 74 tests
passed; Ruff, dependency health, editable-package import, diff, secret, and scope checks passed;
and the 11-document corpus smoke test produced 81 source pages and 194 chunks using
`max_words=300` and `overlap_words=50`, with document and page provenance intact.

## Gate 3 — ACCEPTED

Started on **2026-09-12** after Gate 2 baseline verification. The owner approved OpenAI
`text-embedding-3-small` with explicit 1,536-dimensional output and a Pinecone Serverless dense
cosine index in AWS `us-east-1` for synthetic-only data.

Local implementation evidence on **2026-09-12**: 130 deterministic tests passed with one explicitly
marked live test deselected; the complete 11-PDF corpus produced 81 pages and 194 enriched chunks;
repeat indexing retained 194 stable IDs; named policy queries returned provenance-bearing evidence;
and current-only versus explicit superseded retrieval passed. Ruff, dependency health, editable
imports, whitespace, secret, and scope checks passed.

Formally accepted on **2026-09-12** after the real-provider test passed. The configured Pinecone
Serverless index was ready with dense vectors, 1,536 dimensions, cosine similarity, AWS
`us-east-1`, and exactly 194 records in the configured namespace. Every named live query found
its expected current document with page provenance: member eligibility rank 1/page 3, lending
affordability rank 1/page 5, vulnerable members rank 6/page 5, and supplier change rank 1/page 4.
An explicit historical query found both Lending v4.0 and superseded v3.1.

The live test emitted two non-functional Windows pytest-cache permission warnings. The final
deterministic suite still passed 130 tests, and all final lint, dependency, import, whitespace,
secret, and scope checks passed. Gate 4 has not started.

## Gate 4 — ACCEPTED

Started on **2026-09-12** after the accepted Gate 3 baseline was confirmed clean and synchronized.
The deterministic baseline passed 130 tests, Ruff, dependency health, editable imports, and
whitespace checks. A read-only provider check confirmed that the existing approved Pinecone index
was ready and its configured namespace still contained exactly 194 vectors; nothing was rebuilt.

The implementation adds one stateless OpenAI Responses adapter for `gpt-5.6-terra` with Structured
Outputs, low reasoning effort, `store=false`, and no tools. A provider-independent service retrieves
ten chunks, validates the structured draft against the exact evidence IDs, constructs authoritative
page citations, supports explicit historical retrieval, and abstains safely. The final deterministic
suite contains 169 passing non-live tests and two deselected live tests.

After direct authorization, the focused live Gate 4 test passed on **2026-09-12**. It inspected the
existing namespace's 194-vector count, issued six query embeddings and read-only Pinecone queries,
and generated six `gpt-5.6-terra` Structured Outputs without rebuilding or changing the index. The
four current-policy questions produced grounded answers with application-owned positive page
citations; the unsupported question abstained without citations; and the historical Lending answer
cited current v4.0 and superseded v3.1 with explicit `SUPERSEDED` labelling. Generation used 24,374
input tokens and 1,889 output tokens.

Before acceptance, pytest was changed so credentials alone cannot activate live tests: `--run-live`
is now required. The complete default suite passed 169 deterministic tests and skipped both live
tests. Explicit live collection selected both tests without executing them. Ruff, dependency,
editable-import, whitespace, credential, and scope checks passed. The owner formally accepted Gate 4
on **2026-09-12**. Gate 5 has not started.

## Gate 5 — IMPLEMENTED, PENDING OWNER REVIEW AND LIVE BASELINE

Started on **2026-09-12** from clean, synchronized commit `0126705`. The accepted Gate 4 baseline
was reproduced with 169 deterministic tests passing and both live tests skipped. Gate 5 will add a
local provider-independent evaluation harness, twenty protected synthetic cases, separate retrieval
and answer measures, explicit zero denominators, deterministic reports and fingerprints, distinct
human review, and an authorization-gated read-only live test. Retrieval and generation tuning are
excluded while the baseline is established. Gate 5 is not accepted, and Gate 6 has not started.

Implementation completed locally on **2026-09-12** with 20 human-traced synthetic cases: 12
current-policy cases covering every current document, three multi-document cases, three unsupported
or adversarial cases, and two current-versus-superseded Lending comparisons. The harness validates
dataset provenance, calculates separate retrieval and grounded-answer measures, preserves zero
denominators, renders deterministic JSON and Markdown, produces three SHA-256 fingerprints, and
keeps 0–2 human ratings separate from automated results.

The complete deterministic suite passes 202 tests and skips all three live tests by default. The
Gate 5 live evaluator is collected only with `--run-live`, records one retrieval per case, and
cannot create, upsert, update or delete Pinecone data. It has not been executed. Gate 5 remains
pending owner review and separately authorized live evaluation; Gate 6 has not started.
