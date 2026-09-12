"""Offline end-to-end test for grounded generation and citation construction."""

from collections.abc import Sequence
from datetime import date

from cu_intelligence.domain import DocumentStatus, RetrievalResult
from cu_intelligence.generation import (
    AnswerStatus,
    DraftStatement,
    GenerationDraft,
    GroundedAnswerService,
)


class DeterministicEvidenceRetriever:
    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        include_superseded: bool = False,
    ) -> list[RetrievalResult]:
        assert query == "What evidence establishes employer eligibility?"
        assert top_k == 10
        assert include_superseded is False
        return [
            RetrievalResult(
                chunk_id="eligibility:p0003:c000004",
                document_id="eligibility",
                chunk_text=(
                    "Employer eligibility evidence may include a current payroll record, "
                    "employee number, or employer email confirmation."
                ),
                page_number=3,
                title="Member Eligibility and Onboarding Policy",
                version="2.2",
                document_status=DocumentStatus.CURRENT,
                effective_date=date(2026, 1, 1),
                owner="Head of Membership",
                source_filename="eligibility-v2.2.pdf",
                synthetic=True,
                rank=1,
                similarity_score=0.91,
            )
        ]


class DeterministicStructuredGenerator:
    def generate(
        self,
        question: str,
        evidence: Sequence[RetrievalResult],
    ) -> GenerationDraft:
        assert question == "What evidence establishes employer eligibility?"
        assert [item.chunk_id for item in evidence] == ["eligibility:p0003:c000004"]
        return GenerationDraft(
            status=AnswerStatus.ANSWERED,
            statements=(
                DraftStatement(
                    text=(
                        "Employer eligibility may be evidenced by a current payroll record, "
                        "employee number, or employer email confirmation."
                    ),
                    cited_chunk_ids=("eligibility:p0003:c000004",),
                ),
            ),
            insufficient_evidence_explanation=None,
        )


def test_question_to_retrieval_generation_validation_and_rendering() -> None:
    answer = GroundedAnswerService(
        DeterministicEvidenceRetriever(),
        DeterministicStructuredGenerator(),
    ).answer("What evidence establishes employer eligibility?")

    assert answer.status is AnswerStatus.ANSWERED
    assert answer.statements[0].citation_numbers == (1,)
    assert answer.citations[0].chunk_id == "eligibility:p0003:c000004"
    assert answer.citations[0].page_number == 3
    assert answer.rendered_answer.endswith(
        "[1] [Member Eligibility and Onboarding Policy, version 2.2, page 3]"
    )
