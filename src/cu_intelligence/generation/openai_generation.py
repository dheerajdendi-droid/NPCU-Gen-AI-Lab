"""OpenAI Responses adapter kept behind the generation boundary."""

from collections.abc import Mapping, Sequence
from typing import Any, Literal

from openai import AuthenticationError, NotFoundError, OpenAI, PermissionDeniedError
from pydantic import BaseModel, ConfigDict, ValidationError

from cu_intelligence.domain import RetrievalResult
from cu_intelligence.generation.config import GenerationConfig, OpenAIGenerationConfig
from cu_intelligence.generation.errors import (
    GenerationModelAccessError,
    GenerationProviderError,
    GenerationResponseError,
    StructuredOutputValidationError,
)
from cu_intelligence.generation.models import GenerationDraft, ProviderUsage
from cu_intelligence.generation.prompt import build_generation_prompt


class _StructuredStatement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    cited_chunk_ids: list[str]


class _StructuredDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ANSWERED", "INSUFFICIENT_EVIDENCE"]
    statements: list[_StructuredStatement]
    insufficient_evidence_explanation: str | None


class OpenAIGenerationProvider:
    """Map a parsed OpenAI response to an application-owned structured draft."""

    def __init__(
        self,
        client: Any,
        *,
        config: GenerationConfig | None = None,
    ) -> None:
        self._client = client
        self.config = config or GenerationConfig()

    @classmethod
    def from_config(cls, config: OpenAIGenerationConfig) -> "OpenAIGenerationProvider":
        """Construct the live adapter without exposing its credential."""

        client = OpenAI(api_key=config.api_key.get_secret_value())
        return cls(client, config=config.generation)

    def generate(
        self,
        question: str,
        evidence: Sequence[RetrievalResult],
    ) -> GenerationDraft:
        """Call Responses Structured Outputs and map only application-owned values."""

        prompt = build_generation_prompt(question, evidence)
        try:
            response = self._client.responses.parse(
                model=self.config.model,
                instructions=prompt.instructions,
                input=prompt.user_content,
                reasoning={"effort": self.config.reasoning_effort},
                text_format=_StructuredDraft,
                store=self.config.store_response,
                tools=list(self.config.tools),
            )
        except ValidationError as error:
            raise StructuredOutputValidationError(
                "OpenAI structured output failed schema validation"
            ) from error
        except (AuthenticationError, PermissionDeniedError, NotFoundError) as error:
            raise GenerationModelAccessError(
                "The approved OpenAI generation model is unavailable or unauthorized"
            ) from error
        except Exception as error:
            raise GenerationProviderError("OpenAI generation request failed") from error

        if _read(response, "status") != "completed":
            raise GenerationResponseError("OpenAI generation response was incomplete")
        parsed = _read(response, "output_parsed")
        if parsed is None:
            if _contains_refusal(response):
                raise GenerationResponseError("OpenAI generation response was refused")
            raise GenerationResponseError(
                "OpenAI generation response did not contain structured output"
            )

        try:
            raw_draft = parsed.model_dump() if isinstance(parsed, BaseModel) else parsed
            usage = _map_usage(_read(response, "usage"))
            return GenerationDraft.model_validate(raw_draft).model_copy(
                update={"usage": usage}
            )
        except (AttributeError, TypeError, ValidationError, ValueError) as error:
            raise StructuredOutputValidationError(
                "OpenAI structured output failed application validation"
            ) from error


def _map_usage(raw_usage: Any) -> ProviderUsage | None:
    if raw_usage is None:
        return None
    try:
        return ProviderUsage(
            input_tokens=_read(raw_usage, "input_tokens"),
            output_tokens=_read(raw_usage, "output_tokens"),
            total_tokens=_read(raw_usage, "total_tokens"),
        )
    except (TypeError, ValidationError, ValueError):
        return None


def _contains_refusal(response: Any) -> bool:
    output = _read(response, "output") or []
    for item in output:
        for content in _read(item, "content") or []:
            if _read(content, "type") == "refusal" or _read(content, "refusal"):
                return True
    return False


def _read(value: Any, key: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(key)
    return getattr(value, key, None)
