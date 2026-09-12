"""Focused real-provider Gate 4 smoke test over the existing Gate 3 index."""

from collections.abc import Sequence
from typing import Any

import pytest
from pinecone import Pinecone

from cu_intelligence.domain import DocumentStatus, RetrievalResult
from cu_intelligence.generation import (
    AnswerStatus,
    GenerationConfigurationError,
    GroundedAnswer,
    GroundedAnswerService,
    OpenAIGenerationProvider,
    load_live_generation_config,
)
from cu_intelligence.retrieval import (
    OpenAIEmbeddingProvider,
    PineconeVectorIndex,
    RetrievalConfigurationError,
    SemanticRetrievalService,
    load_live_retrieval_config,
)

CURRENT_CASES = (
    (
        "member-eligibility",
        "What evidence can establish that a member meets employer eligibility?",
        "01_Member_Eligibility_Onboarding_Policy_v2.2",
    ),
    (
        "lending-affordability",
        "How must net income and essential expenditure be assessed for affordability?",
        "02_Lending_Affordability_Policy_v4.0",
    ),
    (
        "vulnerable-members",
        "What support should be offered to vulnerable members making complaints?",
        "05_Complaints_Vulnerable_Members_Policy_v1.8",
    ),
    (
        "supplier-change",
        "What controls apply when an IT change involves a supplier?",
        "10_IT_Change_Supplier_Management_Procedure_v1.6",
    ),
)

UNSUPPORTED_QUESTION = (
    "What uniform must NPCU employees wear while operating a branch on Mars?"
)
HISTORICAL_QUESTION = (
    "Compare the income and affordability assessment controls in current Lending Policy v4.0 "
    "with superseded Lending Policy v3.1. State which version is current."
)
CURRENT_LENDING_ID = "02_Lending_Affordability_Policy_v4.0"
SUPERSEDED_LENDING_ID = "02A_Lending_Affordability_Policy_v3.1_SUPERSEDED"


class ExistingIndexControl:
    """Prevent the adapter's setup path from creating a missing live index."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def has_index(self, name: str) -> bool:
        return True

    def describe_index(self, name: str) -> Any:
        return self._client.describe_index(name)

    def Index(self, **arguments: Any) -> Any:  # noqa: N802
        return self._client.Index(**arguments)


class RecordingRetriever:
    """Record exact evidence used by each live answer without changing retrieval."""

    def __init__(self, delegate: SemanticRetrievalService) -> None:
        self._delegate = delegate
        self.last_results: tuple[RetrievalResult, ...] = ()

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        include_superseded: bool = False,
    ) -> list[RetrievalResult]:
        results = self._delegate.retrieve(
            query,
            top_k=top_k,
            include_superseded=include_superseded,
        )
        self.last_results = tuple(results)
        return results


def _assert_grounded(answer: GroundedAnswer, evidence: Sequence[RetrievalResult]) -> None:
    evidence_ids = {item.chunk_id for item in evidence}
    assert answer.status is AnswerStatus.ANSWERED
    assert answer.statements
    assert answer.citations
    assert all(citation.chunk_id in evidence_ids for citation in answer.citations)
    assert all(citation.page_number >= 1 for citation in answer.citations)
    assert all(statement.citation_numbers for statement in answer.statements)


@pytest.mark.live
def test_existing_index_to_live_grounded_answers_and_abstention() -> None:
    """Query existing vectors and generate six reviewable grounded outcomes."""

    try:
        retrieval_config = load_live_retrieval_config()
        generation_config = load_live_generation_config()
    except (RetrievalConfigurationError, GenerationConfigurationError) as error:
        pytest.skip(str(error))

    control = Pinecone(api_key=retrieval_config.vector_index.api_key.get_secret_value())
    index_name = retrieval_config.vector_index.index_name
    if not control.has_index(index_name):
        pytest.fail("The accepted Gate 3 Pinecone index is missing; rebuilding was not authorized")

    description = control.describe_index(index_name)
    data_index = control.Index(host=description.host)
    stats = data_index.describe_index_stats()
    namespace = retrieval_config.vector_index.namespace
    namespace_stats = stats.namespaces.get(namespace)
    assert namespace_stats is not None
    assert namespace_stats.vector_count == 194

    retrieval = SemanticRetrievalService(
        OpenAIEmbeddingProvider.from_config(retrieval_config.embeddings),
        PineconeVectorIndex.from_config(
            retrieval_config.vector_index,
            control_client=ExistingIndexControl(control),
        ),
    )
    recording_retriever = RecordingRetriever(retrieval)
    service = GroundedAnswerService(
        recording_retriever,
        OpenAIGenerationProvider.from_config(generation_config),
    )

    for name, question, expected_document_id in CURRENT_CASES:
        answer = service.answer(question)
        evidence = recording_retriever.last_results
        if name == "vulnerable-members" and expected_document_id not in {
            item.document_id for item in evidence
        }:
            pytest.fail(
                "Gate 3 retrieval regression: vulnerable-members document is absent from top ten"
            )
        _assert_grounded(answer, evidence)
        assert expected_document_id in {
            citation.document_id for citation in answer.citations
        }
        assert all(
            citation.document_status is DocumentStatus.CURRENT
            for citation in answer.citations
        )
        print(f"\nLIVE ANSWER [{name}]\n{answer.rendered_answer}")
        if answer.usage is not None:
            print(f"USAGE [{name}] {answer.usage.model_dump()}")

    unsupported = service.answer(UNSUPPORTED_QUESTION)
    assert unsupported.status is AnswerStatus.INSUFFICIENT_EVIDENCE
    assert unsupported.statements == ()
    assert unsupported.citations == ()
    print(f"\nLIVE ANSWER [unsupported]\n{unsupported.rendered_answer}")
    if unsupported.usage is not None:
        print(f"USAGE [unsupported] {unsupported.usage.model_dump()}")

    historical = service.answer(HISTORICAL_QUESTION, include_superseded=True)
    historical_evidence = recording_retriever.last_results
    evidence_documents = {item.document_id for item in historical_evidence}
    assert {CURRENT_LENDING_ID, SUPERSEDED_LENDING_ID} <= evidence_documents
    _assert_grounded(historical, historical_evidence)
    cited_documents = {citation.document_id for citation in historical.citations}
    assert {CURRENT_LENDING_ID, SUPERSEDED_LENDING_ID} <= cited_documents
    assert any(
        citation.document_status is DocumentStatus.SUPERSEDED
        for citation in historical.citations
    )
    assert "SUPERSEDED" in historical.rendered_answer
    print(f"\nLIVE ANSWER [historical-lending]\n{historical.rendered_answer}")
    if historical.usage is not None:
        print(f"USAGE [historical-lending] {historical.usage.model_dump()}")
