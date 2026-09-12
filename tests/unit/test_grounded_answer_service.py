"""Tests for retrieval coordination, grounding validation, and rendering."""

from collections.abc import Sequence
from datetime import date

import pytest

from cu_intelligence.domain import DocumentStatus, RetrievalResult
from cu_intelligence.generation import (
    AnswerStatus,
    DraftStatement,
    GenerationDraft,
    GroundedAnswerService,
    GroundingValidationError,
    InvalidQuestionError,
    ProviderUsage,
    UnknownCitationChunkError,
)
from cu_intelligence.retrieval import VectorIndexError


def evidence(
    chunk_id: str,
    *,
    rank: int = 1,
    version: str = "4.0",
    status: DocumentStatus = DocumentStatus.CURRENT,
    page_number: int = 2,
) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        document_id=f"lending-{version}",
        chunk_text="Synthetic policy evidence.",
        page_number=page_number,
        title="Lending and Affordability Policy",
        version=version,
        document_status=status,
        effective_date=date(2026, 1, 1),
        owner="Head of Lending",
        source_filename=f"lending-v{version}.pdf",
        synthetic=True,
        rank=rank,
        similarity_score=0.8,
    )


class FakeRetriever:
    def __init__(
        self,
        results: Sequence[RetrievalResult],
        *,
        error: Exception | None = None,
    ) -> None:
        self.results = list(results)
        self.error = error
        self.calls: list[dict[str, object]] = []

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        include_superseded: bool = False,
    ) -> list[RetrievalResult]:
        self.calls.append(
            {
                "query": query,
                "top_k": top_k,
                "include_superseded": include_superseded,
            }
        )
        if self.error is not None:
            raise self.error
        return self.results


class FakeGenerationProvider:
    def __init__(self, draft: GenerationDraft) -> None:
        self.draft = draft
        self.calls: list[tuple[str, tuple[RetrievalResult, ...]]] = []

    def generate(
        self,
        question: str,
        evidence: Sequence[RetrievalResult],
    ) -> GenerationDraft:
        self.calls.append((question, tuple(evidence)))
        return self.draft


def answered(*statements: DraftStatement) -> GenerationDraft:
    return GenerationDraft(
        status=AnswerStatus.ANSWERED,
        statements=statements,
        insufficient_evidence_explanation=None,
        usage=ProviderUsage(input_tokens=100, output_tokens=20, total_tokens=120),
    )


def insufficient(
    explanation: str = "The evidence does not address that subject.",
) -> GenerationDraft:
    return GenerationDraft(
        status=AnswerStatus.INSUFFICIENT_EVIDENCE,
        statements=(),
        insufficient_evidence_explanation=explanation,
    )


@pytest.mark.parametrize("question", ["", " ", "\r\n", 123])
def test_question_must_be_a_nonblank_string(question: object) -> None:
    retriever = FakeRetriever([])
    provider = FakeGenerationProvider(insufficient())

    with pytest.raises(InvalidQuestionError, match="nonblank"):
        GroundedAnswerService(retriever, provider).answer(question)  # type: ignore[arg-type]

    assert retriever.calls == []
    assert provider.calls == []


def test_default_path_retrieves_top_ten_current_evidence() -> None:
    item = evidence("current-chunk")
    retriever = FakeRetriever([item])
    provider = FakeGenerationProvider(
        answered(DraftStatement(text="Supported statement.", cited_chunk_ids=(item.chunk_id,)))
    )

    answer = GroundedAnswerService(retriever, provider).answer("  What is the rule?  ")

    assert retriever.calls == [
        {
            "query": "What is the rule?",
            "top_k": 10,
            "include_superseded": False,
        }
    ]
    assert provider.calls[0][0] == "What is the rule?"
    assert answer.status is AnswerStatus.ANSWERED


def test_historical_option_is_passed_explicitly() -> None:
    old = evidence(
        "old-chunk",
        version="3.1",
        status=DocumentStatus.SUPERSEDED,
    )
    retriever = FakeRetriever([old])
    provider = FakeGenerationProvider(
        answered(
            DraftStatement(
                text="The old version stated this.",
                cited_chunk_ids=(old.chunk_id,),
            )
        )
    )

    answer = GroundedAnswerService(retriever, provider).answer(
        "What did the old version say?",
        include_superseded=True,
    )

    assert retriever.calls[0]["include_superseded"] is True
    assert answer.citations[0].document_status is DocumentStatus.SUPERSEDED
    assert "SUPERSEDED" in answer.rendered_answer


