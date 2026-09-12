"""Transparent retrieval and grounded-answer metrics."""

from collections import Counter
from collections.abc import Iterable, Sequence

from cu_intelligence.domain import DocumentStatus, RetrievalResult
from cu_intelligence.evaluation.models import (
    AggregateAnswerMetrics,
    AggregateRetrievalMetrics,
    AnswerCaseMetrics,
    CaseEvaluationResult,
    EvaluationCase,
    EvaluationCategory,
    RatioMetric,
    RetrievalCaseMetrics,
)
from cu_intelligence.generation import GroundedAnswer


def ratio_metric(numerator: float, denominator: int) -> RatioMetric:
    """Build a rounded ratio while preserving a visible zero denominator."""

    value = None if denominator == 0 else round(numerator / denominator, 4)
    return RatioMetric(numerator=numerator, denominator=denominator, value=value)


def score_retrieval(
    case: EvaluationCase,
    results: Sequence[RetrievalResult],
    *,
    depth: int = 10,
) -> RetrievalCaseMetrics:
    """Score one ordered retrieval result without hiding structural violations."""

    if isinstance(depth, bool) or not isinstance(depth, int) or depth <= 0:
        raise ValueError("depth must be a positive integer")
    evaluated = tuple(results[:depth])
    expected_ranks = tuple(range(1, len(evaluated) + 1))
    actual_ranks = tuple(result.rank for result in evaluated)
    rank_order_valid = actual_ranks == expected_ranks

    chunk_counts = Counter(result.chunk_id for result in evaluated)
    duplicate_chunk_ids = tuple(
        sorted(chunk_id for chunk_id, count in chunk_counts.items() if count > 1)
    )
    relevant = set(case.relevant_document_ids)
    retrieved_documents = {result.document_id for result in evaluated}

    def hit_at(cutoff: int) -> RatioMetric:
        if not relevant:
            return ratio_metric(0, 0)
        hit = any(
            result.document_id in relevant for result in evaluated[: min(cutoff, depth)]
        )
        return ratio_metric(int(hit), 1)

    first_relevant_position = next(
        (
            position
            for position, result in enumerate(evaluated, start=1)
            if result.document_id in relevant
        ),
        None,
    )
    reciprocal_rank = (
        ratio_metric(0, 0)
        if not relevant
        else ratio_metric(
            0 if first_relevant_position is None else 1 / first_relevant_position,
            1,
        )
    )

    expected_pairs = {
        (document_id, page)
        for document_id, pages in case.expected_evidence_pages.items()
        for page in pages
    }
    retrieved_pairs = {
        (result.document_id, result.page_number) for result in evaluated
    }
    forbidden_documents = tuple(
        sorted(set(case.forbidden_document_ids) & retrieved_documents)
    )
    forbidden_statuses = tuple(
        sorted(
            set(case.forbidden_document_statuses)
            & {result.document_status for result in evaluated},
            key=lambda status: status.value,
        )
    )
    unexpected_superseded_count = sum(
        1
        for result in evaluated
        if not case.include_superseded
        and result.document_status is DocumentStatus.SUPERSEDED
    )

    return RetrievalCaseMetrics(
        document_hit_at_1=hit_at(1),
        document_hit_at_3=hit_at(3),
        document_hit_at_5=hit_at(5),
        document_hit_at_10=hit_at(10),
        reciprocal_rank=reciprocal_rank,
        multi_document_recall=ratio_metric(
            len(relevant & retrieved_documents),
            len(relevant),
        ),
        page_evidence_hit_rate=ratio_metric(
            len(expected_pairs & retrieved_pairs),
            len(expected_pairs),
        ),
        unexpected_superseded_count=unexpected_superseded_count,
        missing_relevant_document_ids=tuple(sorted(relevant - retrieved_documents)),
        forbidden_document_ids_found=forbidden_documents,
        forbidden_statuses_found=forbidden_statuses,
        duplicate_chunk_ids=duplicate_chunk_ids,
        rank_order_valid=rank_order_valid,
    )


