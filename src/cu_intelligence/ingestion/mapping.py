"""Map parser output to provider-independent page models."""

from collections.abc import Iterable

from pydantic import TypeAdapter

from cu_intelligence.domain.models import DocumentPage, NonBlankString

_document_id_adapter = TypeAdapter(NonBlankString)


def map_extracted_pages(
    document_id: str,
    extracted_texts: Iterable[str | None],
) -> list[DocumentPage]:
    """Create validated, one-based page results without dropping empty pages."""

    validated_document_id = _document_id_adapter.validate_python(document_id)
    return [
        DocumentPage(
            document_id=validated_document_id,
            page_number=page_number,
            text="" if text is None else text,
        )
        for page_number, text in enumerate(extracted_texts, start=1)
    ]

