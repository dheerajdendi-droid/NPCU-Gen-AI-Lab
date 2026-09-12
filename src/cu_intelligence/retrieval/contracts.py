"""Provider-independent boundaries for embedding and vector storage."""

from collections.abc import Sequence
from typing import Protocol

from cu_intelligence.domain import DocumentStatus, VectorMatch, VectorRecord


class EmbeddingProvider(Protocol):
    """Convert text to fixed-size application-owned vectors."""

    dimensions: int

    def embed(self, texts: Sequence[str]) -> list[tuple[float, ...]]:
        """Embed texts in input order."""


class VectorIndex(Protocol):
    """Store and query provider-independent vector records."""

    dimensions: int

    def upsert(self, records: Sequence[VectorRecord]) -> int:
        """Insert or replace records by stable record ID."""

    def query(
        self,
        vector: Sequence[float],
        *,
        top_k: int,
        status_filter: DocumentStatus | None,
    ) -> list[VectorMatch]:
        """Return at most top_k matches, optionally restricted by document status."""