def score_answer(
    case: EvaluationCase,
    evidence: Sequence[RetrievalResult],
    answer: GroundedAnswer,
) -> AnswerCaseMetrics:
    """Score citations only against the exact evidence supplied for this answer."""

    violations: list[str] = []
    evidence_counts = Counter(item.chunk_id for item in evidence)
    duplicate_evidence = sorted(
        chunk_id for chunk_id, count in evidence_counts.items() if count > 1
    )
    if duplicate_evidence:
        violations.append("duplicate evidence chunk IDs: " + ", ".join(duplicate_evidence))
    evidence_by_id = {item.chunk_id: item for item in evidence}

    citation_numbers = [citation.citation_number for citation in answer.citations]
    if len(citation_numbers) != len(set(citation_numbers)):
        violations.append("duplicate citation numbers")
    citation_chunk_ids = [citation.chunk_id for citation in answer.citations]
    duplicate_citations = sorted(
        chunk_id
        for chunk_id, count in Counter(citation_chunk_ids).items()
        if count > 1
    )
    if duplicate_citations:
        violations.append("duplicate citation chunk IDs: " + ", ".join(duplicate_citations))

    valid_citation_count = 0
    provenance_mismatch = False
    for citation in answer.citations:
        source = evidence_by_id.get(citation.chunk_id)
        if source is None:
            violations.append(f"unknown citation chunk ID: {citation.chunk_id}")
            continue
        valid_citation_count += 1
        expected = (
            source.document_id,
            source.title,
            source.version,
            source.document_status,
            source.page_number,
            source.source_filename,
        )
        actual = (
            citation.document_id,
            citation.title,
            citation.version,
            citation.document_status,
            citation.page_number,
            citation.source_filename,
        )
        if actual != expected:
            provenance_mismatch = True
            violations.append(f"citation provenance mismatch: {citation.chunk_id}")

    known_numbers = set(citation_numbers)
    if any(
        number not in known_numbers
        for statement in answer.statements
        for number in statement.citation_numbers
    ):
        violations.append("statement references an unknown citation number")
    if answer.status.value == "ANSWERED" and any(
        not statement.citation_numbers for statement in answer.statements
    ):
        violations.append("answered statement has no citation")

    cited_documents = {citation.document_id for citation in answer.citations}
    allowed_documents = set(case.allowed_citation_document_ids)
    required_documents = set(case.required_citation_document_ids)
    unsupported_applicable = (
        case.expected_answer_status.value == "INSUFFICIENT_EVIDENCE"
    )
    historical_applicable = (
        case.category is EvaluationCategory.HISTORICAL_COMPARISON
    )
    superseded_citations = [
        citation
        for citation in answer.citations
        if citation.document_status is DocumentStatus.SUPERSEDED
    ]
    historical_label_correct = bool(superseded_citations) and all(
        "SUPERSEDED" in answer.rendered_answer for _ in superseded_citations
    )
    version_status_correct = (
        bool(answer.citations)
        and not provenance_mismatch
        and {
            citation.document_status for citation in answer.citations
        }
        >= {DocumentStatus.CURRENT, DocumentStatus.SUPERSEDED}
    )

    return AnswerCaseMetrics(
        expected_status_accuracy=ratio_metric(
            int(answer.status is case.expected_answer_status),
            1,
        ),
        citation_chunk_id_validity=ratio_metric(
            valid_citation_count,
            len(answer.citations),
        ),
        citation_document_precision=ratio_metric(
            len(cited_documents & allowed_documents),
            len(cited_documents),
        ),
        citation_document_recall=ratio_metric(
            len(cited_documents & required_documents),
            len(required_documents),
        ),
        unsupported_answer_citation_free_rate=ratio_metric(
            int(not answer.citations),
            1,
        )
        if unsupported_applicable
        else ratio_metric(0, 0),
        historical_status_labelling_correctness=ratio_metric(
            int(historical_label_correct),
            1,
        )
        if historical_applicable
        else ratio_metric(0, 0),
        version_status_correctness=ratio_metric(
            int(version_status_correct),
            1,
        )
        if historical_applicable
        else ratio_metric(0, 0),
        structural_grounding_violations=tuple(dict.fromkeys(violations)),
    )


def aggregate_retrieval(
    results: Sequence[CaseEvaluationResult],
) -> AggregateRetrievalMetrics:
    """Aggregate retrieval numerators and denominators across cases."""

    metrics = [result.retrieval_metrics for result in results]
    return AggregateRetrievalMetrics(
        document_hit_at_1=_combine(metric.document_hit_at_1 for metric in metrics),
        document_hit_at_3=_combine(metric.document_hit_at_3 for metric in metrics),
        document_hit_at_5=_combine(metric.document_hit_at_5 for metric in metrics),
        document_hit_at_10=_combine(metric.document_hit_at_10 for metric in metrics),
        mean_reciprocal_rank=_combine(metric.reciprocal_rank for metric in metrics),
        multi_document_recall=_combine(
            metric.multi_document_recall for metric in metrics
        ),
        page_evidence_hit_rate=_combine(
            metric.page_evidence_hit_rate for metric in metrics
        ),
        unexpected_superseded_count=sum(
            metric.unexpected_superseded_count for metric in metrics
        ),
        missing_relevant_document_count=sum(
            len(metric.missing_relevant_document_ids) for metric in metrics
        ),
        forbidden_document_violation_count=sum(
            len(metric.forbidden_document_ids_found) for metric in metrics
        ),
        forbidden_status_violation_count=sum(
            len(metric.forbidden_statuses_found) for metric in metrics
        ),
        duplicate_chunk_violation_count=sum(
            len(metric.duplicate_chunk_ids) for metric in metrics
        ),
        rank_order_violation_count=sum(
            int(not metric.rank_order_valid) for metric in metrics
        ),
    )


def aggregate_answers(
    results: Sequence[CaseEvaluationResult],
) -> AggregateAnswerMetrics:
    """Aggregate answer measures while counting failed cases as status misses."""

    available = [result.answer_metrics for result in results if result.answer_metrics]
    expected_status_numerator = sum(
        metric.expected_status_accuracy.numerator for metric in available
    )
    return AggregateAnswerMetrics(
        expected_status_accuracy=ratio_metric(
            expected_status_numerator,
            len(results),
        ),
        citation_chunk_id_validity=_combine(
            metric.citation_chunk_id_validity for metric in available
        ),
        citation_document_precision=_combine(
            metric.citation_document_precision for metric in available
        ),
        citation_document_recall=_combine(
            metric.citation_document_recall for metric in available
        ),
        unsupported_answer_citation_free_rate=_combine(
            metric.unsupported_answer_citation_free_rate for metric in available
        ),
        historical_status_labelling_correctness=_combine(
            metric.historical_status_labelling_correctness for metric in available
        ),
        version_status_correctness=_combine(
            metric.version_status_correctness for metric in available
        ),
        structural_grounding_violation_count=sum(
            len(metric.structural_grounding_violations) for metric in available
        ),
        failed_case_count=sum(result.failure is not None for result in results),
    )


def _combine(metrics: Iterable[RatioMetric]) -> RatioMetric:
    values = tuple(metrics)
    return ratio_metric(
        sum(metric.numerator for metric in values),
        sum(metric.denominator for metric in values),
    )
