from app.core.config import Settings
from app.storage.timeseries.operations import (
    TimescaleOperationsConfig,
    expected_compression_targets,
)


def test_timescale_compression_config_parses_overrides() -> None:
    settings = Settings(
        _env_file=None,
        TIMESCALE_COMPRESSION_ENABLED=True,
        TIMESCALE_COMPRESS_AFTER_DAYS=8,
        TIMESCALE_COMPRESS_MARKET_AFTER_DAYS=9,
        TIMESCALE_COMPRESS_HEALTH_AFTER_DAYS=15,
        TIMESCALE_COMPRESS_USAGE_AFTER_DAYS=16,
    )
    config = TimescaleOperationsConfig.from_settings(settings)
    targets = {
        target.table_name: target.after_days for target in expected_compression_targets(config)
    }

    assert config.compression_enabled is True
    assert config.compress_after_days == 8
    assert targets["btc_candles"] == 9
    assert targets["source_health_timeseries_snapshots"] == 15
    assert targets["metric_usage_events"] == 16
