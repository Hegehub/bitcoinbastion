import pytest
from pydantic import ValidationError

from app.core.config import Settings

STRONG_SECRET = "bastion-prod-secret-that-is-long-and-random-2026"
POSTGRES_URL = "postgresql+psycopg://bastion:secret@postgres:5432/bastion"


def make_settings(**overrides: object) -> Settings:
    values = {"_env_file": None}
    values.update(overrides)
    return Settings(**values)


def production_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "ENVIRONMENT": "production",
        "JWT_SECRET_KEY": STRONG_SECRET,
        "STORAGE_PROFILE": "production",
        "DATABASE_URL": POSTGRES_URL,
        "POSTGRES_URL": POSTGRES_URL,
        "REDIS_URL": "redis://redis:6379/0",
        "OBJECT_STORAGE_ENABLED": True,
        "OBJECT_STORAGE_PROVIDER": "minio",
        "OBJECT_STORAGE_BUCKET": "bastion-evidence",
        "OBJECT_STORAGE_CHECKSUM_REQUIRED": True,
    }
    values.update(overrides)
    return make_settings(**values)


def test_default_development_profile_loads() -> None:
    settings = make_settings()
    assert settings.storage.profile == "development"
    assert settings.storage.postgres.effective_url == "sqlite+pysqlite:///./bitcoin_bastion.db"
    assert settings.storage.object_storage.enabled is False


def test_production_requires_postgres_url() -> None:
    with pytest.raises(ValidationError, match="DATABASE_URL or POSTGRES_URL"):
        production_settings(DATABASE_URL="", POSTGRES_URL="")


def test_production_requires_object_storage_if_configured_to_require_it() -> None:
    with pytest.raises(ValidationError, match="OBJECT_STORAGE_ENABLED"):
        production_settings(OBJECT_STORAGE_ENABLED=False)


def test_redis_is_marked_ephemeral_only_by_default() -> None:
    settings = make_settings()
    assert settings.storage.redis.ephemeral_only is True


def test_clickhouse_enabled_requires_non_disabled_profile() -> None:
    with pytest.raises(ValidationError, match="CLICKHOUSE_PROFILE"):
        make_settings(CLICKHOUSE_ENABLED=True)


def test_qdrant_provider_requires_qdrant_url_and_redaction() -> None:
    with pytest.raises(ValidationError, match="QDRANT_URL"):
        make_settings(VECTOR_STORE_PROVIDER="qdrant", QDRANT_ENABLED=True, QDRANT_URL="")

    with pytest.raises(ValidationError, match="VECTOR_REDACTION_REQUIRED"):
        make_settings(
            VECTOR_STORE_PROVIDER="qdrant",
            QDRANT_ENABLED=True,
            QDRANT_URL="http://qdrant:6333",
            VECTOR_REDACTION_REQUIRED=False,
        )

    settings = make_settings(
        VECTOR_STORE_PROVIDER="qdrant",
        QDRANT_ENABLED=True,
        QDRANT_URL="http://qdrant:6333",
    )
    assert settings.storage.vector.provider == "qdrant"


def test_pgvector_provider_requires_pgvector_enabled_true() -> None:
    with pytest.raises(ValidationError, match="PGVECTOR_ENABLED"):
        make_settings(VECTOR_STORE_PROVIDER="pgvector", PGVECTOR_ENABLED=False)

    settings = make_settings(VECTOR_STORE_PROVIDER="pgvector", PGVECTOR_ENABLED=True)
    assert settings.storage.vector.provider == "pgvector"
    assert settings.storage.vector.pgvector_enabled is True


def test_vector_redaction_required_false_is_rejected_in_production() -> None:
    with pytest.raises(ValidationError, match="VECTOR_REDACTION_REQUIRED"):
        production_settings(VECTOR_REDACTION_REQUIRED=False)


def test_local_storage_in_production_requires_encryption() -> None:
    with pytest.raises(ValidationError, match="LOCAL_STORAGE_ENCRYPTION_REQUIRED"):
        production_settings(
            LOCAL_STORAGE_ENABLED=True,
            LOCAL_STORAGE_ENCRYPTION_REQUIRED=False,
        )


def test_database_url_and_postgres_url_mismatch_is_rejected_in_production() -> None:
    with pytest.raises(ValidationError, match="DATABASE_URL and POSTGRES_URL"):
        production_settings(POSTGRES_URL="postgresql+psycopg://other:secret@postgres:5432/bastion")


def test_air_gapped_profile_does_not_require_external_cloud_object_storage_by_default() -> None:
    settings = make_settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY=STRONG_SECRET,
        STORAGE_PROFILE="air_gapped",
        DATABASE_URL=POSTGRES_URL,
        REDIS_URL="redis://localhost:6379/0",
        OBJECT_STORAGE_ENABLED=False,
    )
    assert settings.storage.profile == "air_gapped"
    assert settings.storage.object_storage.enabled is False
