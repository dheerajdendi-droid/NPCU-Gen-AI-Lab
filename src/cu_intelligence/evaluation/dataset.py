"""Strict loading and corpus validation for the protected Gate 5 dataset."""

import json
from collections import Counter, defaultdict
from pathlib import Path

from pydantic import ValidationError

from cu_intelligence.domain import CorpusBuild, DocumentStatus
from cu_intelligence.evaluation.errors import EvaluationDatasetError
from cu_intelligence.evaluation.models import (
    EvaluationCategory,
    EvaluationDataset,
)

EVALUATION_DIRECTORY_NAME = "_evaluation_do_not_index"
EXPECTED_CASE_COUNTS = {
    EvaluationCategory.CURRENT_POLICY: 12,
    EvaluationCategory.MULTI_DOCUMENT: 3,
    EvaluationCategory.UNSUPPORTED: 3,
    EvaluationCategory.HISTORICAL_COMPARISON: 2,
}


def load_evaluation_dataset(
    dataset_path: str | Path,
    *,
    corpus: CorpusBuild,
    require_gate5_coverage: bool = True,
) -> EvaluationDataset:
    """Load strict JSON and validate every declared source against the corpus."""

    path = Path(dataset_path)
    if path.parent.name != EVALUATION_DIRECTORY_NAME:
        raise EvaluationDatasetError(
            f"Evaluation datasets must be stored under {EVALUATION_DIRECTORY_NAME}"
        )
    if not path.is_file():
        raise EvaluationDatasetError(f"Evaluation dataset does not exist: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise EvaluationDatasetError(f"Could not read evaluation dataset: {path}") from error
    try:
        dataset = EvaluationDataset.model_validate(raw)
    except ValidationError as error:
        raise EvaluationDatasetError("Evaluation dataset failed structural validation") from error

    _validate_against_corpus(dataset, corpus)
    if require_gate5_coverage:
        _validate_gate5_coverage(dataset, corpus)
    return dataset


def _validate_against_corpus(dataset: EvaluationDataset, corpus: CorpusBuild) -> None:
    documents = {document.document_id: document for document in corpus.documents}
    populated_pages: dict[str, set[int]] = defaultdict(set)
    for chunk in corpus.chunks:
        populated_pages[chunk.document_id].add(chunk.page_number)

    for case in dataset.cases:
        declared_ids = (
            set(case.relevant_document_ids)
            | set(case.required_citation_document_ids)
            | set(case.allowed_citation_document_ids)
            | set(case.forbidden_document_ids)
            | set(case.expected_evidence_pages)
        )
        unknown = sorted(declared_ids - set(documents))
        if unknown:
            raise EvaluationDatasetError(
                f"Case {case.case_id} names unknown corpus documents: {', '.join(unknown)}"
            )

        for document_id, expected_pages in case.expected_evidence_pages.items():
            invalid_pages = sorted(set(expected_pages) - populated_pages[document_id])
            if invalid_pages:
                raise EvaluationDatasetError(
                    f"Case {case.case_id} has invalid populated pages for {document_id}: "
                    + ", ".join(str(page) for page in invalid_pages)
                )

        relevant_statuses = {
            documents[document_id].status for document_id in case.relevant_document_ids
        }
        if case.category is EvaluationCategory.HISTORICAL_COMPARISON:
            if relevant_statuses != {DocumentStatus.CURRENT, DocumentStatus.SUPERSEDED}:
                raise EvaluationDatasetError(
                    f"Case {case.case_id} must reference current and superseded documents"
                )
        elif DocumentStatus.SUPERSEDED in relevant_statuses:
            raise EvaluationDatasetError(
                f"Case {case.case_id} cannot treat a superseded document as current evidence"
            )

        if (
            case.category is not EvaluationCategory.HISTORICAL_COMPARISON
            and DocumentStatus.SUPERSEDED not in case.forbidden_document_statuses
        ):
            raise EvaluationDatasetError(
                f"Case {case.case_id} must forbid unexpected superseded evidence"
            )


def _validate_gate5_coverage(
    dataset: EvaluationDataset,
    corpus: CorpusBuild,
) -> None:
    counts = Counter(case.category for case in dataset.cases)
    if counts != Counter(EXPECTED_CASE_COUNTS):
        expected = ", ".join(
            f"{category.value}={count}"
            for category, count in EXPECTED_CASE_COUNTS.items()
        )
        raise EvaluationDatasetError(f"Gate 5 requires exactly 20 cases: {expected}")

    current_ids = {
        document.document_id
        for document in corpus.documents
        if document.status is DocumentStatus.CURRENT
    }
    covered_current_ids = {
        document_id
        for case in dataset.cases
        if case.category is EvaluationCategory.CURRENT_POLICY
        for document_id in case.relevant_document_ids
    }
    missing = sorted(current_ids - covered_current_ids)
    if missing:
        raise EvaluationDatasetError(
            "Current-policy cases do not cover every current document: " + ", ".join(missing)
        )
