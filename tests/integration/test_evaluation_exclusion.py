"""Prove protected evaluation data cannot enter the canonical corpus path."""

from pathlib import Path

import pytest

from cu_intelligence.domain import DocumentPage
from cu_intelligence.evaluation import load_evaluation_dataset
from cu_intelligence.ingestion import build_corpus, chunk_pages, parse_pdf
from cu_intelligence.ingestion.errors import InvalidPdfError
from cu_intelligence.retrieval import SemanticRetrievalService

ROOT = Path(__file__).parents[2]
EVALUATION_PATH = ROOT / "data" / "_evaluation_do_not_index" / "gate5_cases.json"


class RecordingEmbeddings:
    dimensions = 1536

    def __init__(self) -> None:
        self.inputs: list[tuple[str, ...]] = []

    def embed(self, texts):
        values = tuple(texts)
        self.inputs.append(values)
        return [(1.0,) + (0.0,) * 1535 for _ in values]


class RecordingIndex:
    dimensions = 1536

    def __init__(self) -> None:
        self.records = ()

    def upsert(self, records):
        self.records = tuple(records)
        return len(self.records)

    def query(self, vector, *, top_k, status_filter):
        return []


def test_evaluation_directory_is_not_corpus_or_answer_evidence() -> None:
    corpus = build_corpus(
        ROOT / "data" / "corpus_manifest.csv",
        pdf_directory=ROOT / "data" / "raw" / "policies",
    )
    dataset = load_evaluation_dataset(EVALUATION_PATH, corpus=corpus)

    assert EVALUATION_PATH.suffix == ".json"
    assert EVALUATION_PATH.parent != ROOT / "data" / "raw" / "policies"
    assert len(corpus.documents) == 11
    assert len(corpus.chunks) == 194
    assert all(document.filename.endswith(".pdf") for document in corpus.documents)
    assert all(
        chunk.source_filename.endswith(".pdf") and chunk.synthetic
        for chunk in corpus.chunks
    )
    assert not any(
        chunk.source_filename == EVALUATION_PATH.name for chunk in corpus.chunks
    )
    assert len(dataset.cases) == 20

    with pytest.raises(InvalidPdfError):
        parse_pdf(EVALUATION_PATH, document_id="evaluation-data")
    with pytest.raises(TypeError, match="DocumentPage"):
        chunk_pages([dataset], max_words=300, overlap_words=50)  # type: ignore[list-item]

    embeddings = RecordingEmbeddings()
    index = RecordingIndex()
    summary = SemanticRetrievalService(embeddings, index).index_corpus(corpus)

    assert summary.chunk_count == 194
    assert embeddings.inputs == [tuple(chunk.text for chunk in corpus.chunks)]
    assert len(index.records) == 194
    assert all(
        record.metadata["source_filename"].endswith(".pdf")
        for record in index.records
    )
    assert all(
        record.metadata["source_filename"] != EVALUATION_PATH.name
        for record in index.records
    )
    assert not isinstance(dataset, DocumentPage)
