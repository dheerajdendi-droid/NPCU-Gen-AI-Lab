"""Metadata-aware semantic retrieval boundaries and adapters."""

from cu_intelligence.retrieval.config import (
    EMBEDDING_MODEL,
    PINECONE_CLOUD,
    PINECONE_REGION,
    SIMILARITY_METRIC,
    VECTOR_DIMENSIONS,
    VECTOR_TYPE,
    LiveRetrievalConfig,
    OpenAIEmbeddingConfig,
    PineconeIndexConfig,
    load_live_retrieval_config,
)
from cu_intelligence.retrieval.contracts import EmbeddingProvider, VectorIndex
from cu_intelligence.retrieval.errors import (
    DimensionMismatchError,
    EmbeddingProviderError,
    RetrievalConfigurationError,
    RetrievalError,
    VectorIndexError,
)
from cu_intelligence.retrieval.openai_embeddings import OpenAIEmbeddingProvider
from cu_intelligence.retrieval.pinecone_index import PineconeVectorIndex
from cu_intelligence.retrieval.service import SemanticRetrievalService, build_vector_records
from cu_intelligence.retrieval.smoke_questions import RETRIEVAL_SMOKE_QUESTIONS

__all__ = [
    "EMBEDDING_MODEL",
    "PINECONE_CLOUD",
    "PINECONE_REGION",
    "RETRIEVAL_SMOKE_QUESTIONS",
    "SIMILARITY_METRIC",
    "VECTOR_DIMENSIONS",
    "VECTOR_TYPE",
    "DimensionMismatchError",
    "EmbeddingProvider",
    "EmbeddingProviderError",
    "LiveRetrievalConfig",
    "OpenAIEmbeddingConfig",
    "OpenAIEmbeddingProvider",
    "PineconeIndexConfig",
    "PineconeVectorIndex",
    "RetrievalConfigurationError",
    "RetrievalError",
    "SemanticRetrievalService",
    "VectorIndex",
    "VectorIndexError",
    "build_vector_records",
    "load_live_retrieval_config",
]
