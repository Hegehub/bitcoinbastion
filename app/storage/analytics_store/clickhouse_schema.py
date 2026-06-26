"""Import-safe ClickHouse analytics schema registry."""

from __future__ import annotations

from pathlib import Path

DDL_DIR = Path(__file__).resolve().parent / "ddl"

CLICKHOUSE_DDL_FILES: list[str] = [
    "001_market_time_machine_events.sql",
    "002_news_impact_events.sql",
    "003_candle_attribution_events.sql",
    "004_trace_runtime_events.sql",
    "005_webhook_delivery_events.sql",
    "006_operator_replay_events.sql",
    "007_api_usage_events.sql",
    "999_schema_metadata.sql",
]

CLICKHOUSE_ANALYTICS_TABLES: list[str] = [
    "market_time_machine_events",
    "news_impact_events",
    "candle_attribution_events",
    "trace_runtime_events",
    "webhook_delivery_events",
    "operator_replay_events",
    "api_usage_events",
    "analytics_schema_metadata",
]


def get_clickhouse_ddl_paths() -> list[Path]:
    """Return registered DDL file paths without requiring a ClickHouse connection."""

    return [DDL_DIR / filename for filename in CLICKHOUSE_DDL_FILES]


def get_clickhouse_table_names() -> list[str]:
    """Return ClickHouse analytics table names in schema application order."""

    return list(CLICKHOUSE_ANALYTICS_TABLES)
