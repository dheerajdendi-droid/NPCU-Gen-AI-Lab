"""Provider-independent retrieval and grounded-answer evaluation."""

from cu_intelligence.evaluation.dataset import (
    EVALUATION_DIRECTORY_NAME,
    EXPECTED_CASE_COUNTS,
    load_evaluation_dataset,
)
from cu_intelligence.evaluation.errors import EvaluationDatasetError, EvaluationError
from cu_intelligence.evaluation.fingerprints import (
    canonical_json,
    fingerprint_configuration,
    fingerprint_corpus,
    fingerprint_dataset,
    fingerprint_value,
)
from cu_intelligence.evaluation.metrics import (
    aggregate_answers,
    aggregate_retrieval,
    ratio_metric,
    score_answer,
    score_retrieval,
)
from cu_intelligence.evaluation.models import (
    AggregateAnswerMetrics,
    AggregateRetrievalMetrics,
    AnswerCaseMetrics,
    CaseEvaluationResult,
    EvaluationCase,
    EvaluationCategory,
    EvaluationConfig,
    EvaluationDataset,
    EvaluationReport,
    EvidenceReference,
    HumanReviewDisposition,
    HumanReviewResult,
    RatioMetric,
    RetrievalCaseMetrics,
)
from cu_intelligence.evaluation.reporting import (
    render_human_review_template,
    render_json_report,
    render_markdown_report,
)
from cu_intelligence.evaluation.runner import EvaluationRunner

__all__ = [
    "EVALUATION_DIRECTORY_NAME",
    "EXPECTED_CASE_COUNTS",
    "AggregateAnswerMetrics",
    "AggregateRetrievalMetrics",
    "AnswerCaseMetrics",
    "CaseEvaluationResult",
    "EvaluationCase",
    "EvaluationCategory",
    "EvaluationConfig",
    "EvaluationDataset",
    "EvaluationDatasetError",
    "EvaluationError",
    "EvaluationReport",
    "EvaluationRunner",
    "EvidenceReference",
    "HumanReviewDisposition",
    "HumanReviewResult",
    "RatioMetric",
    "RetrievalCaseMetrics",
    "aggregate_answers",
    "aggregate_retrieval",
    "canonical_json",
    "fingerprint_configuration",
    "fingerprint_corpus",
    "fingerprint_dataset",
    "fingerprint_value",
    "load_evaluation_dataset",
    "ratio_metric",
    "render_human_review_template",
    "render_json_report",
    "render_markdown_report",
    "score_answer",
    "score_retrieval",
]
