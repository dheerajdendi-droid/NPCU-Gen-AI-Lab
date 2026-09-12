"""Application-level errors raised by ingestion."""


class PdfIngestionError(Exception):
    """Base error for failures while ingesting a PDF."""


class InvalidPdfError(PdfIngestionError):
    """Raised when a file cannot be parsed as a valid PDF."""


class EncryptedPdfError(PdfIngestionError):
    """Raised when a PDF is encrypted and therefore outside Gate 1 scope."""


class ManifestValidationError(ValueError):
    """Raised when canonical corpus metadata and PDFs are inconsistent."""
