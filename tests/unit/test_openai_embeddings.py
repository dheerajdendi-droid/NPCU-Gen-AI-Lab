"""Tests for OpenAI request/response mapping without network access."""

from types import SimpleNamespace
from typing import Any

import pytest

from cu_intelligence.retrieval import (
    VECTOR_DIMENSIONS,
    DimensionMismatchError,
    EmbeddingProviderError,
    OpenAIEmbeddingProvider,
)


class FakeEmbeddings:
    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def create(self, **arguments: Any) -> Any:
        self.calls.append(arguments)
        if self.error is not None:
            raise self.error
        return self.response


def client_with(embeddings: FakeEmbeddings) -> SimpleNamespace:
    return SimpleNamespace(embeddings=embeddings)


def vector(value: float) -> list[float]:
    return [value] * VECTOR_DIMENSIONS


def test_openai_request_and_out_of_order_response_are_mapped() -> None:
    response = SimpleNamespace(
        data=[
            SimpleNamespace(index=1, embedding=vector(0.2)),
            SimpleNamespace(index=0, embedding=vector(0.1)),
        ]
    )
    embeddings = FakeEmbeddings(response)
    provider = OpenAIEmbeddingProvider(client_with(embeddings))

    result = provider.embed(["first synthetic text", "second synthetic text"])

    assert embeddings.calls == [
        {
            "input": ["first synthetic text", "second synthetic text"],
            "model": "text-embedding-3-small",
            "dimensions": 1536,
        }
    ]
    assert result[0][0] == pytest.approx(0.1)
    assert result[1][0] == pytest.approx(0.2)
    assert all(len(item) == VECTOR_DIMENSIONS for item in result)


def test_empty_input_returns_without_provider_call() -> None:
    embeddings = FakeEmbeddings()
    provider = OpenAIEmbeddingProvider(client_with(embeddings))

    assert provider.embed([]) == []
    assert embeddings.calls == []


@pytest.mark.parametrize("text", ["", " ", "\r\n"])
def test_blank_embedding_input_is_rejected(text: str) -> None:
    provider = OpenAIEmbeddingProvider(client_with(FakeEmbeddings()))

    with pytest.raises(ValueError, match="must not be blank"):
        provider.embed([text])


def test_provider_failure_is_translated() -> None:
    provider = OpenAIEmbeddingProvider(
        client_with(FakeEmbeddings(error=RuntimeError("provider detail")))
    )

    with pytest.raises(EmbeddingProviderError, match="request failed") as captured:
        provider.embed(["synthetic text"])

    assert isinstance(captured.value.__cause__, RuntimeError)


def test_unexpected_response_dimension_is_rejected() -> None:
    response = SimpleNamespace(
        data=[SimpleNamespace(index=0, embedding=[0.1] * (VECTOR_DIMENSIONS - 1))]
    )
    provider = OpenAIEmbeddingProvider(client_with(FakeEmbeddings(response)))

    with pytest.raises(DimensionMismatchError, match="unexpected dimension"):
        provider.embed(["synthetic text"])


def test_unexpected_response_indexes_are_rejected() -> None:
    response = SimpleNamespace(
        data=[SimpleNamespace(index=1, embedding=vector(0.1))]
    )
    provider = OpenAIEmbeddingProvider(client_with(FakeEmbeddings(response)))

    with pytest.raises(EmbeddingProviderError, match="invalid embedding response"):
        provider.embed(["synthetic text"])


def test_unapproved_embedding_configuration_is_rejected() -> None:
    with pytest.raises(DimensionMismatchError, match="must use"):
        OpenAIEmbeddingProvider(
            client_with(FakeEmbeddings()),
            dimensions=512,
        )
