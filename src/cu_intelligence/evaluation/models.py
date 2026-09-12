"""Provider-independent models for Gate 5 evaluation."""

from enum import StrEnum
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from cu_intelligence.domain import DocumentStatus
from cu_intelligence.generation import AnswerStatus, GroundedAnswer, ProviderUsage

NonBlankString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
CaseId = Annotated[str, Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
PositivePage = Annotated[int, Field(ge=1)]
Rating = Annotated[int, Field(ge=0, le=2)]


class EvaluationModel(BaseModel):
    """Apply strict field validation to every evaluation value."""

    model_config = ConfigDict(extra="forbid")


class EvaluationCategory(StrEnum):
    """Mutually exclusive case groups in the Gate 5 baseline."""

    CURRENT_POLICY = "CURRENT_POLICY"
    MULTI_DOCUMENT = "MULTI_DOCUMENT"
    UNSUPPORTED = "UNSUPPORTED"
    HISTORICAL_COMPARISON = "HISTORICAL_COMPARISON"


class EvaluationCase(EvaluationModel):
    """One human-authored question and its declared evaluation expectations."""

    case_id: CaseId
    question: NonBlankString
    category: EvaluationCategory
    include_superseded: bool
    expected_answer_status: AnswerStatus
    relevant_document_ids: tuple[NonBlankString, ...]
    required_citation_document_ids: tuple[NonBlankString, ...]
    allowed_citation_document_ids: tuple[NonBlankString, ...]
    forbidden_document_ids: tuple[NonBlankString, ...]
    forbidden_document_statuses: tuple[DocumentStatus, ...]
    expected_evidence_pages: dict[NonBlankString, tuple[PositivePage, ...]]
    reference_facts: tuple[NonBlankString, ...]
    human_review_guidance: NonBlankString

    @model_validator(mode="after")
    def validate_expectations(self) -> "EvaluationCase":
        sequence_fields = (
            "relevant_document_ids",
            "required_citation_document_ids",
            "allowed_citation_document_ids",
            "forbidden_document_ids",
            "forbidden_document_statuses",
            "reference_facts",
        )
        for field_name in sequence_fields:
            values = getattr(self, field_name)
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must not contain duplicates")
        for document_id, pages in self.expected_evidence_pages.items():
            if len(pages) != len(set(pages)):
                raise ValueError(
                    f"expected pages for {document_id} must not contain duplicates"
                )

        relevant = set(self.relevant_document_ids)
        required = set(self.required_citation_document_ids)
        allowed = set(self.allowed_citation_document_ids)
        forbidden = set(self.forbidden_document_ids)
        if not required <= allowed:
            raise ValueError("required citation documents must be allowed")
        if not allowed <= relevant:
            raise ValueError("allowed citation documents must be relevant documents")
        if relevant & forbidden:
            raise ValueError("relevant and forbidden document IDs must be disjoint")
        if not set(self.expected_evidence_pages) <= relevant:
            raise ValueError("page expectations must belong to relevant documents")

        if self.expected_answer_status is AnswerStatus.INSUFFICIENT_EVIDENCE:
            if (
                relevant
                or required
                or allowed
                or self.expected_evidence_pages
                or self.reference_facts
                or self.include_superseded
            ):
                raise ValueError(
                    "unsupported cases cannot declare evidence, citations, facts, or history"
                )
            if self.category is not EvaluationCategory.UNSUPPORTED:
                raise ValueError("only unsupported cases expect insufficient evidence")
            return self

        if self.category is EvaluationCategory.UNSUPPORTED:
            raise ValueError("unsupported cases must expect insufficient evidence")
        if not relevant or not required or not self.reference_facts:
            raise ValueError(
                "answered cases require relevant documents, required citations, and facts"
            )
        if self.category is EvaluationCategory.MULTI_DOCUMENT and len(relevant) < 2:
            raise ValueError("multi-document cases require at least two relevant documents")
        if self.category is EvaluationCategory.HISTORICAL_COMPARISON:
            if not self.include_superseded or len(relevant) < 2:
                raise ValueError(
                    "historical comparisons require superseded retrieval and two documents"
                )
        elif self.include_superseded:
            raise ValueError("only historical comparisons may include superseded evidence")
        return self


class EvaluationDataset(EvaluationModel):
    """A versioned collection of unique evaluation cases."""

    dataset_id: NonBlankString
    cases: tuple[EvaluationCase, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def require_unique_case_ids(self) -> "EvaluationDataset":
        case_ids = [case.case_id for case in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("evaluation case IDs must be unique")
        return self


class RatioMetric(EvaluationModel):
    """A transparent ratio whose value is null when its denominator is zero."""

    numerator: float = Field(ge=0, allow_inf_nan=False)
    denominator: int = Field(ge=0)
    value: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_ratio(self) -> "RatioMetric":
        if self.denominator == 0:
            if self.numerator != 0 or self.value is not None:
                raise ValueError("zero-denominator metrics require numerator 0 and value null")
            return self
        expected = round(self.numerator / self.denominator, 4)
        if self.value != expected:
            raise ValueError("metric value must equal its rounded numerator/denominator")
        return self


class RetrievalCaseMetrics(EvaluationModel):
    """Automated retrieval measures for one case."""

    document_hit_at_1: RatioMetric
    document_hit_at_3: RatioMetric
    document_hit_at_5: RatioMetric
    document_hit_at_10: RatioMetric
    reciprocal_rank: RatioMetric
    multi_document_recall: RatioMetric
    page_evidence_hit_rate: RatioMetric
    unexpected_superseded_count: int = Field(ge=0)
    missing_relevant_document_ids: tuple[str, ...]
    forbidden_document_ids_found: tuple[str, ...]
    forbidden_statuses_found: tuple[DocumentStatus, ...]
    duplicate_chunk_ids: tuple[str, ...]
    rank_order_valid: bool


class AnswerCaseMetrics(EvaluationModel):
    """Automated answer and citation measures for one case."""

    expected_status_accuracy: RatioMetric
    citation_chunk_id_validity: RatioMetric
    citation_document_precision: RatioMetric
    citation_document_recall: RatioMetric
    unsupported_answer_citation_free_rate: RatioMetric
    historical_status_labelling_correctness: RatioMetric
    version_status_correctness: RatioMetric
    structural_grounding_violations: tuple[str, ...]


class HumanReviewDisposition(StrEnum):
    """Possible human conclusions kept separate from automated scores."""

    PENDING = "PENDING"
    ACCEPT = "ACCEPT"
    REVISE = "REVISE"
    REJECT = "REJECT"


class HumanReviewResult(EvaluationModel):
    """Optional human ratings for one case."""

    case_id: CaseId
    correctness: Rating | None = None
    completeness: Rating | None = None
    relevance: Rating | None = None
    appropriate_evidence_use: Rating | None = None
    clarity: Rating | None = None
    version_status_handling: Rating | None = None
    reviewer_notes: str = ""
    disposition: HumanReviewDisposition = HumanReviewDisposition.PENDING

    @model_validator(mode="after")
    def validate_review_completion(self) -> "HumanReviewResult":
        ratings = (
            self.correctness,
            self.completeness,
            self.relevance,
            self.appropriate_evidence_use,
            self.clarity,
            self.version_status_handling,
        )
        if self.disposition is HumanReviewDisposition.PENDING:
            if any(rating is not None for rating in ratings):
                raise ValueError("pending reviews cannot contain ratings")
        elif any(rating is None for rating in ratings):
            raise ValueError("completed reviews require all six ratings")
        return self


class EvidenceReference(EvaluationModel):
    """Exact retrieved evidence identity without duplicating full chunk text in reports."""

    chunk_id: NonBlankString
    document_id: NonBlankString
    document_status: DocumentStatus
    page_number: PositivePage
    rank: int = Field(ge=1)
    similarity_score: float = Field(allow_inf_nan=False)


class EvaluationConfig(EvaluationModel):
    """Public, credential-free identifiers for one evaluation run."""

    retrieval_depth: int = 10
    embedding_model: NonBlankString = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    generation_model: NonBlankString = "gpt-5.6-terra"

    @model_validator(mode="after")
    def require_accepted_baseline(self) -> "EvaluationConfig":
        if self.retrieval_depth != 10:
            raise ValueError("Gate 5 baseline retrieval depth must be 10")
        if self.embedding_model != "text-embedding-3-small":
            raise ValueError("Gate 5 must use the accepted embedding model")
        if self.embedding_dimensions != 1536:
            raise ValueError("Gate 5 must use 1,536-dimensional embeddings")
        if self.generation_model != "gpt-5.6-terra":
            raise ValueError("Gate 5 must use the accepted generation model")
        return self


class CaseEvaluationResult(EvaluationModel):
    """Provider-independent evidence and scores for one evaluated case."""

    case_id: CaseId
    question: NonBlankString
    category: EvaluationCategory
    expected_answer_status: AnswerStatus
    evidence: tuple[EvidenceReference, ...]
    retrieval_metrics: RetrievalCaseMetrics
    answer: GroundedAnswer | None
    answer_metrics: AnswerCaseMetrics | None
    usage: ProviderUsage | None
    latency_ms: float = Field(ge=0, allow_inf_nan=False)
    failure: str | None
    human_review: HumanReviewResult


class AggregateRetrievalMetrics(EvaluationModel):
    """Micro-aggregated retrieval measures with explicit denominators."""

    document_hit_at_1: RatioMetric
    document_hit_at_3: RatioMetric
    document_hit_at_5: RatioMetric
    document_hit_at_10: RatioMetric
    mean_reciprocal_rank: RatioMetric
    multi_document_recall: RatioMetric
    page_evidence_hit_rate: RatioMetric
    unexpected_superseded_count: int = Field(ge=0)
    missing_relevant_document_count: int = Field(ge=0)
    forbidden_document_violation_count: int = Field(ge=0)
    forbidden_status_violation_count: int = Field(ge=0)
    duplicate_chunk_violation_count: int = Field(ge=0)
    rank_order_violation_count: int = Field(ge=0)


class AggregateAnswerMetrics(EvaluationModel):
    """Micro-aggregated answer measures with explicit denominators."""

    expected_status_accuracy: RatioMetric
    citation_chunk_id_validity: RatioMetric
    citation_document_precision: RatioMetric
    citation_document_recall: RatioMetric
    unsupported_answer_citation_free_rate: RatioMetric
    historical_status_labelling_correctness: RatioMetric
    version_status_correctness: RatioMetric
    structural_grounding_violation_count: int = Field(ge=0)
    failed_case_count: int = Field(ge=0)


class EvaluationReport(EvaluationModel):
    """Complete deterministic Gate 5 report."""

    dataset_id: NonBlankString
    dataset_fingerprint: NonBlankString
    corpus_fingerprint: NonBlankString
    configuration_fingerprint: NonBlankString
    configuration: EvaluationConfig
    cases: tuple[CaseEvaluationResult, ...]
    retrieval: AggregateRetrievalMetrics
    answers: AggregateAnswerMetrics
