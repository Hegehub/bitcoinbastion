"""timescale operations aggregates and policies

Revision ID: 20260625_0061
Revises: 20260625_0060
Create Date: 2026-06-25
"""

from __future__ import annotations

import os

from alembic import op
from sqlalchemy import text

revision = "20260625_0061"
down_revision = "20260625_0060"
branch_labels = None
depends_on = None


def _is_postgresql() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, str(default))))
    except ValueError:
        return default


def _timescale_enabled() -> bool:
    return _env_bool("TIMESCALE_ENABLED")


def _create_extension_enabled() -> bool:
    return _env_bool("TIMESCALE_CREATE_EXTENSION")


def _continuous_aggregates_enabled() -> bool:
    return _env_bool("TIMESCALE_CONTINUOUS_AGGREGATES_ENABLED", "true")


def _retention_enabled() -> bool:
    return _env_bool("TIMESCALE_RETENTION_ENABLED", "true")


def _compression_enabled() -> bool:
    return _env_bool("TIMESCALE_COMPRESSION_ENABLED", "true")


AGGREGATES: tuple[tuple[str, str, str], ...] = (
    ("btc_price_1m", "btc_price_points", "1 minute"),
    ("btc_price_5m", "btc_price_points", "5 minutes"),
    ("btc_price_1h", "btc_price_points", "1 hour"),
    ("btc_price_1d", "btc_price_points", "1 day"),
    ("btc_candles_5m", "btc_candles", "5 minutes"),
    ("btc_candles_1h", "btc_candles", "1 hour"),
    ("btc_candles_1d", "btc_candles", "1 day"),
    ("provider_health_5m", "provider_health_timeseries_snapshots", "5 minutes"),
    ("provider_health_1h", "provider_health_timeseries_snapshots", "1 hour"),
    ("provider_health_1d", "provider_health_timeseries_snapshots", "1 day"),
    ("source_health_1h", "source_health_timeseries_snapshots", "1 hour"),
    ("source_health_1d", "source_health_timeseries_snapshots", "1 day"),
    ("metric_usage_5m", "metric_usage_events", "5 minutes"),
    ("metric_usage_1h", "metric_usage_events", "1 hour"),
    ("metric_usage_1d", "metric_usage_events", "1 day"),
    ("access_integrity_1h", "metric_usage_events", "1 hour"),
    ("access_integrity_1d", "metric_usage_events", "1 day"),
)


def _aggregate_select(name: str, table_name: str, interval: str) -> str:
    if table_name == "btc_price_points":
        return f"""
            CREATE MATERIALIZED VIEW IF NOT EXISTS {name}
            WITH (timescaledb.continuous) AS
            SELECT time_bucket('{interval}', observed_at) AS bucket,
                   count(*) AS count,
                   min(price_usd) AS min,
                   max(price_usd) AS max,
                   avg(price_usd) AS avg,
                   last(price_usd, observed_at) AS latest_value,
                   avg(provider_confidence) AS confidence_avg
            FROM {table_name}
            GROUP BY bucket
            WITH NO DATA;
        """
    if table_name == "btc_candles":
        return f"""
            CREATE MATERIALIZED VIEW IF NOT EXISTS {name}
            WITH (timescaledb.continuous) AS
            SELECT time_bucket('{interval}', open_time) AS bucket,
                   count(*) AS count,
                   first(open_price, open_time) AS open,
                   max(high_price) AS high,
                   min(low_price) AS low,
                   last(close_price, close_time) AS close,
                   sum(coalesce(volume_estimate, volume, 0)) AS volume,
                   max(provider_count) AS provider_count,
                   avg(provider_confidence) AS confidence_avg
            FROM {table_name}
            GROUP BY bucket
            WITH NO DATA;
        """
    if table_name in {"provider_health_timeseries_snapshots", "source_health_timeseries_snapshots"}:
        return f"""
            CREATE MATERIALIZED VIEW IF NOT EXISTS {name}
            WITH (timescaledb.continuous) AS
            SELECT time_bucket('{interval}', observed_at) AS bucket,
                   count(*) AS count,
                   min(health_score) AS min,
                   max(health_score) AS max,
                   avg(health_score) AS avg,
                   sum(CASE WHEN is_degraded THEN 1 ELSE 0 END) AS degraded_count,
                   sum(success_count) AS success_count,
                   sum(failure_count) AS error_count
            FROM {table_name}
            GROUP BY bucket
            WITH NO DATA;
        """
    return f"""
        CREATE MATERIALIZED VIEW IF NOT EXISTS {name}
        WITH (timescaledb.continuous) AS
        SELECT time_bucket('{interval}', recorded_at) AS bucket,
               count(*) AS count,
               sum(request_count) AS request_count,
               sum(credit_cost) AS credits_consumed,
               sum(CASE WHEN decision = 'allowed' THEN request_count ELSE 0 END) AS allowed_count,
               sum(CASE WHEN decision IN ('denied', 'quota_exceeded', 'policy_denied') THEN request_count ELSE 0 END) AS denied_count,
               sum(CASE WHEN decision = 'degraded' THEN request_count ELSE 0 END) AS degraded_count
        FROM {table_name}
        GROUP BY bucket
        WITH NO DATA;
    """


