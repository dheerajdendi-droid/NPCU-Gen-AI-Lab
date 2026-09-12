"""Tests for provider-independent indexing and retrieval behavior."""

from datetime import date
from typing import Any

import pytest

from cu_intelligence.domain import (
    CorpusBuild,
    CorpusChunk,
    CorpusDocument,
    DocumentStatus,
    VectorMatch,
    VectorRecord,
)
from cu_intelligence.retrieval import (
    VECTOR_DIMENSIONS,
    DimensionMismatchError,
    EmbeddingProviderError,
    SemanticRetrievalService,
    VectorIndexError,
    build_vector_records,
)


def document(
    *,
    document_id: str = "policy-current",
    version: str = "4.0",
    status: DocumentStatus = DocumentStatus.CURRENT,
) -> CorpusDocument:
    return CorpusDocument(
        document_id=document_id,
        filename=f"{document_id}.pdf",
        title="Lending and Affordability Policy",
        version=version,
        status=status,
        effective_date=date(2026, 6, 1),
        owner="Head of Lending",
        synthetic=True,
    )


def chunk(
    source: CorpusDocument,
    *,
    chunk_id: str | None = None,
    text: str = "Synthetic lending affordability evidence.",
) -> CorpusChunk:
    return CorpusChunk(
        chunk_id=chunk_id or f"{source.document_id}:p0001:c000000",
        document_id=source.document_id,
        text=text,
        chunk_index=0,
        page_number=1,
        title=source.title,
        version=source.version,
        document_status=source.status,
        effective_date=source.effective_date,
        owner=source.owner,
        source_filename=source.filename,
        synthetic=True,
    )


class FixedEmbeddingProvider:
    dimensions = VECTOR_DIMENSIONS

    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[tuple[float, ...]]:
        self.calls.append(list(texts))
        if self.error is not None:
            raise self.error
        return [tuple([0.1] * self.dimensions) for _ in texts]


class MemoryVectorIndex:
    dimensions = VECTOR_DIMENSIONS

    def __init__(self) -> None:
        self.records: dict[str, VectorRecord] = {}
        self.query_calls: list[dict[str, Any]] = []
        self.matches: list[VectorMatch] = []

    def upsert(self, records: list[VectorRecord]) -> int:
        for record in records:
            self.records[record.record_id] = record
        return len(records)

    def query(
        self,
        vector: tuple[float, ...],
        *,
        top_k: int,
        status_filter: DocumentStatus | None,
    ) -> list[VectorMatch]:
        self.query_calls.append(
            {
                "vector": vector,
                "top_k": top_k,
                "status_filter": status_filter,
            }
        )
        return [
            match
            for match in self.matches
            if status_filter is None
            or match.metadata.get("status") == status_filter.value
        ][:top_k]


def match(source: CorpusDocument, *, score: float, chunk_id: str) -> VectorMatch:
    return VectorMatch(
        record_id=chunk_id,
        score=score,
        metadata={
            "document_id": source.document_id,
            "text": "Synthetic evidence.",
            "page_number": 2,
            "title": source.title,
            "version": source.version,
            "status": source.status.value,
            "effective_date": source.effective_date.isoformat(),
            "owner": source.owner,
            "source_filename": source.filename,
            "synthetic": True,
        },
    )


def test_vector_record_contains_stable_id_and_complete_primitive_provenance() -> None:
    source = document()
    source_chunk = chunk(source)

    record = build_vector_records(
        [source_chunk],
        [[0.2] * VECTOR_DIMENSIONS],
    )[0]

    assert record.record_id == source_chunk.chunk_id
    assert record.metadata == {
        "chunk_id": source_chunk.chunk_id,
        "document_id": "policy-current",
        "text": "Synthetic lending affordability evidence.",
        "chunk_index": 0,
        "page_number": 1,
        "title": "Lending and Affordability Policy",
        "version": "4.0",
        "status": "CURRENT",
        "effective_date": "2026-06-01",
        "owner": "Head of Lending",
        "source_filename": "policy-current.pdf",
        "synthetic": True,
        "embedding_model": "text-embedding-3-small",
        "embedding_dimensions": 1536,
    }
    assert all(
        isinstance(value, str | int | float | bool)
        for value in record.metadata.values()
    )


def test_identical_reindexing_updates_same_record_without_duplicates() -> None:
    source = document()
    corpus = CorpusBuild(documents=(source,), chunks=(chunk(source),))
    index = MemoryVectorIndex()
    service = SemanticRetrievalService(FixedEmbeddingProvider(), index)

    first = service.index_corpus(corpus)
    second = service.index_corpus(corpus)

    assert first == second
    assert first.document_count == 1
    assert first.chunk_count == 1
    assert first.upserted_count == 1
    assert list(index.records) == ["policy-current:p0001:c000000"]


