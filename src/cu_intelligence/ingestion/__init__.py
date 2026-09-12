"""Page-aware ingestion for synthetic, born-digital PDF documents."""

from cu_intelligence.ingestion.chunking import chunk_pages
from cu_intelligence.ingestion.errors import EncryptedPdfError, InvalidPdfError, PdfIngestionError
from cu_intelligence.ingestion.mapping import map_extracted_pages
from cu_intelligence.ingestion.pdf import parse_pdf

__all__ = [
    "EncryptedPdfError",
    "InvalidPdfError",
    "PdfIngestionError",
    "chunk_pages",
    "map_extracted_pages",
    "parse_pdf",
]
