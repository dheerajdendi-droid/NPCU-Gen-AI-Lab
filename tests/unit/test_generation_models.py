"""Tests for provider-independent Gate 4 models and configuration."""

import pytest
from pydantic import ValidationError

from cu_intelligence.domain import DocumentStatus
from cu_intelligence.generation import (
    AnswerStatus,
    CitationRecord,
    GenerationConfig,
    GenerationConfigurationError,
    GroundedAnswer,
    GroundedStatement,
)


def citation(**overrides: object) -> CitationRecord:
    values = {
        "citation_number": 1,
        "document_id": "policy-current",
        "title": "Synthetic Policy",
        "version": "2.0",
        "document_status": DocumentStatus.CURRENT,
        "page_number": 3,
        "source_filename": "policy-current.pdf",
        "chunk_id": "policy-current:p0003:c000002",
    }
    values.update(overrides)
    return CitationRecord.model_validate(values)


def test_answered_domain_result_requires_supported_content() -> None:
    answer = GroundedAnswer(
        status=AnswerStatus.ANSWERED,
        question="What is the rule?",
        statements=(GroundedStatement(text="The rule is synthetic.", citation_numbers=(1,)),),
        citations=(citation(),),
        insufficient_evidence_explanation=None,
        rendered_answer="The rule is synthetic. [1]",
    )

    assert answer.citations[0].page_number == 3


@pytest.mark.parametrize(
    "overrides",
    [
        {"statements": ()},
        {"citations": ()},
        {"insufficient_evidence_explanation": "Not enough."},
    ],
)
def test_answered_domain_result_rejects_invalid_status_content(
    overrides: dict[str, object],
) -> None:
    values = {
        "status": AnswerStatus.ANSWERED,
        "question": "What is the rule?",
        "statements": (
            GroundedStatement(text="The rule is synthetic.", citation_numbers=(1,)),
        ),
        "citations": (citation(),),
        "insufficient_evidence_explanation": None,
        "rendered_answer": "The rule is synthetic. [1]",
    }
    values.update(overrides)

    with pytest.raises(ValidationError):
        GroundedAnswer.model_validate(values)


def test_insufficient_domain_result_rejects_fabricated_content() -> None:
    with pytest.raises(ValidationError, match="cannot contain statements"):
        GroundedAnswer(
            status=AnswerStatus.INSUFFICIENT_EVIDENCE,
            question="Unsupported question?",
            statements=(GroundedStatement(text="Invented.", citation_numbers=(1,)),),
            citations=(citation(),),
            insufficient_evidence_explanation="Not enough evidence.",
            rendered_answer="Insufficient evidence.",
        )


def test_citation_requires_positive_one_based_page() -> None:
    with pytest.raises(ValidationError):
        citation(page_number=0)


def test_statement_requires_positive_citation_numbers() -> None:
    with pytest.raises(ValidationError):
        GroundedStatement(text="Synthetic statement.", citation_numbers=(0,))


def test_generation_models_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        CitationRecord.model_validate(citation().model_dump() | {"provider_id": "raw"})


def test_generation_configuration_is_exact_and_rejects_changes() -> None:
    config = GenerationConfig()

    assert config.model == "gpt-5.6-terra"
    assert config.api == "responses"
    assert config.reasoning_effort == "low"
    assert config.structured_output is True
    assert config.store_response is False
    assert config.top_k == 10
    assert config.tools == ()

    with pytest.raises(GenerationConfigurationError, match="model"):
        GenerationConfig(model="another-model")
