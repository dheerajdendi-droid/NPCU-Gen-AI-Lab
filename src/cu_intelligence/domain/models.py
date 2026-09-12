"""Provider-independent domain models used across the application."""

from datetime import date
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

NonBlankString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
type MetadataValue = str | int | float | bool


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
    text: NonBlankString
    chunk_index: int = Field(ge=0)
    section: str | None = None
    page_number: int = Field(ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentStatus(StrEnum):
    """Allowed lifecycle states in the canonical synthetic corpus."""

    CURRENT = "CURRENT"
    SUPERSEDED = "SUPERSEDED"


class CorpusDocument(DomainModel):
    """Validated manifest metadata for one canonical PDF document."""

    document_id: NonBlankString
    filename: NonBlankString
    title: NonBlankString
    version: NonBlankString
    status: DocumentStatus
    effective_date: date
    owner: NonBlankString
    synthetic: bool

    @field_validator("synthetic")
    @classmethod
    def require_synthetic_document(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("corpus documents must be synthetic")
        return value


class CorpusChunk(DomainModel):
    """A deterministic chunk enriched with validated manifest provenance."""

    chunk_id: NonBlankString
    document_id: NonBlankString
    text: NonBlankString
    chunk_index: int = Field(ge=0)
    page_number: int = Field(ge=1)
    title: NonBlankString
    version: NonBlankString
    document_status: DocumentStatus
    effective_date: date
    owner: NonBlankString
    source_filename: NonBlankString
    synthetic: bool


class CorpusBuild(DomainModel):
    """Validated documents and enriched chunks ready for embedding."""

    documents: tuple[CorpusDocument, ...]
    chunks: tuple[CorpusChunk, ...]


class VectorRecord(DomainModel):
    """Provider-independent vector record passed to a vector index boundary."""

    record_id: NonBlankString
    values: tuple[float, ...] = Field(min_length=1)
    metadata: dict[str, MetadataValue]


class VectorMatch(DomainModel):
    """Provider-independent scored match returned by a vector index boundary."""

    record_id: NonBlankString
    score: float = Field(allow_inf_nan=False)
    metadata: dict[str, MetadataValue]


class RetrievalResult(DomainModel):
    """Ranked evidence with the provenance needed for later citation work."""

    chunk_id: NonBlankString
    document_id: NonBlankString
    chunk_text: NonBlankString
    page_number: int = Field(ge=1)
    title: NonBlankString
    version: NonBlankString
    document_status: DocumentStatus
    effective_date: date
    owner: NonBlankString
    source_filename: NonBlankString
    synthetic: bool
    rank: int = Field(ge=1)
    similarity_score: float = Field(allow_inf_nan=False)


class IndexingSummary(DomainModel):
    """Counts returned after one corpus indexing operation."""

    document_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    upserted_count: int = Field(ge=0)
