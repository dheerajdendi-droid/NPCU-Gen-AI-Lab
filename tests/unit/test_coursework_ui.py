"""Tests for the thin Gate 5.5 coursework presentation boundary."""

from collections.abc import Sequence
from datetime import date

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


def _result() -> RetrievalResult:
    return RetrievalResult(
        chunk_id="policy:p0002:c000001",
        document_id="policy",
        chunk_text="Synthetic policy evidence " * 40,
        page_number=2,
        title="Synthetic Lending Policy",
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