def _prepare_extension() -> None:
    if _create_extension_enabled():
        op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")


def _create_continuous_aggregates() -> None:
    if not _continuous_aggregates_enabled():
        return
    for name, table_name, interval in AGGREGATES:
        op.execute(text(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb')
                   AND to_regclass('public.{table_name}') IS NOT NULL THEN
                    EXECUTE $cagg${_aggregate_select(name, table_name, interval)}$cagg$;
                END IF;
            END
            $$;
        """))


def _apply_retention_policies() -> None:
    if not _retention_enabled():
        return
    market_days = _env_int("TIMESCALE_RAW_MARKET_RETENTION_DAYS", 180)
    health_days = _env_int("TIMESCALE_RAW_HEALTH_RETENTION_DAYS", 90)
    usage_days = _env_int("TIMESCALE_RAW_USAGE_RETENTION_DAYS", 180)
    targets = (
        ("btc_price_points", market_days),
        ("btc_candles", market_days),
        ("mempool_fee_snapshots", market_days),
        ("provider_health_timeseries_snapshots", health_days),
        ("source_health_timeseries_snapshots", health_days),
        ("provider_confidence_timeseries_events", health_days),
        ("source_confidence_timeseries_events", health_days),
        ("metric_usage_events", usage_days),
    )
    for table_name, days in targets:
        op.execute(text(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb')
                   AND to_regclass('public.{table_name}') IS NOT NULL THEN
                    PERFORM add_retention_policy('public.{table_name}', INTERVAL '{days} days', if_not_exists => TRUE);
                END IF;
            END
            $$;
        """))


def _apply_compression_policies() -> None:
    if not _compression_enabled():
        return
    market_days = _env_int("TIMESCALE_COMPRESS_MARKET_AFTER_DAYS", 7)
    health_days = _env_int("TIMESCALE_COMPRESS_HEALTH_AFTER_DAYS", 14)
    usage_days = _env_int("TIMESCALE_COMPRESS_USAGE_AFTER_DAYS", 14)
    targets = (
        ("btc_price_points", market_days),
        ("btc_candles", market_days),
        ("mempool_fee_snapshots", market_days),
        ("provider_health_timeseries_snapshots", health_days),
        ("source_health_timeseries_snapshots", health_days),
        ("provider_confidence_timeseries_events", health_days),
        ("source_confidence_timeseries_events", health_days),
        ("metric_usage_events", usage_days),
    )
    for table_name, days in targets:
        op.execute(text(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb')
                   AND to_regclass('public.{table_name}') IS NOT NULL THEN
                    EXECUTE 'ALTER TABLE public.{table_name} SET (timescaledb.compress)';
                    PERFORM add_compression_policy('public.{table_name}', INTERVAL '{days} days', if_not_exists => TRUE);
                END IF;
            END
            $$;
        """))


def upgrade() -> None:
    if not (_is_postgresql() and _timescale_enabled()):
        return
    _prepare_extension()
    _create_continuous_aggregates()
    _apply_retention_policies()
    _apply_compression_policies()


def downgrade() -> None:
    if not _is_postgresql():
        return
    for name, _, _ in reversed(AGGREGATES):
        op.execute(text(f"DROP MATERIALIZED VIEW IF EXISTS {name}"))
