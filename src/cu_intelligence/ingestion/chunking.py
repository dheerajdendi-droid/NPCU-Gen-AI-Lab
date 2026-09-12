"""Deterministic, page-bounded word-window chunking."""

from collections.abc import Iterable
from urllib.parse import quote

from cu_intelligence.domain.models import Chunk, DocumentPage


def chunk_pages(
    pages: Iterable[DocumentPage],
    *,
    max_words: int,
    overlap_words: int = 0,
) -> list[Chunk]:
    """Transform ordered pages from one document into deterministic word chunks."""

    _validate_configuration(max_words, overlap_words)

    chunks: list[Chunk] = []
    document_id: str | None = None
    previous_page_number: int | None = None

    for page in pages:
        if not isinstance(page, DocumentPage):
            raise TypeError("pages must contain only DocumentPage values")

        if document_id is None:
            document_id = page.document_id
        elif page.document_id != document_id:
            raise ValueError("all pages must belong to the same document_id")

        if previous_page_number is not None and page.page_number <= previous_page_number:
            raise ValueError("page numbers must be strictly increasing")
        previous_page_number = page.page_number

        words = page.text.split()
        if not words:
            continue

        step = max_words - overlap_words
        start = 0
        while start < len(words):
            window = words[start : start + max_words]
            chunk_index = len(chunks)
            chunks.append(
                Chunk(
                    chunk_id=_make_chunk_id(document_id, page.page_number, chunk_index),
                    document_id=document_id,
                    text=" ".join(window),
                    chunk_index=chunk_index,
                    page_number=page.page_number,
                )
            )

            if start + max_words >= len(words):
                break
            start += step

    return chunks


def _validate_configuration(max_words: int, overlap_words: int) -> None:
    if isinstance(max_words, bool) or not isinstance(max_words, int) or max_words <= 0:
        raise ValueError("max_words must be a positive integer")
    if isinstance(overlap_words, bool) or not isinstance(overlap_words, int):
        raise ValueError("overlap_words must be a non-negative integer")
    if overlap_words < 0:
        raise ValueError("overlap_words must be a non-negative integer")
    if overlap_words >= max_words:
        raise ValueError("overlap_words must be smaller than max_words")


def _make_chunk_id(document_id: str, page_number: int, chunk_index: int) -> str:
    encoded_document_id = quote(document_id, safe="-._~")
    return f"{encoded_document_id}:p{page_number:04d}:c{chunk_index:06d}"
