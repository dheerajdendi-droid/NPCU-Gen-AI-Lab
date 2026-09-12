"""OpenAI embedding adapter kept behind the application embedding boundary."""

from collections.abc import Sequence
from math import isfinite
from typing import Any

from openai import OpenAI

from cu_intelligence.retrieval.config import (
    EMBEDDING_MODEL,
    VECTOR_DIMENSIONS,
    OpenAIEmbeddingConfig,
)
from cu_intelligence.retrieval.errors import (
    DimensionMismatchError,
    EmbeddingProviderError,
)


class OpenAIEmbeddingProvider:
    """Map OpenAI embeddings to ordered application-owned float tuples."""

    def __init__(
        self,
        client: Any,
        *,
        model: str = EMBEDDING_MODEL,
        dimensions: int = VECTOR_DIMENSIONS,
    ) -> None:
        if model != EMBEDDING_MODEL or dimensions != VECTOR_DIMENSIONS:
            raise DimensionMismatchError(
                "OpenAI embedding configuration must use "
                f"{EMBEDDING_MODEL} with {VECTOR_DIMENSIONS} dimensions"
            )
        self._client = client
        self.model = model
        self.dimensions = dimensions

    @classmethod
    def from_config(cls, config: OpenAIEmbeddingConfig) -> "OpenAIEmbeddingProvider":
        """Construct the live adapter without exposing the credential."""

        client = OpenAI(api_key=config.api_key.get_secret_value())
        return cls(client)

    def embed(self, texts: Sequence[str]) -> list[tuple[float, ...]]:
        """Embed nonblank texts and validate provider ordering and dimensions."""

        if isinstance(texts, (str, bytes)):
            raise TypeError("texts must be a sequence of strings")
        values = list(texts)
        for text in values:
            if not isinstance(text, str):
                raise TypeError("texts must contain only strings")
            if not text.strip():
                raise ValueError("embedding text must not be blank")
        if not values:
            return []

        try:
            response = self._client.embeddings.create(
                input=values,
                model=self.model,
                dimensions=self.dimensions,
            )
        except Exception as error:
            raise EmbeddingProviderError("OpenAI embedding request failed") from error

        try:
            data = sorted(response.data, key=lambda item: item.index)
            if [item.index for item in data] != list(range(len(values))):
                raise ValueError("embedding response indexes do not match request")

            embeddings = [
                tuple(float(component) for component in item.embedding) for item in data
            ]
            for embedding in embeddings:
                if len(embedding) != self.dimensions:
                    raise DimensionMismatchError(
                        "OpenAI returned a vector with an unexpected dimension"
                    )
                if not all(isfinite(component) for component in embedding):
                    raise ValueError("embedding contains a non-finite value")
            return embeddings
        except DimensionMismatchError:
            raise
        except (AttributeError, TypeError, ValueError) as error:
            raise EmbeddingProviderError("OpenAI returned an invalid embedding response") from error
