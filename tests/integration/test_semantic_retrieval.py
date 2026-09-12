"""Local end-to-end Gate 3 integration test over the synthetic PDF corpus."""

import math
import re
from collections.abc import Sequence
from pathlib import Path

from cu_intelligence.domain import DocumentStatus, VectorMatch, VectorRecord
from cu_intelligence.ingestion import build_corpus
from cu_intelligence.retrieval import (
    RETRIEVAL_SMOKE_QUESTIONS,
    VECTOR_DIMENSIONS,
    SemanticRetrievalService,
)

_KEYWORDS = (
    "eligibility",
    "eligible",
    "evidence",
    "identity",
    "residency",
    "affordability",
    "affordable",
    "income",
    "lending",
    "loan",
    "repayment",
    "vulnerable",
    "vulnerability",
    "complaint",
    "support",
    "supplier",
    "change",
    "technology",
    "management",
)


class DeterministicKeywordEmbeddings:
    """Small deterministic test double using keyword counts, padded to 1,536."""

    dimensions = VECTOR_DIMENSIONS

    def embed(self, texts: Sequence[str]) -> list[tuple[float, ...]]:
        results: list[tuple[float, ...]] = []
        for text in texts:
            words = set(re.findall(r"[a-z]+", text.casefold()))
            words.update(word[:-1] for word in tuple(words) if word.endswith("s"))
            values = [float(keyword in words) for keyword in _KEYWORDS]
            values.extend([0.0] * (self.dimensions - len(values)))
            results.append(tuple(values))
        return results


class DeterministicMemoryIndex:
    """Idempotent in-memory cosine index used only by normal tests."""

    dimensions = VECTOR_DIMENSIONS

    def __init__(self) -> None:
        self.records: dict[str, VectorRecord] = {}

    def upsert(self, records: Sequence[VectorRecord]) -> int:
        for record in records:
            self.records[record.record_id] = record
        return len(records)

    def query(
        self,
        vector: Sequence[float],
        *,
        top_k: int,
        status_filter: DocumentStatus | None,
    ) -> list[VectorMatch]:
        matches = [
            VectorMatch(
                record_id=record.record_id,
                score=_cosine_similarity(vector, record.values),
                metadata=record.metadata,
            )
            for record in self.records.values()
            if status_filter is None
            or record.metadata["status"] == status_filter.value
        ]
        return sorted(matches, key=lambda item: (-item.score, item.record_id))[:top_k]


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / (
        left_norm * right_norm
    )


def test_canonical_pdf_corpus_to_metadata_aware_retrieval() -> None:
    root = Path(__file__).parents[2]
    corpus = build_corpus(
        root / "data" / "corpus_manifest.csv",
        pdf_directory=root / "data" / "raw" / "policies",
    )
    index = DeterministicMemoryIndex()
    service = SemanticRetrievalService(DeterministicKeywordEmbeddings(), index)

    first = service.index_corpus(corpus)
    second = service.index_corpus(corpus)

    assert first == second
    assert first.document_count == 11
    assert first.chunk_count == 194
    assert first.upserted_count == 194
    assert len(index.records) == 194
    assert all(
        record.record_id == record.metadata["chunk_id"]
        for record in index.records.values()
    )
    assert all(record.metadata["page_number"] >= 1 for record in index.records.values())

    for question in RETRIEVAL_SMOKE_QUESTIONS:
        results = service.retrieve(question.query, top_k=10)
        assert results
        assert question.expected_document_id in {
            result.document_id for result in results
        }
        assert all(result.document_status is DocumentStatus.CURRENT for result in results)
        assert all(result.synthetic for result in results)

    normal_lending = service.retrieve(
        "lending affordability income repayment",
        top_k=50,
    )
    historical_lending = service.retrieve(
        "lending affordability income repayment",
        top_k=50,
        include_superseded=True,
    )

    assert all(
        result.document_status is not DocumentStatus.SUPERSEDED
        for result in normal_lending
    )
    assert {
        (result.document_id, result.version, result.document_status)
        for result in historical_lending
        if result.title == "Lending and Affordability Policy"
    } >= {
        (
            "02_Lending_Affordability_Policy_v4.0",
            "4.0",
            DocumentStatus.CURRENT,
        ),
        (
            "02A_Lending_Affordability_Policy_v3.1_SUPERSEDED",
            "3.1",
            DocumentStatus.SUPERSEDED,
        ),
    }
