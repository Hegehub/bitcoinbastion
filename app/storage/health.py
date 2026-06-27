"""Storage health aggregation without connecting to real storage engines."""

from collections.abc import Iterable

from app.storage.constants import POSTGRES
from app.storage.interfaces import (
    STORAGE_HEALTH_DEGRADED,
    STORAGE_HEALTH_DISABLED,
    STORAGE_HEALTH_MISCONFIGURED,
    STORAGE_HEALTH_OK,
    STORAGE_HEALTH_UNAVAILABLE,
    StorageHealthCheck,
    StorageHealthResult,
)


class StorageHealthAggregator:
    def __init__(self, checks: Iterable[StorageHealthCheck]) -> None:
        self._checks = list(checks)

    async def run_checks(self) -> list[StorageHealthResult]:
        return [await check.check_health() for check in self._checks]

    async def summary(self) -> dict[str, object]:
        results = await self.run_checks()
        postgres_unavailable = any(
            result.name == POSTGRES
            and result.enabled
            and result.status in {STORAGE_HEALTH_UNAVAILABLE, STORAGE_HEALTH_MISCONFIGURED}
            for result in results
        )
        degraded = any(
            result.enabled
            and (
                result.degraded
                or result.status
                in {
                    STORAGE_HEALTH_DEGRADED,
                    STORAGE_HEALTH_UNAVAILABLE,
                    STORAGE_HEALTH_MISCONFIGURED,
                }
            )
            for result in results
        )

        if postgres_unavailable:
            status = STORAGE_HEALTH_UNAVAILABLE
        elif degraded:
            status = STORAGE_HEALTH_DEGRADED
        else:
            status = STORAGE_HEALTH_OK

        return {
            "status": status,
            "engines": [
                {
                    "name": result.name,
                    "status": result.status,
                    "enabled": result.enabled,
                    "degraded": result.degraded,
                    "latency_ms": result.latency_ms,
                    "message": result.message,
                }
                for result in results
                if result.status != STORAGE_HEALTH_DISABLED or result.enabled is False
            ],
            "degraded": status != STORAGE_HEALTH_OK,
        }
