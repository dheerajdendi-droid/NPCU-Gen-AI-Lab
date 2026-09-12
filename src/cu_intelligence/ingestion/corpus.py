"""Build enriched, page-aware chunks from the canonical PDF corpus."""

from pathlib import Path

from cu_intelligence.domain import CorpusBuild, CorpusChunk
from cu_intelligence.ingestion.chunking import chunk_pages
from cu_intelligence.ingestion.manifest import load_corpus_manifest
from cu_intelligence.ingestion.pdf import parse_pdf


def build_corpus(
    manifest_path: str | Path,
    *,
    pdf_directory: str | Path,
    max_words: int = 300,
    overlap_words: int = 50,
) -> CorpusBuild:
    """Parse and chunk every manifest PDF, enriching chunks with manifest metadata."""

    pdf_dir = Path(pdf_directory)
    documents = load_corpus_manifest(manifest_path, pdf_directory=pdf_dir)
    enriched_chunks: list[CorpusChunk] = []

    for document in documents:
        pages = parse_pdf(pdf_dir / document.filename, document_id=document.document_id)
        chunks = chunk_pages(
            pages,
            max_words=max_words,
            overlap_words=overlap_words,
        )
        enriched_chunks.extend(
            CorpusChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                text=chunk.text,
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                title=document.title,
                version=document.version,
                document_status=document.status,
                effective_date=document.effective_date,
                owner=document.owner,
                source_filename=document.filename,
                synthetic=document.synthetic,
            )
            for chunk in chunks
        )

    return CorpusBuild(documents=tuple(documents), chunks=tuple(enriched_chunks))
