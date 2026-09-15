# NPCU GenAI Intelligence Lab - Coursework Reviewer Guide

This guide gives coursework trainers a reproducible route for reviewing and testing the NPCU
GenAI Intelligence Lab. The project is a deliberately small, production-style
retrieval-augmented generation (RAG) system for a **fictional** credit union. Its committed policy
corpus is entirely synthetic and contains no real member, employee, or organisational data.

> The fastest assessment route is to review the architecture, run the offline suite, and then use
> the Streamlit demonstration if suitable OpenAI and Pinecone credentials are available.

## What the project demonstrates

The implemented path:

1. parses 11 born-digital policy PDFs into page-aware application models;
2. creates 194 deterministic, page-bounded text chunks from 81 source pages;
3. embeds those chunks with OpenAI `text-embedding-3-small` at 1,536 dimensions;
4. retrieves them from a Pinecone Serverless dense cosine index;
5. excludes superseded policies from normal retrieval;
6. generates structured answers with OpenAI `gpt-5.6-terra`;
7. validates cited chunk IDs and builds authoritative document/page citations in application code;
8. returns an explicit insufficient-evidence response instead of an unsupported answer; and
9. evaluates retrieval and grounding separately over a protected 20-case synthetic baseline.

The Streamlit page is a thin coursework presentation layer over that accepted RAG path. It does
not contain retrieval, generation, citation, or evaluation business logic.

```text
Synthetic PDFs -> page-aware parsing -> deterministic chunks
                                             |
                                             v
Question -> OpenAI embedding -> Pinecone query (CURRENT by default)
                                             |
                                             v
                              ranked, page-aware evidence
                                             |
                                             v
                              grounded OpenAI generation
                                             |
                                             v
                         application-validated answer + citations
```

## Current scope and status

- Gates 0-5 are formally accepted.
- Gate 5.5, the coursework demonstration UI, is implemented and locally verified but remains
  pending owner acceptance.
- Gate 6 structured analytics is paused at a documentation-only design checkpoint.
- OCR, scanned PDFs, hybrid retrieval, reranking, authentication, deployment, agents, memory,
  GraphRAG, and production data controls are not implemented.
- The project is an educational synthetic-data demonstration, not a production credit-union
  service or proof of production accuracy, safety, or fairness.

## Repository tour

| Area | Location | What to inspect |
|---|---|---|
| Project overview | [`README.md`](README.md) | Setup, accepted gates, and live commands |
| Architecture | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Capability boundaries and end-to-end flows |
| Decisions | [`docs/DECISIONS.md`](docs/DECISIONS.md) | Concise architecture decisions |
| Detailed ADRs | [`docs/adr/`](docs/adr/) | Parsing, chunking, retrieval, generation, and evaluation rationale |
| Gate evidence | [`docs/GATE_LOG.md`](docs/GATE_LOG.md) | Acceptance and verification history |
| Current UI gate | [`docs/CURRENT_GATE.md`](docs/CURRENT_GATE.md) | Gate 5.5 scope, evidence, and exclusions |
| Synthetic corpus | [`data/raw/policies/`](data/raw/policies/) | Canonical PDFs used for retrieval |
| Corpus metadata | [`data/corpus_manifest.csv`](data/corpus_manifest.csv) | Version, status, ownership, and source metadata |
| Application package | [`src/cu_intelligence/`](src/cu_intelligence/) | Provider-independent models, services, and adapters |
| Automated tests | [`tests/`](tests/) | Unit, integration, safety, and opt-in live verification |

The editable Markdown policy sources explain how the synthetic PDFs were produced. Only the PDFs
under `data/raw/policies` are canonical retrieval input; source Markdown and evaluation files must
not be indexed.

## Route 0 - Review directly on GitHub

A trainer can review the design, source, synthetic corpus, tests, ADRs, and recorded gate evidence
directly in GitHub, beginning with this guide. A useful review order is `README.md`,
`docs/ARCHITECTURE.md`, ADRs 0004-0006, `docs/GATE_LOG.md`, then the application and test folders.

GitHub displays the repository but does not run the Streamlit application or expose the owner's
local `.env`. To execute tests or use the live interface, follow one of the clone-based routes
below.

## Route 1 - Review and test offline

This is the recommended first route. It requires no credentials, network calls, Pinecone index, or
provider cost. Deterministic test doubles exercise the application boundaries.

### 1. Clone and create a Python 3.12 environment

