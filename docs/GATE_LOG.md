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

## Gate 5 — ACCEPTED

Started on **2026-09-12** from clean, synchronized commit `0126705`. The accepted Gate 4 baseline
was reproduced with 169 deterministic tests passing and both live tests skipped. Gate 5 set out to
add a local provider-independent evaluation harness, twenty protected synthetic cases, separate
retrieval and answer measures, explicit zero denominators, deterministic reports and fingerprints,
distinct human review, and an authorization-gated read-only live test. Retrieval and generation
tuning were excluded while the baseline was established. At that point Gate 5 was not accepted,
and Gate 6 had not started.

Implementation completed locally on **2026-09-12** with 20 human-traced synthetic cases: 12
current-policy cases covering every current document, three multi-document cases, three unsupported
or adversarial cases, and two current-versus-superseded Lending comparisons. The harness validates
dataset provenance, calculates separate retrieval and grounded-answer measures, preserves zero
denominators, renders deterministic JSON and Markdown, produces three SHA-256 fingerprints, and
keeps 0–2 human ratings separate from automated results.

The complete deterministic suite passes 202 tests and skips all three live tests by default. The
Gate 5 live evaluator is collected only with `--run-live`, records one retrieval per case, and
cannot create, upsert, update or delete Pinecone data.

After direct authorization, the live baseline passed on **2026-09-13** against the existing
194-vector Pinecone namespace. All 20 cases completed without provider failures or structural
grounding violations. Document Hit@1, Hit@3, Hit@5 and Hit@10 were respectively 14/17, 16/17,
17/17 and 17/17; multi-document recall was 25/25; and page evidence was 25/26. Answer status was
correct for 20/20 cases, all 42 citations referenced supplied chunks, citation-document precision
and recall were both 23/25, all three unsupported cases abstained citation-free, and both historical
cases handled current and superseded status correctly. The run made 20 query-embedding calls, 20
read-only Pinecone searches and 20 stateless generation calls; it performed no remote mutation.

The owner formally accepted Gate 5 on **2026-09-13**. Acceptance retains the observed misses and
the limits of a small synthetic dataset, structural automated scoring, pending human review,
provider variability, page-bounded word-window retrieval, and the absence of reranking, hybrid
search or threshold calibration. Gate 6 has not started.

## Gate 6 — DESIGN CHECKPOINT

Started on **2026-09-13** after confirming Gate 5 was documented, committed, clean, and synchronized
at `1070ab5`. The accepted baseline was reproduced with 202 deterministic tests passing, all three
live tests skipped, and Ruff passing.

The proposed contract defines a synthetic Excel workbook, exact sheets and relational rules,
centralized deterministic metrics, a hand-reconciled July/August arrears scenario, pre-aggregation
rules that prevent fact multiplication, provider-independent analytical results, openpyxl workbook
validation, and derived DuckDB state. ADR 0007 is proposed. No dependency, workbook, database, or
analytics implementation has been added. Work is paused for owner approval, and Gate 7 has not
started.

The design checkpoint was preserved in local commit `1f5d381`. CR-001 pauses Gate 6 before owner
approval or implementation; it does not mark Gate 6 complete.

## Gate 5.5 — ACCEPTED

Started on **2026-09-13** under CR-001 to provide a lightweight Streamlit coursework demonstration
before Gate 6 analytics implementation. The presentation layer reuses the accepted semantic
retrieval and grounded-answer services, retains authoritative citations and abstention, and opens
the existing Pinecone index through a query-only composition. Gate 6 remains paused and Gate 7 has
not started.

Local verification on **2026-09-13** passed 206 deterministic tests with three live tests skipped,
plus Ruff, dependency, import, and whitespace checks. The Streamlit page rendered correctly, kept
blank input local, displayed authoritative citations and exact retrieval details, and returned the
existing insufficient-evidence state without sources. Four authorized UI questions covered current
policy, explicit version support, cross-document payroll-failure handling, and an unsupported
cryptocurrency topic. All provider activity was query-only.

Subsequent owner review identified one material concurrency blocker: the globally cached coursework
service retained mutable evidence-recorder state. The implementation was changed so every `ask()`
call owns its recorder and grounded-answer coordinator. A deterministic two-thread test forces an
interleaving that would have exposed the original crossover and verifies both answers retain their
own evidence and citations. Post-fix verification passed 207 deterministic tests with three live
tests skipped, plus Ruff, dependency, import, and whitespace checks.

Acceptance-day offline verification on **2026-09-19** again passed 207 deterministic tests while
skipping all three live tests by default. Ruff, installed-dependency health, editable-package
import, whitespace, tracked-credential, documentation-link, and Gate 6 scope scans passed. No
OpenAI or Pinecone call was made, and no Gate 6 analytics dependency or implementation was found.

The owner formally accepted Gate 5.5 on **2026-09-19**. Acceptance retains the synthetic-only data
boundary, current-policy default, query-only Pinecone composition, generic user-facing provider
errors, and the documented limitations of the lightweight coursework interface. Gate 6 returns to
its preserved design-approval checkpoint; no Gate 6 implementation or Gate 7 work has started.
