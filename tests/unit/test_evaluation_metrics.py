"""Tests for retrieval and grounded-answer metric calculations."""

from datetime import date

from cu_intelligence.domain import DocumentStatus, RetrievalResult
from cu_intelligence.evaluation import (
    EvaluationCase,
    EvaluationCategory,
    score_answer,
    score_retrieval,
)
from cu_intelligence.generation import (
    AnswerStatus,
    CitationRecord,
    GroundedAnswer,
    GroundedStatement,
)


def _case(
    *,
    category: EvaluationCategory = EvaluationCategory.MULTI_DOCUMENT,
    expected_status: AnswerStatus = AnswerStatus.ANSWERED,
    relevant: tuple[str, ...] = ("doc-a", "doc-b"),
    required: tuple[str, ...] = ("doc-a", "doc-b"),
    allowed: tuple[str, ...] = ("doc-a", "doc-b"),
    include_superseded: bool = False,
    forbidden_statuses: tuple[DocumentStatus, ...] = (DocumentStatus.SUPERSEDED,),
) -> EvaluationCase:
    return EvaluationCase(
        case_id="metric-case",
        question="What applies?",
        category=category,
        include_superseded=include_superseded,
        expected_answer_status=expected_status,
        relevant_document_ids=relevant,
        required_citation_document_ids=required,
        allowed_citation_document_ids=allowed,
        forbidden_document_ids=("doc-forbidden",),
        forbidden_document_statuses=forbidden_statuses,
        expected_evidence_pages={document_id: (2,) for document_id in relevant},
        reference_facts=("A fact",) if expected_status is AnswerStatus.ANSWERED else (),
        human_review_guidance="Review the result.",
    )


def _result(
    document_id: str,
    rank: int,
    *,
    chunk_id: str | None = None,
    page: int = 2,
    status: DocumentStatus = DocumentStatus.CURRENT,
) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id or f"{document_id}-chunk-{rank}",
        document_id=document_id,
        chunk_text="Synthetic evidence.",
        page_number=page,
        title=f"Title {document_id}",
        version="1.0" if status is DocumentStatus.CURRENT else "0.9",
        document_status=status,
        effective_date=date(2026, 1, 1),
        owner="Owner",
        source_filename=f"{document_id}.pdf",
        synthetic=True,
        rank=rank,
        similarity_score=1 - rank / 100,
    )


def _citation(number: int, result: RetrievalResult, *, chunk_id: str | None = None):
    return CitationRecord(
        citation_number=number,
        document_id=result.document_id,
        title=result.title,
        version=result.version,
        document_status=result.document_status,
        page_number=result.page_number,
        source_filename=result.source_filename,
        chunk_id=chunk_id or result.chunk_id,
    )


def test_multiple_relevant_documents_and_page_hits_are_scored() -> None:
    case = _case()
    results = [_result("doc-a", 1), _result("other", 2), _result("doc-b", 3)]

    metrics = score_retrieval(case, results)

    assert metrics.document_hit_at_1.value == 1
    assert metrics.document_hit_at_3.value == 1
    assert metrics.reciprocal_rank.value == 1
    assert metrics.multi_document_recall.value == 1
    assert metrics.page_evidence_hit_rate.value == 1
    assert metrics.missing_relevant_document_ids == ()


def test_empty_retrieval_is_an_explicit_miss() -> None:
    metrics = score_retrieval(_case(), [])

    assert metrics.document_hit_at_10.value == 0
    assert metrics.reciprocal_rank.value == 0
    assert metrics.multi_document_recall.numerator == 0
    assert metrics.multi_document_recall.denominator == 2


def test_unsupported_retrieval_has_zero_relevance_denominators() -> None:
    case = _case(
        category=EvaluationCategory.UNSUPPORTED,
        expected_status=AnswerStatus.INSUFFICIENT_EVIDENCE,
        relevant=(),
        required=(),
        allowed=(),
    )

    metrics = score_retrieval(case, [_result("other", 1)])

    assert metrics.document_hit_at_1.value is None
    assert metrics.reciprocal_rank.value is None
    assert metrics.multi_document_recall.value is None


