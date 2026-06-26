from app.core.config import Settings
from app.storage.timeseries.operations import TimescaleOperationsConfig, expected_retention_targets


def test_timescale_retention_config_parses_defaults_and_overrides() -> None:
    settings = Settings(
        _env_file=None,
        TIMESCALE_RETENTION_ENABLED=True,
        TIMESCALE_RAW_MARKET_RETENTION_DAYS=200,
        TIMESCALE_RAW_HEALTH_RETENTION_DAYS=100,
        TIMESCALE_RAW_USAGE_RETENTION_DAYS=300,
        TIMESCALE_AGGREGATE_RETENTION_DAYS=4000,
        TIMESCALE_ACCESS_HISTORY_RETENTION_DAYS=900,
    )
    config = TimescaleOperationsConfig.from_settings(settings)
    targets = {
        target.table_name: target.after_days for target in expected_retention_targets(config)
    }

    assert config.retention_enabled is True
    assert config.aggregate_retention_days == 4000
    assert config.access_history_retention_days == 900
    assert targets["btc_price_points"] == 200
    assert targets["provider_health_timeseries_snapshots"] == 100
    assert targets["metric_usage_events"] == 300
