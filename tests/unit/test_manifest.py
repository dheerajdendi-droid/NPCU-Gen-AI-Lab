"""Tests for strict canonical corpus manifest validation."""

import csv
from pathlib import Path

import pytest

from cu_intelligence.domain import DocumentStatus
from cu_intelligence.ingestion import ManifestValidationError, load_corpus_manifest

FIELDS = (
    "filename",
    "title",
    "version",
    "status",
    "effective_date",
    "owner",
    "synthetic",
)


def valid_row(filename: str = "policy_v1.pdf") -> dict[str, str]:
    return {
        "filename": filename,
        "title": "Synthetic Policy",
        "version": "1.0",
        "status": "CURRENT",
        "effective_date": "01 January 2026",
        "owner": "Policy Owner",
        "synthetic": "YES",
    }


def write_manifest(
    path: Path,
    rows: list[dict[str, str]],
    *,
    fields: tuple[str, ...] = FIELDS,
) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def make_corpus(tmp_path: Path, rows: list[dict[str, str]]) -> tuple[Path, Path]:
    pdf_dir = tmp_path / "policies"
    pdf_dir.mkdir()
    for row in rows:
        filename = row.get("filename", "")
        if filename and Path(filename).name == filename:
            (pdf_dir / filename).touch()
    manifest = tmp_path / "manifest.csv"
    write_manifest(manifest, rows)
    return manifest, pdf_dir


def test_repository_manifest_loads_all_canonical_pdfs() -> None:
    root = Path(__file__).parents[2]

    documents = load_corpus_manifest(
        root / "data" / "corpus_manifest.csv",
        pdf_directory=root / "data" / "raw" / "policies",
    )

    assert len(documents) == 11
    assert len({document.document_id for document in documents}) == 11
    assert all(document.synthetic for document in documents)
    lending_versions = [
        document
        for document in documents
        if document.title == "Lending and Affordability Policy"
    ]
    assert {(document.version, document.status) for document in lending_versions} == {
        ("4.0", DocumentStatus.CURRENT),
        ("3.1", DocumentStatus.SUPERSEDED),
    }


def test_document_id_and_date_are_derived_deterministically(tmp_path: Path) -> None:
    manifest, pdf_dir = make_corpus(tmp_path, [valid_row("Policy_One_v1.0.pdf")])

    document = load_corpus_manifest(manifest, pdf_directory=pdf_dir)[0]

    assert document.document_id == "Policy_One_v1.0"
    assert document.effective_date.isoformat() == "2026-01-01"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("title", " ", "title"),
        ("status", "DRAFT", "invalid status"),
        ("effective_date", "2026-01-01", "DD Month YYYY"),
        ("effective_date", "31 February 2026", "invalid effective_date"),
        ("synthetic", "NO", "synthetic must be YES"),
    ],
)
def test_malformed_rows_fail_clearly(
    tmp_path: Path,
    field: str,
    value: str,
    message: str,
) -> None:
    row = valid_row()
    row[field] = value
    manifest, pdf_dir = make_corpus(tmp_path, [row])

    with pytest.raises(ManifestValidationError, match=message):
        load_corpus_manifest(manifest, pdf_directory=pdf_dir)


def test_manifest_header_must_match_exact_contract(tmp_path: Path) -> None:
    pdf_dir = tmp_path / "policies"
    pdf_dir.mkdir()
    manifest = tmp_path / "manifest.csv"
    write_manifest(manifest, [], fields=FIELDS[:-1])

    with pytest.raises(ManifestValidationError, match="header must be exactly"):
        load_corpus_manifest(manifest, pdf_directory=pdf_dir)


def test_row_with_extra_values_is_rejected(tmp_path: Path) -> None:
    pdf_dir = tmp_path / "policies"
    pdf_dir.mkdir()
    (pdf_dir / "policy_v1.pdf").touch()
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(
        ",".join(FIELDS)
        + "\npolicy_v1.pdf,Synthetic Policy,1.0,CURRENT,01 January 2026,"
        "Policy Owner,YES,unexpected\n",
        encoding="utf-8",
    )

    with pytest.raises(ManifestValidationError, match="more values"):
        load_corpus_manifest(manifest, pdf_directory=pdf_dir)


def test_duplicate_filenames_are_rejected(tmp_path: Path) -> None:
    rows = [valid_row(), valid_row()]
    manifest, pdf_dir = make_corpus(tmp_path, rows)

    with pytest.raises(ManifestValidationError, match="Duplicate manifest filename"):
        load_corpus_manifest(manifest, pdf_directory=pdf_dir)


def test_filename_must_be_pdf_basename(tmp_path: Path) -> None:
    row = valid_row("nested/policy.pdf")
    manifest, pdf_dir = make_corpus(tmp_path, [row])

    with pytest.raises(ManifestValidationError, match="PDF basename"):
        load_corpus_manifest(manifest, pdf_directory=pdf_dir)


def test_missing_manifest_pdf_is_rejected(tmp_path: Path) -> None:
    manifest, pdf_dir = make_corpus(tmp_path, [valid_row()])
    (pdf_dir / "policy_v1.pdf").unlink()

    with pytest.raises(ManifestValidationError, match="missing PDFs: policy_v1.pdf"):
        load_corpus_manifest(manifest, pdf_directory=pdf_dir)


def test_unlisted_pdf_is_rejected(tmp_path: Path) -> None:
    manifest, pdf_dir = make_corpus(tmp_path, [valid_row()])
    (pdf_dir / "extra.pdf").touch()

    with pytest.raises(ManifestValidationError, match="unlisted PDFs: extra.pdf"):
        load_corpus_manifest(manifest, pdf_directory=pdf_dir)


@pytest.mark.parametrize("missing_target", ["manifest", "directory"])
def test_missing_paths_fail_clearly(tmp_path: Path, missing_target: str) -> None:
    manifest = tmp_path / "manifest.csv"
    pdf_dir = tmp_path / "policies"
    if missing_target == "manifest":
        pdf_dir.mkdir()
    else:
        write_manifest(manifest, [])

    with pytest.raises(ManifestValidationError, match="does not exist"):
        load_corpus_manifest(manifest, pdf_directory=pdf_dir)
