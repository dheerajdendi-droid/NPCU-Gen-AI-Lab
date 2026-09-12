"""Authorization-gated Gate 5 baseline over the existing read-only provider state."""

from pathlib import Path
from typing import Any

import pytest
from pinecone import Pinecone

from cu_intelligence.evaluation import (
    EvaluationRunner,
    load_evaluation_dataset,
    render_markdown_report,
)
from cu_intelligence.generation import (
    GenerationConfigurationError,
    OpenAIGenerationProvider,
    load_live_generation_config,
)
from cu_intelligence.ingestion import build_corpus
from cu_intelligence.retrieval import (
    OpenAIEmbeddingProvider,
    PineconeVectorIndex,
    RetrievalConfigurationError,
    SemanticRetrievalService,
    load_live_retrieval_config,
)

ROOT = Path(__file__).parents[2]


class ReadOnlyDataIndex:
    """Expose only the Pinecone operations permitted by Gate 5."""

    def __init__(self, delegate: Any) -> None:
        self._delegate = delegate

    def query(self, **arguments: Any) -> Any:
        return self._delegate.query(**arguments)

    def describe_index_stats(self) -> Any:
        return self._delegate.describe_index_stats()


class ExistingReadOnlyIndexControl:
    """Validate an existing index without exposing create or mutation methods."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def has_index(self, name: str) -> bool:
        return self._client.has_index(name)

    def describe_index(self, name: str) -> Any:
        return self._client.describe_index(name)

    def Index(self, **arguments: Any) -> ReadOnlyDataIndex:  # noqa: N802
        return ReadOnlyDataIndex(self._client.Index(**arguments))


@pytest.mark.live
def test_read_only_live_gate5_baseline() -> None:
    """Evaluate twenty cases only after both CLI and owner authorization."""

    try:
        retrieval_config = load_live_retrieval_config()
        generation_config = load_live_generation_config()
    except (RetrievalConfigurationError, GenerationConfigurationError) as error:
        pytest.skip(str(error))

    corpus = build_corpus(
        ROOT / "data" / "corpus_manifest.csv",
        pdf_directory=ROOT / "data" / "raw" / "policies",
    )
    dataset = load_evaluation_dataset(
        ROOT / "data" / "_evaluation_do_not_index" / "gate5_cases.json",
        corpus=corpus,
    )

    control_client = Pinecone(
        api_key=retrieval_config.vector_index.api_key.get_secret_value()
    )
    index_name = retrieval_config.vector_index.index_name
    if not control_client.has_index(index_name):
        pytest.fail("The accepted Gate 3 Pinecone index is missing; rebuilding is forbidden")
    description = control_client.describe_index(index_name)
    data_index = ReadOnlyDataIndex(control_client.Index(host=description.host))
    namespace = retrieval_config.vector_index.namespace
    namespace_stats = data_index.describe_index_stats().namespaces.get(namespace)
    assert namespace_stats is not None
    assert namespace_stats.vector_count == 194

    retriever = SemanticRetrievalService(
        OpenAIEmbeddingProvider.from_config(retrieval_config.embeddings),
        PineconeVectorIndex.from_config(
            retrieval_config.vector_index,
            control_client=ExistingReadOnlyIndexControl(control_client),
        ),
    )
    runner = EvaluationRunner(
        retriever,
        OpenAIGenerationProvider.from_config(generation_config),
        corpus=corpus,
    )

    report = runner.run(dataset)

    assert len(report.cases) == 20
    assert all(result.failure is None for result in report.cases)
    assert all(
        evidence.page_number >= 1
        for result in report.cases
        for evidence in result.evidence
    )
    assert all(
        result.answer is None
        or all(
            citation.chunk_id in {item.chunk_id for item in result.evidence}
            for citation in result.answer.citations
        )
        for result in report.cases
    )
    print("\nLIVE GATE 5 BASELINE\n" + render_markdown_report(report))
