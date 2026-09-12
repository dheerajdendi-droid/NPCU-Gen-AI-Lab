# ADR 0006: Provider-independent local evaluation baseline

## Status

Accepted for Gate 5 implementation and implemented locally on 2026-09-12. Gate 5 was formally
accepted on 2026-09-13 after deterministic verification and the directly authorized read-only live
baseline passed.

## Context

Gates 3 and 4 provide accepted semantic retrieval and grounded answers, but a small smoke test does
not quantify their behavior over a representative set of questions. Retrieval quality and answer
quality fail differently and must be measured separately. Evaluation ground truth must also remain
outside the canonical corpus so expected answers cannot leak into embeddings or generation
evidence.

The hosted OpenAI Evals API is not selected because its announced shutdown makes it unsuitable as
the project's baseline. Adding an evaluation framework would also obscure the metric mechanics the
Gate is intended to teach.

## Decision

Implement a local, version-controlled evaluation harness with the Python standard library,
Pydantic, and the existing application contracts. Keep evaluation models, scores, reports, and
fingerprints provider-independent. Use the accepted OpenAI and Pinecone adapters only behind their
existing boundaries in an explicitly opted-in live integration test.

Store twenty synthetic human-authored cases under `data/_evaluation_do_not_index/`. Validate every
document ID and expected page against the canonical built corpus. The canonical corpus builder
continues to read only `data/corpus_manifest.csv` and `data/raw/policies`; regression coverage must
prove evaluation questions and reference facts never reach parsing, chunking, embedding, indexing,
retrieval evidence, or generation evidence.

Retrieve each case exactly once at depth ten. Score document hits at 1, 3, 5, and 10; reciprocal
rank; multi-document recall; page evidence; and required, forbidden, status, rank, and duplicate
violations. Then generate from that recorded evidence and separately score expected answer status,
citation chunk validity, citation document precision and recall, unsupported citation-free behavior,
historical labels, version metadata, and structural grounding.

Represent every ratio as numerator, denominator, and nullable rounded value. A zero denominator is
explicitly not applicable; it is never hidden or coerced to a misleading zero or one. Automated
measures do not judge semantic correctness or completeness, so the report includes a separate 0–2
human-review template. Do not add an LLM judge.

Render canonical JSON and readable Markdown deterministically. Fingerprint the validated dataset,
corpus, and public evaluation configuration with SHA-256 over canonical JSON. Do not fingerprint
credentials or provider deployment identifiers that could reveal configuration.

The live evaluator uses the existing 194-vector namespace read-only. Pytest requires `--run-live`,
and a direct owner authorization is still required before execution. No index creation, upsert,
update, deletion, prompt logging, or raw provider-object retention is permitted.

## Alternatives considered

- A hosted evaluation API was rejected because the selected service is being shut down and would
  add external lifecycle risk.
- An evaluation framework was rejected because the required metrics are small and transparent with
  existing dependencies.
- An LLM-as-judge was rejected because it adds cost, nondeterminism, and a second model-validation
  problem before human review establishes a baseline.
- Tuning retrieval or prompting during baseline creation was rejected because it would move the
  system being measured and conceal accepted Gate 3 or Gate 4 limitations.
- Re-querying retrieval for answer evaluation was rejected because it could score different
  evidence and doubles live cost.

## Consequences

The baseline will be reproducible, reviewable, and independent of provider response types. Metric
math and zero denominators remain visible, while human judgment is clearly distinguished from
automated structural checks. The protected evaluation directory reduces leakage risk.

The dataset is small, synthetic, and manually authored. Document relevance and page expectations
can still be incomplete, semantic answer correctness still requires human review, and live rankings
or prose can change behind provider model aliases. The baseline therefore supports learning and
regression detection; it does not demonstrate production accuracy, fairness, or safety.

The accepted live baseline makes those limitations measurable: Document Hit@1 was 14/17, Hit@3
was 16/17, page evidence was 25/26, and citation-document precision and recall were both 23/25.
Perfect Hit@5 and Hit@10, multi-document recall, answer-status accuracy, chunk-citation validity,
unsupported abstention, and historical status handling do not remove the need for human semantic
review or justify tuning within Gate 5.
