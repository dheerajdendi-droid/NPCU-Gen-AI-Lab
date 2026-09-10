"""Unit tests for provider-independent page mapping."""

import pytest
from pydantic import ValidationError

from cu_intelligence.ingestion import map_extracted_pages


def test_mapping_preserves_order_and_one_based_page_numbers() -> None:
    pages = map_extracted_pages(
        "policy-001",
        ["First synthetic page.", "Second synthetic page."],
    )

    assert [page.page_number for page in pages] == [1, 2]
    assert [page.document_id for page in pages] == ["policy-001", "policy-001"]
    assert [page.text for page in pages] == [
        "First synthetic page.",
        "Second synthetic page.",
    ]


def test_mapping_preserves_empty_pages() -> None:
    pages = map_extracted_pages("policy-001", ["First page.", None, "Third page."])

    assert len(pages) == 3
    assert pages[1].page_number == 2
    assert pages[1].text == ""


def test_mapping_validates_document_id_even_when_there_are_no_pages() -> None:
    with pytest.raises(ValidationError):
        map_extracted_pages(" ", [])


def test_mapping_rejects_non_text_page_content() -> None:
    with pytest.raises(ValidationError):
        map_extracted_pages("policy-001", [123])  # type: ignore[list-item]
