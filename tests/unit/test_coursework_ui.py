"""Tests for the thin Gate 5.5 coursework presentation boundary."""

from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Event

from cu_intelligence.domain import DocumentStatus, RetrievalResult
from cu_intelligence.generation import (
    AnswerStatus,
    DraftStatement,
    GenerationDraft,
)
from cu_intelligence.ui.service import (
    CourseworkDemoService,
    _QueryOnlyDataIndex,
    evidence_preview,
)


def _result(
    *,
    chunk_id: str = "policy:p0002:c000001",
    title: str = "Synthetic Lending Policy",
) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        document_id="policy",
        chunk_text="Synthetic policy evidence " * 40,
        page_number=2,
        title=title,
        version="4.0",
        document_status=DocumentStatus.CURRENT,
        effective_date=date(2026, 1, 1),
        owner="Policy Owner",
        source_filename="policy.pdf",
        synthetic=True,
        rank=1,
        similarity_score=0.91,
    )


class FakeRetriever:
    def __init__(self, results: Sequence[RetrievalResult]) -> None:
        self.results = list(results)
        self.calls: list[tuple[str, int, bool]] = []

    def retrieve(self, query, *, top_k=5, include_superseded=False):
        self.calls.append((query, top_k, include_superseded))
        return self.results[:top_k]


class FakeGenerator:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, question, evidence):
        self.calls += 1
        return GenerationDraft(
            status=AnswerStatus.ANSWERED,
            statements=(
                DraftStatement(
                    text="The policy answer is grounded.",
                    cited_chunk_ids=(evidence[0].chunk_id,),
                ),
            ),
            insufficient_evidence_explanation=None,
        )


def test_demo_service_invokes_existing_answer_path_and_preserves_citations() -> None:
    source = _result()
    retriever = FakeRetriever([source])
    generator = FakeGenerator()

    result = CourseworkDemoService(retriever, generator).ask("  What applies?  ")

    assert retriever.calls == [("What applies?", 10, False)]
    assert generator.calls == 1
    assert result.evidence == (source,)
    assert result.answer.status is AnswerStatus.ANSWERED
    assert result.answer.citations[0].document_id == source.document_id
    assert result.answer.citations[0].page_number == source.page_number
    assert result.answer.citations[0].document_status is DocumentStatus.CURRENT


def test_demo_service_keeps_fallback_distinct_and_bypasses_generation() -> None:
    retriever = FakeRetriever([])
    generator = FakeGenerator()

    result = CourseworkDemoService(retriever, generator).ask("Unknown policy question")

    assert generator.calls == 0
    assert result.evidence == ()
    assert result.answer.status is AnswerStatus.INSUFFICIENT_EVIDENCE
    assert result.answer.citations == ()


def test_concurrent_questions_keep_request_local_evidence() -> None:
    first_source = _result(
        chunk_id="policy:p0002:c000001",
        title="First Synthetic Policy",
    )
    second_source = _result(
        chunk_id="policy:p0003:c000001",
        title="Second Synthetic Policy",
    )
    first_generation_started = Event()
    release_first_generation = Event()

    class ConcurrentRetriever:
        def retrieve(self, query, *, top_k=5, include_superseded=False):
            del top_k, include_superseded
            return [first_source if query == "Question A" else second_source]

    class CoordinatedGenerator:
        def generate(self, question, evidence):
            if question == "Question A":
                first_generation_started.set()
                assert release_first_generation.wait(timeout=5)
            return GenerationDraft(
                status=AnswerStatus.ANSWERED,
                statements=(
                    DraftStatement(
                        text=f"Grounded response for {question}.",
                        cited_chunk_ids=(evidence[0].chunk_id,),
                    ),
                ),
                insufficient_evidence_explanation=None,
            )

    service = CourseworkDemoService(ConcurrentRetriever(), CoordinatedGenerator())

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(service.ask, "Question A")
        assert first_generation_started.wait(timeout=5)
        second_result = executor.submit(service.ask, "Question B").result(timeout=5)
        release_first_generation.set()
        first_result = first_future.result(timeout=5)

    assert first_result.evidence == (first_source,)
    assert first_result.answer.citations[0].chunk_id == first_source.chunk_id
    assert second_result.evidence == (second_source,)
    assert second_result.answer.citations[0].chunk_id == second_source.chunk_id


def test_evidence_preview_is_compact_without_changing_source() -> None:
    source = _result()
    original_chunk_text = source.chunk_text

    preview = evidence_preview(source)

    assert len(preview) <= 500
    assert preview.endswith("…")
    assert source.chunk_text == original_chunk_text


def test_query_only_index_does_not_expose_mutation_operations() -> None:
    class Delegate:
        def query(self, **arguments):
            return arguments

        def upsert(self, **arguments):  # pragma: no cover - must remain inaccessible
            raise AssertionError(arguments)

    index = _QueryOnlyDataIndex(Delegate())

    assert index.query(vector=[1.0]) == {"vector": [1.0]}
    assert not hasattr(index, "upsert")
