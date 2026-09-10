"""Provider-independent domain models used across the application."""

from datetime import date
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonBlankString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class DomainModel(BaseModel):
    """Shared validation policy for application-domain models."""

    model_config = ConfigDict(extra="forbid")


class Document(DomainModel):
    """A source document before any provider-specific processing."""

    document_id: NonBlankString
    title: NonBlankString
    source: NonBlankString
    document_type: NonBlankString
    version: NonBlankString
    status: NonBlankString
    effective_date: date | None = None
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentPage(DomainModel):
    """Text extracted from one source page of a document."""

    document_id: NonBlankString
    page_number: int = Field(ge=1)
    text: str


class Chunk(DomainModel):
    """A logical portion of a document, independent of any retrieval provider."""

    chunk_id: NonBlankString
    document_id: NonBlankString
    text: str
    chunk_index: int = Field(ge=0)
    section: str | None = None
    page: int | None = Field(default=None, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
