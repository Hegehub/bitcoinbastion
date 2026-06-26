from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.storage.timeseries.operations import (
    EXPECTED_CONTINUOUS_AGGREGATES,
    TimescaleOperationsService,
)


def test_expected_continuous_aggregate_names_are_defined() -> None:
    names = {item.name for item in EXPECTED_CONTINUOUS_AGGREGATES}
    assert {
        "btc_price_1m",
        "btc_price_5m",
        "btc_price_1h",
        "btc_price_1d",
        "btc_candles_5m",
        "btc_candles_1h",
        "btc_candles_1d",
        "provider_health_5m",
        "provider_health_1h",
        "provider_health_1d",
        "source_health_1h",
        "source_health_1d",
        "metric_usage_5m",
        "metric_usage_1h",
        "metric_usage_1d",
        "access_integrity_1h",
        "access_integrity_1d",
    } == names


def test_timescale_operations_disabled_status_is_structured() -> None:
    engine = create_engine("sqlite://", future=True, poolclass=StaticPool)
    status = TimescaleOperationsService(
        Settings(_env_file=None, TIMESCALE_ENABLED=False), Session(engine)
    ).get_timescale_operations_status()

    assert status["enabled"] is False
    assert status["status"] == "disabled"
    assert status["continuous_aggregates"]["expected"] == len(EXPECTED_CONTINUOUS_AGGREGATES)
    assert "password" not in str(status).lower()


def test_timescale_operations_enabled_with_sqlite_is_degraded_without_secret_leak() -> None:
    engine = create_engine("sqlite://", future=True, poolclass=StaticPool)
    status = TimescaleOperationsService(
        Settings(
            _env_file=None, TIMESCALE_ENABLED=True, TIMESCALE_URL="postgres://user:secret@db/app"
        ),
        Session(engine),
    ).get_timescale_operations_status()

    assert status["enabled"] is True
    assert status["status"] == "degraded"
    assert "secret" not in str(status).lower()
    assert "postgres://" not in str(status).lower()
