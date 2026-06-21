"""TimescaleDB foundation for Bitcoin Bastion time-series storage."""

from app.storage.timeseries.config import TimescaleConfig
from app.storage.timeseries.health import check_timescale
from app.storage.timeseries.hypertables import (
    create_hypertable_if_not_exists,
    ensure_timescale_extension,
    set_compression_policy,
    set_retention_policy,
    validate_identifier,
    validate_interval,
    validate_table_name,
)
from app.storage.timeseries.repositories import TimeRange, TimeSeriesRepository

__all__ = [
    "TimeRange",
    "TimeSeriesRepository",
    "TimescaleConfig",
    "check_timescale",
    "create_hypertable_if_not_exists",
    "ensure_timescale_extension",
    "set_compression_policy",
    "set_retention_policy",
    "validate_identifier",
    "validate_interval",
    "validate_table_name",
]
