"""Page-aware ingestion for synthetic, born-digital PDF documents."""

from cu_intelligence.ingestion.chunking import chunk_pages
from cu_intelligence.ingestion.corpus import build_corpus
from cu_intelligence.ingestion.errors import (
    EncryptedPdfError,
    InvalidPdfError,
    ManifestValidationError,
    PdfIngestionError,
)
from cu_intelligence.ingestion.manifest import MANIFEST_FIELDS, load_corpus_manifest
from cu_intelligence.ingestion.mapping import map_extracted_pages
from cu_intelligence.ingestion.pdf import parse_pdf

__all__ = [
    "EncryptedPdfError",
    "InvalidPdfError",
    "MANIFEST_FIELDS",
    "ManifestValidationError",
    "PdfIngestionError",
    "build_corpus",
    "chunk_pages",
    "load_corpus_manifest",
    "map_extracted_pages",
    "parse_pdf",
]
