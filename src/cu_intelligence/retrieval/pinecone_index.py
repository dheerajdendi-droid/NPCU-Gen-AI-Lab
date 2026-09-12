"""Pinecone adapter kept behind the application vector-index boundary."""

from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Any

from pinecone import Pinecone, ServerlessSpec

from cu_intelligence.domain import DocumentStatus, VectorMatch, VectorRecord
from cu_intelligence.retrieval.config import (
    PINECONE_CLOUD,
    PINECONE_REGION,
    SIMILARITY_METRIC,
    VECTOR_DIMENSIONS,
    VECTOR_TYPE,
    PineconeIndexConfig,
)
from cu_intelligence.retrieval.errors import (
    DimensionMismatchError,
    RetrievalConfigurationError,
    VectorIndexError,
)


class PineconeVectorIndex:
    """Map application vector records and matches to the Pinecone SDK."""

    dimensions = VECTOR_DIMENSIONS

    def __init__(self, index: Any, *, namespace: str) -> None:
        if not isinstance(namespace, str) or not namespace.strip():
            raise RetrievalConfigurationError("PINECONE_NAMESPACE must be configured")
        self._index = index
        self._namespace = namespace.strip()

    @classmethod
    def from_config(
        cls,
        config: PineconeIndexConfig,
        *,
        control_client: Any | None = None,
        serverless_spec_factory: Any = ServerlessSpec,
    ) -> "PineconeVectorIndex":
        """Create or validate the one approved index, then target it by host."""

        client = control_client or Pinecone(
            api_key=config.api_key.get_secret_value()
        )
        index_name = config.index_name
        try:
            if not client.has_index(index_name):
                client.create_index(
                    name=index_name,
                    vector_type=VECTOR_TYPE,
                    dimension=VECTOR_DIMENSIONS,
                    metric=SIMILARITY_METRIC,
                    spec=serverless_spec_factory(
                        cloud=PINECONE_CLOUD,
                        region=PINECONE_REGION,
                    ),
                    deletion_protection="disabled",
                    timeout=120,
                )

            description = client.describe_index(index_name)
            _validate_index_description(description)
            host = _read(description, "host")
            if not isinstance(host, str) or not host:
                raise VectorIndexError("Pinecone index description did not contain a host")
            index = client.Index(host=host)
        except (DimensionMismatchError, RetrievalConfigurationError, VectorIndexError):
            raise
        except Exception as error:
            raise VectorIndexError("Pinecone index setup failed") from error

        return cls(index, namespace=config.namespace)

    def upsert(self, records: Sequence[VectorRecord]) -> int:
        """Upsert records by stable ID in the configured namespace."""

        vectors: list[dict[str, Any]] = []
        for record in records:
            if len(record.values) != self.dimensions:
                raise DimensionMismatchError(
                    f"Pinecone records must contain {self.dimensions} values"
                )
            if not all(isfinite(component) for component in record.values):
                raise VectorIndexError("Pinecone record vector contains a non-finite value")
            vectors.append(
                {
                    "id": record.record_id,
                    "values": list(record.values),
                    "metadata": dict(record.metadata),
                }
            )
        if not vectors:
            return 0

        try:
            response = self._index.upsert(
                vectors=vectors,
                namespace=self._namespace,
            )
            upserted_count = _read(response, "upserted_count")
            if not isinstance(upserted_count, int):
                raise VectorIndexError("Pinecone upsert response did not contain a count")
            return upserted_count
        except VectorIndexError:
            raise
        except Exception as error:
            raise VectorIndexError("Pinecone upsert failed") from error

    def query(
        self,
        vector: Sequence[float],
        *,
        top_k: int,
        status_filter: DocumentStatus | None,
    ) -> list[VectorMatch]:
        """Query one namespace and map Pinecone matches to application values."""

        values = tuple(float(component) for component in vector)
        if len(values) != self.dimensions:
            raise DimensionMismatchError(
                f"Pinecone query vector must contain {self.dimensions} values"
            )
        if not all(isfinite(component) for component in values):
            raise VectorIndexError("Pinecone query vector contains a non-finite value")
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0:
            raise ValueError("top_k must be a positive integer")

        query_arguments: dict[str, Any] = {
            "vector": list(values),
            "top_k": top_k,
            "namespace": self._namespace,
            "include_metadata": True,
            "include_values": False,
        }
        if status_filter is not None:
            query_arguments["filter"] = {
                "status": {"$eq": status_filter.value}
            }

        try:
            response = self._index.query(**query_arguments)
            raw_matches = _read(response, "matches")
            if raw_matches is None:
                raise VectorIndexError("Pinecone query response did not contain matches")
            return [
                VectorMatch(
                    record_id=_read(match, "id"),
                    score=_read(match, "score"),
                    metadata=dict(_read(match, "metadata") or {}),
                )
                for match in raw_matches
            ]
        except (DimensionMismatchError, VectorIndexError):
            raise
        except Exception as error:
            raise VectorIndexError("Pinecone query failed") from error


def _validate_index_description(description: Any) -> None:
    dimension = _read(description, "dimension")
    if dimension != VECTOR_DIMENSIONS:
        raise DimensionMismatchError(
            f"Pinecone index must have {VECTOR_DIMENSIONS} dimensions; found {dimension!r}"
        )

    expected = {
        "vector type": (VECTOR_TYPE, _read(description, "vector_type")),
        "metric": (SIMILARITY_METRIC, _read(description, "metric")),
        "cloud": (
            PINECONE_CLOUD,
            _read_path(description, "spec", "serverless", "cloud"),
        ),
        "region": (
            PINECONE_REGION,
            _read_path(description, "spec", "serverless", "region"),
        ),
    }
    mismatches = [
        f"{label}={actual!r}"
        for label, (required, actual) in expected.items()
        if actual != required
    ]
    if mismatches:
        raise RetrievalConfigurationError(
            "Pinecone index configuration is incompatible: " + ", ".join(mismatches)
        )

    ready = _read_path(description, "status", "ready")
    if ready is not True:
        raise VectorIndexError("Pinecone index is not ready")


def _read(value: Any, key: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(key)
    return getattr(value, key, None)


def _read_path(value: Any, *keys: str) -> Any:
    current = value
    for key in keys:
        current = _read(current, key)
        if current is None:
            return None
    return current
