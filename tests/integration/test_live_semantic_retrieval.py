"""Explicit real-provider smoke test; never part of deterministic assertions."""

from pathlib import Path

import pytest

from cu_intelligence.domain import DocumentStatus
from cu_intelligence.ingestion import build_corpus
from cu_intelligence.retrieval import (
    RETRIEVAL_SMOKE_QUESTIONS,
    OpenAIEmbeddingProvider,
    PineconeVectorIndex,
    RetrievalConfigurationError,
    SemanticRetrievalService,
    load_live_retrieval_config,
)


@pytest.mark.live
def test_real_openai_and_pinecone_corpus_to_query_smoke() -> None:
    """Exercise the approved live path only when every environment setting exists."""

    try:
        config = load_live_retrieval_config()
    except RetrievalConfigurationError as error:
        pytest.skip(str(error))

    root = Path(__file__).parents[2]
    corpus = build_corpus(
        root / "data" / "corpus_manifest.csv",
        pdf_directory=root / "data" / "raw" / "policies",
    )
    service = SemanticRetrievalService(
        OpenAIEmbeddingProvider.from_config(config.embeddings),
        PineconeVectorIndex.from_config(config.vector_index),
    )

    summary = service.index_corpus(corpus)

    assert summary.document_count == 11
    assert summary.chunk_count == 194
    assert summary.upserted_count == 194

    for question in RETRIEVAL_SMOKE_QUESTIONS:
        results = service.retrieve(question.query, top_k=10)
        assert results
        assert question.expected_document_id in {
            result.document_id for result in results
        }
        assert all(result.document_status is DocumentStatus.CURRENT for result in results)
        assert all(result.page_number >= 1 for result in results)
