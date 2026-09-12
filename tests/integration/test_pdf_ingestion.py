"""Integration test using a real, synthetic, born-digital PDF fixture."""

from pathlib import Path

from cu_intelligence.ingestion import chunk_pages, parse_pdf


def test_parse_synthetic_born_digital_pdf() -> None:
    fixture_path = Path(__file__).parents[1] / "fixtures" / "synthetic_member_policy.pdf"

    pages = parse_pdf(fixture_path, document_id="synthetic-member-policy")

    assert [page.page_number for page in pages] == [1, 2, 3]
    assert "Synthetic Member Lending Policy" in pages[0].text
    assert "Synthetic Operational Guidance" in pages[1].text
    assert pages[2].text == ""
    assert {page.document_id for page in pages} == {"synthetic-member-policy"}


def test_synthetic_pdf_to_deterministic_page_aware_chunks() -> None:
    fixture_path = Path(__file__).parents[1] / "fixtures" / "synthetic_member_policy.pdf"
    pages = parse_pdf(fixture_path, document_id="synthetic-member-policy")

    first = chunk_pages(pages, max_words=3, overlap_words=1)
    second = chunk_pages(pages, max_words=3, overlap_words=1)

    assert first == second
    assert first
    assert {chunk.document_id for chunk in first} == {"synthetic-member-policy"}
    assert {chunk.page_number for chunk in first} == {1, 2}
    assert all(chunk.page_number != 3 for chunk in first)
    assert all(len(chunk.text.split()) <= 3 for chunk in first)
    assert [chunk.chunk_index for chunk in first] == list(range(len(first)))
    assert [chunk.chunk_id for chunk in first] == [
        f"synthetic-member-policy:p{chunk.page_number:04d}:c{chunk.chunk_index:06d}"
        for chunk in first
    ]
    assert any("Synthetic Member Lending" in chunk.text for chunk in first)
    assert any("Synthetic Operational Guidance" in chunk.text for chunk in first)
