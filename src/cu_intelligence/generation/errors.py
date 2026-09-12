"""Application-owned grounded-generation errors."""


class GenerationError(Exception):
    """Base error for Gate 4 generation failures."""


class InvalidQuestionError(GenerationError, ValueError):
    """Raised when a grounded-answer question is not a nonblank string."""


class GenerationConfigurationError(GenerationError):
    """Raised when the approved generation configuration is missing or invalid."""


class GenerationModelAccessError(GenerationError):
    """Raised when the approved model is unavailable or unauthorized."""


class GenerationProviderError(GenerationError):
    """Raised when the generation provider request fails."""


class GenerationResponseError(GenerationError):
    """Raised for refused, incomplete, or malformed provider responses."""


class StructuredOutputValidationError(GenerationError):
    """Raised when parsed provider output cannot form an application draft."""


class GroundingValidationError(GenerationError):
    """Raised when a structured draft violates answer-grounding invariants."""


class UnknownCitationChunkError(GroundingValidationError):
    """Raised when a draft cites a chunk outside its exact evidence set."""
