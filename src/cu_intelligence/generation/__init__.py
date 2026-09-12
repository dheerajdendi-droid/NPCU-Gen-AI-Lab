"""Grounded generation boundaries, models, service, and OpenAI adapter."""

from cu_intelligence.generation.config import (
    GENERATION_API,
    GENERATION_MODEL,
    GENERATION_REASONING_EFFORT,
    GENERATION_STORE_RESPONSE,
    GENERATION_STRUCTURED_OUTPUT,
    GENERATION_TOOLS,
    GENERATION_TOP_K,
    GenerationConfig,
    OpenAIGenerationConfig,
    load_live_generation_config,
)
from cu_intelligence.generation.contracts import EvidenceRetriever, GenerationProvider
from cu_intelligence.generation.errors import (
    GenerationConfigurationError,
    GenerationError,
    GenerationModelAccessError,
    GenerationProviderError,
    GenerationResponseError,
    GroundingValidationError,
    InvalidQuestionError,
    StructuredOutputValidationError,
    UnknownCitationChunkError,
)
from cu_intelligence.generation.models import (
    AnswerStatus,
    CitationRecord,
    DraftStatement,
    GenerationDraft,
    GroundedAnswer,
    GroundedStatement,
    ProviderUsage,
)
from cu_intelligence.generation.openai_generation import OpenAIGenerationProvider
from cu_intelligence.generation.prompt import (
    GROUNDING_INSTRUCTIONS,
    GenerationPrompt,
    build_generation_prompt,
)
from cu_intelligence.generation.service import (
    NO_EVIDENCE_EXPLANATION,
    GroundedAnswerService,
    render_grounded_answer,
)

__all__ = [
    "GENERATION_API",
    "GENERATION_MODEL",
    "GENERATION_REASONING_EFFORT",
    "GENERATION_STORE_RESPONSE",
    "GENERATION_STRUCTURED_OUTPUT",
    "GENERATION_TOOLS",
    "GENERATION_TOP_K",
    "GROUNDING_INSTRUCTIONS",
    "NO_EVIDENCE_EXPLANATION",
    "AnswerStatus",
    "CitationRecord",
    "DraftStatement",
    "EvidenceRetriever",
    "GenerationConfig",
    "GenerationConfigurationError",
    "GenerationDraft",
    "GenerationError",
    "GenerationModelAccessError",
    "GenerationPrompt",
    "GenerationProvider",
    "GenerationProviderError",
    "GenerationResponseError",
    "GroundedAnswer",
    "GroundedAnswerService",
    "GroundedStatement",
    "GroundingValidationError",
    "InvalidQuestionError",
    "OpenAIGenerationConfig",
    "OpenAIGenerationProvider",
    "ProviderUsage",
    "StructuredOutputValidationError",
    "UnknownCitationChunkError",
    "build_generation_prompt",
    "load_live_generation_config",
    "render_grounded_answer",
]
