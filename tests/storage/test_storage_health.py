from dataclasses import dataclass

import asyncio

from app.storage.constants import CLICKHOUSE, POSTGRES
from app.storage.health import StorageHealthAggregator
from app.storage.interfaces import StorageHealthResult


@dataclass(frozen=True)
class FakeHealthCheck:
    name: str
    result: StorageHealthResult

    async def check_health(self) -> StorageHealthResult:
        return self.result


def test_health_summary_returns_unavailable_if_postgres_unavailable() -> None:
    aggregator = StorageHealthAggregator(
        [
            FakeHealthCheck(
                POSTGRES,
                StorageHealthResult(
                    name=POSTGRES,
                    status="unavailable",
                    enabled=True,
                    degraded=True,
                    message="postgres unavailable",
                ),
            ),
            FakeHealthCheck(
                CLICKHOUSE,
                StorageHealthResult(name=CLICKHOUSE, status="ok", enabled=True, degraded=False),
            ),
        ]
    )
    summary = asyncio.run(aggregator.summary())
    assert summary["status"] == "unavailable"
    assert summary["degraded"] is True


def test_health_summary_returns_degraded_if_optional_analytical_store_unavailable() -> None:
    aggregator = StorageHealthAggregator(
        [
            FakeHealthCheck(
                POSTGRES,
                StorageHealthResult(name=POSTGRES, status="ok", enabled=True, degraded=False),
            ),
            FakeHealthCheck(
                CLICKHOUSE,
                StorageHealthResult(
                    name=CLICKHOUSE,
                    status="unavailable",
                    enabled=True,
                    degraded=True,
                    message="analytics unavailable",
                ),
            ),
        ]
    )
    summary = asyncio.run(aggregator.summary())
    assert summary["status"] == "degraded"
    assert summary["degraded"] is True
