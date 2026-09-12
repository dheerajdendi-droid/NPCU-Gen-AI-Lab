# NPCU GenAI Intelligence Lab

NPCU GenAI Intelligence Lab is a production-style learning project for a fictional credit
union. All credit-union data used by the project will be synthetic. The repository is both an
educational RAG project and an exercise in designing an enterprise GenAI architecture.

Development proceeds through explicit gates so that each layer is understood, tested, and
documented before the next is introduced. **Gate 0 — Foundation, Gate 1 — Document Ingestion and
Parsing, and Gate 2 — Deterministic Page-Aware Chunking are accepted.** Gate 3 metadata-aware
semantic retrieval is implemented locally, pending live-provider verification and formal owner
acceptance. Future capabilities described in the architecture are plans, not current features.

## Delivery outlook

The core MVP is planned to include document RAG, structured analytics, citations, evaluation,
and a usable interface. Its estimate is **approximately 10–16 weeks at three focused hours per
day**. The full planned demonstration, including optional advanced extensions, is estimated at
**approximately 22–34 weeks (roughly 5–8 months) at three focused hours per day**.

These are planning estimates, not guarantees. They assume roughly 15–20 focused hours per week
and include learning, debugging, testing, documentation, and architectural review. The core MVP
will be completed and stabilised before optional extensions such as graph retrieval, memory, and
voice are added.

## Current contents

Gate 0 provides a Python 3.12 `src`-layout package, provider-independent domain models, a small
environment-settings foundation, tests, lint configuration, and architecture and planning
documentation. Gate 1 adds page-aware text extraction for synthetic, born-digital PDFs using
`pypdf`. It preserves one-based page provenance and empty pages behind the ingestion boundary.
Gate 2 adds deterministic word-window chunking that keeps every chunk on one source page, uses
configurable maximum word counts and overlap, and assigns stable document-wide indexes and IDs.
Gate 3 validates canonical manifest metadata, enriches those chunks with document provenance,
embeds text behind an OpenAI boundary, upserts stable records behind a Pinecone boundary, and maps
metadata-filtered matches to provider-independent ranked evidence. Normal retrieval excludes
superseded policies; explicit historical retrieval can include them.

The version-controlled synthetic corpus baseline contains 11 PDFs, a manifest, explanatory
documentation, and matching editable Markdown sources. The PDFs are the canonical
retrieval input; source Markdown must not be indexed alongside them.

Gate 3 uses OpenAI text-embedding-3-small with explicit 1,536-dimensional output and a Pinecone
Serverless dense cosine index in AWS us-east-1. Index name, namespace, and credentials are
environment settings. This managed path is approved for synthetic data only. The project does not
perform OCR, model-specific chunking, LLM answer generation, RAG prompting, reranking, hybrid
search, APIs, or user interfaces.

## Local setup

Create and activate a Python 3.12 virtual environment:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

On macOS or Linux, activate it with `source .venv/bin/activate` instead.

Install the package and development tools:

```text
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the tests and lint checks:

```text
python -m pytest -m "not live"
python -m ruff check .
```

Normal tests use deterministic providers and require no network or credentials. To run the
explicit real-provider smoke test, configure OPENAI_API_KEY, PINECONE_API_KEY,
PINECONE_INDEX_NAME, and PINECONE_NAMESPACE in the environment or an ignored .env, then run
python -m pytest -m live.

That live test is the only path that may create or access the configured Pinecone index. It first
checks the approved dense/1,536/cosine/AWS/us-east-1 configuration, indexes the synthetic PDFs, and
runs the named Gate 3 smoke questions. Never commit real credential values.

See [the current gate](docs/CURRENT_GATE.md) and [project state](docs/PROJECT_STATE.md) before
starting any implementation work.
