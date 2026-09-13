"""Coursework UI composition without retrieval or generation business logic."""

from dataclasses import dataclass
from typing import Any

from pinecone import Pinecone

from cu_intelligence.domain import RetrievalResult
from cu_intelligence.generation import (
    GenerationProvider,
    GroundedAnswer,
    GroundedAnswerService,
    OpenAIGenerationProvider,
    load_live_generation_config,
)
from cu_intelligence.generation.contracts import EvidenceRetriever
from cu_intelligence.retrieval import (
    OpenAIEmbeddingProvider,
    PineconeVectorIndex,
    SemanticRetrievalService,
    VectorIndexError,
    load_live_retrieval_config,
)


@dataclass(frozen=True, slots=True)
class CourseworkDemoResult:
    """One validated answer and the exact evidence supplied to generation."""

    answer: GroundedAnswer
    evidence: tuple[RetrievalResult, ...]


class _RecordingRetriever:
    """Expose retrieval evidence to the demo without changing retrieval behavior."""

    def __init__(self, delegate: EvidenceRetriever) -> None:
        self._delegate = delegate
        self.last_results: tuple[RetrievalResult, ...] = ()

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        include_superseded: bool = False,
    ) -> list[RetrievalResult]:
        self.last_results = ()
        results = self._delegate.retrieve(
            query,
            top_k=top_k,
            include_superseded=include_superseded,
        )
        self.last_results = tuple(results)
        return results


class CourseworkDemoService:
    """Call the accepted answer service once and retain its exact evidence."""

    def __init__(
        self,
        retriever: EvidenceRetriever,
        generation_provider: GenerationProvider,
    ) -> None:
        self._recording_retriever = _RecordingRetriever(retriever)
        self._answer_service = GroundedAnswerService(
            self._recording_retriever,
            generation_provider,
        )

    def ask(self, question: str) -> CourseworkDemoResult:
        """Return the existing grounded answer and its retrieval evidence."""

        answer = self._answer_service.answer(question)
        return CourseworkDemoResult(
            answer=answer,
            evidence=self._recording_retriever.last_results,
        )


class _QueryOnlyDataIndex:
    """Expose only the Pinecone data operation required by the demo."""

    def __init__(self, delegate: Any) -> None:
        self._delegate = delegate

    def query(self, **arguments: Any) -> Any:
        return self._delegate.query(**arguments)


class _ExistingReadOnlyIndexControl:
    """Validate and open an existing index without a creation or mutation surface."""

    def __init__(self, delegate: Any) -> None:
        self._delegate = delegate

    def has_index(self, name: str) -> bool:
        return True

    def describe_index(self, name: str) -> Any:
        return self._delegate.describe_index(name)

    def Index(self, **arguments: Any) -> _QueryOnlyDataIndex:  # noqa: N802
        return _QueryOnlyDataIndex(self._delegate.Index(**arguments))


def build_live_coursework_demo_service() -> CourseworkDemoService:
    """Compose existing live adapters around an existing read-only Pinecone index."""

    retrieval_config = load_live_retrieval_config()
    generation_config = load_live_generation_config()
    control = Pinecone(
        api_key=retrieval_config.vector_index.api_key.get_secret_value()
    )
    index_name = retrieval_config.vector_index.index_name
    if not control.has_index(index_name):
        raise VectorIndexError(
            "The configured Pinecone index does not exist; the coursework demo cannot create it"
        )

    retrieval = SemanticRetrievalService(
        OpenAIEmbeddingProvider.from_config(retrieval_config.embeddings),
        PineconeVectorIndex.from_config(
            retrieval_config.vector_index,
            control_client=_ExistingReadOnlyIndexControl(control),
        ),
    )
    return CourseworkDemoService(
        retrieval,
        OpenAIGenerationProvider.from_config(generation_config),
    )


def _evidence_preview(text: str, *, limit: int = 500) -> str:
    """Return a compact evidence preview for the presentation layer."""

    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def evidence_preview(result: RetrievalResult) -> str:
    """Build a display-only preview without changing source evidence."""

    return _evidence_preview(result.chunk_text)
