"""Deterministic JSON and readable Markdown evaluation reports."""

from collections.abc import Iterable

from cu_intelligence.evaluation.fingerprints import canonical_json
from cu_intelligence.evaluation.models import (
    EvaluationReport,
    HumanReviewResult,
    RatioMetric,
)


def render_json_report(report: EvaluationReport) -> str:
    """Render stable machine-readable JSON with no provider objects."""

    return canonical_json(report) + "\n"


def render_markdown_report(report: EvaluationReport) -> str:
    """Render a stable owner-facing baseline and per-case review document."""

    lines = [
        f"# Evaluation report — {report.dataset_id}",
        "",
        "## Run identity",
        "",
        f"- Dataset fingerprint: `{report.dataset_fingerprint}`",
        f"- Corpus fingerprint: `{report.corpus_fingerprint}`",
        f"- Configuration fingerprint: `{report.configuration_fingerprint}`",
        f"- Retrieval depth: {report.configuration.retrieval_depth}",
        f"- Embedding model: `{report.configuration.embedding_model}`",
        f"- Generation model: `{report.configuration.generation_model}`",
        "",
        "## Automated retrieval measures",
        "",
        "| Measure | Numerator | Denominator | Value |",
        "| --- | ---: | ---: | ---: |",
        *_ratio_rows(
            (
                ("Document Hit@1", report.retrieval.document_hit_at_1),
                ("Document Hit@3", report.retrieval.document_hit_at_3),
                ("Document Hit@5", report.retrieval.document_hit_at_5),
                ("Document Hit@10", report.retrieval.document_hit_at_10),
                ("Mean reciprocal rank", report.retrieval.mean_reciprocal_rank),
                ("Multi-document recall", report.retrieval.multi_document_recall),
                ("Page evidence hit rate", report.retrieval.page_evidence_hit_rate),
            )
        ),
        "",
        "## Automated answer measures",
        "",
        "| Measure | Numerator | Denominator | Value |",
        "| --- | ---: | ---: | ---: |",
        *_ratio_rows(
            (
                ("Expected status accuracy", report.answers.expected_status_accuracy),
                ("Citation chunk validity", report.answers.citation_chunk_id_validity),
                ("Citation document precision", report.answers.citation_document_precision),
                ("Citation document recall", report.answers.citation_document_recall),
                (
                    "Unsupported citation-free rate",
                    report.answers.unsupported_answer_citation_free_rate,
                ),
                (
                    "Historical status labelling",
                    report.answers.historical_status_labelling_correctness,
                ),
                ("Version/status correctness", report.answers.version_status_correctness),
            )
        ),
        "",
        f"- Failed cases: {report.answers.failed_case_count}",
        (
            "- Structural grounding violations: "
            f"{report.answers.structural_grounding_violation_count}"
        ),
        "",
        "## Per-case results and human review",
    ]
    for result in report.cases:
        lines.extend(
            [
                "",
                f"### {result.case_id}",
                "",
                f"- Category: `{result.category.value}`",
                f"- Expected status: `{result.expected_answer_status.value}`",
                f"- Latency: {result.latency_ms:.3f} ms",
                f"- Failure: {result.failure or 'none'}",
                "- Evidence:",
            ]
        )
        if result.evidence:
            lines.extend(
                "  - "
                f"rank {item.rank}: `{item.chunk_id}` — `{item.document_id}`, "
                f"page {item.page_number}, {item.document_status.value}"
                for item in result.evidence
            )
        else:
            lines.append("  - none")
        lines.extend(["", "Answer:", ""])
        if result.answer is None:
            lines.append("_No validated answer._")
        else:
            lines.extend(
                f"> {line}" if line else ">"
                for line in result.answer.rendered_answer.splitlines()
            )
        lines.extend(["", *render_human_review_template(result.human_review).splitlines()])
    return "\n".join(lines) + "\n"


def render_human_review_template(review: HumanReviewResult) -> str:
    """Render ratings separately from automated measures."""

    def rating(value: int | None) -> str:
        return "_pending (0/1/2)_" if value is None else str(value)

    return "\n".join(
        (
            "Human review:",
            f"- Correctness: {rating(review.correctness)}",
            f"- Completeness: {rating(review.completeness)}",
            f"- Relevance: {rating(review.relevance)}",
            (
                "- Appropriate use of evidence: "
                f"{rating(review.appropriate_evidence_use)}"
            ),
            f"- Clarity: {rating(review.clarity)}",
            f"- Version and status handling: {rating(review.version_status_handling)}",
            f"- Reviewer notes: {review.reviewer_notes or '_pending_'}",
            f"- Final disposition: `{review.disposition.value}`",
        )
    )


def _ratio_rows(metrics: Iterable[tuple[str, RatioMetric]]) -> list[str]:
    return [
        f"| {name} | {_number(metric.numerator)} | {metric.denominator} | "
        f"{_metric_value(metric)} |"
        for name, metric in metrics
    ]


def _metric_value(metric: RatioMetric) -> str:
    return "N/A" if metric.value is None else f"{metric.value:.4f}"


def _number(value: float) -> str:
    return str(int(value)) if value.is_integer() else f"{value:.4f}"
