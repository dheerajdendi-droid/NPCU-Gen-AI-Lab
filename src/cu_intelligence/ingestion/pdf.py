"""PDF parsing kept behind the application ingestion boundary."""

from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from cu_intelligence.domain.models import DocumentPage
from cu_intelligence.ingestion.errors import EncryptedPdfError, InvalidPdfError
from cu_intelligence.ingestion.mapping import map_extracted_pages


def parse_pdf(path: str | Path, *, document_id: str) -> list[DocumentPage]:
    """Extract text from each page of a born-digital PDF in source order."""

    pdf_path = Path(path)
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)

    try:
        reader = PdfReader(pdf_path)
        if reader.is_encrypted:
            raise EncryptedPdfError(f"Encrypted PDFs are not supported: {pdf_path}")
        extracted_texts = [page.extract_text() for page in reader.pages]
    except EncryptedPdfError:
        raise
    except (OSError, PdfReadError, ValueError) as error:
        raise InvalidPdfError(f"Could not parse PDF: {pdf_path}") from error

    return map_extracted_pages(document_id, extracted_texts)
