"""Tests for environment-driven application settings."""

import pytest
from pydantic import ValidationError

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
