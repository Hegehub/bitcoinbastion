import asyncio

import pytest

from app.storage.timeseries.errors import TimescaleConfigurationError
from app.storage.timeseries.hypertables import (
    create_hypertable_if_not_exists,
    ensure_timescale_extension,
    set_compression_policy,
    set_retention_policy,
    validate_identifier,
    validate_interval,
    validate_table_name,
)


class FakeAsyncConnection:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def execute(self, statement, parameters=None):  # noqa: ANN001 - SQLAlchemy-like fake.
        self.calls.append((str(statement), parameters or {}))
        return None


@pytest.mark.parametrize(
    "identifier",
    ["btc_price_points", "provider_health_1", "_internal_metric"],
)
def test_validate_identifier_accepts_safe_identifiers(identifier: str) -> None:
    assert validate_identifier(identifier) == identifier


@pytest.mark.parametrize(
    "identifier",
    ["", "1metric", "metric-name", "metric;drop", "metric name", "metric.schema.extra"],
)
def test_validate_identifier_rejects_unsafe_identifiers(identifier: str) -> None:
    with pytest.raises(TimescaleConfigurationError):
        validate_identifier(identifier)


@pytest.mark.parametrize("table_name", ["btc_price_points", "timeseries.btc_candles"])
def test_validate_table_name_accepts_one_or_two_part_names(table_name: str) -> None:
    assert validate_table_name(table_name) == table_name


@pytest.mark.parametrize("table_name", ["", "bad-name", "public.table.extra", "public.table;drop"])
def test_validate_table_name_rejects_unsafe_names(table_name: str) -> None:
    with pytest.raises(TimescaleConfigurationError):
        validate_table_name(table_name)


@pytest.mark.parametrize("interval", ["1 day", "12 hours", "30 minutes", "2 weeks"])
def test_validate_interval_accepts_safe_intervals(interval: str) -> None:
    assert validate_interval(interval) == interval


@pytest.mark.parametrize("interval", ["", "0 day", "one day", "1 fortnight", "1 day; drop table x"])
def test_validate_interval_rejects_unsafe_intervals(interval: str) -> None:
    with pytest.raises(TimescaleConfigurationError):
        validate_interval(interval)


def test_ensure_timescale_extension_generates_idempotent_sql() -> None:
    conn = FakeAsyncConnection()

    asyncio.run(ensure_timescale_extension(conn))

    statement, params = conn.calls[0]
    assert "CREATE EXTENSION IF NOT EXISTS timescaledb" in statement
    assert params == {}


def test_create_hypertable_uses_validated_parameters() -> None:
    conn = FakeAsyncConnection()

    asyncio.run(
        create_hypertable_if_not_exists(
            conn,
            "timeseries.btc_candles",
            "bucket_start",
            chunk_interval="1 day",
        )
    )

    statement, params = conn.calls[0]
    assert "create_hypertable" in statement
    assert "if_not_exists" in statement
    assert params["table_name"] == '"timeseries"."btc_candles"'
    assert params["time_column"] == "bucket_start"
    assert params["chunk_interval"] == "1 day"


def test_policy_helpers_generate_safe_idempotent_sql() -> None:
    conn = FakeAsyncConnection()

    asyncio.run(set_compression_policy(conn, "timeseries.provider_health_snapshots", "7 days"))
    asyncio.run(set_retention_policy(conn, "timeseries.provider_health_snapshots", "90 days"))

    assert "add_compression_policy" in conn.calls[0][0]
    assert "if_not_exists" in conn.calls[0][0]
    assert conn.calls[0][1]["compress_after"] == "7 days"
    assert "add_retention_policy" in conn.calls[1][0]
    assert "if_not_exists" in conn.calls[1][0]
    assert conn.calls[1][1]["drop_after"] == "90 days"
