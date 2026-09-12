"""Environment-driven application settings."""

from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, including redacted optional live-provider configuration."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="NPCU_", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    openai_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
    )
    pinecone_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="PINECONE_API_KEY",
    )
    pinecone_index_name: str | None = Field(
        default=None,
        validation_alias="PINECONE_INDEX_NAME",
    )
    pinecone_namespace: str | None = Field(
        default=None,
        validation_alias="PINECONE_NAMESPACE",
    )

    @field_validator("pinecone_index_name", "pinecone_namespace")
    @classmethod
    def validate_optional_nonblank_setting(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("configured names must not be blank")
        return stripped
