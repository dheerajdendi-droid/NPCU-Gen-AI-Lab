"""Stable canonical fingerprints for evaluation inputs."""

import hashlib
import json
from typing import Any

from pydantic import BaseModel

from cu_intelligence.domain import CorpusBuild
from cu_intelligence.evaluation.models import EvaluationConfig, EvaluationDataset


def canonical_json(value: Any) -> str:
    """Serialize application-owned data with stable keys and compact separators."""

    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def fingerprint_value(value: Any) -> str:
    """Return a lowercase SHA-256 fingerprint of canonical JSON."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def fingerprint_dataset(dataset: EvaluationDataset) -> str:
    """Fingerprint validated case content and ordering."""

    return fingerprint_value(dataset)


def fingerprint_corpus(corpus: CorpusBuild) -> str:
    """Fingerprint canonical corpus metadata and deterministic chunk content."""

    documents = sorted(
        (document.model_dump(mode="json") for document in corpus.documents),
        key=lambda item: item["document_id"],
    )
    chunks = sorted(
        (chunk.model_dump(mode="json") for chunk in corpus.chunks),
        key=lambda item: item["chunk_id"],
    )
    return fingerprint_value({"documents": documents, "chunks": chunks})


def fingerprint_configuration(config: EvaluationConfig) -> str:
    """Fingerprint only public evaluation settings, never deployment secrets."""

    return fingerprint_value(config)