def test_duplicate_forbidden_and_superseded_results_are_reported() -> None:
    duplicate = _result("doc-forbidden", 1, chunk_id="duplicate")
    repeated = _result(
        "doc-forbidden",
        3,
        chunk_id="duplicate",
        status=DocumentStatus.SUPERSEDED,
    )

    metrics = score_retrieval(_case(), [duplicate, repeated])

    assert metrics.duplicate_chunk_ids == ("duplicate",)
    assert metrics.forbidden_document_ids_found == ("doc-forbidden",)
    assert metrics.forbidden_statuses_found == (DocumentStatus.SUPERSEDED,)
    assert metrics.unexpected_superseded_count == 1
    assert metrics.rank_order_valid is False


def test_citation_precision_recall_and_validity_are_separate() -> None:
    case = _case()
    evidence = [_result("doc-a", 1), _result("doc-c", 2)]
    answer = GroundedAnswer(
        status=AnswerStatus.ANSWERED,
        question=case.question,
        statements=(GroundedStatement(text="Answer", citation_numbers=(1, 2)),),
        citations=(
            _citation(1, evidence[0]),
            _citation(2, evidence[1]),
        ),
        insufficient_evidence_explanation=None,
        rendered_answer="Answer [1] [2]",
    )

    metrics = score_answer(case, evidence, answer)

    assert metrics.citation_chunk_id_validity.value == 1
    assert metrics.citation_document_precision.value == 0.5
    assert metrics.citation_document_recall.value == 0.5


def test_unknown_citation_id_is_a_structural_violation() -> None:
    case = _case(
        category=EvaluationCategory.CURRENT_POLICY,
        relevant=("doc-a",),
        required=("doc-a",),
        allowed=("doc-a",),
    )
    evidence = [_result("doc-a", 1)]
    answer = GroundedAnswer(
        status=AnswerStatus.ANSWERED,
        question=case.question,
        statements=(GroundedStatement(text="Answer", citation_numbers=(1,)),),
        citations=(_citation(1, evidence[0], chunk_id="invented"),),
        insufficient_evidence_explanation=None,
        rendered_answer="Answer [1]",
    )

    metrics = score_answer(case, evidence, answer)

    assert metrics.citation_chunk_id_validity.value == 0
    assert metrics.structural_grounding_violations == (
        "unknown citation chunk ID: invented",
    )


def test_unsupported_abstention_is_citation_free() -> None:
    case = _case(
        category=EvaluationCategory.UNSUPPORTED,
        expected_status=AnswerStatus.INSUFFICIENT_EVIDENCE,
        relevant=(),
        required=(),
        allowed=(),
    )
    answer = GroundedAnswer(
        status=AnswerStatus.INSUFFICIENT_EVIDENCE,
        question=case.question,
        statements=(),
        citations=(),
        insufficient_evidence_explanation="The evidence is insufficient.",
        rendered_answer="Insufficient evidence: The evidence is insufficient.",
    )

    metrics = score_answer(case, [], answer)

    assert metrics.expected_status_accuracy.value == 1
    assert metrics.unsupported_answer_citation_free_rate.value == 1
    assert metrics.citation_chunk_id_validity.value is None


def test_historical_citations_require_both_statuses_and_visible_label() -> None:
    case = _case(
        category=EvaluationCategory.HISTORICAL_COMPARISON,
        include_superseded=True,
        forbidden_statuses=(),
    )
    current = _result("doc-a", 1)
    old = _result("doc-b", 2, status=DocumentStatus.SUPERSEDED)
    answer = GroundedAnswer(
        status=AnswerStatus.ANSWERED,
        question=case.question,
        statements=(GroundedStatement(text="Comparison", citation_numbers=(1, 2)),),
        citations=(_citation(1, current), _citation(2, old)),
        insufficient_evidence_explanation=None,
        rendered_answer="Comparison [1] [2]\n[2] old, SUPERSEDED",
    )

    metrics = score_answer(case, [current, old], answer)

    assert metrics.historical_status_labelling_correctness.value == 1
    assert metrics.version_status_correctness.value == 1
