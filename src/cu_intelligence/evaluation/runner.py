"""Provider-independent orchestration for one evaluation baseline run."""

from collections.abc import Callable
from time import perf_counter

from cu_intelligence.domain import CorpusBuild, RetrievalResult
from cu_intelligence.evaluation.fingerprints import (
    fingerprint_configuration,
    fingerprint_corpus,
    fingerprint_dataset,
)
from cu_intelligence.evaluation.metrics import (
    aggregate_answers,
    aggregate_retrieval,
    score_answer,
    score_retrieval,
)
from cu_intelligence.evaluation.models import (
    CaseEvaluationResult,
    EvaluationConfig,
    EvaluationDataset,
    EvaluationReport,
    EvidenceReference,
    HumanReviewResult,
)
from cu_intelligence.generation import GenerationProvider, GroundedAnswerService
from cu_intelligence.generation.contracts import EvidenceRetriever


class _RecordingRetriever:
    """Capture the exact single retrieval used by grounded generation."""

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


class EvaluationRunner:
    """Evaluate each case with one retrieval and at most one generation call."""

    def __init__(
        self,
        retriever: EvidenceRetriever,
        generation_provider: GenerationProvider,
        *,
        corpus: CorpusBuild,
        config: EvaluationConfig | None = None,
        clock: Callable[[], float] = perf_counter,
    ) -> None:
        self._recording_retriever = _RecordingRetriever(retriever)
        self._answer_service = GroundedAnswerService(
            self._recording_retriever,
            generation_provider,
        )
        self._corpus = corpus
        self._config = config or EvaluationConfig()
        self._clock = clock

    def run(self, dataset: EvaluationDataset) -> EvaluationReport:
        """Return aggregate and per-case scores without leaking provider objects."""

        case_results: list[CaseEvaluationResult] = []
        for case in dataset.cases:
            started = self._clock()
            answer = None
            answer_metrics = None
            failure = None
            try:
                answer = self._answer_service.answer(
                    case.question,
                    include_superseded=case.include_superseded,
                )
                answer_metrics = score_answer(
                    case,
                    self._recording_retriever.last_results,
                    answer,
                )
            except Exception as error:  # provider failures belong in per-case reports
                failure = f"{type(error).__name__}: case execution failed"
            elapsed_ms = round(max(0.0, (self._clock() - started) * 1000), 3)
            evidence = self._recording_retriever.last_results
            case_results.append(
                CaseEvaluationResult(
                    case_id=case.case_id,
                    question=case.question,
                    category=case.category,
                    expected_answer_status=case.expected_answer_status,
                    evidence=tuple(_evidence_reference(item) for item in evidence),
                    retrieval_metrics=score_retrieval(
                        case,
                        evidence,
                        depth=self._config.retrieval_depth,
                    ),
                    answer=answer,
                    answer_metrics=answer_metrics,
                    usage=None if answer is None else answer.usage,
                    latency_ms=elapsed_ms,
                    failure=failure,
                    human_review=HumanReviewResult(case_id=case.case_id),
                )
            )

        ordered_results = tuple(case_results)
        return EvaluationReport(
            dataset_id=dataset.dataset_id,
            dataset_fingerprint=fingerprint_dataset(dataset),
            corpus_fingerprint=fingerprint_corpus(self._corpus),
            configuration_fingerprint=fingerprint_configuration(self._config),
            configuration=self._config,
            cases=ordered_results,
            retrieval=aggregate_retrieval(ordered_results),
            answers=aggregate_answers(ordered_results),
        )


def _evidence_reference(result: RetrievalResult) -> EvidenceReference:
    return EvidenceReference(
        chunk_id=result.chunk_id,
        document_id=result.document_id,
        document_status=result.document_status,
        page_number=result.page_number,
        rank=result.rank,
        similarity_score=result.similarity_score,
    )