```powershell
git clone https://github.com/dheerajdendi-droid/NPCU-Gen-AI-Lab.git
cd NPCU-Gen-AI-Lab
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

On macOS or Linux, create the environment with `python3.12 -m venv .venv` and activate it with
`source .venv/bin/activate`.

### 2. Run the deterministic checks

```text
python -m pytest
python -m ruff check .
python -m pip check
python -c "import cu_intelligence; print('cu_intelligence import: OK')"
git diff --check
```

Plain `python -m pytest` always skips tests marked `live`, even when credentials exist. Credentials
alone never authorize external calls.

For a focused offline walkthrough of the complete grounded-answer boundary and the coursework UI
integration, run:

```text
python -m pytest tests/integration/test_grounded_generation.py -vv
python -m pytest tests/unit/test_coursework_ui.py -vv
```

These tests demonstrate retrieval-to-answer mapping, citation validation, insufficient-evidence
behavior, query-only UI composition, and request-local evidence isolation without calling OpenAI
or Pinecone.

## Route 2 - Run the live RAG demonstration

Live testing is optional. It sends synthetic questions and retrieved synthetic evidence to OpenAI
and Pinecone, requires accounts with available quota, and may incur cost. Do not submit personal,
member, employee, confidential, or real organisational data.

The repository does not contain credentials or a portable copy of the hosted vector index. A
reviewer should use their own provider project and a separate lab index/namespace. Do not share or
commit API keys.

### 1. Configure the accepted provider stack

The Pinecone index must use exactly:

| Setting | Required value |
|---|---|
| Vector type | dense |
| Dimensions | 1,536 |
| Similarity metric | cosine |
| Cloud | AWS |
| Region | `us-east-1` |
| Index name | reviewer-selected, environment-configured |
| Namespace | reviewer-selected, environment-configured |

Copy the tracked template to the ignored local settings file:

```powershell
Copy-Item .env.example .env
```

On macOS or Linux, use `cp .env.example .env`.

Then replace the placeholders in `.env` locally:

```dotenv
OPENAI_API_KEY=your-own-openai-key
PINECONE_API_KEY=your-own-pinecone-key
PINECONE_INDEX_NAME=your-own-index-name
PINECONE_NAMESPACE=your-own-namespace
```

Confirm that Git ignores the file before proceeding:

```text
git check-ignore .env
```

The command should print `.env`. Never commit or paste its values into an issue, report, or
terminal transcript.

### 2. Create/populate a fresh reviewer index

For a new reviewer-owned environment, the existing Gate 3 smoke test validates or creates the
configured index, embeds the synthetic corpus, and idempotently upserts all 194 deterministic
chunk IDs:

```text
python -m pytest --run-live tests/integration/test_live_semantic_retrieval.py -vv
```

This is the only route in this guide that may create an index or upsert vectors. Reviewers should
run it only after approving the associated OpenAI/Pinecone calls and cost. Re-running it targets
the same deterministic record IDs, but the project does not delete stale remote records.

If an administrator provides access to an already populated compatible index and namespace, skip
this provisioning step. The Streamlit application itself is query-only and will not create or
populate a missing index.

### 3. Launch the coursework interface

```text
python -m streamlit run src/cu_intelligence/ui/streamlit_app.py --server.address localhost
```

Open `http://localhost:8501` if the browser does not open automatically. Restart Streamlit after
changing `.env`, because provider clients are cached for the life of the application process.

Suggested checks:

| Question | Expected behavior |
|---|---|
| What is the current maximum Join and Borrow loan for a new member? | Answers from the current Lending and Affordability Policy and shows page provenance. |
| What should happen when a payroll processing failure causes loan payments to be missed? | Combines relevant current evidence from more than one policy when retrieved. |
| What is the policy for cryptocurrency investment? | Returns `INSUFFICIENT_EVIDENCE` with no fabricated sources. |

Exact answer wording and similarity scores can vary because the live providers are nondeterministic.
Assess whether each factual statement is supported by its displayed source, whether page numbers
are positive, and whether normal results avoid `SUPERSEDED` documents. The collapsed **View
retrieval details** section shows the exact ranked evidence supplied to generation.

### 4. Optional focused live verification

After the index contains the expected 194 vectors, the Gate 4 test performs six grounded-answer
checks without modifying the index:

```text
python -m pytest --run-live tests/integration/test_live_grounded_generation.py -vv
```

The Gate 5 test runs the 20-case read-only evaluation baseline:

```text
python -m pytest --run-live tests/integration/test_live_evaluation.py -vv -s
```

Do not use `--run-live` casually. The flag is the explicit authorization boundary for tests that
can contact providers and incur cost. The Gate 3 test can create/upsert remote state; the Gate 4
and Gate 5 tests use the existing index read-only.

## Evidence already recorded

The accepted live baseline used 11 documents, 81 pages, 194 chunks/vectors, and 20 evaluation
cases. It recorded:

- document Hit@1 of 14/17, Hit@3 of 16/17, and Hit@5/Hit@10 of 17/17;
- 25/26 expected page-evidence hits;
- answer-status agreement for 20/20 cases;
- all 42 citations referring to evidence supplied to generation;
- citation-document precision and recall of 23/25; and
- citation-free abstention for all three unsupported cases.

These measures demonstrate the tested mechanics and baseline behavior. They do not establish that
every answer is semantically complete or suitable for real financial decision-making. Human review
remains important, particularly for answer completeness and the less-than-perfect top-rank and page
metrics.

## Troubleshooting the live page

If the page reports that the policy service is temporarily unavailable, inspect the terminal that
launched Streamlit. The page intentionally hides provider exception details and credentials.
Typical causes are an unavailable or incompatible Pinecone index, an incorrect namespace, provider
authentication/billing/rate limits, network access, or unavailable OpenAI model access.

Check that:

1. all four `.env` settings are nonblank;
2. Streamlit was restarted after settings changed;
3. the configured index has the exact stack described above;
4. the configured namespace contains 194 vectors; and
5. both provider accounts have permission and available quota.

Do not post `.env`, API keys, complete provider responses, or secrets when sharing a traceback.

## Important limitations

- All data and evaluation cases are synthetic and deliberately small.
- `pypdf` supports born-digital PDFs only in this project; OCR and layout reconstruction are absent.
- Chunking uses page-bounded word windows, which can split headings, lists, and tables awkwardly.
- Retrieval is dense semantic search only; there is no lexical search, hybrid search, or reranker.
- Live ranking and generated prose may change behind provider model aliases.
- Citation validation proves that cited IDs came from retrieved evidence; human review is still
  required to judge whether prose accurately and completely represents that evidence.
- Normal retrieval excludes superseded documents, but the current UI has no historical-mode
  control.
- The Pinecone deployment is restricted to AWS `us-east-1` and is approved only for synthetic lab
  data. Its architecture must be reconsidered before any real data is used.
- The repository does not include deployment, authentication, persistence, or production
  monitoring.

For the detailed evidence trail, continue with the [gate log](docs/GATE_LOG.md),
[architecture decisions](docs/DECISIONS.md), and [ADRs](docs/adr/).
