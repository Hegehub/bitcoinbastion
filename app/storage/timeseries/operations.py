"""Operational TimescaleDB maintenance helpers.

This module defines the expected continuous aggregates, retention policies, and
compression policies for Bitcoin Bastion time-series storage. It is defensive:
disabled/non-PostgreSQL environments return structured degraded/disabled status
instead of requiring TimescaleDB during local tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.storage.timeseries.errors import TimescaleConfigurationError
from app.storage.timeseries.hypertables import validate_identifier


@dataclass(frozen=True)
class ContinuousAggregateDefinition:
    name: str
    source_table: str
    bucket_interval: str
    time_column: str
    family: str


@dataclass(frozen=True)
class PolicyTarget:
    table_name: str
    policy_family: str
    after_days: int


@dataclass(frozen=True)
class TimescaleOperationsConfig:
    retention_enabled: bool
    raw_market_retention_days: int
    raw_health_retention_days: int
    raw_usage_retention_days: int
    aggregate_retention_days: int
    access_history_retention_days: int
    compression_enabled: bool
    compress_after_days: int
    compress_market_after_days: int
    compress_health_after_days: int
    compress_usage_after_days: int

    @classmethod
    def from_settings(cls, settings: Settings) -> "TimescaleOperationsConfig":
        return cls(
            retention_enabled=settings.timescale_retention_enabled,
            raw_market_retention_days=settings.timescale_raw_market_retention_days,
            raw_health_retention_days=settings.timescale_raw_health_retention_days,
            raw_usage_retention_days=settings.timescale_raw_usage_retention_days,
            aggregate_retention_days=settings.timescale_aggregate_retention_days,
            access_history_retention_days=settings.timescale_access_history_retention_days,
            compression_enabled=settings.timescale_compression_enabled,
            compress_after_days=settings.timescale_compress_after_days,
            compress_market_after_days=settings.timescale_compress_market_after_days,
            compress_health_after_days=settings.timescale_compress_health_after_days,
            compress_usage_after_days=settings.timescale_compress_usage_after_days,
        )


EXPECTED_CONTINUOUS_AGGREGATES: tuple[ContinuousAggregateDefinition, ...] = (
    ContinuousAggregateDefinition(
        "btc_price_1m", "btc_price_points", "1 minute", "observed_at", "market"
    ),
    ContinuousAggregateDefinition(
        "btc_price_5m", "btc_price_points", "5 minutes", "observed_at", "market"
    ),
    ContinuousAggregateDefinition(
        "btc_price_1h", "btc_price_points", "1 hour", "observed_at", "market"
    ),
    ContinuousAggregateDefinition(
        "btc_price_1d", "btc_price_points", "1 day", "observed_at", "market"
    ),
    ContinuousAggregateDefinition(
        "btc_candles_5m", "btc_candles", "5 minutes", "open_time", "market"
    ),
    ContinuousAggregateDefinition("btc_candles_1h", "btc_candles", "1 hour", "open_time", "market"),
    ContinuousAggregateDefinition("btc_candles_1d", "btc_candles", "1 day", "open_time", "market"),
    ContinuousAggregateDefinition(
        "provider_health_5m",
        "provider_health_timeseries_snapshots",
        "5 minutes",
        "observed_at",
        "health",
    ),
    ContinuousAggregateDefinition(
        "provider_health_1h",
        "provider_health_timeseries_snapshots",
        "1 hour",
        "observed_at",
        "health",
    ),
    ContinuousAggregateDefinition(
        "provider_health_1d",
        "provider_health_timeseries_snapshots",
        "1 day",
        "observed_at",
        "health",
    ),
    ContinuousAggregateDefinition(
        "source_health_1h", "source_health_timeseries_snapshots", "1 hour", "observed_at", "health"
    ),
    ContinuousAggregateDefinition(
        "source_health_1d", "source_health_timeseries_snapshots", "1 day", "observed_at", "health"
    ),
    ContinuousAggregateDefinition(
        "metric_usage_5m", "metric_usage_events", "5 minutes", "recorded_at", "usage"
    ),
    ContinuousAggregateDefinition(
        "metric_usage_1h", "metric_usage_events", "1 hour", "recorded_at", "usage"
    ),
    ContinuousAggregateDefinition(
        "metric_usage_1d", "metric_usage_events", "1 day", "recorded_at", "usage"
    ),
    ContinuousAggregateDefinition(
        "access_integrity_1h", "metric_usage_events", "1 hour", "recorded_at", "access"
    ),
    ContinuousAggregateDefinition(
        "access_integrity_1d", "metric_usage_events", "1 day", "recorded_at", "access"
    ),
)


def expected_retention_targets(config: TimescaleOperationsConfig) -> tuple[PolicyTarget, ...]:
    return (
        PolicyTarget("btc_price_points", "market_raw", config.raw_market_retention_days),
        PolicyTarget("btc_candles", "market_raw", config.raw_market_retention_days),
        PolicyTarget("mempool_fee_snapshots", "market_raw", config.raw_market_retention_days),
        PolicyTarget(
            "provider_health_timeseries_snapshots", "health_raw", config.raw_health_retention_days
        ),
        PolicyTarget(
            "source_health_timeseries_snapshots", "health_raw", config.raw_health_retention_days
        ),
        PolicyTarget(
            "provider_confidence_timeseries_events", "health_raw", config.raw_health_retention_days
        ),
        PolicyTarget(
            "source_confidence_timeseries_events", "health_raw", config.raw_health_retention_days
        ),
        PolicyTarget("metric_usage_events", "usage_raw", config.raw_usage_retention_days),
    )


def expected_compression_targets(config: TimescaleOperationsConfig) -> tuple[PolicyTarget, ...]:
    return (
        PolicyTarget("btc_price_points", "market_raw", config.compress_market_after_days),
        PolicyTarget("btc_candles", "market_raw", config.compress_market_after_days),
        PolicyTarget("mempool_fee_snapshots", "market_raw", config.compress_market_after_days),
        PolicyTarget(
            "provider_health_timeseries_snapshots", "health_raw", config.compress_health_after_days
        ),
        PolicyTarget(
            "source_health_timeseries_snapshots", "health_raw", config.compress_health_after_days
        ),
        PolicyTarget(
            "provider_confidence_timeseries_events", "health_raw", config.compress_health_after_days
        ),
        PolicyTarget(
            "source_confidence_timeseries_events", "health_raw", config.compress_health_after_days
        ),
        PolicyTarget("metric_usage_events", "usage_raw", config.compress_usage_after_days),
    )


class TimescaleOperationsService:
    def __init__(self, settings: Settings, db: Session) -> None:
        self.settings = settings
        self.db = db
        self.config = TimescaleOperationsConfig.from_settings(settings)

    def list_continuous_aggregates(self) -> list[str]:
        if not self._is_postgresql_enabled():
            return []
        rows = self.db.execute(
            text("""
                SELECT view_name
                FROM timescaledb_information.continuous_aggregates
                WHERE view_schema = :schema
            """),
            {"schema": self.settings.timescale_schema},
        ).fetchall()
        return sorted(str(row[0]) for row in rows)

    def refresh_aggregate(
        self, name: str, start: datetime | None = None, end: datetime | None = None
    ) -> dict[str, object]:
        if not self._is_postgresql_enabled():
            return {"name": name, "refreshed": False, "reason": "timescale_disabled_or_unavailable"}
        aggregate_name = validate_identifier(name, label="continuous aggregate")
        start_at = start or (datetime.utcnow() - timedelta(days=1))
        end_at = end or datetime.utcnow()
        self.db.execute(
            text("SELECT refresh_continuous_aggregate(:name, :start_at, :end_at)"),
            {"name": aggregate_name, "start_at": start_at, "end_at": end_at},
        )
        return {"name": aggregate_name, "refreshed": True}

    def refresh_all_recent(self) -> dict[str, object]:
        results = [self.refresh_aggregate(item.name) for item in EXPECTED_CONTINUOUS_AGGREGATES]
        return {
            "refreshed": sum(1 for item in results if item.get("refreshed")),
            "results": results,
        }

    def validate_retention_policies(self) -> dict[str, object]:
        targets = expected_retention_targets(self.config)
        if not self.settings.timescale_enabled:
            return {
                "enabled": self.config.retention_enabled,
                "policies_found": 0,
                "missing": [target.table_name for target in targets],
            }
        found = self._policy_tables("policy_retention")
        missing = [target.table_name for target in targets if target.table_name not in found]
        return {
            "enabled": self.config.retention_enabled,
            "policies_found": len(found),
            "missing": missing,
        }

    def validate_compression_policies(self) -> dict[str, object]:
        targets = expected_compression_targets(self.config)
        if not self.settings.timescale_enabled:
            return {
                "enabled": self.config.compression_enabled,
                "policies_found": 0,
                "missing": [target.table_name for target in targets],
            }
        found = self._policy_tables("policy_compression")
        missing = [target.table_name for target in targets if target.table_name not in found]
        return {
            "enabled": self.config.compression_enabled,
            "policies_found": len(found),
            "missing": missing,
        }

    def get_timescale_operations_status(self) -> dict[str, object]:
        if not self.settings.timescale_enabled:
            return self._disabled_status()
        if not self._is_postgresql():
            status = self._disabled_status()
            status.update(
                {
                    "enabled": True,
                    "status": "degraded",
                    "degraded": True,
                    "reason": "Timescale operations require PostgreSQL/TimescaleDB",
                }
            )
            return status
        try:
            extension_available = self._extension_available()
            aggregates = self.list_continuous_aggregates() if extension_available else []
            expected_names = [item.name for item in EXPECTED_CONTINUOUS_AGGREGATES]
            missing = [name for name in expected_names if name not in aggregates]
            retention = (
                self.validate_retention_policies()
                if extension_available
                else {
                    "enabled": self.config.retention_enabled,
                    "policies_found": 0,
                    "missing": [
                        target.table_name for target in expected_retention_targets(self.config)
                    ],
                }
            )
            compression = (
                self.validate_compression_policies()
                if extension_available
                else {
                    "enabled": self.config.compression_enabled,
                    "policies_found": 0,
                    "missing": [
                        target.table_name for target in expected_compression_targets(self.config)
                    ],
                }
            )
            degraded = (not extension_available) or bool(missing)
            return {
                "enabled": True,
                "status": "degraded" if degraded else "ok",
                "extension_available": extension_available,
                "continuous_aggregates": {
                    "expected": len(expected_names),
                    "found": len(aggregates),
                    "missing": missing,
                },
                "retention": retention,
                "compression": compression,
                "degraded": degraded,
            }
        except (SQLAlchemyError, TimescaleConfigurationError) as exc:
            return {
                "enabled": True,
                "status": "degraded",
                "extension_available": False,
                "continuous_aggregates": {
                    "expected": len(EXPECTED_CONTINUOUS_AGGREGATES),
                    "found": 0,
                    "missing": [item.name for item in EXPECTED_CONTINUOUS_AGGREGATES],
                },
                "retention": {
                    "enabled": self.config.retention_enabled,
                    "policies_found": 0,
                    "missing": [],
                },
                "compression": {
                    "enabled": self.config.compression_enabled,
                    "policies_found": 0,
                    "missing": [],
                },
                "degraded": True,
                "error_class": type(exc).__name__,
            }

    def _disabled_status(self) -> dict[str, object]:
        return {
            "enabled": False,
            "status": "disabled",
            "extension_available": None,
            "continuous_aggregates": {
                "expected": len(EXPECTED_CONTINUOUS_AGGREGATES),
                "found": 0,
                "missing": [item.name for item in EXPECTED_CONTINUOUS_AGGREGATES],
            },
            "retention": {
                "enabled": self.config.retention_enabled,
                "policies_found": 0,
                "missing": [],
            },
            "compression": {
                "enabled": self.config.compression_enabled,
                "policies_found": 0,
                "missing": [],
            },
            "degraded": False,
        }

    def _is_postgresql_enabled(self) -> bool:
        return self.settings.timescale_enabled and self._is_postgresql()

    def _is_postgresql(self) -> bool:
        bind = self.db.get_bind()
        return getattr(getattr(bind, "dialect", None), "name", "") == "postgresql"

    def _extension_available(self) -> bool:
        row = self.db.execute(
            text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb')")
        ).first()
        return bool(row[0]) if row is not None else False

    def _policy_tables(self, proc_name: str) -> set[str]:
        rows = self.db.execute(
            text("""
                SELECT hypertable_name
                FROM timescaledb_information.jobs
                WHERE proc_name = :proc_name
            """),
            {"proc_name": proc_name},
        ).fetchall()
        return {str(row[0]) for row in rows}
