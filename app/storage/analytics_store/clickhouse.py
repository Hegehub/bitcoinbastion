"""ClickHouse-backed analytics-store foundation.

The implementation is intentionally generic: it provides health, query, and
insert primitives only. Domain-specific analytics schemas and projections are
introduced by later prompts.
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import time
from typing import Any

from app.core.config import ClickHouseStorageSettings
from app.storage.analytics_store.errors import (
    AnalyticsStoreConfigurationError,
    AnalyticsStoreInsertError,
    AnalyticsStoreQueryError,
)
from app.storage.analytics_store.schemas import (
    AnalyticsInsertResult,
    AnalyticsQueryResult,
    AnalyticsStoreHealth,
    AnalyticsStoreStatusValue,
)


class ClickHouseAnalyticsStore:
    def __init__(self, settings: ClickHouseStorageSettings) -> None:
        self._settings = settings
        self._client: Any | None = None

    def _require_dependency(self) -> Any:
        if importlib.util.find_spec("clickhouse_connect") is None:
            raise AnalyticsStoreConfigurationError(
                "clickhouse-connect dependency is not installed."
            )
        return importlib.import_module("clickhouse_connect")

    def _client_kwargs(self) -> dict[str, object]:
        return {
            "host": self._settings.host,
            "port": self._settings.port,
            "database": self._settings.database,
            "username": self._settings.username,
            "password": self._settings.password,
            "secure": self._settings.secure,
            "connect_timeout": self._settings.connect_timeout_seconds,
            "send_receive_timeout": self._settings.query_timeout_seconds,
        }

    def _get_client(self) -> Any:
        if self._client is None:
            module = self._require_dependency()
            self._client = module.get_client(**self._client_kwargs())
        return self._client

    async def healthcheck(self) -> AnalyticsStoreHealth:
        started_at = time.monotonic()
        try:
            await asyncio.to_thread(self._get_client().query, "SELECT 1")
        except Exception as exc:  # noqa: BLE001 - health responses must be sanitized.
            return AnalyticsStoreHealth(
                enabled=True,
                status=AnalyticsStoreStatusValue.UNAVAILABLE,
                database=self._settings.database,
                latency_ms=_latency_ms(started_at),
                error=type(exc).__name__,
                details={"connection": "failed", "profile": self._settings.profile},
            )
        return AnalyticsStoreHealth(
            enabled=True,
            status=AnalyticsStoreStatusValue.OK,
            database=self._settings.database,
            latency_ms=_latency_ms(started_at),
            error=None,
            details={"connection": "ok", "profile": self._settings.profile},
        )

    async def execute(
        self, query: str, parameters: dict[str, object] | None = None
    ) -> AnalyticsQueryResult:
        started_at = time.monotonic()
        try:
            result = await asyncio.to_thread(
                self._get_client().query,
                query,
                parameters=parameters or {},
                settings={"max_execution_time": self._settings.query_timeout_seconds},
            )
        except Exception as exc:  # noqa: BLE001 - wrapped without leaking query text.
            raise AnalyticsStoreQueryError(
                f"ClickHouse analytics query failed: {type(exc).__name__}"
            ) from exc

        rows = _rows_as_dicts(result)
        return AnalyticsQueryResult(
            rows=rows,
            row_count=len(rows),
            elapsed_ms=_latency_ms(started_at),
        )

    async def insert_events(
        self, table: str, events: list[dict[str, object]]
    ) -> AnalyticsInsertResult:
        started_at = time.monotonic()
        if not events:
            return AnalyticsInsertResult(
                table=table,
                inserted_count=0,
                elapsed_ms=0,
                status=AnalyticsStoreStatusValue.OK,
            )

        try:
            columns = list(events[0].keys())
            data = [[event.get(column) for column in columns] for event in events]
            await asyncio.to_thread(
                self._get_client().insert,
                table,
                data,
                column_names=columns,
                settings={"insert_quorum_timeout": self._settings.insert_timeout_seconds * 1000},
            )
        except Exception as exc:  # noqa: BLE001 - wrapped without leaking event payloads.
            raise AnalyticsStoreInsertError(
                f"ClickHouse analytics insert failed: {type(exc).__name__}"
            ) from exc

        return AnalyticsInsertResult(
            table=table,
            inserted_count=len(events),
            elapsed_ms=_latency_ms(started_at),
            status=AnalyticsStoreStatusValue.OK,
        )


def _rows_as_dicts(result: Any) -> list[dict[str, Any]]:
    column_names = list(getattr(result, "column_names", []) or [])
    rows = list(getattr(result, "result_rows", []) or [])
    if not column_names:
        return [dict(row) for row in rows if isinstance(row, dict)]
    return [dict(zip(column_names, row, strict=False)) for row in rows]


def _latency_ms(started_at: float) -> float:
    return round((time.monotonic() - started_at) * 1000, 3)
