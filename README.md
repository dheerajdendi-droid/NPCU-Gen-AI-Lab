# NPCU GenAI Intelligence Lab

NPCU GenAI Intelligence Lab is a production-style learning project for a fictional credit
union. All credit-union data used by the project will be synthetic. The repository is both an
educational RAG project and an exercise in designing an enterprise GenAI architecture.

> **Coursework reviewers:** Start with the
> [coursework reviewer guide](COURSEWORK_README.md) for a repository tour, an offline assessment
> route, and an optional live end-to-end RAG demonstration using reviewer-owned credentials.

Development proceeds through explicit gates so that each layer is understood, tested, and
documented before the next is introduced. **Gates 0–5 are accepted.** Gate 5's protected 20-case
evaluation passed deterministic verification and a directly authorized read-only live baseline
before owner acceptance on 2026-09-13. CR-001 inserts Gate 5.5, a minimal Streamlit coursework UI,
while Gate 6 analytics remains paused at its preserved documentation-only design checkpoint. No
analytics dependency, workbook, database, or implementation has been added.

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

Gate 5 adds a protected 20-case synthetic evaluation dataset and a provider-independent local
harness. It measures retrieval rankings separately from answer status, citation validity,
provenance and version handling; renders deterministic JSON and Markdown; provides separate 0–2
human-review templates; and fingerprints the dataset, corpus and public configuration. It does not
tune retrieval or prompting and does not use an LLM judge.

Gate 5.5 adds a thin Streamlit presentation layer. It sends one question through the accepted
grounded-answer service, displays application-owned citations and the existing insufficient-evidence
outcome, and can show the exact ranked evidence supplied to generation. Its live Pinecone surface
supports queries only and cannot create or upsert records.

The version-controlled synthetic corpus baseline contains 11 PDFs, a manifest, explanatory
documentation, and matching editable Markdown sources. The PDFs are the canonical
retrieval input; source Markdown must not be indexed alongside them.

Gate 3 uses OpenAI text-embedding-3-small with explicit 1,536-dimensional output and a Pinecone
Serverless dense cosine index in AWS us-east-1. Index name, namespace, and credentials are
environment settings. This managed path is approved for synthetic data only. The project does not
perform OCR, model-specific chunking, reranking, hybrid search, APIs, general orchestration, or Gate
6 analytics functionality.

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

The Gate 5 live baseline is also separate and keeps Pinecone read-only. It must not run without
direct authorization for its 20 questions, retrieved synthetic evidence, provider cost, and remote
queries:

```text
python -m pytest --run-live tests/integration/test_live_evaluation.py -vv -s
```

## Running the coursework demo

Configure `OPENAI_API_KEY`, `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, and
`PINECONE_NAMESPACE` in the environment or ignored `.env`, then run:

```text
python -m streamlit run src/cu_intelligence/ui/streamlit_app.py --server.address localhost
```

The demo sends policy questions and retrieved synthetic evidence to the accepted OpenAI and
Pinecone services and may incur provider cost. It demonstrates semantic policy retrieval,
current-policy filtering, grounded generation, application-owned page citations, and explicit
insufficient-evidence behavior. It does not implement hybrid search or reranking.

See [the current gate](docs/CURRENT_GATE.md) and [project state](docs/PROJECT_STATE.md) before
starting any implementation work.
