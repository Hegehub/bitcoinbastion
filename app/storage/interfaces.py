"""Implementation-neutral storage protocols and lightweight models."""

from dataclasses import dataclass
from typing import Protocol

STORAGE_HEALTH_OK = "ok"
STORAGE_HEALTH_DISABLED = "disabled"
STORAGE_HEALTH_DEGRADED = "degraded"
STORAGE_HEALTH_UNAVAILABLE = "unavailable"
STORAGE_HEALTH_MISCONFIGURED = "misconfigured"

VALID_STORAGE_HEALTH_STATUSES = {
    STORAGE_HEALTH_OK,
    STORAGE_HEALTH_DISABLED,
    STORAGE_HEALTH_DEGRADED,
    STORAGE_HEALTH_UNAVAILABLE,
    STORAGE_HEALTH_MISCONFIGURED,
}


@dataclass(frozen=True)
class StorageEngineDescriptor:
    name: str
    role: str
    enabled: bool
    source_of_truth: bool
    stores_sensitive_material: bool
    description: str


@dataclass(frozen=True)
class StorageHealthResult:
    name: str
    status: str
    enabled: bool
    degraded: bool
    latency_ms: float | None = None
    message: str | None = None

    def __post_init__(self) -> None:
        if self.status not in VALID_STORAGE_HEALTH_STATUSES:
            raise ValueError(f"Unsupported storage health status: {self.status}")


@dataclass(frozen=True)
class StorageSafetyRule:
    code: str
    description: str
    severity: str


class StorageHealthCheck(Protocol):
    name: str

    async def check_health(self) -> StorageHealthResult: ...


class TransactionalStore(Protocol):
    name: str
    role: str


class CacheStore(Protocol):
    name: str
    role: str


class ObjectStore(Protocol):
    name: str
    role: str


class TimeSeriesStore(Protocol):
    name: str
    role: str


class AnalyticsStore(Protocol):
    name: str
    role: str


class VectorStore(Protocol):
    name: str
    role: str


class LocalStore(Protocol):
    name: str
    role: str
