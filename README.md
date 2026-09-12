# NPCU GenAI Intelligence Lab

NPCU GenAI Intelligence Lab is a production-style learning project for a fictional credit
union. All credit-union data used by the project will be synthetic. The repository is both an
educational RAG project and an exercise in designing an enterprise GenAI architecture.

Development proceeds through explicit gates so that each layer is understood, tested, and
documented before the next is introduced. **Gates 0–3 are accepted.** Gate 4 grounded answer
generation and page citations are implemented with deterministic verification and await focused
live verification and owner review. Future capabilities described in the architecture are plans,
not current features.

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

Gate 4 adds one grounded-answer service and one provider-independent generation boundary. The
OpenAI adapter uses `gpt-5.6-terra` through Responses Structured Outputs with low reasoning effort,
disabled response storage, and no model tools. The application validates every model-selected chunk
ID against the exact top-ten retrieval set, builds page citations from RetrievalResult metadata,
labels superseded evidence, and produces deterministic readable output. Empty evidence bypasses the
model and returns an explicit insufficient-evidence result.

The version-controlled synthetic corpus baseline contains 11 PDFs, a manifest, explanatory
documentation, and matching editable Markdown sources. The PDFs are the canonical
retrieval input; source Markdown must not be indexed alongside them.

Gate 3 uses OpenAI text-embedding-3-small with explicit 1,536-dimensional output and a Pinecone
Serverless dense cosine index in AWS us-east-1. Index name, namespace, and credentials are
environment settings. This managed path is approved for synthetic data only. The project does not
perform OCR, model-specific chunking, reranking, hybrid search, APIs, user interfaces, general
orchestration, or Gate 5 evaluation.

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
python -m pytest
python -m ruff check .
```

Normal tests use deterministic providers and require no network or credentials. Pytest skips every
test marked `live` unless the command includes `--run-live`; credentials alone never opt in. To run
the Gate 3 real-provider smoke test, configure OPENAI_API_KEY, PINECONE_API_KEY,
PINECONE_INDEX_NAME, and PINECONE_NAMESPACE in the environment or an ignored .env, obtain the
required authorization, then run:

```text
python -m pytest --run-live tests/integration/test_live_semantic_retrieval.py -vv
```

That live test is the tracked provider-verification path. It first checks the approved
dense/1,536/cosine/AWS/us-east-1 configuration, indexes the synthetic PDFs, and runs the named
Gate 3 smoke questions. Never commit real credential values.

Gate 3 acceptance verified an index containing 194 vectors in the configured namespace and found
the expected current document for every named smoke question with one-based page provenance.

The focused Gate 4 live test is separate so it does not re-index the corpus:

```text
python -m pytest --run-live tests/integration/test_live_grounded_generation.py -vv
```

It requires direct authorization to send the synthetic retrieved evidence and questions to OpenAI
and Pinecone. It never recreates, deletes, reconfigures, or bulk-upserts the accepted index.

See [the current gate](docs/CURRENT_GATE.md) and [project state](docs/PROJECT_STATE.md) before
starting any implementation work.
