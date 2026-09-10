"""Focused tests for PDF parser error behavior."""

from pathlib import Path

import pytest
from pypdf import PdfWriter

from cu_intelligence.ingestion import EncryptedPdfError, InvalidPdfError, parse_pdf


def test_missing_pdf_raises_file_not_found(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.pdf"

    with pytest.raises(FileNotFoundError, match="missing.pdf"):
        parse_pdf(missing_path, document_id="policy-001")


def test_invalid_pdf_raises_application_error(tmp_path: Path) -> None:
    invalid_path = tmp_path / "invalid.pdf"
    invalid_path.write_text("synthetic content that is not a PDF", encoding="utf-8")

    with pytest.raises(InvalidPdfError, match="Could not parse PDF"):
        parse_pdf(invalid_path, document_id="policy-001")


def test_encrypted_pdf_raises_application_error(tmp_path: Path) -> None:
    encrypted_path = tmp_path / "encrypted.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.encrypt("synthetic-password")
    with encrypted_path.open("wb") as pdf_file:
        writer.write(pdf_file)

    with pytest.raises(EncryptedPdfError, match="Encrypted PDFs are not supported"):
        parse_pdf(encrypted_path, document_id="policy-001")
