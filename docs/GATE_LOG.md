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
