import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.storage.timeseries.config import TimescaleConfig


def test_timescale_disabled_by_default_does_not_require_timescaledb() -> None:
    settings = Settings(_env_file=None)

    assert settings.timescale_enabled is False
    assert settings.storage.timescale.enabled is False
    assert settings.storage.timescale.schema == "public"
    assert settings.storage.timescale.create_extension is False
    assert settings.storage.timescale.default_chunk_interval == "1 day"
    assert settings.storage.timescale.health_timeout_seconds == 2


def test_timescale_config_can_be_enabled_without_domain_migrations() -> None:
    settings = Settings(
        _env_file=None,
        TIMESCALE_ENABLED=True,
        TIMESCALE_SCHEMA="timeseries",
        TIMESCALE_DEFAULT_CHUNK_INTERVAL="12 hours",
        TIMESCALE_HEALTH_TIMEOUT_SECONDS=3,
        TIMESCALE_CREATE_EXTENSION=True,
    )
    config = TimescaleConfig.from_settings(settings)

    assert config.enabled is True
    assert config.create_extension is True
    assert config.schema == "timeseries"
    assert config.default_chunk_interval == "12 hours"
    assert config.health_timeout_seconds == 3


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("TIMESCALE_SCHEMA", "public;drop table storage_artifacts"),
        ("TIMESCALE_DEFAULT_CHUNK_INTERVAL", "1 day; drop extension timescaledb"),
    ],
)
def test_timescale_config_rejects_unsafe_schema_or_interval(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, TIMESCALE_ENABLED=True, **{field: value})
