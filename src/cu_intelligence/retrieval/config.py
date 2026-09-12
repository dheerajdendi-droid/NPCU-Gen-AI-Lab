"""Approved Gate 3 provider configuration and environment mapping."""

from typing import Final

from pydantic import BaseModel, ConfigDict, SecretStr, field_validator

from cu_intelligence.retrieval.errors import RetrievalConfigurationError
from cu_intelligence.settings import Settings

EMBEDDING_MODEL: Final = "text-embedding-3-small"
VECTOR_TYPE: Final = "dense"
VECTOR_DIMENSIONS: Final = 1536
SIMILARITY_METRIC: Final = "cosine"
PINECONE_CLOUD: Final = "aws"
PINECONE_REGION: Final = "us-east-1"


class OpenAIEmbeddingConfig(BaseModel):
    """OpenAI-only settings for the embedding boundary."""

    model_config = ConfigDict(extra="forbid")

    api_key: SecretStr

    @field_validator("api_key")
    @classmethod
    def require_nonblank_key(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("OPENAI_API_KEY must not be blank")
        return value


class PineconeIndexConfig(BaseModel):
    """Pinecone-only settings for the vector-index boundary."""

    model_config = ConfigDict(extra="forbid")

    api_key: SecretStr
    index_name: str
    namespace: str

    @field_validator("api_key")
    @classmethod
    def require_nonblank_key(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("PINECONE_API_KEY must not be blank")
        return value

    @field_validator("index_name", "namespace")
    @classmethod
    def require_nonblank_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Pinecone index name and namespace must not be blank")
        return stripped


class LiveRetrievalConfig(BaseModel):
    """Combined live smoke configuration with separate provider subcontracts."""

    model_config = ConfigDict(extra="forbid")

    embeddings: OpenAIEmbeddingConfig
    vector_index: PineconeIndexConfig


def load_live_retrieval_config(settings: Settings | None = None) -> LiveRetrievalConfig:
    """Require every setting needed by the explicitly opted-in live path."""

    configured = settings or Settings()
    required = {
        "OPENAI_API_KEY": configured.openai_api_key,
        "PINECONE_API_KEY": configured.pinecone_api_key,
        "PINECONE_INDEX_NAME": configured.pinecone_index_name,
        "PINECONE_NAMESPACE": configured.pinecone_namespace,
    }
    missing = [
        name
        for name, value in required.items()
        if value is None
        or (isinstance(value, SecretStr) and not value.get_secret_value().strip())
    ]
    if missing:
        raise RetrievalConfigurationError(
            "Missing live retrieval settings: " + ", ".join(missing)
        )

    return LiveRetrievalConfig(
        embeddings=OpenAIEmbeddingConfig(api_key=configured.openai_api_key),
        vector_index=PineconeIndexConfig(
            api_key=configured.pinecone_api_key,
            index_name=configured.pinecone_index_name,
            namespace=configured.pinecone_namespace,
        ),
    )
