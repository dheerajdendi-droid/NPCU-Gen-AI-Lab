"""Tests for OpenAI Responses mapping without network access."""

from datetime import date
from types import SimpleNamespace
from typing import Any

import pytest
from openai import NotFoundError

from cu_intelligence.domain import DocumentStatus, RetrievalResult
from cu_intelligence.generation import (
    AnswerStatus,
    GenerationDraft,
    GenerationModelAccessError,
    GenerationProviderError,
    GenerationResponseError,
    OpenAIGenerationProvider,
    StructuredOutputValidationError,
)


def evidence() -> RetrievalResult:
    return RetrievalResult(
        chunk_id="policy:p0003:c000002",
        document_id="policy",
        chunk_text="Synthetic evidence.",
        page_number=3,
        title="Synthetic Policy",
        version="2.0",
        document_status=DocumentStatus.CURRENT,
        effective_date=date(2026, 1, 1),
        owner="Synthetic Owner",
        source_filename="policy.pdf",
        synthetic=True,
        rank=1,
        similarity_score=0.9,
    )


class FakeResponses:
    def __init__(
        self,
        payload: dict[str, Any] | None = None,
        *,
        status: str = "completed",
        error: Exception | None = None,
        refusal: bool = False,
    ) -> None:
        self.payload = payload
        self.status = status
        self.error = error
        self.refusal = refusal
        self.calls: list[dict[str, Any]] = []

    def parse(self, **arguments: Any) -> Any:
        self.calls.append(arguments)
        if self.error is not None:
            raise self.error
        parsed = None
        if self.payload is not None:
            parsed = arguments["text_format"].model_validate(self.payload)
        output = []
        if self.refusal:
            output = [
                SimpleNamespace(
                    content=[SimpleNamespace(type="refusal", refusal="safe refusal")]
                )
            ]
        return SimpleNamespace(
            status=self.status,
            output_parsed=parsed,
            output=output,
            usage=SimpleNamespace(
                input_tokens=101,
                output_tokens=22,
                total_tokens=123,
            ),
        )


def fake_client(responses: FakeResponses) -> SimpleNamespace:
    return SimpleNamespace(responses=responses)


def answered_payload() -> dict[str, Any]:
    return {
        "status": "ANSWERED",
        "statements": [
            {
                "text": "The evidence supports this statement.",
                "cited_chunk_ids": ["policy:p0003:c000002"],
            }
        ],
        "insufficient_evidence_explanation": None,
    }


def test_responses_structured_output_request_uses_exact_approved_configuration() -> None:
    responses = FakeResponses(answered_payload())
    provider = OpenAIGenerationProvider(fake_client(responses))

    draft = provider.generate("What is supported?", [evidence()])

    call = responses.calls[0]
    assert call["model"] == "gpt-5.6-terra"
    assert call["reasoning"] == {"effort": "low"}
    assert call["store"] is False
    assert call["tools"] == []
    assert call["text_format"].__name__ == "_StructuredDraft"
    assert "untrusted reference data" in call["instructions"]
    assert "policy:p0003:c000002" in call["input"]
    assert "web_search" not in repr(call)
    assert draft.status is AnswerStatus.ANSWERED


def test_provider_response_maps_to_application_owned_draft_and_usage() -> None:
    provider = OpenAIGenerationProvider(fake_client(FakeResponses(answered_payload())))

    result = provider.generate("Question?", [evidence()])

    assert type(result) is GenerationDraft
    assert result.statements[0].cited_chunk_ids == ("policy:p0003:c000002",)
    assert result.usage is not None
    assert result.usage.model_dump() == {
        "input_tokens": 101,
        "output_tokens": 22,
        "total_tokens": 123,
    }
    assert not result.__class__.__module__.startswith("openai")


def test_structured_output_schema_failure_is_translated() -> None:
    malformed = answered_payload() | {"unexpected": "provider field"}
    provider = OpenAIGenerationProvider(fake_client(FakeResponses(malformed)))

    with pytest.raises(StructuredOutputValidationError, match="schema validation"):
        provider.generate("Question?", [evidence()])


def test_incomplete_provider_response_is_rejected() -> None:
    provider = OpenAIGenerationProvider(
        fake_client(FakeResponses(answered_payload(), status="incomplete"))
    )

    with pytest.raises(GenerationResponseError, match="incomplete"):
        provider.generate("Question?", [evidence()])


def test_provider_refusal_is_rejected_without_exposing_response() -> None:
    provider = OpenAIGenerationProvider(
        fake_client(FakeResponses(payload=None, refusal=True))
    )

    with pytest.raises(GenerationResponseError, match="refused") as captured:
        provider.generate("Question?", [evidence()])

    assert "safe refusal" not in str(captured.value)


def test_missing_parsed_output_is_rejected_as_malformed() -> None:
    provider = OpenAIGenerationProvider(fake_client(FakeResponses(payload=None)))

    with pytest.raises(GenerationResponseError, match="structured output"):
        provider.generate("Question?", [evidence()])


def test_provider_request_exception_is_translated_with_safe_cause() -> None:
    provider = OpenAIGenerationProvider(
        fake_client(FakeResponses(error=RuntimeError("private provider detail")))
    )

    with pytest.raises(GenerationProviderError, match="request failed") as captured:
        provider.generate("Question?", [evidence()])

    assert "private provider detail" not in str(captured.value)
    assert isinstance(captured.value.__cause__, RuntimeError)


def test_unavailable_or_unauthorized_model_is_translated() -> None:
    response = SimpleNamespace(request="request", status_code=404, headers={})
    error = NotFoundError("model unavailable", response=response, body=None)
    provider = OpenAIGenerationProvider(fake_client(FakeResponses(error=error)))

    with pytest.raises(GenerationModelAccessError, match="unavailable or unauthorized"):
        provider.generate("Question?", [evidence()])
