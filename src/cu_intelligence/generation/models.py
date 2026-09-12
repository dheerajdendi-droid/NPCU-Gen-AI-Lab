"""Provider-independent models for structured drafts and grounded answers."""

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from cu_intelligence.domain import DocumentStatus

NonBlankString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
PositiveCitationNumber = Annotated[int, Field(ge=1)]


class GenerationModel(BaseModel):
    """Shared strict validation for application-owned generation values."""

    model_config = ConfigDict(extra="forbid")


class AnswerStatus(StrEnum):
    """Grounded-answer outcomes exposed by the application."""

    ANSWERED = "ANSWERED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ProviderUsage(GenerationModel):
    """Provider-independent token counts retained for cost learning."""

    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)


class DraftStatement(GenerationModel):
    """One provider-proposed statement and its claimed evidence IDs."""

    text: NonBlankString
    cited_chunk_ids: tuple[NonBlankString, ...]


class GenerationDraft(GenerationModel):
    """Application-owned structured draft returned by a generation boundary."""

    status: AnswerStatus
    statements: tuple[DraftStatement, ...]
    insufficient_evidence_explanation: str | None
    usage: ProviderUsage | None = None


class GroundedStatement(GenerationModel):
    """A validated readable statement linked to stable citation numbers."""

    text: NonBlankString
    citation_numbers: tuple[PositiveCitationNumber, ...] = Field(min_length=1)


class CitationRecord(GenerationModel):
    """Authoritative provenance constructed from a retrieved evidence chunk."""

    citation_number: int = Field(ge=1)
    document_id: NonBlankString
    title: NonBlankString
    version: NonBlankString
    document_status: DocumentStatus
    page_number: int = Field(ge=1)
    source_filename: NonBlankString
    chunk_id: NonBlankString


class GroundedAnswer(GenerationModel):
    """Fully validated provider-independent answer or safe abstention."""

    status: AnswerStatus
    question: NonBlankString
    statements: tuple[GroundedStatement, ...]
    citations: tuple[CitationRecord, ...]
    insufficient_evidence_explanation: str | None
    rendered_answer: NonBlankString
    usage: ProviderUsage | None = None

    @model_validator(mode="after")
    def validate_status_content(self) -> "GroundedAnswer":
        if self.status is AnswerStatus.ANSWERED:
            if not self.statements or not self.citations:
                raise ValueError("answered results require statements and citations")
            if self.insufficient_evidence_explanation is not None:
                raise ValueError("answered results cannot contain an insufficient explanation")
            known_numbers = {citation.citation_number for citation in self.citations}
            if any(
                number not in known_numbers
                for statement in self.statements
                for number in statement.citation_numbers
            ):
                raise ValueError("statement citation numbers must reference a citation record")
        else:
            if self.statements or self.citations:
                raise ValueError("insufficient results cannot contain statements or citations")
            explanation = self.insufficient_evidence_explanation
            if explanation is None or not explanation.strip():
                raise ValueError("insufficient results require a nonblank explanation")
        return self
