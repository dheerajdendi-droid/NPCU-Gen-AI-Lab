"""Application service for retrieval, grounding validation, and citation rendering."""

from collections.abc import Sequence

from cu_intelligence.domain import RetrievalResult
from cu_intelligence.generation.config import GenerationConfig
from cu_intelligence.generation.contracts import EvidenceRetriever, GenerationProvider
from cu_intelligence.generation.errors import (
    GroundingValidationError,
    InvalidQuestionError,
    UnknownCitationChunkError,
)
from cu_intelligence.generation.models import (
    AnswerStatus,
    CitationRecord,
    GenerationDraft,
    GroundedAnswer,
    GroundedStatement,
    ProviderUsage,
)

NO_EVIDENCE_EXPLANATION = "The supplied policy evidence is insufficient to answer this question."


class GroundedAnswerService:
    """Coordinate the single Gate 4 document-grounded question-answer path."""

    def __init__(
        self,
        retriever: EvidenceRetriever,
        generation_provider: GenerationProvider,
        *,
        config: GenerationConfig | None = None,
    ) -> None:
        self._retriever = retriever
        self._generation_provider = generation_provider
        self._config = config or GenerationConfig()

    def answer(
        self,
        question: str,
        *,
        include_superseded: bool = False,
    ) -> GroundedAnswer:
        """Return a fully validated answer or explicit insufficient-evidence result."""

        normalized_question = _validate_question(question)
        evidence = self._retriever.retrieve(
            normalized_question,
            top_k=self._config.top_k,
            include_superseded=include_superseded,
        )
        if not evidence:
            return _insufficient_answer(
                normalized_question,
                explanation=NO_EVIDENCE_EXPLANATION,
                usage=None,
            )

        draft = self._generation_provider.generate(normalized_question, evidence)
        return _ground_draft(normalized_question, evidence, draft)


def _validate_question(question: str) -> str:
    if not isinstance(question, str) or not question.strip():
        raise InvalidQuestionError("question must be a nonblank string")
    return question.strip()


def _ground_draft(
    question: str,
    evidence: Sequence[RetrievalResult],
    draft: GenerationDraft,
) -> GroundedAnswer:
    if draft.status is AnswerStatus.INSUFFICIENT_EVIDENCE:
        if draft.statements or any(
            statement.cited_chunk_ids for statement in draft.statements
        ):
            raise GroundingValidationError(
                "insufficient-evidence output cannot contain answer statements or citations"
            )
        explanation = draft.insufficient_evidence_explanation
        if explanation is None or not explanation.strip():
            raise GroundingValidationError(
                "insufficient-evidence output requires a nonblank explanation"
            )
        return _insufficient_answer(
            question,
            explanation=explanation.strip(),
            usage=draft.usage,
        )

    if draft.insufficient_evidence_explanation is not None:
        raise GroundingValidationError(
            "answered output cannot contain an insufficient-evidence explanation"
        )
    if not draft.statements:
        raise GroundingValidationError("answered output requires at least one statement")

    evidence_by_id: dict[str, RetrievalResult] = {}
    for item in evidence:
        if item.chunk_id in evidence_by_id:
            raise GroundingValidationError("retrieved evidence contains a duplicate chunk ID")
        evidence_by_id[item.chunk_id] = item

    citation_number_by_id: dict[str, int] = {}
    citations: list[CitationRecord] = []
    statements: list[GroundedStatement] = []
    for draft_statement in draft.statements:
        cited_ids = tuple(dict.fromkeys(draft_statement.cited_chunk_ids))
        if not cited_ids:
            raise GroundingValidationError(
                "every answered statement must cite at least one evidence chunk"
            )
        unknown = [chunk_id for chunk_id in cited_ids if chunk_id not in evidence_by_id]
        if unknown:
            raise UnknownCitationChunkError(
                "generation cited a chunk outside the supplied evidence set"
            )

        statement_numbers: list[int] = []
        for chunk_id in cited_ids:
            number = citation_number_by_id.get(chunk_id)
            if number is None:
                number = len(citations) + 1
                citation_number_by_id[chunk_id] = number
                citations.append(_citation_from_evidence(number, evidence_by_id[chunk_id]))
            statement_numbers.append(number)
        statements.append(
            GroundedStatement(
                text=draft_statement.text,
                citation_numbers=tuple(statement_numbers),
            )
        )

    rendered = render_grounded_answer(statements, citations)
    return GroundedAnswer(
        status=AnswerStatus.ANSWERED,
        question=question,
        statements=tuple(statements),
        citations=tuple(citations),
        insufficient_evidence_explanation=None,
        rendered_answer=rendered,
        usage=draft.usage,
    )


def _citation_from_evidence(number: int, evidence: RetrievalResult) -> CitationRecord:
    return CitationRecord(
        citation_number=number,
        document_id=evidence.document_id,
        title=evidence.title,
        version=evidence.version,
        document_status=evidence.document_status,
        page_number=evidence.page_number,
        source_filename=evidence.source_filename,
        chunk_id=evidence.chunk_id,
    )


def _insufficient_answer(
    question: str,
    *,
    explanation: str,
    usage: ProviderUsage | None,
) -> GroundedAnswer:
    rendered = f"Insufficient evidence: {explanation}"
    return GroundedAnswer(
        status=AnswerStatus.INSUFFICIENT_EVIDENCE,
        question=question,
        statements=(),
        citations=(),
        insufficient_evidence_explanation=explanation,
        rendered_answer=rendered,
        usage=usage,
    )


def render_grounded_answer(
    statements: Sequence[GroundedStatement],
    citations: Sequence[CitationRecord],
) -> str:
    """Render statements and stable source labels without provider formatting."""

    answer_lines = [
        f"{statement.text} "
        + " ".join(f"[{number}]" for number in statement.citation_numbers)
        for statement in statements
    ]
    citation_lines = [
        f"[{citation.citation_number}] {_citation_label(citation)}"
        for citation in citations
    ]
    return "\n".join([*answer_lines, "", "Sources:", *citation_lines])


def _citation_label(citation: CitationRecord) -> str:
    status = (
        ", SUPERSEDED"
        if citation.document_status.value == "SUPERSEDED"
        else ""
    )
    return (
        f"[{citation.title}, version {citation.version}, "
        f"page {citation.page_number}{status}]"
    )
