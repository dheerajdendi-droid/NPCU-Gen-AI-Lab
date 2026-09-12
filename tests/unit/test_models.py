"""Unit tests for provider-independent domain models."""

from datetime import date

import pytest
from pydantic import ValidationError

from cu_intelligence.domain.models import Chunk, Document, DocumentPage


def make_document(**overrides: object) -> Document:
    values = {
        "document_id": "policy-001",
        "title": "Member Lending Policy",
        "source": "synthetic/policies/member-lending.pdf",
        "document_type": "policy",
        "version": "1.0",
        "status": "approved",
        "effective_date": date(2026, 1, 1),
        "text": "Synthetic policy content.",
    }
    values.update(overrides)
    return Document.model_validate(values)


def make_chunk(**overrides: object) -> Chunk:
    values = {
        "chunk_id": "policy-001-000",
        "document_id": "policy-001",
        "text": "Synthetic policy content.",
        "chunk_index": 0,
        "section": "Purpose",
        "page_number": 1,
    }
    values.update(overrides)
    return Chunk.model_validate(values)


def test_valid_document_can_be_created() -> None:
    document = make_document()

    assert document.document_id == "policy-001"
    assert document.effective_date == date(2026, 1, 1)


def test_valid_chunk_can_be_created() -> None:
    chunk = make_chunk()

    assert chunk.document_id == "policy-001"
    assert chunk.chunk_index == 0


@pytest.mark.parametrize("document_id", ["", "   "])
def test_document_id_cannot_be_blank(document_id: str) -> None:
    with pytest.raises(ValidationError):
        make_document(document_id=document_id)


@pytest.mark.parametrize("field", ["title", "source", "document_type", "version", "status"])
@pytest.mark.parametrize("value", ["", "   "])
def test_required_document_descriptive_fields_cannot_be_blank(
    field: str,
    value: str,
) -> None:
    with pytest.raises(ValidationError):
        make_document(**{field: value})


@pytest.mark.parametrize("field", ["chunk_id", "document_id"])
@pytest.mark.parametrize("value", ["", "   "])
def test_chunk_identifiers_cannot_be_blank(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        make_chunk(**{field: value})


def test_chunk_index_cannot_be_negative() -> None:
    with pytest.raises(ValidationError):
        make_chunk(chunk_index=-1)


@pytest.mark.parametrize("page_number", [0, -1])
def test_chunk_page_number_must_be_one_based(page_number: int) -> None:
    with pytest.raises(ValidationError):
        make_chunk(page_number=page_number)


def test_chunk_page_number_is_required() -> None:
    values = make_chunk().model_dump()
    del values["page_number"]

    with pytest.raises(ValidationError):
        Chunk.model_validate(values)


@pytest.mark.parametrize("text", ["", "   ", "\r\n\t"])
def test_chunk_text_cannot_be_blank(text: str) -> None:
    with pytest.raises(ValidationError):
        make_chunk(text=text)


def test_document_metadata_is_retained() -> None:
    metadata = {"department": "lending", "synthetic": True}

    assert make_document(metadata=metadata).metadata == metadata


def test_chunk_metadata_is_retained() -> None:
    metadata = {"heading_level": 2, "reviewed": False}

    assert make_chunk(metadata=metadata).metadata == metadata


@pytest.mark.parametrize(
    "model, values",
    [
        (Document, {"unexpected": "value"}),
        (Chunk, {"unexpected": "value"}),
        (
            DocumentPage,
            {
                "document_id": "policy-001",
                "page_number": 1,
                "text": "Synthetic text.",
                "unexpected": "value",
            },
        ),
    ],
)
def test_domain_models_reject_unknown_fields(
    model: type[Document] | type[Chunk] | type[DocumentPage],
    values: dict[str, object],
) -> None:
    if model is Document:
        complete_values = make_document().model_dump() | values
    elif model is Chunk:
        complete_values = make_chunk().model_dump() | values
    else:
        complete_values = values

    with pytest.raises(ValidationError):
        model.model_validate(complete_values)


def test_document_page_requires_a_nonblank_document_id() -> None:
    with pytest.raises(ValidationError):
        DocumentPage(document_id=" ", page_number=1, text="Synthetic text.")


@pytest.mark.parametrize("page_number", [0, -1])
def test_document_page_number_must_be_one_based(page_number: int) -> None:
    with pytest.raises(ValidationError):
        DocumentPage(
            document_id="policy-001",
            page_number=page_number,
            text="Synthetic text.",
        )


def test_document_page_allows_empty_text() -> None:
    page = DocumentPage(document_id="policy-001", page_number=1, text="")

    assert page.text == ""
