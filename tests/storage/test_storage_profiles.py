import pytest

from app.storage.constants import CLICKHOUSE, OBJECT_STORAGE, POSTGRES, QDRANT, REDIS, TIMESCALE
from app.storage.errors import StorageConfigurationError
from app.storage.profiles import get_expected_engines_for_profile, validate_storage_profile


def test_full_production_profile_expects_required_engines() -> None:
    assert get_expected_engines_for_profile("full_production") == {
        POSTGRES,
        REDIS,
        OBJECT_STORAGE,
        TIMESCALE,
        CLICKHOUSE,
        QDRANT,
    }


def test_initial_production_profile_expects_foundation_engines() -> None:
    assert get_expected_engines_for_profile("initial_production") == {
        POSTGRES,
        REDIS,
        OBJECT_STORAGE,
    }


def test_profile_validation_returns_missing_engine_warnings() -> None:
    warnings = validate_storage_profile("full_production", {POSTGRES, REDIS, OBJECT_STORAGE})
    assert "full_production profile expects clickhouse but it is not enabled" in warnings
    assert "full_production profile expects qdrant but it is not enabled" in warnings
    assert "full_production profile expects timescale but it is not enabled" in warnings
    assert "redis is enabled but must not be treated as durable truth" in warnings


def test_unknown_profile_raises_clean_configuration_error() -> None:
    with pytest.raises(StorageConfigurationError, match="Unknown storage profile"):
        get_expected_engines_for_profile("unknown")
