import pytest
from pydantic import ValidationError

from app.core.config import Settings

POSTGRES_URL = "postgresql+psycopg://bastion:secret@postgres:5432/bastion"
STRONG_SECRET = "bastion-prod-secret-that-is-long-and-random-2026"


def make_settings(**overrides: object) -> Settings:
    values = {"_env_file": None}
    values.update(overrides)
    return Settings(**values)


def test_clickhouse_defaults_are_safe_and_disabled() -> None:
    settings = make_settings()

    assert settings.storage.clickhouse.enabled is False
    assert settings.storage.clickhouse.profile == "disabled"
    assert settings.storage.clickhouse.host == "localhost"
    assert settings.storage.clickhouse.port == 8123
    assert settings.storage.clickhouse.database == "bitcoin_bastion"


def test_clickhouse_enabled_requires_non_disabled_profile() -> None:
    with pytest.raises(ValidationError, match="CLICKHOUSE_PROFILE"):
        make_settings(CLICKHOUSE_ENABLED=True)


def test_clickhouse_enabled_settings_are_exposed_without_secrets_in_repr() -> None:
    settings = make_settings(
        CLICKHOUSE_ENABLED=True,
        CLICKHOUSE_PROFILE="development",
        CLICKHOUSE_PASSWORD="dev-password",
    )

    clickhouse = settings.storage.clickhouse
    assert clickhouse.enabled is True
    assert clickhouse.username == "default"
    assert clickhouse.query_timeout_seconds == 15
    assert clickhouse.insert_timeout_seconds == 30


def test_clickhouse_production_like_rejects_placeholder_password() -> None:
    with pytest.raises(ValidationError, match="CLICKHOUSE_PASSWORD"):
        make_settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY=STRONG_SECRET,
            STORAGE_PROFILE="production",
            DATABASE_URL=POSTGRES_URL,
            POSTGRES_URL=POSTGRES_URL,
            REDIS_URL="redis://redis:6379/0",
            OBJECT_STORAGE_ENABLED=True,
            OBJECT_STORAGE_PROVIDER="minio",
            OBJECT_STORAGE_BUCKET="bastion-evidence",
            CLICKHOUSE_ENABLED=True,
            CLICKHOUSE_PROFILE="production",
            CLICKHOUSE_PASSWORD="password",
        )
