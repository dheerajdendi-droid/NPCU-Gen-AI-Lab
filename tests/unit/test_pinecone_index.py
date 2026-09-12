"""Tests for Pinecone configuration and mapping without provider calls."""

from typing import Any

import pytest
from pydantic import SecretStr

from cu_intelligence.domain import DocumentStatus, VectorRecord
from cu_intelligence.retrieval import (
    VECTOR_DIMENSIONS,
    DimensionMismatchError,
    PineconeIndexConfig,
    PineconeVectorIndex,
    RetrievalConfigurationError,
    VectorIndexError,
)


def live_config() -> PineconeIndexConfig:
    return PineconeIndexConfig(
        api_key=SecretStr("synthetic-pinecone-key"),
        index_name="npcu-gate-3",
        namespace="synthetic-corpus",
    )


def valid_description(**overrides: Any) -> dict[str, Any]:
    description: dict[str, Any] = {
        "name": "npcu-gate-3",
        "vector_type": "dense",
        "dimension": VECTOR_DIMENSIONS,
        "metric": "cosine",
        "host": "synthetic-host.example",
        "status": {"ready": True},
        "spec": {"serverless": {"cloud": "aws", "region": "us-east-1"}},
    }
    description.update(overrides)
    return description


class FakeDataIndex:
    def __init__(self) -> None:
        self.upsert_calls: list[dict[str, Any]] = []
        self.query_calls: list[dict[str, Any]] = []
        self.matches: list[dict[str, Any]] = []

    def upsert(self, **arguments: Any) -> dict[str, int]:
        self.upsert_calls.append(arguments)
        return {"upserted_count": len(arguments["vectors"])}

    def query(self, **arguments: Any) -> dict[str, Any]:
        self.query_calls.append(arguments)
        return {"matches": self.matches}


class FakeControlClient:
    def __init__(
        self,
        *,
        exists: bool,
        description: dict[str, Any] | None = None,
    ) -> None:
        self.exists = exists
        self.description = description or valid_description()
        self.data_index = FakeDataIndex()
        self.create_calls: list[dict[str, Any]] = []
        self.index_calls: list[dict[str, Any]] = []

    def has_index(self, name: str) -> bool:
        assert name == "npcu-gate-3"
        return self.exists

    def create_index(self, **arguments: Any) -> None:
        self.create_calls.append(arguments)

    def describe_index(self, name: str) -> dict[str, Any]:
        assert name == "npcu-gate-3"
        return self.description

    def Index(self, **arguments: Any) -> FakeDataIndex:  # noqa: N802
        self.index_calls.append(arguments)
        return self.data_index


def test_missing_index_is_created_with_exact_approved_configuration() -> None:
    control = FakeControlClient(exists=False)

    index = PineconeVectorIndex.from_config(
        live_config(),
        control_client=control,
        serverless_spec_factory=lambda **values: values,
    )

    assert index.dimensions == 1536
    assert control.create_calls == [
        {
            "name": "npcu-gate-3",
            "vector_type": "dense",
            "dimension": 1536,
            "metric": "cosine",
            "spec": {"cloud": "aws", "region": "us-east-1"},
            "deletion_protection": "disabled",
            "timeout": 120,
        }
    ]
    assert control.index_calls == [{"host": "synthetic-host.example"}]


def test_compatible_existing_index_is_not_created_again() -> None:
    control = FakeControlClient(exists=True)

    PineconeVectorIndex.from_config(live_config(), control_client=control)

    assert control.create_calls == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"vector_type": "sparse"},
        {"metric": "dotproduct"},
        {"spec": {"serverless": {"cloud": "gcp", "region": "us-east-1"}}},
        {"spec": {"serverless": {"cloud": "aws", "region": "eu-west-1"}}},
    ],
)
def test_incompatible_existing_index_is_rejected(overrides: dict[str, Any]) -> None:
    control = FakeControlClient(exists=True, description=valid_description(**overrides))

    with pytest.raises(RetrievalConfigurationError, match="incompatible"):
        PineconeVectorIndex.from_config(live_config(), control_client=control)


def test_existing_index_dimension_mismatch_is_rejected() -> None:
    control = FakeControlClient(
        exists=True,
        description=valid_description(dimension=512),
    )

    with pytest.raises(DimensionMismatchError, match="1536"):
        PineconeVectorIndex.from_config(live_config(), control_client=control)


def test_not_ready_index_is_rejected() -> None:
    control = FakeControlClient(
        exists=True,
        description=valid_description(status={"ready": False}),
    )

    with pytest.raises(VectorIndexError, match="not ready"):
        PineconeVectorIndex.from_config(live_config(), control_client=control)


def test_upsert_maps_record_id_vector_metadata_and_namespace() -> None:
    data_index = FakeDataIndex()
    index = PineconeVectorIndex(data_index, namespace="synthetic-corpus")
    record = VectorRecord(
        record_id="document:p0001:c000000",
        values=tuple([0.1] * VECTOR_DIMENSIONS),
        metadata={"document_id": "document", "status": "CURRENT"},
    )

    assert index.upsert([record]) == 1
    assert data_index.upsert_calls == [
        {
            "vectors": [
                {
                    "id": "document:p0001:c000000",
                    "values": [0.1] * VECTOR_DIMENSIONS,
                    "metadata": {"document_id": "document", "status": "CURRENT"},
                }
            ],
            "namespace": "synthetic-corpus",
        }
    ]


def test_query_applies_current_filter_and_maps_matches() -> None:
    data_index = FakeDataIndex()
    data_index.matches = [
        {
            "id": "document:p0001:c000000",
            "score": 0.75,
            "metadata": {"document_id": "document", "status": "CURRENT"},
        }
    ]
    index = PineconeVectorIndex(data_index, namespace="synthetic-corpus")

    matches = index.query(
        [0.2] * VECTOR_DIMENSIONS,
        top_k=3,
        status_filter=DocumentStatus.CURRENT,
    )

    assert matches[0].record_id == "document:p0001:c000000"
    assert matches[0].score == pytest.approx(0.75)
    assert data_index.query_calls[0]["filter"] == {
        "status": {"$eq": "CURRENT"}
    }
    assert data_index.query_calls[0]["namespace"] == "synthetic-corpus"


def test_query_omits_status_filter_when_superseded_is_included() -> None:
    data_index = FakeDataIndex()
    index = PineconeVectorIndex(data_index, namespace="synthetic-corpus")

    assert (
        index.query(
            [0.2] * VECTOR_DIMENSIONS,
            top_k=3,
            status_filter=None,
        )
        == []
    )
    assert "filter" not in data_index.query_calls[0]


def test_data_operation_failure_is_translated() -> None:
    class BrokenIndex:
        def query(self, **arguments: Any) -> None:
            raise RuntimeError("provider detail")

    index = PineconeVectorIndex(BrokenIndex(), namespace="synthetic-corpus")

    with pytest.raises(VectorIndexError, match="query failed") as captured:
        index.query(
            [0.2] * VECTOR_DIMENSIONS,
            top_k=1,
            status_filter=DocumentStatus.CURRENT,
        )

    assert isinstance(captured.value.__cause__, RuntimeError)