def test_current_lending_is_default_and_superseded_is_explicit() -> None:
    current = document()
    superseded = document(
        document_id="policy-superseded",
        version="3.1",
        status=DocumentStatus.SUPERSEDED,
    )
    index = MemoryVectorIndex()
    index.matches = [
        match(
            superseded,
            score=0.95,
            chunk_id="policy-superseded:p0001:c000000",
        ),
        match(current, score=0.90, chunk_id="policy-current:p0001:c000000"),
    ]
    service = SemanticRetrievalService(FixedEmbeddingProvider(), index)

    normal = service.retrieve("How is affordability assessed?", top_k=10)
    historical = service.retrieve(
        "How is affordability assessed?",
        top_k=10,
        include_superseded=True,
    )

    assert [(result.version, result.document_status) for result in normal] == [
        ("4.0", DocumentStatus.CURRENT)
    ]
    assert {(result.version, result.document_status) for result in historical} == {
        ("4.0", DocumentStatus.CURRENT),
        ("3.1", DocumentStatus.SUPERSEDED),
    }
    assert index.query_calls[0]["status_filter"] is DocumentStatus.CURRENT
    assert index.query_calls[1]["status_filter"] is None


def test_results_are_ranked_by_score_then_chunk_id_for_ties() -> None:
    source = document()
    index = MemoryVectorIndex()
    index.matches = [
        match(source, score=0.8, chunk_id="chunk-b"),
        match(source, score=0.9, chunk_id="chunk-c"),
        match(source, score=0.8, chunk_id="chunk-a"),
    ]
    service = SemanticRetrievalService(FixedEmbeddingProvider(), index)

    results = service.retrieve("synthetic query", top_k=10)

    assert [result.chunk_id for result in results] == ["chunk-c", "chunk-a", "chunk-b"]
    assert [result.rank for result in results] == [1, 2, 3]


def test_top_k_larger_than_results_and_no_matches_are_supported() -> None:
    source = document()
    index = MemoryVectorIndex()
    index.matches = [
        match(source, score=0.8, chunk_id="policy-current:p0001:c000000")
    ]
    service = SemanticRetrievalService(FixedEmbeddingProvider(), index)

    assert len(service.retrieve("synthetic query", top_k=100)) == 1

    index.matches = []
    assert service.retrieve("synthetic query", top_k=100) == []


@pytest.mark.parametrize("query", ["", " ", "\r\n"])
def test_blank_query_is_rejected(query: str) -> None:
    service = SemanticRetrievalService(FixedEmbeddingProvider(), MemoryVectorIndex())

    with pytest.raises(ValueError, match="query must be a nonblank string"):
        service.retrieve(query)


@pytest.mark.parametrize("top_k", [0, -1, 1.5, True])
def test_invalid_top_k_is_rejected(top_k: object) -> None:
    service = SemanticRetrievalService(FixedEmbeddingProvider(), MemoryVectorIndex())

    with pytest.raises(ValueError, match="top_k must be a positive integer"):
        service.retrieve("synthetic query", top_k=top_k)  # type: ignore[arg-type]


def test_embedding_provider_failure_remains_an_application_error() -> None:
    error = EmbeddingProviderError("synthetic provider failure")
    service = SemanticRetrievalService(
        FixedEmbeddingProvider(error=error),
        MemoryVectorIndex(),
    )

    with pytest.raises(EmbeddingProviderError, match="synthetic provider failure"):
        service.retrieve("synthetic query")


def test_vector_index_failure_remains_an_application_error() -> None:
    class BrokenIndex(MemoryVectorIndex):
        def query(
            self,
            vector: tuple[float, ...],
            *,
            top_k: int,
            status_filter: DocumentStatus | None,
        ) -> list[VectorMatch]:
            raise VectorIndexError("synthetic index failure")

    service = SemanticRetrievalService(FixedEmbeddingProvider(), BrokenIndex())

    with pytest.raises(VectorIndexError, match="synthetic index failure"):
        service.retrieve("synthetic query")


def test_dimension_mismatch_is_rejected_at_service_boundary() -> None:
    provider = FixedEmbeddingProvider()
    provider.dimensions = 512

    with pytest.raises(DimensionMismatchError, match="1536"):
        SemanticRetrievalService(provider, MemoryVectorIndex())
