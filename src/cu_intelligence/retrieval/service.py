"""Provider-independent indexing and semantic retrieval application service."""

from collections.abc import Sequence

from pydantic import ValidationError

from cu_intelligence.domain import (
    CorpusBuild,
    CorpusChunk,
    DocumentStatus,
    IndexingSummary,
    RetrievalResult,
    VectorMatch,
    VectorRecord,
)
from cu_intelligence.retrieval.config import EMBEDDING_MODEL, VECTOR_DIMENSIONS
from cu_intelligence.retrieval.contracts import EmbeddingProvider, VectorIndex
from cu_intelligence.retrieval.errors import (
    DimensionMismatchError,
    EmbeddingProviderError,
    VectorIndexError,
)


def build_vector_records(
    chunks: Sequence[CorpusChunk],
    embeddings: Sequence[Sequence[float]],
) -> list[VectorRecord]:
    """Map enriched chunks and vectors to stable provider-independent records."""

    if len(chunks) != len(embeddings):
        raise EmbeddingProviderError(
            "embedding response count does not match the number of chunks"
        )

    records: list[VectorRecord] = []
    for chunk, embedding in zip(chunks, embeddings, strict=True):
        values = tuple(float(component) for component in embedding)
        if len(values) != VECTOR_DIMENSIONS:
            raise DimensionMismatchError(
                f"vectors must contain exactly {VECTOR_DIMENSIONS} values"
            )
        records.append(
            VectorRecord(
                record_id=chunk.chunk_id,
                values=values,
                metadata={
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "text": chunk.text,
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                    "title": chunk.title,
                    "version": chunk.version,
                    "status": chunk.document_status.value,
                    "effective_date": chunk.effective_date.isoformat(),
                    "owner": chunk.owner,
                    "source_filename": chunk.source_filename,
                    "synthetic": chunk.synthetic,
                    "embedding_model": EMBEDDING_MODEL,
                    "embedding_dimensions": VECTOR_DIMENSIONS,
                },
            )
        )
    return records


class SemanticRetrievalService:
    """Coordinate approved embedding and vector-index boundaries."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_index: VectorIndex,
    ) -> None:
        if embedding_provider.dimensions != VECTOR_DIMENSIONS:
            raise DimensionMismatchError(
                f"embedding provider must use {VECTOR_DIMENSIONS} dimensions"
            )
        if vector_index.dimensions != VECTOR_DIMENSIONS:
            raise DimensionMismatchError(
                f"vector index must use {VECTOR_DIMENSIONS} dimensions"
            )
        self._embedding_provider = embedding_provider
        self._vector_index = vector_index

    def index_corpus(self, corpus: CorpusBuild) -> IndexingSummary:
        """Embed and idempotently upsert every enriched corpus chunk."""

        chunks = list(corpus.chunks)
        embeddings = self._embedding_provider.embed([chunk.text for chunk in chunks])
        records = build_vector_records(chunks, embeddings)
        upserted_count = self._vector_index.upsert(records)
        return IndexingSummary(
            document_count=len(corpus.documents),
            chunk_count=len(chunks),
            upserted_count=upserted_count,
        )

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        include_superseded: bool = False,
    ) -> list[RetrievalResult]:
        """Return ranked evidence, excluding superseded material by default."""

        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a nonblank string")
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0:
            raise ValueError("top_k must be a positive integer")

        query_vectors = self._embedding_provider.embed([query.strip()])
        if len(query_vectors) != 1:
            raise EmbeddingProviderError("query embedding did not return exactly one vector")

        status_filter = None if include_superseded else DocumentStatus.CURRENT
        matches = self._vector_index.query(
            query_vectors[0],
            top_k=top_k,
            status_filter=status_filter,
        )
        ordered = sorted(matches, key=lambda match: (-match.score, match.record_id))[:top_k]
        return [
            _map_match(match, rank=rank)
            for rank, match in enumerate(ordered, start=1)
        ]


def _map_match(match: VectorMatch, *, rank: int) -> RetrievalResult:
    try:
        metadata = match.metadata
        return RetrievalResult(
            chunk_id=match.record_id,
            document_id=metadata["document_id"],
            chunk_text=metadata["text"],
            page_number=metadata["page_number"],
            title=metadata["title"],
            version=metadata["version"],
            document_status=metadata["status"],
            effective_date=metadata["effective_date"],
            owner=metadata["owner"],
            source_filename=metadata["source_filename"],
            synthetic=metadata["synthetic"],
            rank=rank,
            similarity_score=match.score,
        )
    except (KeyError, TypeError, ValidationError) as error:
        raise VectorIndexError("Vector match contains invalid provenance metadata") from error
