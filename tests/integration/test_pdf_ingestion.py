"""Integration test using a real, synthetic, born-digital PDF fixture."""

from pathlib import Path

from cu_intelligence.ingestion import parse_pdf


def test_parse_synthetic_born_digital_pdf() -> None:
    fixture_path = Path(__file__).parents[1] / "fixtures" / "synthetic_member_policy.pdf"

    pages = parse_pdf(fixture_path, document_id="synthetic-member-policy")

    assert [page.page_number for page in pages] == [1, 2, 3]
    assert "Synthetic Member Lending Policy" in pages[0].text
    assert "Synthetic Operational Guidance" in pages[1].text
    assert pages[2].text == ""
    assert {page.document_id for page in pages} == {"synthetic-member-policy"}
