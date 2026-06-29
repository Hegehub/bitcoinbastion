import asyncio
from dataclasses import dataclass

from fastapi.testclient import TestClient
from redis import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1 import storage_status as storage_status_module
from app.core.config import Settings
from app.main import app

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


class FakeStatusDB:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def execute(self, statement: object) -> None:
        if self.fail:
            raise SQLAlchemyError("postgres://user:password@private/db failed")


class FakeStatusRedis:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def ping(self) -> bool:
        if self.fail:
            raise RedisError("redis://:secret@private-redis:6379 failed")
        return True


def _storage_status_client(monkeypatch, *, db_fail: bool = False, redis_fail: bool = False):
    app.dependency_overrides.clear()

    def _db_override():
        yield FakeStatusDB(fail=db_fail)

    app.dependency_overrides[storage_status_module.db_session] = _db_override
    monkeypatch.setattr(
        storage_status_module,
        "get_settings",
        lambda: Settings(
            DATABASE_URL="sqlite+pysqlite:///:memory:",
            REDIS_URL="redis://localhost:6379/0",
            STORAGE_PROFILE="development",
        ),
    )
    monkeypatch.setattr(
        storage_status_module,
        "get_redis_client",
        lambda: FakeStatusRedis(fail=redis_fail),
    )
    return TestClient(app)


def test_storage_status_api_returns_expected_response_shape(monkeypatch) -> None:
    client = _storage_status_client(monkeypatch)
    payload = client.get("/api/v1/storage/status").json()

    assert {"status", "profile", "summary", "stores", "degraded_mode"}.issubset(payload)
    assert payload["profile"] == "development"
    assert set(payload["stores"]) == {
        "postgres",
        "redis",
        "object_storage",
        "timescale",
        "clickhouse",
        "qdrant",
        "sqlite_local",
        "duckdb_local",
    }


def test_disabled_optional_stores_are_represented_not_missing(monkeypatch) -> None:
    client = _storage_status_client(monkeypatch)
    stores = client.get("/api/v1/storage/status").json()["stores"]

    assert stores["timescale"]["status"] == "disabled"
    assert stores["clickhouse"]["status"] == "disabled"
    assert stores["qdrant"]["status"] == "disabled"


def test_critical_storage_status_failure_uses_unavailable_semantics(monkeypatch) -> None:
    client = _storage_status_client(monkeypatch, db_fail=True)
    payload = client.get("/api/v1/storage/status").json()

    assert payload["status"] == "unavailable"
    assert payload["summary"]["required_ok"] is False
    assert payload["stores"]["postgres"]["details"]["error_class"] == "SQLAlchemyError"


def test_storage_status_api_does_not_leak_secret_connection_strings(monkeypatch) -> None:
    client = _storage_status_client(monkeypatch, db_fail=True, redis_fail=True)
    body = client.get("/api/v1/storage/status").text

    assert "password" not in body
    assert "secret" not in body
    assert "private-redis" not in body