def test_citations_use_evidence_metadata_and_normalize_duplicates() -> None:
    first = evidence("chunk-a", rank=1, page_number=2)
    second = evidence("chunk-b", rank=2, page_number=4)
    provider = FakeGenerationProvider(
        answered(
            DraftStatement(
                text="First supported statement.",
                cited_chunk_ids=("chunk-b", "chunk-b", "chunk-a"),
            ),
            DraftStatement(
                text="Second supported statement.",
                cited_chunk_ids=("chunk-a", "chunk-b"),
            ),
        )
    )

    answer = GroundedAnswerService(FakeRetriever([first, second]), provider).answer(
        "What is supported?"
    )

    assert [item.chunk_id for item in answer.citations] == ["chunk-b", "chunk-a"]
    assert [item.citation_number for item in answer.citations] == [1, 2]
    assert answer.statements[0].citation_numbers == (1, 2)
    assert answer.statements[1].citation_numbers == (2, 1)
    assert answer.citations[0].title == second.title
    assert answer.citations[0].source_filename == second.source_filename
    assert answer.usage is not None and answer.usage.total_tokens == 120
    assert answer.rendered_answer == (
        "First supported statement. [1] [2]\n"
        "Second supported statement. [2] [1]\n\n"
        "Sources:\n"
        "[1] [Lending and Affordability Policy, version 4.0, page 4]\n"
        "[2] [Lending and Affordability Policy, version 4.0, page 2]"
    )


def test_distinct_chunks_on_one_page_remain_distinct_citations() -> None:
    first = evidence("chunk-a", page_number=2)
    second = evidence("chunk-b", rank=2, page_number=2)
    provider = FakeGenerationProvider(
        answered(
            DraftStatement(
                text="Supported by two chunks.",
                cited_chunk_ids=("chunk-a", "chunk-b"),
            )
        )
    )

    answer = GroundedAnswerService(FakeRetriever([first, second]), provider).answer("Question?")

    assert len(answer.citations) == 2
    assert {citation.page_number for citation in answer.citations} == {2}


def test_unknown_or_invented_citation_rejects_the_whole_draft() -> None:
    provider = FakeGenerationProvider(
        answered(DraftStatement(text="Unsupported.", cited_chunk_ids=("invented-chunk",)))
    )

    with pytest.raises(UnknownCitationChunkError, match="outside"):
        GroundedAnswerService(FakeRetriever([evidence("known-chunk")]), provider).answer(
            "Question?"
        )


def test_answered_statement_without_citation_is_rejected() -> None:
    provider = FakeGenerationProvider(
        answered(DraftStatement(text="Unsupported.", cited_chunk_ids=()))
    )

    with pytest.raises(GroundingValidationError, match="at least one"):
        GroundedAnswerService(FakeRetriever([evidence("known-chunk")]), provider).answer(
            "Question?"
        )


def test_answered_result_without_statements_is_rejected() -> None:
    with pytest.raises(GroundingValidationError, match="at least one"):
        GroundedAnswerService(
            FakeRetriever([evidence("known")]),
            FakeGenerationProvider(answered()),
        ).answer("Question?")


def test_empty_retrieval_bypasses_generation_and_abstains() -> None:
    provider = FakeGenerationProvider(insufficient())

    answer = GroundedAnswerService(FakeRetriever([]), provider).answer("Unsupported question?")

    assert answer.status is AnswerStatus.INSUFFICIENT_EVIDENCE
    assert answer.statements == ()
    assert answer.citations == ()
    assert "supplied policy evidence is insufficient" in answer.rendered_answer
    assert provider.calls == []


def test_provider_insufficient_evidence_result_has_no_fabricated_answer() -> None:
    answer = GroundedAnswerService(
        FakeRetriever([evidence("unrelated")]),
        FakeGenerationProvider(insufficient()),
    ).answer("Unsupported question?")

    assert answer.status is AnswerStatus.INSUFFICIENT_EVIDENCE
    assert answer.statements == ()
    assert answer.citations == ()


def test_invalid_insufficient_evidence_content_is_rejected() -> None:
    invalid = GenerationDraft(
        status=AnswerStatus.INSUFFICIENT_EVIDENCE,
        statements=(DraftStatement(text="Fabricated.", cited_chunk_ids=("known",)),),
        insufficient_evidence_explanation="Not enough.",
    )

    with pytest.raises(GroundingValidationError, match="cannot contain"):
        GroundedAnswerService(
            FakeRetriever([evidence("known")]), FakeGenerationProvider(invalid)
        ).answer("Question?")


def test_conflicting_versions_remain_distinct_and_label_superseded() -> None:
    current = evidence("current", rank=1, version="4.0")
    old = evidence(
        "old",
        rank=2,
        version="3.1",
        status=DocumentStatus.SUPERSEDED,
    )
    provider = FakeGenerationProvider(
        answered(
            DraftStatement(
                text="The versions differ on the described process.",
                cited_chunk_ids=("current", "old"),
            )
        )
    )

    answer = GroundedAnswerService(FakeRetriever([current, old]), provider).answer(
        "Compare the versions.", include_superseded=True
    )

    assert [citation.version for citation in answer.citations] == ["4.0", "3.1"]
    assert "version 3.1, page 2, SUPERSEDED" in answer.rendered_answer


def test_retrieval_failure_propagates_unchanged() -> None:
    error = VectorIndexError("synthetic retrieval failure")
    service = GroundedAnswerService(
        FakeRetriever([], error=error),
        FakeGenerationProvider(insufficient()),
    )

    with pytest.raises(VectorIndexError, match="synthetic retrieval failure") as captured:
        service.answer("Question?")

    assert captured.value is error
