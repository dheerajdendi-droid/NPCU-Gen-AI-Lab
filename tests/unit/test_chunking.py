"""Unit tests for deterministic, page-aware word-window chunking."""

import pytest

from cu_intelligence.domain.models import DocumentPage
from cu_intelligence.ingestion import chunk_pages


def page(page_number: int, text: str, document_id: str = "policy-001") -> DocumentPage:
    return DocumentPage(document_id=document_id, page_number=page_number, text=text)


def test_no_pages_produce_no_chunks() -> None:
    assert chunk_pages([], max_words=5) == []


def test_short_text_produces_one_normalized_chunk() -> None:
    chunks = chunk_pages([page(1, "  Preserve\nCASE,\tand punctuation.  ")], max_words=10)

    assert len(chunks) == 1
    assert chunks[0].text == "Preserve CASE, and punctuation."


def test_text_exactly_at_maximum_produces_one_chunk() -> None:
    chunks = chunk_pages([page(1, "one two three four")], max_words=4)

    assert [chunk.text for chunk in chunks] == ["one two three four"]


def test_text_exceeding_maximum_produces_multiple_bounded_chunks() -> None:
    chunks = chunk_pages([page(1, "one two three four five six seven")], max_words=3)

    assert [chunk.text for chunk in chunks] == ["one two three", "four five six", "seven"]
    assert all(len(chunk.text.split()) <= 3 for chunk in chunks)


def test_adjacent_chunks_have_exact_configured_overlap() -> None:
    chunks = chunk_pages(
        [page(1, "one two three four five six seven")],
        max_words=4,
        overlap_words=2,
    )

    assert [chunk.text for chunk in chunks] == [
        "one two three four",
        "three four five six",
        "five six seven",
    ]
    assert chunks[0].text.split()[-2:] == chunks[1].text.split()[:2]
    assert chunks[1].text.split()[-2:] == chunks[2].text.split()[:2]


def test_repeated_chunking_is_deterministic() -> None:
    pages = [page(2, "one two three four five")]

    first = chunk_pages(pages, max_words=3, overlap_words=1)
    second = chunk_pages(pages, max_words=3, overlap_words=1)

    assert first == second
    assert [chunk.chunk_id for chunk in first] == [
        "policy-001:p0002:c000000",
        "policy-001:p0002:c000001",
    ]


def test_document_id_is_url_encoded_in_deterministic_chunk_id() -> None:
    chunks = chunk_pages([page(1, "synthetic text", "Policy / 001")], max_words=5)

    assert chunks[0].chunk_id == "Policy%20%2F%20001:p0001:c000000"
    assert chunks[0].document_id == "Policy / 001"


def test_indexes_are_zero_based_and_document_wide_across_pages() -> None:
    chunks = chunk_pages(
        [page(1, "one two three"), page(2, "four five six")],
        max_words=2,
    )

    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2, 3]
    assert [chunk.page_number for chunk in chunks] == [1, 1, 2, 2]


def test_chunks_never_combine_pages() -> None:
    chunks = chunk_pages(
        [page(1, "page-one-final"), page(2, "page-two-first")],
        max_words=10,
        overlap_words=2,
    )

    assert [chunk.text for chunk in chunks] == ["page-one-final", "page-two-first"]
    assert [chunk.page_number for chunk in chunks] == [1, 2]


def test_empty_pages_produce_no_chunks_without_shifting_provenance() -> None:
    chunks = chunk_pages(
        [page(1, "first page"), page(2, ""), page(3, "third page")],
        max_words=5,
    )

    assert [chunk.page_number for chunk in chunks] == [1, 3]
    assert [chunk.chunk_index for chunk in chunks] == [0, 1]
    assert chunks[1].chunk_id == "policy-001:p0003:c000001"


@pytest.mark.parametrize("text", [" ", "\t", "\r\n  \t"])
def test_whitespace_only_pages_produce_no_chunks(text: str) -> None:
    assert chunk_pages([page(4, text)], max_words=5) == []


@pytest.mark.parametrize("max_words", [0, -1, 1.5, True])
def test_invalid_max_words_fails_clearly(max_words: object) -> None:
    with pytest.raises(ValueError, match="max_words must be a positive integer"):
        chunk_pages([], max_words=max_words)  # type: ignore[arg-type]


@pytest.mark.parametrize("overlap_words", [-1, 1.5, True])
def test_invalid_overlap_type_or_sign_fails_clearly(overlap_words: object) -> None:
    with pytest.raises(ValueError, match="overlap_words must be a non-negative integer"):
        chunk_pages([], max_words=5, overlap_words=overlap_words)  # type: ignore[arg-type]


@pytest.mark.parametrize("overlap_words", [5, 6])
def test_overlap_must_be_smaller_than_maximum(overlap_words: int) -> None:
    with pytest.raises(ValueError, match="overlap_words must be smaller than max_words"):
        chunk_pages([], max_words=5, overlap_words=overlap_words)


def test_mixed_document_ids_are_rejected() -> None:
    pages = [page(1, "first", "policy-001"), page(2, "second", "policy-002")]

    with pytest.raises(ValueError, match="same document_id"):
        chunk_pages(pages, max_words=5)


@pytest.mark.parametrize("page_numbers", [(1, 1), (2, 1)])
def test_duplicate_or_out_of_order_pages_are_rejected(page_numbers: tuple[int, int]) -> None:
    pages = [page(number, f"page {number}") for number in page_numbers]

    with pytest.raises(ValueError, match="strictly increasing"):
        chunk_pages(pages, max_words=5)


def test_ordered_non_contiguous_page_subset_is_accepted() -> None:
    chunks = chunk_pages([page(2, "second"), page(5, "fifth")], max_words=5)

    assert [chunk.page_number for chunk in chunks] == [2, 5]


def test_non_page_input_is_rejected_at_runtime() -> None:
    with pytest.raises(TypeError, match="only DocumentPage"):
        chunk_pages(["not a page"], max_words=5)  # type: ignore[list-item]
