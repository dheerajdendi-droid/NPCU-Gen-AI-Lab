"""Offline end-to-end evaluation over all twenty protected cases."""

from collections.abc import Sequence
from itertools import count
from pathlib import Path

from cu_intelligence.domain import RetrievalResult
from cu_intelligence.evaluation import (
    EvaluationRunner,
    load_evaluation_dataset,
    render_json_report,
    render_markdown_report,
)
from cu_intelligence.generation import (
    AnswerStatus,
    DraftStatement,
    GenerationDraft,
    ProviderUsage,
)
from cu_intelligence.ingestion import build_corpus

ROOT = Path(__file__).parents[2]


class DeterministicRetriever:
    def __init__(self, results_by_question: dict[str, list[RetrievalResult]]) -> None:
        self._results_by_question = results_by_question
        self.calls: list[tuple[str, int, bool]] = []

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        include_superseded: bool = False,
    ) -> list[RetrievalResult]:
        self.calls.append((query, top_k, include_superseded))
        return self._results_by_question[query][:top_k]


class DeterministicGenerator:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[str, ...]]] = []

    def generate(
        self,
        question: str,
        evidence: Sequence[RetrievalResult],
    ) -> GenerationDraft:
        chunk_ids = tuple(item.chunk_id for item in evidence)
        self.calls.append((question, chunk_ids))
        return GenerationDraft(
            status=AnswerStatus.ANSWERED,
            statements=(
                DraftStatement(
                    text="The deterministic answer is supported by every required document.",
                    cited_chunk_ids=chunk_ids,
                ),
            ),
            insufficient_evidence_explanation=None,
            usage=ProviderUsage(input_tokens=10, output_tokens=5, total_tokens=15),
        )


def test_all_cases_run_once_and_render_stably_offline() -> None:
    corpus = build_corpus(
        ROOT / "data" / "corpus_manifest.csv",
        pdf_directory=ROOT / "data" / "raw" / "policies",
    )
    dataset = load_evaluation_dataset(
        ROOT / "data" / "_evaluation_do_not_index" / "gate5_cases.json",
        corpus=corpus,
    )
    chunks_by_document_and_page = {
        (chunk.document_id, chunk.page_number): chunk for chunk in corpus.chunks
    }
    results_by_question: dict[str, list[RetrievalResult]] = {}
    for case in dataset.cases:
        selected = []
        for document_id in case.required_citation_document_ids:
            preferred_pages = case.expected_evidence_pages.get(document_id, ())
            page = preferred_pages[0]
            chunk = chunks_by_document_and_page[(document_id, page)]
            selected.append(
                RetrievalResult(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    chunk_text=chunk.text,
                    page_number=chunk.page_number,
                    title=chunk.title,
                    version=chunk.version,
                    document_status=chunk.document_status,
                    effective_date=chunk.effective_date,
                    owner=chunk.owner,
                    source_filename=chunk.source_filename,
                    synthetic=True,
                    rank=len(selected) + 1,
                    similarity_score=round(0.99 - len(selected) / 100, 4),
                )
            )
        results_by_question[case.question] = selected

    retriever = DeterministicRetriever(results_by_question)
    generator = DeterministicGenerator()
    ticks = count()
    runner = EvaluationRunner(
        retriever,
        generator,
        corpus=corpus,
        clock=lambda: next(ticks) / 1000,
    )

    report = runner.run(dataset)

    assert len(report.cases) == 20
    assert len(retriever.calls) == 20
    assert all(top_k == 10 for _, top_k, _ in retriever.calls)
    assert len(generator.calls) == 17
    assert report.answers.expected_status_accuracy.value == 1
    assert report.retrieval.document_hit_at_10.value == 1
    assert report.retrieval.multi_document_recall.value == 1
    assert report.answers.citation_document_recall.value == 1
    assert report.answers.failed_case_count == 0
    assert all(len(value) == 64 for value in (
        report.dataset_fingerprint,
        report.corpus_fingerprint,
        report.configuration_fingerprint,
    ))
    assert render_json_report(report) == render_json_report(report)
    markdown = render_markdown_report(report)
    assert markdown == render_markdown_report(report)
    assert "Human review:" in markdown
    assert "_pending (0/1/2)_" in markdown
    assert "Document Hit@10" in markdown
