import pytest

from app.core.config import Settings
from app.storage.constants import CLICKHOUSE, OBJECT_STORAGE, POSTGRES, QDRANT, REDIS, TIMESCALE
from app.storage.errors import StorageConfigurationError
from app.storage.profiles import get_expected_engines_for_profile, validate_storage_profile


def test_development_profile_exists_and_is_bounded() -> None:
    assert get_expected_engines_for_profile("development") == {POSTGRES, REDIS}


def test_initial_production_profile_expects_foundation_engines() -> None:
    assert get_expected_engines_for_profile("initial_production") == {
        POSTGRES,
        REDIS,
        OBJECT_STORAGE,
    }


def test_full_production_profile_expects_required_engines() -> None:
    assert get_expected_engines_for_profile("full_production") == {
        POSTGRES,
        REDIS,
        OBJECT_STORAGE,
        TIMESCALE,
        CLICKHOUSE,
        QDRANT,
    }


def test_single_node_and_self_hosted_style_profiles_are_explicit() -> None:
    single_node = get_expected_engines_for_profile("single_node")
    enterprise_self_hosted = get_expected_engines_for_profile("enterprise_self_hosted")

    assert {POSTGRES, REDIS, OBJECT_STORAGE}.issubset(single_node)
    assert {POSTGRES, REDIS, OBJECT_STORAGE, TIMESCALE, CLICKHOUSE, QDRANT}.issubset(
        enterprise_self_hosted
    )


def test_staging_and_production_storage_settings_profiles_can_be_derived() -> None:
    for profile in ("staging", "production"):
        settings = Settings(
            STORAGE_PROFILE=profile,
            DATABASE_URL="postgresql://bastion@db/bitcoin_bastion",
            REDIS_URL="redis://redis:6379/0",
            OBJECT_STORAGE_ENABLED=True,
            OBJECT_STORAGE_BACKEND="local",
            OBJECT_STORAGE_PROVIDER="local",
            OBJECT_STORAGE_BUCKET="bastion-evidence",
        )
        assert settings.storage.profile == profile
        assert settings.storage.postgres.effective_url.startswith("postgresql://")
        assert settings.storage.redis.ephemeral_only is True


def test_profile_validation_returns_missing_engine_warnings() -> None:
    warnings = validate_storage_profile("full_production", {POSTGRES, REDIS, OBJECT_STORAGE})
    assert "full_production profile expects clickhouse but it is not enabled" in warnings
    assert "full_production profile expects qdrant but it is not enabled" in warnings
    assert "full_production profile expects timescale but it is not enabled" in warnings
    assert "redis is enabled but must not be treated as durable truth" in warnings


def test_unknown_profile_raises_clean_configuration_error() -> None:
    with pytest.raises(StorageConfigurationError, match="Unknown storage profile"):
        get_expected_engines_for_profile("unknown")


def test_production_profile_does_not_silently_disable_critical_stores() -> None:
    with pytest.raises(ValueError, match="PostgreSQL URL"):
        Settings(STORAGE_PROFILE="production", DATABASE_URL="sqlite+pysqlite:///./local.db")


def test_optional_future_stores_can_be_disabled_explicitly() -> None:
    settings = Settings(
        STORAGE_PROFILE="development",
        TIMESCALE_ENABLED=False,
        CLICKHOUSE_ENABLED=False,
        QDRANT_ENABLED=False,
        VECTOR_STORE_PROVIDER="disabled",
    )
    assert settings.storage.timescale.enabled is False
    assert settings.storage.clickhouse.enabled is False
    assert settings.storage.vector.qdrant_enabled is False
