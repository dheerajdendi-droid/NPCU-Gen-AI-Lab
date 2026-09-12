"""Strict loading of the canonical synthetic corpus manifest."""

import csv
import re
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from cu_intelligence.domain import CorpusDocument, DocumentStatus
from cu_intelligence.ingestion.errors import ManifestValidationError

MANIFEST_FIELDS = (
    "filename",
    "title",
    "version",
    "status",
    "effective_date",
    "owner",
    "synthetic",
)

_DATE_PATTERN = re.compile(
    r"^(?P<day>\d{2}) "
    r"(?P<month>January|February|March|April|May|June|July|August|September|"
    r"October|November|December) "
    r"(?P<year>\d{4})$"
)
_MONTHS = {
    month: number
    for number, month in enumerate(
        (
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ),
        start=1,
    )
}


def load_corpus_manifest(
    manifest_path: str | Path,
    *,
    pdf_directory: str | Path,
) -> list[CorpusDocument]:
    """Load manifest rows and verify an exact one-to-one match with corpus PDFs."""

    path = Path(manifest_path)
    pdf_dir = Path(pdf_directory)
    if not path.is_file():
        raise ManifestValidationError(f"Manifest file does not exist: {path}")
    if not pdf_dir.is_dir():
        raise ManifestValidationError(f"PDF directory does not exist: {pdf_dir}")

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as manifest_file:
            reader = csv.DictReader(manifest_file)
            if tuple(reader.fieldnames or ()) != MANIFEST_FIELDS:
                raise ManifestValidationError(
                    "Manifest header must be exactly: " + ", ".join(MANIFEST_FIELDS)
                )
            rows = list(reader)
    except ManifestValidationError:
        raise
    except (OSError, UnicodeError, csv.Error) as error:
        raise ManifestValidationError(f"Could not read manifest: {path}") from error

    documents: list[CorpusDocument] = []
    filenames: set[str] = set()
    document_ids: set[str] = set()

    for row_number, row in enumerate(rows, start=2):
        if None in row:
            raise ManifestValidationError(
                f"Manifest row {row_number} has more values than the declared header"
            )
        filename = _required_value(row, "filename", row_number)
        filename_path = Path(filename)
        if filename_path.name != filename or filename_path.suffix.casefold() != ".pdf":
            raise ManifestValidationError(
                f"Manifest row {row_number} filename must be a PDF basename"
            )

        filename_key = filename.casefold()
        document_id = filename_path.stem
        document_id_key = document_id.casefold()
        if filename_key in filenames:
            raise ManifestValidationError(f"Duplicate manifest filename: {filename}")
        if document_id_key in document_ids:
            raise ManifestValidationError(f"Duplicate document ID: {document_id}")
        filenames.add(filename_key)
        document_ids.add(document_id_key)

        status_text = _required_value(row, "status", row_number)
        try:
            status = DocumentStatus(status_text)
        except ValueError as error:
            raise ManifestValidationError(
                f"Manifest row {row_number} has invalid status: {status_text}"
            ) from error

        synthetic_text = _required_value(row, "synthetic", row_number)
        if synthetic_text != "YES":
            raise ManifestValidationError(
                f"Manifest row {row_number} synthetic must be YES"
            )

        try:
            document = CorpusDocument(
                document_id=document_id,
                filename=filename,
                title=_required_value(row, "title", row_number),
                version=_required_value(row, "version", row_number),
                status=status,
                effective_date=_parse_effective_date(
                    _required_value(row, "effective_date", row_number),
                    row_number,
                ),
                owner=_required_value(row, "owner", row_number),
                synthetic=True,
            )
        except ValidationError as error:
            raise ManifestValidationError(
                f"Manifest row {row_number} failed validation"
            ) from error
        documents.append(document)

    available_pdf_names: dict[str, str] = {}
    for item in pdf_dir.iterdir():
        if not item.is_file() or item.suffix.casefold() != ".pdf":
            continue
        key = item.name.casefold()
        if key in available_pdf_names:
            raise ManifestValidationError(
                "PDF directory contains duplicate case-insensitive filenames: "
                f"{available_pdf_names[key]}, {item.name}"
            )
        available_pdf_names[key] = item.name
    missing = sorted(
        document.filename
        for document in documents
        if document.filename.casefold() not in available_pdf_names
    )
    unlisted = sorted(
        original_name
        for key, original_name in available_pdf_names.items()
        if key not in filenames
    )
    if missing or unlisted:
        details: list[str] = []
        if missing:
            details.append("missing PDFs: " + ", ".join(missing))
        if unlisted:
            details.append("unlisted PDFs: " + ", ".join(unlisted))
        raise ManifestValidationError("Corpus and manifest do not match; " + "; ".join(details))

    return documents


def _required_value(row: dict[str, str | None], field: str, row_number: int) -> str:
    value = row.get(field)
    if value is None or not value.strip():
        raise ManifestValidationError(
            f"Manifest row {row_number} field {field!r} must not be blank"
        )
    return value.strip()


def _parse_effective_date(value: str, row_number: int) -> date:
    match = _DATE_PATTERN.fullmatch(value)
    if match is None:
        raise ManifestValidationError(
            f"Manifest row {row_number} effective_date must use DD Month YYYY"
        )
    try:
        return date(
            int(match.group("year")),
            _MONTHS[match.group("month")],
            int(match.group("day")),
        )
    except ValueError as error:
        raise ManifestValidationError(
            f"Manifest row {row_number} has invalid effective_date: {value}"
        ) from error
