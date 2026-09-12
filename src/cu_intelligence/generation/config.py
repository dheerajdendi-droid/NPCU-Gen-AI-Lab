"""Single source of truth for the approved Gate 4 generation configuration."""

from dataclasses import dataclass
from typing import Final

from pydantic import BaseModel, ConfigDict, SecretStr, field_validator

from cu_intelligence.generation.errors import GenerationConfigurationError
from cu_intelligence.settings import Settings

GENERATION_MODEL: Final = "gpt-5.6-terra"
GENERATION_API: Final = "responses"
GENERATION_REASONING_EFFORT: Final = "low"
GENERATION_STRUCTURED_OUTPUT: Final = True
GENERATION_STORE_RESPONSE: Final = False
GENERATION_TOP_K: Final = 10
GENERATION_TOOLS: Final[tuple[()]] = ()


@dataclass(frozen=True, slots=True)
class GenerationConfig:
    """Validated immutable configuration for the sole Gate 4 answer path."""

    model: str = GENERATION_MODEL
    api: str = GENERATION_API
    reasoning_effort: str = GENERATION_REASONING_EFFORT
    structured_output: bool = GENERATION_STRUCTURED_OUTPUT
    store_response: bool = GENERATION_STORE_RESPONSE
    top_k: int = GENERATION_TOP_K
    tools: tuple[()] = GENERATION_TOOLS

    def __post_init__(self) -> None:
        expected = {
            "model": GENERATION_MODEL,
            "api": GENERATION_API,
            "reasoning_effort": GENERATION_REASONING_EFFORT,
            "structured_output": GENERATION_STRUCTURED_OUTPUT,
            "store_response": GENERATION_STORE_RESPONSE,
            "top_k": GENERATION_TOP_K,
            "tools": GENERATION_TOOLS,
        }
        actual = {
            "model": self.model,
            "api": self.api,
            "reasoning_effort": self.reasoning_effort,
            "structured_output": self.structured_output,
            "store_response": self.store_response,
            "top_k": self.top_k,
            "tools": self.tools,
        }
        mismatches = [name for name, value in actual.items() if value != expected[name]]
        if mismatches:
            raise GenerationConfigurationError(
                "Generation configuration differs from the approved Gate 4 values: "
                + ", ".join(mismatches)
            )


class OpenAIGenerationConfig(BaseModel):
    """Environment-only credential plus the explicit application configuration."""

    model_config = ConfigDict(extra="forbid")

    api_key: SecretStr
    generation: GenerationConfig = GenerationConfig()

    @field_validator("api_key")
    @classmethod
    def require_nonblank_key(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("OPENAI_API_KEY must not be blank")
        return value


def load_live_generation_config(settings: Settings | None = None) -> OpenAIGenerationConfig:
    """Load the existing OpenAI credential without exposing its value."""

    configured = settings or Settings()
    key = configured.openai_api_key
    if key is None or not key.get_secret_value().strip():
        raise GenerationConfigurationError(
            "Missing live generation setting: OPENAI_API_KEY"
        )
    return OpenAIGenerationConfig(api_key=key)
