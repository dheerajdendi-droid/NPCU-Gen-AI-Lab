"""Tests for strict loading of the protected Gate 5 dataset."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from cu_intelligence.evaluation import (
    EvaluationCase,
    EvaluationDatasetError,
    load_evaluation_dataset,
)
from cu_intelligence.ingestion import build_corpus

ROOT = Path(__file__).parents[2]
DATASET_PATH = ROOT / "data" / "_evaluation_do_not_index" / "gate5_cases.json"


@pytest.fixture(scope="module")
def corpus():  # type annotation would repeat the concrete application model
    return build_corpus(
        ROOT / "data" / "corpus_manifest.csv",
        pdf_directory=ROOT / "data" / "raw" / "policies",
    )


def _raw_dataset() -> dict:
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def _write_dataset(tmp_path: Path, raw: object) -> Path:
    directory = tmp_path / "_evaluation_do_not_index"
    directory.mkdir()
    path = directory / "cases.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    return path


def test_committed_dataset_has_required_coverage_and_known_sources(corpus) -> None:
    dataset = load_evaluation_dataset(DATASET_PATH, corpus=corpus)

    assert len(dataset.cases) == 20
    assert len({case.case_id for case in dataset.cases}) == 20
    assert sum(case.category.value == "CURRENT_POLICY" for case in dataset.cases) == 12
    assert sum(case.category.value == "MULTI_DOCUMENT" for case in dataset.cases) == 3
    assert sum(case.category.value == "UNSUPPORTED" for case in dataset.cases) == 3
    assert sum(
        case.category.value == "HISTORICAL_COMPARISON" for case in dataset.cases
    ) == 2


def test_malformed_json_is_rejected(tmp_path: Path, corpus) -> None:
    path = _write_dataset(tmp_path, {})
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(EvaluationDatasetError, match="Could not read"):
        load_evaluation_dataset(path, corpus=corpus)


def test_duplicate_case_ids_are_rejected(tmp_path: Path, corpus) -> None:
    raw = _raw_dataset()
    raw["cases"][1]["case_id"] = raw["cases"][0]["case_id"]

    with pytest.raises(EvaluationDatasetError, match="structural validation"):
        load_evaluation_dataset(_write_dataset(tmp_path, raw), corpus=corpus)


def test_unknown_manifest_document_is_rejected(tmp_path: Path, corpus) -> None:
    raw = _raw_dataset()
    raw["cases"][0]["forbidden_document_ids"] = ["unknown-policy"]

    with pytest.raises(EvaluationDatasetError, match="unknown corpus documents"):
        load_evaluation_dataset(_write_dataset(tmp_path, raw), corpus=corpus)


def test_invalid_expected_page_is_rejected(tmp_path: Path, corpus) -> None:
    raw = _raw_dataset()
    document_id = raw["cases"][0]["relevant_document_ids"][0]
    raw["cases"][0]["expected_evidence_pages"] = {document_id: [999]}

    with pytest.raises(EvaluationDatasetError, match="invalid populated pages"):
        load_evaluation_dataset(_write_dataset(tmp_path, raw), corpus=corpus)


def test_invalid_expected_status_is_rejected(tmp_path: Path, corpus) -> None:
    raw = _raw_dataset()
    raw["cases"][0]["expected_answer_status"] = "MAYBE"

    with pytest.raises(EvaluationDatasetError, match="structural validation"):
        load_evaluation_dataset(_write_dataset(tmp_path, raw), corpus=corpus)


def test_unsupported_case_cannot_declare_relevant_evidence() -> None:
    raw = _raw_dataset()["cases"][15]
    raw["relevant_document_ids"] = ["01_Member_Eligibility_Onboarding_Policy_v2.2"]

    with pytest.raises(ValidationError, match="unsupported cases cannot declare"):
        EvaluationCase.model_validate(raw)


def test_gate5_coverage_counts_are_enforced(tmp_path: Path, corpus) -> None:
    raw = _raw_dataset()
    raw["cases"] = raw["cases"][:-1]

    with pytest.raises(EvaluationDatasetError, match="exactly 20 cases"):
        load_evaluation_dataset(_write_dataset(tmp_path, raw), corpus=corpus)


def test_dataset_must_live_in_protected_directory(tmp_path: Path, corpus) -> None:
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(_raw_dataset()), encoding="utf-8")

    with pytest.raises(EvaluationDatasetError, match="must be stored"):
        load_evaluation_dataset(path, corpus=corpus)


def test_unknown_fields_are_rejected() -> None:
    raw = _raw_dataset()["cases"][0]
    raw["provider_hint"] = "not allowed"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        EvaluationCase.model_validate(raw)
