# NPCU GenAI Intelligence Lab

NPCU GenAI Intelligence Lab is a production-style learning project for a fictional credit
union. All credit-union data used by the project will be synthetic. The repository is both an
educational RAG project and an exercise in designing an enterprise GenAI architecture.

Development proceeds through explicit gates so that each layer is understood, tested, and
documented before the next is introduced. **Gate 0 — Foundation, Gate 1 — Document Ingestion and
Parsing, and Gate 2 — Deterministic Page-Aware Chunking are accepted.** The project is awaiting
explicit Gate 3 initiation. Future capabilities described in the architecture are plans, not
current features.

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

The version-controlled synthetic corpus baseline contains 11 PDFs, a manifest, explanatory
documentation, and matching editable Markdown sources. The PDFs are the future canonical
retrieval input; source Markdown must not be indexed alongside them.

The project does not yet perform OCR, model-specific tokenization, embeddings, vector storage,
retrieval, model calls, or RAG. Gate 3 has not started.

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

See [the current gate](docs/CURRENT_GATE.md) and [project state](docs/PROJECT_STATE.md) before
starting any implementation work.
