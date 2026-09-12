"""Tests for environment-driven application settings."""

import pytest
from pydantic import SecretStr, ValidationError

from cu_intelligence.retrieval import (
    RetrievalConfigurationError,
    load_live_retrieval_config,
)
from cu_intelligence.settings import Settings


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NPCU_ENVIRONMENT", raising=False)
    monkeypatch.delenv("NPCU_LOG_LEVEL", raising=False)

    settings = Settings(_env_file=None)

    assert settings.environment == "development"
    assert settings.log_level == "INFO"


def test_settings_can_be_overridden_by_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NPCU_ENVIRONMENT", "test")
    monkeypatch.setenv("NPCU_LOG_LEVEL", "DEBUG")

    settings = Settings(_env_file=None)

    assert settings.environment == "test"
    assert settings.log_level == "DEBUG"


def test_live_provider_settings_are_read_from_environment_and_redacted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-openai-secret")
    monkeypatch.setenv("PINECONE_API_KEY", "synthetic-pinecone-secret")
    monkeypatch.setenv("PINECONE_INDEX_NAME", "npcu-gate-3")
    monkeypatch.setenv("PINECONE_NAMESPACE", "synthetic-corpus")

    config = load_live_retrieval_config(Settings(_env_file=None))

    assert isinstance(config.embeddings.api_key, SecretStr)
    assert config.vector_index.index_name == "npcu-gate-3"
    assert config.vector_index.namespace == "synthetic-corpus"
    assert "synthetic-openai-secret" not in repr(config)
    assert "synthetic-pinecone-secret" not in repr(config)


def test_missing_live_provider_settings_fail_without_secret_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (
        "OPENAI_API_KEY",
        "PINECONE_API_KEY",
        "PINECONE_INDEX_NAME",
        "PINECONE_NAMESPACE",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RetrievalConfigurationError) as captured:
        load_live_retrieval_config(Settings(_env_file=None))

    assert "OPENAI_API_KEY" in str(captured.value)
    assert "PINECONE_API_KEY" in str(captured.value)


@pytest.mark.parametrize("name", ["PINECONE_INDEX_NAME", "PINECONE_NAMESPACE"])
def test_blank_provider_names_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    monkeypatch.setenv(name, "   ")

    with pytest.raises(ValidationError, match="must not be blank"):
        Settings(_env_file=None)


@pytest.mark.parametrize(
    ("name", "value"),
    [("NPCU_ENVIRONMENT", "staging"), ("NPCU_LOG_LEVEL", "VERBOSE")],
)
def test_settings_reject_invalid_values(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
