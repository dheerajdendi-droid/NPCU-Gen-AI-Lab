"""Provider-independent boundaries used by grounded-answer generation."""

from collections.abc import Sequence
from typing import Protocol

from cu_intelligence.domain import RetrievalResult
from cu_intelligence.generation.models import GenerationDraft


class EvidenceRetriever(Protocol):
    """Retrieve ranked application-owned evidence for one question."""

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        include_superseded: bool = False,
    ) -> list[RetrievalResult]:
        """Return ranked evidence under the requested document-status policy."""


class GenerationProvider(Protocol):
    """Produce one application-owned structured draft from supplied evidence."""

    def generate(
        self,
        question: str,
        evidence: Sequence[RetrievalResult],
    ) -> GenerationDraft:
        """Generate a structured draft without returning provider SDK types."""
