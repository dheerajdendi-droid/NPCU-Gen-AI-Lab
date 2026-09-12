# CU RAG Synthetic Lab

This corpus was created for an educational RAG / GraphRAG / structured-data analytics project.

Organisation: North Pennine Community Credit Union (NPCU)

IMPORTANT: Every document and every data record in this package is fictional.

## Why the corpus is intentionally non-trivial

The policy corpus includes:
- long multi-section documents
- headings, prose and tables
- overlapping terminology across documents
- cross-domain concepts such as payroll, vulnerability, lending and complaints
- one deliberately superseded Lending Policy (v3.1) alongside the current v4.0
- rules with numerical thresholds suitable for exact-search and hybrid-search testing
- operational and governance thresholds that can later be linked to synthetic data

## Evaluation-data safety

No planted evaluation ground truth is included in the current corpus baseline. If a future
`_evaluation_do_not_index` directory or other ground-truth package is added, it must never be
indexed, embedded, uploaded with the retrieval corpus, or used as source content.

## Suggested learning order

1. Parse one PDF.
2. Compare page/paragraph/fixed-token/structure-aware chunking.
3. Add chunk metadata: title, version, status, effective date, section and page.
4. Embed and index in Pinecone.
5. Test semantic retrieval.
6. Add lexical/hybrid retrieval and reranking.
7. Test version-aware filtering.
8. Build a Neo4j knowledge graph for rules, products, processes and dependencies.
9. Add structured operational data querying.
10. Combine data analysis + policy RAG + graph context into management intelligence.

The operational workbook is created separately as `NPCU_Synthetic_Operational_Data.xlsx`.
