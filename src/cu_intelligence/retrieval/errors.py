"""Application-level retrieval and provider errors."""


class RetrievalError(Exception):
    """Base error for Gate 3 retrieval failures."""


class RetrievalConfigurationError(RetrievalError):
    """Raised when required live-provider configuration is missing or invalid."""


class EmbeddingProviderError(RetrievalError):
    """Raised when embedding generation fails or returns an invalid response."""


class VectorIndexError(RetrievalError):
    """Raised when vector-index configuration or data operations fail."""


class DimensionMismatchError(RetrievalError):
    """Raised when a vector does not use the accepted Gate 3 dimensions."""
